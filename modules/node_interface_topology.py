"""
modules/node_interface_topology.py
-----------------------------------
Per-node interface topology data collector.

v6.2.0 Enhancements:
  - Collects speed/duplex from 'show interfaces' for richer display
  - Collects VLAN assignment from 'show interface status'
  - Returns structured data for the improved interface map in adapters.py
"""
import re
from .network_base import connect_device, build_json, resolve_hostname_from_prompt
from utils.juniper_iface import (
    collect_juniper_lag_detail,
    apply_juniper_bundles,
    resolve_junos_iface_key,
    split_junos_unit,
)
from utils.mac_utils import extract_junos_interface


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


def _parse_speed_duplex(line):
    """Extract speed and duplex from a 'show interface status' line."""
    speed = ""
    duplex = ""
    # Speed patterns — check longer/more specific patterns first
    # Order matters: 10G before 10, 100G before 100, a-1g before 1000
    if re.search(r'\ba-1g\b', line, re.IGNORECASE) or re.search(r'\b1000\b', line):
        speed = '1G'
    elif re.search(r'\b10G\b', line, re.IGNORECASE) or re.search(r'\b10000\b', line):
        speed = '10G'
    elif re.search(r'\b100G\b', line, re.IGNORECASE) or re.search(r'\b100000\b', line):
        speed = '100G'
    elif re.search(r'\b40G\b', line, re.IGNORECASE) or re.search(r'\b40000\b', line):
        speed = '40G'
    elif re.search(r'\b25G\b', line, re.IGNORECASE) or re.search(r'\b25000\b', line):
        speed = '25G'
    elif re.search(r'\ba-100\b|\b100\b', line, re.IGNORECASE):
        speed = '100M'
    elif re.search(r'\ba-10\b|\b10\b', line, re.IGNORECASE):
        speed = '10M'
    elif re.search(r'\bauto\b', line, re.IGNORECASE):
        speed = 'Auto'
    # Duplex patterns
    if re.search(r'\ba-full\b|full', line, re.IGNORECASE):
        duplex = 'Full'
    elif re.search(r'\ba-half\b|half', line, re.IGNORECASE):
        duplex = 'Half'
    return speed, duplex


def _parse_vlan(line):
    """Extract VLAN from a 'show interface status' line."""
    # Typical format: Gi0/1  desc  connected  100  a-full  a-1g  10/100/1000BaseTX
    parts = line.split()
    for p in parts:
        if p.isdigit() and 1 <= int(p) <= 4094:
            return p
        if p.lower() in ('trunk', 'routed', 'access'):
            return p
    return ""


def run(device, user, pwd, enb_pwd="", log_func=None):
    """
    Collect per-node interface data for the interface topology map.

    v6.2.0: Returns speed, duplex, VLAN per interface for richer visualization.
    """
    host = device['host']
    dtype = device['device_type']
    conn = None
    try:
        if log_func:
            log_func(f"[{host}] Connecting for interface topology...")
        conn = connect_device(device, user, pwd, enb_pwd)
        true_host = resolve_hostname_from_prompt(conn, host)
        if log_func:
            log_func(f"[{true_host}] Successfully connected")

        int_meta = {}

        # Status command
        stat_cmd = "show interface status"
        if "juniper" in dtype.lower():
            stat_cmd = "show interfaces terse"
        stat_out = conn.send_command(stat_cmd)

        # Description command
        desc_out = conn.send_command("show interfaces description")

        # Parse descriptions — handle both formats:
        # Format 1 (IOS): "Gi0/1  up  up  Description text"
        # Format 2 (IOS desc cmd): "Interface  Status  Protocol  Description"
        #   Gi0/1    up       up        Uplink to Core
        # The key insight: description is the LAST field(s) after status columns.
        # We use a flexible parser that handles both.
        desc_regex = re.compile(
            r'^(\S+)\s+'
            r'(up|down|connected|admin\s+down|administratively\s+down)\s+'
            r'(up|down|proto\s+up|proto\s+down)?\s*(.*)',
            re.IGNORECASE
        )
        # Also handle the simpler "show interfaces description" format:
        # Interface              Status     Protocol   Description
        # GigabitEthernet0/1     up         up         Uplink to Core-SW
        desc_simple_regex = re.compile(
            r'^(\S+)\s+(up|down|admin-down|admin down)\s+(up|down)\s+(.*)',
            re.IGNORECASE
        )
        for line in desc_out.splitlines():
            line_stripped = line.strip()
            if not line_stripped or any(x in line_stripped for x in [
                '--', 'Interface', 'Status', 'Description', 'Admin', 'Protocol'
            ]):
                continue
            # Try the full regex first
            m = desc_regex.match(line_stripped)
            if not m:
                # Try the simpler format
                m = desc_simple_regex.match(line_stripped)
            if m:
                in_name = norm_int(m.group(1))
                # Description is always the last capture group
                desc_content = (m.group(4) or m.group(m.lastindex) or "").strip()
                # Strip common placeholder values
                if desc_content.lower() in ('--', 'none', 'n/a', ''):
                    desc_content = ""
                int_meta[in_name] = {
                    "desc": desc_content,
                    "op_status": "unknown",
                    "admin_status": "unknown",
                    "speed": "",
                    "duplex": "",
                    "vlan": "",
                }
            else:
                # Last resort: split on 2+ spaces (tabular format)
                # "GigabitEthernet0/1     up         up         Uplink to Core"
                parts_tab = re.split(r'\s{2,}', line_stripped)
                if len(parts_tab) >= 2:
                    in_name = norm_int(parts_tab[0])
                    if in_name and len(in_name) > 1:
                        # Description is the last column if 4+ columns, else empty
                        desc_content = parts_tab[-1].strip() if len(parts_tab) >= 4 else ""
                        if desc_content.lower() in ('up', 'down', '--', 'none', 'n/a'):
                            desc_content = ""
                        if in_name not in int_meta:
                            int_meta[in_name] = {
                                "desc": desc_content,
                                "op_status": "unknown",
                                "admin_status": "unknown",
                                "speed": "",
                                "duplex": "",
                                "vlan": "",
                            }

        # Parse status (Juniper)
        if "juniper" in dtype.lower():
            for line in stat_out.splitlines():
                if not line or 'Interface' in line:
                    continue
                parts = line.split()
                if len(parts) >= 3:
                    pname = norm_int(parts[0])
                    if pname not in int_meta:
                        int_meta[pname] = {
                            "desc": "-", "op_status": "unknown",
                            "admin_status": "unknown",
                            "speed": "", "duplex": "", "vlan": "",
                        }
                    int_meta[pname]["admin_status"] = parts[1].lower()
                    int_meta[pname]["op_status"] = parts[2].lower()
        else:
            # Cisco IOS / NXOS
            for line in stat_out.splitlines():
                line = line.strip()
                if not line or line.startswith('--') or line.startswith('Interface') or line.startswith('Port'):
                    continue
                parts = line.split()
                if len(parts) >= 3:
                    pname = norm_int(parts[0])
                    if pname not in int_meta:
                        int_meta[pname] = {
                            "desc": "-", "op_status": "unknown",
                            "admin_status": "unknown",
                            "speed": "", "duplex": "", "vlan": "",
                        }
                    l_low = line.lower()
                    if "disabled" in l_low:
                        int_meta[pname]["admin_status"] = "down"
                        int_meta[pname]["op_status"] = "down"
                    elif "notconnect" in l_low:
                        int_meta[pname]["admin_status"] = "up"
                        int_meta[pname]["op_status"] = "down"
                    elif "connected" in l_low:
                        int_meta[pname]["admin_status"] = "up"
                        int_meta[pname]["op_status"] = "up"
                    elif "err-disabled" in l_low:
                        int_meta[pname]["admin_status"] = "up"
                        int_meta[pname]["op_status"] = "err-disabled"
                    else:
                        int_meta[pname]["admin_status"] = "up"
                        int_meta[pname]["op_status"] = "unknown"

                    # v6.2.0: Extract speed, duplex, VLAN from status line
                    speed, duplex = _parse_speed_duplex(line)
                    vlan = _parse_vlan(line)
                    int_meta[pname]["speed"] = speed
                    int_meta[pname]["duplex"] = duplex
                    int_meta[pname]["vlan"] = vlan

        # Juniper: correlate physical ports with ae bundles before MAC mapping
        juniper_bundles = {}
        if "juniper" in dtype.lower():
            lag_detail = collect_juniper_lag_detail(conn)
            juniper_bundles = apply_juniper_bundles(int_meta, lag_detail)

        # MAC addresses
        mac_cmd = "show mac-address-table"
        if "juniper" in dtype.lower():
            mac_cmd = "show ethernet-switching table"
        elif "nxos" in dtype.lower():
            mac_cmd = "show mac address-table"
        mac_out = conn.send_command(mac_cmd)
        if "juniper" in dtype.lower() and (
            not mac_out.strip() or "error:" in mac_out.lower()[:80]
        ):
            mac_out = conn.send_command("show bridge mac-table")

        interface_macs = {}
        is_juniper = "juniper" in dtype.lower()
        for line in mac_out.splitlines():
            m_mac = re.search(
                r'([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})'
                r'|([0-9a-fA-F]{2}[:.-][0-9a-fA-F]{2}[:.-][0-9a-fA-F]{2}'
                r'[:.-][0-9a-fA-F]{2}[:.-][0-9a-fA-F]{2}[:.-][0-9a-fA-F]{2})',
                line
            )
            if not m_mac:
                continue
            mac_addr = m_mac.group(0)
            parts = re.split(r'\s+', line.strip())
            if len(parts) < 3:
                continue

            # Build a set of candidate interface names from this line.
            # The interface is typically the LAST token, but we check all tokens.
            # Priority: exact norm_int match > parent port-channel match > substring
            matched_im = None

            # Collect all candidate interface tokens (skip MAC, VLAN numbers, keywords)
            skip_keywords = {'dynamic', 'static', 'learned', 'sticky', 'forward',
                             'secure', 'drop', 'system', 'self', 'igmp', 'mcast'}
            candidates = []
            for p in reversed(parts):
                # Skip the MAC address itself
                if re.match(r'([0-9a-fA-F]{4}\.){2}[0-9a-fA-F]{4}', p):
                    continue
                if re.match(r'([0-9a-fA-F]{2}[:.-]){5}[0-9a-fA-F]{2}', p):
                    continue
                # Skip pure VLAN numbers
                if re.match(r'^\d+$', p):
                    continue
                if p.lower() in skip_keywords:
                    continue
                candidates.append(p)

            for cand in candidates:
                norm_cand = norm_int(cand)
                if not norm_cand:
                    continue

                if is_juniper:
                    junos_cand = extract_junos_interface(cand) or cand
                    matched_im = resolve_junos_iface_key(junos_cand, int_meta.keys())
                    if not matched_im:
                        phys, _ = split_junos_unit(junos_cand)
                        matched_im = resolve_junos_iface_key(phys, int_meta.keys())
                    if matched_im:
                        break
                    continue

                # 1. Exact match (case-insensitive)
                for im in int_meta.keys():
                    if im.lower() == norm_cand.lower():
                        matched_im = im
                        break
                if matched_im:
                    break

                # 2. Port-channel / sub-interface suffix (Gi0/1.100 -> Gi0/1)
                if not matched_im:
                    base_cand = norm_cand.split('.')[0]
                    for im in int_meta.keys():
                        if im.lower() == base_cand.lower():
                            matched_im = im
                            break
                if matched_im:
                    break

            # Juniper: MAC on ae0.0 — attach to ae bundle and member ports
            if is_juniper and matched_im:
                ae_target = int_meta.get(matched_im, {}).get('ae_bundle')
                if not ae_target and matched_im in juniper_bundles.values():
                    ae_target = matched_im
                if ae_target and ae_target in int_meta:
                    matched_im = ae_target

            if matched_im:
                if matched_im not in interface_macs:
                    interface_macs[matched_im] = []
                if mac_addr not in interface_macs[matched_im]:
                    interface_macs[matched_im].append(mac_addr)

        # v6.7.5: Traffic statistics collection
        # Get interface traffic rates for live interfaces
        traffic_cmd = "show interface"
        if "juniper" in dtype.lower():
            traffic_cmd = "show interface detail"
        elif "nxos" in dtype.lower():
            traffic_cmd = "show interface"
        
        try:
            traffic_out = conn.send_command(traffic_cmd)
            current_interface = None
            for line in traffic_out.splitlines():
                line = line.strip()
                # Detect interface header (e.g., "GigabitEthernet0/1 is up")
                intf_header = re.match(r'^(\S+)(?:\s+|\.)is\s+(up|down|administratively\s+down)', line, re.IGNORECASE)
                if intf_header:
                    current_interface = norm_int(intf_header.group(1))
                    continue
                
                # Parse input rate
                if current_interface and current_interface in int_meta:
                    # NXOS/IOS pattern: "5 minute input rate 1000 bits/sec" or "input rate 1000 bits/sec"
                    in_match = re.search(r'(?:\d+\s+minute\s+)?input\s+rate\s+(\d+)\s+bits/sec', line, re.IGNORECASE)
                    if in_match:
                        int_meta[current_interface]["input_rate"] = int(in_match.group(1))
                    
                    # NXOS/IOS pattern: "5 minute output rate 1000 bits/sec"
                    out_match = re.search(r'(?:\d+\s+minute\s+)?output\s+rate\s+(\d+)\s+bits/sec', line, re.IGNORECASE)
                    if out_match:
                        int_meta[current_interface]["output_rate"] = int(out_match.group(1))
                    
                    # Also try absolute counters for newer devices
                    # "  Input: 1000 packets, 10000 bytes"
                    bytes_in = re.search(r'Input.*?(\d+)\s+bytes', line, re.IGNORECASE)
                    if bytes_in:
                        int_meta[current_interface]["input_bytes"] = int(bytes_in.group(1))
                    
                    bytes_out = re.search(r'Output.*?(\d+)\s+bytes', line, re.IGNORECASE)
                    if bytes_out:
                        int_meta[current_interface]["output_bytes"] = int(bytes_out.group(1))
        except Exception as e:
            # Traffic stats are optional, continue without them
            pass
        
        if log_func:
            log_func(f"[{true_host}] Logging out from device...")
        conn.disconnect()
        conn = None
        if log_func:
            log_func(f"[{true_host}] Successfully logged out")

        return build_json(host, "success", {
            "true_host": true_host,
            "int_meta": int_meta,
            "interface_macs": interface_macs,
            "bundles": juniper_bundles,
        })
    except Exception as e:
        error_msg = str(e).splitlines()[0] if str(e).splitlines() else str(e)
        if log_func:
            log_func(f"[{host}] ERROR: {error_msg}")
        return build_json(host, "fail", {}, error_msg)
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
