"""Golden-config gate for VLAN and Interface Manager mutations.

Local YAML policy. Fail-closed when enabled and a rule matches.
Does not replace dry-run / vendor syntax — it is an extra step.
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def _policy_path() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, 'policies', 'golden_gate.yaml')


def load_golden_policy(path: Optional[str] = None) -> Dict[str, Any]:
    p = path or _policy_path()
    if not os.path.isfile(p):
        return {'enabled': False, 'missing': True}
    raw = open(p, encoding='utf-8').read()
    if yaml:
        data = yaml.safe_load(raw) or {}
    else:
        pat = re.search(r'vlan_name_pattern:\s*"([^"]+)"', raw)
        data = {
            'enabled': 'enabled: false' not in raw,
            'forbidden_vlan_ids': [int(x) for x in re.findall(r'^\s*-\s*(\d+)\s*$', raw, re.M)],
            'vlan_name_pattern': pat.group(1) if pat else '',
            'interface_forbidden_substrings': ['default interface'] if 'default interface' in raw else [],
            'require_description_with_access_vlan': 'require_description_with_access_vlan: true' in raw,
            'block_apply_on_fail': 'block_apply_on_fail: false' not in raw,
        }
    if not isinstance(data, dict):
        return {'enabled': False, 'invalid': True}
    return data


def _step(passed: bool, message: str = '', errors: Optional[List[str]] = None) -> Dict[str, Any]:
    return {
        'passed': passed,
        'message': message,
        'errors': [{'message': e} for e in (errors or [])],
        'warnings': [],
    }


def evaluate_vlan_change(
    action: str,
    vlan_id: str,
    vlan_name: str = '',
    policy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    pol = policy if policy is not None else load_golden_policy()
    if not pol.get('enabled', True):
        return _step(True, 'Golden-config gate disabled')
    errors: List[str] = []
    try:
        vid = int(str(vlan_id).strip())
    except (TypeError, ValueError):
        errors.append(f'VLAN id not numeric: {vlan_id!r}')
        vid = None
    forbidden = {int(x) for x in (pol.get('forbidden_vlan_ids') or []) if str(x).isdigit() or isinstance(x, int)}
    if vid is not None and vid in forbidden:
        errors.append(f'VLAN {vid} is forbidden by golden-config policy')
    pat = (pol.get('vlan_name_pattern') or '').strip()
    name = (vlan_name or '').strip()
    op = (action or '').lower()
    if pat and op in ('add', 'add_vlan', 'rename', 'rename_vlan') and name:
        if not re.match(pat, name):
            errors.append(f'VLAN name {name!r} does not match golden pattern')
    passed = not errors
    return _step(
        passed,
        'Golden-config VLAN checks passed' if passed else 'Golden-config VLAN gate failed',
        errors,
    )


def evaluate_interface_change(
    proposed_config: str,
    policy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    pol = policy if policy is not None else load_golden_policy()
    if not pol.get('enabled', True):
        return _step(True, 'Golden-config gate disabled')
    errors: List[str] = []
    blob = proposed_config or ''
    low = blob.lower()
    for tok in pol.get('interface_forbidden_substrings') or []:
        if tok and tok.lower() in low:
            errors.append(f'Forbidden by golden-config: {tok}')
    if pol.get('require_description_with_access_vlan'):
        if re.search(r'switchport\s+access\s+vlan\s+\d+', blob, re.I):
            if not re.search(r'^\s*description\s+\S+', blob, re.I | re.M):
                errors.append('Access VLAN change requires a description line (golden-config)')
    passed = not errors
    return _step(
        passed,
        'Golden-config interface checks passed' if passed else 'Golden-config interface gate failed',
        errors,
    )


def raise_if_blocked(step: Dict[str, Any], *, apply: bool = True) -> None:
    pol = load_golden_policy()
    if not pol.get('block_apply_on_fail', True) or not apply:
        return
    if not step.get('passed'):
        msgs = [e.get('message') for e in (step.get('errors') or []) if e.get('message')]
        raise RuntimeError('Golden-config gate blocked apply: ' + '; '.join(msgs[:6]))
