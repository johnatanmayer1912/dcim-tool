"""Build a NOC Issues list from topology edges. Does not invent links."""
from __future__ import annotations

from typing import Any, Dict, List


def build_link_issues(edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """One row per witness problem. Overlay/L3 edges are skipped for cable kinds."""
    issues: List[Dict[str, Any]] = []
    for e in edges or []:
        frm, to = e.get('from') or '', e.get('to') or ''
        fp, tp = e.get('f_port') or '', e.get('t_port') or ''
        base = {
            'from': frm, 'to': to, 'f_port': fp, 't_port': tp,
            'protocol': e.get('protocol') or e.get('discovery') or '',
        }
        if e.get('one_sided') or e.get('spoof_risk'):
            issues.append({**base, 'kind': 'one_sided', 'severity': 'medium',
                           'summary': 'One-sided CDP/LLDP — spoofable, not a verified cable'})
        if (e.get('confidence') or '') == 'Mismatch' or (
            (e.get('f_int_data') or {}).get('status') == 'up'
            and (e.get('t_int_data') or {}).get('status') in ('down', 'err-disabled')
        ) or (
            (e.get('t_int_data') or {}).get('status') == 'up'
            and (e.get('f_int_data') or {}).get('status') in ('down', 'err-disabled')
        ):
            issues.append({**base, 'kind': 'updown_mismatch', 'severity': 'high',
                           'summary': 'One end up, other down/err-disabled'})
        for kind, summary, sev in (
            ('description_vs_neighbor', 'Interface description does not name the CDP/LLDP neighbor', 'medium'),
            ('speed_mismatch', 'Speed differs at the two ends', 'high'),
            ('duplex_mismatch', 'Duplex differs at the two ends', 'high'),
            ('dom_alarm_local', 'Local DOM/Rx power alarm or missing optic', 'high'),
            ('dom_alarm_remote', 'Remote DOM/Rx power alarm or missing optic', 'high'),
        ):
            if kind in (e.get('cable_issues') or []):
                issues.append({**base, 'kind': kind, 'severity': sev, 'summary': summary})
        if e.get('lacp_collected') and e.get('lacp_oper') == 'down':
            issues.append({**base, 'kind': 'lacp_member_down', 'severity': 'high',
                           'summary': 'LACP member down (bundle edge kept)'})
        elif e.get('degraded') and e.get('bundle_kind') == 'member':
            issues.append({**base, 'kind': 'lacp_member_down', 'severity': 'high',
                           'summary': 'LAG member degraded (bundle kept)'})
    # Stable unique key
    seen = set()
    uniq = []
    for i in issues:
        key = (i['kind'], i['from'], i['f_port'], i['to'], i['t_port'])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(i)
    return uniq
