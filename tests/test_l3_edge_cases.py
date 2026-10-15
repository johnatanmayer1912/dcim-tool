"""
Edge Case Tests for L3 Map Feature
Tests for duplicate gateway resolution, bulk scanning, and network crawling scenarios.
"""
from __future__ import annotations

import pytest
from modules.routing_analyzer.graph_builder import L3TopologyGraphBuilder


class TestDuplicateGatewayResolution:
    """Test that duplicate gateway nodes are properly resolved."""
    
    def test_single_gateway_multiple_switches(self):
        """1 gateway + 4 switches should show as 1 gateway node with 4 connections."""
        routes = [
            # Switch 1 routes to gateway
            {'device_id': 'sw-01', 'destination': '0.0.0.0/0', 'next_hop': '10.0.0.1', 'protocol': 'Static'},
            {'device_id': 'sw-01', 'destination': '192.168.1.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
            # Switch 2 routes to same gateway
            {'device_id': 'sw-02', 'destination': '0.0.0.0/0', 'next_hop': '10.0.0.1', 'protocol': 'Static'},
            {'device_id': 'sw-02', 'destination': '192.168.2.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
            # Switch 3 routes to same gateway
            {'device_id': 'sw-03', 'destination': '0.0.0.0/0', 'next_hop': '10.0.0.1', 'protocol': 'Static'},
            {'device_id': 'sw-03', 'destination': '192.168.3.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
            # Switch 4 routes to same gateway
            {'device_id': 'sw-04', 'destination': '0.0.0.0/0', 'next_hop': '10.0.0.1', 'protocol': 'Static'},
            {'device_id': 'sw-04', 'destination': '192.168.4.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
        ]
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Should have 4 device nodes (switches)
        device_nodes = [n for n in result['nodes'] if n['group'] == 'device']
        assert len(device_nodes) == 4
        
        # Should have 1 gateway node (not 4)
        gateway_nodes = [n for n in result['nodes'] if n['group'] == 'default_gateway']
        assert len(gateway_nodes) == 1
        assert gateway_nodes[0]['id'] == '10.0.0.1'
        
        # Gateway should have 4 incoming edges (from 4 switches)
        edges_to_gateway = [e for e in result['edges'] if e['to'] == '10.0.0.1']
        assert len(edges_to_gateway) == 4
        
        # Each switch should have an edge to the gateway
        for sw in ['sw-01', 'sw-02', 'sw-03', 'sw-04']:
            edges_from_sw = [e for e in result['edges'] if e['from'] == sw]
            assert len(edges_from_sw) >= 1
            assert any(e['to'] == '10.0.0.1' for e in edges_from_sw)
    
    def test_gateway_is_also_device(self):
        """Gateway that is also a device should be upgraded to gateway type."""
        routes = [
            # Gateway device has its own routes
            {'device_id': '10.0.0.1', 'destination': '192.168.100.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
            # Switch routes to gateway
            {'device_id': 'sw-01', 'destination': '0.0.0.0/0', 'next_hop': '10.0.0.1', 'protocol': 'Static'},
            {'device_id': 'sw-02', 'destination': '0.0.0.0/0', 'next_hop': '10.0.0.1', 'protocol': 'Static'},
        ]
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Should have 1 gateway node (the gateway device)
        gateway_nodes = [n for n in result['nodes'] if n['group'] == 'default_gateway']
        assert len(gateway_nodes) == 1
        assert gateway_nodes[0]['id'] == '10.0.0.1'
        
        # Should have 2 device nodes (switches)
        device_nodes = [n for n in result['nodes'] if n['group'] == 'device']
        assert len(device_nodes) == 2
        assert all(n['id'] in ['sw-01', 'sw-02'] for n in device_nodes)
        
        # Total nodes should be 5 (1 gateway + 2 switches + 2 subnets)
        assert len(result['nodes']) == 5
    
    def test_multiple_gateways_same_ip_different_contexts(self):
        """Same gateway IP appearing in different contexts should still deduplicate."""
        routes = [
            {'device_id': 'sw-01', 'destination': '0.0.0.0/0', 'next_hop': '10.0.0.1', 'protocol': 'Static'},
            {'device_id': 'sw-01', 'destination': '0.0.0.0/0', 'next_hop': '10.0.0.1', 'protocol': 'Static'},  # Duplicate
            {'device_id': 'sw-02', 'destination': '0.0.0.0/0', 'next_hop': '10.0.0.1', 'protocol': 'Static'},
        ]
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Should still have 1 gateway node
        gateway_nodes = [n for n in result['nodes'] if n['group'] == 'default_gateway']
        assert len(gateway_nodes) == 1
        
        # Edges should be deduplicated by (from, to, protocol)
        edges_to_gateway = [e for e in result['edges'] if e['to'] == '10.0.0.1']
        # sw-01 should have only 1 edge to gateway (deduplicated)
        edges_from_sw01 = [e for e in edges_to_gateway if e['from'] == 'sw-01']
        assert len(edges_from_sw01) == 1


class TestBulkScanning:
    """Test bulk/group device scanning functionality."""
    
    def test_large_device_count_handling(self):
        """Test that the system handles 150+ devices (current limit)."""
        routes = []
        for i in range(200):
            device_id = f'sw-{i:03d}'
            routes.append({
                'device_id': device_id,
                'destination': f'192.168.{i//256}.{i%256}.0/24',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
            })
            routes.append({
                'device_id': device_id,
                'destination': '0.0.0.0/0',
                'next_hop': '10.0.0.1',
                'protocol': 'Static',
            })
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Should handle all routes without error
        assert result['analysis']['total_routes'] == 400
        assert result['analysis']['total_devices'] == 200
    
    def test_device_groups(self):
        """Test that devices can be processed in groups."""
        # Simulate grouped devices by having them share gateways
        routes = []
        for group in ['group-a', 'group-b', 'group-c']:
            for i in range(10):
                device_id = f'{group}-sw-{i:02d}'
                routes.append({
                    'device_id': device_id,
                    'destination': f'192.168.{group[-1]}.{i}.0/24',
                    'next_hop': '0.0.0.0',
                    'protocol': 'Connected',
                })
                routes.append({
                    'device_id': device_id,
                    'destination': '0.0.0.0/0',
                    'next_hop': f'10.0.{group[-1]}.1',
                    'protocol': 'Static',
                })
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Should have 30 device nodes
        assert result['analysis']['total_devices'] == 30
        
        # Should have 3 gateway nodes (one per group)
        gateway_nodes = [n for n in result['nodes'] if n['group'] == 'default_gateway']
        assert len(gateway_nodes) == 3
    
    def test_mixed_device_types(self):
        """Test scanning mixed device types (switches, routers, firewalls)."""
        routes = [
            # Switch
            {'device_id': 'sw-01', 'destination': '192.168.1.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
            {'device_id': 'sw-01', 'destination': '0.0.0.0/0', 'next_hop': '10.0.0.1', 'protocol': 'Static'},
            # Router
            {'device_id': 'rtr-01', 'destination': '10.0.0.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
            {'device_id': 'rtr-01', 'destination': '0.0.0.0/0', 'next_hop': '203.0.113.1', 'protocol': 'Static'},
            # Firewall
            {'device_id': 'fw-01', 'destination': '203.0.113.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
        ]
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Should have 3 device nodes
        assert result['analysis']['total_devices'] == 3
        
        # Should have 2 gateway nodes
        gateway_nodes = [n for n in result['nodes'] if n['group'] in ['gateway', 'default_gateway']]
        assert len(gateway_nodes) == 2


class TestNetworkCrawlingScenarios:
    """Test network crawling and topology discovery scenarios."""
    
    def test_hub_and_spoke_topology(self):
        """Test hub-and-spoke topology (central router with many spokes)."""
        routes = []
        central_router = 'rtr-core-01'
        
        # Central router connected to many subnets
        for i in range(20):
            routes.append({
                'device_id': central_router,
                'destination': f'10.{i}.0.0/24',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
            })
        
        # Each spoke switch routes to central router
        for i in range(20):
            spoke_id = f'sw-spoke-{i:02d}'
            routes.append({
                'device_id': spoke_id,
                'destination': f'10.{i}.0.0/24',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
            })
            routes.append({
                'device_id': spoke_id,
                'destination': '0.0.0.0/0',
                'next_hop': f'10.{i}.0.1',
                'protocol': 'Static',
            })
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Should have 21 device nodes (1 core + 20 spokes)
        assert result['analysis']['total_devices'] == 21
        
        # Central router should have many connections
        edges_from_core = [e for e in result['edges'] if e['from'] == central_router]
        assert len(edges_from_core) >= 20
    
    def test_mesh_topology(self):
        """Test mesh topology where many devices connect to each other."""
        routes = []
        devices = [f'dev-{i:02d}' for i in range(10)]
        
        # Each device has routes to all other devices
        for dev in devices:
            for other in devices:
                if dev != other:
                    routes.append({
                        'device_id': dev,
                        'destination': f'192.168.{int(dev.split('-')[1])}.0/24',
                        'next_hop': f'192.168.{int(other.split('-')[1])}.1',
                        'protocol': 'Static',
                    })
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Should have 10 device nodes
        assert result['analysis']['total_devices'] == 10
        
        # Should have many gateway nodes (each device acts as gateway for others)
        gateway_nodes = [n for n in result['nodes'] if n['group'] in ['gateway', 'default_gateway']]
        assert len(gateway_nodes) >= 9  # At least 9 devices act as gateways
    
    def test_multi_layer_topology(self):
        """Test multi-layer topology (core, distribution, access)."""
        routes = []
        
        # Core layer
        for i in range(2):
            core_id = f'rtr-core-{i+1}'
            routes.append({
                'device_id': core_id,
                'destination': f'10.0.{i}.0/24',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
            })
        
        # Distribution layer
        for i in range(4):
            dist_id = f'rtr-dist-{i+1}'
            routes.append({
                'device_id': dist_id,
                'destination': f'10.1.{i}.0/24',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
            })
            routes.append({
                'device_id': dist_id,
                'destination': '0.0.0.0/0',
                'next_hop': '10.0.{i%2}.1',
                'protocol': 'OSPF',
            })
        
        # Access layer
        for i in range(8):
            access_id = f'sw-access-{i+1}'
            routes.append({
                'device_id': access_id,
                'destination': f'192.168.{i}.0/24',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
            })
            routes.append({
                'device_id': access_id,
                'destination': '0.0.0.0/0',
                'next_hop': f'10.1.{i%4}.1',
                'protocol': 'Static',
            })
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Should have 14 device nodes (2 core + 4 dist + 8 access)
        assert result['analysis']['total_devices'] == 14
        
        # Should have gateway nodes at each layer
        gateway_nodes = [n for n in result['nodes'] if n['group'] in ['gateway', 'default_gateway']]
        assert len(gateway_nodes) >= 4


class TestEdgeCaseConnections:
    """Test edge cases for connection handling."""
    
    def test_self_referential_routes(self):
        """Test that self-referential routes don't create self-loops."""
        routes = [
            {'device_id': 'sw-01', 'destination': '192.168.1.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
            {'device_id': 'sw-01', 'destination': '192.168.1.0/24', 'next_hop': '192.168.1.1', 'protocol': 'Static'},  # Self-ref
        ]
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Should not have self-loop edges
        self_loops = [e for e in result['edges'] if e['from'] == e['to']]
        assert len(self_loops) == 0
    
    def test_loopback_addresses(self):
        """Test that loopback addresses are handled correctly."""
        routes = [
            {'device_id': 'sw-01', 'destination': '192.168.1.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
            {'device_id': 'sw-01', 'destination': '0.0.0.0/0', 'next_hop': '127.0.0.1', 'protocol': 'Static'},  # Loopback
        ]
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Loopback should be filtered out
        gateway_nodes = [n for n in result['nodes'] if n['group'] in ['gateway', 'default_gateway']]
        assert len(gateway_nodes) == 0
    
    def test_multicast_routes(self):
        """Test that multicast routes are filtered out."""
        routes = [
            {'device_id': 'sw-01', 'destination': '224.0.0.0/4', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
            {'device_id': 'sw-01', 'destination': '192.168.1.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
        ]
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Multicast should be filtered out
        subnet_nodes = [n for n in result['nodes'] if n['group'] == 'subnet']
        assert len(subnet_nodes) == 1
        assert subnet_nodes[0]['id'] == '192.168.1.0/24'
    
    def test_host_route_filtering(self):
        """Test that /32 host routes are filtered out from subnet nodes."""
        routes = [
            {'device_id': 'sw-01', 'destination': '192.168.1.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
            {'device_id': 'sw-01', 'destination': '192.168.1.1/32', 'next_hop': '0.0.0.0', 'protocol': 'Local'},
            {'device_id': 'sw-01', 'destination': '192.168.1.2/32', 'next_hop': '0.0.0.0', 'protocol': 'Local'},
        ]
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # /32 routes should not create subnet nodes
        subnet_nodes = [n for n in result['nodes'] if n['group'] == 'subnet']
        assert len(subnet_nodes) == 1
        assert subnet_nodes[0]['id'] == '192.168.1.0/24'
    
    def test_empty_next_hop(self):
        """Test routes with empty next-hop are handled correctly."""
        routes = [
            {'device_id': 'sw-01', 'destination': '192.168.1.0/24', 'next_hop': '', 'protocol': 'Connected'},
            {'device_id': 'sw-01', 'destination': '192.168.2.0/24', 'next_hop': None, 'protocol': 'Connected'},
            {'device_id': 'sw-01', 'destination': '192.168.3.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
        ]
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Should treat empty/None next-hop as connected
        assert result['analysis']['total_subnets'] == 3


class TestProtocolEdgeCases:
    """Test edge cases related to routing protocols."""
    
    def test_mixed_protocol_same_destination(self):
        """Test same destination with different protocols."""
        routes = [
            {'device_id': 'sw-01', 'destination': '192.168.1.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected'},
            {'device_id': 'sw-01', 'destination': '192.168.1.0/24', 'next_hop': '10.0.0.1', 'protocol': 'OSPF'},
            {'device_id': 'sw-01', 'destination': '192.168.1.0/24', 'next_hop': '10.0.0.2', 'protocol': 'Static'},
        ]
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Should have 1 subnet node
        subnet_nodes = [n for n in result['nodes'] if n['group'] == 'subnet']
        assert len(subnet_nodes) == 1
        
        # Should have edges for each protocol
        edges = [e for e in result['edges'] if e['to'] == '192.168.1.0/24' or e['from'] == '192.168.1.0/24']
        assert len(edges) >= 1
    
    def test_vrf_specific_routes(self):
        """Test VRF-specific routing doesn't create duplicate nodes."""
        routes = [
            {'device_id': 'sw-01', 'destination': '192.168.1.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected', 'vrf': 'MGMT'},
            {'device_id': 'sw-01', 'destination': '192.168.2.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected', 'vrf': 'PROD'},
            {'device_id': 'sw-01', 'destination': '192.168.3.0/24', 'next_hop': '0.0.0.0', 'protocol': 'Connected', 'vrf': 'default'},
        ]
        
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology(routes)
        
        # Should have 3 subnet nodes (different subnets)
        subnet_nodes = [n for n in result['nodes'] if n['group'] == 'subnet']
        assert len(subnet_nodes) == 3
        
        # Should have 1 device node
        device_nodes = [n for n in result['nodes'] if n['group'] == 'device']
        assert len(device_nodes) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
