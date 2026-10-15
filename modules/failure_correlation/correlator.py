"""Cluster classified events into operator-facing failure hypotheses."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from modules.failure_correlation.rules import SEVERITY_ORDER

# Symptom priority when multiple rules fire on same object
_SYMPTOM_WEIGHT = {
    'VPC_DUAL_ACTIVE': 100,
    'VPC_PEERLINK_DOWN': 95,
    'VPC_KEEPALIVE_FAIL': 90,
    'VPC_CONSISTENCY': 85,
    'ERRDISABLE': 80,
    'BPDU_GUARD': 78,
    'UDLD': 75,
    'INTERFACE_DOWN': 70,
    'PORT_SECURITY': 68,
    'LAYER1_ERRORS': 60,
    'OSPF_DOWN': 55,
    'BGP_DOWN': 55,
    'HARDWARE_ALARM': 92,
    'MODULE_DOWN': 88,
    'DEVICE_RELOAD': 50,
    'INTERFACE_ADMIN_DOWN': 40,
    'STORM_CONTROL': 45,
    'FHRP_CHANGE': 35,
    'VPC_ROLE_CHANGE': 30,
    'CONFIG_CHANGE': 10,
    'LINK_STATE_CHANGE': 15,
    'AUTH_FAIL': 25,
}


def _object_key(event: Dict[str, Any]) -> str:
    iface = (event.get('interface') or '').strip()
    code = event.get('symptom_code') or 'GENERAL'
    if event.get('category') == 'vpc':
        return f'vpc::{code}'
    if iface:
        return f'if::{iface.lower()}'
    if event.get('category') == 'protocol':
        return f'proto::{code}'
    if event.get('category') == 'hardware':
        return f'hw::{code}'
    return f'host::{code}'


def build_hypotheses(
    events: List[Dict[str, Any]],
    *,
    host: str,
    cli_context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Group relevant events into ranked hypotheses with evidence quotes."""
    cli_context = cli_context or {}
    clusters: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for e in events:
        if not e.get('rule_id') or e.get('category') == 'noise':
            continue
        if e.get('severity') == 'noise':
            continue
        clusters[_object_key(e)].append(e)

    hypotheses: List[Dict[str, Any]] = []
    for key, group in clusters.items():
        # Primary = highest weight symptom in cluster
        primary = max(
            group,
            key=lambda e: (
                _SYMPTOM_WEIGHT.get(e.get('symptom_code') or '', 0),
                -SEVERITY_ORDER.get(e.get('severity') or 'info', 9),
            ),
        )
        evidence_lines = []
        seen = set()
        for e in sorted(group, key=lambda x: x.get('index', 0)):
            line = e.get('line') or ''
            if line in seen:
                continue
            seen.add(line)
            evidence_lines.append(line)
            if len(evidence_lines) >= 8:
                break

        confidence = _confidence(primary, group, cli_context)
        obj = primary.get('interface') or key.split('::', 1)[-1]
        hyp = {
            'id': key,
            'host': host,
            'object': obj,
            'category': primary.get('category'),
            'severity': primary.get('severity'),
            'symptom_code': primary.get('symptom_code'),
            'title': primary.get('title') or 'Correlated failure',
            'why': _why_narrative(primary, group, cli_context),
            'hint': primary.get('hint') or '',
            'confidence': confidence,
            'confidence_label': _confidence_label(confidence),
            'evidence_count': len(group),
            'evidence': evidence_lines,
            'rule_ids': sorted({e.get('rule_id') for e in group if e.get('rule_id')}),
            'incomplete': False,
        }
        hypotheses.append(hyp)

    # CLI-only context: interface down in status but no logs
    for iface, status in (cli_context.get('interfaces_down') or {}).items():
        key = f'if::{iface.lower()}'
        if any(h['id'] == key for h in hypotheses):
            continue
        hypotheses.append({
            'id': key,
            'host': host,
            'object': iface,
            'category': 'interface',
            'severity': 'warning',
            'symptom_code': 'INTERFACE_DOWN_NO_LOG',
            'title': 'Interface down — no matching log evidence',
            'why': (
                f'{iface} is operationally down in CLI status ({status}), '
                'but buffered logs did not contain a matching IF_DOWN / errdisable line. '
                'Incomplete observation — increase logging buffer or check archive.'
            ),
            'hint': 'show logging logfile / logging buffered; confirm timestamps and severity.',
            'confidence': 0.35,
            'confidence_label': 'low',
            'evidence_count': 0,
            'evidence': [f'CLI: {iface} status={status}'],
            'rule_ids': [],
            'incomplete': True,
        })

    hypotheses.sort(
        key=lambda h: (
            -float(h.get('confidence') or 0),
            SEVERITY_ORDER.get(h.get('severity') or 'info', 9),
        )
    )
    return hypotheses


def _confidence(primary: Dict[str, Any], group: List[Dict[str, Any]], cli: Dict[str, Any]) -> float:
    base = 0.55
    weight = _SYMPTOM_WEIGHT.get(primary.get('symptom_code') or '', 20)
    base += min(0.30, weight / 400.0)
    if len(group) >= 2:
        base += 0.08
    if len(group) >= 4:
        base += 0.05
    iface = (primary.get('interface') or '').lower()
    if iface and iface in {k.lower() for k in (cli.get('interfaces_down') or {})}:
        base += 0.12  # log + operational state agree
    if primary.get('category') == 'vpc' and cli.get('vpc_peer_down'):
        base += 0.12
    return round(min(0.97, base), 2)


def _confidence_label(score: float) -> str:
    if score >= 0.8:
        return 'high'
    if score >= 0.55:
        return 'medium'
    return 'low'


def _why_narrative(primary: Dict[str, Any], group: List[Dict[str, Any]], cli: Dict[str, Any]) -> str:
    title = primary.get('title') or 'Failure'
    obj = primary.get('interface') or primary.get('symptom_code') or 'device'
    parts = [
        f'Symptom: {title} on {obj}.',
        f'Matched {len(group)} relevant log/CLI evidence line(s) '
        f'(primary rule {primary.get("rule_id")}).',
    ]
    # Supporting symptoms
    others = sorted({
        e.get('symptom_code') for e in group
        if e.get('symptom_code') and e.get('symptom_code') != primary.get('symptom_code')
    })
    if others:
        parts.append('Also seen nearby: ' + ', '.join(others[:6]) + '.')
    if primary.get('interface') and primary['interface'] in (cli.get('interfaces_down') or {}):
        parts.append(
            f"Operational state confirms {primary['interface']} is down "
            f"({cli['interfaces_down'][primary['interface']]})."
        )
    if primary.get('category') == 'vpc' and cli.get('vpc_summary'):
        parts.append(f"vPC CLI context: {cli['vpc_summary'][:200]}")
    parts.append(primary.get('hint') or '')
    return ' '.join(p for p in parts if p).strip()


def fleet_rollups(device_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate per-device hypotheses for manager/NOC summary."""
    all_h: List[Dict[str, Any]] = []
    for dr in device_results:
        for h in dr.get('hypotheses') or []:
            all_h.append(h)
    by_cat: Dict[str, int] = defaultdict(int)
    by_sev: Dict[str, int] = defaultdict(int)
    for h in all_h:
        by_cat[h.get('category') or 'unknown'] += 1
        by_sev[h.get('severity') or 'info'] += 1
    top = all_h[:12]
    return {
        'hypothesis_count': len(all_h),
        'by_category': dict(by_cat),
        'by_severity': dict(by_sev),
        'top_hypotheses': top,
        'hosts_with_findings': sorted({h.get('host') for h in all_h if h.get('host')}),
    }
