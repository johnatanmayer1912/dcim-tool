"""
modules/network_audit.py
------------------------
Hardware/OS audit: retrieves hostname, model, OS version, serial number,
and uptime from each device and returns a structured record for CSV export.

Supports: Cisco IOS, IOS-XE, NX-OS, Juniper JunOS.
"""
import re
from .network_base import connect_device, build_json, resolve_hostname_from_prompt


def run(device, user, pwd, enb_pwd="", log_func=None):
    """
    Run hardware/OS audit on a single device.

    Args:
        device:   Device dict {host, device_type, port, group}
        user:     SSH username
        pwd:      SSH password
        enb_pwd:  Enable/secret password (optional)
        log_func: Callable(str) for UI log streaming (optional)

    Returns:
        Standard JSON dict {device, status, data, error}
    """
    host = device['host']
    device_type = device['device_type']
    conn = None

    try:
        if log_func:
            log_func(f"[{host}] Connecting for network audit...")
        conn = connect_device(device, user, pwd, enb_pwd, log_func=log_func)
        true_host = resolve_hostname_from_prompt(conn, host)
        if log_func:
            log_func(f"[{true_host}] Connected — running show version...")

        ver_out = conn.send_command("show version")
        uptime_out = ""
        if "juniper" in device_type.lower():
            uptime_out = conn.send_command("show system uptime")

        record = {
            "Hostname"     : true_host,
            "Device Type"  : device_type,
            "Model"        : "Unknown",
            "OS Version"   : "Unknown",
            "Serial Number": "Unknown",
            "Uptime"       : "Unknown",
        }

        if "cisco" in device_type.lower() or "ios" in device_type.lower():
            m = re.search(r'uptime is (.*)', ver_out)
            if m: record["Uptime"] = m.group(1).strip()
            m = re.search(r'Version ([^,]+),', ver_out) or re.search(r'Cisco IOS.*?Version ([^\s]+),', ver_out)
            if m: record["OS Version"] = m.group(1).strip()
            m = re.search(r'Processor board ID (.*)', ver_out)
            if m: record["Serial Number"] = m.group(1).strip()
            m = re.search(r'cisco (.+?) processor', ver_out, re.IGNORECASE) or re.search(r'Hardware:\s+(.*)', ver_out)
            if m: record["Model"] = m.group(1).strip()

        elif "nxos" in device_type.lower():
            m = re.search(r'Kernel uptime is (.*)', ver_out)
            if m: record["Uptime"] = m.group(1).strip()
            m = re.search(r'system:\s+version (.*)', ver_out)
            if m: record["OS Version"] = m.group(1).strip()
            m = re.search(r'Processor Board ID\s+(.*)', ver_out)
            if m: record["Serial Number"] = m.group(1).strip()
            m = re.search(r'Hardware\s+(.*)', ver_out) or re.search(r'cisco (.*?) Chassis', ver_out)
            if m: record["Model"] = m.group(1).strip()

        elif "juniper" in device_type.lower():
            m = re.search(r'System booted:\s+(.*?)\s+\(', uptime_out) or re.search(r'up (.*?),', uptime_out)
            if m: record["Uptime"] = m.group(1).strip()
            m = re.search(r'Junos: (.*)', ver_out)
            if m: record["OS Version"] = m.group(1).strip()
            m = re.search(r'Model: (.*)', ver_out)
            if m: record["Model"] = m.group(1).strip()
            m = re.search(r'Serial Number: (.*)', ver_out)
            if m: record["Serial Number"] = m.group(1).strip()

        if log_func:
            log_func(f"[{true_host}] Audit complete — {record['Model']} / {record['OS Version']}")
            log_func(f"[{true_host}] Logging out from device...")
        conn.disconnect()
        conn = None
        if log_func:
            log_func(f"[{true_host}] Successfully logged out")
        return build_json(host, "success", {"record": record, "true_host": true_host})

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
