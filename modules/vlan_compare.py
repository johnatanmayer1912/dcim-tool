"""
modules/vlan_compare.py
-----------------------
Retrieve the VLAN database from a device for cross-device comparison.
Returns parsed (id, name, status) tuples via parse_vlan_output().

Used by adapters.run_vlan_compare() to build a global VLAN baseline
and identify devices missing VLANs present on other devices.
"""
import re
from .network_base import connect_device, build_json, resolve_hostname_from_prompt, parse_vlan_output


def run(device, user, pwd, enb_pwd="", log_func=None):
    """
    Retrieve and parse the VLAN database from a single device.

    Args:
        device:   Device dict {host, device_type, port, group}
        user:     SSH username
        pwd:      SSH password
        enb_pwd:  Enable/secret password (optional)
        log_func: Callable(str) for UI log streaming (optional)

    Returns:
        Standard JSON dict {device, status, data:{true_host, vlans}, error}
        vlans is a list of (vlan_id, vlan_name, status) tuples.
    """
    host = device['host']
    device_type = device['device_type']
    conn = None

    try:
        if log_func:
            log_func(f"[{host}] Connecting for VLAN compare...")
        conn = connect_device(device, user, pwd, enb_pwd)
        true_host = resolve_hostname_from_prompt(conn, host)
        if log_func:
            log_func(f"[{true_host}] Connected — retrieving VLAN database...")

        # Select the appropriate show command per platform
        if "nxos" in device_type.lower() or "ios" in device_type.lower():
            cmd = "show vlan brief"
        elif "juniper" in device_type.lower():
            cmd = "show vlans"
        else:
            cmd = "show vlan"

        output = conn.send_command(cmd)
        results = parse_vlan_output(output, device_type)

        if log_func:
            log_func(f"[{true_host}] Found {len(results)} VLANs")
            log_func(f"[{true_host}] Logging out from device...")
        conn.disconnect()
        conn = None
        if log_func:
            log_func(f"[{true_host}] Successfully logged out")
        return build_json(host, "success", {"true_host": true_host, "vlans": results})

    except Exception as e:
        error_msg = str(e).splitlines()[0] if str(e).splitlines() else str(e)
        if log_func:
            log_func(f"[{host}] ERROR: {error_msg}")
        return build_json(host, "fail", {}, error_msg)

    finally:
        # Always disconnect — prevents SSH session leaks on exception
        if conn:
            try:
                if log_func:
                    log_func(f"[{host}] Logging out (cleanup)...")
                conn.disconnect()
                if log_func:
                    log_func(f"[{host}] Logged out (cleanup)")
            except Exception:
                pass
