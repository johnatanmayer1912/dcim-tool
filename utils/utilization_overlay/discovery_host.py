"""Discovery Command Center host for the utilization overlay.

Viewer only. Reuses bind_overlay_to_standard_l2 / paint. Does not collect,
does not mint edges, does not thaw telemetry, does not clear release_gate.
EVPN / overlay / incomplete observations stay non-cables.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Union

from utils.utilization_overlay.join import (
    OverlayBindResult,
    bind_overlay_to_standard_l2,
    is_paint_eligible_l2_edge,
    topology_fingerprint,
)

DISCOVERY_HOST = 'discovery'
DISCOVERY_NOTE = (
    'Discovery is a viewer. EVPN, overlay, and incomplete observations are not cables '
    'and are never painted as utilization. Paint is not topology. Release gate is unchanged.'
)


def discovery_embed_payload(bound: OverlayBindResult) -> Dict[str, Any]:
    """Standard embed payload plus Discovery host flags. Does not mutate topology."""
    payload = bound.as_embed_payload()
    payload['host'] = DISCOVERY_HOST
    payload['live_controls'] = False
    payload['discovery_note'] = DISCOVERY_NOTE
    extra = ' ' + DISCOVERY_NOTE
    banner = payload.get('banner') or ''
    if DISCOVERY_NOTE not in banner:
        payload['banner'] = (banner + extra).strip()
    # Fail closed: never bind paint to non-cable vis ids.
    bindings = dict(payload.get('bindings') or {})
    payload['bindings'] = bindings
    return payload


def bind_overlay_to_discovery(
    nodes: Optional[Sequence[Dict[str, Any]]],
    edges: Optional[Sequence[Dict[str, Any]]],
    overlay_source: Optional[Union[str, Dict[str, Any]]],
) -> OverlayBindResult:
    """Bind overlay JSON onto existing Discovery vis/graph edges.

    Join is lookup-only onto paint-eligible L2 cable keys. Overlay/EVPN/
    not_physical edges are excluded from the join set (same is_paint_eligible_l2_edge).
    """
    edge_list = list(edges or [])
    fp_before = topology_fingerprint(edge_list)
    bound = bind_overlay_to_standard_l2(nodes, edge_list, overlay_source)
    dropped = []
    for e in edge_list:
        if not isinstance(e, dict):
            continue
        if is_paint_eligible_l2_edge(e):
            continue
        vid = str(e.get('id') or '')
        if vid and vid in bound.bindings:
            dropped.append(vid)
            del bound.bindings[vid]
    if dropped:
        bound.painted_count = len(bound.bindings)
    if topology_fingerprint(edge_list) != fp_before:
        bound.ok = False
        bound.available = False
        bound.error = 'discovery overlay bind mutated topology — refusing to paint'
        bound.bindings = {}
        bound.doc = None
        bound.painted_count = 0
    return bound
