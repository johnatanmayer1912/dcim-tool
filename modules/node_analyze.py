import re
from .network_base import connect_device, build_json, resolve_hostname_from_prompt

def run(device, user, pwd, enb_pwd, target_node, log_func=None):
    host = device['host']
    dtype = device['device_type']
    results = []
    found_any = False
    conn = None
    
    try:
        if log_func:
            log_func(f"[{host}] Connecting for node analysis...")
        conn = connect_device(device, user, pwd, enb_pwd)
        true_host = resolve_hostname_from_prompt(conn, host)
        if log_func:
            log_func(f"[{true_host}] Successfully connected")
        
        neigh_cmd = "show lldp neighbors" if "juniper" in dtype.lower() else "show cdp neighbors"
        if "ios" in dtype.lower(): neigh_cmd = "show cdp neighbors"
        if "nxos" in dtype.lower(): neigh_cmd = "show cdp neighbors"
            
        out_neigh = conn.send_command(neigh_cmd)
        port_hits = []
        
        for line in out_neigh.splitlines():
            if target_node.lower() in line.lower():
                m = re.search(r'([Ee]th\d+/\d+|[Gg]i\d+/\d+|[Tt]e\d+/\d+|[Ff]a\d+/\d+|[Pp]o\d+)', line)
                if m: port_hits.append(m.group(1))
                else:
                    parts = line.split()
                    if len(parts) > 1: port_hits.append(parts[1])

        for port in set(port_hits):
            found_any = True
            if "juniper" in dtype.lower():
                st_cmd = f"show interfaces terse {port}"
            else:
                st_cmd = f"show interface {port} status"
                if "Invalid" in conn.send_command(st_cmd): st_cmd = f"show interface {port}"
            
            out_st = conn.send_command(st_cmd)
            is_up = "up" in out_st.lower() or "connected" in out_st.lower()
            status = "UP \u2705" if is_up else "DOWN \u274c"
            
            desc_cmd = f"show interfaces description | include {port}"
            if "juniper" in dtype.lower(): 
               p_base = port.split('.')[0]
               desc_cmd = f"show configuration interfaces {p_base} | display set"
            
            out_desc = conn.send_command(desc_cmd)
            desc = "No description"
            m_desc = re.search(r'description "(.*)"', out_desc) or re.search(r'description\s+(.*)', out_desc)
            if m_desc: desc = m_desc.group(1).strip()
            
            mac_count_cmd = f"show mac-address-table interface {port}"
            if "juniper" in dtype.lower(): 
                mac_count_cmd = f"show ethernet-switching table interface {port}"
            elif "nxos" in dtype.lower(): 
                mac_count_cmd = f"show mac address-table interface {port}"
            
            out_mac_cnt = conn.send_command(mac_count_cmd)
            mac_lines = [l for l in out_mac_cnt.splitlines() if re.search(r'[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}', l) or re.search(r'[0-9a-fA-F]{2}:[0-9a-fA-F]{2}', l)]
            
            results.append({
                "port": port,
                "status": status,
                "desc": desc,
                "macs": len(mac_lines),
                "first_mac": mac_lines[0].split()[1] if (mac_lines and len(mac_lines[0].split()) > 1) else 'Found'
            })
        
        if log_func:
            log_func(f"[{true_host}] Logging out from device...")
        conn.disconnect()
        conn = None
        if log_func:
            log_func(f"[{true_host}] Successfully logged out")
        return build_json(host, "success", {"true_host": true_host, "found": found_any, "ports": results})
    except Exception as e:
        error_msg = str(e).splitlines()[0] if str(e).splitlines() else str(e)
        if log_func:
            log_func(f"[{host}] ERROR: {error_msg}")
        return build_json(host, "fail", {"found": False}, error_msg)
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
