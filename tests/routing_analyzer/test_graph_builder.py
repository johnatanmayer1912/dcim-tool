"""
tests/routing_analyzer/test_graph_builder.py
--------------------------------------------
Automated tests for L3 topology graph builder — aligned with v7.0.65 API.

New API contracts:
  build_topology() → {'nodes': [...], 'edges': [...], 'analysis': {total_devices,
                       total_gateways, total_subnets, total_routes, protocol_distribution}}
  SubnetAnalyzer.analyze_subnets() → {subnet_cidr: {gateway_ips, advertising_devices,
                                       protocols, route_count, is_multicast, is_private,
                                       prefix_len, subnet_size}}
  GatewayDetector.detect_gateways() → {gw_ip: {subnet_count, subnets, routing_devices,
                                        protocols, is_default_gateway}}
"""

import pytest
from modules.routing_analyzer.graph_builder import (
    L3TopologyGraphBuilder,
    SubnetAnalyzer,
    GatewayDetector,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def graph_builder():
    return L3TopologyGraphBuilder()


@pytest.fixture
def subnet_analyzer():
    return SubnetAnalyzer()


@pytest.fixture
def gateway_detector():
    return GatewayDetector()


@pytest.fixture
def sample_routing_data():
    """Minimal normalized route list for testing."""
    return [
        {
            'destination': '192.168.1.0/24',
            'next_hop': '0.0.0.0',
            'protocol': 'Connected',
            'route_type': 'Connected',
            'device_id': 'router01',
            'interface': 'GigabitEthernet1/0/1',
        },
        {
            'destination': '10.0.0.0/8',
            'next_hop': '10.0.0.2',
            'protocol': 'Static',
            'route_type': 'Static',
            'device_id': 'router01',
            'interface': 'GigabitEthernet1/0/2',
        },
        {
            'destination': '172.16.0.0/16',
            'next_hop': '10.0.0.1',
            'protocol': 'OSPF',
            'route_type': 'Dynamic',
            'device_id': 'router02',
            'interface': 'GigabitEthernet1/0/1',
        },
    ]


# ---------------------------------------------------------------------------
# TestL3TopologyGraphBuilder
# ---------------------------------------------------------------------------

class TestL3TopologyGraphBuilder:

    def test_graph_builder_initialization(self, graph_builder):
        assert graph_builder is not None

    def test_build_topology_returns_expected_keys(self, graph_builder, sample_routing_data):
        result = graph_builder.build_topology(sample_routing_data)
        assert 'nodes' in result
        assert 'edges' in result
        assert 'analysis' in result

    def test_build_topology_creates_device_nodes(self, graph_builder, sample_routing_data):
        result = graph_builder.build_topology(sample_routing_data)
        node_ids = [n['id'] for n in result['nodes']]
        assert 'router01' in node_ids
        assert 'router02' in node_ids

    def test_build_topology_creates_gateway_nodes(self, graph_builder, sample_routing_data):
        result = graph_builder.build_topology(sample_routing_data)
        node_ids = [n['id'] for n in result['nodes']]
        # 10.0.0.1 and 10.0.0.2 are next-hops → become gateway nodes
        assert '10.0.0.1' in node_ids or '10.0.0.2' in node_ids

    def test_build_topology_creates_edges(self, graph_builder, sample_routing_data):
        result = graph_builder.build_topology(sample_routing_data)
        assert len(result['edges']) > 0
        for edge in result['edges']:
            assert 'from' in edge
            assert 'to' in edge
            assert edge.get('layer') == 'l3'
            assert edge.get('not_physical') is True
            assert edge.get('edge_kind')
            assert edge['edge_kind'] != 'physical-link'

    def test_bgp_edge_is_not_a_cable(self, graph_builder):
        routes = [{
            'destination': '0.0.0.0/0',
            'next_hop': '192.0.2.1',
            'protocol': 'BGP',
            'route_type': 'Dynamic',
            'device_id': 'rr1',
            'interface': 'Loopback0',
        }]
        result = graph_builder.build_topology(routes)
        bgp_edges = [e for e in result['edges'] if e.get('protocol') == 'BGP']
        assert bgp_edges
        assert all(e['edge_kind'] == 'bgp-neighbor' for e in bgp_edges)
        assert all('not a cable' in (e.get('title') or '').lower() for e in bgp_edges)

    def test_build_topology_analysis_device_count(self, graph_builder, sample_routing_data):
        result = graph_builder.build_topology(sample_routing_data)
        assert result['analysis']['total_devices'] == 2

    def test_build_topology_analysis_gateway_count(self, graph_builder, sample_routing_data):
        result = graph_builder.build_topology(sample_routing_data)
        # 10.0.0.1 and 10.0.0.2 are gateways
        assert result['analysis']['total_gateways'] >= 1

    def test_build_topology_analysis_subnet_count(self, graph_builder, sample_routing_data):
        result = graph_builder.build_topology(sample_routing_data)
        # 192.168.1.0/24 (connected), 10.0.0.0/8, 172.16.0.0/16 → subnet nodes
        assert result['analysis']['total_subnets'] >= 1

    def test_build_topology_analysis_route_count(self, graph_builder, sample_routing_data):
        result = graph_builder.build_topology(sample_routing_data)
        assert result['analysis']['total_routes'] == 3

    def test_build_topology_protocol_distribution(self, graph_builder, sample_routing_data):
        result = graph_builder.build_topology(sample_routing_data)
        dist = result['analysis']['protocol_distribution']
        assert 'Connected' in dist
        assert 'Static' in dist
        assert 'OSPF' in dist

    def test_build_topology_empty_data(self, graph_builder):
        result = graph_builder.build_topology([])
        assert result['nodes'] == []
        assert result['edges'] == []
        assert result['analysis']['total_devices'] == 0
        assert result['analysis']['total_routes'] == 0

    def test_build_topology_single_device_no_duplicate_node(self, graph_builder):
        data = [
            {'destination': '192.168.1.0/24', 'next_hop': '0.0.0.0',
             'protocol': 'Connected', 'route_type': 'Connected', 'device_id': 'router01'},
            {'destination': '10.0.0.0/8', 'next_hop': '10.0.0.2',
             'protocol': 'Static', 'route_type': 'Static', 'device_id': 'router01'},
        ]
        result = graph_builder.build_topology(data)
        device_nodes = [n for n in result['nodes'] if n['id'] == 'router01']
        assert len(device_nodes) == 1

    def test_build_topology_no_gateway_for_zero_next_hop(self, graph_builder):
        data = [
            {'destination': '192.168.1.0/24', 'next_hop': '0.0.0.0',
             'protocol': 'Connected', 'route_type': 'Connected', 'device_id': 'router01'},
        ]
        result = graph_builder.build_topology(data)
        node_ids = [n['id'] for n in result['nodes']]
        assert '0.0.0.0' not in node_ids

    def test_build_topology_loopback_next_hop_excluded(self, graph_builder):
        data = [
            {'destination': '10.0.0.0/8', 'next_hop': '127.0.0.1',
             'protocol': 'Static', 'route_type': 'Static', 'device_id': 'router01'},
        ]
        result = graph_builder.build_topology(data)
        node_ids = [n['id'] for n in result['nodes']]
        assert '127.0.0.1' not in node_ids

    def test_build_topology_multicast_destination_excluded(self, graph_builder):
        data = [
            {'destination': '224.0.0.0/4', 'next_hop': '10.0.0.1',
             'protocol': 'Static', 'route_type': 'Static', 'device_id': 'router01'},
        ]
        result = graph_builder.build_topology(data)
        node_ids = [n['id'] for n in result['nodes']]
        assert '224.0.0.0/4' not in node_ids

    def test_build_topology_host_route_no_subnet_node(self, graph_builder):
        data = [
            {'destination': '10.0.0.1/32', 'next_hop': '0.0.0.0',
             'protocol': 'Local', 'route_type': 'Connected', 'device_id': 'router01'},
        ]
        result = graph_builder.build_topology(data)
        subnet_nodes = [n for n in result['nodes']
                        if (n.get('type') == 'subnet' or n.get('group') == 'subnet')]
        assert len(subnet_nodes) == 0

    def test_build_topology_edges_deduplicated(self, graph_builder):
        data = [
            {'destination': '10.1.0.0/24', 'next_hop': '10.0.0.1',
             'protocol': 'OSPF', 'route_type': 'Dynamic', 'device_id': 'devA'},
            {'destination': '10.1.0.0/24', 'next_hop': '10.0.0.1',
             'protocol': 'OSPF', 'route_type': 'Dynamic', 'device_id': 'devA'},
        ]
        result = graph_builder.build_topology(data)
        matching = [e for e in result['edges']
                    if e.get('from') == 'devA' and e.get('to') == '10.0.0.1']
        assert len(matching) == 1


# ---------------------------------------------------------------------------
# TestSubnetAnalyzer
# ---------------------------------------------------------------------------

class TestSubnetAnalyzer:

    def test_analyze_subnets_basic(self, subnet_analyzer, sample_routing_data):
        result = subnet_analyzer.analyze_subnets(sample_routing_data)
        assert '192.168.1.0/24' in result
        assert '172.16.0.0/16' in result

    def test_analyze_subnets_gateway_ips(self, subnet_analyzer, sample_routing_data):
        result = subnet_analyzer.analyze_subnets(sample_routing_data)
        # 172.16.0.0/16 routed via 10.0.0.1
        assert '10.0.0.1' in result['172.16.0.0/16']['gateway_ips']

    def test_analyze_subnets_advertising_devices(self, subnet_analyzer, sample_routing_data):
        result = subnet_analyzer.analyze_subnets(sample_routing_data)
        assert 'router02' in result['172.16.0.0/16']['advertising_devices']

    def test_analyze_subnets_protocols(self, subnet_analyzer, sample_routing_data):
        result = subnet_analyzer.analyze_subnets(sample_routing_data)
        assert 'OSPF' in result['172.16.0.0/16']['protocols']

    def test_analyze_subnets_route_count(self, subnet_analyzer, sample_routing_data):
        result = subnet_analyzer.analyze_subnets(sample_routing_data)
        assert result['192.168.1.0/24']['route_count'] == 1

    def test_analyze_subnets_prefix_len(self, subnet_analyzer):
        data = [{'destination': '10.0.0.0/8', 'next_hop': '10.0.0.1',
                 'device_id': 'r1', 'protocol': 'S'}]
        result = subnet_analyzer.analyze_subnets(data)
        assert result['10.0.0.0/8']['prefix_len'] == 8

    def test_analyze_subnets_subnet_size(self, subnet_analyzer):
        data = [{'destination': '192.168.1.0/24', 'next_hop': '10.0.0.1',
                 'device_id': 'r1', 'protocol': 'C'}]
        result = subnet_analyzer.analyze_subnets(data)
        assert result['192.168.1.0/24']['subnet_size'] == 256

    def test_analyze_subnets_is_private(self, subnet_analyzer):
        data = [{'destination': '10.0.0.0/8', 'next_hop': '10.0.0.1',
                 'device_id': 'r1', 'protocol': 'C'}]
        result = subnet_analyzer.analyze_subnets(data)
        assert result['10.0.0.0/8']['is_private'] is True

    def test_analyze_subnets_is_multicast_flagged(self, subnet_analyzer):
        data = [{'destination': '224.0.0.0/4', 'next_hop': '10.0.0.1',
                 'device_id': 'r1', 'protocol': 'S'}]
        result = subnet_analyzer.analyze_subnets(data)
        assert '224.0.0.0/4' in result
        assert result['224.0.0.0/4']['is_multicast'] is True

    def test_analyze_subnets_empty_data(self, subnet_analyzer):
        assert subnet_analyzer.analyze_subnets([]) == {}

    def test_analyze_subnets_invalid_destination_skipped(self, subnet_analyzer):
        data = [{'destination': 'not_a_subnet', 'device_id': 'r1', 'protocol': 'S'}]
        result = subnet_analyzer.analyze_subnets(data)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# TestGatewayDetector
# ---------------------------------------------------------------------------

class TestGatewayDetector:

    def test_detect_gateways_basic(self, gateway_detector, sample_routing_data):
        result = gateway_detector.detect_gateways(sample_routing_data)
        assert '10.0.0.1' in result or '10.0.0.2' in result

    def test_detect_gateways_subnet_count(self, gateway_detector, sample_routing_data):
        result = gateway_detector.detect_gateways(sample_routing_data)
        # 10.0.0.2 serves 10.0.0.0/8
        if '10.0.0.2' in result:
            assert result['10.0.0.2']['subnet_count'] >= 1

    def test_detect_gateways_routing_devices(self, gateway_detector, sample_routing_data):
        result = gateway_detector.detect_gateways(sample_routing_data)
        # router01 routes via 10.0.0.2
        if '10.0.0.2' in result:
            assert 'router01' in result['10.0.0.2']['routing_devices']

    def test_detect_gateways_protocols(self, gateway_detector, sample_routing_data):
        result = gateway_detector.detect_gateways(sample_routing_data)
        if '10.0.0.1' in result:
            assert len(result['10.0.0.1']['protocols']) >= 1

    def test_detect_gateways_default_gateway(self, gateway_detector):
        data = [
            {'destination': '0.0.0.0/0', 'next_hop': '10.0.0.1',
             'protocol': 'Static', 'device_id': 'r1'},
        ]
        result = gateway_detector.detect_gateways(data)
        assert result['10.0.0.1']['is_default_gateway'] is True

    def test_detect_gateways_non_default_gateway(self, gateway_detector):
        data = [
            {'destination': '10.1.0.0/24', 'next_hop': '10.0.0.1',
             'protocol': 'OSPF', 'device_id': 'r1'},
        ]
        result = gateway_detector.detect_gateways(data)
        assert result['10.0.0.1']['is_default_gateway'] is False

    def test_detect_gateways_empty_data(self, gateway_detector):
        assert gateway_detector.detect_gateways([]) == {}

    def test_detect_gateways_zero_next_hop_excluded(self, gateway_detector):
        data = [{'destination': '192.168.1.0/24', 'next_hop': '0.0.0.0',
                 'protocol': 'Connected', 'device_id': 'r1'}]
        result = gateway_detector.detect_gateways(data)
        assert '0.0.0.0' not in result

    def test_detect_gateways_missing_next_hop(self, gateway_detector):
        data = [{'destination': '192.168.1.0/24', 'protocol': 'Connected', 'device_id': 'r1'}]
        result = gateway_detector.detect_gateways(data)
        assert len(result) == 0

    def test_detect_gateways_loopback_excluded(self, gateway_detector):
        data = [{'destination': '10.0.0.0/8', 'next_hop': '127.0.0.1',
                 'protocol': 'Static', 'device_id': 'r1'}]
        result = gateway_detector.detect_gateways(data)
        assert '127.0.0.1' not in result


# ---------------------------------------------------------------------------
# TestIntegration
# ---------------------------------------------------------------------------

class TestIntegration:
    """Integration between graph builder components."""

    @pytest.fixture
    def complex_routing_data(self):
        return [
            {'destination': '192.168.1.0/24', 'next_hop': '0.0.0.0',
             'protocol': 'Connected', 'route_type': 'Connected',
             'device_id': 'core-router-01', 'interface': 'GigabitEthernet1/0/1'},
            {'destination': '192.168.2.0/24', 'next_hop': '0.0.0.0',
             'protocol': 'Connected', 'route_type': 'Connected',
             'device_id': 'core-router-01', 'interface': 'GigabitEthernet1/0/2'},
            {'destination': '10.0.0.0/8', 'next_hop': '10.0.0.254',
             'protocol': 'Static', 'route_type': 'Static',
             'device_id': 'core-router-01', 'interface': 'GigabitEthernet1/0/3'},
            {'destination': '172.16.0.0/16', 'next_hop': '10.0.0.1',
             'protocol': 'OSPF', 'route_type': 'Dynamic',
             'device_id': 'dist-router-01', 'interface': 'GigabitEthernet1/0/1'},
            {'destination': '0.0.0.0/0', 'next_hop': '10.0.0.254',
             'protocol': 'Static', 'route_type': 'Static',
             'device_id': 'core-router-01', 'interface': 'GigabitEthernet1/0/3'},
        ]

    def test_full_l3_analysis_pipeline(self, complex_routing_data):
        topology = L3TopologyGraphBuilder().build_topology(complex_routing_data)
        subnet_analysis = SubnetAnalyzer().analyze_subnets(complex_routing_data)
        gateway_analysis = GatewayDetector().detect_gateways(complex_routing_data)

        assert topology['analysis']['total_devices'] == 2
        assert len(subnet_analysis) >= 3
        assert len(gateway_analysis) == 2

        default_gateways = [g for g, info in gateway_analysis.items()
                            if info['is_default_gateway']]
        assert len(default_gateways) == 1
        assert default_gateways[0] == '10.0.0.254'

    def test_topology_analysis_consistency(self, complex_routing_data):
        topology = L3TopologyGraphBuilder().build_topology(complex_routing_data)
        gateway_analysis = GatewayDetector().detect_gateways(complex_routing_data)
        assert topology['analysis']['total_gateways'] == len(gateway_analysis)

    def test_all_edges_have_valid_from_to(self, complex_routing_data):
        topology = L3TopologyGraphBuilder().build_topology(complex_routing_data)
        node_ids = {n['id'] for n in topology['nodes']}
        for edge in topology['edges']:
            assert edge['from'] in node_ids, f"Edge 'from' {edge['from']} not a known node"
            assert edge['to'] in node_ids, f"Edge 'to' {edge['to']} not a known node"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
