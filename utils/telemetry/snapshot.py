"""Fixture-only series snapshot export (Phase 3 slice 5).

Answers: latest retained value per normalized series, plus last deterministic
delta when two compatible observations exist.

NON-GOALS
---------
- No live dashboards, scheduled exports, files, DBs, or network I/O.
- No alerting, topology, or trust decisions.
- ``generated_at`` is never taken from the system clock — caller supplies it
  or it is ``unknown``.
"""
from __future__ import annotations

import copy
import json
from typing import Any, Dict, List, Optional

from utils.telemetry.contract import UNKNOWN
from utils.telemetry.delta import (
    STATUS_UNAVAILABLE,
    empty_delta,
    latest_delta,
    order_observations,
    series_key,
)

SNAPSHOT_SCHEMA_VERSION = 'p3s5-1'


def _s(value: Any, default: str = '') -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _json_safe(value: Any) -> Any:
    """Ensure value is JSON-serializable; fall back to string for odd types."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return str(value)


def _serialize_delta(delta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(delta, dict):
        delta = empty_delta(
            delta_status=STATUS_UNAVAILABLE,
            notes=['no delta available'],
        )
    # Slim, JSON-safe projection — no nested raw observations
    return _json_safe({
        'previous_observation_id': delta.get('previous_observation_id'),
        'current_observation_id': delta.get('current_observation_id'),
        'comparison_basis': delta.get('comparison_basis') or UNKNOWN,
        'previous_value': delta.get('previous_value'),
        'current_value': delta.get('current_value'),
        'absolute_delta': delta.get('absolute_delta'),
        'direction': delta.get('direction') or UNKNOWN,
        'reset_detected': bool(delta.get('reset_detected')),
        'delta_status': delta.get('delta_status') or STATUS_UNAVAILABLE,
        'warnings': list(delta.get('warnings') or []),
        'notes': list(delta.get('notes') or []),
    })


def _series_summary(obs_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    ordered, basis = order_observations(obs_list)
    latest = ordered[-1]
    if len(ordered) >= 2:
        delta = latest_delta(ordered)
    else:
        delta = empty_delta(
            current_observation_id=latest.get('observation_id'),
            series_key=series_key(latest),
            metric_name=_s(latest.get('metric_name')) or UNKNOWN,
            entity_path=_s(latest.get('entity_path')) or UNKNOWN,
            comparison_basis=basis,
            current_value=latest.get('value'),
            delta_status=STATUS_UNAVAILABLE,
            notes=['single observation in series; delta unavailable'],
        )

    return _json_safe({
        'series_key': series_key(latest),
        'device_id': latest.get('device_id') or UNKNOWN,
        'metric_name': latest.get('metric_name') or UNKNOWN,
        'entity_path': latest.get('entity_path') or UNKNOWN,
        'unit': latest.get('unit') or UNKNOWN,
        'value_type': latest.get('value_type') or UNKNOWN,
        'metric_kind': latest.get('metric_kind') or UNKNOWN,
        'monotonic': latest.get('monotonic') or UNKNOWN,
        'catalog_status': latest.get('catalog_status') or UNKNOWN,
        'catalog_entry_id': latest.get('catalog_entry_id'),
        'latest_observation_id': latest.get('observation_id'),
        'latest_value': latest.get('value'),
        'latest_source_timestamp': latest.get('source_timestamp'),
        'latest_received_at': latest.get('received_at'),
        'latest_quality': latest.get('quality') or UNKNOWN,
        'observation_count': len(ordered),
        'ordering_basis': basis,
        'last_delta': _serialize_delta(delta),
        'delta_status': (delta or {}).get('delta_status') or STATUS_UNAVAILABLE,
        'reset_detected': bool((delta or {}).get('reset_detected')),
        'warnings': list(latest.get('warnings') or []),
        'notes': list(latest.get('notes') or []),
    })


def export_series_snapshot(
    store: Any,
    *,
    generated_at: Optional[str] = None,
    device_id: Optional[str] = None,
    metric_name: Optional[str] = None,
    entity_path: Optional[str] = None,
    catalog_status: Optional[str] = None,
    source_timestamp_start: Optional[str] = None,
    source_timestamp_end: Optional[str] = None,
    received_at_start: Optional[str] = None,
    received_at_end: Optional[str] = None,
    limit: Optional[int] = None,
    query_limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Build a deterministic JSON-compatible snapshot from an ObservationStore.

    ``generated_at``: caller-supplied export time, or ``unknown`` if omitted.
    Never reads the system clock.
    """
    export_notes: List[str] = []
    warnings: List[str] = []

    if generated_at is None or _s(generated_at) == '':
        gen = UNKNOWN
        export_notes.append('generated_at unknown — caller did not supply export time')
    else:
        gen = _s(generated_at)

    if limit is not None and int(limit) < 0:
        raise ValueError('limit must be >= 0')

    # Pull matching observations up to store capacity (retained set is already bounded).
    if query_limit is None:
        try:
            q_lim = max(int(store.stats().get('max_observations') or 1000), int(store.count() or 0), 1)
        except Exception:
            q_lim = 1000
    else:
        q_lim = int(query_limit)
    if q_lim < 0:
        raise ValueError('query_limit must be >= 0')

    rows = store.query(
        device_id=device_id,
        metric_name=metric_name,
        entity_path=entity_path,
        catalog_status=catalog_status,
        source_timestamp_start=source_timestamp_start,
        source_timestamp_end=source_timestamp_end,
        received_at_start=received_at_start,
        received_at_end=received_at_end,
        limit=int(q_lim),
    )

    # Group by series_key preserving first-seen order of keys via sorted keys for determinism
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for obs in rows:
        if not isinstance(obs, dict):
            continue
        if obs.get('quarantined'):
            continue
        key = series_key(obs)
        groups.setdefault(key, []).append(obs)

    summaries = [_series_summary(items) for _, items in sorted(groups.items(), key=lambda kv: kv[0])]

    if limit is not None:
        summaries = summaries[: int(limit)]

    snap = {
        'schema_version': SNAPSHOT_SCHEMA_VERSION,
        'generated_at': gen,
        'series_count': len(summaries),
        'observation_count': sum(int(s.get('observation_count') or 0) for s in summaries),
        'series': summaries,
        'warnings': warnings,
        'export_notes': export_notes,
    }
    # Defensive deep copy so callers cannot mutate internal lists by reference
    return copy.deepcopy(_json_safe(snap))


def snapshot_to_json(snapshot: Dict[str, Any], *, indent: Optional[int] = 2) -> str:
    """Serialize a snapshot to JSON text (fixture/test helper)."""
    return json.dumps(snapshot, indent=indent, sort_keys=True, default=str)
