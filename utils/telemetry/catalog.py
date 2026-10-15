"""Fixture-only metric catalog / path registry (Phase 3 slice 2).

Answers: given platform + raw path, is the path known and what metadata apply?

NON-GOALS
---------
- No live sensors, SNMP walk, gRPC, or vendor capability discovery.
- No topology / cable / trust inference from metric paths.
- No fuzzy path matching; exact paths only (plus optional explicit generic entries).
- Catalog coverage is limited to fixture-backed paths in this repository.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from utils.telemetry.contract import (
    PLATFORM_IOSXE,
    PLATFORM_JUNOS,
    PLATFORM_NXOS,
    UNKNOWN,
    is_secret_field_name,
)

CATALOG_VERSION = 'p3s2-1'

# Status values for lookup / observation.catalog_status
STATUS_KNOWN = 'known'
STATUS_UNKNOWN = 'unknown'
STATUS_AMBIGUOUS = 'ambiguous'
STATUS_INVALID = 'invalid'


def _s(value: Any, default: str = '') -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def empty_catalog_entry(**overrides: Any) -> Dict[str, Any]:
    base = {
        'entry_id': UNKNOWN,
        'metric_name': UNKNOWN,
        'platforms': (),
        'raw_path': UNKNOWN,
        'normalized_path': UNKNOWN,
        'value_type': UNKNOWN,
        'unit': UNKNOWN,
        'entity_kind': UNKNOWN,
        'entity_required': False,
        'metric_kind': UNKNOWN,  # counter | gauge | unknown
        'monotonic': UNKNOWN,  # true | false | unknown (string)
        'notes': [],
        'catalog_version': CATALOG_VERSION,
    }
    base.update(overrides)
    return base


def empty_lookup_result(**overrides: Any) -> Dict[str, Any]:
    base = {
        'status': STATUS_UNKNOWN,
        'entry': None,
        'matches': [],
        'warnings': [],
        'notes': [],
        'catalog_version': CATALOG_VERSION,
    }
    base.update(overrides)
    return base


def _fixture_catalog() -> Tuple[Dict[str, Any], ...]:
    """Exact paths from Phase 3 slice 1 fixtures only — not a vendor capability map."""
    return (
        empty_catalog_entry(
            entry_id='iosxe.if.in_octets',
            metric_name='interface_in_octets',
            platforms=(PLATFORM_IOSXE,),
            raw_path='Cisco-IOS-XE-interfaces-oper:interfaces/interface/statistics/in-octets',
            normalized_path='interfaces/interface/statistics/in-octets',
            value_type='int',
            unit='octets',
            entity_kind='interface',
            entity_required=True,
            metric_kind='counter',
            monotonic='true',
            notes=['fixture: iosxe_interface_counters.json'],
        ),
        empty_catalog_entry(
            entry_id='iosxe.if.out_octets',
            metric_name='interface_out_octets',
            platforms=(PLATFORM_IOSXE,),
            raw_path='interfaces/interface/statistics/out-octets',
            normalized_path='interfaces/interface/statistics/out-octets',
            value_type='int',
            unit='octets',
            entity_kind='interface',
            entity_required=True,
            metric_kind='counter',
            monotonic='true',
            notes=['fixture: missing_timestamp.json path'],
        ),
        empty_catalog_entry(
            entry_id='nxos.if.in_octets',
            metric_name='interface_in_octets',
            platforms=(PLATFORM_NXOS,),
            raw_path='sys/intf/phys-[eth1/1]/dbgStats/inOctets',
            normalized_path='sys/intf/phys/dbgStats/inOctets',
            value_type='int',
            unit='bytes',
            entity_kind='interface',
            entity_required=True,
            metric_kind='counter',
            monotonic='true',
            notes=['fixture: nxos_interface_counters.json — path is instance-specific'],
        ),
        empty_catalog_entry(
            entry_id='junos.optics.rx_power',
            metric_name='optics_rx_power',
            platforms=(PLATFORM_JUNOS,),
            raw_path="/interfaces/interface[name='xe-0/0/0']/optics/rx-power",
            normalized_path='interfaces/interface/optics/rx-power',
            value_type='float',
            unit='dBm',
            entity_kind='interface',
            entity_required=True,
            metric_kind='gauge',
            monotonic='false',
            notes=['fixture: junos_interface_optics.json'],
        ),
        # Intentional ambiguous pair for deterministic ambiguity tests (same path+platform).
        empty_catalog_entry(
            entry_id='test.ambiguous.a',
            metric_name='ambiguous_metric_a',
            platforms=(PLATFORM_IOSXE,),
            raw_path='test/ambiguous/sensor',
            normalized_path='test/ambiguous/sensor',
            value_type='int',
            unit='count',
            entity_kind='unknown',
            metric_kind='gauge',
            notes=['synthetic ambiguous entry A'],
        ),
        empty_catalog_entry(
            entry_id='test.ambiguous.b',
            metric_name='ambiguous_metric_b',
            platforms=(PLATFORM_IOSXE,),
            raw_path='test/ambiguous/sensor',
            normalized_path='test/ambiguous/sensor',
            value_type='int',
            unit='count',
            entity_kind='unknown',
            metric_kind='counter',
            notes=['synthetic ambiguous entry B'],
        ),
    )


_CATALOG: Tuple[Dict[str, Any], ...] = _fixture_catalog()


def get_catalog_entries() -> Tuple[Dict[str, Any], ...]:
    return _CATALOG


def _path_has_secret_segment(path: str) -> bool:
    for part in path.replace('\\', '/').split('/'):
        seg = part.split('[')[0].strip()
        if seg and is_secret_field_name(seg):
            return True
    return False


def _platforms_of(entry: Dict[str, Any]) -> Tuple[str, ...]:
    plats = entry.get('platforms') or ()
    return tuple(str(p) for p in plats)


def _is_generic(entry: Dict[str, Any]) -> bool:
    plats = _platforms_of(entry)
    return not plats or plats == ('*',) or plats == (UNKNOWN,)


def lookup_metric(
    path: Any,
    *,
    platform: str = '',
    normalized_path: str = '',
    catalog: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Deterministic exact-path catalog lookup.

    Precedence: platform-specific exact raw_path matches; if none, exact
    normalized_path matches against entry.normalized_path; then explicit
    generic entries. Multiple survivors → ambiguous (never silent pick).
    """
    raw = _s(path)
    norm = _s(normalized_path) or raw
    plat = _s(platform).lower() or UNKNOWN

    if not raw and not norm:
        return empty_lookup_result(
            status=STATUS_INVALID,
            notes=['malformed path: empty'],
        )
    check_path = raw or norm
    if _path_has_secret_segment(check_path):
        return empty_lookup_result(
            status=STATUS_INVALID,
            warnings=['path rejected: secret-like segment'],
            notes=['invalid: secret-like path segment redacted'],
        )

    entries = list(catalog) if catalog is not None else list(get_catalog_entries())
    raw_matches = [e for e in entries if _s(e.get('raw_path')) == raw]
    # Also allow match when observation only has normalized path equal to entry raw/normalized
    if not raw_matches and norm:
        raw_matches = [
            e for e in entries
            if _s(e.get('raw_path')) == norm or _s(e.get('normalized_path')) == norm
        ]

    if not raw_matches:
        return empty_lookup_result(
            status=STATUS_UNKNOWN,
            notes=['path not in fixture catalog'],
        )

    specific = [e for e in raw_matches if plat in _platforms_of(e) and not _is_generic(e)]
    generic = [e for e in raw_matches if _is_generic(e)]

    if len(specific) == 1:
        return empty_lookup_result(
            status=STATUS_KNOWN,
            entry=dict(specific[0]),
            matches=[specific[0]['entry_id']],
            notes=['platform-specific exact match'],
        )
    if len(specific) > 1:
        return empty_lookup_result(
            status=STATUS_AMBIGUOUS,
            matches=[e['entry_id'] for e in specific],
            notes=['ambiguous: multiple platform-specific exact matches'],
        )
    if len(generic) == 1 and not specific:
        return empty_lookup_result(
            status=STATUS_KNOWN,
            entry=dict(generic[0]),
            matches=[generic[0]['entry_id']],
            notes=['explicit generic exact match'],
        )
    if len(generic) > 1:
        return empty_lookup_result(
            status=STATUS_AMBIGUOUS,
            matches=[e['entry_id'] for e in generic],
            notes=['ambiguous: multiple generic exact matches'],
        )
    # Path exists in catalog but only for other platforms
    return empty_lookup_result(
        status=STATUS_UNKNOWN,
        matches=[e['entry_id'] for e in raw_matches],
        notes=['path known for other platform(s) only'],
    )


def apply_catalog_to_observation(obs: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich a normalized observation with catalog metadata (in place + return).

    Never overwrites source unit/type silently — conflicts become warnings.
    Does not change quarantine/duplicate/timestamp rules.
    """
    obs = obs if isinstance(obs, dict) else {}
    path = obs.get('metric_path_raw') or obs.get('metric_path') or ''
    result = lookup_metric(
        path,
        platform=str(obs.get('platform') or ''),
        normalized_path=str(obs.get('metric_path') or ''),
    )
    obs['catalog_status'] = result['status']
    obs['catalog_entry_id'] = (
        (result.get('entry') or {}).get('entry_id') if result.get('entry') else None
    )
    obs['catalog_matches'] = list(result.get('matches') or [])
    obs.setdefault('warnings', [])
    obs.setdefault('notes', [])
    obs['warnings'] = list(obs['warnings']) + list(result.get('warnings') or [])
    obs['notes'] = list(obs['notes']) + list(result.get('notes') or [])

    entry = result.get('entry')
    if result['status'] != STATUS_KNOWN or not entry:
        if result['status'] == STATUS_UNKNOWN:
            obs['metric_kind'] = obs.get('metric_kind') or UNKNOWN
            obs['entity_kind'] = obs.get('entity_kind') or UNKNOWN
            obs['monotonic'] = obs.get('monotonic') or UNKNOWN
        elif result['status'] == STATUS_AMBIGUOUS:
            obs['notes'].append('catalog ambiguous — source fields retained')
            obs['metric_kind'] = obs.get('metric_kind') or UNKNOWN
            obs['entity_kind'] = obs.get('entity_kind') or UNKNOWN
            obs['monotonic'] = obs.get('monotonic') or UNKNOWN
        elif result['status'] == STATUS_INVALID:
            obs['notes'].append('catalog invalid path')
        return obs

    # Known entry enrichment
    obs['metric_kind'] = entry.get('metric_kind') or UNKNOWN
    obs['entity_kind'] = entry.get('entity_kind') or UNKNOWN
    obs['monotonic'] = entry.get('monotonic') or UNKNOWN
    if (obs.get('metric_name') in (None, '', UNKNOWN)) and entry.get('metric_name'):
        obs['metric_name'] = entry['metric_name']
        obs['notes'].append('metric_name filled from catalog')
    cat_unit = entry.get('unit') or UNKNOWN
    src_unit = obs.get('unit') or UNKNOWN
    if src_unit == UNKNOWN and cat_unit != UNKNOWN:
        obs['unit'] = cat_unit
        obs['notes'].append('unit filled from catalog')
    elif src_unit != UNKNOWN and cat_unit != UNKNOWN and src_unit != cat_unit:
        obs['warnings'].append(
            f'unit conflict: source={src_unit} catalog={cat_unit}; keeping source'
        )
    cat_vt = entry.get('value_type') or UNKNOWN
    src_vt = obs.get('value_type') or UNKNOWN
    if src_vt == UNKNOWN and cat_vt != UNKNOWN:
        obs['value_type'] = cat_vt
        obs['notes'].append('value_type filled from catalog')
    elif src_vt != UNKNOWN and cat_vt != UNKNOWN and src_vt != cat_vt:
        obs['warnings'].append(
            f'value_type conflict: source={src_vt} catalog={cat_vt}; keeping source'
        )
    cat_norm = entry.get('normalized_path') or UNKNOWN
    if cat_norm != UNKNOWN and (obs.get('metric_path') in (None, '', UNKNOWN)):
        obs['metric_path'] = cat_norm
    elif (
        cat_norm != UNKNOWN
        and obs.get('metric_path')
        and obs.get('metric_path') != cat_norm
        and obs.get('metric_path') == obs.get('metric_path_raw')
    ):
        # Keep raw; record catalog normalized form in notes only (do not erase raw)
        obs['notes'].append(f'catalog normalized_path={cat_norm}')
    if entry.get('entity_required') and (obs.get('entity_path') in (None, '', UNKNOWN)):
        obs['warnings'].append('catalog expects interface/entity path; source missing')
    return obs
