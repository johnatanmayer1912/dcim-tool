"""UI-facing stroke fields for overlay paint. Topology is never computed here."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

NO_SAMPLE_COLOR = '#64748b'
OK_COLOR = '#22c55e'
WARN_COLOR = '#eab308'
HOT_COLOR = '#ef4444'
NO_SAMPLE_DASH: List[int] = [5, 4]
PARTIAL_DASH: List[int] = [4, 3]

TRUTH_SENTENCE = (
    'Paint is not topology. Gray dashed = no sample — not down. '
    'Overlay never creates cables. Not a forwarding path, QoS class, or cable certification.'
)
REPLAY_LABEL = 'Replay snapshot — not a live poll.'
LIVE_LABEL = 'Live SSH counters — not SNMP.'
PARTIAL_LABEL = 'One side sampled — not a full duplex measurement.'
STALE_LABEL = 'STALE — last sample older than policy. Colors kept; do not treat as current load.'
NO_SAMPLE_LABEL = 'No utilization sample for this link.'
BANNER = (
    'Utilization paints existing L2 links only. It is not topology. '
    'Gray dashed = no sample — not down. Overlay never creates cables.'
)


def color_for_pct(pct: Optional[float]) -> str:
    if pct is None:
        return NO_SAMPLE_COLOR
    try:
        value = float(pct)
    except (TypeError, ValueError):
        return NO_SAMPLE_COLOR
    if value >= 90:
        return HOT_COLOR
    if value >= 70:
        return WARN_COLOR
    return OK_COLOR


def width_for_pct(pct: Optional[float]) -> int:
    if pct is None:
        return 2
    try:
        value = float(pct)
    except (TypeError, ValueError):
        return 2
    if value >= 90:
        return 4
    return 3


def stroke_for_paint(paint: Dict[str, Any]) -> Dict[str, Any]:
    """Map paint_state (+ pct) to vis stroke. Unsampled is gray dashed, not down."""
    state = str(paint.get('paint_state') or 'no_sample')
    pct = paint.get('pct')
    if pct is None:
        ins = [x for x in (paint.get('in_pct'), paint.get('out_pct')) if x is not None]
        pct = max(ins) if ins else None
    if state in ('no_sample', 'no_speed', 'invalid', 'unmapped_endpoint'):
        return {
            'color': NO_SAMPLE_COLOR,
            'width': 2,
            'dashes': list(NO_SAMPLE_DASH),
            'meaning': 'no_sample',
        }
    if state == 'partial':
        return {
            'color': color_for_pct(pct),
            'width': 3,
            'dashes': list(PARTIAL_DASH),
            'meaning': 'partial',
        }
    if state == 'stale':
        return {
            'color': color_for_pct(pct),
            'width': width_for_pct(pct),
            'dashes': False,
            'meaning': 'stale',
        }
    if state == 'hot' or (state == 'ok' and pct is not None and float(pct) >= 90):
        return {'color': HOT_COLOR, 'width': 4, 'dashes': False, 'meaning': 'hot'}
    if state == 'warn' or (pct is not None and 70 <= float(pct) < 90):
        return {'color': WARN_COLOR, 'width': 3, 'dashes': False, 'meaning': 'warn'}
    if state == 'ok':
        return {'color': OK_COLOR, 'width': 3, 'dashes': False, 'meaning': 'ok'}
    return {
        'color': NO_SAMPLE_COLOR,
        'width': 2,
        'dashes': list(NO_SAMPLE_DASH),
        'meaning': 'no_sample',
    }


def no_sample_stroke() -> Dict[str, Any]:
    return {
        'color': NO_SAMPLE_COLOR,
        'width': 2,
        'dashes': list(NO_SAMPLE_DASH),
        'meaning': 'no_sample',
    }


def ui_paint_view(paint: Dict[str, Any], document: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Computed inspector/renderer view. Raw fixture fields do not drive the UI."""
    doc = document or {}
    stroke = stroke_for_paint(paint)
    join = paint.get('join') if isinstance(paint.get('join'), dict) else {}
    prov = paint.get('provenance') if isinstance(paint.get('provenance'), dict) else {}
    fresh = paint.get('freshness') if isinstance(paint.get('freshness'), dict) else {}
    mode = prov.get('mode') or doc.get('mode') or 'replay'
    evidence = prov.get('evidence_class') or doc.get('evidence_class') or 'fixture'
    stale = bool(fresh.get('stale'))
    state = str(paint.get('paint_state') or 'no_sample')
    labels = [BANNER]
    if mode == 'replay':
        labels.append(REPLAY_LABEL)
    elif mode == 'live':
        labels.append(LIVE_LABEL)
    if state == 'partial' or join.get('status') == 'partial':
        labels.append(PARTIAL_LABEL)
    if stale or state == 'stale':
        labels.append(STALE_LABEL)
    labels.append(TRUTH_SENTENCE)
    return {
        'cable_key': paint.get('cable_key'),
        'paint_state': state,
        'stroke': stroke,
        'in_bps': paint.get('in_bps'),
        'out_bps': paint.get('out_bps'),
        'in_pct': paint.get('in_pct'),
        'out_pct': paint.get('out_pct'),
        'pct': paint.get('pct'),
        'if_speed_bps': paint.get('if_speed_bps'),
        'join_status': join.get('status'),
        'join_sides': list(join.get('sides') or []),
        'mode': mode,
        'evidence_class': evidence,
        'job_id': prov.get('job_id') or doc.get('topology_job_id'),
        'sampled_at': fresh.get('sampled_at'),
        'age_seconds': fresh.get('age_seconds'),
        'stale': stale,
        'labels': labels,
        'truth': TRUTH_SENTENCE,
        'replay_label': REPLAY_LABEL if mode == 'replay' else '',
        'live_label': LIVE_LABEL if mode == 'live' else '',
    }
