from .network_base import connect_device, build_json, resolve_hostname_from_connection
from utils.mac_utils import (
    normalize_mac_hex,
    cisco_search_terms,
    junos_search_terms,
    line_contains_mac,
    extract_junos_interface,
    mac_in_line,
    distinct_macs_matching_query,
    is_partial_mac_query,
    format_mac_for_display,
)
import re

_MAC_SAFE_PATTERN = re.compile(r'^[0-9a-fA-F.:_\-]{4,17}$')


def _validate_mac(mac):
    """Validate MAC address format to prevent command injection."""
    clean = mac.strip()
    if not _MAC_SAFE_PATTERN.match(clean):
        raise ValueError(f"Invalid MAC address format: '{clean}'")
    return clean


def _parse_mac_match_line(line, dtype):
    """Platform-specific VLAN/port extraction."""
    line = line.strip()
    if not line or line.lower().startswith(('vlan', 'mac', 'address', 'legend', '---', 'routing')):
        return None, None, False
    if not mac_in_line(line):
        return None, None, False

    parts = line.split()
    dtype_low = (dtype or '').lower()

    if 'juniper' in dtype_low:
        if 'srx' in dtype_low:
            for i, p in enumerate(parts):
                if mac_in_line(p) and i + 1 < len(parts):
                    return None, parts[i + 1], True
            return None, None, False

        port = extract_junos_interface(line)
        if not port:
            return None, None, False
        vlan = parts[0] if parts else None
        mac_pos = next((i for i, p in enumerate(parts) if mac_in_line(p)), -1)
        if mac_pos > 0:
            vlan = ' '.join(parts[:mac_pos])
        return vlan, port, True

    if len(parts) >= 3 and mac_in_line(parts[0]):
        # NX-OS / IOS-XR include output: MAC VLAN PORT
        return parts[1], parts[-1], True

    if len(parts) >= 3:
        port = parts[-1]
        vlan = parts[0]
        if vlan.isdigit() or vlan.lower() in ('all', 'cpu', '*'):
            return vlan, port, True
        if len(parts) >= 4:
            return vlan, port, True
    return None, None, False


def _build_mac_commands(dtype, target_mac):
    """Build ordered list of MAC search commands for the platform."""
    dtype_low = (dtype or '').lower()
    cmds = []

    if 'juniper' in dtype_low:
        if 'srx' in dtype_low:
            for term in junos_search_terms(target_mac):
                cmds.append(f"show arp | match {term}")
        else:
            for term in junos_search_terms(target_mac):
                cmds.append(f"show ethernet-switching table | match {term}")
            for term in junos_search_terms(target_mac):
                cmds.append(f"show ethernet-switching mac-ip-table | match {term}")
            for term in junos_search_terms(target_mac):
                cmds.append(f"show bridge mac-table | match {term}")
            cmds.append("show ethernet-switching table")
            cmds.append("show bridge mac-table")
    elif 'nxos' in dtype_low or 'iosxr' in dtype_low:
        for term in cisco_search_terms(target_mac):
            cmds.append(f"show mac address-table | include {term}")
    else:
        for term in cisco_search_terms(target_mac):
            cmds.append(f"show mac address-table | include {term}")

    return list(dict.fromkeys(cmds))


def _search_mac_on_device(conn, dtype, target_mac, log_func, true_host):
    """Run platform-appropriate MAC search with format fallbacks."""
    all_matches = []
    last_cmd = None

    for cmd in _build_mac_commands(dtype, target_mac):
        last_cmd = cmd
        if log_func:
            log_func(f"[{true_host}] Executing: {cmd}")
        out = conn.send_command(cmd)
        lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
        if not lines:
            continue

        is_full_table = cmd in (
            "show ethernet-switching table",
            "show bridge mac-table",
        )
        for line in lines:
            if is_full_table and not line_contains_mac(line, target_mac):
                continue
            if not is_full_table or line_contains_mac(line, target_mac):
                all_matches.append(line)

        for line in all_matches:
            v, p, ok = _parse_mac_match_line(line, dtype)
            if ok and p:
                distinct = distinct_macs_matching_query(all_matches, target_mac)
                if is_partial_mac_query(target_mac) and len(distinct) > 1:
                    return all_matches, v, p, False, last_cmd, True, distinct
                return all_matches, v, p, True, last_cmd, False, distinct

    distinct = distinct_macs_matching_query(all_matches, target_mac)
    ambiguous = is_partial_mac_query(target_mac) and len(distinct) > 1
    return all_matches, None, None, False, last_cmd, ambiguous, distinct


def run(device, user, pwd, enb_pwd, target_mac, log_func=None):
    """Run MAC address trace on a device with disconnect logging."""
    host = (device or {}).get('host', 'unknown')
    dtype = (device or {}).get('device_type', 'cisco_ios')
    conn = None

    try:
        target_mac = _validate_mac(target_mac)
        normalize_mac_hex(target_mac)

        if log_func:
            log_func(f"[{host}] Connecting to device...")
        conn = connect_device(device, user, pwd, enb_pwd)
        true_host = resolve_hostname_from_connection(
            conn, host, dtype, log_func=log_func, fetch_version=True,
        )
        if log_func:
            log_func(f"[{true_host}] Successfully connected")

        matches, vlan, port, found, cmd_used, ambiguous, distinct_macs = _search_mac_on_device(
            conn, dtype, target_mac, log_func, true_host,
        )
        resolved_mac = None
        if found and distinct_macs:
            resolved_mac = format_mac_for_display(distinct_macs[0])
        elif found and matches:
            from utils.mac_utils import extract_macs_from_line
            for line in matches:
                extracted = extract_macs_from_line(line)
                if extracted:
                    distinct_macs = list(dict.fromkeys(distinct_macs + extracted))
                    resolved_mac = format_mac_for_display(extracted[0])
                    break
        if log_func and cmd_used:
            log_func(f"[{true_host}] Command completed successfully")

        if ambiguous and distinct_macs:
            display_macs = [format_mac_for_display(m) for m in distinct_macs[:8]]
            msg = (
                f"Partial MAC '{target_mac}' matches {len(distinct_macs)} distinct address(es) "
                f"on {true_host}: {', '.join(display_macs)}"
                + (" …" if len(distinct_macs) > 8 else "")
                + " — refine your search to a full MAC."
            )
            if log_func:
                log_func(f"[{true_host}] [AMBIGUOUS] {msg}")
            conn.disconnect()
            conn = None
            hop = {
                "hop_index": 1,
                "device_ip": host,
                "hostname": true_host,
                "found": False,
                "ambiguous": True,
                "distinct_macs": distinct_macs,
                "vlan": None,
                "port": None,
                "status": "ambiguous",
                "matches": matches,
                "message": msg,
            }
            return build_json(host, "success", {
                "true_host": true_host,
                "matches": matches,
                "found": False,
                "ambiguous": True,
                "distinct_macs": distinct_macs,
                "ambiguous_message": msg,
                "port": None,
                "vlan": None,
                "path_hops": [hop],
            })

        if log_func:
            log_func(f"[{true_host}] MAC {target_mac} {'found' if found else 'not found'}")
            log_func(f"[{true_host}] Logging out from device...")
        conn.disconnect()
        conn = None
        if log_func:
            log_func(f"[{true_host}] Successfully logged out")

        hop = {
            "hop_index": 1,
            "device_ip": host,
            "hostname": true_host,
            "found": found,
            "vlan": vlan,
            "port": port,
            "status": "found" if found else "not_found",
            "matches": matches,
            "distinct_macs": distinct_macs or [],
            "resolved_mac": resolved_mac,
        }
        return build_json(host, "success", {
            "true_host": true_host,
            "matches": matches,
            "found": found,
            "port": port,
            "vlan": vlan,
            "distinct_macs": distinct_macs or [],
            "resolved_mac": resolved_mac,
            "path_hops": [hop],
        })
    except Exception as e:
        error_msg = str(e).splitlines()[0] if str(e).splitlines() else str(e)
        if log_func:
            log_func(f"[{host}] Error: {error_msg}")
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
