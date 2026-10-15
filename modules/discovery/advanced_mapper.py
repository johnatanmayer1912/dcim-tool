"""
modules/discovery/advanced_mapper.py
------------------------------------
Advanced L2/L3/Flow map orchestration (Secure Cartography + Netdisco inspired).
Uses SSH routing analysis and CDP/LLDP enrichment — no SNMP walk required.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from modules.routing_analyzer.graph_builder import GatewayDetector, L3TopologyGraphBuilder
from modules.routing_analyzer.normalizer import RoutingNormalizer


class AdvancedMapper:
    """Build enriched topology map models for offline HTML rendering."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._normalizer = RoutingNormalizer()
        self._graph_builder = L3TopologyGraphBuilder()
        self._gateway_detector = GatewayDetector()

    def build_l2_map(self, devices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build enriched L2 topology (Secure Cartography style) from neighbor data.
        Expects devices with neighbors: [{ip, local_port, remote_port, protocol?}]
        
        Enhanced deduplication: Uses hostname as primary key, falls back to IP.
        Prevents duplicate nodes when same device appears with multiple IPs.
        """
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        seen_nodes = set()  # Track by hostname (preferred) or IP
        ip_to_hostname = {}  # Map IPs to hostnames for correlation

        # First pass: build IP to hostname mapping from device list
        for d in devices:
            ip = d.get('ip') or d.get('host') or '?'
            hostname = d.get('hostname') or d.get('true_host') or ip
            if ip != '?' and hostname != ip:
                ip_to_hostname[ip] = hostname

        for d in devices:
            ip = d.get('ip') or d.get('host') or '?'
            hostname = d.get('hostname') or d.get('true_host') or ip
            
            # Use hostname as primary key, IP as fallback
            node_id = hostname if hostname != ip else ip
            
            if node_id not in seen_nodes:
                seen_nodes.add(node_id)
                nodes.append({
                    'id': node_id,
                    'label': hostname,
                    'group': 'switch',
                    'platform': d.get('platform') or d.get('device_type') or '',
                    'management_ip': ip if ip != hostname else '',
                })
            
            for n in d.get('neighbors') or []:
                peer_ip = n.get('ip') or n.get('remote_host') or n.get('to')
                if not peer_ip:
                    continue
                
                # Resolve peer hostname from mapping or use remote_host from neighbor data
                peer_hostname = n.get('remote_host') or ip_to_hostname.get(peer_ip, peer_ip)
                peer_id = peer_hostname if peer_hostname != peer_ip else peer_ip
                
                if peer_id not in seen_nodes:
                    seen_nodes.add(peer_id)
                    nodes.append({
                        'id': peer_id,
                        'label': peer_hostname,
                        'group': 'switch',
                        'management_ip': peer_ip if peer_ip != peer_hostname else '',
                    })
                
                proto = n.get('protocol') or 'CDP/LLDP'
                edges.append({
                    'from': node_id,
                    'to': peer_id,
                    'label': f"{n.get('local_port', '?')} → {n.get('remote_port', '?')}",
                    'protocol': proto,
                })
        
        return {'nodes': nodes, 'edges': edges, 'node_count': len(nodes), 'edge_count': len(edges)}

    def build_l3_map(self, devices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build L3 routing topology from device route lists.
        Each device: {ip, hostname, routes: [{network, protocol, next_hop?, interface?}]}
        """
        all_normalized: List[Dict[str, Any]] = []
        device_meta: Dict[str, Any] = {}

        for d in devices:
            device_id = d.get('hostname') or d.get('true_host') or d.get('ip') or '?'
            raw_routes = d.get('routes') or []
            normalized = self._normalizer.normalize_routing_table(raw_routes, device_id)
            all_normalized.extend(normalized)
            device_meta[device_id] = {
                'route_count': len(normalized),
                'protocols': sorted({r.get('protocol') for r in normalized if r.get('protocol')}),
            }

        topology = self._graph_builder.build_topology(all_normalized)
        vis_nodes = [
            {'id': n['id'], 'label': n.get('label', n['id']), 'type': n.get('type', 'device')}
            for n in topology.get('nodes') or []
        ]
        vis_edges = [
            {
                'from': e.get('source'),
                'to': e.get('target'),
                'label': e.get('protocol') or e.get('type') or '',
                'protocol': e.get('protocol'),
            }
            for e in topology.get('edges') or []
        ]
        return {
            'nodes': vis_nodes,
            'edges': vis_edges,
            'analysis': topology.get('analysis') or {},
            'devices': device_meta,
            'route_count': len(all_normalized),
        }

    def build_flow_map(self, devices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build gateway-centric flow map from routing tables."""
        l3 = self.build_l3_map(devices)
        routes: List[Dict[str, Any]] = []
        for d in devices:
            device_id = d.get('hostname') or d.get('true_host') or d.get('ip') or '?'
            routes.extend(self._normalizer.normalize_routing_table(d.get('routes') or [], device_id))

        gateway_analysis = self._gateway_detector.detect_gateways(routes)
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        node_ids = set()

        for did, info in (l3.get('devices') or {}).items():
            node_ids.add(did)
            nodes.append({'id': did, 'label': did, 'group': 'device'})

        for gw, info in gateway_analysis.items():
            node_ids.add(gw)
            group = 'default_gateway' if info.get('is_default_gateway') else 'gateway'
            nodes.append({'id': gw, 'label': gw, 'group': group})
            for dev in info.get('routing_devices') or []:
                if dev in node_ids:
                    edges.append({
                        'from': dev,
                        'to': gw,
                        'label': 'via',
                        'protocol': ','.join(info.get('protocols') or []),
                    })
            for subnet in info.get('subnets') or []:
                if subnet.startswith('224.') or subnet.startswith('239.'):
                    continue
                if subnet not in node_ids:
                    node_ids.add(subnet)
                    nodes.append({'id': subnet, 'label': subnet, 'group': 'subnet'})
                edges.append({'from': gw, 'to': subnet, 'label': 'serves'})

        return {
            'nodes': nodes,
            'edges': edges,
            'gateway_count': len(gateway_analysis),
            'device_count': len(l3.get('devices') or {}),
            'analysis': l3.get('analysis') or {},
        }

    def build_combined_l2l3_map(
        self,
        l2_devices: List[Dict[str, Any]],
        l3_devices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build combined L2+L3 topology correlating physical (CDP/LLDP) and logical (routing) topology.
        
        Parameters
        ----------
        l2_devices : List of devices with neighbor data from CDP/LLDP
                    [{ip, hostname, neighbors: [{ip, local_port, remote_port, protocol}]}]
        l3_devices : List of devices with routing data
                    [{hostname, routes: [{destination, protocol, next_hop, interface}]}]
        
        Returns
        -------
        {
            'nodes': [...],
            'edges': [...],
            'l2_edges': [...],      # Physical links (CDP/LLDP)
            'l3_edges': [...],      # Logical routing paths
            'correlation': {...},    # Physical-to-logical mapping
            'analysis': {...}
        }
        """
        # Build L2 topology (physical layer)
        l2_model = self.build_l2_map(l2_devices)
        l2_nodes = {n['id']: n for n in l2_model['nodes']}
        l2_edges = l2_model['edges']
        
        # Build L3 topology (logical layer)
        l3_model = self.build_l3_map(l3_devices)
        l3_nodes = {n['id']: n for n in l3_model.get('nodes', [])}
        l3_edges = l3_model.get('edges', [])
        
        # Merge nodes: L2 nodes are primary, enrich with L3 metadata
        merged_nodes: List[Dict[str, Any]] = []
        node_ids = set()
        
        # Start with L2 nodes (physical topology is the base)
        for nid, node in l2_nodes.items():
            merged = dict(node)
            merged['group'] = 'switch'
            merged['layer'] = 'l2'
            # Enrich with L3 data if available
            if nid in l3_nodes:
                l3_meta = l3_nodes[nid]
                merged['protocols'] = l3_meta.get('_protocols', [])
                merged['vrfs'] = l3_meta.get('_vrfs', [])
                merged['layer'] = 'l2+l3'
            merged_nodes.append(merged)
            node_ids.add(nid)
        
        # Add L3-only nodes (gateways, subnets not in L2)
        for nid, node in l3_nodes.items():
            if nid not in node_ids:
                merged = dict(node)
                merged['layer'] = 'l3'
                merged_nodes.append(merged)
                node_ids.add(nid)
        
        # Correlate edges: mark which L3 paths traverse which L2 links
        correlation = {
            'physical_to_logical': {},
            'logical_to_physical': {},
            'gateway_devices': set(),
        }
        
        # Build physical link map for correlation
        physical_links = {}
        for edge in l2_edges:
            from_id = edge['from']
            to_id = edge['to']
            key = tuple(sorted([from_id, to_id]))
            physical_links[key] = edge
            correlation['physical_to_logical'][key] = []
        
        # Correlate L3 routing edges with physical links
        # If device A routes to gateway B via interface X, and A has CDP neighbor B on port X,
        # that's a direct correlation
        for l3_edge in l3_edges:
            from_id = l3_edge.get('from')
            to_id = l3_edge.get('to')
            if not from_id or not to_id:
                continue
            
            # Check if there's a direct physical link
            phys_key = tuple(sorted([from_id, to_id]))
            if phys_key in physical_links:
                correlation['physical_to_logical'][phys_key].append({
                    'protocol': l3_edge.get('protocol'),
                    'label': l3_edge.get('label'),
                })
                correlation['logical_to_physical'][(from_id, to_id)] = phys_key
            
            # Track gateway devices
            if l3_edge.get('to') and l3_nodes.get(l3_edge.get('to'), {}).get('group') in ('gateway', 'default_gateway'):
                correlation['gateway_devices'].add(l3_edge['to'])
        
        # Merge edges with layer annotations
        merged_edges = []
        
        # Add L2 physical edges with correlation metadata
        for edge in l2_edges:
            merged = dict(edge)
            merged['layer'] = 'l2'
            merged['edge_type'] = 'physical'
            phys_key = tuple(sorted([edge['from'], edge['to']]))
            merged['l3_correlations'] = correlation['physical_to_logical'].get(phys_key, [])
            merged_edges.append(merged)
        
        # Add L3 logical edges
        for edge in l3_edges:
            merged = dict(edge)
            merged['layer'] = 'l3'
            merged['edge_type'] = 'logical'
            # Check if this logical edge has a physical counterpart
            phys_key = correlation['logical_to_physical'].get((edge['from'], edge['to']))
            if phys_key:
                merged['physical_link'] = f"{phys_key[0]}--{phys_key[1]}"
            merged_edges.append(merged)
        
        analysis = {
            'total_nodes': len(merged_nodes),
            'total_edges': len(merged_edges),
            'l2_node_count': len(l2_nodes),
            'l3_node_count': len(l3_nodes),
            'l2_edge_count': len(l2_edges),
            'l3_edge_count': len(l3_edges),
            'correlated_edges': sum(1 for e in merged_edges if e.get('physical_link')),
            'gateway_count': len(correlation['gateway_devices']),
            'protocols': sorted(set(
                n.get('protocols', []) for n in merged_nodes if n.get('protocols')
            )),
        }
        
        return {
            'nodes': merged_nodes,
            'edges': merged_edges,
            'l2_edges': l2_edges,
            'l3_edges': l3_edges,
            'correlation': {
                'physical_to_logical': {str(k): v for k, v in correlation['physical_to_logical'].items()},
                'logical_to_physical': {str(k): v for k, v in correlation['logical_to_physical'].items()},
                'gateway_devices': sorted(correlation['gateway_devices']),
            },
            'analysis': analysis,
        }
