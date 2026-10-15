"""
modules/vlan_mgmt_production.py
------------------------------
Production-grade VLAN management with idempotency, validation, and pre-change backup.

This module extends the base vlan_mgmt.py with enterprise features:
- Idempotent operations (no duplicate changes)
- Pre-change validation
- Config state tracking
- Pre-change backup for manual restore (automated rollback removed v6.5.4 — see utils/restore_guide.py)
- Comprehensive logging
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import time

# CRITICAL: Install telnetlib compatibility for Python 3.13+
import sys
try:
    import telnetlib
except ImportError:
    import telnetlib_compat  # noqa: F401

# v6.3.0: Ensure project root is on sys.path for absolute imports
import os as _os, sys as _sys
_proj_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _proj_root not in _sys.path:
    _sys.path.insert(0, _proj_root)
if getattr(_sys, 'frozen', False):
    _exe_internal = getattr(_sys, '_MEIPASS', None)
    if _exe_internal and _exe_internal not in _sys.path:
        _sys.path.insert(0, _exe_internal)

from modules.network_base import connect_device, build_json, parse_vlan_output
from utils.structured_logger import get_logger, OperationType, ConfigState, create_legacy_adapter
from utils.config_backup_system import get_backup_system
from modules.save_config import run as save_config_run
import re


def _is_ios_xr(dtype: str) -> bool:
    """True for Cisco IOS-XR device_type variants (G-006 first-class)."""
    dt = (dtype or "").lower()
    return any(tag in dt for tag in ('iosxr', 'ios_xr', 'cisco_xr', 'ios-xr'))


def _vlan_show_cmd(dtype: str) -> str:
    """Get the appropriate VLAN show command for device type."""
    dt = (dtype or "").lower()
    if "juniper" in dt:
        return "show vlans"
    if "nxos" in dt or _is_ios_xr(dt):
        return "show vlan"
    return "show vlan brief"


def _is_junos_els(conn, dtype: str) -> bool:
    """Detect Juniper ELS vs non-ELS VLAN syntax."""
    if "juniper" not in (dtype or "").lower():
        return False
    try:
        test_output = conn.send_command("show vlans | match default-switch")
        if "default-switch" in test_output or "Routing instance" in test_output:
            return True
        config_test = conn.send_command(
            'show configuration vlans | display set | match "default-switch"',
            expect_string=r".*[>#].*",
            delay_factor=2,
        )
        if "default-switch" in config_test:
            return True
        model_check = conn.send_command("show version | match model")
        ml = model_check.lower()
        if any(m in ml for m in ('ex2300', 'ex3400', 'ex4300', 'qfx')):
            return True
        if any(m in ml for m in ('ex2200', 'ex3300', 'ex4200', 'ex4500')):
            return False
    except Exception:
        pass
    return True


def _get_junos_vlan_syntax(conn, dtype: str) -> Tuple[str, str]:
    """Return (set_syntax_prefix, show_syntax) for Junos VLAN commands."""
    if _is_junos_els(conn, dtype):
        return ('set vlans', 'show vlans')
    return ('set ethernet-switching vlan', 'show ethernet-switching vlan')


def _resolve_junos_vlan_name(conn, dtype: str, vid: str, vname: Optional[str] = None) -> Optional[str]:
    """Resolve Junos VLAN name from ID when name not provided."""
    if vname:
        return vname
    set_syntax, show_syntax = _get_junos_vlan_syntax(conn, dtype)
    vlan_out = conn.send_command(f"{show_syntax} | display set")
    for line in vlan_out.splitlines():
        match = re.search(rf"{re.escape(set_syntax)}\s+(\S+)\s+vlan-id\s+{re.escape(str(vid))}\b", line)
        if match:
            return match.group(1)
    parsed = parse_vlan_output(conn.send_command(show_syntax), dtype)
    for entry in parsed:
        if str(entry[0]) == str(vid) and len(entry) > 1:
            return entry[1]
    return None


def _vlan_section_cmd(dtype: str) -> str:
    """Get the appropriate VLAN config section command."""
    dt = (dtype or "").lower()
    if "juniper" in dt:
        return "show configuration vlans | display set"
    if _is_ios_xr(dt):
        return "show running-config vlan"
    return "show running-config | section vlan"


def _validate_vlan_id(vid: str) -> Tuple[bool, str]:
    """Validate VLAN ID is within acceptable range."""
    try:
        vlan_num = int(vid)
        if not (1 <= vlan_num <= 4094):
            return False, f"VLAN ID {vid} out of range (1-4094)"
        # Reserved VLANs
        if vlan_num in (1, 1002, 1003, 1004, 1005):
            return False, f"VLAN {vid} is reserved and cannot be modified"
        return True, ""
    except ValueError:
        return False, f"Invalid VLAN ID: {vid}"


def _cisco_vlan_has_active_ports(conn, vid: str) -> Tuple[bool, str]:
    """Return True if Cisco VLAN still has switchports assigned."""
    try:
        output = conn.send_command(f"show vlan id {vid}", read_timeout=30)
        for line in output.splitlines():
            s = line.strip()
            if not s or s.startswith(('VLAN', '---', 'VLAN ID')):
                continue
            if re.match(r'^\d+\s+\S+', s):
                continue
            if re.search(
                r'\b(Gi|Fa|Te|Eth|Hu|Fo|Twe|Po|Vl|Vlan|Port-channel|App|mgmt)\S*',
                s, re.IGNORECASE,
            ):
                return True, s
        return False, ""
    except Exception:
        return False, ""


def _get_vlan_state(conn, dtype: str, vid: str) -> Dict[str, Any]:
    """Get current state of a specific VLAN."""
    cmd = _vlan_show_cmd(dtype)
    output = conn.send_command(cmd)
    parsed = parse_vlan_output(output, dtype)
    
    vlan_entry = None
    for entry in parsed:
        if str(entry[0]) == str(vid):
            vlan_entry = entry
            break
    
    return {
        "exists": vlan_entry is not None,
        "vlan_data": vlan_entry,
        "all_vlans": parsed
    }


def _run_post_check(
    conn, dtype: str, vid: str, expected_exists: bool = True,
    expected_name: str = None,
) -> Dict[str, Any]:
    """Run post-change verification check."""
    verify_output = conn.send_command(_vlan_show_cmd(dtype))
    parsed = parse_vlan_output(verify_output, dtype)
    exists = any(str(v[0]) == str(vid) for v in parsed)
    
    check_passed = exists == expected_exists
    actual_name = None
    if exists:
        for entry in parsed:
            if str(entry[0]) == str(vid):
                actual_name = entry[1] if len(entry) > 1 else ''
                break
        if expected_exists and expected_name and actual_name is not None:
            if actual_name.lower() != expected_name.lower():
                check_passed = False
    
    return {
        "vlan_exists": exists,
        "vlan_name": actual_name,
        "expected_name": expected_name,
        "vlan_count_seen": len(parsed),
        "show_cmd": _vlan_show_cmd(dtype),
        "expected_exists": expected_exists,
        "check_passed": check_passed,
        "parsed_vlans": [v[0] for v in parsed]
    }


def _result_status(*, skipped: bool = False, dry_run: bool = False,
                   verification_passed: bool = True) -> str:
    if skipped:
        return "skipped"
    if dry_run:
        return "success"
    if not verification_passed:
        return "verification_failed"
    return "success"


def _run_idempotency_check(conn, dtype: str, vid: str, vname: str, 
                           operation: str) -> Dict[str, Any]:
    """Check if the desired state already exists (idempotency)."""
    vlan_state = _get_vlan_state(conn, dtype, vid)
    
    if operation == "add":
        if vlan_state["exists"]:
            vlan_data = vlan_state["vlan_data"]
            existing_name = vlan_data[1] if len(vlan_data) > 1 else ""
            if existing_name.lower() == vname.lower():
                return {
                    "should_skip": True,
                    "reason": f"VLAN {vid} with name '{vname}' already exists",
                    "current_state": vlan_state
                }
            else:
                if "juniper" in dtype.lower():
                    return {
                        "should_skip": False,
                        "reason": (
                            f"VLAN {vid} exists as '{existing_name}'; "
                            "Junos cannot rename — delete and re-add required"
                        ),
                        "current_state": vlan_state,
                        "block_add": True,
                    }
                return {
                    "should_skip": False,
                    "reason": (
                        f"VLAN {vid} exists as '{existing_name}'; "
                        f"cannot add as '{vname}' — rename or delete first"
                    ),
                    "current_state": vlan_state,
                    "block_add": True,
                }
        return {"should_skip": False, "reason": "VLAN does not exist", "current_state": vlan_state}
    
    elif operation == "rename":
        if not vlan_state["exists"]:
            return {
                "should_skip": True,
                "reason": f"VLAN {vid} does not exist, cannot rename",
                "current_state": vlan_state
            }
        vlan_data = vlan_state["vlan_data"]
        existing_name = vlan_data[1] if len(vlan_data) > 1 else ""
        if existing_name.lower() == vname.lower():
            return {
                "should_skip": True,
                "reason": f"VLAN {vid} already has name '{vname}'",
                "current_state": vlan_state
            }
        return {"should_skip": False, "reason": "Rename needed", "current_state": vlan_state}
    
    elif operation == "delete":
        if not vlan_state["exists"]:
            return {
                "should_skip": True,
                "reason": f"VLAN {vid} does not exist",
                "current_state": vlan_state
            }
        return {"should_skip": False, "reason": "VLAN exists, deletion needed", "current_state": vlan_state}
    
    return {"should_skip": False, "reason": "Unknown operation", "current_state": vlan_state}


def _get_prechange_snapshot(device: Dict[str, Any], conn, dtype: str) -> Dict[str, Any]:
    """Get pre-change VLAN configuration snapshot."""
    snap_cmd = _vlan_section_cmd(dtype)
    snapshot = conn.send_command(snap_cmd)
    return {"snapshot_cmd": snap_cmd, "snapshot": snapshot}


def _save_vlan_config(conn, dtype: str, host: str, log_func=None) -> Dict[str, Any]:
    """
    Save configuration after VLAN changes using platform-specific commands.
    Mimics the save logic from interface management.
    """
    try:
        dtype_lower = (dtype or "").lower()
        
        if "juniper" in dtype_lower:
            # Juniper already commits during config change, no additional save needed
            if log_func:
                log_func(f"[{host}] Configuration already committed (Juniper)")
            return {"saved": True, "method": "commit"}
        
        elif _is_ios_xr(dtype_lower):
            if log_func:
                log_func(f"[{host}] IOS-XR: configuration persisted via commit")
            return {"saved": True, "method": "commit"}

        elif "nxos" in dtype_lower:
            if log_func:
                log_func(f"[{host}] Saving configuration (copy running-config startup-config)...")
            output = conn.send_command(
                "copy running-config startup-config",
                delay_factor=10,
                max_loops=5000
            )
            if log_func:
                log_func(f"[{host}] Configuration saved successfully")
            return {"saved": True, "method": "copy running-config startup-config", "output": output}

        else:
            # Cisco IOS/IOS-XE uses write memory
            if log_func:
                log_func(f"[{host}] Saving configuration (write memory)...")
            output = conn.send_command(
                "write memory",
                delay_factor=10,
                max_loops=5000
            )
            if log_func:
                log_func(f"[{host}] Configuration saved successfully")
            return {"saved": True, "method": "write memory", "output": output}
    
    except Exception as e:
        error_msg = str(e)
        if log_func:
            log_func(f"[{host}] WARNING: Could not save configuration: {error_msg}")
        return {"saved": False, "error": error_msg}


def _is_commit_platform(dtype: str) -> bool:
    dt = (dtype or "").lower()
    return "juniper" in dt or _is_ios_xr(dt)


def _apply_vlan_config(conn, dtype: str, cmds: List[str]) -> None:
    """Push VLAN config — commit on Juniper and IOS-XR."""
    if _is_commit_platform(dtype):
        conn.send_config_set(cmds, exit_config_mode=False)
        conn.commit()
        conn.exit_config_mode()
    else:
        conn.send_config_set(cmds)


def add_vlan(device: Dict[str, Any], user: str, pwd: str, enb_pwd: str,
             vid: str, vname: str, dry_run: bool = False,
             auto_backup: bool = True, enable_idempotency: bool = True,
             save_config: bool = True) -> Dict[str, Any]:
    """
    Production-grade VLAN add with idempotency, validation, and rollback support.
    
    Args:
        device: Device dictionary with host and device_type
        user, pwd, enb_pwd: Credentials
        vid: VLAN ID to add
        vname: VLAN name
        dry_run: If True, only preview commands without making changes
        auto_backup: If True, automatically backup before change
        enable_idempotency: If True, skip if VLAN already exists with same name
        save_config: If True, save configuration after change (default: True)
    
    Returns:
        Dictionary with operation result, status, and context
    """
    host = device["host"]
    dtype = device["device_type"]
    logger = get_logger()
    legacy_log = create_legacy_adapter(OperationType.VLAN_ADD, host)
    
    start_time = time.time()
    
    # Validate VLAN ID
    valid, error_msg = _validate_vlan_id(vid)
    if not valid:
        logger.error(error_msg, OperationType.VLAN_ADD, host)
        return build_json(host, "fail", {}, error_msg)
    
    try:
        conn = connect_device(device, user, pwd, enb_pwd)
        
        # Get hostname from device
        try:
            prompt = conn.find_prompt()
            hostname = prompt.replace('#', '').replace('>', '').strip()
        except:
            hostname = host
        
        # Idempotency check
        if enable_idempotency:
            idem_check = _run_idempotency_check(conn, dtype, vid, vname, "add")
            if idem_check.get("block_add"):
                conn.disconnect()
                msg = idem_check["reason"]
                logger.error(msg, OperationType.VLAN_ADD, host)
                return build_json(host, "fail", {}, msg)
            if idem_check["should_skip"]:
                logger.log_idempotency_skip(OperationType.VLAN_ADD, host, vid, idem_check["reason"])
                legacy_log.info(f"[SKIP] {idem_check['reason']}")
                conn.disconnect()
                return build_json(host, "skipped", {
                    "skipped": True,
                    "reason": idem_check["reason"],
                    "commands": [],
                    "dry_run": False
                })
        
        # Build command list
        if "juniper" in dtype.lower():
            set_syntax, _ = _get_junos_vlan_syntax(conn, dtype)
            if "ethernet-switching" in set_syntax:
                cmds = [f"{set_syntax} {vname} vlan-id {vid}"]
            else:
                cmds = [f"{set_syntax} {vname} vlan-id {vid}"]
        else:
            cmds = [f"vlan {vid}"]
            if vname:
                cmds.append(f"name {vname}")
        
        # Dry-run mode
        if dry_run:
            logger.log_dry_run(OperationType.VLAN_ADD, host, cmds)
            legacy_log.info(f"[DRY-RUN] Commands: {' ; '.join(cmds)}")
            conn.disconnect()
            return build_json(host, "success", {
                "commands": cmds,
                "dry_run": True,
                "skipped": False
            })
        
        # Auto-backup before change
        backup_result = None
        if auto_backup:
            backup_system = get_backup_system()
            backup_result = backup_system.auto_backup_pre_change(
                device, user, pwd, enb_pwd,
                f"Add VLAN {vid} '{vname}'"
            )
            if backup_result.get("success"):
                legacy_log.info(f"[BACKUP] Pre-change snapshot saved: {backup_result.get('backup_path', 'N/A')}")
        
        # Log config state change: PENDING -> PUSHED
        logger.log_config_state_change(
            OperationType.VLAN_ADD, host, vid,
            ConfigState.PENDING, ConfigState.PUSHED, cmds
        )
        
        # Execute commands
        legacy_log.info(f"[EXEC] Adding VLAN {vid} '{vname}'...")
        _apply_vlan_config(conn, dtype, cmds)
        
        # Post-change verification
        post_check = _run_post_check(
            conn, dtype, vid, expected_exists=True, expected_name=vname,
        )
        
        # Log verification result
        logger.log_verification_result(
            OperationType.VLAN_ADD, host,
            "vlan_exists", True, post_check["vlan_exists"],
            post_check["check_passed"]
        )
        
        # Determine final config state
        cfg_state = ConfigState.COMMITTED if _is_commit_platform(dtype) else ConfigState.PUSHED
        
        logger.log_config_state_change(
            OperationType.VLAN_ADD, host, vid,
            ConfigState.PUSHED, cfg_state
        )
        
        # Save configuration if requested (mimics interface management behavior)
        save_result = None
        if save_config and post_check["check_passed"]:
            save_result = _save_vlan_config(conn, dtype, host, legacy_log.info)
            if save_result.get("saved"):
                cfg_state = ConfigState.COMMITTED
                logger.log_config_state_change(
                    OperationType.VLAN_ADD, host, vid,
                    ConfigState.PUSHED, cfg_state
                )
        
        conn.disconnect()
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log completion
        logger.log_operation_complete(
            OperationType.VLAN_ADD, host, duration_ms,
            "success" if post_check["check_passed"] else "verification_failed",
            {
                "vlan_id": vid,
                "vlan_name": vname,
                "commands": cmds,
                "verification": post_check,
                "backup_path": backup_result.get("backup_path") if backup_result else None
            }
        )
        
        if post_check["check_passed"]:
            legacy_log.info(f"[SUCCESS] VLAN {vid} added and verified")
            if save_result and save_result.get("saved"):
                legacy_log.info(f"[CONFIG] Configuration saved successfully ({save_result.get('method', 'unknown')})")
            elif _is_commit_platform(dtype):
                legacy_log.info("[CONFIG] Persisted (commit complete)")
            else:
                legacy_log.info("[CONFIG] Changed in running-config only (save needed)")
        else:
            legacy_log.warning(f"[VERIFY] VLAN {vid} NOT found after add attempt")
        
        op_status = _result_status(verification_passed=post_check["check_passed"])
        return build_json(host, op_status, {
            "commands": cmds,
            "dry_run": False,
            "post_check": post_check,
            "verification_passed": post_check["check_passed"],
            "backup_path": backup_result.get("backup_path") if backup_result else None,
            "save_result": save_result
        })
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        error_msg = str(e).splitlines()[0] if str(e).splitlines() else str(e)
        
        logger.error(
            f"VLAN add failed: {error_msg}",
            OperationType.VLAN_ADD, host,
            {"duration_ms": duration_ms, "vlan_id": vid, "vlan_name": vname},
            exception=e
        )
        legacy_log.error(f"[ERROR] {error_msg}")
        
        return build_json(host, "fail", {"vlan_id": vid}, error_msg)


def rename_vlan(device: Dict[str, Any], user: str, pwd: str, enb_pwd: str,
                vid: str, vname: str, dry_run: bool = False,
                auto_backup: bool = True, enable_idempotency: bool = True,
                save_config: bool = True) -> Dict[str, Any]:
    """Production-grade VLAN rename with idempotency and validation.
    
    Args:
        device: Device dictionary with host and device_type
        user, pwd, enb_pwd: Credentials
        vid: VLAN ID to rename
        vname: New VLAN name
        dry_run: If True, only preview commands without making changes
        auto_backup: If True, automatically backup before change
        enable_idempotency: If True, skip if VLAN already has same name
        save_config: If True, save configuration after change (default: True)
    """
    host = device["host"]
    dtype = device["device_type"]
    logger = get_logger()
    legacy_log = create_legacy_adapter(OperationType.VLAN_RENAME, host)
    
    start_time = time.time()
    
    # Validate VLAN ID
    valid, error_msg = _validate_vlan_id(vid)
    if not valid:
        logger.error(error_msg, OperationType.VLAN_RENAME, host)
        return build_json(host, "fail", {}, error_msg)
    
    try:
        conn = connect_device(device, user, pwd, enb_pwd)
        
        # Check if rename is supported on this platform
        if "juniper" in dtype.lower():
            conn.disconnect()
            error_msg = "Rename requires delete/add on Junos. Use delete then add instead."
            logger.error(error_msg, OperationType.VLAN_RENAME, host)
            return build_json(host, "fail", {}, error_msg)
        
        # Idempotency check
        if enable_idempotency:
            idem_check = _run_idempotency_check(conn, dtype, vid, vname, "rename")
            if idem_check["should_skip"]:
                logger.log_idempotency_skip(OperationType.VLAN_RENAME, host, vid, idem_check["reason"])
                legacy_log.info(f"[SKIP] {idem_check['reason']}")
                conn.disconnect()
                return build_json(host, "skipped", {
                    "skipped": True,
                    "reason": idem_check["reason"],
                    "commands": [],
                    "dry_run": False
                })
        
        # Build command list
        cmds = [f"vlan {vid}", f"name {vname}"]
        
        # Dry-run mode
        if dry_run:
            logger.log_dry_run(OperationType.VLAN_RENAME, host, cmds)
            legacy_log.info(f"[DRY-RUN] Commands: {' ; '.join(cmds)}")
            conn.disconnect()
            return build_json(host, "success", {
                "commands": cmds,
                "dry_run": True,
                "skipped": False
            })
        
        # Auto-backup before change
        backup_result = None
        if auto_backup:
            backup_system = get_backup_system()
            backup_result = backup_system.auto_backup_pre_change(
                device, user, pwd, enb_pwd,
                f"Rename VLAN {vid} to '{vname}'"
            )
            if backup_result.get("success"):
                legacy_log.info(f"[BACKUP] Pre-change snapshot saved: {backup_result.get('backup_path', 'N/A')}")
        
        logger.log_config_state_change(
            OperationType.VLAN_RENAME, host, vid,
            ConfigState.PENDING, ConfigState.PUSHED, cmds
        )
        
        legacy_log.info(f"[EXEC] Renaming VLAN {vid} to '{vname}'...")
        _apply_vlan_config(conn, dtype, cmds)
        
        # Post-change verification
        post_check = _run_post_check(
            conn, dtype, vid, expected_exists=True, expected_name=vname,
        )
        
        logger.log_verification_result(
            OperationType.VLAN_RENAME, host,
            "vlan_exists", True, post_check["vlan_exists"],
            post_check["check_passed"]
        )
        
        logger.log_config_state_change(
            OperationType.VLAN_RENAME, host, vid,
            ConfigState.PUSHED, ConfigState.PUSHED
        )
        
        # Save configuration if requested (mimics interface management behavior)
        save_result = None
        if save_config and post_check["check_passed"]:
            save_result = _save_vlan_config(conn, dtype, host, legacy_log.info)
            if save_result.get("saved"):
                cfg_state = ConfigState.COMMITTED
                logger.log_config_state_change(
                    OperationType.VLAN_RENAME, host, vid,
                    ConfigState.PUSHED, cfg_state
                )
        
        conn.disconnect()
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.log_operation_complete(
            OperationType.VLAN_RENAME, host, duration_ms,
            "success" if post_check["check_passed"] else "verification_failed",
            {
                "vlan_id": vid,
                "new_name": vname,
                "commands": cmds,
                "verification": post_check,
                "backup_path": backup_result.get("backup_path") if backup_result else None
            }
        )
        
        if post_check["check_passed"]:
            legacy_log.info(f"[SUCCESS] VLAN {vid} renamed and verified")
            if save_result and save_result.get("saved"):
                legacy_log.info(f"[CONFIG] Configuration saved successfully ({save_result.get('method', 'unknown')})")
            else:
                legacy_log.info("[CONFIG] Changed in running-config only (save needed)")
        else:
            legacy_log.warning(f"[VERIFY] VLAN {vid} NOT found after rename attempt")
        
        op_status = _result_status(verification_passed=post_check["check_passed"])
        return build_json(host, op_status, {
            "commands": cmds,
            "dry_run": False,
            "post_check": post_check,
            "verification_passed": post_check["check_passed"],
            "backup_path": backup_result.get("backup_path") if backup_result else None,
            "save_result": save_result
        })
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        error_msg = str(e).splitlines()[0] if str(e).splitlines() else str(e)
        
        logger.error(
            f"VLAN rename failed: {error_msg}",
            OperationType.VLAN_RENAME, host,
            {"duration_ms": duration_ms, "vlan_id": vid, "vlan_name": vname},
            exception=e
        )
        legacy_log.error(f"[ERROR] {error_msg}")
        
        return build_json(host, "fail", {"vlan_id": vid}, error_msg)


def delete_vlan(device: Dict[str, Any], user: str, pwd: str, enb_pwd: str,
                vid: str, vname: str = None, dry_run: bool = False,
                auto_backup: bool = True, enable_idempotency: bool = True,
                save_config: bool = True) -> Dict[str, Any]:
    """Production-grade VLAN delete with idempotency and validation.
    
    Args:
        device: Device dictionary with host and device_type
        user, pwd, enb_pwd: Credentials
        vid: VLAN ID to delete
        vname: VLAN name (required for Juniper)
        dry_run: If True, only preview commands without making changes
        auto_backup: If True, automatically backup before change
        enable_idempotency: If True, skip if VLAN does not exist
        save_config: If True, save configuration after change (default: True)
    """
    host = device["host"]
    dtype = device["device_type"]
    logger = get_logger()
    legacy_log = create_legacy_adapter(OperationType.VLAN_DELETE, host)
    
    start_time = time.time()
    
    # Validate VLAN ID
    valid, error_msg = _validate_vlan_id(vid)
    if not valid:
        logger.error(error_msg, OperationType.VLAN_DELETE, host)
        return build_json(host, "fail", {}, error_msg)
    
    try:
        conn = connect_device(device, user, pwd, enb_pwd)
        
        # Juniper: resolve VLAN name (required for delete command)
        if "juniper" in dtype.lower():
            resolved_name = _resolve_junos_vlan_name(conn, dtype, vid, vname)
            if not resolved_name:
                conn.disconnect()
                error_msg = f"VLAN {vid} not found on Junos device (cannot resolve VLAN name)."
                logger.error(error_msg, OperationType.VLAN_DELETE, host)
                return build_json(host, "fail", {}, error_msg)
            set_syntax, _ = _get_junos_vlan_syntax(conn, dtype)
            cmds = [f"delete {set_syntax} {resolved_name}"]
        else:
            cmds = [f"no vlan {vid}"]
        
        # Idempotency check
        if enable_idempotency:
            idem_check = _run_idempotency_check(conn, dtype, vid, vname or "", "delete")
            if idem_check["should_skip"]:
                logger.log_idempotency_skip(OperationType.VLAN_DELETE, host, vid, idem_check["reason"])
                legacy_log.info(f"[SKIP] {idem_check['reason']}")
                conn.disconnect()
                return build_json(host, "skipped", {
                    "skipped": True,
                    "reason": idem_check["reason"],
                    "commands": [],
                    "dry_run": False
                })
        
        # Cisco: block delete when VLAN still has active interfaces
        if "juniper" not in dtype.lower():
            in_use, detail = _cisco_vlan_has_active_ports(conn, vid)
            if in_use:
                conn.disconnect()
                error_msg = (
                    f"Cannot delete VLAN {vid}: still assigned to interface(s)"
                    f"{f' ({detail})' if detail else ''}. Remove VLAN from ports first."
                )
                logger.error(error_msg, OperationType.VLAN_DELETE, host)
                legacy_log.error(f"[ERROR] {error_msg}")
                return build_json(host, "fail", {"vlan_id": vid}, error_msg)
        
        # Dry-run mode
        if dry_run:
            logger.log_dry_run(OperationType.VLAN_DELETE, host, cmds)
            legacy_log.info(f"[DRY-RUN] Commands: {' ; '.join(cmds)}")
            conn.disconnect()
            return build_json(host, "success", {
                "commands": cmds,
                "dry_run": True,
                "skipped": False
            })
        
        # Auto-backup before change
        backup_result = None
        if auto_backup:
            backup_system = get_backup_system()
            backup_result = backup_system.auto_backup_pre_change(
                device, user, pwd, enb_pwd,
                f"Delete VLAN {vid}"
            )
            if backup_result.get("success"):
                legacy_log.info(f"[BACKUP] Pre-change snapshot saved: {backup_result.get('backup_path', 'N/A')}")
        
        logger.log_config_state_change(
            OperationType.VLAN_DELETE, host, vid,
            ConfigState.PENDING, ConfigState.PUSHED, cmds
        )
        
        legacy_log.info(f"[EXEC] Deleting VLAN {vid}...")
        _apply_vlan_config(conn, dtype, cmds)
        
        # Post-change verification
        post_check = _run_post_check(conn, dtype, vid, expected_exists=False)
        post_check["vlan_removed"] = not post_check["vlan_exists"]
        
        logger.log_verification_result(
            OperationType.VLAN_DELETE, host,
            "vlan_removed", True, post_check["vlan_removed"],
            post_check["vlan_removed"]
        )
        
        cfg_state = ConfigState.COMMITTED if _is_commit_platform(dtype) else ConfigState.PUSHED
        
        logger.log_config_state_change(
            OperationType.VLAN_DELETE, host, vid,
            ConfigState.PUSHED, cfg_state
        )
        
        # Save configuration if requested (mimics interface management behavior)
        save_result = None
        if save_config and post_check["vlan_removed"]:
            save_result = _save_vlan_config(conn, dtype, host, legacy_log.info)
            if save_result.get("saved"):
                cfg_state = ConfigState.COMMITTED
                logger.log_config_state_change(
                    OperationType.VLAN_DELETE, host, vid,
                    ConfigState.PUSHED, cfg_state
                )
        
        conn.disconnect()
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.log_operation_complete(
            OperationType.VLAN_DELETE, host, duration_ms,
            "success" if post_check["vlan_removed"] else "verification_failed",
            {
                "vlan_id": vid,
                "commands": cmds,
                "verification": post_check,
                "backup_path": backup_result.get("backup_path") if backup_result else None
            }
        )
        
        if post_check["vlan_removed"]:
            legacy_log.info(f"[SUCCESS] VLAN {vid} deleted and verified")
            if save_result and save_result.get("saved"):
                legacy_log.info(f"[CONFIG] Configuration saved successfully ({save_result.get('method', 'unknown')})")
            elif "juniper" in dtype.lower():
                legacy_log.info("[CONFIG] Deletion committed")
            else:
                legacy_log.info("[CONFIG] Deletion in running-config (save needed)")
        else:
            legacy_log.warning(f"[VERIFY] VLAN {vid} still present after delete attempt")
        
        op_status = _result_status(verification_passed=post_check["vlan_removed"])
        return build_json(host, op_status, {
            "commands": cmds,
            "dry_run": False,
            "post_check": post_check,
            "verification_passed": post_check["vlan_removed"],
            "backup_path": backup_result.get("backup_path") if backup_result else None,
            "save_result": save_result
        })
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        error_msg = str(e).splitlines()[0] if str(e).splitlines() else str(e)
        
        logger.error(
            f"VLAN delete failed: {error_msg}",
            OperationType.VLAN_DELETE, host,
            {"duration_ms": duration_ms, "vlan_id": vid},
            exception=e
        )
        legacy_log.error(f"[ERROR] {error_msg}")
        
        return build_json(host, "fail", {"vlan_id": vid}, error_msg)



# Legacy compatibility - delegate to new functions
def get_prechange_snapshot(device, user, pwd, enb_pwd):
    """Legacy compatibility function."""
    host = device["host"]
    dtype = device["device_type"]
    try:
        conn = connect_device(device, user, pwd, enb_pwd)
        snap = _get_prechange_snapshot(device, conn, dtype)
        conn.disconnect()
        return build_json(host, "success", snap)
    except Exception as e:
        return build_json(host, "fail", {}, str(e).splitlines()[0] if str(e).splitlines() else str(e))
