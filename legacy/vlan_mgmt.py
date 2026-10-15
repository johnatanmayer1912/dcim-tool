from .network_base import connect_permissive, build_json, parse_vlan_output


def _is_junos_els(conn, dtype):
    """Detect if Juniper device uses ELS (Enhanced Layer 2 Software) syntax.
    
    ELS devices: EX2300, EX3400, EX4300, QFX series (JUNOS 15.1+)
    Non-ELS: EX2200, EX3300, EX4200, EX4500 (older JUNOS)
    
    Returns True if ELS, False if non-ELS or unknown.
    """
    if "juniper" not in dtype.lower():
        return False
    
    try:
        # Try ELS command first - if it works without error, it's ELS
        test_output = conn.send_command("show vlans | match default-switch")
        if "default-switch" in test_output or "Routing instance" in test_output:
            return True
        
        # Check for ELS-only features in configuration
        config_test = conn.send_command('show configuration vlans | display set | match "default-switch"', 
                                       expect_string=r".*[>#].*", delay_factor=2)
        if "default-switch" in config_test:
            return True
            
        # Check device model from LLDP or system info (if available)
        model_check = conn.send_command("show version | match model")
        if any(model in model_check.lower() for model in ['ex2300', 'ex3400', 'ex4300', 'qfx']):
            return True
        if any(model in model_check.lower() for model in ['ex2200', 'ex3300', 'ex4200', 'ex4500']):
            return False
            
    except Exception:
        pass
    
    # Default to ELS for newer JUNOS versions, non-ELS for older
    return True  # Safer default for modern deployments


def _get_junos_vlan_syntax(conn, dtype):
    """Determine whether to use ELS or non-ELS VLAN syntax.
    
    Returns tuple: (config_syntax, show_syntax)
    - ELS: ('set vlans', 'show vlans')
    - Non-ELS: ('set ethernet-switching vlan', 'show ethernet-switching vlan')
    """
    if _is_junos_els(conn, dtype):
        return ('set vlans', 'show vlans')
    else:
        return ('set ethernet-switching vlan', 'show ethernet-switching vlan')


def _vlan_show_cmd(dtype):
    dt = (dtype or "").lower()
    if "juniper" in dt:
        return "show vlans"
    if "nxos" in dt or "iosxr" in dt:
        return "show vlan"
    return "show vlan brief"


def _run_post_check(conn, dtype, vid):
    verify_output = conn.send_command(_vlan_show_cmd(dtype))
    parsed = parse_vlan_output(verify_output, dtype)
    exists = any(str(v[0]) == str(vid) for v in parsed)
    return {"vlan_exists": exists, "vlan_count_seen": len(parsed), "show_cmd": _vlan_show_cmd(dtype)}


def get_prechange_snapshot(device, user, pwd, enb_pwd):
    host = device["host"]
    dtype = device["device_type"]
    try:
        conn = connect_permissive(device, user, pwd, enb_pwd)
        if "juniper" in dtype.lower():
            snap_cmd = "show configuration vlans | display set"
        else:
            snap_cmd = "show running-config | section vlan"
        snapshot = conn.send_command(snap_cmd)
        conn.disconnect()
        return build_json(host, "success", {"snapshot_cmd": snap_cmd, "snapshot": snapshot})
    except Exception as e:
        return build_json(host, "fail", {}, str(e).splitlines()[0] if str(e).splitlines() else str(e))


def add_vlan(device, user, pwd, enb_pwd, vid, vname, dry_run=False):
    try:
        conn = connect_permissive(device, user, pwd, enb_pwd)
        dtype = device["device_type"]
        if "juniper" in dtype.lower():
            # Detect ELS vs non-ELS and use appropriate syntax
            set_syntax, show_syntax = _get_junos_vlan_syntax(conn, dtype)
            if "ethernet-switching" in set_syntax:
                # Non-ELS: set ethernet-switching vlan <name> vlan-id <id>
                cmds = [f"{set_syntax} {vname} vlan-id {vid}"]
            else:
                # ELS: set vlans <name> vlan-id <id>
                cmds = [f"{set_syntax} {vname} vlan-id {vid}"]
            if not dry_run:
                conn.send_config_set(cmds, exit_config_mode=False)
                conn.commit()
                conn.exit_config_mode()
        else:
            cmds = [f"vlan {vid}"]
            if vname:
                cmds.append(f"name {vname}")
            if not dry_run:
                conn.send_config_set(cmds)
        post_check = _run_post_check(conn, dtype, vid) if not dry_run else {"skipped": True}
        conn.disconnect()
        return build_json(device["host"], "success", {"commands": cmds, "dry_run": dry_run, "post_check": post_check})
    except Exception as e:
        return build_json(device["host"], "fail", {}, str(e).splitlines()[0] if str(e).splitlines() else str(e))


def rename_vlan(device, user, pwd, enb_pwd, vid, vname, dry_run=False):
    try:
        conn = connect_permissive(device, user, pwd, enb_pwd)
        dtype = device["device_type"]
        if "juniper" in dtype.lower():
            conn.disconnect()
            return build_json(device["host"], "fail", {}, "Rename requires delete/add on Junos. Skipping.")
        else:
            cmds = [f"vlan {vid}", f"name {vname}"]
            if not dry_run:
                conn.send_config_set(cmds)
            post_check = _run_post_check(conn, dtype, vid) if not dry_run else {"skipped": True}
            conn.disconnect()
            return build_json(device["host"], "success", {"commands": cmds, "dry_run": dry_run, "post_check": post_check})
    except Exception as e:
        return build_json(device["host"], "fail", {}, str(e).splitlines()[0] if str(e).splitlines() else str(e))


def delete_vlan(device, user, pwd, enb_pwd, vid, dry_run=False):
    try:
        conn = connect_permissive(device, user, pwd, enb_pwd)
        dtype = device["device_type"]
        if "juniper" in dtype.lower():
            # Get VLAN name from ID first (required for JUNOS deletion)
            set_syntax, show_syntax = _get_junos_vlan_syntax(conn, dtype)
            vlan_out = conn.send_command(f"{show_syntax} | display set")
            
            # Parse to find VLAN name by ID
            import re
            vlan_name = None
            for line in vlan_out.splitlines():
                # Look for pattern: set vlans VLAN-NAME vlan-id X or set ethernet-switching vlan VLAN-NAME vlan-id X
                match = re.search(rf"{re.escape(set_syntax)}\s+(\S+)\s+vlan-id\s+{vid}\b", line)
                if match:
                    vlan_name = match.group(1)
                    break
            
            if not vlan_name:
                conn.disconnect()
                return build_json(device["host"], "fail", {}, f"VLAN {vid} not found on JUNOS device.")
            
            # Delete using appropriate syntax
            if "ethernet-switching" in set_syntax:
                cmds = [f"delete {set_syntax} {vlan_name}"]
            else:
                cmds = [f"delete {set_syntax} {vlan_name}"]
            
            if not dry_run:
                conn.send_config_set(cmds, exit_config_mode=False)
                conn.commit()
                conn.exit_config_mode()
            
            post_check_raw = _run_post_check(conn, dtype, vid) if not dry_run else {"skipped": True}
            post_check = dict(post_check_raw)
            if not dry_run:
                post_check["vlan_removed"] = not post_check_raw.get("vlan_exists", True)
            conn.disconnect()
            return build_json(device["host"], "success", {"commands": cmds, "dry_run": dry_run, "post_check": post_check})
        else:
            cmds = [f"no vlan {vid}"]
            if not dry_run:
                conn.send_config_set(cmds)
            post_check_raw = _run_post_check(conn, dtype, vid) if not dry_run else {"skipped": True}
            post_check = dict(post_check_raw)
            if not dry_run:
                post_check["vlan_removed"] = not post_check_raw.get("vlan_exists", True)
            conn.disconnect()
            return build_json(device["host"], "success", {"commands": cmds, "dry_run": dry_run, "post_check": post_check})
    except Exception as e:
        return build_json(device["host"], "fail", {}, str(e).splitlines()[0] if str(e).splitlines() else str(e))
