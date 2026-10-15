"""
modules/config_backup.py
------------------------
Pull running configuration from a device and return it as a string.
The adapter layer (adapters.py) handles writing to disk.

Supports: Cisco IOS/NX-OS (show running-config) and Juniper JunOS
          (show configuration | display set).
"""
from .network_base import connect_device, build_json, resolve_hostname_from_prompt


def run(device, user, pwd, enb_pwd, filt, log_func=None):
    """
    Retrieve running configuration from a single device.

    Args:
        device:   Device dict {host, device_type, port, group}
        user:     SSH username
        pwd:      SSH password
        enb_pwd:  Enable/secret password (optional)
        filt:     Optional filter string appended to the show command
        log_func: Callable(str) for UI log streaming (optional)

    Returns:
        Standard JSON dict {device, status, data:{config}, error}
    """
    host = device['host']
    dtype = device['device_type']
    conn = None

    try:
        if log_func:
            log_func(f"[{host}] Connecting for config backup...")
        conn = connect_device(device, user, pwd, enb_pwd)
        true_host = resolve_hostname_from_prompt(conn, host)
        if log_func:
            log_func(f"[{true_host}] Connected — pulling running config...")

        if "juniper" in dtype.lower():
            cmd = "show configuration | display set"
            if filt:
                cmd += f" | match {filt}"
        else:
            cmd = "show running-config"
            if filt:
                cmd += f" | {filt}"

        out = conn.send_command(cmd)
        if log_func:
            log_func(f"[{true_host}] Config retrieved ({len(out)} chars)")

        conn.disconnect()
        conn = None
        return build_json(host, "success", {"config": out, "true_host": true_host})

    except Exception as e:
        error_msg = str(e).splitlines()[0] if str(e).splitlines() else str(e)
        if log_func:
            log_func(f"[{host}] ERROR: {error_msg}")
        return build_json(host, "fail", {}, error_msg)

    finally:
        # Always disconnect — prevents SSH session leaks on exception
        if conn:
            try:
                conn.disconnect()
            except Exception:
                pass
