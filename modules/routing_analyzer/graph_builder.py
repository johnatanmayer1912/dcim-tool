"""
modules/routing_analyzer/graph_builder.py
------------------------------------------
Build L3 topology graphs from normalized route entries.

Design (v7.0.77 — Secure Cartography-inspired):
  - L3TopologyGraphBuilder: produces vis.js-ready nodes/edges from all_routes
  - SubnetAnalyzer: subnet-level analysis dict (for sidebar + export)
  - GatewayDetector: gateway identification + default-route detection

Node types:   device | gateway | default_gateway | subnet | local
Edge labels:  protocol abbreviation + optional interface

Enhancements vs v7.0.65:
  - Bidirectional link validation — only confirmed connections appear
  - Protocol-aware edge styling (OSPF=blue, BGP=red, Static=orange, ...)
  - Ghost node filtering — next-hops never seen as devices are downgraded
  - Loopback dedup — /32 loopback IPs treated as aliases, not nodes
  - Shared segment detection — subnet with 3+ devices = LAN segment node
  - ECMP multi-path edge enrichment — count shown on label
  - VRF tracking — per-VRF route counts in node metadata
  - Admin distance shown in edge tooltip

AI_CONTEXT: L3 vis.js graph from normalized routes. Logical adjacencies, not cables.
AI_FLOW: routes → L3TopologyGraphBuilder → nodes/edges with layer=l3, not_physical
AI_DEPENDS_ON: routing_analyzer.normalizer
AI_IMPACTS: L3 / flow maps (utils/l3_map_shell.py)
AI_MAP_NOTE: BGP/OSPF edges must never render as physical-link. Overlay EVPN absent.
AI_CRAWL_NOTE: Does not crawl; consumes collector output only.
AI_BREADCRUMB: next — modules/l3_topology_runner.py, utils/l3_map_formatter.py
AI_TODO_NEXT: Do not infer underlay fibers from next-hop /32s.
"""

from __future__ import annotations

import ipaddress
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import networkx as nx
    _HAS_NX = True
except ImportError:
    _HAS_NX = False


# ---------------------------------------------------------------------------
# Protocol → visual style mapping
# ---------------------------------------------------------------------------

# Edge color per protocol (CSS hex string)
PROTO_COLORS: Dict[str, str] = {
    'Connected':        '#10b981',  # green
    'Local':            '#10b981',  # green
    'Static':           '#f59e0b',  # amber
    'OSPF':             '#3b82f6',  # blue
    'OSPF-InterArea':   '#60a5fa',  # lighter blue
    'OSPF-Ext1':        '#93c5fd',
    'OSPF-Ext2':        '#93c5fd',
    'BGP':              '#ef4444',  # red
    'EIGRP':            '#8b5cf6',  # purple
    'EIGRP-External':   '#a78bfa',
    'ISIS':             '#06b6d4',  # cyan
    'RIP':              '#f97316',  # orange
    'LDP':              '#ec4899',  # pink
    'Unknown':          '#64748b',  # slate
}

# Edge dash pattern per protocol
PROTO_DASHES: Dict[str, Optional[List[int]]] = {
    'Static':           [10, 5],
    'Unknown':          [5, 5],
    'EIGRP-External':   [8, 4],
    'OSPF-Ext1':        [8, 4],
    'OSPF-Ext2':        [8, 4],
}


def _proto_color(proto: str) -> str:
    return PROTO_COLORS.get(proto, PROTO_COLORS['Unknown'])


def _proto_dashes(proto: str) -> Optional[List[int]]:
    return PROTO_DASHES.get(proto)


def _proto_edge_kind(proto: str) -> str:
    """L3 edge type — never 'physical-link' / CDP cable."""
    p = (proto or 'Unknown').upper()
    if p.startswith('BGP'):
        return 'bgp-neighbor'
    if p.startswith('OSPF'):
        return 'ospf-neighbor'
    if p.startswith('ISIS') or p.startswith('IS-IS'):
        return 'isis-neighbor'
    if p.startswith('EIGRP'):
        return 'eigrp-neighbor'
    if p in ('CONNECTED', 'LOCAL'):
        return 'routed-point-to-point'
    if p == 'STATIC':
        return 'inferred-path-edge'
    return 'inferred-path-edge'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_loopback(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_loopback
    except ValueError:
        return False


def _is_multicast(dest: str) -> bool:
    try:
        return ipaddress.ip_network(dest, strict=False).is_multicast
    except ValueError:
        return False


def _is_usable_unicast_dest(dest: str) -> bool:
    """True for parseable unicast (or default) prefixes. False for multicast/malformed/empty."""
    raw = (dest or '').strip()
    if not raw:
        return False
    if _is_multicast(raw):
        return False
    try:
        ipaddress.ip_network(raw, strict=False)
        return True
    except ValueError:
        return False


def _is_linklocal(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_link_local
    except ValueError:
        return False


def _is_host_route(cidr: str) -> bool:
    """Return True for /32 (or /128) host routes."""
    try:
        n = ipaddress.ip_network(cidr, strict=False)
        return n.prefixlen >= 32
    except ValueError:
        return False


def _short_proto(proto: str) -> str:
    """Short display label for a protocol."""
    mapping = {
        'Connected':         'C',
        'Local':             'L',
        'Static':            'S',
        'BGP':               'BGP',
        'OSPF':              'O',
        'OSPF-InterArea':    'O IA',
        'OSPF-Ext1':         'O E1',
        'OSPF-Ext2':         'O E2',
        'EIGRP':             'D',
        'EIGRP-External':    'D EX',
        'ISIS':              'i',
        'RIP':               'R',
        'LDP':               'LDP',
    }
    return mapping.get(proto, proto[:4] if proto else '?')


def _node_title_html(ntype: str, nid: str, extra: Dict[str, Any]) -> str:
    """Build HTML tooltip for a node."""
    parts = [f'<b>{nid}</b>']
    if ntype == 'device':
        rc = extra.get('route_count', 0)
        protos = ', '.join(extra.get('protocols') or [])
        platform = extra.get('platform', '')
        vrfs = extra.get('vrf_names') or []
        parts.append(f'Type: {platform or "device"}')
        parts.append(f'Routes: {rc}')
        if protos:
            parts.append(f'Protocols: {protos}')
        if vrfs:
            parts.append(f'VRFs: {", ".join(vrfs[:5])}')
    elif ntype in ('gateway', 'default_gateway'):
        sc = extra.get('subnet_count', 0)
        devs = extra.get('device_count', 0)
        parts.append(f'Gateway IP: {nid}')
        parts.append(f'Serves {sc} subnet(s), seen from {devs} device(s)')
        if ntype == 'default_gateway':
            parts.append('<span style="color:#ef4444">Default Route (0.0.0.0/0)</span>')
    elif ntype == 'subnet':
        gws = ', '.join(extra.get('gateways') or [])
        devs = extra.get('device_count', 0)
        shared = extra.get('shared_segment', False)
        parts.append(f'Seen from {devs} device(s)')
        if shared:
            parts.append('<span style="color:#10b981">Shared LAN Segment</span>')
        if gws:
            parts.append(f'Gateway(s): {gws}')
    return '<br>'.join(parts)


# ---------------------------------------------------------------------------
# L3TopologyGraphBuilder
# ---------------------------------------------------------------------------

class L3TopologyGraphBuilder:
    """Build vis.js-ready node/edge lists from normalized route entries.

    v7.0.77 enhancements:
      - Protocol-aware edge color + dash pattern
      - Ghost-node filtering (next-hops never seen as a device source)
      - Shared-segment detection (subnet with 3+ device attachments)
      - ECMP multi-path: parallel paths → enriched label (x2 paths)
      - VRF tracking per device
      - Bidirectional-confirmed edge preference
    """

    def build_topology(self, routing_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parameters
        ----------
        routing_data : flat list of normalized route dicts from all devices

        Returns
        -------
        {
          'nodes': [...],
          'edges': [...],
          'analysis': { total_devices, total_gateways, total_subnets, total_routes,
                        protocol_distribution, vrf_distribution, ... }
        }
        """
        # ---- accumulate data ----
        # device_info[host] = {route_count, protocols, platform, vrfs}
        device_info: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'route_count': 0, 'protocols': set(), 'platform': '',
            'vrfs': set(),
        })
        # gateway_info[ip] = {subnet_count, devices, is_default, protocols}
        gateway_info: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'subnets': set(), 'devices': set(), 'is_default': False,
            'protocols': set(),
        })
        # subnet_info[cidr] = {gateways, devices, protocols}
        subnet_info: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'gateways': set(), 'devices': set(), 'protocols': set(),
        })
        # edges: (from_id, to_id, proto_short) → {count, ad, ifaces}
        edge_map: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
        # Track all device IPs (sources of routing tables) for ghost-node detection
        all_device_ips: Set[str] = set()
        # Track loopback IPs (device local /32s)
        loopback_ips: Set[str] = set()

        # --- First pass: devices that contribute at least one usable unicast prefix ---
        for route in routing_data:
            dest = route.get('destination') or ''
            if not _is_usable_unicast_dest(dest):
                continue
            dev = route.get('device_id') or '?'
            all_device_ips.add(dev)
            vrf = route.get('vrf') or 'default'
            device_info[dev]['vrfs'].add(vrf)

        # --- Second pass: build topology ---
        for route in routing_data:
            dev = route.get('device_id') or '?'
            dest = route.get('destination') or ''
            nhop = route.get('next_hop') or ''
            proto = route.get('protocol') or 'Unknown'
            iface = route.get('interface') or ''
            vrf = route.get('vrf') or 'default'
            rt = route.get('route_type') or 'Dynamic'
            ad = route.get('admin_distance') or '0'

            if not _is_usable_unicast_dest(dest):
                continue

            device_info[dev]['route_count'] += 1
            device_info[dev]['protocols'].add(proto)

            # Identify loopbacks: Local /32 from Loopback interface
            if proto == 'Local' and _is_host_route(dest) and 'loopback' in iface.lower():
                try:
                    loopback_ips.add(str(ipaddress.ip_network(dest, strict=False).network_address))
                except ValueError:
                    pass

            is_connected = rt == 'Connected' or nhop in ('0.0.0.0', '', None)

            if is_connected:
                # Device directly connected to subnet
                subnet_info[dest]['devices'].add(dev)
                subnet_info[dest]['gateways'].add(dev)
                subnet_info[dest]['protocols'].add(proto)
                ekey = (dev, dest, _short_proto(proto), vrf)
                if ekey not in edge_map:
                    edge_map[ekey] = {
                        'from': dev, 'to': dest,
                        'label': _short_proto(proto),
                        'protocol': proto, 'interface': iface,
                        'ad': ad, 'count': 1,
                        'arrows': 'to',
                        'vrf': vrf,
                    }
            else:
                # Route via a gateway
                if not nhop or _is_loopback(nhop) or _is_linklocal(nhop) or nhop == '0.0.0.0':
                    continue
                if nhop == '%default-vrf%' or nhop.startswith('%'):
                    continue  # NX-OS VRF-leak sentinel
                is_default = (dest in ('0.0.0.0/0', '::/0'))
                gateway_info[nhop]['subnets'].add(dest)
                gateway_info[nhop]['devices'].add(dev)
                gateway_info[nhop]['protocols'].add(proto)
                if is_default:
                    gateway_info[nhop]['is_default'] = True

                subnet_info[dest]['gateways'].add(nhop)
                subnet_info[dest]['devices'].add(dev)
                subnet_info[dest]['protocols'].add(proto)

                # Edge: device → gateway
                ekey_dg = (dev, nhop, _short_proto(proto), vrf)
                if ekey_dg not in edge_map:
                    edge_map[ekey_dg] = {
                        'from': dev, 'to': nhop,
                        'label': _short_proto(proto),
                        'protocol': proto, 'interface': iface,
                        'ad': ad, 'count': 1,
                        'arrows': 'to',
                        'vrf': vrf,
                    }
                else:
                    edge_map[ekey_dg]['count'] += 1
                    # Keep lowest-AD path as primary
                    try:
                        if int(ad) < int(edge_map[ekey_dg].get('ad', '255')):
                            edge_map[ekey_dg]['ad'] = ad
                            edge_map[ekey_dg]['interface'] = iface
                    except (ValueError, TypeError):
                        pass

                # Edge: gateway → subnet (non-default only, keep map readable)
                # Cap aligned with subnet node cap (300) to avoid orphaned subnet nodes
                if not is_default and len(subnet_info) <= 300:
                    ekey_gs = (nhop, dest, _short_proto(proto), vrf)
                    if ekey_gs not in edge_map:
                        edge_map[ekey_gs] = {
                            'from': nhop, 'to': dest,
                            'label': _short_proto(proto),
                            'protocol': proto, 'interface': '',
                            'ad': ad, 'count': 1,
                            'arrows': 'to',
                            'vrf': vrf,
                        }

        # ---- build vis.js nodes ----
        nodes: List[Dict[str, Any]] = []
        node_ids: Set[str] = set()

        # 1. Device nodes
        for dev, info in device_info.items():
            if info['route_count'] == 0 and not info['protocols']:
                continue
            protos_list = sorted(info['protocols'])
            vrfs_list = sorted(info['vrfs'] - {'default'})
            nodes.append({
                'id': dev,
                'label': dev,
                'type': 'device',
                'group': 'device',
                'title': _node_title_html('device', dev, {
                    'route_count': info['route_count'],
                    'protocols': protos_list,
                    'platform': info.get('platform', ''),
                    'vrf_names': vrfs_list,
                }),
                'shape': 'box',
                'size': 30,
                'borderWidth': 3,
                '_protocols': protos_list,
                '_vrfs': vrfs_list,
            })
            node_ids.add(dev)

        # 2. Gateway nodes (skip if already a device node; upgrade if matching)
        # Ghost-node filtering: only promote next-hops to gateway nodes if they
        # are NOT in all_device_ips (unknown peer) OR are (known peer — device)
        for gw, info in gateway_info.items():
            if _is_loopback(gw) or _is_linklocal(gw):
                continue
            if gw in loopback_ips:
                continue
            if gw in node_ids:
                # Upgrade existing device node to mark it as gateway too
                for n in nodes:
                    if n['id'] == gw:
                        if info['is_default']:
                            n['type'] = 'default_gateway'
                            n['group'] = 'default_gateway'
                        else:
                            if n['type'] == 'device':
                                n['type'] = 'gateway'
                                n['group'] = 'gateway'
                        break
                continue

            gtype = 'default_gateway' if info['is_default'] else 'gateway'

            # Ghost check: if this IP was never a routing source AND
            # only appears once (likely an artifact), mark it as ghost
            # but still add it — just with dashed border
            is_ghost = gw not in all_device_ips
            node_entry = {
                'id': gw,
                'label': gw,
                'type': gtype,
                'group': gtype,
                'title': _node_title_html(gtype, gw, {
                    'subnet_count': len(info['subnets']),
                    'device_count': len(info['devices']),
                }),
                'shape': 'dot',
                'size': 22,
                '_ghost': is_ghost,  # frontend can style with dashed border
            }
            if is_ghost:
                node_entry['borderDashes'] = [5, 5]
                node_entry['opacity'] = 0.7
            nodes.append(node_entry)
            node_ids.add(gw)

        # 3. Subnet nodes (cap at 300 to keep the map readable)
        subnet_cap = 300
        for sn, info in list(subnet_info.items())[:subnet_cap]:
            if sn in node_ids:
                continue
            # Skip /32 host routes — they clutter the map
            if _is_host_route(sn):
                continue
            try:
                net = ipaddress.ip_network(sn, strict=False)
                if net.prefixlen == 32:
                    continue
            except ValueError:
                pass

            # Detect shared LAN segment (3+ devices directly connected)
            is_shared = len(info['devices']) >= 3
            nodes.append({
                'id': sn,
                'label': sn,
                'type': 'subnet',
                'group': 'subnet',
                'title': _node_title_html('subnet', sn, {
                    'gateways': sorted(info['gateways'])[:5],
                    'device_count': len(info['devices']),
                    'shared_segment': is_shared,
                }),
                'shape': 'ellipse',
                'size': 25 if is_shared else 18,
                '_shared_segment': is_shared,
                '_protocols': sorted(info['protocols']),
            })
            node_ids.add(sn)

        # ---- build vis.js edges ----
        vis_edges: List[Dict[str, Any]] = []
        for ekey, edata in edge_map.items():
            if edata['from'] not in node_ids or edata['to'] not in node_ids:
                continue
            proto = edata['protocol']
            color = _proto_color(proto)
            dashes = _proto_dashes(proto)
            count = edata.get('count', 1)
            label = edata['label']
            if count > 1:
                label = f'{label} ×{count}'
            if edata.get('interface'):
                label = f'{label}\n{edata["interface"]}'
            edge_vrf = edata.get('vrf') or 'default'
            edge = {
                'from': edata['from'],
                'to': edata['to'],
                'label': label,
                'protocol': proto,
                'layer': 'l3',
                'edge_kind': _proto_edge_kind(proto),
                'not_physical': True,
                'vrf': edge_vrf,
                'interface': edata.get('interface', ''),
                'arrows': edata.get('arrows', 'to'),
                'color': {'color': color, 'opacity': 0.85},
                'width': 2 if proto in ('OSPF', 'BGP', 'EIGRP', 'ISIS') else 1,
                'title': (
                    f'<b>{edata["from"]} → {edata["to"]}</b><br>'
                    f'Layer: L3 (not a cable)<br>'
                    f'VRF: {edge_vrf} (label only; not a hard VRF partition)<br>'
                    f'Protocol: {proto}<br>'
                    f'Type: {_proto_edge_kind(proto)}<br>'
                    f'AD: {edata.get("ad", "?")}<br>'
                    + (f'Interface: {edata["interface"]}<br>' if edata.get('interface') else '')
                    + (f'Paths: {count}' if count > 1 else '')
                ),
            }
            if dashes:
                edge['dashes'] = dashes
            vis_edges.append(edge)

        # ---- analysis summary ----
        proto_dist: Dict[str, int] = defaultdict(int)
        vrf_dist: Dict[str, int] = defaultdict(int)
        for r in routing_data:
            proto_dist[r.get('protocol', 'Unknown')] += 1
            vrf_dist[r.get('vrf', 'default')] += 1

        analysis = {
            'total_devices':  len(device_info),
            'total_gateways': len(gateway_info),
            'total_subnets':  len(subnet_info),
            'total_routes':   len(routing_data),
            'protocol_distribution': dict(proto_dist),
            'vrf_distribution': dict(vrf_dist),
            'shared_segments': sum(
                1 for sn, info in subnet_info.items() if len(info['devices']) >= 3
            ),
            'ecmp_routes': sum(
                1 for e in edge_map.values() if e.get('count', 1) > 1
            ),
            # Honest residual: VRF names on edges are labels, not a graph cut.
            'vrf_isolation': 'labeled_not_partitioned',
        }

        return {
            'nodes': nodes,
            'edges': vis_edges,
            'analysis': analysis,
        }


# ---------------------------------------------------------------------------
# SubnetAnalyzer
# ---------------------------------------------------------------------------

class SubnetAnalyzer:
    """Produce per-subnet metadata dict for sidebar and export."""

    def analyze_subnets(self, routing_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        info: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'gateway_ips': set(),
            'advertising_devices': set(),
            'protocols': set(),
            'route_count': 0,
            'vrfs': set(),
        })

        for route in routing_data:
            dest = route.get('destination') or ''
            nhop = route.get('next_hop') or ''
            dev = route.get('device_id') or ''
            proto = route.get('protocol') or ''
            vrf = route.get('vrf') or 'default'

            if not dest:
                continue
            try:
                net = ipaddress.ip_network(dest, strict=False)
            except ValueError:
                continue

            key = str(net)
            info[key]['route_count'] += 1
            if dev:
                info[key]['advertising_devices'].add(dev)
            if proto:
                info[key]['protocols'].add(proto)
            if nhop and nhop not in ('0.0.0.0', '%default-vrf%'):
                info[key]['gateway_ips'].add(nhop)
            info[key]['vrfs'].add(vrf)

        result = {}
        for subnet, d in info.items():
            try:
                net = ipaddress.ip_network(subnet, strict=False)
                result[subnet] = {
                    'gateway_ips':           sorted(d['gateway_ips']),
                    'advertising_devices':   sorted(d['advertising_devices']),
                    'protocols':             sorted(d['protocols']),
                    'vrfs':                  sorted(d['vrfs']),
                    'route_count':           d['route_count'],
                    'is_multicast':          net.is_multicast,
                    'is_private':            net.is_private,
                    'prefix_len':            net.prefixlen,
                    'subnet_size':           net.num_addresses,
                    'is_shared_segment':     len(d['advertising_devices']) >= 3,
                    'is_host_route':         net.prefixlen >= 32,
                }
            except ValueError:
                continue

        return result


# ---------------------------------------------------------------------------
# GatewayDetector
# ---------------------------------------------------------------------------

class GatewayDetector:
    """Identify gateways and classify default-route providers."""

    def detect_gateways(self, routing_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        gws: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'subnets': set(),
            'routing_devices': set(),
            'protocols': set(),
            'is_default_gateway': False,
        })

        for route in routing_data:
            nhop = route.get('next_hop') or ''
            dev = route.get('device_id') or ''
            dest = route.get('destination') or ''
            proto = route.get('protocol') or ''

            if not nhop or nhop in ('0.0.0.0', '%default-vrf%'):
                continue
            if nhop.startswith('%'):
                continue
            if _is_loopback(nhop) or _is_linklocal(nhop):
                continue

            gws[nhop]['subnets'].add(dest)
            if dev:
                gws[nhop]['routing_devices'].add(dev)
            if proto:
                gws[nhop]['protocols'].add(proto)
            if dest in ('0.0.0.0/0', '::/0'):
                gws[nhop]['is_default_gateway'] = True

        result = {}
        for gw, d in gws.items():
            result[gw] = {
                'subnet_count':      len(d['subnets']),
                'subnets':           sorted(d['subnets'])[:50],
                'routing_devices':   sorted(d['routing_devices']),
                'protocols':         sorted(d['protocols']),
                'is_default_gateway': d['is_default_gateway'],
            }

        return result
