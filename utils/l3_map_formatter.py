"""
utils/l3_map_formatter.py
---------------------------
Convert L3 topology bundle to Vis.js graph payloads for offline HTML maps.
"""

from __future__ import annotations
from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# Node / edge adapters — already in final vis.js format from graph_builder
# ---------------------------------------------------------------------------

def l3_bundle_to_vis(l3_bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Convert L3 topology bundle to vis.js payload."""
    topo      = l3_bundle.get('topology') or {}
    raw_nodes = topo.get('nodes') or []
    raw_edges = topo.get('edges') or []
    analysis  = topo.get('analysis') or {}

    # Nodes/edges already in vis.js format from graph_builder
    nodes = [n for n in raw_nodes if n.get('id')]
    edges = [
        e for e in raw_edges
        if (e.get('source') or e.get('from')) and (e.get('target') or e.get('to'))
    ]
    # Normalize edge from/to keys (graph_builder uses from/to already)
    norm_edges = []
    for e in edges:
        ne = dict(e)
        if 'source' in ne and 'from' not in ne:
            ne['from'] = ne.pop('source')
        if 'target' in ne and 'to' not in ne:
            ne['to'] = ne.pop('target')
        norm_edges.append(ne)

    return {
        'nodes':            nodes,
        'edges':            norm_edges,
        'analysis':         analysis,
        'subnet_analysis':  l3_bundle.get('subnet_analysis') or {},
        'gateway_analysis': l3_bundle.get('gateway_analysis') or {},
        'devices':          l3_bundle.get('devices') or {},
        'all_routes':       l3_bundle.get('all_routes') or [],
        'failed_hosts':     l3_bundle.get('failed_hosts') or [],
        'route_count':      l3_bundle.get('route_count', 0),
    }


def flow_bundle_to_vis(flow_bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Convert flow topology bundle to vis.js payload."""
    raw_nodes = flow_bundle.get('nodes') or []
    raw_edges = flow_bundle.get('edges') or []

    nodes = [n for n in raw_nodes if n.get('id')]
    norm_edges = []
    for e in raw_edges:
        ne = dict(e)
        if 'source' in ne and 'from' not in ne:
            ne['from'] = ne.pop('source')
        if 'target' in ne and 'to' not in ne:
            ne['to'] = ne.pop('target')
        if ne.get('from') and ne.get('to'):
            norm_edges.append(ne)

    return {
        'nodes':            nodes,
        'edges':            norm_edges,
        'analysis': {
            'total_devices':  flow_bundle.get('device_count', 0),
            'total_gateways': flow_bundle.get('gateway_count', 0),
            'total_subnets':  flow_bundle.get('subnet_count', 0),
        },
        'gateway_analysis': flow_bundle.get('gateway_analysis') or {},
        'subnet_analysis':  flow_bundle.get('subnet_analysis') or {},
        'devices':          flow_bundle.get('devices') or {},
        'all_routes':       flow_bundle.get('all_routes') or [],
        'failed_hosts':     flow_bundle.get('failed_hosts') or [],
        'route_count':      flow_bundle.get('route_count', 0),
    }
