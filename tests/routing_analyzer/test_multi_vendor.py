"""
tests/routing_analyzer/test_multi_vendor.py
----------------------------------------
Comprehensive multi-vendor routing analysis tests.
Tests Cisco IOS, Juniper Junos, Cisco NX-OS, and Arista EOS.
"""

import pytest
from modules.routing_analyzer.collector import RoutingCollector
from modules.routing_analyzer.normalizer import RoutingNormalizer
from modules.routing_analyzer.graph_builder import L3TopologyGraphBuilder, SubnetAnalyzer, GatewayDetector


class TestCiscoIOSRouting:
    """Test Cisco IOS-specific routing scenarios"""
    
    @pytest.fixture
    def cisco_collector(self):
        return RoutingCollector('cisco_ios')
    
    @pytest.fixture
    def normalizer(self):
        return RoutingNormalizer()
    
    def test_cisco_connected_routes(self, cisco_collector, normalizer):
        """Test Cisco connected route handling"""
        raw_routes = [
            {'network': '192.168.1.0/24', 'protocol': 'C', 'metric': '0', 'interface': 'Gi1/0/1'},
            {'network': '10.0.0.0/8', 'protocol': 'C', 'metric': '0', 'interface': 'Gi1/0/2'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'cisco-router-01')
        
        assert len(normalized) == 2
        assert all(route['protocol'] == 'Connected' for route in normalized)
        assert all(route['route_type'] == 'Connected' for route in normalized)
    
    def test_cisco_static_routes(self, cisco_collector, normalizer):
        """Test Cisco static route handling"""
        raw_routes = [
            {'network': '0.0.0.0/0', 'protocol': 'S', 'metric': '[1/0]', 'next_hop': '10.0.0.1'},
            {'network': '172.16.0.0/16', 'protocol': 'S', 'metric': '[1/0]', 'next_hop': '10.0.0.2'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'cisco-router-01')
        
        assert len(normalized) == 2
        assert all(route['protocol'] == 'Static' for route in normalized)
        assert all(route['admin_distance'] == 1 for route in normalized)
    
    def test_cisco_ospf_routes(self, cisco_collector, normalizer):
        """Test Cisco OSPF route handling"""
        raw_routes = [
            {'network': '192.168.10.0/24', 'protocol': 'O', 'metric': '[110/2]', 'next_hop': '10.0.0.1'},
            {'network': '192.168.20.0/24', 'protocol': 'O', 'metric': '[110/3]', 'next_hop': '10.0.0.2'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'cisco-router-01')
        
        assert len(normalized) == 2
        assert all(route['protocol'] == 'OSPF' for route in normalized)
        assert all(route['admin_distance'] == 110 for route in normalized)
    
    def test_cisco_bgp_routes(self, cisco_collector, normalizer):
        """Test Cisco BGP route handling"""
        raw_routes = [
            {'network': '203.0.113.0/24', 'protocol': 'B', 'metric': '[20/0]', 'next_hop': '192.0.2.1'},
            {'network': '198.51.100.0/24', 'protocol': 'B', 'metric': '[20/0]', 'next_hop': '192.0.2.2'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'cisco-router-01')
        
        assert len(normalized) == 2
        assert all(route['protocol'] == 'BGP' for route in normalized)
        assert all(route['admin_distance'] == 20 for route in normalized)
    
    def test_cisco_eigrp_routes(self, cisco_collector, normalizer):
        """Test Cisco EIGRP route handling"""
        raw_routes = [
            {'network': '10.10.0.0/16', 'protocol': 'D', 'metric': '[90/2172416]', 'next_hop': '10.0.0.1'},
            {'network': '10.20.0.0/16', 'protocol': 'D', 'metric': '[90/2172416]', 'next_hop': '10.0.0.2'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'cisco-router-01')
        
        assert len(normalized) == 2
        assert all(route['protocol'] == 'EIGRP' for route in normalized)
        assert all(route['admin_distance'] == 90 for route in normalized)
    
    def test_cisco_rip_routes(self, cisco_collector, normalizer):
        """Test Cisco RIP route handling"""
        raw_routes = [
            {'network': '192.168.100.0/24', 'protocol': 'R', 'metric': '[120/4]', 'next_hop': '10.0.0.1'},
            {'network': '192.168.200.0/24', 'protocol': 'R', 'metric': '[120/4]', 'next_hop': '10.0.0.2'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'cisco-router-01')
        
        assert len(normalized) == 2
        assert all(route['protocol'] == 'RIP' for route in normalized)
        assert all(route['admin_distance'] == 120 for route in normalized)
    
    def test_cisco_default_route(self, cisco_collector, normalizer):
        """Test Cisco default route handling"""
        raw_routes = [
            {'network': '0.0.0.0/0', 'protocol': 'S*', 'metric': '[1/0]', 'next_hop': '10.0.0.1'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'cisco-router-01')
        
        assert len(normalized) == 1
        assert normalized[0]['destination'] == '0.0.0.0/0'
        assert normalized[0]['protocol'] == 'Static'
    
    def test_cisco_vrf_aware_routing(self, cisco_collector, normalizer):
        """Test Cisco VRF-aware routing — vrf must be passed explicitly to normalize_routing_table."""
        raw_routes_a = [
            {'network': '192.168.1.0/24', 'protocol': 'C', 'metric': '0'},
        ]
        raw_routes_b = [
            {'network': '10.0.0.0/8', 'protocol': 'C', 'metric': '0'},
        ]
        normalized_a = normalizer.normalize_routing_table(raw_routes_a, 'cisco-router-01', vrf='VRF_A')
        normalized_b = normalizer.normalize_routing_table(raw_routes_b, 'cisco-router-01', vrf='VRF_B')
        combined = normalized_a + normalized_b

        assert len(combined) == 2
        assert combined[0]['vrf'] == 'VRF_A'
        assert combined[1]['vrf'] == 'VRF_B'


class TestJuniperJunosRouting:
    """Test Juniper Junos-specific routing scenarios"""
    
    @pytest.fixture
    def juniper_collector(self):
        return RoutingCollector('juniper_junos')
    
    @pytest.fixture
    def normalizer(self):
        return RoutingNormalizer()
    
    def test_juniper_direct_routes(self, juniper_collector, normalizer):
        """Test Juniper direct route handling"""
        raw_routes = [
            {'network': '192.168.1.0/24', 'protocol': 'Direct', 'metric': '0', 'interface': 'ge-0/0/0'},
            {'network': '10.0.0.0/8', 'protocol': 'Direct', 'metric': '0', 'interface': 'ge-0/0/1'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'juniper-router-01')
        
        assert len(normalized) == 2
        assert all(route['protocol'] == 'Connected' for route in normalized)
    
    def test_juniper_static_routes(self, juniper_collector, normalizer):
        """Test Juniper static route handling"""
        raw_routes = [
            {'network': '0.0.0.0/0', 'protocol': 'Static', 'metric': '5', 'next_hop': '10.0.0.1'},
            {'network': '172.16.0.0/16', 'protocol': 'Static', 'metric': '5', 'next_hop': '10.0.0.2'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'juniper-router-01')
        
        assert len(normalized) == 2
        assert all(route['protocol'] == 'Static' for route in normalized)
    
    def test_juniper_ospf_routes(self, juniper_collector, normalizer):
        """Test Juniper OSPF route handling"""
        raw_routes = [
            {'network': '192.168.10.0/24', 'protocol': 'OSPF', 'metric': '10', 'next_hop': '10.0.0.1'},
            {'network': '192.168.20.0/24', 'protocol': 'OSPF', 'metric': '10', 'next_hop': '10.0.0.2'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'juniper-router-01')
        
        assert len(normalized) == 2
        assert all(route['protocol'] == 'OSPF' for route in normalized)
    
    def test_juniper_bgp_routes(self, juniper_collector, normalizer):
        """Test Juniper BGP route handling"""
        raw_routes = [
            {'network': '203.0.113.0/24', 'protocol': 'BGP', 'metric': '170', 'next_hop': '192.0.2.1'},
            {'network': '198.51.100.0/24', 'protocol': 'BGP', 'metric': '170', 'next_hop': '192.0.2.2'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'juniper-router-01')
        
        assert len(normalized) == 2
        assert all(route['protocol'] == 'BGP' for route in normalized)
    
    def test_juniper_isis_routes(self, juniper_collector, normalizer):
        """Test Juniper IS-IS route handling"""
        raw_routes = [
            {'network': '10.10.0.0/16', 'protocol': 'IS-IS', 'metric': '18', 'next_hop': '10.0.0.1'},
            {'network': '10.20.0.0/16', 'protocol': 'IS-IS', 'metric': '18', 'next_hop': '10.0.0.2'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'juniper-router-01')
        
        assert len(normalized) == 2
        assert all(route['protocol'] == 'ISIS' for route in normalized)
    
    def test_juniper_interface_naming(self, juniper_collector, normalizer):
        """Test Juniper interface naming conventions"""
        raw_routes = [
            {'network': '192.168.1.0/24', 'protocol': 'Direct', 'interface': 'ge-0/0/0'},
            {'network': '10.0.0.0/8', 'protocol': 'Direct', 'interface': 'xe-0/0/1'},
            {'network': '172.16.0.0/16', 'protocol': 'Direct', 'interface': 'et-0/0/2'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'juniper-router-01')
        
        assert normalized[0]['interface'] == 'ge-0/0/0'
        assert normalized[1]['interface'] == 'xe-0/0/1'
        assert normalized[2]['interface'] == 'et-0/0/2'


class TestCiscoNXOSRouting:
    """Test Cisco NX-OS-specific routing scenarios"""
    
    @pytest.fixture
    def nxos_collector(self):
        return RoutingCollector('cisco_nxos')
    
    @pytest.fixture
    def normalizer(self):
        return RoutingNormalizer()
    
    def test_nxos_connected_routes(self, nxos_collector, normalizer):
        """Test NX-OS connected route handling"""
        raw_routes = [
            {'network': '192.168.1.0/24', 'protocol': 'C', 'metric': '0', 'interface': 'Ethernet1/1'},
            {'network': '10.0.0.0/8', 'protocol': 'C', 'metric': '0', 'interface': 'Ethernet1/2'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'nxos-switch-01')
        
        assert len(normalized) == 2
        assert all(route['protocol'] == 'Connected' for route in normalized)
    
    def test_nxos_port_channel_routes(self, nxos_collector, normalizer):
        """Test NX-OS port-channel route handling — normalizer preserves case as-is."""
        raw_routes = [
            {'network': '192.168.1.0/24', 'protocol': 'C', 'metric': '0', 'interface': 'port-channel1'},
            {'network': '10.0.0.0/8', 'protocol': 'C', 'metric': '0', 'interface': 'port-channel2'}
        ]
        normalized = normalizer.normalize_routing_table(raw_routes, 'nxos-switch-01')
        assert len(normalized) == 2
        # normalizer preserves the interface name as-is (no forced capitalisation)
        assert normalized[0]['interface'].lower() == 'port-channel1'
        assert normalized[1]['interface'].lower() == 'port-channel2'
    
    def test_nxos_vlan_interface_routes(self, nxos_collector, normalizer):
        """Test NX-OS VLAN interface route handling"""
        raw_routes = [
            {'network': '192.168.1.0/24', 'protocol': 'C', 'metric': '0', 'interface': 'Vlan10'},
            {'network': '10.0.0.0/8', 'protocol': 'C', 'metric': '0', 'interface': 'Vlan20'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'nxos-switch-01')
        
        assert len(normalized) == 2
        assert normalized[0]['interface'] == 'Vlan10'
        assert normalized[1]['interface'] == 'Vlan20'


class TestAristaEOSRouting:
    """Test Arista EOS-specific routing scenarios"""
    
    @pytest.fixture
    def arista_collector(self):
        return RoutingCollector('arista_eos')
    
    @pytest.fixture
    def normalizer(self):
        return RoutingNormalizer()
    
    def test_arista_connected_routes(self, arista_collector, normalizer):
        """Test Arista EOS connected route handling"""
        raw_routes = [
            {'network': '192.168.1.0/24', 'protocol': 'C', 'metric': '0', 'interface': 'Ethernet1'},
            {'network': '10.0.0.0/8', 'protocol': 'C', 'metric': '0', 'interface': 'Ethernet2'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'arista-switch-01')
        
        assert len(normalized) == 2
        assert all(route['protocol'] == 'Connected' for route in normalized)
    
    def test_arista_interface_naming(self, arista_collector, normalizer):
        """Test Arista interface naming conventions"""
        raw_routes = [
            {'network': '192.168.1.0/24', 'protocol': 'C', 'interface': 'Ethernet1'},
            {'network': '10.0.0.0/8', 'protocol': 'C', 'interface': 'Ethernet1/1'},
            {'network': '172.16.0.0/16', 'protocol': 'C', 'interface': 'Port-Channel1'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'arista-switch-01')
        
        assert normalized[0]['interface'] == 'Ethernet1'
        assert normalized[1]['interface'] == 'Ethernet1/1'
        assert normalized[2]['interface'] == 'Port-Channel1'


class TestMultiVendorTopology:
    """Test multi-vendor topology integration"""
    
    @pytest.fixture
    def graph_builder(self):
        return L3TopologyGraphBuilder()
    
    @pytest.fixture
    def normalizer(self):
        return RoutingNormalizer()
    
    def test_cisco_juniper_interop(self, graph_builder, normalizer):
        """Test Cisco and Juniper interoperability"""
        cisco_routes = [
            {'network': '192.168.1.0/24', 'protocol': 'C', 'metric': '0', 'interface': 'Gi1/0/1', 'next_hop': '0.0.0.0'},
            {'network': '10.0.0.0/8', 'protocol': 'S', 'metric': '[1/0]', 'next_hop': '10.0.0.1', 'interface': 'Gi1/0/2'}
        ]
        
        juniper_routes = [
            {'network': '192.168.1.0/24', 'protocol': 'Direct', 'metric': '0', 'interface': 'ge-0/0/0', 'next_hop': '0.0.0.0'},
            {'network': '172.16.0.0/16', 'protocol': 'OSPF', 'metric': '10', 'next_hop': '10.0.0.2', 'interface': 'ge-0/0/1'}
        ]
        
        cisco_normalized = normalizer.normalize_routing_table(cisco_routes, 'cisco-core-01')
        juniper_normalized = normalizer.normalize_routing_table(juniper_routes, 'juniper-core-01')
        
        all_routes = cisco_normalized + juniper_normalized
        topology = graph_builder.build_topology(all_routes)
        
        assert topology['analysis']['total_devices'] == 2
        assert len(topology['nodes']) >= 2
    
    def test_three_vendor_topology(self, graph_builder, normalizer):
        """Test three-vendor topology (Cisco, Juniper, Arista)."""
        cisco_routes = [
            {'network': '192.168.1.0/24', 'protocol': 'C', 'metric': '0', 'interface': 'Gi1/0/1', 'next_hop': '0.0.0.0'}
        ]
        juniper_routes = [
            {'network': '10.0.0.0/8', 'protocol': 'Direct', 'metric': '0', 'interface': 'ge-0/0/0', 'next_hop': '0.0.0.0'}
        ]
        arista_routes = [
            {'network': '172.16.0.0/16', 'protocol': 'C', 'metric': '0', 'interface': 'Ethernet1', 'next_hop': '0.0.0.0'}
        ]
        cisco_normalized = normalizer.normalize_routing_table(cisco_routes, 'cisco-router')
        juniper_normalized = normalizer.normalize_routing_table(juniper_routes, 'juniper-router')
        arista_normalized = normalizer.normalize_routing_table(arista_routes, 'arista-switch')
        all_routes = cisco_normalized + juniper_normalized + arista_normalized
        topology = graph_builder.build_topology(all_routes)
        assert topology['analysis']['total_devices'] == 3
        # Use subnet_analysis from SubnetAnalyzer, not the old 'subnets' key
        from modules.routing_analyzer.graph_builder import SubnetAnalyzer
        subnet_analysis = SubnetAnalyzer().analyze_subnets(all_routes)
        assert len(subnet_analysis) == 3


class TestEdgeCaseRouting:
    """Test edge case routing scenarios"""
    
    @pytest.fixture
    def normalizer(self):
        return RoutingNormalizer()
    
    @pytest.fixture
    def graph_builder(self):
        return L3TopologyGraphBuilder()
    
    def test_host_routes(self, normalizer):
        """Test /32 host routes"""
        raw_routes = [
            {'network': '192.168.1.1/32', 'protocol': 'S', 'metric': '[1/0]', 'next_hop': '10.0.0.1'},
            {'network': '10.0.0.1/32', 'protocol': 'S', 'metric': '[1/0]', 'next_hop': '10.0.0.2'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'router-01')
        
        assert len(normalized) == 2
        assert all('/32' in route['destination'] for route in normalized)
    
    def test_supernet_routes(self, normalizer):
        """Test supernet routes"""
        raw_routes = [
            {'network': '10.0.0.0/8', 'protocol': 'S', 'metric': '[1/0]', 'next_hop': '10.0.0.1'},
            {'network': '172.16.0.0/12', 'protocol': 'S', 'metric': '[1/0]', 'next_hop': '10.0.0.2'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'router-01')
        
        assert len(normalized) == 2
        assert normalized[0]['destination'] == '10.0.0.0/8'
        assert normalized[1]['destination'] == '172.16.0.0/12'
    
    def test_multicast_routes(self, normalizer):
        """Multicast routes are filtered out by normalizer (is_multicast check)."""
        raw_routes = [
            {'network': '224.0.0.0/4', 'protocol': 'S', 'metric': '[1/0]', 'next_hop': '10.0.0.1'},
            {'network': '239.0.0.0/8', 'protocol': 'S', 'metric': '[1/0]', 'next_hop': '10.0.0.2'}
        ]
        normalized = normalizer.normalize_routing_table(raw_routes, 'router-01')
        # normalizer strips multicast destinations → 0 results
        assert len(normalized) == 0
    
    def test_ipv6_routes(self, normalizer):
        """Test IPv6 routing (basic support)"""
        raw_routes = [
            {'network': '2001:db8::/32', 'protocol': 'S', 'metric': '[1/0]', 'next_hop': '2001:db8::1'},
            {'network': 'fe80::/10', 'protocol': 'C', 'metric': '0', 'interface': 'Gi1/0/1'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'router-01')
        
        assert len(normalized) == 2
        assert all(':' in route['destination'] for route in normalized)
    
    def test_recursive_routing(self, graph_builder, normalizer):
        """Recursive routing: build_topology produces nodes for all devices and gateways."""
        raw_routes = [
            {'network': '192.168.1.0/24', 'protocol': 'S', 'metric': '[1/0]', 'next_hop': '10.0.0.1'},
            {'network': '10.0.0.0/8', 'protocol': 'S', 'metric': '[1/0]', 'next_hop': '172.16.0.1'},
            {'network': '172.16.0.0/16', 'protocol': 'C', 'metric': '0', 'interface': 'Gi1/0/1', 'next_hop': '0.0.0.0'}
        ]
        normalized = normalizer.normalize_routing_table(raw_routes, 'router-01')
        topology = graph_builder.build_topology(normalized)
        # Two gateway nodes (10.0.0.1 and 172.16.0.1) must be present
        node_ids = {n['id'] for n in topology['nodes']}
        assert '10.0.0.1' in node_ids
        assert '172.16.0.1' in node_ids
    
    def test_load_balancing_routes(self, normalizer):
        """Test ECMP/load balancing routes"""
        raw_routes = [
            {'network': '192.168.1.0/24', 'protocol': 'S', 'metric': '[1/0]', 'next_hop': '10.0.0.1'},
            {'network': '192.168.1.0/24', 'protocol': 'S', 'metric': '[1/0]', 'next_hop': '10.0.0.2'},
            {'network': '192.168.1.0/24', 'protocol': 'S', 'metric': '[1/0]', 'next_hop': '10.0.0.3'}
        ]
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'router-01')
        
        assert len(normalized) == 3
        assert all(route['destination'] == '192.168.1.0/24' for route in normalized)
    
    def test_route_flapping_scenario(self, graph_builder, normalizer):
        """Test route flapping scenario"""
        # Simulate route changes over time
        routes_v1 = [
            {'network': '192.168.1.0/24', 'protocol': 'O', 'metric': '[110/2]', 'next_hop': '10.0.0.1'}
        ]
        
        routes_v2 = [
            {'network': '192.168.1.0/24', 'protocol': 'B', 'metric': '[20/0]', 'next_hop': '10.0.0.2'}
        ]
        
        normalized_v1 = normalizer.normalize_routing_table(routes_v1, 'router-01')
        normalized_v2 = normalizer.normalize_routing_table(routes_v2, 'router-01')
        
        # Both should process successfully
        assert len(normalized_v1) == 1
        assert len(normalized_v2) == 1
        assert normalized_v1[0]['protocol'] == 'OSPF'
        assert normalized_v2[0]['protocol'] == 'BGP'


class TestLargeScaleRouting:
    """Test large-scale routing scenarios"""
    
    @pytest.fixture
    def normalizer(self):
        return RoutingNormalizer()
    
    @pytest.fixture
    def graph_builder(self):
        return L3TopologyGraphBuilder()
    
    def test_large_routing_table(self, normalizer):
        """Test handling of large routing tables (1000+ routes)"""
        raw_routes = []
        for i in range(1000):
            raw_routes.append({
                'network': f'192.168.{i}.0/24',
                'protocol': 'S' if i % 2 == 0 else 'O',
                'metric': '[1/0]' if i % 2 == 0 else '[110/2]',
                'next_hop': f'10.0.0.{i % 256}'
            })
        
        normalized = normalizer.normalize_routing_table(raw_routes, 'core-router')
        
        assert len(normalized) == 1000
        assert all('destination' in route for route in normalized)
    
    def test_multi_device_large_scale(self, graph_builder, normalizer):
        """Test multi-device topology with large routing tables."""
        all_routes = []
        for device_id in range(10):
            raw = []
            for i in range(100):
                raw.append({
                    'network': f'10.{device_id}.{i}.0/24',
                    'protocol': 'C',
                    'metric': '0',
                    'interface': f'Gi1/0/{i % 10}',
                    'next_hop': '0.0.0.0',
                })
            all_routes.extend(
                normalizer.normalize_routing_table(raw, f'device-{device_id}')
            )
        topology = graph_builder.build_topology(all_routes)
        assert topology['analysis']['total_devices'] == 10
        assert topology['analysis']['total_routes'] == 1000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
