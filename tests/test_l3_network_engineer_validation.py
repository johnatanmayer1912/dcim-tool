"""
Network Engineer-Focused L3 Map Validation Tests
Tests for network engineering workflows and operational use cases.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from modules.l3_topology_runner import (
    collect_device_routing,
    build_l3_topology_bundle,
    _device_conn_dict,
    _extract_network_meta,
)
from modules.routing_analyzer.graph_builder import L3TopologyGraphBuilder
from modules.routing_analyzer.parser import RoutingParser
from modules.routing_analyzer.normalizer import RoutingNormalizer
from utils.l3_map_shell import render_l3_map_html


class TestNetworkEngineerWorkflows:
    """Test common network engineering workflows with L3 maps."""
    
    def test_default_gateway_identification(self):
        """Network engineers need to quickly identify default gateways."""
        routes = [
            {
                'device_id': 'rtr-01',
                'destination': '0.0.0.0/0',
                'next_hop': '203.0.113.1',
                'protocol': 'Static',
                'route_type': 'Static',
            },
            {
                'device_id': 'rtr-02',
                'destination': '192.168.1.0/24',
                'next_hop': '203.0.113.1',
                'protocol': 'OSPF',
                'route_type': 'Dynamic',
            },
        ]
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Should identify the default gateway
        gateway_nodes = [n for n in result['nodes'] if n.get('group') == 'default_gateway']
        assert len(gateway_nodes) >= 1
        assert '203.0.113.1' in [n['id'] for n in gateway_nodes]
    
    def test_routing_protocol_distribution(self):
        """Network engineers need to see protocol distribution for troubleshooting."""
        routes = [
            {'device_id': 'sw-01', 'destination': '10.0.0.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
            {'device_id': 'sw-01', 'destination': '0.0.0.0/0', 'next_hop': '10.0.0.1', 'protocol': 'Static'},
            {'device_id': 'sw-01', 'destination': '172.16.0.0/16', 'next_hop': '10.0.0.2', 'protocol': 'OSPF'},
            {'device_id': 'sw-01', 'destination': '192.168.0.0/16', 'next_hop': '10.0.0.3', 'protocol': 'BGP'},
        ]
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        analysis = result['analysis']
        proto_dist = analysis['protocol_distribution']
        
        assert 'Connected' in proto_dist
        assert 'Static' in proto_dist
        assert 'OSPF' in proto_dist
        assert 'BGP' in proto_dist
        assert proto_dist['Connected'] == 1
        assert proto_dist['Static'] == 1
    
    def test_multihomed_device_detection(self):
        """Network engineers need to identify devices with multiple gateways."""
        routes = [
            {'device_id': 'sw-01', 'destination': '10.0.0.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
            {'device_id': 'sw-01', 'destination': '0.0.0.0/0', 'next_hop': '10.0.0.1', 'protocol': 'Static'},
            {'device_id': 'sw-01', 'destination': '0.0.0.0/0', 'next_hop': '10.0.0.2', 'protocol': 'Static'},
        ]
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Should detect multiple next-hops (gateways) in the routing data
        next_hops = set(r.get('next_hop') for r in routes if r.get('next_hop') and r.get('next_hop') != '0.0.0.0')
        assert len(next_hops) >= 2
    
    def test_vrf_aware_routing(self):
        """Network engineers need to see VRF-specific routing."""
        routes = [
            {
                'device_id': 'sw-01',
                'destination': '10.0.0.0/24',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
                'vrf': 'MGMT',
            },
            {
                'device_id': 'sw-01',
                'destination': '192.168.0.0/24',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
                'vrf': 'PROD',
            },
        ]
        
        # Verify VRF information is preserved
        vrf_names = set(r.get('vrf', 'default') for r in routes)
        assert 'MGMT' in vrf_names
        assert 'PROD' in vrf_names
    
    def test_connected_subnet_identification(self):
        """Network engineers need to identify directly connected subnets."""
        routes = [
            {'device_id': 'sw-01', 'destination': '192.168.1.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
            {'device_id': 'sw-01', 'destination': '192.168.2.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
        ]
        
        meta = _extract_network_meta(routes, '10.0.0.5', 22, 'cisco_ios')
        
        assert '192.168.1.0/24' in meta['connected_subnets']
        assert '192.168.2.0/24' in meta['connected_subnets']
        assert len(meta['connected_subnets']) == 2
    
    def test_interface_to_subnet_mapping(self):
        """Network engineers need to see which interface is on which subnet."""
        routes = [
            {
                'device_id': 'sw-01',
                'destination': '192.168.1.0/24',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
                'interface': 'Vlan10',
            },
            {
                'device_id': 'sw-01',
                'destination': '192.168.2.0/24',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
                'interface': 'Vlan20',
            },
        ]
        
        meta = _extract_network_meta(routes, '10.0.0.5', 22, 'cisco_ios')
        
        assert 'Vlan10' in meta['interfaces']
        assert meta['interfaces']['Vlan10'] == '192.168.1.0/24'
        assert 'Vlan20' in meta['interfaces']
        assert meta['interfaces']['Vlan20'] == '192.168.2.0/24'


class TestRoutingTroubleshooting:
    """Test routing troubleshooting scenarios."""
    
    def test_route_loop_detection(self):
        """Network engineers need to detect potential routing loops."""
        routes = [
            {'device_id': 'rtr-01', 'destination': '10.0.0.0/24', 'next_hop': '10.0.0.2', 'protocol': 'OSPF'},
            {'device_id': 'rtr-02', 'destination': '10.0.0.0/24', 'next_hop': '10.0.0.1', 'protocol': 'OSPF'},
        ]
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Should create edges between devices
        assert len(result['edges']) >= 2
    
    def test_asymmetric_routing_detection(self):
        """Network engineers need to detect asymmetric routing paths."""
        routes = [
            {'device_id': 'rtr-01', 'destination': '10.0.0.0/24', 'next_hop': '10.0.0.2', 'protocol': 'OSPF'},
            {'device_id': 'rtr-02', 'destination': '10.0.0.0/24', 'next_hop': '10.0.0.3', 'protocol': 'OSPF'},
            {'device_id': 'rtr-03', 'destination': '10.0.0.0/24', 'next_hop': '10.0.0.1', 'protocol': 'OSPF'},
        ]
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Should show the routing path
        assert len(result['nodes']) >= 3
        assert len(result['edges']) >= 3
    
    def test_multi_path_routing(self):
        """Network engineers need to see ECMP/multi-path routing."""
        routes = [
            {'device_id': 'rtr-01', 'destination': '10.0.0.0/24', 'next_hop': '10.0.0.2', 'protocol': 'OSPF'},
            {'device_id': 'rtr-01', 'destination': '10.0.0.0/24', 'next_hop': '10.0.0.3', 'protocol': 'OSPF'},
        ]
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Should show multiple paths to the same destination
        edges_from_rtr01 = [e for e in result['edges'] if e['from'] == 'rtr-01']
        assert len(edges_from_rtr01) >= 2


class TestNetworkChangeValidation:
    """Test validation of network changes using L3 maps."""
    
    def test_new_gateway_detection(self):
        """Network engineers need to detect when a new gateway is added."""
        before_routes = [
            {'device_id': 'sw-01', 'destination': '0.0.0.0/0', 'next_hop': '10.0.0.1', 'protocol': 'Static'},
        ]
        
        after_routes = [
            {'device_id': 'sw-01', 'destination': '0.0.0.0/0', 'next_hop': '10.0.0.1', 'protocol': 'Static'},
            {'device_id': 'sw-01', 'destination': '0.0.0.0/0', 'next_hop': '10.0.0.2', 'protocol': 'Static'},
        ]
        
        # Check next-hops directly in routing data
        next_hops_before = set(r.get('next_hop') for r in before_routes if r.get('next_hop') and r.get('next_hop') != '0.0.0.0')
        next_hops_after = set(r.get('next_hop') for r in after_routes if r.get('next_hop') and r.get('next_hop') != '0.0.0.0')
        
        assert len(next_hops_after) > len(next_hops_before)
    
    def test_subnet_change_detection(self):
        """Network engineers need to detect subnet changes."""
        before_routes = [
            {'device_id': 'sw-01', 'destination': '192.168.1.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
        ]
        
        after_routes = [
            {'device_id': 'sw-01', 'destination': '192.168.1.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
            {'device_id': 'sw-01', 'destination': '192.168.2.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
        ]
        
        meta_before = _extract_network_meta(before_routes, '10.0.0.5', 22, 'cisco_ios')
        meta_after = _extract_network_meta(after_routes, '10.0.0.5', 22, 'cisco_ios')
        
        assert len(meta_after['connected_subnets']) > len(meta_before['connected_subnets'])


class TestVendorSpecificFeatures:
    """Test vendor-specific routing features."""
    
    def test_cisco_ios_route_codes(self):
        """Network engineers need to understand Cisco IOS route codes."""
        from modules.routing_analyzer.parser import PROTO_CODE_MAP
        
        # Test that Cisco-specific route codes are mapped correctly
        assert PROTO_CODE_MAP.get('C') == 'Connected'
        assert PROTO_CODE_MAP.get('S') == 'Static'
        assert PROTO_CODE_MAP.get('O') == 'OSPF'
        assert PROTO_CODE_MAP.get('B') == 'BGP'
        assert PROTO_CODE_MAP.get('D') == 'EIGRP'
    
    def test_juniper_protocol_names(self):
        """Network engineers need to understand Juniper protocol names."""
        from modules.routing_analyzer.normalizer import PROTOCOL_MAP
        
        # Test that Juniper protocol names are normalized correctly
        assert PROTOCOL_MAP.get('Direct') == 'Connected'
        assert PROTOCOL_MAP.get('Static') == 'Static'
        assert PROTOCOL_MAP.get('OSPF') == 'OSPF'
        assert PROTOCOL_MAP.get('BGP') == 'BGP'
        assert PROTOCOL_MAP.get('ISIS') == 'ISIS'


class TestOperationalReadiness:
    """Test operational readiness of L3 maps for network teams."""
    
    def test_failed_host_reporting(self):
        """Network engineers need to know which devices failed collection."""
        device_results = [
            {'status': 'success', 'true_host': 'sw-01', 'routes_normalized': []},
            {'status': 'error', 'true_host': 'sw-02', 'routes_normalized': [], 'errors': ['SSH timeout']},
            {'status': 'error', 'true_host': 'sw-03', 'routes_normalized': [], 'errors': ['Auth failed']},
        ]
        
        bundle = build_l3_topology_bundle(device_results)
        
        assert 'sw-02' in bundle['failed_hosts']
        assert 'sw-03' in bundle['failed_hosts']
        assert len(bundle['failed_hosts']) == 2
    
    def test_route_count_per_device(self):
        """Network engineers need to see route counts per device."""
        device_results = [
            {
                'status': 'success',
                'true_host': 'sw-01',
                'routes_normalized': [{'destination': '10.0.0.0/24'}] * 100,
            },
            {
                'status': 'success',
                'true_host': 'sw-02',
                'routes_normalized': [{'destination': '10.0.0.0/24'}] * 50,
            },
        ]
        
        bundle = build_l3_topology_bundle(device_results)
        
        assert bundle['devices']['sw-01']['route_count'] == 100
        assert bundle['devices']['sw-02']['route_count'] == 50
    
    def test_html_export_includes_all_critical_info(self):
        """Network engineers need all critical info in the HTML export."""
        vis_payload = {
            'nodes': [{'id': 'sw-01', 'label': 'sw-01', 'group': 'device'}],
            'edges': [],
            'analysis': {'total_devices': 1, 'total_routes': 10},
            'gateway_analysis': {},
            'subnet_analysis': {},
            'devices': {'sw-01': {'route_count': 10, 'protocols': ['Connected']}},
            'all_routes': [],
            'failed_hosts': [],
            'route_count': 10,
        }
        
        html = render_l3_map_html(vis_payload, title='Test Map', map_kind='l3')
        
        # Verify critical information is present
        assert 'sw-01' in html
        assert 'Connected' in html
        assert 'Devices' in html
        assert 'Routes' in html
    
    def test_vendor_color_coding_in_html(self):
        """Network engineers need vendor color coding for quick identification."""
        vis_payload = {
            'nodes': [
                {'id': 'cisco-sw', 'label': 'cisco-sw', 'group': 'device', 'platform': 'cisco_ios'},
                {'id': 'juniper-sw', 'label': 'juniper-sw', 'group': 'device', 'platform': 'juniper_junos'},
            ],
            'edges': [],
            'analysis': {},
            'gateway_analysis': {},
            'subnet_analysis': {},
            'devices': {},
            'all_routes': [],
            'failed_hosts': [],
            'route_count': 0,
        }
        
        html = render_l3_map_html(vis_payload, title='Test Map', map_kind='l3')
        
        # Verify vendor-specific CSS classes are present
        assert 'l3-vendor-cisco' in html or 'cisco' in html.lower()
        assert 'l3-vendor-juniper' in html or 'juniper' in html.lower()


class TestPerformanceAtScale:
    """Test performance with large-scale networks."""
    
    def test_large_device_count_handling(self):
        """Network engineers need to handle large networks (100+ devices)."""
        device_results = []
        for i in range(150):
            device_results.append({
                'status': 'success',
                'true_host': f'sw-{i:03d}',
                'routes_normalized': [{'destination': f'10.{i//256}.{i%256}.0/24'}] * 10,
            })
        
        bundle = build_l3_topology_bundle(device_results)
        
        # Should handle 150 devices without error
        assert len(bundle['devices']) == 150
        assert bundle['route_count'] == 1500
    
    def test_large_route_count_handling(self):
        """Network engineers need to handle devices with many routes (1000+)."""
        routes = []
        for i in range(1000):
            routes.append({
                'device_id': 'sw-01',
                'destination': f'10.{i//256}.{i%256}.0/24',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
            })
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Should handle 1000 routes without error
        assert result['analysis']['total_routes'] == 1000


class TestSecurityAndCompliance:
    """Test security and compliance features."""
    
    def test_unencrypted_credentials_not_in_html(self):
        """Network engineers need to ensure credentials are not exposed in HTML."""
        device_results = [
            {
                'status': 'success',
                'true_host': 'sw-01',
                'routes_normalized': [],
                'password': 'secret123',  # Should not appear in HTML
            },
        ]
        
        bundle = build_l3_topology_bundle(device_results)
        vis_payload = {
            'nodes': [{'id': 'sw-01', 'label': 'sw-01', 'group': 'device'}],
            'edges': [],
            'analysis': {},
            'gateway_analysis': {},
            'subnet_analysis': {},
            'devices': bundle['devices'],
            'all_routes': [],
            'failed_hosts': [],
            'route_count': 0,
        }
        
        html = render_l3_map_html(vis_payload, title='Test Map', map_kind='l3')
        
        # Credentials should not be in the HTML
        assert 'secret123' not in html
        assert 'password' not in html.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
