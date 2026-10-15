import re
from .network_base import connect_device, build_json, resolve_hostname_from_prompt

def run(device, user, pwd, enb_pwd, filter_str, log_func=None):
    """Run interface check on a device with disconnect logging.
    
    Args:
        device: Device dict with host, device_type, port
        user: Username
        pwd: Password
        enb_pwd: Enable password (optional)
        filter_str: Interface filter string (optional)
        log_func: Logging function (optional)
    
    Returns:
        JSON response dict
    """
    host = device['host']
    dtype = device['device_type']
    conn = None
    
    try:
        if log_func:
            log_func(f"[{host}] Connecting to device...")
        conn = connect_device(device, user, pwd, enb_pwd, log_func=log_func)
        true_host = resolve_hostname_from_prompt(conn, host)
        if log_func:
            log_func(f"[{true_host}] Successfully connected")
        
        if "juniper" in dtype.lower():
            cmd_status = "show interfaces terse"
        elif "nxos" in dtype.lower():
            cmd_status = "show interface status"
        else:
            cmd_status = "show ip interface brief"
        
        if log_func:
            log_func(f"[{true_host}] Executing: {cmd_status}")
        out_status = conn.send_command(cmd_status)
        if log_func:
            log_func(f"[{true_host}] Command completed successfully")
        
        desc_map = {}
        out_desc = ""
        if "juniper" in dtype.lower():
            cmd_junos_conf = "show configuration interfaces | display set | match description"
            if log_func:
                log_func(f"[{true_host}] Executing: {cmd_junos_conf}")
            out_junos_conf = conn.send_command(cmd_junos_conf)
            for line in out_junos_conf.splitlines():
                m_p = re.search(r'set interfaces (\S+) description "(.*)"', line)
                if m_p: desc_map[m_p.group(1)] = m_p.group(2)
                m_l = re.search(r'set interfaces (\S+) unit (\d+) description "(.*)"', line)
                if m_l: desc_map[f"{m_l.group(1)}.{m_l.group(2)}"] = m_l.group(3)
            out_desc = conn.send_command("show interfaces description")
        else:
            out_desc = conn.send_command("show interfaces description")
        
        if log_func:
            log_func(f"[{true_host}] Logging out from device...")
        conn.disconnect()
        conn = None
        if log_func:
            log_func(f"[{true_host}] Successfully logged out")
        
        return build_json(host, "success", {
            "true_host": true_host,
            "status_output": out_status,
            "desc_output": out_desc,
            "desc_map": desc_map,
            "filter_str": filter_str
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
            except:
                pass
