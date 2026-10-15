"""Fixture-driven normalization of streaming telemetry observations.

Transport-neutral: accepts JSON-like dicts labeled by platform fixture family.
Does not open sockets, subscribe to devices, or invent source timestamps.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from utils.telemetry.contract import (
    PLATFORM_IOSXE,
    PLATFORM_JUNOS,
    PLATFORM_NXOS,
    UNKNOWN,
    assert_no_secrets_in_observation,
    compute_observation_id,
    empty_observation,
    is_secret_field_name,
)
from utils.telemetry.catalog import apply_catalog_to_observation


def _s(value: Any, default: str = '') -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _detect_secrets(payload: Any, path: str = '') -> List[str]:
    hits: List[str] = []
    if isinstance(payload, dict):
        for k, v in payload.items():
            key = str(k)
            here = f'{path}.{key}' if path else key
            if is_secret_field_name(key):
                hits.append(here)
            hits.extend(_detect_secrets(v, here))
    elif isinstance(payload, list):
        for i, item in enumerate(payload):
            hits.extend(_detect_secrets(item, f'{path}[{i}]'))
    return hits


def _platform_from_payload(raw: Dict[str, Any], hint: str = '') -> Tuple[str, str]:
    hint = _s(hint).lower()
    platform = _s(raw.get('platform') or raw.get('device_type') or hint).lower()
    vendor = _s(raw.get('vendor')).lower()
    if platform in ('cisco_xe', 'iosxe', 'ios-xe', 'cisco_iosxe'):
        return PLATFORM_IOSXE, vendor or 'cisco'
    if platform in ('cisco_nxos', 'nxos', 'nx-os'):
        return PLATFORM_NXOS, vendor or 'cisco'
    if platform in ('juniper_junos', 'junos', 'juniper'):
        return PLATFORM_JUNOS, vendor or 'juniper'
    if 'iosxe' in hint or 'ios-xe' in hint or hint == 'cisco_xe':
        return PLATFORM_IOSXE, vendor or 'cisco'
    if 'nxos' in hint or hint == 'cisco_nxos':
        return PLATFORM_NXOS, vendor or 'cisco'
    if 'junos' in hint or 'juniper' in hint:
        return PLATFORM_JUNOS, vendor or 'juniper'
    return (platform or UNKNOWN), (vendor or UNKNOWN)


def _coerce_value(raw_value: Any) -> Tuple[Any, str, List[str]]:
    """Return (value, value_type, warnings). Malformed → quarantined caller decides."""
    warnings: List[str] = []
    if raw_value is None:
        return None, UNKNOWN, ['value missing']
    if isinstance(raw_value, bool):
        return raw_value, 'bool', warnings
    if isinstance(raw_value, int) and not isinstance(raw_value, bool):
        return raw_value, 'int', warnings
    if isinstance(raw_value, float):
        return raw_value, 'float', warnings
    if isinstance(raw_value, str):
        text = raw_value.strip()
        if not text or text.lower() in ('unknown', 'n/a', 'na', '-'):
            return None, UNKNOWN, ['value unknown string']
        # numeric strings
        try:
            if '.' in text or 'e' in text.lower():
                return float(text), 'float', warnings
            return int(text), 'int', warnings
        except ValueError:
            return text, 'str', warnings
    warnings.append(f'unsupported value type {type(raw_value).__name__}')
    return None, UNKNOWN, warnings


def _extract_paths(raw: Dict[str, Any]) -> Tuple[str, str, str, str]:
    """metric_name, metric_path, metric_path_raw, entity_path."""
    path_raw = _s(
        raw.get('metric_path_raw')
        or raw.get('path')
        or raw.get('sensor_path')
        or raw.get('xpath')
        or raw.get('metric')
    )
    path_norm = _s(raw.get('metric_path') or path_raw)
    name = _s(
        raw.get('metric_name')
        or raw.get('leaf')
        or raw.get('name')
        or (path_norm.split('/')[-1] if path_norm else '')
    )
    entity = _s(
        raw.get('entity_path')
        or raw.get('interface')
        or raw.get('if_name')
        or raw.get('entity')
        or raw.get('component')
    )
    return (
        name or UNKNOWN,
        path_norm or UNKNOWN,
        path_raw or UNKNOWN,
        entity or UNKNOWN,
    )


def _source_timestamp(raw: Dict[str, Any]) -> Tuple[Optional[str], List[str]]:
    """Preserve source time only when present; never invent."""
    notes: List[str] = []
    for key in (
        'source_timestamp',
        'timestamp',
        'collection_id',
        'msg_timestamp',
        'event_time',
        'time',
    ):
        if key not in raw:
            continue
        val = raw.get(key)
        if val is None or val == '':
            notes.append(f'{key} present but empty → unknown')
            return None, notes
        # Reject non-scalar fabricated placeholders
        text = _s(val)
        if text.lower() in ('unknown', 'n/a', 'none'):
            notes.append(f'{key} explicitly unknown')
            return None, notes
        return text, notes
    notes.append('source_timestamp absent')
    return None, notes


def normalize_observation(
    payload: Any,
    *,
    platform_hint: str = '',
    received_at: Optional[str] = None,
    source_protocol: str = 'fixture',
) -> Dict[str, Any]:
    """Normalize one telemetry payload into the Phase 3 observation contract.

    ``received_at`` is applied only when the caller (collector boundary) supplies it.
    """
    warnings: List[str] = []
    notes: List[str] = []

    if not isinstance(payload, dict):
        obs = empty_observation(
            quarantined=True,
            quality='error',
            warnings=['payload is not an object'],
            notes=['quarantined: malformed root'],
            source_protocol=_s(source_protocol) or UNKNOWN,
            received_at=received_at,
        )
        obs['observation_id'] = compute_observation_id(obs)
        return apply_catalog_to_observation(obs)

    secret_hits = _detect_secrets(payload)
    if secret_hits:
        obs = empty_observation(
            device_id=_s(payload.get('device_id') or payload.get('hostname') or payload.get('device'))
            or UNKNOWN,
            quarantined=True,
            quality='error',
            warnings=[f'secret field rejected: {h}' for h in secret_hits[:8]],
            notes=['quarantined: secret-like fields must not enter the model'],
            source_protocol=_s(source_protocol) or UNKNOWN,
            received_at=received_at,
        )
        # Do not copy secret values into the observation
        obs['observation_id'] = compute_observation_id(obs)
        return apply_catalog_to_observation(obs)

    platform, vendor = _platform_from_payload(payload, platform_hint)
    device_id = _s(
        payload.get('device_id') or payload.get('hostname') or payload.get('device') or payload.get('sysName')
    ) or UNKNOWN
    metric_name, metric_path, metric_path_raw, entity_path = _extract_paths(payload)
    value, value_type, value_warnings = _coerce_value(
        payload.get('value', payload.get('val', payload.get('metric_value')))
    )
    warnings.extend(value_warnings)

    unit = _s(payload.get('unit') or payload.get('units')) or UNKNOWN
    if unit == UNKNOWN:
        notes.append('unit unknown')

    src_ts, ts_notes = _source_timestamp(payload)
    notes.extend(ts_notes)

    seq_raw = payload.get('sequence', payload.get('seq', payload.get('msg_id')))
    sequence: Any = None
    if seq_raw is not None and seq_raw != '':
        try:
            sequence = int(seq_raw)
        except (TypeError, ValueError):
            sequence = _s(seq_raw)
            warnings.append('sequence not integer; preserved as string')

    quality = _s(payload.get('quality') or payload.get('status')).lower() or 'ok'
    quarantined = False
    if metric_name == UNKNOWN and metric_path == UNKNOWN:
        quarantined = True
        quality = 'error'
        notes.append('quarantined: missing metric identity')
    elif value is None and 'unsupported value type' in ' '.join(warnings):
        quarantined = True
        quality = 'error'
        notes.append('quarantined: malformed value')
    elif src_ts is None:
        if quality == 'ok':
            quality = UNKNOWN
        notes.append('source_timestamp unknown')

    if metric_name == UNKNOWN and metric_path != UNKNOWN:
        notes.append('metric_name unknown; path retained')

    obs = empty_observation(
        device_id=device_id,
        platform=platform,
        vendor=vendor,
        metric_name=metric_name,
        metric_path=metric_path,
        metric_path_raw=metric_path_raw,
        value=value,
        value_type=value_type,
        unit=unit,
        source_timestamp=src_ts,
        received_at=received_at,  # only if caller provided
        source_protocol=_s(source_protocol) or UNKNOWN,
        entity_path=entity_path,
        sequence=sequence,
        quality=quality if quality else UNKNOWN,
        warnings=warnings,
        notes=notes,
        quarantined=quarantined,
    )
    obs['observation_id'] = compute_observation_id(obs)
    assert_no_secrets_in_observation(obs)
    return apply_catalog_to_observation(obs)


def normalize_batch(
    payloads: List[Any],
    *,
    platform_hint: str = '',
    received_at: Optional[str] = None,
    source_protocol: str = 'fixture',
) -> Dict[str, Any]:
    """Normalize a batch; quarantine individuals without failing the whole batch.

    Duplicate handling: first observation_id wins; later copies set
    ``duplicate_of`` and ``quarantined`` with a duplicate note (deterministic).
    """
    accepted: List[Dict[str, Any]] = []
    quarantined: List[Dict[str, Any]] = []
    seen: Dict[str, str] = {}

    for item in payloads or []:
        obs = normalize_observation(
            item,
            platform_hint=platform_hint,
            received_at=received_at,
            source_protocol=source_protocol,
        )
        oid = obs['observation_id']
        if oid in seen:
            obs = dict(obs)
            obs['duplicate_of'] = seen[oid]
            obs['quarantined'] = True
            obs['notes'] = list(obs.get('notes') or []) + ['duplicate observation_id; first wins']
            obs['quality'] = 'error'
            quarantined.append(obs)
            continue
        seen[oid] = oid
        if obs.get('quarantined'):
            quarantined.append(obs)
        else:
            accepted.append(obs)

    return {
        'accepted': accepted,
        'quarantined': quarantined,
        'count_in': len(payloads or []),
        'count_accepted': len(accepted),
        'count_quarantined': len(quarantined),
    }


def load_fixture_json(path: str) -> Any:
    """Load a telemetry fixture file (JSON object or array)."""
    with open(path, encoding='utf-8') as f:
        return json.load(f)
