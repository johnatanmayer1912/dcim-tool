"""Canonical nst.utilization_overlay.v1 model — strict Python validator.

Source of truth: docs/21-utilization-overlay/overlay-contract.schema.json
Does not load jsonschema (not a product dependency). Rejects live/replay
mismatches, malformed cable keys, unsupported kinds, and invalid paint states.
"""
from __future__ import annotations

import copy
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union

SCHEMA_ID = 'nst.utilization_overlay.v1'
MODES = frozenset({'replay', 'live'})
EVIDENCE_CLASSES = frozenset({'fixture', 'replay_snapshot', 'live_ssh'})
REPLAY_EVIDENCE = frozenset({'fixture', 'replay_snapshot'})
PAINT_STATES = frozenset({
    'ok', 'warn', 'hot', 'partial', 'stale', 'no_sample', 'no_speed', 'invalid',
})
JOIN_STATUSES = frozenset({'mapped', 'partial'})
UNMAPPED_REASONS = frozenset({
    'no_matching_edge',
    'ambiguous_edges',
    'mgmt_or_l3_svi',
    'bundle_member_not_on_graph',
    'subinterface_no_parent_edge',
    'no_speed',
    'counter_invalid',
    'identity_mismatch',
    'not_paint_eligible_layer',
})
COLLECTOR_KINDS = frozenset({'ssh_cli', 'none'})
VENDORS = frozenset({'cisco_ios', 'cisco_xe', 'cisco_nxos', 'juniper_junos'})
DOC_REQUIRED = (
    'schema', 'mode', 'evidence_class', 'generated_at', 'paints', 'unmapped', 'summary',
)
DOC_ALLOWED = frozenset({
    'schema', 'mode', 'evidence_class', 'topology_job_id', 'topology_relation_keys_ref',
    'generated_at', 'stale_after_seconds', 'degraded', 'collector', 'paints',
    'unmapped', 'summary',
})
PAINT_REQUIRED = ('cable_key', 'paint_state', 'join', 'provenance')
PAINT_ALLOWED = frozenset({
    'cable_key', 'paint_state', 'in_bps', 'out_bps', 'in_pct', 'out_pct', 'pct',
    'if_speed_bps', 'pct_gt_100', 'join', 'provenance', 'freshness',
})
UNMAPPED_REQUIRED = ('device_id', 'if_name_raw', 'reason')
UNMAPPED_ALLOWED = frozenset({
    'device_id', 'if_name_raw', 'if_name_normalized', 'reason', 'command',
})
SUMMARY_REQUIRED = ('l2_edge_count', 'painted_count', 'unmapped_count')
SUMMARY_ALLOWED = frozenset({
    'l2_edge_count', 'painted_count', 'unmapped_count', 'partial_count', 'stale_count',
})
VIS_ID_RE = re.compile(r'^e\d+$', re.I)
CABLE_KIND_ALLOWED = frozenset({'l2'})


class OverlayValidationError(ValueError):
    """Inbound overlay document failed the v1 contract."""


def _err(msg: str) -> OverlayValidationError:
    return OverlayValidationError(msg)


def parse_cable_key(key: Any) -> Tuple[str, str, str, str, str]:
    """Parse topology_relation_key (kind=l2). Never accepts vis e* ids."""
    if not isinstance(key, str) or not key.strip():
        raise _err('malformed cable_key: empty')
    raw = key.strip()
    if VIS_ID_RE.match(raw) or raw.lower().startswith('e') and raw[1:].isdigit():
        raise _err('malformed cable_key: vis display id is not a join key')
    parts = raw.split('|')
    if len(parts) != 5:
        raise _err('malformed cable_key: expected host_a|port_a|host_b|port_b|kind')
    ha, pa, hb, pb, kind = [p.strip() for p in parts]
    kind_l = (kind or 'l2').lower()
    if kind_l not in CABLE_KIND_ALLOWED:
        raise _err(f'unsupported kind: {kind}')
    if not ha or not hb:
        raise _err('malformed cable_key: missing host')
    if VIS_ID_RE.match(ha) or VIS_ID_RE.match(hb):
        raise _err('malformed cable_key: vis display id is not a join key')
    return ha.lower(), pa.lower(), hb.lower(), pb.lower(), kind_l


def _nonneg(name: str, value: Any, allow_null: bool = True) -> None:
    if value is None:
        if allow_null:
            return
        raise _err(f'{name} must not be null')
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise _err(f'{name} must be a number')
    if value < 0:
        raise _err(f'{name} must be >= 0')


def _validate_join(join: Any) -> None:
    if not isinstance(join, dict):
        raise _err('paint.join must be an object')
    extra = set(join) - {'status', 'sides'}
    if extra:
        raise _err(f'paint.join unknown fields: {sorted(extra)}')
    status = join.get('status')
    if status not in JOIN_STATUSES:
        raise _err(f'invalid join status: {status!r}')
    sides = join.get('sides')
    if sides is not None:
        if not isinstance(sides, list):
            raise _err('join.sides must be an array')
        for s in sides:
            if s not in ('a', 'b'):
                raise _err(f'invalid join side: {s!r}')


def _validate_provenance(prov: Any, doc_mode: str, doc_evidence: str) -> None:
    if not isinstance(prov, dict):
        raise _err('paint.provenance must be an object')
    extra = set(prov) - {'mode', 'evidence_class', 'job_id', 'commands'}
    if extra:
        raise _err(f'paint.provenance unknown fields: {sorted(extra)}')
    if prov.get('mode') not in MODES:
        raise _err(f'invalid provenance.mode: {prov.get("mode")!r}')
    if prov.get('evidence_class') not in EVIDENCE_CLASSES:
        raise _err(f'invalid provenance.evidence_class: {prov.get("evidence_class")!r}')
    if prov.get('mode') != doc_mode or prov.get('evidence_class') != doc_evidence:
        raise _err('paint.provenance must match document mode/evidence_class')
    cmds = prov.get('commands')
    if cmds is not None and (
        not isinstance(cmds, list) or any(not isinstance(c, str) for c in cmds)
    ):
        raise _err('provenance.commands must be an array of strings')


def _validate_freshness(fresh: Any) -> None:
    if fresh is None:
        return
    if not isinstance(fresh, dict):
        raise _err('paint.freshness must be an object')
    extra = set(fresh) - {'sampled_at', 'age_seconds', 'stale'}
    if extra:
        raise _err(f'paint.freshness unknown fields: {sorted(extra)}')
    age = fresh.get('age_seconds')
    if age is not None:
        _nonneg('freshness.age_seconds', age)
    if fresh.get('stale') is not None and not isinstance(fresh.get('stale'), bool):
        raise _err('freshness.stale must be boolean')


def _validate_paint(paint: Any, doc_mode: str, doc_evidence: str) -> None:
    if not isinstance(paint, dict):
        raise _err('paint row must be an object')
    extra = set(paint) - PAINT_ALLOWED
    if extra:
        raise _err(f'paint unknown fields: {sorted(extra)}')
    for req in PAINT_REQUIRED:
        if req not in paint:
            raise _err(f'paint missing {req}')
    parse_cable_key(paint.get('cable_key'))
    state = paint.get('paint_state')
    if state not in PAINT_STATES:
        raise _err(f'invalid paint status: {state!r}')
    for num_field in ('in_bps', 'out_bps', 'if_speed_bps'):
        _nonneg(num_field, paint.get(num_field))
    for pct_field in ('in_pct', 'out_pct', 'pct'):
        val = paint.get(pct_field)
        if val is not None and (not isinstance(val, (int, float)) or isinstance(val, bool)):
            raise _err(f'{pct_field} must be a number')
    _validate_join(paint.get('join'))
    _validate_provenance(paint.get('provenance'), doc_mode, doc_evidence)
    _validate_freshness(paint.get('freshness'))


def _validate_unmapped(row: Any) -> None:
    if not isinstance(row, dict):
        raise _err('unmapped row must be an object')
    extra = set(row) - UNMAPPED_ALLOWED
    if extra:
        raise _err(f'unmapped unknown fields: {sorted(extra)}')
    for req in UNMAPPED_REQUIRED:
        if req not in row:
            raise _err(f'unmapped missing {req}')
    if not isinstance(row.get('device_id'), str) or not isinstance(row.get('if_name_raw'), str):
        raise _err('unmapped device_id and if_name_raw must be strings')
    if row.get('reason') not in UNMAPPED_REASONS:
        raise _err(f'invalid unmapped reason: {row.get("reason")!r}')


def _validate_collector(collector: Any) -> None:
    if collector is None:
        return
    if not isinstance(collector, dict):
        raise _err('collector must be an object')
    extra = set(collector) - {'kind', 'vendors', 'delta_seconds_planned'}
    if extra:
        raise _err(f'collector unknown fields: {sorted(extra)}')
    kind = collector.get('kind')
    if kind not in COLLECTOR_KINDS:
        raise _err(f'unsupported collector.kind: {kind!r}')
    vendors = collector.get('vendors')
    if vendors is not None:
        if not isinstance(vendors, list):
            raise _err('collector.vendors must be an array')
        for v in vendors:
            if v not in VENDORS:
                raise _err(f'unsupported collector vendor: {v!r}')


def _validate_summary(summary: Any) -> None:
    if not isinstance(summary, dict):
        raise _err('summary must be an object')
    extra = set(summary) - SUMMARY_ALLOWED
    if extra:
        raise _err(f'summary unknown fields: {sorted(extra)}')
    for req in SUMMARY_REQUIRED:
        if req not in summary:
            raise _err(f'summary missing {req}')
        val = summary[req]
        if not isinstance(val, int) or isinstance(val, bool) or val < 0:
            raise _err(f'summary.{req} must be a non-negative integer')
    for opt in ('partial_count', 'stale_count'):
        if opt in summary:
            val = summary[opt]
            if not isinstance(val, int) or isinstance(val, bool) or val < 0:
                raise _err(f'summary.{opt} must be a non-negative integer')


def validate_overlay_document(data: Any) -> Dict[str, Any]:
    """Return a deep copy of a contract-valid overlay document, or raise."""
    if not isinstance(data, dict):
        raise _err('overlay document must be an object')
    extra = set(data) - DOC_ALLOWED
    if extra:
        raise _err(f'document unknown fields: {sorted(extra)}')
    for req in DOC_REQUIRED:
        if req not in data:
            raise _err(f'document missing {req}')
    if data.get('schema') != SCHEMA_ID:
        raise _err(f'unsupported schema: {data.get("schema")!r}')
    mode = data.get('mode')
    evidence = data.get('evidence_class')
    if mode not in MODES:
        raise _err(f'invalid mode: {mode!r}')
    if evidence not in EVIDENCE_CLASSES:
        raise _err(f'invalid evidence_class: {evidence!r}')
    if mode == 'live' and evidence != 'live_ssh':
        raise _err('invalid mode/evidence: live requires evidence_class=live_ssh')
    if mode == 'replay' and evidence not in REPLAY_EVIDENCE:
        raise _err('invalid mode/evidence: replay forbids live_ssh')
    if not isinstance(data.get('generated_at'), str) or not data.get('generated_at').strip():
        raise _err('generated_at must be a non-empty string')
    stale = data.get('stale_after_seconds')
    if stale is not None:
        if not isinstance(stale, int) or isinstance(stale, bool) or stale < 1:
            raise _err('stale_after_seconds must be an integer >= 1 or null')
    if 'degraded' in data and not isinstance(data.get('degraded'), bool):
        raise _err('degraded must be boolean')
    _validate_collector(data.get('collector'))
    if mode == 'live':
        kind = ((data.get('collector') or {}).get('kind'))
        if kind != 'ssh_cli':
            raise _err('live overlay requires collector.kind=ssh_cli')
        if data.get('stale_after_seconds') is None:
            raise _err('live overlay requires stale_after_seconds')
    paints = data.get('paints')
    if not isinstance(paints, list):
        raise _err('paints must be an array')
    for p in paints:
        _validate_paint(p, mode, evidence)
    unmapped = data.get('unmapped')
    if not isinstance(unmapped, list):
        raise _err('unmapped must be an array')
    for u in unmapped:
        _validate_unmapped(u)
    _validate_summary(data.get('summary'))
    return copy.deepcopy(data)


def load_replay_overlay(
    source: Union[str, Dict[str, Any]],
    *,
    require_replay: bool = True,
) -> Dict[str, Any]:
    """Load and validate a replay overlay from a dict or filesystem path."""
    if isinstance(source, str):
        path = os.path.abspath(source)
        if not os.path.isfile(path):
            raise _err(f'replay fixture not found: {path}')
        try:
            with open(path, encoding='utf-8') as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise _err(f'replay fixture is not valid JSON: {exc}') from exc
    elif isinstance(source, dict):
        data = source
    else:
        raise _err('overlay source must be a dict or file path')
    doc = validate_overlay_document(data)
    if require_replay:
        if doc['mode'] != 'replay':
            raise _err('this Standard L2 path accepts replay only; live SSH is not implemented')
        if doc['evidence_class'] not in REPLAY_EVIDENCE:
            raise _err('replay overlay requires evidence_class fixture or replay_snapshot')
        collector = doc.get('collector') or {}
        if collector.get('kind') not in (None, 'none'):
            raise _err('replay collector.kind must be none')
    return doc


def load_overlay_document(source: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Load replay or live overlay. Live requires evidence_class=live_ssh and ssh_cli."""
    doc = load_replay_overlay(source, require_replay=False)
    if doc['mode'] == 'live':
        if doc['evidence_class'] != 'live_ssh':
            raise _err('live overlay requires evidence_class=live_ssh')
        if (doc.get('collector') or {}).get('kind') != 'ssh_cli':
            raise _err('live overlay requires collector.kind=ssh_cli')
    return doc


def resolve_replay_overlay_source(
    html_file: Optional[str] = None,
    explicit: Optional[Union[str, Dict[str, Any]]] = None,
) -> Optional[Union[str, Dict[str, Any]]]:
    """Explicit path/dict, else NST_UTILIZATION_OVERLAY, else sibling JSON.

    Missing files return None (map stays usable; overlay unavailable).
    """
    if explicit is not None:
        return explicit
    env = os.environ.get('NST_UTILIZATION_OVERLAY', '').strip()
    if env:
        return env
    if html_file:
        sibling = os.path.join(os.path.dirname(os.path.abspath(html_file)), 'utilization_overlay.json')
        if os.path.isfile(sibling):
            return sibling
    return None
