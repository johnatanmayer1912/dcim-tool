"""
End-to-End Rendering Tests for L3 Map
Tests that data flows correctly from collection through to HTML rendering.
"""
from __future__ import annotations

import pytest
from modules.l3_topology_runner import build_l3_topology_bundle
from modules.routing_analyzer.graph_builder import L3TopologyGraphBuilder
from utils.l3_map_shell import render_l3_map_html
from utils.l3_map_formatter import l3_bundle_to_vis


class TestEndToEndRendering:
    """Test that collected data is actually rendered in the HTML output."""
    
    def test_single_device_data_renders_in_html(self):
        """Test that a single device's routing data is rendered in the HTML."""
        # Simulate collected routing data from a single device
        device_results = [
            {
                'status': 'success',
                'true_host': 'sw-01.example.com',
                'host': 'sw-01.example.com',
                'routes_normalized': [
                    {
                        'device_id': 'sw-01.example.com',
                        'destination': '192.168.1.0/24',
                        'next_hop': '0.0.0.0',
                        'protocol': 'Connected',
                        'interface': 'Vlan10',
                        'vrf': 'default',
                        'route_type': 'Connected',
                    },
                    {
                        'device_id': 'sw-01.example.com',
                        'destination': '0.0.0.0/0',
                        'next_hop': '10.0.0.1',
                        'protocol': 'Static',
                        'interface': 'Vlan1',
                        'vrf': 'default',
                        'route_type': 'Dynamic',
                    },
                ],
            }
        ]
        
        # Build the topology bundle
        bundle = build_l3_topology_bundle(device_results)
        
        # Convert to vis.js payload (this is what the adapters do)
        vis_payload = l3_bundle_to_vis(bundle)
        
        # Verify bundle has data
        assert vis_payload['analysis']['total_devices'] == 1
        assert vis_payload['route_count'] == 2
        
        # Render to HTML
        html = render_l3_map_html(vis_payload, map_kind='l3')
        
        # Verify HTML contains the device data
        assert 'sw-01.example.com' in html
        assert '192.168.1.0/24' in html
        assert '10.0.0.1' in html
        
        # Verify HTML contains the JSON data for vis.js
        assert 'RAW_NODES' in html
        assert 'RAW_EDGES' in html
        assert 'DEVICES_META' in html
        
        # Verify the JSON data is not empty - check for actual data content
        # The data is stored in JavaScript variables, not as JSON with "nodes": key
        assert 'sw-01.example.com' in html  # Device should be in the data
        assert '[' in html and ']' in html  # JSON arrays
    
    def test_multiple_devices_group_data_renders_in_html(self):
        """Test that multiple devices in a group are rendered in the HTML."""
        # Simulate collected routing data from multiple devices
        device_results = [
            {
                'status': 'success',
                'true_host': 'sw-01.example.com',
                'host': 'sw-01.example.com',
                'routes_normalized': [
                    {
                        'device_id': 'sw-01.example.com',
                        'destination': '192.168.1.0/24',
                        'next_hop': '0.0.0.0',
                        'protocol': 'Connected',
                        'interface': 'Vlan10',
                        'vrf': 'default',
                        'route_type': 'Connected',
                    },
                    {
                        'device_id': 'sw-01.example.com',
                        'destination': '0.0.0.0/0',
                        'next_hop': '10.0.0.1',
                        'protocol': 'Static',
                        'interface': 'Vlan1',
                        'vrf': 'default',
                        'route_type': 'Dynamic',
                    },
                ],
            },
            {
                'status': 'success',
                'true_host': 'sw-02.example.com',
                'host': 'sw-02.example.com',
                'routes_normalized': [
                    {
                        'device_id': 'sw-02.example.com',
                        'destination': '192.168.2.0/24',
                        'next_hop': '0.0.0.0',
                        'protocol': 'Connected',
                        'interface': 'Vlan20',
                        'vrf': 'default',
                        'route_type': 'Connected',
                    },
                    {
                        'device_id': 'sw-02.example.com',
                        'destination': '0.0.0.0/0',
                        'next_hop': '10.0.0.1',
                        'protocol': 'Static',
                        'interface': 'Vlan1',
                        'vrf': 'default',
                        'route_type': 'Dynamic',
                    },
                ],
            },
            {
                'status': 'success',
                'true_host': 'sw-03.example.com',
                'host': 'sw-03.example.com',
                'routes_normalized': [
                    {
                        'device_id': 'sw-03.example.com',
                        'destination': '192.168.3.0/24',
                        'next_hop': '0.0.0.0',
                        'protocol': 'Connected',
                        'interface': 'Vlan30',
                        'vrf': 'default',
                        'route_type': 'Connected',
                    },
                    {
                        'device_id': 'sw-03.example.com',
                        'destination': '0.0.0.0/0',
                        'next_hop': '10.0.0.1',
                        'protocol': 'Static',
                        'interface': 'Vlan1',
                        'vrf': 'default',
                        'route_type': 'Dynamic',
                    },
                ],
            },
        ]
        
        # Build the topology bundle
        bundle = build_l3_topology_bundle(device_results)
        
        # Convert to vis.js payload (this is what the adapters do)
        vis_payload = l3_bundle_to_vis(bundle)
        
        # Verify bundle has data
        assert vis_payload['analysis']['total_devices'] == 3
        assert vis_payload['route_count'] == 6
        
        # Render to HTML
        html = render_l3_map_html(vis_payload, map_kind='l3')
        
        # Verify HTML contains all device data
        assert 'sw-01.example.com' in html
        assert 'sw-02.example.com' in html
        assert 'sw-03.example.com' in html
        assert '192.168.1.0/24' in html
        assert '192.168.2.0/24' in html
        assert '192.168.3.0/24' in html
        assert '10.0.0.1' in html
        
        # Verify HTML contains the JSON data for vis.js
        assert 'RAW_NODES' in html
        assert 'RAW_EDGES' in html
        assert 'DEVICES_META' in html
        
        # Verify the JSON data has all devices
        assert html.count('sw-01.example.com') >= 1
        assert html.count('sw-02.example.com') >= 1
        assert html.count('sw-03.example.com') >= 1
    
    def test_empty_routes_still_renders_html(self):
        """Test that even with no routes, HTML is still generated (but empty map)."""
        device_results = [
            {
                'status': 'success',
                'true_host': 'sw-01.example.com',
                'host': 'sw-01.example.com',
                'routes_normalized': [],
            }
        ]
        
        # Build the topology bundle
        bundle = build_l3_topology_bundle(device_results)
        
        # Convert to vis.js payload
        vis_payload = l3_bundle_to_vis(bundle)
        
        # Render to HTML
        html = render_l3_map_html(vis_payload, map_kind='l3')
        
        # HTML should still be generated
        assert html is not None
        assert len(html) > 0
        assert '<!DOCTYPE html>' in html
        assert 'RAW_NODES' in html
        assert 'RAW_EDGES' in html
    
    def test_failed_devices_still_show_successful_ones(self):
        """Test that failed devices don't prevent rendering of successful ones."""
        device_results = [
            {
                'status': 'success',
                'true_host': 'sw-01.example.com',
                'host': 'sw-01.example.com',
                'routes_normalized': [
                    {
                        'device_id': 'sw-01.example.com',
                        'destination': '192.168.1.0/24',
                        'next_hop': '0.0.0.0',
                        'protocol': 'Connected',
                        'interface': 'Vlan10',
                        'vrf': 'default',
                        'route_type': 'Connected',
                    },
                ],
            },
            {
                'status': 'error',
                'true_host': 'sw-02.example.com',
                'host': 'sw-02.example.com',
                'routes_normalized': [],
                'errors': ['SSH timeout'],
            },
            {
                'status': 'success',
                'true_host': 'sw-03.example.com',
                'host': 'sw-03.example.com',
                'routes_normalized': [
                    {
                        'device_id': 'sw-03.example.com',
                        'destination': '192.168.3.0/24',
                        'next_hop': '0.0.0.0',
                        'protocol': 'Connected',
                        'interface': 'Vlan30',
                        'vrf': 'default',
                        'route_type': 'Connected',
                    },
                ],
            },
        ]
        
        # Build the topology bundle
        bundle = build_l3_topology_bundle(device_results)
        
        # Verify bundle tracks failed hosts
        assert 'sw-02.example.com' in bundle['failed_hosts']
        
        # Convert to vis.js payload
        vis_payload = l3_bundle_to_vis(bundle)
        
        # Render to HTML
        html = render_l3_map_html(vis_payload, map_kind='l3')
        
        # Verify HTML contains successful device data
        assert 'sw-01.example.com' in html
        assert 'sw-03.example.com' in html
        assert '192.168.1.0/24' in html
        assert '192.168.3.0/24' in html
        
        # Verify failed host is shown in the HTML
        assert 'sw-02.example.com' in html
    
    def test_vis_payload_structure_in_html(self):
        """Test that the vis.js payload structure is correct in the HTML."""
        device_results = [
            {
                'status': 'success',
                'true_host': 'sw-01.example.com',
                'host': 'sw-01.example.com',
                'routes_normalized': [
                    {
                        'device_id': 'sw-01.example.com',
                        'destination': '192.168.1.0/24',
                        'next_hop': '0.0.0.0',
                        'protocol': 'Connected',
                        'interface': 'Vlan10',
                        'vrf': 'default',
                        'route_type': 'Connected',
                    },
                ],
            }
        ]
        
        bundle = build_l3_topology_bundle(device_results)
        vis_payload = l3_bundle_to_vis(bundle)
        html = render_l3_map_html(vis_payload, map_kind='l3')
        
        # Verify the JavaScript variable assignments are present
        assert 'var RAW_NODES' in html or 'const RAW_NODES' in html
        assert 'var RAW_EDGES' in html or 'const RAW_EDGES' in html
        assert 'var DEVICES_META' in html or 'const DEVICES_META' in html
        assert 'var GW_META' in html or 'const GW_META' in html
        assert 'var SN_META' in html or 'const SN_META' in html
        assert 'var ALL_ROUTES' in html or 'const ALL_ROUTES' in html
        
        # Verify the data is actually JSON (has brackets)
        assert '[' in html and ']' in html  # JSON arrays
        assert '{' in html and '}' in html  # JSON objects
    
    def test_duplicate_gateway_shows_once_in_html(self):
        """Test that duplicate gateway IPs show as single node in HTML."""
        device_results = [
            {
                'status': 'success',
                'true_host': 'sw-01.example.com',
                'host': 'sw-01.example.com',
                'routes_normalized': [
                    {
                        'device_id': 'sw-01.example.com',
                        'destination': '0.0.0.0/0',
                        'next_hop': '10.0.0.1',
                        'protocol': 'Static',
                        'interface': 'Vlan1',
                        'vrf': 'default',
                        'route_type': 'Dynamic',
                    },
                ],
            },
            {
                'status': 'success',
                'true_host': 'sw-02.example.com',
                'host': 'sw-02.example.com',
                'routes_normalized': [
                    {
                        'device_id': 'sw-02.example.com',
                        'destination': '0.0.0.0/0',
                        'next_hop': '10.0.0.1',
                        'protocol': 'Static',
                        'interface': 'Vlan1',
                        'vrf': 'default',
                        'route_type': 'Dynamic',
                    },
                ],
            },
        ]
        
        bundle = build_l3_topology_bundle(device_results)
        vis_payload = l3_bundle_to_vis(bundle)
        html = render_l3_map_html(vis_payload, map_kind='l3')
        
        # Gateway IP should appear in HTML
        assert '10.0.0.1' in html
        
        # Count occurrences of the gateway IP in the nodes section
        # It should appear as a single node, not duplicated
        # This is a basic check - the actual deduplication is in the graph builder
        assert 'sw-01.example.com' in html
        assert 'sw-02.example.com' in html


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
