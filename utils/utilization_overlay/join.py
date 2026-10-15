"""Lookup-only join onto existing Standard L2 cable keys.

Never creates, deletes, or reclassifies topology. Never uses vis e* ids as
join identifiers. Identity mismatch fails closed (no paint).
Replay and live share this path; only provenance/freshness differ.
"""
from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from utils.cisco_iface import normalize_cisco_iface
from utils.juniper_iface import (
    is_junos_interface,
    is_junos_irb_or_l3_svi,
    split_junos_unit,
)
from utils.utilization_overlay.model import (
    OverlayValidationError,
    load_overlay_document,
    load_replay_overlay,
    parse_cable_key,
)
from utils.utilization_overlay.paint import LIVE_LABEL, REPLAY_LABEL, ui_paint_view

_MGMT_L3_RE = re.compile(
    r'^(?:mgmt\d*|management(?:\d+)?|lo\d+|loopback\d+|vlan\d+)$',
    re.I,
)
_CISCO_SUBIF_RE = re.compile(
    r'^(?:Ethernet|Eth|GigabitEthernet|Gig|Gi|FastEthernet|Fas|Fa|'
    r'TenGigabitEthernet|TenGigE|Ten|Te|TwentyFiveGigE|Twe|'
    r'FortyGigabitEthernet|For|Fo|HundredGigE|Hun|Hu)\S*\.\d+$',
    re.I,
)
_BUNDLE_IF_RE = re.compile(r'^(?:Po|Port-channel|ae)\d+', re.I)
_PHYSICAL_MEMBER_RE = re.compile(
    r'^(?:Ethernet|Eth|Gi|Te|Fa|Hu|Fo|Twe|ge-|xe-|et-|fe-)',
    re.I,
)


def _edge_dict(edge: Dict[str, Any]) -> Dict[str, Any]:
    ed = edge.get('edge_data') if isinstance(edge.get('edge_data'), dict) else {}
    merged = dict(ed)
    for k in (
        'from', 'to', 'f_port', 't_port', 'local_port', 'remote_port',
        'type', 'layer', 'not_physical', 'trust_tier', 'confidence',
        'one_sided', 'protocol', 'edge_eligible', 'id', 'link_type',
    ):
        if k in edge and edge[k] is not None:
            merged.setdefault(k, edge[k])
    merged['from'] = edge.get('from', merged.get('from', ''))
    merged['to'] = edge.get('to', merged.get('to', ''))
    merged['f_port'] = edge.get('f_port', merged.get('f_port') or merged.get('local_port') or '')
    merged['t_port'] = edge.get('t_port', merged.get('t_port') or merged.get('remote_port') or '')
    merged['id'] = edge.get('id', merged.get('id'))
    return merged


def normalize_if_name(raw: Any) -> str:
    s = str(raw or '').strip().rstrip('*')
    if not s:
        return ''
    cisco = normalize_cisco_iface(s)
    return cisco if cisco else s


def topology_fingerprint(edges: Optional[Sequence[Dict[str, Any]]]) -> Tuple[Tuple[Any, ...], ...]:
    """Durable topology identity — not vis stroke, not overlay paint."""
    rows: List[Tuple[Any, ...]] = []
    for e in edges or []:
        if not isinstance(e, dict):
            continue
        ed = e.get('edge_data') if isinstance(e.get('edge_data'), dict) else {}
        rows.append((
            e.get('from'),
            e.get('to'),
            e.get('f_port') or ed.get('f_port'),
            e.get('t_port') or ed.get('t_port'),
            e.get('id'),
            e.get('trust_tier') or ed.get('trust_tier'),
            e.get('type') or ed.get('type'),
            bool(e.get('not_physical') if 'not_physical' in e else ed.get('not_physical')),
            e.get('layer') or ed.get('layer'),
            e.get('confidence') or ed.get('confidence'),
            bool(e.get('one_sided') if 'one_sided' in e else ed.get('one_sided')),
            e.get('protocol') or ed.get('protocol'),
        ))
    return tuple(rows)


def is_paint_eligible_l2_edge(edge: Dict[str, Any]) -> bool:
    d = _edge_dict(edge)
    if d.get('edge_eligible') is False:
        return False
    if d.get('not_physical'):
        return False
    layer = str(d.get('layer') or '').lower()
    if layer in ('overlay', 'l3', 'evpn'):
        return False
    proto = str(d.get('protocol') or '').lower()
    if proto in ('evpn', 'ospf', 'bgp', 'isis'):
        return False
    etype = str(d.get('type') or '').lower()
    if 'evpn' in etype or etype == 'overlay':
        return False
    if etype in ('stp-blocked', 'stp_blocked') or 'stp-blocked' in etype:
        return False
    link_type = str(d.get('link_type') or '').lower()
    if link_type in ('stp-blocked', 'stp_blocked'):
        return False
    if proto == 'stp':
        return False
    if not d.get('from') or not d.get('to'):
        return False
    if not d.get('f_port') and not d.get('t_port'):
        return False
    return True


def canonical_l2_key(host_a: str, port_a: str, host_b: str, port_b: str) -> str:
    ha = str(host_a or '').strip().lower()
    hb = str(host_b or '').strip().lower()
    pa = normalize_if_name(port_a).lower()
    pb = normalize_if_name(port_b).lower()
    left = (ha, pa)
    right = (hb, pb)
    if left > right:
        left, right = right, left
    return '|'.join([left[0], left[1], right[0], right[1], 'l2'])


def l2_cable_key(edge: Dict[str, Any]) -> str:
    """Authoritative undirected L2 key (normalized ports). Not a vis id."""
    d = _edge_dict(edge)
    return canonical_l2_key(d.get('from') or '', d.get('f_port') or '',
                            d.get('to') or '', d.get('t_port') or '')


def canonicalize_cable_key(key: str) -> str:
    ha, pa, hb, pb, _kind = parse_cable_key(key)
    return canonical_l2_key(ha, pa, hb, pb)


def is_mgmt_or_l3_svi(name: str) -> bool:
    n = str(name or '').strip().rstrip('*')
    if not n:
        return False
    if is_junos_irb_or_l3_svi(n):
        return True
    if n.lower().startswith('irb'):
        return True
    return bool(_MGMT_L3_RE.match(n))


def is_cisco_subinterface(name: str) -> bool:
    n = str(name or '').strip()
    if not n or is_junos_interface(n):
        return False
    return bool(_CISCO_SUBIF_RE.match(n))


def is_bundle_if(name: str) -> bool:
    return bool(_BUNDLE_IF_RE.match(str(name or '').strip()))


@dataclass
class OverlayBindResult:
    ok: bool
    available: bool
    error: Optional[str]
    mode: Optional[str] = None
    evidence_class: Optional[str] = None
    doc: Optional[Dict[str, Any]] = None
    bindings: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    l2_edge_count: int = 0
    painted_count: int = 0
    edge_count_before: int = 0
    edge_count_after: int = 0
    fingerprint_before: Tuple[Tuple[Any, ...], ...] = ()
    fingerprint_after: Tuple[Tuple[Any, ...], ...] = ()

    def as_embed_payload(self) -> Dict[str, Any]:
        """JSON-safe payload for Standard L2 HTML. No topology mutation fields."""
        return {
            'ok': self.ok,
            'available': self.available,
            'error': self.error,
            'mode': self.mode,
            'evidence_class': self.evidence_class,
            'doc': self.doc,
            'bindings': self.bindings,
            'l2_edge_count': self.l2_edge_count,
            'painted_count': self.painted_count,
            'banner': (
                'Utilization paints existing L2 links only. It is not topology. '
                'Gray dashed = no sample — not down. Overlay never creates cables.'
            ),
            'replay_label': (
                LIVE_LABEL
                if (self.mode == 'live' or (self.doc or {}).get('mode') == 'live')
                else REPLAY_LABEL
            ),
            'live_label': LIVE_LABEL,
            'unmapped_title': 'Unmapped interfaces (not drawn)',
            'degraded': bool((self.doc or {}).get('degraded')),
        }


def _fail_bind(
    error: str,
    edges: Sequence[Dict[str, Any]],
    fp_before: Tuple[Tuple[Any, ...], ...],
) -> OverlayBindResult:
    fp_after = topology_fingerprint(edges)
    return OverlayBindResult(
        ok=False,
        available=False,
        error=error,
        edge_count_before=len(edges or []),
        edge_count_after=len(edges or []),
        fingerprint_before=fp_before,
        fingerprint_after=fp_after,
        l2_edge_count=sum(1 for e in (edges or []) if isinstance(e, dict) and is_paint_eligible_l2_edge(e)),
    )


def _node_id_set(nodes: Optional[Sequence[Dict[str, Any]]]) -> Tuple[set, set]:
    ids = set()
    for n in nodes or []:
        if not isinstance(n, dict):
            continue
        nid = str(n.get('id') or '').strip()
        if nid:
            ids.add(nid)
    return ids, {i.lower() for i in ids}


def _index_l2_endpoints(
    edges: Sequence[Dict[str, Any]],
) -> Tuple[Dict[str, List[str]], Dict[Tuple[str, str], List[str]], Dict[str, Dict[str, Any]]]:
    """cable_key -> vis ids; (host,port) -> cable_keys; cable_key -> edge meta."""
    key_to_vis: Dict[str, List[str]] = {}
    endpoint_index: Dict[Tuple[str, str], List[str]] = {}
    key_meta: Dict[str, Dict[str, Any]] = {}
    for e in edges:
        if not isinstance(e, dict) or not is_paint_eligible_l2_edge(e):
            continue
        d = _edge_dict(e)
        key = l2_cable_key(e)
        if not key:
            continue
        vis_id = d.get('id')
        if vis_id is not None:
            key_to_vis.setdefault(key, []).append(str(vis_id))
        ha = str(d.get('from') or '').strip().lower()
        hb = str(d.get('to') or '').strip().lower()
        pa = normalize_if_name(d.get('f_port')).lower()
        pb = normalize_if_name(d.get('t_port')).lower()
        if ha and pa:
            endpoint_index.setdefault((ha, pa), []).append(key)
        if hb and pb:
            endpoint_index.setdefault((hb, pb), []).append(key)
        key_meta[key] = {
            'one_sided': bool(d.get('one_sided')),
            'from': ha,
            'to': hb,
            'f_port': pa,
            't_port': pb,
        }
    return key_to_vis, endpoint_index, key_meta


def bind_overlay_to_standard_l2(
    nodes: Optional[Sequence[Dict[str, Any]]],
    edges: Optional[Sequence[Dict[str, Any]]],
    overlay_source: Optional[Union[str, Dict[str, Any]]],
) -> OverlayBindResult:
    """Bind replay or live overlay documents. Replay tests keep bind_replay_to_standard_l2."""
    edge_list = list(edges or [])
    fp_before = topology_fingerprint(edge_list)
    if overlay_source is None:
        result = _fail_bind('No utilization document loaded', edge_list, fp_before)
        result.error = 'No utilization document loaded'
        return result
    try:
        doc = load_overlay_document(overlay_source)
    except OverlayValidationError as exc:
        return _fail_bind(str(exc), edge_list, fp_before)
    return _bind_validated_doc(nodes, edge_list, doc, fp_before)


def _bind_validated_doc(nodes, edge_list, doc, fp_before) -> OverlayBindResult:
    _ids, ids_l = _node_id_set(nodes)
    key_to_vis, _endpoint_index, _meta = _index_l2_endpoints(edge_list)

    paint_hosts = set()
    for p in doc.get('paints') or []:
        ha, _pa, hb, _pb, _k = parse_cable_key(p['cable_key'])
        paint_hosts.add(ha)
        paint_hosts.add(hb)
    if paint_hosts - ids_l:
        return _fail_bind('device identity mismatch — refusing to paint', edge_list, fp_before)

    canonical_paints = []
    for p in doc.get('paints') or []:
        try:
            ck = canonicalize_cable_key(p['cable_key'])
        except OverlayValidationError as exc:
            return _fail_bind(str(exc), edge_list, fp_before)
        if ck not in key_to_vis:
            return _fail_bind(
                'overlay cable_key not in bound L2 set — refusing to paint',
                edge_list,
                fp_before,
            )
        row = copy.deepcopy(p)
        row['cable_key'] = ck
        canonical_paints.append(row)

    bindings: Dict[str, Dict[str, Any]] = {}
    for p in canonical_paints:
        view = ui_paint_view(p, doc)
        for vid in key_to_vis.get(p['cable_key']) or []:
            bindings[str(vid)] = view

    embed_doc = copy.deepcopy(doc)
    embed_doc['paints'] = canonical_paints
    fp_after = topology_fingerprint(edge_list)
    return OverlayBindResult(
        ok=True,
        available=True,
        error=None,
        mode=doc['mode'],
        evidence_class=doc['evidence_class'],
        doc=embed_doc,
        bindings=bindings,
        l2_edge_count=sum(1 for e in edge_list if isinstance(e, dict) and is_paint_eligible_l2_edge(e)),
        painted_count=len(canonical_paints),
        edge_count_before=len(edge_list),
        edge_count_after=len(edge_list),
        fingerprint_before=fp_before,
        fingerprint_after=fp_after,
    )


def bind_replay_to_standard_l2(
    nodes: Optional[Sequence[Dict[str, Any]]],
    edges: Optional[Sequence[Dict[str, Any]]],
    overlay_source: Optional[Union[str, Dict[str, Any]]],
) -> OverlayBindResult:
    """Bind a validated replay document onto existing L2 edges by cable_key."""
    edge_list = list(edges or [])
    fp_before = topology_fingerprint(edge_list)
    if overlay_source is None:
        result = _fail_bind('No utilization document loaded', edge_list, fp_before)
        result.error = 'No utilization document loaded'
        return result
    try:
        doc = load_replay_overlay(overlay_source, require_replay=True)
    except OverlayValidationError as exc:
        return _fail_bind(str(exc), edge_list, fp_before)
    return _bind_validated_doc(nodes, edge_list, doc, fp_before)


def _unique_keys(keys: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for k in keys:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def _lookup_endpoint(
    device_id: str,
    if_norm: str,
    endpoint_index: Dict[Tuple[str, str], List[str]],
    raw_name: str,
) -> Tuple[Optional[List[str]], Optional[str]]:
    """Return (cable_keys, unmapped_reason). keys=None means unmapped."""
    host = device_id.strip().lower()
    exact = _unique_keys(endpoint_index.get((host, if_norm.lower()), []))
    if len(exact) == 1:
        return exact, None
    if len(exact) >= 2:
        return None, 'ambiguous_edges'

    if is_cisco_subinterface(raw_name) or is_cisco_subinterface(if_norm):
        return None, 'subinterface_no_parent_edge'

    physical, logical = split_junos_unit(if_norm or raw_name)
    if physical and physical.lower() != (if_norm or '').lower() and is_junos_interface(if_norm or raw_name):
        unit_keys = _unique_keys(endpoint_index.get((host, physical.lower()), []))
        if len(unit_keys) == 1:
            return unit_keys, None
        if len(unit_keys) >= 2:
            return None, 'ambiguous_edges'

    return None, 'no_matching_edge'


def _paint_state_from_pct(pct: Optional[float], partial: bool) -> str:
    if pct is None:
        return 'partial' if partial else 'no_sample'
    if partial:
        return 'partial'
    if pct >= 90:
        return 'hot'
    if pct >= 70:
        return 'warn'
    return 'ok'


def join_observations_to_l2(
    observations: Sequence[Dict[str, Any]],
    nodes: Optional[Sequence[Dict[str, Any]]],
    edges: Optional[Sequence[Dict[str, Any]]],
    *,
    generated_at: str = '1970-01-01T00:00:00+00:00',
    topology_job_id: Optional[str] = None,
    mode: str = 'replay',
    evidence_class: str = 'fixture',
    stale_after_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """Map interface observations onto existing L2 keys. Never inserts edges.

    Fail closed on device_id mismatch: no paints, identity_mismatch unmapped rows.
    """
    mode_l = 'live' if str(mode or '').strip().lower() == 'live' else 'replay'
    if mode_l == 'live':
        evidence_l = 'live_ssh'
        collector_kind = 'ssh_cli'
        stale_l = int(stale_after_seconds) if stale_after_seconds else 900
    else:
        evidence_l = evidence_class if evidence_class in ('fixture', 'replay_snapshot') else 'fixture'
        collector_kind = 'none'
        stale_l = None
    edge_list = list(edges or [])
    fp_before = topology_fingerprint(edge_list)
    _ids, ids_l = _node_id_set(nodes)
    key_to_vis, endpoint_index, key_meta = _index_l2_endpoints(edge_list)

    unmapped: List[Dict[str, Any]] = []
    # cable_key -> list of (side_host, side_port, obs)
    hits: Dict[str, List[Tuple[str, str, Dict[str, Any]]]] = {}

    identity_fail = False
    for obs in observations or []:
        if not isinstance(obs, dict):
            continue
        device_id = str(obs.get('device_id') or '').strip()
        raw = str(obs.get('if_name_raw') or obs.get('if_name') or '').strip()
        if not device_id:
            unmapped.append({
                'device_id': '',
                'if_name_raw': raw,
                'if_name_normalized': normalize_if_name(raw) or None,
                'reason': 'identity_mismatch',
                'command': obs.get('command'),
            })
            identity_fail = True
            continue
        if device_id.lower() not in ids_l:
            unmapped.append({
                'device_id': device_id,
                'if_name_raw': raw,
                'if_name_normalized': normalize_if_name(raw) or None,
                'reason': 'identity_mismatch',
                'command': obs.get('command'),
            })
            identity_fail = True
            continue
        if not raw:
            unmapped.append({
                'device_id': device_id,
                'if_name_raw': raw,
                'if_name_normalized': None,
                'reason': 'no_matching_edge',
                'command': obs.get('command'),
            })
            continue
        if is_mgmt_or_l3_svi(raw):
            unmapped.append({
                'device_id': device_id,
                'if_name_raw': raw,
                'if_name_normalized': normalize_if_name(raw) or None,
                'reason': 'mgmt_or_l3_svi',
                'command': obs.get('command'),
            })
            continue
        if obs.get('member_of') or obs.get('is_bundle_member'):
            if not is_bundle_if(raw):
                unmapped.append({
                    'device_id': device_id,
                    'if_name_raw': raw,
                    'if_name_normalized': normalize_if_name(raw) or None,
                    'reason': 'bundle_member_not_on_graph',
                    'command': obs.get('command'),
                })
                continue
        if_norm = normalize_if_name(raw) or raw
        keys, reason = _lookup_endpoint(device_id, if_norm, endpoint_index, raw)
        if keys is None:
            if (
                reason == 'no_matching_edge'
                and _PHYSICAL_MEMBER_RE.match(raw)
                and obs.get('member_of')
            ):
                reason = 'bundle_member_not_on_graph'
            unmapped.append({
                'device_id': device_id,
                'if_name_raw': raw,
                'if_name_normalized': if_norm,
                'reason': reason or 'no_matching_edge',
                'command': obs.get('command'),
            })
            continue
        for ck in keys:
            hits.setdefault(ck, []).append((device_id.lower(), if_norm.lower(), obs))

    if identity_fail:
        assert topology_fingerprint(edge_list) == fp_before
        return {
            'schema': 'nst.utilization_overlay.v1',
            'mode': mode_l,
            'evidence_class': evidence_l,
            'topology_job_id': topology_job_id,
            'generated_at': generated_at,
            'stale_after_seconds': stale_l,
            'degraded': True,
            'collector': {'kind': collector_kind},
            'paints': [],
            'unmapped': unmapped,
            'summary': {
                'l2_edge_count': len(key_meta),
                'painted_count': 0,
                'unmapped_count': len(unmapped),
                'partial_count': 0,
                'stale_count': 0,
            },
            'error': 'device identity mismatch — refusing to paint',
            '_edge_count': len(edge_list),
            '_fingerprint': fp_before,
        }

    paints: List[Dict[str, Any]] = []
    partial_count = 0
    for ck, sides in hits.items():
        meta = key_meta.get(ck) or {}
        unique_endpoints = _unique_keys([f'{h}|{p}' for h, p, _o in sides])
        hosts_ports = {(h, p) for h, p, _o in sides}
        edge_ends = {
            (meta.get('from'), meta.get('f_port')),
            (meta.get('to'), meta.get('t_port')),
        }
        sampled_ends = hosts_ports & edge_ends
        one_sided_edge = bool(meta.get('one_sided'))
        both = len(sampled_ends) >= 2
        if not both and not one_sided_edge and len(edge_ends) >= 2:
            join_status = 'partial'
            paint_state_partial = True
        else:
            join_status = 'mapped'
            paint_state_partial = False
        # pick numbers from first obs; max pct across sides
        pcts = []
        in_bps = out_bps = in_pct = out_pct = if_speed = None
        sampled_at = None
        for _h, _p, obs in sides:
            if obs.get('in_bps') is not None:
                in_bps = obs.get('in_bps')
            if obs.get('out_bps') is not None:
                out_bps = obs.get('out_bps')
            if obs.get('in_pct') is not None:
                in_pct = obs.get('in_pct')
                pcts.append(float(obs['in_pct']))
            if obs.get('out_pct') is not None:
                out_pct = obs.get('out_pct')
                pcts.append(float(obs['out_pct']))
            if obs.get('pct') is not None:
                pcts.append(float(obs['pct']))
            if obs.get('if_speed_bps') is not None:
                if_speed = obs.get('if_speed_bps')
            if obs.get('sampled_at'):
                sampled_at = obs.get('sampled_at')
        pct = max(pcts) if pcts else None
        speed_missing = if_speed in (None, 0)
        rates_present = in_bps is not None or out_bps is not None
        if speed_missing and pct is None and not rates_present:
            unmapped.append({
                'device_id': sides[0][0],
                'if_name_raw': sides[0][1],
                'if_name_normalized': sides[0][1],
                'reason': 'no_speed',
                'command': sides[0][2].get('command'),
            })
            continue
        if speed_missing and pct is None and rates_present:
            state = 'partial' if paint_state_partial else 'no_speed'
        else:
            state = _paint_state_from_pct(pct, paint_state_partial)
        if paint_state_partial:
            partial_count += 1
        join_sides = []
        if (meta.get('from'), meta.get('f_port')) in sampled_ends:
            join_sides.append('a')
        if (meta.get('to'), meta.get('t_port')) in sampled_ends:
            join_sides.append('b')
        if not join_sides:
            join_sides = ['a'] if unique_endpoints else []
        paints.append({
            'cable_key': ck,
            'paint_state': state,
            'in_bps': in_bps,
            'out_bps': out_bps,
            'in_pct': in_pct,
            'out_pct': out_pct,
            'pct': pct,
            'if_speed_bps': if_speed,
            'join': {'status': join_status, 'sides': join_sides},
            'provenance': {
                'mode': mode_l,
                'evidence_class': evidence_l,
                'job_id': topology_job_id,
                'commands': [],
            },
            'freshness': {
                'sampled_at': sampled_at,
                'age_seconds': None,
                'stale': False,
            },
        })

    assert topology_fingerprint(edge_list) == fp_before
    return {
        'schema': 'nst.utilization_overlay.v1',
        'mode': mode_l,
        'evidence_class': evidence_l,
        'topology_job_id': topology_job_id,
        'generated_at': generated_at,
        'stale_after_seconds': stale_l,
        'degraded': False,
        'collector': {'kind': collector_kind},
        'paints': paints,
        'unmapped': unmapped,
        'summary': {
            'l2_edge_count': len(key_meta),
            'painted_count': len(paints),
            'unmapped_count': len(unmapped),
            'partial_count': partial_count,
            'stale_count': 0,
        },
        '_edge_count': len(edge_list),
        '_fingerprint': fp_before,
        '_key_to_vis': key_to_vis,
    }
