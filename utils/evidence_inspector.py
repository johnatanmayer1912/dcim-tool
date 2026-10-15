"""Read-only topology evidence inspector view-model (Phase 2 slice 4).

Builds explainability sections from existing edge metadata / evidence[].
Does not invent timestamps, ports, or cable truth. No mutation helpers.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def _s(value: Any, default: str = '') -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _display_or_unknown(value: Any, unknown: str = 'unknown') -> str:
    text = _s(value)
    return text if text else unknown


def _evidence_bucket(ev: Dict[str, Any]) -> str:
    """Classify one observation for the inspector (not a trust promotion)."""
    role = _s(ev.get('port_role')).lower()
    kind = _s(ev.get('evidence_type')).lower()
    if ev.get('not_physical') or role in (
        'l3_irb', 'l3_svi', 'l3_logical', 'irb', 'vlan_l3'
    ) or 'irb' in role or kind in ('vlan_context', 'irb_context', 'l3_context'):
        return 'supporting_context'
    if kind in ('inferred', 'heuristic'):
        return 'inferred'
    return 'observed'


def _item_view(ev: Dict[str, Any]) -> Dict[str, Any]:
    collected = ev.get('collected_at')
    ts_known = bool(collected)
    freshness = _s(ev.get('freshness'))
    if not freshness:
        freshness = 'unknown' if not ts_known else ''
    return {
        'bucket': _evidence_bucket(ev),
        'protocol': _display_or_unknown(ev.get('protocol')),
        'vendor': _display_or_unknown(ev.get('vendor') or ev.get('platform'), 'unknown'),
        'command': _display_or_unknown(ev.get('command')),
        'parse_source': _display_or_unknown(ev.get('parse_source'), 'unknown'),
        'local_port': _display_or_unknown(ev.get('local_port'), 'unknown'),
        'remote_port': _display_or_unknown(ev.get('remote_port'), 'unknown'),
        'port_role': _display_or_unknown(ev.get('port_role'), 'unknown'),
        'not_physical': bool(ev.get('not_physical')),
        'collected_at': collected if ts_known else None,
        'collected_at_display': str(collected) if ts_known else 'unknown',
        'timestamp_known': ts_known,
        'freshness': freshness or 'unknown',
        'evidence_type': _display_or_unknown(ev.get('evidence_type'), 'neighbor'),
        'raw_fragment_present': bool(_s(ev.get('raw_fragment'))),
    }


def topology_relation_key(obj: Optional[Dict[str, Any]]) -> str:
    """Deterministic undirected relationship key for map ↔ Link Inventory sync.

    Uses endpoints + ports + physical/logical kind. Never uses array index.
    Does not include secrets. Empty endpoints yield an empty string (no fake id).
    """
    o = obj if isinstance(obj, dict) else {}
    a_host = _s(o.get('from')).lower()
    b_host = _s(o.get('to')).lower()
    a_port = _s(o.get('f_port') or o.get('local_port')).lower()
    b_port = _s(o.get('t_port') or o.get('remote_port')).lower()
    if not a_host and not b_host:
        return ''
    left = (a_host, a_port)
    right = (b_host, b_port)
    if left > right:
        left, right = right, left
    kind = _s(o.get('edge_kind')).lower()
    if not kind:
        layer = _s(o.get('layer')).lower()
        if o.get('not_physical') or layer in ('l3', 'overlay'):
            kind = layer or 'logical'
        else:
            kind = 'l2'
    return '|'.join([left[0], left[1], right[0], right[1], kind])


def link_row_as_inspector_edge(row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Normalize a Link Inventory row into the edge shape used by the inspector.

    Does not invent evidence — missing fields stay empty/unknown downstream.
    """
    r = row if isinstance(row, dict) else {}
    evidence = r.get('evidence') if isinstance(r.get('evidence'), list) else []
    edge = {
        'from': r.get('from') or '',
        'to': r.get('to') or '',
        'f_port': r.get('f_port') or r.get('local_port') or '',
        't_port': r.get('t_port') or r.get('remote_port') or '',
        'local_port': r.get('local_port') or r.get('f_port') or '',
        'remote_port': r.get('remote_port') or r.get('t_port') or '',
        'protocol': r.get('protocol') or '',
        'layer': r.get('layer') or '',
        'edge_kind': r.get('edge_kind') or '',
        'not_physical': bool(r.get('not_physical')),
        'confidence': r.get('confidence') or '',
        'trust_tier': r.get('trust_tier') or '',
        'trust_note': r.get('trust_note') or '',
        'one_sided': bool(r.get('one_sided')),
        'spoof_risk': bool(r.get('spoof_risk')),
        'sources': list(r.get('sources') or []),
        'contradictions': list(r.get('contradictions') or []),
        'evidence': [dict(ev) for ev in evidence if isinstance(ev, dict)],
        'evidence_summary': (
            dict(r['evidence_summary'])
            if isinstance(r.get('evidence_summary'), dict) else {}
        ),
        'collected_at': r.get('collected_at') or None,
        'collected_at_latest': r.get('collected_at_latest') or None,
        'freshness': r.get('freshness') or '',
        'freshness_conflict': bool(r.get('freshness_conflict')),
        'freshness_note': r.get('freshness_note') or '',
        'bundle_kind': r.get('bundle_kind') or '',
        'lag_note': r.get('lag_note') or '',
        'lacp_collected': bool(r.get('lacp_collected')),
        'lacp_oper': r.get('lacp_oper') or '',
        'degraded': bool(r.get('degraded')),
    }
    # Preserve precomputed key when present; otherwise derive
    rk = _s(r.get('relation_key')) or topology_relation_key(edge)
    if rk:
        edge['relation_key'] = rk
    return edge


def build_evidence_inspector_model(edge: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a JSON-serializable read-only inspector model for one map edge."""
    e = edge if isinstance(edge, dict) else {}
    raw_evidence = e.get('evidence') if isinstance(e.get('evidence'), list) else []
    items: List[Dict[str, Any]] = []
    for ev in raw_evidence:
        if isinstance(ev, dict):
            items.append(_item_view(ev))
        else:
            items.append({
                'bucket': 'unknown',
                'protocol': 'unknown',
                'vendor': 'unknown',
                'command': 'unknown',
                'parse_source': 'unknown',
                'local_port': 'unknown',
                'remote_port': 'unknown',
                'port_role': 'unknown',
                'not_physical': False,
                'collected_at': None,
                'collected_at_display': 'unknown',
                'timestamp_known': False,
                'freshness': 'unknown',
                'evidence_type': 'malformed',
                'raw_fragment_present': False,
                'malformed': True,
            })

    contradictions = [
        _s(c) for c in (e.get('contradictions') or []) if _s(c)
    ]
    freshness = _display_or_unknown(e.get('freshness'), 'unknown')
    freshness_conflict = bool(
        e.get('freshness_conflict') or freshness == 'mixed'
    )
    summary = e.get('evidence_summary') if isinstance(e.get('evidence_summary'), dict) else {}

    inferred: List[str] = []
    if e.get('one_sided') or e.get('spoof_risk'):
        inferred.append('ONE-SIDED / spoof-risk — not a verified cable')
    conf = _s(e.get('confidence') or e.get('trust_tier'))
    if conf:
        inferred.append(f'confidence/trust conclusion={conf}')
    if e.get('not_physical') or _s(e.get('edge_kind')).lower() in (
        'irb-adjacency', 'l3-adjacency', 'logical'
    ):
        inferred.append('edge classified as non-cable / logical adjacency')
    if _s(e.get('bundle_kind')) == 'bundle' and not e.get('lacp_collected'):
        inferred.append('BUNDLE/AE naming heuristic — not LACP proof')

    supporting = [i for i in items if i['bucket'] == 'supporting_context']
    observed = [i for i in items if i['bucket'] == 'observed']
    unknown_items = [i for i in items if i['bucket'] not in ('observed', 'supporting_context', 'inferred')]

    return {
        'read_only': True,
        'title': 'Link evidence (read-only)',
        'endpoints': {
            'from': _display_or_unknown(e.get('from')),
            'to': _display_or_unknown(e.get('to')),
            'f_port': _display_or_unknown(e.get('f_port') or e.get('local_port'), 'unknown'),
            't_port': _display_or_unknown(e.get('t_port') or e.get('remote_port'), 'unknown'),
        },
        'classification': {
            'protocol': _display_or_unknown(e.get('protocol')),
            'layer': _display_or_unknown(e.get('layer'), 'unknown'),
            'edge_kind': _display_or_unknown(e.get('edge_kind'), 'unknown'),
            'not_physical': bool(e.get('not_physical')),
            'cable_claim': (
                'supporting L3/IRB context — not cable proof'
                if (e.get('not_physical') or supporting)
                else (
                    'not a verified cable (one-sided)'
                    if (e.get('one_sided') or e.get('spoof_risk'))
                    else 'adjacency from neighbor protocol(s) — inspect evidence'
                )
            ),
        },
        'trust': {
            'confidence': _display_or_unknown(e.get('confidence'), 'unknown'),
            'trust_tier': _display_or_unknown(e.get('trust_tier'), 'unknown'),
            'trust_note': _s(e.get('trust_note')) or None,
        },
        'freshness': {
            'state': freshness,
            'conflict': freshness_conflict,
            'note': _s(e.get('freshness_note')) or None,
            'collected_at': e.get('collected_at') or None,
            'collected_at_latest': e.get('collected_at_latest') or None,
            'collected_at_display': _display_or_unknown(e.get('collected_at'), 'unknown'),
            'collected_at_latest_display': _display_or_unknown(
                e.get('collected_at_latest'), 'unknown'
            ),
        },
        'evidence_count': len(items),
        'evidence_summary': {
            'count': summary.get('count', len(items)),
            'protocols': list(summary.get('protocols') or []),
            'vendors': list(summary.get('vendors') or []),
        },
        'sections': {
            'observed': observed,
            'supporting_context': supporting,
            'inferred_conclusions': inferred,
            'conflicts': contradictions,
            'unknowns': unknown_items,
        },
        'evidence_items': items,
        'has_evidence': len(items) > 0,
        'empty_message': (
            None if items else
            'No supporting observations attached to this edge.'
        ),
    }


def _display_unobserved(value: Any) -> str:
    """UI label for empty ports — prefer unobserved over misleading 'unknown'."""
    text = _s(value)
    return text if text else '(unobserved)'


def build_incomplete_observation_model(obs: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Read-only inspector model for an incomplete discovery observation.

    Does not invent ports. Empty ports display as '(unobserved)', never as a
    fabricated interface name. Not an edge and not cable proof.
    """
    o = obs if isinstance(obs, dict) else {}
    gaps = [_s(g) for g in (o.get('evidence_gaps') or []) if _s(g)]
    warning = _s(o.get('parse_warning')) or 'incomplete observation'
    return {
        'read_only': True,
        'incomplete': True,
        'edge_eligible': False,
        'title': 'Incomplete discovery observation',
        'peer': {
            'hostname': _s(o.get('hostname')) or '(unobserved)',
            'platform': _s(o.get('platform')) or '(unobserved)',
            'protocol': _s(o.get('protocol')) or '(unobserved)',
        },
        'ports': {
            'local_port': _display_unobserved(o.get('local_port')),
            'remote_port': _display_unobserved(o.get('remote_port')),
            'local_port_raw': _s(o.get('local_port')),
            'remote_port_raw': _s(o.get('remote_port')),
        },
        'classification': {
            'observation_kind': 'incomplete',
            'cable_claim': 'incomplete observation — not a cable and not a map edge',
            'parse_source': _s(o.get('parse_source')) or '(unobserved)',
        },
        'evidence_gaps': gaps,
        'parse_warning': warning,
        'raw_fragment_present': bool(_s(o.get('raw_fragment'))),
    }
