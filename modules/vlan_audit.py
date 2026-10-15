from .network_base import connect_device, build_json, resolve_hostname_from_prompt
from modules.vlan_mgmt_production import _vlan_show_cmd

def run(device, user, pwd, enb_pwd="", log_func=None):
    """Run VLAN audit on a device with disconnect logging.
    
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
    dtype = device['device_type']
    conn = None
    
    try:
        if log_func:
            log_func(f"[{host}] Connecting to device...")
        conn = connect_device(device, user, pwd, enb_pwd)
        true_host = resolve_hostname_from_prompt(conn, host)
        if log_func:
            log_func(f"[{true_host}] Successfully connected")
        
        cmd = _vlan_show_cmd(dtype)
        if log_func:
            log_func(f"[{true_host}] Executing: {cmd}")
        out = conn.send_command(cmd)
        if log_func:
            log_func(f"[{true_host}] Command completed successfully")
        
        # Parse VLANs from output
        vlans = []
        for line in out.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith('-'):
                continue
            # Skip header lines
            low = stripped.lower()
            if low.startswith('vlan') or low.startswith('name') or low.startswith('----'):
                continue
            parts = stripped.split()
            if len(parts) >= 2:
                # Try first column as VLAN ID (Cisco format)
                try:
                    vlan_id = int(parts[0])
                    vlan_name = parts[1] if len(parts) > 1 else ""
                    vlans.append({"id": vlan_id, "name": vlan_name})
                    continue
                except ValueError:
                    pass
                # Try second column as VLAN ID (Juniper legacy format: name id)
                try:
                    vlan_id = int(parts[1])
                    vlan_name = parts[0]
                    vlans.append({"id": vlan_id, "name": vlan_name})
                except ValueError:
                    continue
        
        if log_func:
            log_func(f"[{true_host}] Found {len(vlans)} VLANs")
            log_func(f"[{true_host}] Logging out from device...")
        conn.disconnect()
        conn = None
        if log_func:
            log_func(f"[{true_host}] Successfully logged out")
        
        return build_json(host, "success", {"true_host": true_host, "output": out, "vlans": vlans})
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
