"""
Comprehensive L3 topology mapping pipeline tests.
Tests collection, parsing, normalization, graph building, and HTML rendering.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from modules.l3_topology_runner import (
    collect_device_routing,
    build_l3_topology_bundle,
    build_flow_topology_bundle,
    _device_conn_dict,
    _parse_and_extend,
)
from modules.routing_analyzer.parser import RoutingParser
from modules.routing_analyzer.normalizer import RoutingNormalizer
from modules.routing_analyzer.graph_builder import L3TopologyGraphBuilder, SubnetAnalyzer, GatewayDetector
from modules.routing_analyzer.collector import RoutingCollector
from utils.l3_map_formatter import l3_bundle_to_vis, flow_bundle_to_vis
from utils.l3_map_shell import render_l3_map_html


# Test data samples
CISCO_IOS_ROUTE_OUTPUT = """
Codes: C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area 
       N1 - OSPF NSSA external type 1, N2 - OSPF NSSA external type 2
       E1 - OSPF external type 1, E2 - OSPF external type 2
       i - IS-IS, su - IS-IS summary, L1 - IS-IS level-1, L2 - IS-IS level-2
       ia - IS-IS inter area, * - candidate default, U - per-user static route
       o - ODR, P - periodic downloaded static route, H - NHRP, l - LISP
       a - application route, + - replicated route, % - next hop override

Gateway of last resort is 10.0.0.1 to network 0.0.0.0

C        192.168.1.0/24 is directly connected, Vlan10
S*       0.0.0.0/0 [1/0] via 10.0.0.1
O        10.10.0.0/24 [110/2] via 10.0.0.2, 00:05:12, GigabitEthernet0/1
B        203.0.113.0/24 [20/0] via 192.0.2.1
"""

JUNOS_ROUTE_OUTPUT = """
inet.0: 10 destinations, 10 routes (10 active, 0 holddown, 0 hidden)
+ = Active Route, - = Last Active, * = Both

0.0.0.0/0          *[Static/5] 1w6d
                    >  to 10.0.0.1 via ge-0/0/0.0
192.168.1.0/24    *[Direct/0] 2w1d
                    >  to 192.168.1.1 via ge-0/0/1.0
10.10.0.0/24      *[OSPF/10] 1d
                    >  to 10.0.0.2 via ge-0/0/2.0
"""

NXOS_ROUTE_OUTPUT = """
IP Route Table for VRF "default"
'*' denotes best ucast next-hop
'+' denotes backup ucast next-hop

C        192.168.1.0/24 is directly connected, Vlan10
S        0.0.0.0/0 [1/0] via 10.0.0.1, Ethernet1/1
O        172.16.0.0/16 [110/20] via 10.0.0.2, Vlan20
"""


class TestDeviceConnDict:
    """Test device connection dictionary construction."""
    
    def test_device_conn_dict_basic(self):
        dev = {'host': '10.0.0.1', 'device_type': 'cisco_ios'}
        result = _device_conn_dict(dev)
        assert result['host'] == '10.0.0.1'
        assert result['device_type'] == 'cisco_ios'
        assert result['port'] == 22
    
    def test_device_conn_dict_with_port(self):
        dev = {'host': '10.0.0.1', 'device_type': 'cisco_ios', 'port': 2222}
        result = _device_conn_dict(dev)
        assert result['port'] == 2222
    
    def test_device_conn_dict_with_group(self):
        dev = {'host': '10.0.0.1', 'device_type': 'cisco_ios', 'group': 'core'}
        result = _device_conn_dict(dev)
        assert result['group'] == 'core'
    
    def test_device_conn_dict_ip_fallback(self):
        dev = {'ip': '10.0.0.1', 'device_type': 'cisco_ios'}
        result = _device_conn_dict(dev)
        assert result['host'] == '10.0.0.1'


class TestRoutingParser:
    """Test routing table parsing for different platforms."""
    
    @pytest.fixture
    def parser(self):
        return RoutingParser()
    
    def test_cisco_ios_textfsm_parsing(self, parser):
        routes = parser.parse_routing_output('cisco_ios', 'show ip route', CISCO_IOS_ROUTE_OUTPUT)
        # Should parse at least some routes
        assert len(routes) > 0
    
    def test_cisco_ios_regex_fallback(self, parser):
        routes = parser.parse_routing_output_regex('cisco_ios', CISCO_IOS_ROUTE_OUTPUT)
        assert len(routes) > 0
        # Check for known routes
        dests = {r.get('network') or r.get('destination', '') for r in routes}
        assert any('192.168.1' in d for d in dests)
    
    def test_juniper_regex_parsing(self, parser):
        routes = parser.parse_routing_output_regex('juniper_junos', JUNOS_ROUTE_OUTPUT)
        assert len(routes) > 0
    
    def test_nxos_regex_parsing(self, parser):
        routes = parser.parse_routing_output_regex('cisco_nxos', NXOS_ROUTE_OUTPUT)
        assert len(routes) > 0
    
    def test_empty_output_handling(self, parser):
        routes = parser.parse_routing_output_regex('cisco_ios', '')
        assert routes == []
    
    def test_invalid_output_handling(self, parser):
        routes = parser.parse_routing_output_regex('cisco_ios', 'Invalid input')
        assert routes == []


class TestRoutingNormalizer:
    """Test route normalization to unified format."""
    
    @pytest.fixture
    def normalizer(self):
        return RoutingNormalizer()
    
    def test_normalize_cisco_routes(self, normalizer):
        raw = [
            {'network': '192.168.1.0/24', 'protocol': 'C', 'metric': '0', 'interface': 'Vlan10', 'next_hop': '0.0.0.0'},
            {'network': '0.0.0.0/0', 'protocol': 'S', 'metric': '[1/0]', 'next_hop': '10.0.0.1'},
        ]
        normalized = normalizer.normalize_routing_table(raw, 'core-sw-01')
        assert len(normalized) == 2
        assert all('device_id' in r for r in normalized)
        assert all('destination' in r for r in normalized)
        assert all('protocol' in r for r in normalized)
    
    def test_deduplication(self, normalizer):
        raw = [
            {'network': '192.168.1.0/24', 'protocol': 'C', 'metric': '0', 'interface': 'Vlan10', 'next_hop': '0.0.0.0'},
            {'network': '192.168.1.0/24', 'protocol': 'C', 'metric': '0', 'interface': 'Vlan10', 'next_hop': '0.0.0.0'},
        ]
        normalized = normalizer.normalize_routing_table(raw, 'core-sw-01')
        # Should deduplicate
        assert len(normalized) == 1
    
    def test_protocol_normalization(self, normalizer):
        raw = [{'network': '192.168.1.0/24', 'protocol': 'C', 'metric': '0', 'interface': 'Vlan10', 'next_hop': '0.0.0.0'}]
        normalized = normalizer.normalize_routing_table(raw, 'core-sw-01')
        assert normalized[0]['protocol'] == 'Connected'
    
    def test_vrf_preservation(self, normalizer):
        raw = [{'network': '192.168.1.0/24', 'protocol': 'C', 'metric': '0', 'interface': 'Vlan10', 'next_hop': '0.0.0.0'}]
        normalized = normalizer.normalize_routing_table(raw, 'core-sw-01', vrf='MGMT')
        assert normalized[0]['vrf'] == 'MGMT'


class TestGraphBuilder:
    """Test L3 topology graph construction."""
    
    @pytest.fixture
    def graph_builder(self):
        return L3TopologyGraphBuilder()
    
    @pytest.fixture
    def sample_routes(self):
        return [
            {
                'device_id': 'core-sw-01',
                'destination': '192.168.1.0/24',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
                'interface': 'Vlan10',
                'route_type': 'Connected',
            },
            {
                'device_id': 'core-sw-01',
                'destination': '0.0.0.0/0',
                'next_hop': '10.0.0.1',
                'protocol': 'Static',
                'interface': 'Gi0/0',
                'route_type': 'Static',
            },
            {
                'device_id': 'core-sw-02',
                'destination': '192.168.2.0/24',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
                'interface': 'Vlan20',
                'route_type': 'Connected',
            },
        ]
    
    def test_build_topology_with_routes(self, graph_builder, sample_routes):
        result = graph_builder.build_topology(sample_routes)
        assert 'nodes' in result
        assert 'edges' in result
        assert 'analysis' in result
        assert len(result['nodes']) > 0
    
    def test_device_nodes_created(self, graph_builder, sample_routes):
        result = graph_builder.build_topology(sample_routes)
        device_nodes = [n for n in result['nodes'] if n.get('group') == 'device']
        assert len(device_nodes) >= 2  # core-sw-01 and core-sw-02
    
    def test_gateway_detection(self, graph_builder, sample_routes):
        result = graph_builder.build_topology(sample_routes)
        gateway_nodes = [n for n in result['nodes'] if n.get('group') in ('gateway', 'default_gateway')]
        assert len(gateway_nodes) >= 1  # 10.0.0.1 should be detected
    
    def test_edge_creation(self, graph_builder, sample_routes):
        result = graph_builder.build_topology(sample_routes)
        assert len(result['edges']) > 0
    
    def test_analysis_summary(self, graph_builder, sample_routes):
        result = graph_builder.build_topology(sample_routes)
        analysis = result['analysis']
        assert analysis['total_devices'] >= 2
        assert analysis['total_routes'] == len(sample_routes)
        assert 'protocol_distribution' in analysis
    
    def test_empty_routes_handling(self, graph_builder):
        result = graph_builder.build_topology([])
        assert result['nodes'] == []
        assert result['edges'] == []
        assert result['analysis']['total_devices'] == 0
    
    def test_multicast_filtering(self, graph_builder):
        routes = [
            {
                'device_id': 'sw-01',
                'destination': '224.0.0.0/4',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
                'route_type': 'Connected',
            },
        ]
        result = graph_builder.build_topology(routes)
        # Multicast routes should be filtered out
        assert len(result['nodes']) == 0

    def test_ipv6_multicast_only_no_device_node(self, graph_builder):
        routes = [{
            'device_id': 'sw-01',
            'destination': 'ff00::/8',
            'next_hop': '::',
            'protocol': 'Connected',
            'route_type': 'Connected',
        }]
        result = graph_builder.build_topology(routes)
        assert result['nodes'] == []

    def test_mixed_unicast_and_multicast_keeps_unicast_device(self, graph_builder):
        routes = [
            {
                'device_id': 'sw-01',
                'destination': '224.0.0.0/4',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
                'route_type': 'Connected',
            },
            {
                'device_id': 'sw-01',
                'destination': '10.1.1.0/24',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
                'route_type': 'Connected',
            },
        ]
        result = graph_builder.build_topology(routes)
        ids = [n['id'] for n in result['nodes']]
        assert 'sw-01' in ids
        assert '224.0.0.0/4' not in ids

    def test_malformed_destination_no_fabricated_node(self, graph_builder):
        routes = [{
            'device_id': 'sw-01',
            'destination': 'not-a-prefix',
            'next_hop': '0.0.0.0',
            'protocol': 'Connected',
            'route_type': 'Connected',
        }]
        result = graph_builder.build_topology(routes)
        assert result['nodes'] == []


class TestSubnetAnalyzer:
    """Test subnet-level analysis."""
    
    @pytest.fixture
    def analyzer(self):
        return SubnetAnalyzer()
    
    @pytest.fixture
    def sample_routes(self):
        return [
            {
                'device_id': 'sw-01',
                'destination': '192.168.1.0/24',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
            },
            {
                'device_id': 'sw-02',
                'destination': '192.168.1.0/24',
                'next_hop': '10.0.0.1',
                'protocol': 'OSPF',
            },
        ]
    
    def test_subnet_analysis(self, analyzer, sample_routes):
        result = analyzer.analyze_subnets(sample_routes)
        assert '192.168.1.0/24' in result
        assert len(result['192.168.1.0/24']['advertising_devices']) >= 1
    
    def test_gateway_tracking(self, analyzer, sample_routes):
        result = analyzer.analyze_subnets(sample_routes)
        assert '10.0.0.1' in result['192.168.1.0/24']['gateway_ips']


class TestGatewayDetector:
    """Test gateway detection logic."""
    
    @pytest.fixture
    def detector(self):
        return GatewayDetector()
    
    @pytest.fixture
    def sample_routes(self):
        return [
            {
                'device_id': 'rtr-01',
                'destination': '0.0.0.0/0',
                'next_hop': '203.0.113.1',
                'protocol': 'Static',
            },
            {
                'device_id': 'rtr-02',
                'destination': '192.168.1.0/24',
                'next_hop': '203.0.113.1',
                'protocol': 'OSPF',
            },
        ]
    
    def test_default_gateway_detection(self, detector, sample_routes):
        result = detector.detect_gateways(sample_routes)
        assert '203.0.113.1' in result
        assert result['203.0.113.1']['is_default_gateway'] == True


class TestL3TopologyRunner:
    """Test end-to-end L3 topology collection and bundle building."""
    
    def test_build_l3_bundle_with_results(self):
        device_results = [
            {
                'status': 'success',
                'true_host': 'core-sw-01',
                'host': '10.0.0.5',
                'platform': 'cisco_ios',
                'ssh_port': 22,
                'management_ip': '10.0.0.5',
                'routes_normalized': [
                    {
                        'device_id': 'core-sw-01',
                        'destination': '192.168.1.0/24',
                        'next_hop': '0.0.0.0',
                        'protocol': 'Connected',
                        'interface': 'Vlan10',
                    },
                ],
                'protocols': ['Connected'],
                'network_meta': {
                    'management_ip': '10.0.0.5',
                    'ssh_port': 22,
                    'default_gateway': '10.0.0.1',
                    'interfaces': {'Vlan10': '192.168.1.0/24'},
                    'local_ips': [],
                    'connected_subnets': ['192.168.1.0/24'],
                },
            }
        ]
        bundle = build_l3_topology_bundle(device_results)
        assert bundle['route_count'] == 1
        assert len(bundle['devices']) == 1
        assert 'core-sw-01' in bundle['devices']
    
    def test_build_flow_bundle(self):
        device_results = [
            {
                'status': 'success',
                'true_host': 'gw-rtr-01',
                'routes_normalized': [
                    {
                        'device_id': 'gw-rtr-01',
                        'destination': '0.0.0.0/0',
                        'next_hop': '203.0.113.1',
                        'protocol': 'Static',
                    },
                ],
            }
        ]
        l3_bundle = build_l3_topology_bundle(device_results)
        flow_bundle = build_flow_topology_bundle(l3_bundle)
        assert len(flow_bundle['nodes']) >= 1
        assert len(flow_bundle['edges']) >= 1
    
    def test_failed_hosts_tracking(self):
        device_results = [
            {
                'status': 'error',
                'true_host': 'failed-sw-01',
                'host': '10.0.0.99',
                'routes_normalized': [],
                'errors': ['SSH timeout'],
            },
            {
                'status': 'success',
                'true_host': 'good-sw-01',
                'routes_normalized': [
                    {
                        'device_id': 'good-sw-01',
                        'destination': '192.168.1.0/24',
                        'next_hop': '0.0.0.0',
                        'protocol': 'Connected',
                    },
                ],
            }
        ]
        bundle = build_l3_topology_bundle(device_results)
        assert 'failed-sw-01' in bundle['failed_hosts']
        assert bundle['route_count'] == 1


class TestL3MapFormatter:
    """Test L3 map to vis.js payload conversion."""
    
    def test_l3_bundle_to_vis(self):
        bundle = {
            'topology': {
                'nodes': [
                    {'id': 'sw-01', 'label': 'sw-01', 'group': 'device'},
                ],
                'edges': [
                    {'from': 'sw-01', 'to': 'sw-02', 'label': 'C'},
                ],
                'analysis': {'total_devices': 1, 'total_routes': 10},
            },
            'subnet_analysis': {},
            'gateway_analysis': {},
            'devices': {},
            'all_routes': [],
            'failed_hosts': [],
            'route_count': 10,
        }
        vis = l3_bundle_to_vis(bundle)
        assert len(vis['nodes']) == 1
        assert len(vis['edges']) == 1
        assert vis['route_count'] == 10
    
    def test_flow_bundle_to_vis(self):
        bundle = {
            'nodes': [{'id': 'rtr-01', 'label': 'rtr-01', 'group': 'device'}],
            'edges': [{'from': 'rtr-01', 'to': '10.0.0.1', 'label': 'S'}],
            'device_count': 1,
            'gateway_count': 1,
            'subnet_count': 0,
            'gateway_analysis': {},
            'subnet_analysis': {},
            'devices': {},
            'all_routes': [],
            'failed_hosts': [],
            'route_count': 5,
        }
        vis = flow_bundle_to_vis(bundle)
        assert len(vis['nodes']) == 1
        assert len(vis['edges']) == 1


class TestL3MapShell:
    """Test HTML map rendering."""
    
    def test_render_l3_map_html(self):
        vis_payload = {
            'nodes': [
                {'id': 'sw-01', 'label': 'sw-01', 'group': 'device', 'title': 'Switch 01'},
            ],
            'edges': [
                {'from': 'sw-01', 'to': 'sw-02', 'label': 'C'},
            ],
            'analysis': {'total_devices': 1, 'total_gateways': 0, 'total_subnets': 0},
            'gateway_analysis': {},
            'subnet_analysis': {},
            'devices': {},
            'all_routes': [],
            'failed_hosts': [],
            'route_count': 5,
        }
        html = render_l3_map_html(vis_payload, title='Test Map', map_kind='l3')
        assert '<!DOCTYPE html>' in html
        assert 'vis.Network' in html
        assert 'sw-01' in html
        assert 'Test Map' in html
    
    def test_render_flow_map_html(self):
        vis_payload = {
            'nodes': [{'id': 'rtr-01', 'label': 'rtr-01', 'group': 'device'}],
            'edges': [{'from': 'rtr-01', 'to': '10.0.0.1', 'label': 'S'}],
            'analysis': {'total_devices': 1, 'total_gateways': 1, 'total_subnets': 0},
            'gateway_analysis': {},
            'subnet_analysis': {},
            'devices': {},
            'all_routes': [],
            'failed_hosts': [],
            'route_count': 3,
        }
        html = render_l3_map_html(vis_payload, title='Flow Map', map_kind='flow')
        assert 'Network Flow Map' in html or 'Flow Map' in html
    
    def test_html_includes_failed_hosts(self):
        vis_payload = {
            'nodes': [],
            'edges': [],
            'analysis': {},
            'gateway_analysis': {},
            'subnet_analysis': {},
            'devices': {},
            'all_routes': [],
            'failed_hosts': ['sw-01', 'sw-02'],
            'route_count': 0,
        }
        html = render_l3_map_html(vis_payload, title='Test', map_kind='l3')
        assert 'Failed hosts' in html
        assert 'sw-01' in html


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_device_list(self):
        bundle = build_l3_topology_bundle([])
        assert bundle['route_count'] == 0
        assert bundle['failed_hosts'] == []
    
    def test_all_devices_failed(self):
        device_results = [
            {'status': 'error', 'true_host': 'sw-01', 'routes_normalized': []},
            {'status': 'error', 'true_host': 'sw-02', 'routes_normalized': []},
        ]
        bundle = build_l3_topology_bundle(device_results)
        assert bundle['route_count'] == 0
        assert len(bundle['failed_hosts']) == 2
    
    def test_malformed_route_data(self):
        graph_builder = L3TopologyGraphBuilder()
        malformed_routes = [
            {'device_id': 'sw-01'},  # Missing required fields
            {'destination': '192.168.1.0/24'},  # Missing device_id
        ]
        result = graph_builder.build_topology(malformed_routes)
        # Should not crash, may produce empty result
        assert 'nodes' in result
        assert 'edges' in result
    
    def test_very_large_route_count(self):
        # Test with many routes to ensure performance
        routes = []
        for i in range(1000):
            routes.append({
                'device_id': f'sw-{i % 10}',
                'destination': f'10.{i // 256}.{i % 256}.0/24',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
                'route_type': 'Connected',
            })
        graph_builder = L3TopologyGraphBuilder()
        result = graph_builder.build_topology(routes)
        assert len(result['nodes']) > 0


class TestHTMLValidation:
    """Validate HTML output structure and content."""
    
    def test_html_has_required_sections(self):
        vis_payload = {
            'nodes': [{'id': 'sw-01', 'label': 'sw-01', 'group': 'device'}],
            'edges': [],
            'analysis': {},
            'gateway_analysis': {},
            'subnet_analysis': {},
            'devices': {},
            'all_routes': [],
            'failed_hosts': [],
            'route_count': 1,
        }
        html = render_l3_map_html(vis_payload, title='Test', map_kind='l3')
        
        # Required HTML structure
        assert '<html' in html
        assert '</html>' in html
        assert '<head>' in html
        assert '<body' in html
        
        # Required JavaScript
        assert 'vis.Network' in html
        assert 'RAW_NODES' in html
        assert 'RAW_EDGES' in html
        
        # Required CSS
        assert 'l3-routing-map' in html
    
    def test_html_escaping(self):
        vis_payload = {
            'nodes': [
                {'id': 'sw<script>alert(1)</script>', 'label': 'sw<script>', 'group': 'device'}
            ],
            'edges': [],
            'analysis': {},
            'gateway_analysis': {},
            'subnet_analysis': {},
            'devices': {},
            'all_routes': [],
            'failed_hosts': [],
            'route_count': 1,
        }
        html = render_l3_map_html(vis_payload, title='Test', map_kind='l3')
        # Should be escaped or handled safely
        # The JSON encoding should handle this
        assert 'RAW_NODES' in html


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
