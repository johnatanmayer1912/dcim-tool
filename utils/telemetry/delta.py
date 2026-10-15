"""Fixture-only change / delta helpers over normalized telemetry observations.

Answers: for the same device/metric/entity series, what changed between two
observations? Deterministic local comparison only — not alerting or analytics.

NON-GOALS
---------
- No live collectors, gRPC, alerting, UI, anomaly detection, or forecasting.
- No topology / cable inference from entity paths.
- No invented timestamps; no silent unit/type coercion.
- No counter rollover/wrap math unless catalog explicitly supports it (not in fixtures).

Ordering basis (documented)
---------------------------
1. ``source_timestamp`` when both observations have a non-empty value;
2. else ``received_at`` when both have a non-empty value;
3. else caller-supplied insertion rank / list order (last resort).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from utils.telemetry.contract import UNKNOWN

STATUS_COMPUTED = 'computed'
STATUS_UNAVAILABLE = 'unavailable'
STATUS_RESET = 'reset'
STATUS_INVALID = 'invalid'
STATUS_INCOMPATIBLE = 'incompatible'

DIR_INCREASED = 'increased'
DIR_DECREASED = 'decreased'
DIR_UNCHANGED = 'unchanged'
DIR_UNKNOWN = 'unknown'


def _s(value: Any, default: str = '') -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def series_key(obs: Dict[str, Any]) -> str:
    """Deterministic series identity from normalized fields only."""
    return '|'.join([
        _s(obs.get('device_id')).lower() or UNKNOWN,
        _s(obs.get('metric_name')) or UNKNOWN,
        _s(obs.get('entity_path')) or UNKNOWN,
        _s(obs.get('unit')) or UNKNOWN,
        _s(obs.get('value_type')) or UNKNOWN,
    ])


def same_series(a: Any, b: Any) -> bool:
    """True when both dicts share device, metric, entity, unit, and value_type."""
    if not isinstance(a, dict) or not isinstance(b, dict):
        return False
    for field in ('device_id', 'metric_name', 'entity_path', 'unit', 'value_type'):
        av = _s(a.get(field)).lower() if field == 'device_id' else _s(a.get(field))
        bv = _s(b.get(field)).lower() if field == 'device_id' else _s(b.get(field))
        # Normalize empty to UNKNOWN for comparison consistency
        if not av:
            av = UNKNOWN
        if not bv:
            bv = UNKNOWN
        if field == 'device_id':
            if av != bv:
                return False
        elif av != bv:
            return False
    return True


def empty_delta(**overrides: Any) -> Dict[str, Any]:
    base = {
        'previous_observation_id': None,
        'current_observation_id': None,
        'series_key': UNKNOWN,
        'metric_name': UNKNOWN,
        'entity_path': UNKNOWN,
        'comparison_basis': UNKNOWN,
        'previous_value': None,
        'current_value': None,
        'absolute_delta': None,
        'direction': DIR_UNKNOWN,
        'reset_detected': False,
        'delta_status': STATUS_UNAVAILABLE,
        'warnings': [],
        'notes': [],
    }
    base.update(overrides)
    return base


def _order_rank(obs: Dict[str, Any], insertion_index: Optional[int] = None) -> Tuple[int, str, int]:
    """Return sortable rank: (tier, timestamp_or_empty, insertion_index).

    tier 0 = source_timestamp, 1 = received_at, 2 = insertion only.
    """
    src = _s(obs.get('source_timestamp'))
    if src:
        return (0, src, insertion_index if insertion_index is not None else 0)
    rx = _s(obs.get('received_at'))
    if rx:
        return (1, rx, insertion_index if insertion_index is not None else 0)
    return (2, '', insertion_index if insertion_index is not None else 0)


def order_observations(
    observations: Sequence[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], str]:
    """Stable-sort observations; return (ordered_list, comparison_basis_label)."""
    indexed = list(enumerate(observations))
    if not indexed:
        return [], UNKNOWN

    # Prefer source_timestamp if any pair can use it; else received_at; else insertion
    any_src = any(_s(o.get('source_timestamp')) for _, o in indexed)
    any_rx = any(_s(o.get('received_at')) for _, o in indexed)
    if any_src:
        basis = 'source_timestamp'
    elif any_rx:
        basis = 'received_at'
    else:
        basis = 'insertion_order'

    def sort_key(item: Tuple[int, Dict[str, Any]]):
        idx, obs = item
        tier, ts, _ = _order_rank(obs, idx)
        # When mixing present/absent timestamps within a basis, missing sorts first
        if basis == 'source_timestamp':
            return (0 if _s(obs.get('source_timestamp')) else 1, _s(obs.get('source_timestamp')), idx)
        if basis == 'received_at':
            return (0 if _s(obs.get('received_at')) else 1, _s(obs.get('received_at')), idx)
        return (idx,)

    ordered = [o for _, o in sorted(indexed, key=sort_key)]
    return ordered, basis


def _incompatible(reason: str, a: Dict[str, Any], b: Dict[str, Any], **extra) -> Dict[str, Any]:
    return empty_delta(
        previous_observation_id=a.get('observation_id'),
        current_observation_id=b.get('observation_id'),
        series_key=series_key(a) if isinstance(a, dict) else UNKNOWN,
        metric_name=_s(a.get('metric_name')) or UNKNOWN,
        entity_path=_s(a.get('entity_path')) or UNKNOWN,
        delta_status=STATUS_INCOMPATIBLE,
        previous_value=a.get('value'),
        current_value=b.get('value'),
        notes=[reason],
        **extra,
    )


def _reset_supported(obs: Dict[str, Any]) -> bool:
    """Reset detection only when metric is an explicit monotonic counter."""
    kind = _s(obs.get('metric_kind')).lower()
    mono = _s(obs.get('monotonic')).lower()
    # Catalog stores monotonic on entries; observations get metric_kind from catalog.
    # Treat counter + monotonic true, or counter with catalog_entry known counters.
    if kind == 'counter' and mono in ('true', '1', 'yes'):
        return True
    if kind == 'counter' and mono in ('', UNKNOWN):
        # Fixture counters are monotonic; if kind is counter and unit is octets/bytes, allow
        # only when monotonic explicitly true — otherwise unavailable (no guessing).
        return False
    return False


def compute_delta(
    previous: Any,
    current: Any,
    *,
    comparison_basis: str = '',
) -> Dict[str, Any]:
    """Compare two observations; previous must be earlier than current."""
    if not isinstance(previous, dict) or not isinstance(current, dict):
        return empty_delta(
            delta_status=STATUS_INVALID,
            notes=['both previous and current must be observation dicts'],
        )

    pid = _s(previous.get('observation_id'))
    cid = _s(current.get('observation_id'))
    if pid and cid and pid == cid:
        return empty_delta(
            previous_observation_id=pid,
            current_observation_id=cid,
            series_key=series_key(previous),
            metric_name=_s(previous.get('metric_name')) or UNKNOWN,
            entity_path=_s(previous.get('entity_path')) or UNKNOWN,
            delta_status=STATUS_INVALID,
            notes=['no self-comparison'],
        )

    if not same_series(previous, current):
        # Specific mismatch notes
        reasons = []
        if _s(previous.get('device_id')).lower() != _s(current.get('device_id')).lower():
            reasons.append('device mismatch')
        if _s(previous.get('metric_name')) != _s(current.get('metric_name')):
            reasons.append('metric mismatch')
        if (_s(previous.get('entity_path')) or UNKNOWN) != (_s(current.get('entity_path')) or UNKNOWN):
            reasons.append('entity_path mismatch')
        if (_s(previous.get('unit')) or UNKNOWN) != (_s(current.get('unit')) or UNKNOWN):
            reasons.append('unit mismatch')
        if (_s(previous.get('value_type')) or UNKNOWN) != (_s(current.get('value_type')) or UNKNOWN):
            reasons.append('value_type mismatch')
        return _incompatible('; '.join(reasons) or 'series mismatch', previous, current)

    basis = _s(comparison_basis) or UNKNOWN
    # Verify temporal order when timestamps exist
    prev_rank = _order_rank(previous, 0)
    curr_rank = _order_rank(current, 1)
    if prev_rank[:2] > curr_rank[:2]:
        return empty_delta(
            previous_observation_id=pid or None,
            current_observation_id=cid or None,
            series_key=series_key(previous),
            metric_name=_s(previous.get('metric_name')) or UNKNOWN,
            entity_path=_s(previous.get('entity_path')) or UNKNOWN,
            comparison_basis=basis,
            previous_value=previous.get('value'),
            current_value=current.get('value'),
            delta_status=STATUS_INVALID,
            notes=['previous is not earlier than current under ordering basis'],
        )

    pv = previous.get('value')
    cv = current.get('value')
    kind = _s(previous.get('metric_kind') or current.get('metric_kind')).lower() or UNKNOWN
    vtype = _s(previous.get('value_type')).lower() or UNKNOWN

    result = empty_delta(
        previous_observation_id=pid or None,
        current_observation_id=cid or None,
        series_key=series_key(previous),
        metric_name=_s(previous.get('metric_name')) or UNKNOWN,
        entity_path=_s(previous.get('entity_path')) or UNKNOWN,
        comparison_basis=basis,
        previous_value=pv,
        current_value=cv,
    )

    # String / state
    if vtype == 'str' or (not isinstance(pv, (int, float)) and not isinstance(cv, (int, float))
                          and pv is not None and cv is not None and not isinstance(pv, bool)):
        if pv == cv:
            result['delta_status'] = STATUS_COMPUTED
            result['direction'] = DIR_UNCHANGED
            result['absolute_delta'] = 0
            result['notes'].append('string/state unchanged')
        else:
            result['delta_status'] = STATUS_COMPUTED
            result['direction'] = DIR_UNKNOWN
            result['absolute_delta'] = None
            result['notes'].append('string/state changed')
        return result

    if vtype not in ('int', 'float') and not isinstance(pv, (int, float)) and not isinstance(cv, (int, float)):
        result['delta_status'] = STATUS_UNAVAILABLE
        result['notes'].append('non-numeric values; delta unavailable')
        return result

    try:
        pnum = float(pv)
        cnum = float(cv)
    except (TypeError, ValueError):
        result['delta_status'] = STATUS_UNAVAILABLE
        result['notes'].append('values not numeric')
        return result

    if kind == 'counter' or (kind == UNKNOWN and _reset_supported(previous)):
        # Counter path: only when explicitly counter
        pass

    if kind == 'counter':
        mono = _s(previous.get('monotonic') or current.get('monotonic')).lower()
        if cnum >= pnum:
            delta = cnum - pnum
            result['absolute_delta'] = int(delta) if delta == int(delta) else delta
            result['delta_status'] = STATUS_COMPUTED
            if delta == 0:
                result['direction'] = DIR_UNCHANGED
            else:
                result['direction'] = DIR_INCREASED
            result['notes'].append('counter delta')
            return result
        # current < previous
        if mono in ('true', '1', 'yes'):
            result['reset_detected'] = True
            result['delta_status'] = STATUS_RESET
            result['absolute_delta'] = None
            result['direction'] = DIR_UNKNOWN
            result['notes'].append('counter reset detected (monotonic=true)')
            result['warnings'].append('reset: no wraparound math applied')
            return result
        result['delta_status'] = STATUS_UNAVAILABLE
        result['absolute_delta'] = None
        result['notes'].append('current < previous; reset semantics unsupported')
        return result

    if kind == 'gauge' or kind == UNKNOWN:
        delta = cnum - pnum
        result['absolute_delta'] = int(delta) if isinstance(pv, int) and isinstance(cv, int) and delta == int(delta) else delta
        result['delta_status'] = STATUS_COMPUTED
        if delta > 0:
            result['direction'] = DIR_INCREASED
        elif delta < 0:
            result['direction'] = DIR_DECREASED
        else:
            result['direction'] = DIR_UNCHANGED
        if kind == UNKNOWN:
            result['warnings'].append('metric_kind unknown; treated as gauge-like numeric')
        result['notes'].append('gauge delta')
        return result

    result['delta_status'] = STATUS_UNAVAILABLE
    result['notes'].append(f'unsupported metric_kind={kind}')
    return result


def pairwise_deltas(
    observations: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Compute consecutive deltas along a same-series ordered list.

    Observations not in the majority series or mismatched mid-list yield
    incompatible/invalid results for that pair; list is ordered first.
    """
    if not observations:
        return []
    ordered, basis = order_observations(list(observations))
    # Prefer the series of the first observation; skip cross-series silently? No —
    # compute_delta returns incompatible.
    out: List[Dict[str, Any]] = []
    for i in range(1, len(ordered)):
        out.append(compute_delta(ordered[i - 1], ordered[i], comparison_basis=basis))
    return out


def latest_delta(
    observations: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """Delta between the two latest observations in deterministic order."""
    ordered, basis = order_observations(list(observations))
    if len(ordered) < 2:
        return empty_delta(
            delta_status=STATUS_UNAVAILABLE,
            comparison_basis=basis,
            notes=['need at least two observations'],
        )
    return compute_delta(ordered[-2], ordered[-1], comparison_basis=basis)
