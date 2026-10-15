"""
tests/test_l3_cartography_comprehensive.py
-------------------------------------------
Master test file for L3 cartography integration.
All tests are self-contained — no SSH required.
"""
import sys
import os
import time
import re

# Ensure project root on path
_proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _proj_root not in sys.path:
    sys.path.insert(0, _proj_root)

import pytest

from modules.routing_analyzer.parser import RoutingParser
from modules.routing_analyzer.normalizer import RoutingNormalizer
from modules.routing_analyzer.graph_builder import (
    L3TopologyGraphBuilder, SubnetAnalyzer, GatewayDetector,
)
from modules.l3_topology_runner import (
    build_l3_topology_bundle, build_flow_topology_bundle,
)
from utils.l3_map_formatter import l3_bundle_to_vis, flow_bundle_to_vis
from utils.l3_map_shell import render_l3_map_html


# ---------------------------------------------------------------------------
# Class TestCiscoIOSParserEdgeCases
# ---------------------------------------------------------------------------

class TestCiscoIOSParserEdgeCases:
    """Edge-case parsing of Cisco IOS 'show ip route' output variants."""

    @pytest.fixture(autouse=True)
    def _parser(self):
        self.parser = RoutingParser()

    def _parse(self, text):
        return self.parser.parse_routing_output_regex('cisco_ios', text)

    def test_ios_standard_connected_routes(self):
        output = (
            "C        10.1.1.0/24 is directly connected, GigabitEthernet0/0\n"
            "C        10.1.2.0/24 is directly connected, Vlan100\n"
            "L        10.1.1.1/32 is directly connected, GigabitEthernet0/0\n"
        )
        routes = self._parse(output)
        assert len(routes) >= 2
        networks = [r.get('network') or r.get('destination', '') for r in routes]
        assert any('10.1.1.0' in n for n in networks)

    def test_ios_ospf_multiline_via(self):
        output = (
            "O        10.0.0.0/8 [110/2] via 192.168.1.1, 00:01:23, GigabitEthernet0/1\n"
            "                    [110/2] via 192.168.1.2, 00:01:23, GigabitEthernet0/2\n"
        )
        routes = self._parse(output)
        assert len(routes) >= 1
        protocols = [r.get('protocol', '') for r in routes]
        assert any('OSPF' in p for p in protocols)

    def test_ios_default_route_static_star(self):
        output = "S*   0.0.0.0/0 [1/0] via 10.0.0.1\n"
        routes = self._parse(output)
        assert len(routes) == 1
        r = routes[0]
        assert '0.0.0.0' in (r.get('network') or r.get('destination', ''))
        assert r.get('protocol') in ('Static', 'S', 'S*')

    def test_ios_legacy_classful_mask(self):
        output = "S    192.168.1.0 255.255.255.0 [1/0] via 10.0.0.1\n"
        routes = self._parse(output)
        assert len(routes) >= 1
        networks = [r.get('network') or r.get('destination', '') for r in routes]
        assert any('192.168.1' in n for n in networks)

    def test_ios_bgp_external_route(self):
        output = "B        203.0.113.0/24 [20/0] via 10.0.0.1, 3d02h\n"
        routes = self._parse(output)
        assert len(routes) >= 1
        protocols = [r.get('protocol', '') for r in routes]
        assert any('BGP' in p for p in protocols)

    def test_ios_empty_output(self):
        routes = self._parse('')
        assert routes == []

    def test_ios_garbage_output(self):
        routes = self._parse('% Invalid input detected')
        # Should return empty list or list with no valid IP networks
        ip_re = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
        valid = [r for r in routes if ip_re.search(r.get('network', '') or r.get('destination', ''))]
        assert len(valid) == 0

    def test_ios_eigrp_routes(self):
        output = (
            "D        10.10.0.0/16 [90/2172416] via 10.0.0.1, 00:00:23, GigabitEthernet0/1\n"
            "D EX     10.20.0.0/16 [170/2172416] via 10.0.0.2, 00:00:23, GigabitEthernet0/2\n"
        )
        routes = self._parse(output)
        assert len(routes) >= 1
        protocols = [r.get('protocol', '') for r in routes]
        assert any('EIGRP' in p for p in protocols)

    def test_ios_ospf_inter_area(self):
        output = "O IA     192.168.100.0/24 [110/20] via 10.0.0.1, 00:01:00, GigabitEthernet0/1\n"
        routes = self._parse(output)
        assert len(routes) >= 1

    def test_ios_isis_routes(self):
        output = "i L1     10.30.0.0/16 [115/20] via 10.0.0.1, 00:01:00, GigabitEthernet0/1\n"
        routes = self._parse(output)
        assert len(routes) >= 1


# ---------------------------------------------------------------------------
# Class TestCiscoNXOSParserEdgeCases
# ---------------------------------------------------------------------------

class TestCiscoNXOSParserEdgeCases:
    """Edge-case parsing of Cisco NX-OS 'show ip route' output."""

    @pytest.fixture(autouse=True)
    def _parser(self):
        self.parser = RoutingParser()

    def _parse(self, text):
        return self.parser.parse_routing_output_regex('cisco_nxos', text)

    def test_nxos_standard_format(self):
        output = (
            "IP Route Table for VRF \"default\"\n"
            "'*' denotes best ucast next-hop\n"
            "'**' denotes best mcast next-hop\n"
            "'[x/y]' denotes [preference/metric]\n"
            "'%<string>' in via output denotes VRF <string>\n\n"
            "10.1.1.0/24, ubest/mbest: 1/0, attached\n"
            "    *via 10.1.1.1, Eth1/1, [0/0], 00:05:00, direct\n"
            "10.1.2.0/24, ubest/mbest: 1/0\n"
            "    *via 10.0.0.1, Eth1/2, [110/20], 00:01:00, ospf-1, intra\n"
            "0.0.0.0/0, ubest/mbest: 1/0\n"
            "    *via 10.0.0.1, Eth1/3, [1/0], 00:01:00, static\n"
        )
        routes = self._parse(output)
        assert len(routes) >= 2
        networks = [r.get('network') or r.get('destination', '') for r in routes]
        assert any('10.1' in n for n in networks)
        next_hops = [r.get('next_hop', '') for r in routes]
        assert any('10.0.0.1' in nh for nh in next_hops)

    def test_nxos_local_route(self):
        output = "L 10.1.1.1/32, ubest/mbest: 1/0, attached\n    *via 10.1.1.1, Lo0, [0/0], 00:01:00, local\n"
        routes = self._parse(output)
        assert len(routes) >= 1

    def test_nxos_vlan_interface(self):
        output = (
            "192.168.1.0/24, ubest/mbest: 1/0, attached\n"
            "    *via 192.168.1.1, Vlan10, [0/0], 00:01:00, direct\n"
        )
        routes = self._parse(output)
        assert len(routes) >= 1

    def test_nxos_empty_output(self):
        routes = self._parse('')
        assert routes == []

    def test_nxos_bgp_route(self):
        output = (
            "203.0.113.0/24, ubest/mbest: 1/0\n"
            "    *via 10.0.0.1, Eth1/1, [20/0], 00:00:10, bgp-65001, external, tag 65002\n"
        )
        routes = self._parse(output)
        assert len(routes) >= 1


# ---------------------------------------------------------------------------
# Class TestJuniperJunosParserEdgeCases
# ---------------------------------------------------------------------------

class TestJuniperJunosParserEdgeCases:
    """Edge-case parsing of Juniper JunOS 'show route' output."""

    @pytest.fixture(autouse=True)
    def _parser(self):
        self.parser = RoutingParser()

    def _parse(self, text):
        return self.parser.parse_routing_output_regex('juniper_junos', text)

    def test_junos_classic_inet0(self):
        output = (
            "inet.0: 5 destinations, 5 routes (5 active, 0 holddown, 0 hidden)\n"
            "+ = Active Route, - = Last Active, * = Both\n\n"
            "10.1.1.0/24        *[Direct/0] 1w6d\n"
            "                    > via ge-0/0/0.0\n"
            "10.0.0.0/8         *[Static/5] 1w6d\n"
            "                    > to 10.1.1.1 via ge-0/0/0.0\n"
            "0.0.0.0/0          *[Static/5] 1w6d\n"
            "                    > to 10.1.1.1 via ge-0/0/0.0\n"
            "192.168.1.0/24     *[OSPF/10] 00:01:23, metric 2\n"
            "                    > to 10.1.1.1 via ge-0/0/0.0\n"
            "203.0.113.0/24     *[BGP/170] 00:05:30, localpref 100, from 10.0.0.2\n"
            "                    > to 10.1.1.1 via ge-0/0/0.0\n"
        )
        routes = self._parse(output)
        assert len(routes) >= 3
        networks = [r.get('network') or r.get('destination', '') for r in routes]
        assert any('10.1.1.0' in n for n in networks)

    def test_junos_multiple_nexthops(self):
        output = (
            "10.5.0.0/24        *[OSPF/10] 00:01:23\n"
            "                    > to 10.1.1.1 via ge-0/0/0.0\n"
            "                    > to 10.1.1.2 via ge-0/0/1.0\n"
        )
        routes = self._parse(output)
        assert len(routes) >= 1

    def test_junos_direct_route(self):
        output = (
            "10.0.0.0/30        *[Direct/0] 1w6d\n"
            "                    > via ge-0/0/0.0\n"
        )
        routes = self._parse(output)
        assert len(routes) >= 1
        # Protocol should canonicalize to Connected or Direct
        if routes:
            proto = routes[0].get('protocol', '')
            assert proto in ('Connected', 'Direct', 'Unknown')

    def test_junos_isis_routes(self):
        output = (
            "10.10.0.0/16       *[IS-IS/15] 00:01:00, metric 10\n"
            "                    > to 10.1.1.1 via ge-0/0/0.0\n"
        )
        routes = self._parse(output)
        assert len(routes) >= 1
        if routes:
            proto = routes[0].get('protocol', '')
            assert 'ISIS' in proto or 'IS-IS' in proto or proto == 'Unknown'

    def test_junos_empty_output(self):
        routes = self._parse('')
        assert routes == []

    def test_junos_garbage_output(self):
        routes = self._parse('error: unknown command')
        ip_re = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
        valid = [r for r in routes if ip_re.search(r.get('network', '') or r.get('destination', ''))]
        assert len(valid) == 0


# ---------------------------------------------------------------------------
# Class TestRoutingNormalizerEdgeCases
# ---------------------------------------------------------------------------

class TestRoutingNormalizerEdgeCases:
    """Edge cases for RoutingNormalizer."""

    @pytest.fixture(autouse=True)
    def _norm(self):
        self.norm = RoutingNormalizer()

    def test_normalize_strips_multicast(self):
        route = {'destination': '224.0.0.0/4', 'protocol': 'S'}
        result = self.norm.normalize_route(route, 'r1')
        assert result is None

    def test_normalize_cidr_strict(self):
        # Should not crash on unusual input
        route = {'destination': '10.1.1.0/255.255.255.0', 'protocol': 'C'}
        try:
            result = self.norm.normalize_route(route, 'r1')
            # either None or a dict — just mustn't raise
        except Exception as e:
            pytest.fail(f"normalize_route raised on unusual CIDR: {e}")

    def test_normalize_dedup_same_route_twice(self):
        route = {'destination': '10.0.0.0/8', 'protocol': 'S', 'next_hop': '10.0.0.1'}
        result = self.norm.normalize_routing_table([route, route], 'r1')
        assert len(result) == 1

    def test_normalize_vrf_preserved(self):
        route = {'destination': '10.0.0.0/8', 'protocol': 'S'}
        result = self.norm.normalize_route(route, 'r1', vrf='PROD')
        assert result is not None
        assert result['vrf'] == 'PROD'

    def test_normalize_admin_distance_from_bracket(self):
        route = {'destination': '10.0.0.0/8', 'metric': '[110/2]', 'protocol': 'O'}
        result = self.norm.normalize_route(route, 'r1')
        assert result is not None
        assert result['admin_distance'] == 110
        assert result['metric'] == 2

    def test_normalize_empty_next_hop(self):
        route = {'destination': '10.0.0.0/8', 'next_hop': '', 'protocol': 'C'}
        result = self.norm.normalize_route(route, 'r1')
        assert result is not None
        assert result['next_hop'] == ''

    def test_normalize_ospf_default_ad(self):
        route = {'destination': '10.0.0.0/8', 'protocol': 'O'}
        result = self.norm.normalize_route(route, 'r1')
        assert result is not None
        assert result['admin_distance'] == 110

    def test_normalize_protocol_with_star(self):
        route = {'destination': '0.0.0.0/0', 'protocol': 'S*', 'next_hop': '10.0.0.1'}
        result = self.norm.normalize_route(route, 'r1')
        assert result is not None
        assert result['protocol'] == 'Static'

    def test_normalize_protocol_direct(self):
        route = {'destination': '10.0.0.0/8', 'protocol': 'Direct'}
        result = self.norm.normalize_route(route, 'r1')
        assert result is not None
        assert result['protocol'] == 'Connected'

    def test_normalize_protocol_junos_bgp(self):
        route = {'destination': '10.0.0.0/8', 'protocol': 'BGP'}
        result = self.norm.normalize_route(route, 'r1')
        assert result is not None
        assert result['protocol'] == 'BGP'

    def test_normalize_large_table_performance(self):
        routes = [
            {'destination': f'10.{i // 256}.{i % 256}.0/24',
             'protocol': 'O', 'next_hop': '10.0.0.1'}
            for i in range(5000)
        ]
        t0 = time.time()
        result = self.norm.normalize_routing_table(routes, 'bigdevice')
        elapsed = time.time() - t0
        assert len(result) == 5000
        assert elapsed < 30, f"Normalization too slow: {elapsed:.1f}s"

    def test_normalize_invalid_ip_graceful(self):
        route = {'destination': '10.0.0.0/8', 'next_hop': 'not-an-ip', 'protocol': 'S'}
        result = self.norm.normalize_route(route, 'r1')
        assert result is not None
        assert result['next_hop'] == 'not-an-ip'


# ---------------------------------------------------------------------------
# Class TestGraphBuilderEdgeCases
# ---------------------------------------------------------------------------

class TestGraphBuilderEdgeCases:
    """Edge cases for L3TopologyGraphBuilder, SubnetAnalyzer, GatewayDetector."""

    def test_build_topology_empty(self):
        topo = L3TopologyGraphBuilder().build_topology([])
        assert topo['nodes'] == []
        assert topo['edges'] == []
        assert topo['analysis']['total_devices'] == 0
        assert topo['analysis']['total_routes'] == 0

    def test_build_topology_single_device_connected(self):
        data = [
            {'destination': f'10.0.{i}.0/24', 'next_hop': '0.0.0.0',
             'protocol': 'Connected', 'device_id': 'devA', 'route_type': 'Connected'}
            for i in range(3)
        ]
        topo = L3TopologyGraphBuilder().build_topology(data)
        node_ids = [n['id'] for n in topo['nodes']]
        assert 'devA' in node_ids

    def test_build_topology_device_is_gateway(self):
        data = [
            {'destination': '10.1.0.0/24', 'next_hop': '10.0.0.1',
             'protocol': 'Static', 'device_id': 'devA', 'route_type': 'Static'},
        ]
        topo = L3TopologyGraphBuilder().build_topology(data)
        node_ids = [n['id'] for n in topo['nodes']]
        assert '10.0.0.1' in node_ids

    def test_build_topology_default_route_gateway_type(self):
        data = [
            {'destination': '0.0.0.0/0', 'next_hop': '10.0.0.1',
             'protocol': 'Static', 'device_id': 'devA', 'route_type': 'Static'},
        ]
        gw_analysis = GatewayDetector().detect_gateways(data)
        assert '10.0.0.1' in gw_analysis
        assert gw_analysis['10.0.0.1']['is_default_gateway'] is True

    def test_build_topology_dedup_edges(self):
        # Same (from, to, proto) pair twice — only 1 edge after dedup
        data = [
            {'destination': '10.1.0.0/24', 'next_hop': '10.0.0.1',
             'protocol': 'OSPF', 'device_id': 'devA', 'route_type': 'Dynamic'},
            {'destination': '10.1.0.0/24', 'next_hop': '10.0.0.1',
             'protocol': 'OSPF', 'device_id': 'devA', 'route_type': 'Dynamic'},
        ]
        topo = L3TopologyGraphBuilder().build_topology(data)
        # Edges from devA to 10.0.0.1 with OSPF should be deduplicated
        matching = [e for e in topo['edges']
                    if e.get('from') == 'devA' and e.get('to') == '10.0.0.1']
        assert len(matching) == 1

    def test_build_topology_subnet_cap_300(self):
        data = [
            {'destination': f'10.{i // 256}.{i % 256}.0/24',
             'next_hop': '10.0.0.1',
             'protocol': 'OSPF', 'device_id': 'devA', 'route_type': 'Dynamic'}
            for i in range(400)
        ]
        topo = L3TopologyGraphBuilder().build_topology(data)
        subnet_nodes = [n for n in topo['nodes'] if n.get('group') == 'subnet' or n.get('type') == 'subnet']
        assert len(subnet_nodes) <= 300

    def test_build_topology_host_routes_excluded(self):
        data = [
            {'destination': '10.0.0.1/32', 'next_hop': '10.0.0.1',
             'protocol': 'Local', 'device_id': 'devA', 'route_type': 'Connected'},
        ]
        topo = L3TopologyGraphBuilder().build_topology(data)
        # /32 routes must not produce subnet nodes
        subnet_nodes = [n for n in topo['nodes']
                        if (n.get('group') == 'subnet' or n.get('type') == 'subnet')
                        and '10.0.0.1' in n.get('id', '')]
        assert len(subnet_nodes) == 0

    def test_build_topology_loopback_gw_excluded(self):
        data = [
            {'destination': '10.0.0.0/8', 'next_hop': '127.0.0.1',
             'protocol': 'Static', 'device_id': 'devA', 'route_type': 'Static'},
        ]
        topo = L3TopologyGraphBuilder().build_topology(data)
        node_ids = [n['id'] for n in topo['nodes']]
        assert '127.0.0.1' not in node_ids

    def test_build_topology_multicast_excluded(self):
        data = [
            {'destination': '224.0.0.1/32', 'next_hop': '10.0.0.1',
             'protocol': 'Static', 'device_id': 'devA', 'route_type': 'Static'},
        ]
        topo = L3TopologyGraphBuilder().build_topology(data)
        node_ids = [n['id'] for n in topo['nodes']]
        assert '224.0.0.1/32' not in node_ids
        assert '224.0.0.1' not in node_ids

    def test_detect_gateways_default_gateway(self):
        data = [
            {'destination': '0.0.0.0/0', 'next_hop': '10.0.0.1',
             'protocol': 'Static', 'device_id': 'devA'},
        ]
        result = GatewayDetector().detect_gateways(data)
        assert '10.0.0.1' in result
        assert result['10.0.0.1']['is_default_gateway'] is True

    def test_detect_gateways_excludes_loopback(self):
        data = [
            {'destination': '10.0.0.0/8', 'next_hop': '127.0.0.1',
             'protocol': 'Static', 'device_id': 'devA'},
        ]
        result = GatewayDetector().detect_gateways(data)
        assert '127.0.0.1' not in result

    def test_subnet_analyzer_prefix_len(self):
        data = [{'destination': '10.0.0.0/8', 'next_hop': '10.0.0.1',
                 'device_id': 'r1', 'protocol': 'S'}]
        result = SubnetAnalyzer().analyze_subnets(data)
        assert '10.0.0.0/8' in result
        assert result['10.0.0.0/8']['prefix_len'] == 8

    def test_subnet_analyzer_is_private(self):
        data = [{'destination': '192.168.1.0/24', 'next_hop': '10.0.0.1',
                 'device_id': 'r1', 'protocol': 'C'}]
        result = SubnetAnalyzer().analyze_subnets(data)
        assert result['192.168.1.0/24']['is_private'] is True

    def test_subnet_analyzer_excludes_multicast_flag(self):
        data = [{'destination': '224.0.0.0/4', 'next_hop': '10.0.0.1',
                 'device_id': 'r1', 'protocol': 'S'}]
        result = SubnetAnalyzer().analyze_subnets(data)
        # Multicast is NOT excluded from subnet_analysis, but flagged
        assert '224.0.0.0/4' in result
        assert result['224.0.0.0/4']['is_multicast'] is True


# ---------------------------------------------------------------------------
# Helpers for bundle/vis tests
# ---------------------------------------------------------------------------

def _make_device_result(host, routes, status='success', platform='cisco_ios'):
    return {
        'host': host,
        'true_host': host,
        'device_type': platform,
        'platform': platform,
        'status': status,
        'device_id': host,
        'routes_raw_count': len(routes),
        'routes_normalized': routes,
        'errors': [],
        'protocols': list({r.get('protocol', '') for r in routes}),
        'vrf_routes_by_vrf': {},
    }


def _norm_routes(raw_list, device_id='testdev', vrf='default'):
    norm = RoutingNormalizer()
    return norm.normalize_routing_table(raw_list, device_id, vrf)


# ---------------------------------------------------------------------------
# Class TestL3BundleAndVisPayload
# ---------------------------------------------------------------------------

class TestL3BundleAndVisPayload:
    """Tests for bundle builders and vis formatters."""

    @pytest.fixture
    def basic_routes(self):
        return _norm_routes([
            {'destination': f'10.0.{i}.0/24', 'next_hop': '10.0.0.1',
             'protocol': 'OSPF', 'interface': 'Gi0/0'}
            for i in range(5)
        ], 'dev1')

    @pytest.fixture
    def bundle(self, basic_routes):
        result = _make_device_result('dev1', basic_routes)
        return build_l3_topology_bundle([result])

    @pytest.fixture
    def vis(self, bundle):
        return l3_bundle_to_vis(bundle)

    def test_bundle_failed_hosts_aggregated(self):
        ok_routes = _norm_routes([
            {'destination': '10.0.0.0/24', 'next_hop': '10.0.0.1', 'protocol': 'C'}
        ], 'dev-ok')
        ok = _make_device_result('dev-ok', ok_routes)
        fail = _make_device_result('dev-fail', [], status='error')
        bundle = build_l3_topology_bundle([ok, fail])
        assert 'dev-fail' in bundle['failed_hosts']

    def test_bundle_route_count(self, basic_routes):
        result = _make_device_result('dev1', basic_routes)
        bundle = build_l3_topology_bundle([result])
        assert bundle['route_count'] == len(basic_routes)

    def test_vis_payload_nodes_and_edges_present(self, vis):
        assert 'nodes' in vis
        assert 'edges' in vis
        assert isinstance(vis['nodes'], list)
        assert isinstance(vis['edges'], list)

    def test_vis_edges_from_to_not_source_target(self, vis):
        for edge in vis['edges']:
            assert 'from' in edge
            assert 'to' in edge
            assert 'source' not in edge
            assert 'target' not in edge

    def test_render_html_offline_no_cdn(self, vis):
        try:
            html = render_l3_map_html(vis)
        except Exception:
            pytest.skip("render_l3_map_html raised (vis.js missing?) — skipping CDN check")
        # If vis.js is bundled there should be no CDN references
        if 'vis.Network' in html:
            assert 'unpkg.com' not in html, "CDN reference found in offline HTML"
            assert 'cdnjs.com' not in html, "CDN reference found in offline HTML"

    def test_render_html_contains_vis_network(self, vis):
        html = render_l3_map_html(vis)
        assert 'vis.Network' in html

    def test_render_html_has_search_input(self, vis):
        html = render_l3_map_html(vis)
        assert 'search-input' in html

    def test_render_html_has_detail_panel(self, vis):
        html = render_l3_map_html(vis)
        assert 'detail-panel' in html

    def test_render_html_has_stats_bar(self, vis):
        html = render_l3_map_html(vis)
        assert 'l3-stat' in html

    def test_render_html_has_legend(self, vis):
        html = render_l3_map_html(vis)
        assert 'l3-legend' in html

    def test_render_html_no_text_overlap_structure(self, vis):
        html = render_l3_map_html(vis)
        assert 'l3-layout' in html
        assert 'l3-network' in html

    def test_flow_map_bundle_has_gateway_nodes(self):
        routes = _norm_routes([
            {'destination': '0.0.0.0/0', 'next_hop': '10.0.0.1', 'protocol': 'S'}
        ], 'dev1')
        result = _make_device_result('dev1', routes)
        l3_bundle = build_l3_topology_bundle([result])
        flow = build_flow_topology_bundle(l3_bundle)
        gw_nodes = [n for n in flow.get('nodes', [])
                    if n.get('group') == 'default_gateway']
        assert len(gw_nodes) >= 1

    def test_flow_map_vis_edges_normalized(self):
        routes = _norm_routes([
            {'destination': '0.0.0.0/0', 'next_hop': '10.0.0.1', 'protocol': 'S'}
        ], 'dev1')
        result = _make_device_result('dev1', routes)
        l3_bundle = build_l3_topology_bundle([result])
        flow = build_flow_topology_bundle(l3_bundle)
        vis = flow_bundle_to_vis(flow)
        for edge in vis.get('edges', []):
            assert 'from' in edge
            assert 'to' in edge

    def test_l3_bundle_with_vrf_routes(self):
        vrf_routes = _norm_routes([
            {'destination': '172.16.0.0/16', 'next_hop': '10.0.0.1', 'protocol': 'O'}
        ], 'dev1', 'VRF_PROD')
        result = _make_device_result('dev1', vrf_routes)
        result['vrf_routes_by_vrf'] = {'VRF_PROD': vrf_routes}
        bundle = build_l3_topology_bundle([result])
        assert bundle['route_count'] >= len(vrf_routes)


# ---------------------------------------------------------------------------
# Class TestRealWorldOutputSamples
# ---------------------------------------------------------------------------

class TestRealWorldOutputSamples:
    """Tests using realistic multi-line 'show ip route' outputs."""

    IOS_FULL_TABLE = """
Codes: C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area
Gateway of last resort is 10.0.0.1 to network 0.0.0.0

      10.0.0.0/8 is variably subnetted, 4 subnets, 3 masks
C        10.0.0.0/30 is directly connected, GigabitEthernet0/0
L        10.0.0.1/32 is directly connected, GigabitEthernet0/0
O        10.1.0.0/24 [110/2] via 10.0.0.2, 00:05:12, GigabitEthernet0/0
O IA     10.2.0.0/24 [110/3] via 10.0.0.2, 00:05:12, GigabitEthernet0/0
S*       0.0.0.0/0 [1/0] via 10.0.0.1
B        203.0.113.0/24 [20/0] via 192.0.2.1, 3d02h
"""

    NXOS_FULL_TABLE = """
IP Route Table for VRF "default"
'*' denotes best ucast next-hop
10.0.0.0/30, ubest/mbest: 1/0, attached
    *via 10.0.0.1, Eth1/1, [0/0], 00:05:00, direct
10.1.0.0/24, ubest/mbest: 1/0
    *via 10.0.0.2, Eth1/1, [110/20], 00:01:00, ospf-1, intra
0.0.0.0/0, ubest/mbest: 1/0
    *via 10.0.0.1, Eth1/1, [1/0], 00:01:00, static
"""

    JUNOS_FULL_TABLE = """
inet.0: 6 destinations, 6 routes (6 active, 0 holddown, 0 hidden)

10.0.0.0/30        *[Direct/0] 1w6d
                    > via ge-0/0/0.0
10.0.0.1/32        *[Local/0] 1w6d
                      Local via ge-0/0/0.0
10.1.0.0/24        *[OSPF/10] 00:05:12, metric 2
                    > to 10.0.0.2 via ge-0/0/0.0
0.0.0.0/0          *[Static/5] 1w6d
                    > to 10.0.0.1 via ge-0/0/0.0
203.0.113.0/24     *[BGP/170] 3d02h, localpref 100
                    > to 10.0.0.1 via ge-0/0/0.0
"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.parser = RoutingParser()
        self.norm = RoutingNormalizer()

    def _full_pipeline(self, platform, raw_text, device_id='testdev'):
        routes = self.parser.parse_routing_output_regex(platform, raw_text)
        return self.norm.normalize_routing_table(routes, device_id)

    def test_ios_full_table_parse(self):
        routes = self.parser.parse_routing_output_regex('cisco_ios', self.IOS_FULL_TABLE)
        assert len(routes) >= 4

    def test_nxos_full_table_parse(self):
        routes = self.parser.parse_routing_output_regex('cisco_nxos', self.NXOS_FULL_TABLE)
        assert len(routes) >= 2

    def test_junos_full_table_parse(self):
        routes = self.parser.parse_routing_output_regex('juniper_junos', self.JUNOS_FULL_TABLE)
        assert len(routes) >= 3

    def test_ios_full_pipeline_to_html(self):
        normalized = self._full_pipeline('cisco_ios', self.IOS_FULL_TABLE, 'ios-dev')
        result = _make_device_result('ios-dev', normalized)
        bundle = build_l3_topology_bundle([result])
        vis = l3_bundle_to_vis(bundle)
        html = render_l3_map_html(vis)
        assert 'vis.Network' in html
        assert len(html) > 10000

    def test_nxos_full_pipeline_to_html(self):
        normalized = self._full_pipeline('cisco_nxos', self.NXOS_FULL_TABLE, 'nxos-dev')
        result = _make_device_result('nxos-dev', normalized)
        bundle = build_l3_topology_bundle([result])
        vis = l3_bundle_to_vis(bundle)
        html = render_l3_map_html(vis)
        assert len(html) > 1000
        assert '<html' in html

    def test_junos_full_pipeline_to_html(self):
        normalized = self._full_pipeline('juniper_junos', self.JUNOS_FULL_TABLE, 'junos-dev')
        result = _make_device_result('junos-dev', normalized)
        bundle = build_l3_topology_bundle([result])
        vis = l3_bundle_to_vis(bundle)
        html = render_l3_map_html(vis)
        assert len(html) > 1000
        assert '<html' in html

    def test_multivendor_bundle_three_devices(self):
        ios_norm = self._full_pipeline('cisco_ios', self.IOS_FULL_TABLE, 'ios-dev')
        nxos_norm = self._full_pipeline('cisco_nxos', self.NXOS_FULL_TABLE, 'nxos-dev')
        junos_norm = self._full_pipeline('juniper_junos', self.JUNOS_FULL_TABLE, 'junos-dev')
        results = [
            _make_device_result('ios-dev', ios_norm, platform='cisco_ios'),
            _make_device_result('nxos-dev', nxos_norm, platform='cisco_nxos'),
            _make_device_result('junos-dev', junos_norm, platform='juniper_junos'),
        ]
        bundle = build_l3_topology_bundle(results)
        assert bundle['route_count'] > 5
        assert len(bundle['devices']) == 3

    def test_bundle_to_vis_all_edge_keys_valid(self):
        ios_norm = self._full_pipeline('cisco_ios', self.IOS_FULL_TABLE, 'ios-dev')
        result = _make_device_result('ios-dev', ios_norm)
        bundle = build_l3_topology_bundle([result])
        vis = l3_bundle_to_vis(bundle)
        for edge in vis.get('edges', []):
            assert edge.get('from') is not None, f"Edge missing 'from': {edge}"
            assert edge.get('to') is not None, f"Edge missing 'to': {edge}"


# ---------------------------------------------------------------------------
# Class TestCollectorPlatformMapping
# ---------------------------------------------------------------------------

class TestCollectorPlatformMapping:
    """Tests for RoutingCollector — no SSH required."""

    @pytest.fixture(autouse=True)
    def _imports(self):
        from modules.routing_analyzer.collector import RoutingCollector, _is_valid_output
        self.Collector = RoutingCollector
        self._is_valid_output = _is_valid_output

    def test_collector_ios_commands(self):
        col = self.Collector('cisco_ios')
        cmds = [c for c, _ in col._command_list]
        assert any('show ip route' in c for c in cmds)

    def test_collector_nxos_commands(self):
        col = self.Collector('cisco_nxos')
        cmds = [c for c, _ in col._command_list]
        assert any('show ip route' in c for c in cmds)

    def test_collector_junos_commands(self):
        col = self.Collector('juniper_junos')
        cmds = [c for c, _ in col._command_list]
        assert any('show route' in c for c in cmds)

    def test_collector_invalid_output_detection(self):
        assert self._is_valid_output('') is False
        assert self._is_valid_output('% Invalid input') is False
        assert self._is_valid_output('10.0.0.0/8 is variably subnetted') is True

    def test_collector_vrf_name_parsing(self):
        col = self.Collector('cisco_ios')
        output = "Name\nVRF_PROD\nVRF_DEV\n"
        vrfs = col._parse_vrf_names(output)
        assert 'VRF_PROD' in vrfs
        assert 'VRF_DEV' in vrfs


# ---------------------------------------------------------------------------
# Class TestUIAndHTMLContracts
# ---------------------------------------------------------------------------

class TestUIAndHTMLContracts:
    """Validate integration contracts between UI, web API, and HTML output."""

    @pytest.fixture(autouse=True)
    def _load_files(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        html_path = os.path.join(base, 'modules', 'web', 'templates', 'index.html')
        web_path = os.path.join(base, 'vlan_checker_web.py')
        adapters_path = os.path.join(base, 'modules', 'adapters.py')

        with open(html_path, encoding='utf-8') as f:
            self.index_html = f.read()

        with open(web_path, encoding='utf-8') as f:
            self.web_py = f.read()

        with open(adapters_path, encoding='utf-8') as f:
            self.adapters_py = f.read()

    def test_swiss_tools_tab_has_5_map_buttons(self):
        for btn_id in ('btn-map-all', 'btn-map-vpc', 'btn-map-adv-l2',
                       'btn-map-adv-l3', 'btn-map-adv-flow'):
            assert btn_id in self.index_html, f"Missing button: {btn_id}"

    def test_l3_action_map_complete(self):
        assert 'L3_ACTION_MAP' in self.index_html
        assert "'l3'" in self.index_html or '"l3"' in self.index_html
        assert 'flow' in self.index_html
        assert 'advanced_l2' in self.index_html

    def test_tools_l3_map_status_panel_present(self):
        assert 'tools-l3-map-status' in self.index_html

    def test_open_l3_map_button_present(self):
        assert 'toolsOpenL3Map' in self.index_html

    def test_no_cdn_dependency_in_l3_map(self):
        """Rendered HTML should not reference CDN when vis.js file is present."""
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        vis_candidates = [
            os.path.join(base, 'vis-network.min.js'),
            os.path.join(base, 'modules', 'web', 'vis-network.min.js'),
        ]
        vis_exists = any(os.path.exists(p) for p in vis_candidates)
        if not vis_exists:
            pytest.skip("vis-network.min.js not found — skipping CDN test")
        dummy_vis = {'nodes': [], 'edges': [], 'analysis': {}, 'route_count': 0}
        html = render_l3_map_html(dummy_vis)
        assert 'unpkg.com' not in html

    def test_api_routes_registered(self):
        assert '/api/l3-map/status' in self.web_py
        assert '/api/l3-map/open' in self.web_py

    def test_l3_topology_action_dispatched(self):
        assert "'l3_topology'" in self.web_py or '"l3_topology"' in self.web_py
        assert "'flow_map'" in self.web_py or '"flow_map"' in self.web_py
        assert "'advanced_l2_map'" in self.web_py or '"advanced_l2_map"' in self.web_py

    def test_adapters_uses_correct_log_param(self):
        """_collect_l3 closure must use log=log (not log_func=log)."""
        # Find the _collect_l3 function block
        idx = self.adapters_py.find('def _collect_l3')
        assert idx != -1, "_collect_l3 not found in adapters.py"
        block = self.adapters_py[idx:idx + 400]
        # The correct call uses log=log
        assert 'log=log' in block, "adapters._collect_l3 must use log=log"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
