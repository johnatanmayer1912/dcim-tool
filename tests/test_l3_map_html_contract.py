"""L3 cartography HTML contract and integration tests."""
from __future__ import annotations

import inspect
import os
import pytest
from unittest.mock import MagicMock, patch

from modules.discovery.advanced_mapper import AdvancedMapper
from modules.l3_topology_runner import (
    build_l3_topology_bundle,
    build_flow_topology_bundle,
    collect_device_routing,
    _device_conn_dict,
)
from modules.routing_analyzer.parser import RoutingParser
from modules.routing_analyzer.normalizer import RoutingNormalizer
from utils.l3_map_formatter import l3_bundle_to_vis, flow_bundle_to_vis
from utils.l3_map_shell import render_l3_map_html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, 'vlan_checker_web.py')
HTML = os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html')


CISCO_ROUTE_SAMPLE = """
Codes: C - connected, S - static, R - RIP, O - OSPF
Gateway of last resort is 10.0.0.1 to network 0.0.0.0

C        192.168.1.0/24 is directly connected, Vlan10
S*       0.0.0.0/0 [1/0] via 10.0.0.1
O        10.10.0.0/24 [110/2] via 10.0.0.2, 00:05:12, GigabitEthernet0/1
B        203.0.113.0/24 [20/0] via 192.0.2.1
"""

JUNOS_ROUTE_SAMPLE = """
203.0.113.0/24    *[Static/5] 1w6d
                    >  to 10.0.0.1 via ge-0/0/0.0
192.168.1.0/24    *[Direct/0] 2w1d
                    >  to 192.168.1.1 via ge-0/0/1.0
"""

NXOS_ROUTE_SAMPLE = """
IP Route Table for VRF "default"
C        192.168.1.0/24 is directly connected, Vlan10
S        0.0.0.0/0 [1/0] via 10.0.0.1, Ethernet1/1
O        172.16.0.0/16 [110/20] via 10.0.0.2, Vlan20
"""


class TestL3SafeConnectionContract:
    """Regression: safe_connection() takes a device dict — never port= kwarg."""

    def test_collect_device_routing_uses_device_dict_for_safe_connection(self):
        dev = {'host': '10.0.0.1', 'device_type': 'cisco_ios', 'port': 2222}
        mock_conn = MagicMock()
        mock_conn.find_prompt.return_value = 'sw1#'

        with patch('modules.l3_topology_runner.RoutingCollector') as mock_collector_cls, \
             patch('modules.l3_topology_runner.safe_connection') as mock_sc:
            mock_sc.return_value.__enter__.return_value = mock_conn
            mock_collector_cls.return_value.collect_routing_table.return_value = {
                'routing_tables': {},
                'routing_v6': {},
                'vrf_routes': {},
                'errors': [],
            }

            collect_device_routing(dev, 'user', 'pwd', 'secret', log=None)

            assert mock_sc.called
            args, kwargs = mock_sc.call_args
            device_arg = args[0]
            assert isinstance(device_arg, dict)
            assert device_arg['host'] == '10.0.0.1'
            assert device_arg['device_type'] == 'cisco_ios'
            assert device_arg['port'] == 2222
            assert 'port' not in kwargs

    def test_l3_runner_source_has_no_port_kwarg_on_safe_connection(self):
        import modules.l3_topology_runner as runner
        src = inspect.getsource(runner.collect_device_routing)
        assert 'port=port' not in src
        assert 'safe_connection(device' in src.replace(' ', '')

    def test_device_conn_dict_preserves_inventory_fields(self):
        dev = {'host': '192.168.1.10', 'device_type': 'juniper_junos', 'port': 8022, 'group': 'core'}
        out = _device_conn_dict(dev)
        assert out['host'] == '192.168.1.10'
        assert out['port'] == 8022
        assert out['group'] == 'core'


class TestL3MapNetworkMeta:
    def test_bundle_includes_mgmt_port_gateway_and_interfaces(self):
        routes = [
            {
                'destination': '192.168.1.0/24',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
                'interface': 'Vlan10',
                'route_type': 'Connected',
                'device_id': 'core-sw-01',
            },
            {
                'destination': '0.0.0.0/0',
                'next_hop': '10.0.0.1',
                'protocol': 'Static',
                'interface': 'Gi0/0',
                'route_type': 'Static',
                'device_id': 'core-sw-01',
            },
        ]
        bundle = build_l3_topology_bundle([{
            'status': 'success',
            'true_host': 'core-sw-01',
            'host': '10.0.0.5',
            'platform': 'cisco_ios',
            'ssh_port': 2222,
            'management_ip': '10.0.0.5',
            'routes_normalized': routes,
            'protocols': ['Connected', 'Static'],
            'network_meta': {
                'management_ip': '10.0.0.5',
                'ssh_port': 2222,
                'default_gateway': '10.0.0.1',
                'interfaces': {'Vlan10': '192.168.1.0/24', 'Gi0/0': '0.0.0.0/0'},
                'local_ips': [],
                'connected_subnets': ['192.168.1.0/24'],
            },
        }])
        meta = bundle['devices']['core-sw-01']
        assert meta['management_ip'] == '10.0.0.5'
        assert meta['ssh_port'] == 2222
        assert meta['default_gateway'] == '10.0.0.1'
        assert 'Vlan10' in meta['interfaces']
        vis = l3_bundle_to_vis(bundle)
        html = render_l3_map_html(vis, title='Meta Test', map_kind='l3')
        assert '10.0.0.5' in html
        assert 'Vlan10' in html
        assert 'Default GW' in html or 'default' in html.lower()


class TestRoutingParserRegex:
    def test_cisco_regex_parses_connected_and_ospf(self):
        parser = RoutingParser()
        routes = parser.parse_routing_output_regex('cisco_ios', CISCO_ROUTE_SAMPLE)
        assert len(routes) >= 3
        networks = {r['network'] for r in routes}
        assert '192.168.1.0/24' in networks
        assert '0.0.0.0/0' in networks or any('0.0.0.0' in n for n in networks)

    def test_juniper_regex_parses_routes(self):
        parser = RoutingParser()
        routes = parser.parse_routing_output_regex('juniper_junos', JUNOS_ROUTE_SAMPLE)
        assert len(routes) >= 1

    def test_nxos_regex_parses_routes(self):
        parser = RoutingParser()
        routes = parser.parse_routing_output_regex('cisco_nxos', NXOS_ROUTE_SAMPLE)
        assert len(routes) >= 2


class TestL3MapPipeline:
    @pytest.fixture
    def normalizer(self):
        return RoutingNormalizer()

    def test_l3_bundle_to_vis_and_html_offline(self, normalizer):
        raw = [
            {'network': '192.168.1.0/24', 'protocol': 'C', 'metric': '0', 'interface': 'Vlan10', 'next_hop': '0.0.0.0'},
            {'network': '10.10.0.0/24', 'protocol': 'O', 'metric': '[110/2]', 'next_hop': '10.0.0.1', 'interface': 'Gi0/1'},
        ]
        normalized = normalizer.normalize_routing_table(raw, 'core-sw-01')
        bundle = build_l3_topology_bundle([{
            'status': 'success',
            'true_host': 'core-sw-01',
            'routes_normalized': normalized,
        }])
        vis = l3_bundle_to_vis(bundle)
        html = render_l3_map_html(vis, title='Test L3', map_kind='l3')
        assert 'vis.Network' in html
        assert 'L2/L3 only — EVPN/VXLAN overlay not collected.' in html
        assert 'nstSetLayer' in html
        assert 'nstWhyThisLink' in html
        assert 'id="nst-why-link"' in html
        assert 'id="nst-overlay-empty"' in html
        assert 'Overlay not collected' in html
        assert 'vis-network' not in html or 'unpkg.com' not in html
        assert len(vis['nodes']) >= 1
        assert 'core-sw-01' in html or '192.168.1.0/24' in html

    def test_flow_map_pipeline(self, normalizer):
        raw = [
            {'network': '0.0.0.0/0', 'protocol': 'S', 'metric': '[1/0]', 'next_hop': '10.0.0.1'},
            {'network': '192.168.10.0/24', 'protocol': 'C', 'metric': '0', 'interface': 'Vlan10', 'next_hop': '0.0.0.0'},
        ]
        normalized = normalizer.normalize_routing_table(raw, 'gw-rtr-01')
        bundle = build_l3_topology_bundle([{
            'status': 'success',
            'true_host': 'gw-rtr-01',
            'routes_normalized': normalized,
        }])
        flow = build_flow_topology_bundle(bundle)
        vis = flow_bundle_to_vis(flow)
        html = render_l3_map_html(vis, title='Flow', map_kind='flow')
        assert 'Network Flow Map' in html or 'Flow' in html
        assert len(vis['nodes']) >= 1


class TestAdvancedMapperIntegration:
    def test_flow_map_not_empty_with_routes(self):
        mapper = AdvancedMapper()
        devices = [{
            'ip': '10.0.0.1',
            'hostname': 'rtr-a',
            'routes': [
                {'network': '0.0.0.0/0', 'protocol': 'S', 'next_hop': '203.0.113.1'},
                {'network': '192.168.1.0/24', 'protocol': 'C', 'interface': 'Vlan10'},
            ],
        }]
        result = mapper.build_flow_map(devices)
        assert len(result['nodes']) >= 2
        assert len(result['edges']) >= 1


class TestUIAndAPIContracts:
    def test_l3_actions_registered_in_web(self):
        src = open(WEB, encoding='utf-8').read()
        for action in ('l3_topology', 'flow_map', 'advanced_l2_map'):
            assert f"'{action}':" in src

    def test_l3_status_api_present(self):
        src = open(WEB, encoding='utf-8').read()
        assert '/api/l3-map/status' in src
        assert '/api/l3-map/open' in src

    def test_ui_no_raw_json_window_open_for_advanced_maps(self):
        html = open(HTML, encoding='utf-8').read()
        assert "window.open('/api/discovery/advanced_map/l3'" not in html
        assert "toolsRunL3Map('l3')" in html
        assert "toolsRunL3Map('flow')" in html
        assert "toolsRunL3Map('advanced_l2')" in html
        assert 'toolsSetMapLayer' in html

    def test_ui_l3_status_panel_present(self):
        html = open(HTML, encoding='utf-8').read()
        assert 'tools-l3-map-status' in html
        assert 'toolsOpenL3Map' in html
