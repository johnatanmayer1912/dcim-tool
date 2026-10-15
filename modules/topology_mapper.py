"""
modules/topology_mapper.py
--------------------------
CDP/LLDP topology discovery with enriched neighbor metadata.

v6.2.0 Enhancements:
  - Priority 2: Full CDP/LLDP detail parsing — platform, IOS version, mgmt IP
    captured per neighbor and surfaced in edge tooltips.
  - Priority 5: Edges carry peer metadata so multi-device merge in adapters.py
    can build a unified enriched graph.
"""
import re
from .network_base import connect_device, build_json, safe_node_name, resolve_hostname_from_connection


class TopologyCancelled(Exception):
    """Operator cancelled; live SSH sockets are force-closed when registered."""


def _send_cli(conn, command, timeout=60):
    """Send one CLI command after a cooperative cancel check."""
    try:
        from utils.task_control_plane import should_abort
        if should_abort():
            raise TopologyCancelled('cancelled by operator before CLI')
    except TopologyCancelled:
        raise
    except Exception:
        pass
    try:
        return conn.send_command(command, read_timeout=timeout)
    except TopologyCancelled:
        raise
    except Exception:
        try:
            from utils.task_control_plane import should_abort
            if should_abort():
                raise TopologyCancelled('cancelled during CLI (SSH session closed)')
        except TopologyCancelled:
            raise
        except Exception:
            pass
        raise


def norm_int(n):
    """Normalize interface name to short form."""
    return (n.replace("Ethernet", "Eth")
             .replace("GigabitEthernet", "Gi")
             .replace("FastEthernet", "Fa")
             .replace("TenGigabitEthernet", "Te")
             .replace("HundredGigE", "Hu")
             .replace("FortyGigabitEthernet", "Fo")
             .replace("TwentyFiveGigE", "Twe")
             .replace("Port-channel", "Po")
             .replace("port-channel", "Po")
             .strip())


def _parse_status_line_fields(line, parts):
    """
    Extract VLAN, speed, and duplex from a 'show interface status' line.

    IOS/NX-OS column order (after interface name):
      [description]  status  vlan  duplex  speed  type

    Returns (speed_str, duplex_str, vlan_str) — empty string if not found.
    """
    speed = ""
    duplex = ""
    vlan = ""

    # Speed patterns (check longer/more specific first)
    speed_patterns = [
        (r'\b100G\b|\b100000\b', '100G'),
        (r'\b40G\b|\b40000\b', '40G'),
        (r'\b25G\b|\b25000\b', '25G'),
        (r'\b10G\b|\b10000\b', '10G'),
        (r'\ba-1g\b|\b1000\b', '1G'),
        (r'\ba-100\b', '100M'),
        (r'\ba-10\b', '10M'),
        (r'\bauto\b', 'Auto'),
    ]
    for pattern, label in speed_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            speed = label
            break

    # Duplex
    if re.search(r'\ba-full\b|full-duplex', line, re.IGNORECASE):
        duplex = 'Full'
    elif re.search(r'\ba-half\b|half-duplex', line, re.IGNORECASE):
        duplex = 'Half'

    # VLAN — look for a standalone number that's a plausible VLAN ID (1-4094)
    # Typical position: 4th column after interface name in 'show interface status'
    # Skip status keywords and interface name
    status_keywords = {
        'connected', 'notconnect', 'notconn', 'disabled', 'err-disabled',
        'inactive', 'up', 'down', 'auto', 'full', 'half', 'trunk', 'routed'
    }
    for part in parts[1:]:
        clean = re.sub(r'\(.*\)', '', part).strip()
        if clean.lower() in status_keywords:
            continue
        if re.match(r'^\d+$', clean):
            vid = int(clean)
            if 1 <= vid <= 4094:
                vlan = clean
                break
        if clean.lower() == 'trunk':
            vlan = 'trunk'
            break
        if clean.lower() == 'routed':
            vlan = 'routed'
            break

    return speed, duplex, vlan


def _extract_desc_from_status_line(line: str, iface_name: str) -> str:
    """Best-effort description extraction from 'show interface status' rows."""
    if not line or not iface_name:
        return ""
    m = re.match(
        r'^\s*(\S+)\s+(.*?)\s+(connected|notconnect|notconn|disabled|err-disabled|inactive|up|down)\b',
        line,
        re.IGNORECASE
    )
    if not m:
        return ""
    if norm_int(m.group(1)) != norm_int(iface_name):
        return ""
    desc = (m.group(2) or "").strip()
    if desc.lower() in ("--", "none", "n/a", "null"):
        return ""
    return desc


# ── Priority 2: Enriched CDP/LLDP parsers ────────────────────────────────────

def _parse_cdp_detail(out, true_host):
    """
    Parse 'show cdp neighbors detail' output only.

    CDP fields only — does not accept LLDP keys (System Name / Local Intf / Port id)
    to avoid CDP/LLDP conflation. Missing local or remote ports → edge dropped
    (no invented unknown/n/a ports).

    Returns list of edge dicts with enriched neighbor metadata:
      peer_platform, peer_version, peer_mgmt_ip, peer_caps
    """
    edges = []
    cur_rem = cur_loc = cur_rem_int = None
    cur_platform = cur_version = cur_mgmt = cur_caps = ""
    cur_raw_lines = []

    def _flush():
        nonlocal cur_rem, cur_loc, cur_rem_int
        nonlocal cur_platform, cur_version, cur_mgmt, cur_caps, cur_raw_lines
        plat_low = (cur_platform or '').lower()
        if any(x in plat_low for x in (
            'ip phone', 'ata', 'desktop', 'camera', 'air-ap', 'air-', 'wireless ap',
            'access point', 'meraki mr',
        )):
            cur_rem = cur_loc = cur_rem_int = None
            cur_platform = cur_version = cur_mgmt = cur_caps = ""
            cur_raw_lines = []
            return
        if cur_rem and cur_loc and cur_rem_int:
            edges.append({
                "from": true_host,
                "f_port": cur_loc,
                "to": cur_rem,
                "t_port": cur_rem_int,
                "peer_platform": cur_platform,
                "peer_version": cur_version,
                "peer_mgmt_ip": cur_mgmt,
                "peer_caps": cur_caps,
                "discovery": "cdp",
                "protocol": "CDP",
                "raw_evidence": "\n".join(cur_raw_lines)[:500] if cur_raw_lines else "",
            })
        elif cur_rem and (not cur_loc or not cur_rem_int):
            # Partial CDP observation — refuse invented ports
            pass
        cur_rem = cur_loc = cur_rem_int = None
        cur_platform = cur_version = cur_mgmt = cur_caps = ""
        cur_raw_lines = []

    for line in out.splitlines():
        # New neighbor block — CDP Device ID only (not LLDP System Name)
        dev_m = re.search(r'Device ID:\s*(.*)', line, re.I)
        if dev_m:
            _flush()
            cur_rem = dev_m.group(1).strip().split('.')[0]
            cur_raw_lines = [line.strip()]
            continue

        if cur_rem is not None:
            cur_raw_lines.append(line.strip())

        # Local/remote interface (CDP combined line)
        int_m = re.search(r'Interface:\s*(.*?),.*?Port ID.*?:\s*(.*)', line)
        if int_m:
            cur_loc = int_m.group(1).strip()
            cur_rem_int = int_m.group(2).strip()
            continue

        # Split Interface / Port ID lines (some NX-OS / IOS variants)
        only_int = re.search(r'^Interface:\s*([^,\n]+)', line)
        if only_int and 'Port ID' not in line:
            cur_loc = only_int.group(1).strip().rstrip(',')
            continue
        only_pid = re.search(r'Port ID\s*\(outgoing port\)\s*:\s*(\S+)', line, re.I)
        if only_pid:
            cur_rem_int = only_pid.group(1).strip()
            continue

        # Platform
        plat_m = re.search(r'Platform:\s*(.*?)(?:,|$)', line)
        if plat_m:
            cur_platform = plat_m.group(1).strip()
            continue

        # IOS/Software version — grab first meaningful version token
        ver_m = re.search(r'Version\s*:\s*(.*)', line, re.IGNORECASE)
        if ver_m and not cur_version:
            raw = ver_m.group(1).strip()
            if raw:
                short = re.search(r'[Vv]ersion\s+([\w\.\(\)]+)', raw)
                cur_version = short.group(1) if short else raw[:40]
            continue

        # Version on its own line (after "Version :" with empty value)
        if cur_rem and not cur_version and line.strip():
            ver_inline = re.search(r'(?:Version\s+)?([\d]+\.[\d]+[\w\.\(\)]+)', line.strip())
            if ver_inline and not any(skip in line for skip in [
                'Interface', 'Platform', 'IP address', 'Capabilities',
                'Device', 'Port', 'Duplex', 'Advertisement'
            ]):
                cur_version = ver_inline.group(1)
                continue

        # Management IP (CDP)
        mgmt_m = re.search(r'IP address:\s*(\S+)', line)
        if mgmt_m and not cur_mgmt:
            cur_mgmt = mgmt_m.group(1).strip()
            continue

        # Capabilities
        caps_m = re.search(r'Capabilities:\s*(.*)', line)
        if caps_m:
            cur_caps = caps_m.group(1).strip()
            continue

    _flush()
    return edges


def _parse_lldp_detail(out, true_host):
    """
    Parse 'show lldp neighbors detail' (Juniper / IOS LLDP).
    Returns enriched edge list.
    """
    edges = []
    cur_rem = cur_loc = cur_rem_int = None
    cur_platform = cur_version = cur_mgmt = cur_caps = ""

    def _flush():
        nonlocal cur_rem, cur_loc, cur_rem_int
        nonlocal cur_platform, cur_version, cur_mgmt, cur_caps
        if cur_rem and cur_loc and cur_rem_int:
            edges.append({
                "from": true_host,
                "f_port": cur_loc,
                "to": cur_rem,
                "t_port": cur_rem_int,
                "peer_platform": cur_platform,
                "peer_version": cur_version,
                "peer_mgmt_ip": cur_mgmt,
                "peer_caps": cur_caps,
                "discovery": "lldp",
            })
        cur_rem = cur_loc = cur_rem_int = None
        cur_platform = cur_version = cur_mgmt = cur_caps = ""

    for line in out.splitlines():
        sys_m = re.search(r'System Name:\s*(.*)', line)
        if sys_m:
            _flush()
            cur_rem = sys_m.group(1).strip().split('.')[0]
            continue

        sys_desc = re.search(r'System Description:\s*(.*)', line)
        if sys_desc and not cur_platform:
            desc = sys_desc.group(1).strip()
            cur_platform = desc[:60]
            # v6.5.0: Extract version from LLDP System Description
            # Match patterns like "Version 15.2(4)E8", "Version 9.3(8)", etc.
            ver_m = re.search(r'(?:Version|Ver|V)?\s*([\d]+\.[\d]+[\w\.\(\)]+)', desc)
            if ver_m:
                cur_version = ver_m.group(1)
            continue

        loc_m = re.search(r'Local Interface:\s*(.*)', line)
        if loc_m:
            cur_loc = loc_m.group(1).strip()
            continue

        port_m = re.search(r'Port ID:\s*(.*)', line)
        if port_m:
            cur_rem_int = port_m.group(1).strip()
            continue

        mgmt_m = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
        if mgmt_m and 'Management' in line and not cur_mgmt:
            cur_mgmt = mgmt_m.group(1).strip()
            continue

        caps_m = re.search(r'System Capabilities:\s*(.*)', line)
        if caps_m:
            cur_caps = caps_m.group(1).strip()
            continue

    _flush()
    return edges


# v6.5.0: Structured MAC table parsing with interface validation
def _parse_mac_table(mac_out, dtype, int_meta, log_func=None):
    """
    Parse MAC address table with structured column extraction.
    Returns dict of {normalized_interface: [mac_addresses]}.
    Only associates MACs if interface exists in int_meta.
    """
    interface_macs = {}
    valid_interfaces = set(int_meta.keys())
    
    for line in mac_out.splitlines():
        line = line.strip()
        if not line or any(x in line for x in ['Vlan', 'MAC', 'Type', 'Ports', '---']):
            continue
        
        # Match MAC address patterns
        mac_match = re.search(
            r'([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})'
            r'|([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})'
            r'|([0-9a-fA-F]{2}-[0-9a-fA-F]{2}-[0-9a-fA-F]{2}-[0-9a-fA-F]{2}-[0-9a-fA-F]{2}-[0-9a-fA-F]{2})',
            line
        )
        if not mac_match:
            continue
        
        mac_addr = mac_match.group(0)
        
        # Parse line columns
        parts = re.split(r'\s+', line)
        if len(parts) < 3:
            continue
        
        # Find interface column - typically the last column or contains interface name
        interface_candidate = None
        for part in reversed(parts):
            # Skip MAC addresses
            if re.match(r'([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})'
                       r'|([0-9a-fA-F]{2}[:.-]){5}[0-9a-fA-F]{2}', part):
                continue
            # Skip VLAN numbers
            if re.match(r'^\d+$', part):
                continue
            # Skip type keywords
            if part.lower() in ['dynamic', 'static', 'learned', 'sticky', 'forward']:
                continue
            # This might be the interface
            iface = norm_int(part)
            if iface:
                interface_candidate = iface
                break
        
        # Only add if interface is valid and in our interface list.
        # Try the candidate as-is first, then try common prefix variations
        # because the MAC table may use full names (GigabitEthernet0/1)
        # while int_meta keys are normalized (Gi0/1).
        matched_iface = None
        if interface_candidate:
            if interface_candidate in valid_interfaces:
                matched_iface = interface_candidate
            else:
                # Try normalizing the raw part that produced the candidate
                # by also checking if any valid interface is a prefix match
                for vi in valid_interfaces:
                    if vi.lower() == interface_candidate.lower():
                        matched_iface = vi
                        break
                    # e.g. candidate="Gi0/1", vi="Gi0/1/0" — skip
                    # e.g. candidate="Gi0/1", vi="gi0/1" — match
        if matched_iface:
            if matched_iface not in interface_macs:
                interface_macs[matched_iface] = []
            if mac_addr not in interface_macs[matched_iface]:
                interface_macs[matched_iface].append(mac_addr)
    
    return interface_macs


# ── v6.9.0: Structured Port-Channel / vPC / LACP Parsers ─────────────────────

def _extract_po_members(members_str):
    """
    Extract (intf, flags, status) tuples from a port-channel summary member string.
    v6.9.3: Hardened to handle missing flags or multiple bracketed flags.
    """
    members = []
    # Tokenize by whitespace first
    tokens = members_str.strip().split()
    for token in tokens:
        # Extract the interface name (everything before the first '(')
        name_m = re.match(r'^([^\(]+)', token)
        if not name_m: continue
        
        intf_raw = name_m.group(1)
        intf = norm_int(intf_raw)
        if not intf: continue
        
        # Extract all flags inside brackets
        flags_found = re.findall(r'\((.*?)\)', token)
        flags = "".join(flags_found)
        
        status = 'unknown'
        if flags:
            f_up = flags.upper()
            if 'P' in f_up and 'D' not in f_up:
                status = 'bundled'
            elif 'S' in f_up: # Note: case-insensitive check for suspended
                status = 'suspended'
            elif 'D' in f_up:
                status = 'down'
            elif 'I' in f_up:
                status = 'individual'
        
        members.append({'intf': intf, 'flags': flags, 'status': status})
    return members


def _parse_port_channel_summary_nxos(out):
    """
    Parse 'show port-channel summary' for NX-OS with a column-resilient strategy.
    Handles varying column counts across NX-OS versions (7.x, 9.x, 10.x).
    """
    result = {}
    current_po = None
    for line in out.splitlines():
        line = line.strip()
        if not line or any(x in line for x in ['Group', '------', 'Flags:', 'Protocol']):
            continue
        
        # Strategy: Look for the Po identifier (e.g., Po1) and extract the tailing ports
        m = re.search(r'(\d+)\s+(Po\d+)\s*\(.*?\)\s+.*?\s+(.*)', line, re.IGNORECASE)
        if m:
            po_id = norm_int(m.group(2))
            ports_chunk = m.group(3)
            protocol = "LACP" if "LACP" in line.upper() else "None"
            result[po_id] = {'protocol': protocol, 'members': _extract_po_members(ports_chunk)}
            current_po = po_id
            continue
            
        # Continuation line (wrapped member list)
        if current_po and '(' in line and ')' in line:
            result[current_po]['members'].extend(_extract_po_members(line))
            
    return result


def _parse_etherchannel_summary_ios(out):
    """
    Parse 'show etherchannel summary' for IOS/IOS-XE — extracts full member list.
    Returns: { 'Po1': { 'protocol': 'LACP', 'members': [{intf, flags, status}] } }
    """
    result = {}
    current_po = None
    for line in out.splitlines():
        line = line.strip()
        if not line or any(x in line for x in ['Number of', 'RU -', 'Flags:', '------']):
            continue
        m = re.match(r'(\d+)\s+(Po\d+)\s*\(\S*\)\s+(\w+)\s+(.*)', line, re.IGNORECASE)
        if m:
            po_id = norm_int(m.group(2))
            result[po_id] = {'protocol': m.group(3).upper(), 'members': _extract_po_members(m.group(4))}
            current_po = po_id
            continue
        if current_po and re.search(r'\w+\d+[/\d]+\(\w+\)', line):
            if not re.match(r'\d+\s+Po', line, re.IGNORECASE):
                result[current_po]['members'].extend(_extract_po_members(line))
    return result


def _normalize_vpc_peer_status(status_raw):
    """Normalize NX-OS peer status text to up/down."""
    from utils.nxos_vpc_parse import normalize_vpc_peer_status
    return normalize_vpc_peer_status(status_raw)


def _normalize_vpc_keepalive_status(status_raw):
    """Normalize NX-OS keepalive status text to up/down."""
    from utils.nxos_vpc_parse import normalize_vpc_keepalive_status
    return normalize_vpc_keepalive_status(status_raw)


def _parse_vpc_full(vpc_out, brief_out='', peer_link_out=''):
    """Parse 'show vpc' + 'show vpc peer-link' into a structured dict."""
    from utils.nxos_vpc_parse import parse_vpc_full
    return parse_vpc_full(vpc_out, brief_out, peer_link_out)


def _parse_vpc_brief_table(brief_out):
    """Parse vPC ID / Port / Status rows from 'show vpc brief' output."""
    from utils.nxos_vpc_parse import parse_vpc_table_from_cli
    return parse_vpc_table_from_cli('', brief_out)


def _parse_lacp_neighbors_nxos(lacp_out):
    """
    Parse 'show lacp neighbor' for NX-OS.
    Returns: { 'Po1': [{ local_port, partner_id, partner_port, partner_state }] }
    """
    result = {}
    current_po = None
    current_port = None
    entry = {}
    for line in lacp_out.splitlines():
        line_s = line.strip()
        if not line_s:
            continue
        po_m = re.match(r'(port-channel\d+|Po\d+)\s*$', line_s, re.IGNORECASE)
        if po_m:
            if current_po and current_port and entry:
                result[current_po].append(entry)
            current_po = norm_int(po_m.group(1))
            result.setdefault(current_po, [])
            current_port = None
            entry = {}
            continue
        port_m = re.match(r'(Eth\d+/\d+|Gi\d+/\d+|Te\d+/\d+)\s*:', line_s, re.IGNORECASE)
        if port_m and current_po is not None:
            if current_port and entry:
                result[current_po].append(entry)
            current_port = norm_int(port_m.group(1))
            entry = {'local_port': current_port, 'partner_id': '', 'partner_port': '', 'partner_state': ''}
            continue
        if current_po is not None and current_port:
            m = re.search(r'Partner\s+ID\s*[=:]\s*(\S+)', line_s, re.IGNORECASE)
            if m:
                raw = m.group(1)
                entry['partner_id'] = raw.split(',', 1)[-1] if ',' in raw else raw
            m = re.search(r'Partner\s+Port\s*[=:]\s*(\S+)', line_s, re.IGNORECASE)
            if m:
                entry['partner_port'] = norm_int(m.group(1))
            m = re.search(r'Partner\s+State\s*[=:]\s*(.*)', line_s, re.IGNORECASE)
            if m:
                entry['partner_state'] = m.group(1).strip()
    if current_po and current_port and entry:
        result[current_po].append(entry)
    return result


def _parse_lacp_neighbors_ios(lacp_out):
    """
    Parse 'show lacp neighbor' for IOS/IOS-XE.
    Returns: { 'Po1': [{ local_port, partner_id, partner_port, partner_state }] }
    """
    result = {}
    current_group = None
    for line in lacp_out.splitlines():
        line_s = line.strip()
        m = re.match(r'Channel\s+group\s+(\d+)', line_s, re.IGNORECASE)
        if m:
            current_group = f"Po{m.group(1)}"
            result.setdefault(current_group, [])
            continue
        if current_group and line_s:
            m = re.match(
                r'((?:Gi|Te|Fa|Eth|Hu|Fo|Twe)\S+)\s+\S+\s+\d+\s+'
                r'([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})'
                r'\s+\S+\s+\S+\s+(\S+)',
                line_s, re.IGNORECASE
            )
            if m:
                result[current_group].append({
                    'local_port': norm_int(m.group(1)),
                    'partner_id': m.group(2),
                    'partner_port': norm_int(m.group(3)),
                    'partner_state': ''
                })
    return result


def _parse_juniper_lag_detail(out):
    """
    Parse 'show lacp interfaces' or 'show aggregated-ethernet detail' for Juniper.
    Returns: { 'ae0': { 'protocol': 'LACP', 'members': [{intf, status, partner_id, partner_port}] } }
    """
    result = {}
    current_ae = None
    current_member = None
    for line in out.splitlines():
        line_s = line.strip()
        ae_m = re.match(r'(ae\d+)(?:\s+|$)', line_s, re.IGNORECASE)
        if ae_m:
            current_ae = ae_m.group(1).lower()
            result.setdefault(current_ae, {'protocol': 'LACP', 'members': []})
            current_member = None
            continue
        phys_m = re.match(r'(ge-\d+/\d+/\d+|xe-\d+/\d+/\d+|et-\d+/\d+/\d+)', line_s, re.IGNORECASE)
        if phys_m and current_ae:
            current_member = {'intf': phys_m.group(1).lower(), 'status': 'unknown', 'partner_id': '', 'partner_port': ''}
            result[current_ae]['members'].append(current_member)
            continue
        if current_member:
            m = re.search(r'Aggregate\s+status:\s*(\S+)', line_s, re.IGNORECASE)
            if m:
                current_member['status'] = 'bundled' if m.group(1).lower() in ('attached', 'up', 'collecting-distributing') else 'down'
            m = re.search(r'Partner\s+System\s+ID:\s*(\S+)', line_s, re.IGNORECASE)
            if m:
                current_member['partner_id'] = m.group(1)
            m = re.search(r'Partner\s+Port:\s*(\S+)', line_s, re.IGNORECASE)
            if m:
                current_member['partner_port'] = norm_int(m.group(1))
            m = re.search(r'LACP\s+state:\s*(.*)', line_s, re.IGNORECASE)
            if m and current_member['status'] == 'unknown':
                current_member['status'] = 'bundled' if any(x in m.group(1).lower() for x in ['col', 'dist']) else 'down'
    return result


def run(device, user, pwd, enb_pwd="", log_func=None):
    """
    Run topology mapping on a device.

    v6.2.0: Returns enriched edges with peer_platform, peer_version, peer_mgmt_ip.

    Args:
        device: Device dict with host, device_type, port
        user: Username
        pwd: Password
        enb_pwd: Enable password (optional)
        log_func: Logging function (optional)

    Returns:
        JSON response dict
    """
    host = device['host']
    dtype = (device.get('device_type') or 'cisco_ios').lower()
    conn = None

    try:
        if log_func:
            log_func(f"[{host}] Connecting to device...")
        conn = connect_device(device, user, pwd, enb_pwd)
        true_host = resolve_hostname_from_connection(conn, host, dtype, log_func=log_func)
        if log_func:
            log_func(f"[{true_host}] Successfully connected")

        int_meta = {}

        # Determine commands based on device type
        if "juniper" in dtype:
            stat_cmd = "show interfaces terse"
            desc_cmd = "show interfaces description"
        elif "nxos" in dtype:
            stat_cmd = "show interface status"
            desc_cmd = "show interface description"
        else:
            stat_cmd = "show interface status"
            desc_cmd = "show interfaces description"

        stat_out = _send_cli(conn, stat_cmd)
        desc_out = _send_cli(conn, desc_cmd)

        # Parse description output
        desc_regex = re.compile(
            r'^(\S+)\s+'
            r'(up|down|connected|admin\s+down|administratively\s+down'
            r'|notconn|notconnect|disabled|err-disabled)'
            r'\s+(up|down|proto\s+up|proto\s+down)?\s*(.*)',
            re.IGNORECASE
        )
        for line in desc_out.splitlines():
            line = line.strip()
            if not line or any(x in line for x in [
                '--', 'Interface', 'Status', 'Description',
                'Admin', 'Port', 'Vlan', 'Name'
            ]):
                continue
            m = desc_regex.match(line)
            if m:
                in_name = norm_int(m.group(1))
                desc_content = m.group(4) if m.group(4) else ""
                # Always initialise ALL fields so JS never gets undefined
                int_meta[in_name] = {
                    "desc"        : desc_content.strip(),
                    "admin_status": "unknown",
                    "op_status"   : "unknown",
                    "status"      : "unknown",
                    "speed"       : "",
                    "vlan"        : "",
                    "duplex"      : "",
                    "macs"        : [],
                }

        # Parse status output
        for line in stat_out.splitlines():
            line = line.strip()
            if not line or line.startswith('--') or any(
                x in line.lower() for x in ['interface', 'port', 'vlan', 'status']
            ):
                continue
            parts = line.split()
            if len(parts) >= 2:
                pname = norm_int(parts[0])
                if pname not in int_meta:
                    # New interface seen only in status output — init all fields
                    int_meta[pname] = {
                        "desc"        : "-",
                        "admin_status": "unknown",
                        "op_status"   : "unknown",
                        "status"      : "unknown",
                        "speed"       : "",
                        "vlan"        : "",
                        "duplex"      : "",
                        "macs"        : [],
                    }
                l_low = line.lower()
                if "err-disabled" in l_low:
                    int_meta[pname].update({
                        "admin_status": "up", "op_status": "err-disabled", "status": "err-disabled"
                    })
                elif "disabled" in l_low or "admin down" in l_low:
                    int_meta[pname].update({
                        "admin_status": "down", "op_status": "down", "status": "down"
                    })
                elif "notconnect" in l_low or "not conn" in l_low:
                    int_meta[pname].update({
                        "admin_status": "up", "op_status": "down", "status": "down"
                    })
                elif "connected" in l_low or (
                    " up" in l_low and "down" not in l_low.split(pname.lower())[-1]
                ):
                    int_meta[pname].update({
                        "admin_status": "up", "op_status": "up", "status": "up"
                    })
                elif any(x in l_low for x in ["sfp-absent", "sfp absent", "inactive"]):
                    int_meta[pname].update({
                        "admin_status": "up", "op_status": "inactive", "status": "down"
                    })
                else:
                    int_meta[pname].update({
                        "admin_status": "up", "op_status": "unknown", "status": "unknown"
                    })

                # v6.5.2: Extract VLAN, speed, duplex from 'show interface status' columns
                # Typical IOS/NX-OS format:
                #   Gi0/1   description   connected   100   a-full   1000   10/100/1000BaseTX
                # Columns: Port, Name/Desc, Status, Vlan, Duplex, Speed, Type
                _speed, _duplex, _vlan = _parse_status_line_fields(line, parts)
                if _speed:
                    int_meta[pname]["speed"] = _speed
                if _duplex:
                    int_meta[pname]["duplex"] = _duplex
                if _vlan:
                    int_meta[pname]["vlan"] = _vlan
                if not int_meta[pname].get("desc") or int_meta[pname].get("desc") == "-":
                    inferred_desc = _extract_desc_from_status_line(line, pname)
                    if inferred_desc:
                        int_meta[pname]["desc"] = inferred_desc

        # v6.5.0: Improved MAC address correlation with structured parsing
        interface_macs = {}
        mac_cmd = "show mac address-table"
        if "juniper" in dtype:
            mac_cmd = "show ethernet-switching table"
        elif "nxos" in dtype:
            mac_cmd = "show mac address-table"

        mac_out = _send_cli(conn, mac_cmd)
        interface_macs = _parse_mac_table(mac_out, dtype, int_meta, log_func)

        # v6.5.0: Pass ALL MACs for the new UI side-panel (no truncation)
        for iface, macs in interface_macs.items():
            if iface in int_meta:
                int_meta[iface]["macs"] = macs
                int_meta[iface]["mac_count"] = len(macs)

        # Port-channel and vPC detection
        bundles = {}
        vpc_ids = []
        vpc_domain_id = ""
        vpc_details = {}

        # v6.9.0: Initialize new enrichment containers
        port_channel_detail = {}   # Structured Po data: {po_id: {protocol, members}}
        vpc_structured = {}        # Parsed vPC domain state (role, keepalive, table)
        lacp_neighbors = {}        # LACP partner info: {po_id: [{local_port, partner_id, ...}]}
        nxos_version = ''

        if "nxos" in dtype or "nexus" in dtype:
            from utils.nxos_vpc_parse import extract_nxos_version
            try:
                ver_out = _send_cli(conn, "show version")
                nxos_version = extract_nxos_version(ver_out)
            except Exception:
                nxos_version = ''

            # --- Port-Channel: structured member list (v6.9.0) ---
            pc_out = _send_cli(conn, "show port-channel summary")
            port_channel_detail = _parse_port_channel_summary_nxos(pc_out)
            for po_id, po_data in port_channel_detail.items():
                for mem in po_data.get('members', []):
                    bundles[mem['intf']] = po_id

            # --- vPC: dual collection (show vpc + brief + peer-link) ---
            vpc_out = _send_cli(conn, "show vpc")
            brief_out_raw = _send_cli(conn, "show vpc brief")
            peer_link_out = _send_cli(conn, "show vpc peer-link")

            from utils.nxos_vpc_parse import parse_vpc_full, vpc_details_from_structured

            vpc_structured = parse_vpc_full(vpc_out, brief_out_raw, peer_link_out, nxos_version)
            vpc_domain_id = vpc_structured.get('domain_id') or vpc_domain_id
            if not vpc_domain_id:
                domain_match = re.search(r'vpc\s+domain\s+id\s*[:=]\s*(\d+)', vpc_out, re.IGNORECASE)
                if domain_match:
                    vpc_domain_id = domain_match.group(1)

            vpc_ids, vpc_details = vpc_details_from_structured(vpc_structured, peer_link_out)

            if not vpc_structured.get('vpc_table') and port_channel_detail:
                peer_po = vpc_structured.get('peer_link_po', '')
                for po_id in port_channel_detail:
                    if po_id == peer_po:
                        continue
                    if po_id not in vpc_details:
                        vpc_ids.append(po_id)
                        vpc_details[po_id] = {
                            'vpc_id': po_id.replace('Po', ''),
                            'status': 'up',
                            'consistency': 'unknown',
                            'active_vlans': '-',
                            'type': 'vpc',
                            'source': 'port-channel-summary',
                        }
                        vpc_structured.setdefault('vpc_table', []).append({
                            'vpc_id': po_id.replace('Po', ''),
                            'po': po_id,
                            'status': 'up',
                            'consistency': 'unknown',
                            'active_vlans': '-',
                        })

            const_out = _send_cli(conn, "show vpc consistency-parameters global")
            vpc_details["_consistency_global"] = {"type": "metadata", "raw": const_out}
            vpc_details["_vpc_brief"] = {"type": "metadata", "raw": brief_out_raw}

            # v6.9.0: LACP neighbor structured parse
            lacp_out = _send_cli(conn, "show lacp neighbor")
            vpc_details["_lacp_neighbor"] = {"type": "metadata", "raw": lacp_out}
            lacp_neighbors = _parse_lacp_neighbors_nxos(lacp_out)

            stp_out = _send_cli(conn, "show spanning-tree summary")
            vpc_details["_stp_summary"] = {"type": "metadata", "raw": stp_out}

        elif "ios" in dtype or "cisco" in dtype:
            # v6.9.0: Structured IOS EtherChannel parse
            ec_out = _send_cli(conn, "show etherchannel summary")
            port_channel_detail = _parse_etherchannel_summary_ios(ec_out)
            for po_id, po_data in port_channel_detail.items():
                for mem in po_data.get('members', []):
                    bundles[mem['intf']] = po_id
            # Backward-compat fallback
            if not port_channel_detail:
                for line in ec_out.splitlines():
                    em = re.search(r'(\d+)\s+Po(\d+).+?\s+(.*)', line)
                    if em:
                        po_id = f"Po{em.group(2)}"
                        for mem in em.group(3).split():
                            bundles[re.sub(r'\(.*\)', '', mem)] = po_id

            # v6.9.0: IOS LACP neighbor
            try:
                lacp_ios_out = _send_cli(conn, "show lacp neighbor")
                if "Invalid" not in lacp_ios_out and "not enabled" not in lacp_ios_out.lower():
                    lacp_neighbors = _parse_lacp_neighbors_ios(lacp_ios_out)
            except Exception:
                pass

        # ── Priority 2: Enriched CDP/LLDP topology discovery ─────────────────
        edges = []
        if "juniper" in dtype:
            out = _send_cli(conn, "show lldp neighbors detail")
            edges = _parse_lldp_detail(out, true_host)
            if not edges:
                out_brief = _send_cli(conn, "show lldp neighbors")
                for line in out_brief.splitlines():
                    parts = re.split(r'\s{2,}', line.strip())
                    if (len(parts) >= 5
                            and "Interface" not in parts[0]
                            and "interface" not in parts[0].lower()):
                        edges.append({
                            "from": true_host, "f_port": parts[0],
                            "to": parts[4].split('.')[0], "t_port": parts[3],
                            "peer_platform": "", "peer_version": "",
                            "peer_mgmt_ip": "", "peer_caps": "",
                        })
            # v6.9.0: Juniper LAG/ae collection
            try:
                lag_out = _send_cli(conn, "show lacp interfaces")
                if "Invalid" not in lag_out and "not found" not in lag_out.lower():
                    port_channel_detail = _parse_juniper_lag_detail(lag_out)
                if not port_channel_detail:
                    ae_out = _send_cli(conn, "show aggregated-ethernet detail")
                    port_channel_detail = _parse_juniper_lag_detail(ae_out)
                # Build bundles map from ae members
                for ae_id, ae_data in port_channel_detail.items():
                    for mem in ae_data.get('members', []):
                        bundles[norm_int(mem['intf'])] = norm_int(ae_id)
                    lacp_neighbors[norm_int(ae_id)] = [
                        {'local_port': m['intf'], 'partner_id': m.get('partner_id', ''),
                         'partner_port': m.get('partner_port', ''), 'partner_state': m.get('status', '')}
                        for m in ae_data.get('members', [])
                    ]
            except Exception:
                pass
        else:
            cdp_out = _send_cli(conn, "show cdp neighbors detail")
            lldp_out = _send_cli(conn, "show lldp neighbors detail")

            cdp_edges = []
            lldp_edges = []

            if not any(err in cdp_out for err in ["% Invalid input", "CDP is not enabled", "Invalid command"]):
                cdp_edges = _parse_cdp_detail(cdp_out, true_host)

            if not any(err in lldp_out for err in ["% Invalid input", "LLDP is not enabled", "Invalid command", "LLDP is not active"]):
                lldp_edges = _parse_lldp_detail(lldp_out, true_host)

            # Deduplicate by local port and remote port to avoid doubling edges
            seen_local = set()
            for e in cdp_edges + lldp_edges:
                key = (e['from'], e.get('to'), norm_int(e.get('f_port', '')), norm_int(e.get('t_port', '')))
                if key not in seen_local:
                    seen_local.add(key)
                    edges.append(e)

        overlay_links = []
        overlay_collected = False
        ov = {}
        optics = {}
        try:
            from modules.overlay_collector import collect_overlay
            from utils.lacp_oper import apply_lacp_to_edges, parse_lacp_neighbor_index
            ov = collect_overlay(conn, true_host, dtype, lambda cmd, timeout=60: _send_cli(conn, cmd, timeout))
            overlay_links = ov.get('links') or []
            overlay_collected = bool(ov.get('collected'))
            apply_lacp_to_edges(edges, parse_lacp_neighbor_index(lacp_neighbors), None)
            edges.extend(overlay_links)
        except TopologyCancelled:
            raise
        except Exception:
            pass
        try:
            from utils.optics_dom import collect_optics
            optics = collect_optics(dtype, lambda cmd, timeout=60: _send_cli(conn, cmd, timeout))
        except TopologyCancelled:
            raise
        except Exception:
            optics = {}

        # v6.9.0: Build CDP validation map — local_port → {peer, peer_port, validated}
        cdp_validation_map = {}
        for e in edges:
            local_port = norm_int(e.get('f_port', ''))
            if local_port:
                cdp_validation_map[local_port] = {
                    'peer': e.get('to', ''),
                    'peer_port': norm_int(e.get('t_port', '')),
                    'validated': True
                }

        # v6.9.3: Synthetic Interface Promotion
        # Ensure all discovered Port-Channels have entries in int_meta, even if missing from 'show interface status'
        for po_id, po_data in port_channel_detail.items():
            if po_id not in int_meta:
                int_meta[po_id] = {
                    "status": "up" if po_data.get('members') else "down",
                    "desc": f"Logical Bundle ({po_data.get('protocol', 'LACP')})",
                    "speed": "Aggregated",
                    "vlan": "multiple",
                    "macs": []
                }

        if log_func:
            log_func(f"[{true_host}] Found {len(edges)} neighbor links")
            log_func(f"[{true_host}] Logging out from device...")
        conn.disconnect()
        conn = None
        if log_func:
            log_func(f"[{true_host}] Successfully logged out")

        return build_json(host, "success", {
            "true_host": true_host,
            "int_meta": int_meta,
            "interface_macs": interface_macs,
            "bundles": bundles,
            "vpcs": vpc_ids,
            "vpc_domain_id": vpc_domain_id,
            "vpc_details": vpc_details,
            "edges": edges,
            # v6.9.3: Unified logical interface registry naming
            "port_channels": port_channel_detail,
            "port_channel_detail": port_channel_detail,
            "vpc_structured": vpc_structured,
            "lacp_neighbors": lacp_neighbors,
            "nxos_version": nxos_version,
            "cdp_validation_map": cdp_validation_map,
            "overlay_collected": overlay_collected,
            "overlay_links": overlay_links,
            "overlay_note": ov.get('overlay_note') or '',
            "optics": optics,
            # Validation metadata
            "node_validation": {
                "vpc_nodes": ["VPC_Domain_" + str(vpc_domain_id)] if vpc_domain_id else [],
                "bundle_nodes": list(bundles.values()),
                "interface_nodes": list(int_meta.keys())
            }
        })
    except TopologyCancelled as e:
        if log_func:
            log_func(
                f"[{host}] Topology mapping cancelled by operator "
                "(between CLI; in-flight SSH is not killed)"
            )
        return build_json(host, "fail", {}, str(e))
    except Exception as e:
        if log_func:
            log_func(f"[{host}] Error during topology mapping: {str(e)}")
        return build_json(host, "fail", {}, str(e))
    finally:
        if conn:
            try:
                if log_func:
                    log_func(f"[{host}] Logging out (cleanup)...")
                conn.disconnect()
                if log_func:
                    log_func(f"[{host}] Logged out (cleanup)")
            except Exception:
                pass
