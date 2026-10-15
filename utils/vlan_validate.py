"""
VLAN operation validation pipeline (mirrors Interface Manager validation shape).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from modules.vlan_mgmt_production import (
    _is_ios_xr,
    _validate_vlan_id,
    add_vlan,
    delete_vlan,
    rename_vlan,
)


def _step(passed: bool, message: str = '', warnings: Optional[List[str]] = None,
          errors: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    return {
        'passed': passed,
        'message': message,
        'warnings': warnings or [],
        'errors': errors or [],
    }


def _golden_vlan_step(op: str, vid: str, vname: str) -> Dict[str, Any]:
    from utils.golden_config_gate import evaluate_vlan_change
    return evaluate_vlan_change(op, vid, vname)


def _map_action(action: str) -> str:
    m = {'add_vlan': 'add', 'rename_vlan': 'rename', 'delete_vlan': 'delete'}
    return m.get(action, action.replace('_vlan', ''))


def validate_vlan_operation(
    action: str,
    devices: List[Dict[str, Any]],
    user: str,
    pwd: str,
    enb_pwd: str,
    vid: str,
    vname: str = '',
    log_func=None,
) -> Dict[str, Any]:
    """Dry-run validation across scoped devices; returns IM-compatible validation_results."""
    op = _map_action(action)
    if not devices:
        return {
            'overall_status': 'failed',
            'risk_level': 'high',
            'validation_results': {
                'dry_run': _step(False, errors=[{'message': 'No target devices in scope'}]),
                'vendor_syntax': _step(False),
                'platform': _step(False),
                'conflicts': _step(False),
            },
            'preview_commands': [],
            'device_count': 0,
        }

    syntax_errors: List[str] = []
    syntax_warnings: List[str] = []
    valid_id, id_err = _validate_vlan_id(str(vid))
    if not valid_id:
        syntax_errors.append(id_err)

    if op in ('add', 'rename') and not (vname or '').strip():
        syntax_errors.append('VLAN name is required for add/rename operations')

    juniper_hosts = [
        d.get('host', '?') for d in devices
        if 'juniper' in (d.get('device_type') or '').lower()
    ]
    if op == 'rename' and juniper_hosts:
        syntax_errors.append(
            f'Rename is not supported on Juniper ({", ".join(juniper_hosts[:5])}). Use delete + add.'
        )

    preview_commands: List[str] = []
    platform_notes: List[str] = []
    platform_errors: List[str] = []
    conflict_msgs: List[str] = []
    dry_ok = True
    _supported = ('cisco', 'ios', 'nxos', 'iosxr', 'ios_xr', 'juniper', 'junos')
    golden_step = _golden_vlan_step(op, vid, vname)

    for dev in devices:
        host = dev.get('host', 'unknown')
        dtype = (dev.get('device_type') or 'cisco_ios').lower()
        if not any(tag in dtype for tag in _supported):
            platform_errors.append(f'{host}: unsupported device_type "{dtype}"')
            dry_ok = False
            continue
        # Do not open SSH when local syntax already forbids the operation.
        if op == 'rename' and 'juniper' in dtype:
            dry_ok = False
            conflict_msgs.append(
                f'{host}: Rename is not supported on Juniper. Use delete + add.'
            )
            continue
        if not valid_id:
            dry_ok = False
            continue
        if op in ('add', 'rename') and not (vname or '').strip():
            dry_ok = False
            continue
        if not golden_step.get('passed'):
            continue
        try:
            if op == 'add':
                res = add_vlan(dev, user, pwd, enb_pwd, vid, vname, dry_run=True, auto_backup=False)
            elif op == 'rename':
                res = rename_vlan(dev, user, pwd, enb_pwd, vid, vname, dry_run=True, auto_backup=False)
            elif op == 'delete':
                res = delete_vlan(dev, user, pwd, enb_pwd, vid, vname or None, dry_run=True, auto_backup=False)
            else:
                res = {'status': 'fail', 'error': f'Unknown action: {action}'}
        except Exception as exc:
            res = {'status': 'fail', 'error': str(exc)}

        if res.get('status') != 'success':
            dry_ok = False
            err = res.get('error', 'dry-run failed')
            conflict_msgs.append(f'{host}: {err}')
            continue

        data = res.get('data') or {}
        cmds = data.get('commands') or []
        if cmds:
            preview_commands.extend([f'{host}: {c}' for c in cmds])
        if data.get('skipped'):
            platform_notes.append(f'{host}: {data.get("reason", "skipped")}')
        if 'juniper' in dtype:
            platform_notes.append(f'{host}: Juniper — commit required after change')
            if op == 'delete' and not vname:
                syntax_warnings.append(f'{host}: Junos delete will auto-resolve VLAN name from ID')
        elif 'nxos' in dtype:
            platform_notes.append(f'{host}: NX-OS — save startup-config recommended')
        elif _is_ios_xr(dtype):
            platform_notes.append(f'{host}: IOS-XR — commit-based VLAN (device_type: cisco_xr / ios_xr)')
        if log_func:
            log_func(f'[VLAN Validate] {host}: dry-run OK ({len(cmds)} command(s))')

    if len(devices) > 10:
        syntax_warnings.append(f'Validated all {len(devices)} devices in scope')

    syntax_ok = not syntax_errors
    validation_results = {
        'dry_run': _step(
            dry_ok,
            'Command preview generated' if dry_ok else 'Dry-run failed on one or more devices',
            errors=[{'message': m} for m in conflict_msgs],
        ),
        'vendor_syntax': _step(
            syntax_ok,
            'VLAN ID/name validated for target platforms' if syntax_ok else 'Syntax validation failed',
            warnings=syntax_warnings,
            errors=[{'message': m} for m in syntax_errors],
        ),
        'platform': _step(
            not platform_errors,
            '; '.join(platform_notes[:8]) if platform_notes else 'Platform checks passed',
            warnings=platform_notes,
            errors=[{'message': m} for m in platform_errors],
        ),
        'conflicts': _step(not conflict_msgs, errors=[{'message': m} for m in conflict_msgs]),
        'golden_config': golden_step,
    }
    all_pass = all(
        validation_results[k]['passed']
        for k in ('dry_run', 'vendor_syntax', 'platform', 'conflicts', 'golden_config')
    )
    risk = 'low' if all_pass else ('medium' if dry_ok else 'high')

    return {
        'overall_status': 'passed' if all_pass else 'failed',
        'risk_level': risk,
        'validation_results': validation_results,
        'preview_commands': preview_commands[:60],
        'device_count': len(devices),
        'operation': action,
        'vlan_id': vid,
        'vlan_name': vname,
    }
