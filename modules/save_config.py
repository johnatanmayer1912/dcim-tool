"""
modules/save_config.py
----------------------
Persist the running configuration to startup-config (Cisco) or
commit the candidate configuration (Juniper).

Cisco IOS/IOS-XE: write memory
Cisco NX-OS:      copy running-config startup-config
Juniper JunOS:    commit
"""
from .network_base import connect_device, build_json, resolve_hostname_from_prompt


def _save_cisco(conn, device_type):
    """Send the appropriate save command for Cisco platforms."""
    dtype = (device_type or "").lower()
    # NX-OS uses 'copy running-config startup-config'; IOS uses 'write memory'
    cmd = "copy running-config startup-config" if "nxos" in dtype else "write memory"
    out = conn.send_command_timing(cmd, strip_prompt=False, strip_command=False)

    # Handle interactive confirmation prompts (e.g. "Destination filename [startup-config]?")
    if "destination filename" in out.lower() or "[yes/no]" in out.lower():
        out += conn.send_command_timing("\n", strip_prompt=False, strip_command=False)

    return out


def _save_juniper(conn):
    """Commit the candidate configuration on Juniper."""
    conn.config_mode()
    out = conn.commit()
    conn.exit_config_mode()
    return str(out)


def run(device, user, pwd, enb_pwd="", log_func=None):
    """
    Save/commit device configuration.

    Args:
        device:   Device dict {host, device_type, port, group}
        user:     SSH username
        pwd:      SSH password
        enb_pwd:  Enable/secret password (optional)
        log_func: Callable(str) for UI log streaming (optional)

    Returns:
        Standard JSON dict {device, status, data:{saved, save_output}, error}
    """
    host = device["host"]
    dtype = device["device_type"]
    conn = None

    try:
        if log_func:
            log_func(f"[{host}] Connecting to save config...")
        conn = connect_device(device, user, pwd, enb_pwd)
        true_host = resolve_hostname_from_prompt(conn, host)
        if log_func:
            log_func(f"[{true_host}] Connected — saving configuration...")

        if "juniper" in dtype.lower():
            output = _save_juniper(conn)
        else:
            output = _save_cisco(conn, dtype)

        if log_func:
            log_func(f"[{true_host}] Configuration saved successfully")
            log_func(f"[{true_host}] Logging out from device...")
        conn.disconnect()
        conn = None
        if log_func:
            log_func(f"[{true_host}] Successfully logged out")
        return build_json(host, "success", {
            "save_output": output,
            "saved"      : True,
            "device_type": dtype,
            "true_host"  : true_host,
        })

    except Exception as e:
        error_msg = str(e).splitlines()[0] if str(e).splitlines() else str(e)
        if log_func:
            log_func(f"[{host}] ERROR saving config: {error_msg}")
        return build_json(host, "fail", {"saved": False, "device_type": dtype}, error_msg)

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
