"""Phase 3 streaming telemetry — transport-neutral observation contract.

NON-GOALS (this package / Phase 3 slice 1)
=========================================
- No live gRPC / gNMI / NETCONF / SSH / dial-out listeners.
- No device subscriptions, authentication, or credential storage.
- No production ingestion pipeline, alerting, or UI.
- No topology edge creation, trust mutation, or cable proof from paths.
- No Arista support; no live vendor compatibility claims.
- No protobuf/gRPC dependency; fixture JSON only.

Timestamp rules
---------------
- ``source_timestamp``: device/export time when present in the payload; never invented.
- ``received_at``: set only by an explicit collector boundary argument; never copied
  from source time and never synthesized when absent.
- Missing source time → ``None`` with quality/notes marking ``unknown``.
"""
from __future__ import annotations

from typing import Any, Dict, Final, Optional, Tuple

# Explicit unknown sentinel for string fields in the normalized model.
UNKNOWN: Final[str] = 'unknown'

# Supported fixture platform labels (not live compatibility claims).
PLATFORM_IOSXE: Final[str] = 'cisco_xe'
PLATFORM_NXOS: Final[str] = 'cisco_nxos'
PLATFORM_JUNOS: Final[str] = 'juniper_junos'

SECRET_FIELD_NAMES: Final[Tuple[str, ...]] = (
    'password',
    'passwd',
    'secret',
    'token',
    'api_key',
    'apikey',
    'private_key',
    'privatekey',
    'credential',
    'credentials',
    'auth',
    'authorization',
    'bearer',
    'community',
    'snmp_community',
    'enable_secret',
)


def observation_field_names() -> Tuple[str, ...]:
    """Canonical keys of a normalized telemetry observation."""
    return (
        'observation_id',
        'device_id',
        'platform',
        'vendor',
        'metric_name',
        'metric_path',
        'metric_path_raw',
        'value',
        'value_type',
        'unit',
        'source_timestamp',
        'received_at',
        'source_protocol',
        'entity_path',
        'sequence',
        'quality',
        'warnings',
        'notes',
        'quarantined',
        'duplicate_of',
        # Phase 3 slice 2 — catalog enrichment (backward-compatible)
        'catalog_status',
        'catalog_entry_id',
        'catalog_matches',
        'metric_kind',
        'entity_kind',
        'monotonic',
    )


def empty_observation(**overrides: Any) -> Dict[str, Any]:
    """Return a fully keyed observation with explicit unknowns / empty lists."""
    base: Dict[str, Any] = {
        'observation_id': '',
        'device_id': UNKNOWN,
        'platform': UNKNOWN,
        'vendor': UNKNOWN,
        'metric_name': UNKNOWN,
        'metric_path': UNKNOWN,
        'metric_path_raw': UNKNOWN,
        'value': None,
        'value_type': UNKNOWN,
        'unit': UNKNOWN,
        'source_timestamp': None,
        'received_at': None,
        'source_protocol': UNKNOWN,
        'entity_path': UNKNOWN,
        'sequence': None,
        'quality': UNKNOWN,
        'warnings': [],
        'notes': [],
        'quarantined': False,
        'duplicate_of': None,
        'catalog_status': UNKNOWN,
        'catalog_entry_id': None,
        'catalog_matches': [],
        'metric_kind': UNKNOWN,
        'entity_kind': UNKNOWN,
        'monotonic': UNKNOWN,
    }
    base.update(overrides)
    return base


def is_secret_field_name(name: str) -> bool:
    n = (name or '').strip().lower().replace('-', '_')
    if n in SECRET_FIELD_NAMES:
        return True
    return any(s in n for s in ('password', 'secret', 'token', 'private_key', 'api_key'))


def observation_identity_parts(obs: Dict[str, Any]) -> Tuple[str, ...]:
    """Stable identity tuple — no secrets, no array index, no invented timestamps."""
    return (
        str(obs.get('device_id') or UNKNOWN).strip().lower(),
        str(obs.get('metric_path') or obs.get('metric_name') or UNKNOWN).strip().lower(),
        str(obs.get('entity_path') or UNKNOWN).strip().lower(),
        str(obs.get('source_timestamp') or 'unknown'),
        str(obs.get('sequence') if obs.get('sequence') is not None else 'none'),
    )


def compute_observation_id(obs: Dict[str, Any]) -> str:
    """Deterministic observation id from identity parts (hex digest of joined key)."""
    import hashlib

    key = '|'.join(observation_identity_parts(obs))
    return hashlib.sha256(key.encode('utf-8')).hexdigest()[:24]


def assert_no_secrets_in_observation(obs: Optional[Dict[str, Any]]) -> None:
    """Raise ValueError if a normalized observation embeds secret-like keys/values."""
    if not isinstance(obs, dict):
        return
    for k, v in obs.items():
        if is_secret_field_name(str(k)):
            raise ValueError(f'secret field not allowed in observation: {k}')
        if isinstance(v, dict):
            assert_no_secrets_in_observation(v)
