import platform, subprocess, sys
from .network_base import connect_device, build_json, resolve_hostname_from_prompt

def run(device, user, pwd, enb_pwd="", log_func=None):
    """Run connectivity check (ping + SSH) on a device with disconnect logging.
    
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
    conn = None
    
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    
    # Windows-specific subprocess flags to hide CMD popup
    if sys.platform == 'win32':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        creationflags = subprocess.CREATE_NO_WINDOW
    else:
        startupinfo = None
        creationflags = 0
    
    res = subprocess.run(
        ['ping', param, '1', '-w', '2000', host],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        startupinfo=startupinfo,
        creationflags=creationflags
    )
    
    if res.returncode != 0:
        if log_func:
            log_func(f"[{host}] Ping failed - device unreachable")
        return build_json(host, "fail", {"ping": False}, "Ping unreachable")
    
    if log_func:
        log_func(f"[{host}] Ping successful, attempting SSH connection...")
        
    try:
        conn = connect_device(device, user, pwd, enb_pwd, log_func=log_func)
        true_host = resolve_hostname_from_prompt(conn, host)
        if log_func:
            log_func(f"[{true_host}] SSH connection successful")
            log_func(f"[{true_host}] Logging out from device...")
        conn.disconnect()
        conn = None
        if log_func:
            log_func(f"[{true_host}] Successfully logged out")
        return build_json(host, "success", {"ping": True, "ssh": True, "device_type": device['device_type']})
    except Exception as e:
        error_msg = str(e).splitlines()[0] if str(e).splitlines() else str(e)
        if log_func:
            log_func(f"[{host}] SSH connection failed: {error_msg}")
        return build_json(host, "fail", {"ping": True, "ssh": False}, error_msg)
    finally:
        if conn:
            try:
                if log_func:
                    log_func(f"[{host}] Logging out (cleanup)...")
                conn.disconnect()
                if log_func:
                    log_func(f"[{host}] Logged out (cleanup)")
            except:
                pass
