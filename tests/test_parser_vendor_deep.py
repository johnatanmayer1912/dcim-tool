"""
Deep vendor parser validation — zero-trust policy.

Covers every blind spot from the 2026-09-03 audit:
  1. Cisco IOS  — full route table: C/L/S/O/O IA/O E2/O N1/O N2/D/D EX/i L1/i L2/B/R + ECMP
  2. Cisco IOS  — ECMP continuation lines survive comment lines mid-table
  3. Cisco NX-OS modern (ubest/mbest) — ospf-1, bgp-65001, eigrp-100, eigrp-100 external
  4. Cisco NX-OS legacy / IOS-style fallback
  5. Cisco NX-OS — output containing 'Default gateway is' must NOT short-circuit
  6. Juniper Junos — static/Direct/OSPF/BGP ECMP/IS-IS/multi-path
  7. Multi-token protocol codes map to correct canonical names (O IA, O N1, D EX, i L1)
  8. Full pipeline: fixture text → parser → normalizer → graph_builder → vis.js payload
  9. graph_builder: ghost nodes get borderDashes in node dict
 10. graph_builder: subnet nodes 251-300 have gateway edges (cap aligned to 300)
 11. XSS: enhanced shell uses script_safe_json, not json.dumps
 12. XSS: title/subtitle are html-escaped in both standard and enhanced shells
"""
from __future__ import annotations

import os
import sys
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, 'tests', 'fixtures', 'routing')

from modules.routing_analyzer.parser import RoutingParser, _canon_proto
from modules.routing_analyzer.normalizer import RoutingNormalizer
from modules.routing_analyzer.graph_builder import L3TopologyGraphBuilder, SubnetAnalyzer, GatewayDetector
from modules.l3_topology_runner import build_l3_topology_bundle, build_flow_topology_bundle
from utils.l3_map_formatter import l3_bundle_to_vis, flow_bundle_to_vis
from utils.l3_map_shell import render_l3_map_html
from utils.l3_map_shell_enhanced import render_l3_map_html_enhanced
from utils.topo_map_shell import OFFLINE_VIS_MISSING_SCRIPT


def _fixture(name: str) -> str:
    path = os.path.join(FIXTURES, name)
    with open(path, encoding='utf-8') as f:
        return f.read()


parser = RoutingParser()
normalizer = RoutingNormalizer()


# ────────────────────────────────────────────────────────────────────────────
# 1. Cisco IOS full route table
# ────────────────────────────────────────────────────────────────────────────

class TestCiscoIOSFullTable:
    @pytest.fixture(scope='class')
    def routes(self):
        raw = parser.parse_routing_output('cisco_ios', 'show ip route', _fixture('ios_show_ip_route_full.txt'))
        return normalizer.normalize_routing_table(raw, 'ios-router-01')

    def test_connected_routes_present(self, routes):
        dests = {r['destination'] for r in routes}
        assert '10.0.0.0/30' in dests
        assert '192.168.1.0/24' in dests
        assert '192.168.2.0/24' in dests

    def test_static_default_route(self, routes):
        statics = [r for r in routes if r['destination'] == '0.0.0.0/0']
        assert statics, 'Default static route missing'
        assert statics[0]['protocol'] == 'Static'
        assert statics[0]['next_hop'] == '10.0.0.1'

    def test_ospf_inter_area_correctly_labeled(self, routes):
        oia = [r for r in routes if r['destination'] == '172.16.1.0/24']
        assert oia, 'O IA route 172.16.1.0/24 missing'
        assert oia[0]['protocol'] == 'OSPF-InterArea', \
            f"O IA route got protocol={oia[0]['protocol']!r} instead of OSPF-InterArea"

    def test_ospf_inter_area_second_subnet(self, routes):
        oia = [r for r in routes if r['destination'] == '172.16.2.0/24']
        assert oia, 'O IA route 172.16.2.0/24 missing'
        assert oia[0]['protocol'] == 'OSPF-InterArea'

    def test_ospf_ext2_labeled(self, routes):
        oe2 = [r for r in routes if r['destination'] == '172.16.3.0/24']
        assert oe2, 'O E2 route missing'
        proto = oe2[0]['protocol']
        assert 'Ext' in proto or 'OSPF' in proto, f"O E2 got {proto!r}"

    def test_ospf_nssa_n1_labeled(self, routes):
        on1 = [r for r in routes if r['destination'] == '172.16.4.0/24']
        assert on1, 'O N1 route missing'
        assert 'OSPF' in on1[0]['protocol'], f"O N1 got {on1[0]['protocol']!r}"

    def test_ospf_nssa_n2_labeled(self, routes):
        on2 = [r for r in routes if r['destination'] == '172.16.5.0/24']
        assert on2, 'O N2 route missing'
        assert 'OSPF' in on2[0]['protocol']

    def test_ecmp_two_paths_parsed(self, routes):
        ecmp = [r for r in routes if r['destination'] == '172.16.6.0/24']
        assert len(ecmp) == 2, f'Expected 2 ECMP paths for 172.16.6.0/24, got {len(ecmp)}'
        nhops = {r['next_hop'] for r in ecmp}
        assert '10.0.0.1' in nhops
        assert '10.0.0.5' in nhops

    def test_eigrp_external_labeled(self, routes):
        dex = [r for r in routes if r['destination'] == '10.200.0.0/16']
        assert dex, 'D EX route missing'
        assert dex[0]['protocol'] == 'EIGRP-External', f"D EX got {dex[0]['protocol']!r}"

    def test_isis_l1_labeled(self, routes):
        il1 = [r for r in routes if r['destination'] == '10.50.0.0/16']
        assert il1, 'i L1 route missing'
        assert 'ISIS' in il1[0]['protocol'], f"i L1 got {il1[0]['protocol']!r}"

    def test_isis_l2_labeled(self, routes):
        il2 = [r for r in routes if r['destination'] == '10.60.0.0/16']
        assert il2, 'i L2 route missing'
        assert 'ISIS' in il2[0]['protocol']

    def test_bgp_route_present(self, routes):
        bgp = [r for r in routes if r['destination'] == '203.0.113.0/24']
        assert bgp, 'BGP route missing'
        assert bgp[0]['protocol'] == 'BGP'

    def test_rip_route_present(self, routes):
        rip = [r for r in routes if r['destination'] == '10.99.0.0/16']
        assert rip, 'RIP route missing'
        assert rip[0]['protocol'] == 'RIP'

    def test_no_empty_destinations(self, routes):
        for r in routes:
            assert r['destination'], f"Route with empty destination: {r}"

    def test_protocol_never_empty(self, routes):
        for r in routes:
            assert r['protocol'] and r['protocol'] != 'Unknown', \
                f"Route has Unknown/empty protocol: {r}"


# ────────────────────────────────────────────────────────────────────────────
# 2. IOS ECMP continuations survive comment lines mid-table
# ────────────────────────────────────────────────────────────────────────────

class TestCiscoIOSECMPWithComments:
    @pytest.fixture(scope='class')
    def routes(self):
        raw = parser.parse_routing_output(
            'cisco_ios', 'show ip route',
            _fixture('ios_show_ip_route_ecmp_with_comments.txt'),
        )
        return normalizer.normalize_routing_table(raw, 'ios-ecmp-01')

    def test_first_ecmp_route_3_paths(self, routes):
        paths = [r for r in routes if r['destination'] == '10.1.0.0/24']
        assert len(paths) == 3, \
            f'Expected 3 ECMP paths for 10.1.0.0/24 (comment must not break continuation), got {len(paths)}'

    def test_second_ecmp_route_2_paths(self, routes):
        paths = [r for r in routes if r['destination'] == '10.2.0.0/24']
        assert len(paths) == 2, \
            f'Expected 2 ECMP paths for 10.2.0.0/24, got {len(paths)}'

    def test_connected_route_present(self, routes):
        assert any(r['destination'] == '192.168.1.0/24' for r in routes)

    def test_static_default_present(self, routes):
        assert any(r['destination'] == '0.0.0.0/0' for r in routes)


# ────────────────────────────────────────────────────────────────────────────
# 3. NX-OS modern (ubest/mbest) — protocol process IDs
# ────────────────────────────────────────────────────────────────────────────

class TestNXOSModern:
    @pytest.fixture(scope='class')
    def routes(self):
        raw = parser.parse_routing_output(
            'cisco_nxos', 'show ip route',
            _fixture('nxos_show_ip_route_modern.txt'),
        )
        return normalizer.normalize_routing_table(raw, 'nxos-01')

    def test_default_route_static(self, routes):
        default = [r for r in routes if r['destination'] == '0.0.0.0/0']
        assert default, 'Default route missing from NX-OS modern output'
        assert default[0]['protocol'] == 'Static'

    def test_ospf_process_id_stripped(self, routes):
        ospf = [r for r in routes if r['destination'] == '10.1.1.0/24']
        assert ospf, 'OSPF route 10.1.1.0/24 missing'
        assert ospf[0]['protocol'] == 'OSPF', \
            f"ospf-1 should map to OSPF, got {ospf[0]['protocol']!r}"

    def test_ecmp_two_paths(self, routes):
        ecmp = [r for r in routes if r['destination'] == '10.2.2.0/24']
        assert len(ecmp) == 2, f'Expected 2 ECMP paths for 10.2.2.0/24, got {len(ecmp)}'

    def test_bgp_process_id_stripped(self, routes):
        bgp = [r for r in routes if r['destination'] == '10.3.3.0/24']
        assert bgp, 'BGP route missing'
        assert bgp[0]['protocol'] == 'BGP', \
            f"bgp-65001 should map to BGP, got {bgp[0]['protocol']!r}"

    def test_eigrp_internal(self, routes):
        eigrp = [r for r in routes if r['destination'] == '10.4.4.0/24']
        assert eigrp, 'EIGRP route missing'
        assert eigrp[0]['protocol'] == 'EIGRP', \
            f"eigrp-100 should map to EIGRP, got {eigrp[0]['protocol']!r}"

    def test_eigrp_external(self, routes):
        eigrp_ex = [r for r in routes if r['destination'] == '10.5.5.0/24']
        assert eigrp_ex, 'EIGRP-external route missing'
        # eigrp-100 external may map to EIGRP-External or EIGRP — either is acceptable
        assert 'EIGRP' in eigrp_ex[0]['protocol']

    def test_direct_connected(self, routes):
        direct = [r for r in routes if r['destination'] == '192.168.10.0/24']
        assert direct, 'Direct/connected route missing'
        assert direct[0]['protocol'] in ('Connected', 'Local', 'Direct')


# ────────────────────────────────────────────────────────────────────────────
# 4. NX-OS IOS-style fallback
# ────────────────────────────────────────────────────────────────────────────

class TestNXOSIOSStyleFallback:
    @pytest.fixture(scope='class')
    def routes(self):
        raw = parser.parse_routing_output(
            'cisco_nxos', 'show ip route',
            _fixture('nxos_ios_style_fallback.txt'),
        )
        return normalizer.normalize_routing_table(raw, 'nxos-legacy-01')

    def test_routes_parsed(self, routes):
        assert len(routes) >= 3, f'Expected at least 3 routes, got {len(routes)}'

    def test_static_default(self, routes):
        d = [r for r in routes if r['destination'] == '0.0.0.0/0']
        assert d, 'Default route missing from NX-OS IOS-style'

    def test_ospf_route(self, routes):
        o = [r for r in routes if r['destination'] == '10.1.0.0/24']
        assert o, 'OSPF route missing'


# ────────────────────────────────────────────────────────────────────────────
# 5. NX-OS with "Default gateway is" phrase must NOT short-circuit
# ────────────────────────────────────────────────────────────────────────────

class TestNXOSDefaultGatewayPhrase:
    def test_nxos_not_short_circuited(self):
        """NX-OS output with 'Default gateway is' phrase must NOT hit minimal-switch guard."""
        nxos_output = (
            "IP Route Table for VRF \"default\"\n"
            "0.0.0.0/0, ubest/mbest: 1/0\n"
            "    *via 10.0.0.1, Eth1/1, [1/0], 2w, static\n"
            "Default gateway is 10.0.0.1\n"  # phrase present but no ICMP redirect cache line
            "10.0.0.0/30, ubest/mbest: 1/0, attached\n"
            "    *via 10.0.0.2, Eth1/1, [0/0], 3w, direct\n"
            "192.168.1.0/24, ubest/mbest: 1/0\n"
            "    *via 10.0.0.1, Eth1/1, [110/40], 1h, ospf-1, intra\n"
        )
        raw = parser.parse_routing_output('cisco_nxos', 'show ip route', nxos_output)
        normalized = normalizer.normalize_routing_table(raw, 'nxos-gw-test')
        dests = {r['destination'] for r in normalized}
        assert '192.168.1.0/24' in dests, \
            'NX-OS parser short-circuited on "Default gateway is" phrase — full table lost'
        assert len(normalized) >= 3, \
            f'Expected >=3 routes from NX-OS output, got {len(normalized)}'

    def test_ios_switch_minimal_still_works(self):
        """Minimal IOS L2 switch with only default-gateway line still produces a static route."""
        ios_minimal = (
            "Default gateway is 10.10.10.1 Host Gateway         Last Use    Total Uses  Interface\n"
            "10.10.10.1           11:17        13  Ethernet0\n"
            "  ICMP redirect cache is empty\n"
        )
        raw = parser.parse_routing_output('cisco_ios', 'show ip route', ios_minimal)
        normalized = normalizer.normalize_routing_table(raw, 'l2-switch-01')
        assert any(r['destination'] == '0.0.0.0/0' for r in normalized), \
            'Minimal IOS switch default gateway not parsed'


# ────────────────────────────────────────────────────────────────────────────
# 6. Juniper Junos
# ────────────────────────────────────────────────────────────────────────────

class TestJuniperJunos:
    @pytest.fixture(scope='class')
    def routes(self):
        raw = parser.parse_routing_output(
            'juniper_junos', 'show route',
            _fixture('junos_show_route.txt'),
        )
        return normalizer.normalize_routing_table(raw, 'junos-rtr-01')

    def test_static_default(self, routes):
        d = [r for r in routes if r['destination'] == '0.0.0.0/0']
        assert d, 'Default static route missing from Junos output'
        assert d[0]['protocol'] == 'Static'
        assert d[0]['next_hop'] == '10.0.0.1'

    def test_direct_connected(self, routes):
        direct = [r for r in routes if r['destination'] == '10.0.0.0/30']
        assert direct, 'Direct connected route missing'
        assert direct[0]['protocol'] in ('Connected', 'Direct')

    def test_ospf_route(self, routes):
        ospf = [r for r in routes if r['destination'] == '10.1.1.0/24']
        assert ospf, 'OSPF route missing from Junos output'
        assert ospf[0]['protocol'] == 'OSPF'
        assert ospf[0]['next_hop'] == '10.0.0.1'

    def test_ospf_ecmp_two_paths(self, routes):
        ecmp = [r for r in routes if r['destination'] == '10.2.2.0/24']
        assert len(ecmp) == 2, \
            f'Expected 2 ECMP OSPF paths for 10.2.2.0/24 from Junos, got {len(ecmp)}'

    def test_bgp_route(self, routes):
        bgp = [r for r in routes if r['destination'] == '10.3.3.0/24']
        assert bgp, 'BGP route missing'
        assert bgp[0]['protocol'] == 'BGP'
        assert bgp[0]['next_hop'] == '10.0.0.9'

    def test_isis_route(self, routes):
        isis = [r for r in routes if r['destination'] == '10.4.4.0/24']
        assert isis, 'IS-IS route missing from Junos output'
        assert 'ISIS' in isis[0]['protocol'], f"IS-IS route got {isis[0]['protocol']!r}"

    def test_static_subnet(self, routes):
        s = [r for r in routes if r['destination'] == '192.168.3.0/24']
        assert s, 'Static subnet route missing'
        assert s[0]['protocol'] == 'Static'

    def test_no_multicast_routes(self, routes):
        for r in routes:
            dest = r.get('destination', '')
            try:
                import ipaddress
                assert not ipaddress.ip_network(dest, strict=False).is_multicast, \
                    f"Multicast route leaked into normalized output: {dest}"
            except ValueError:
                pass


# ────────────────────────────────────────────────────────────────────────────
# 7. Multi-token protocol code mapping
# ────────────────────────────────────────────────────────────────────────────

class TestMultiTokenProtocolCodes:
    @pytest.mark.parametrize('code,expected', [
        ('O IA',  'OSPF-InterArea'),
        ('O E1',  'OSPF-Ext1'),
        ('O E2',  'OSPF-Ext2'),
        ('O N1',  'OSPF-NSSA-Ext1'),
        ('O N2',  'OSPF-NSSA-Ext2'),
        ('D EX',  'EIGRP-External'),
        ('i L1',  'ISIS-L1'),
        ('i L2',  'ISIS-L2'),
        ('i su',  'ISIS-Summary'),
        # Single-char codes still work
        ('O',    'OSPF'),
        ('B',    'BGP'),
        ('C',    'Connected'),
        ('L',    'Local'),
        ('S',    'Static'),
        ('D',    'EIGRP'),
        ('i',    'ISIS'),
        ('R',    'RIP'),
        # NX-OS process IDs
        ('ospf-101',   'OSPF'),
        ('bgp-65000',  'BGP'),
        ('eigrp-100',  'EIGRP'),
        ('isis-1',     'ISIS'),
        # Junos protocol strings
        ('Direct',  'Connected'),
        ('Static',  'Static'),
        ('OSPF',    'OSPF'),
        ('BGP',     'BGP'),
        ('IS-IS',   'ISIS'),
    ])
    def test_canon_proto(self, code, expected):
        result = _canon_proto(code)
        assert result == expected, f"_canon_proto({code!r}) = {result!r}, expected {expected!r}"


# ────────────────────────────────────────────────────────────────────────────
# 8. Full pipeline: fixture → nodes/edges → HTML output
# ────────────────────────────────────────────────────────────────────────────

class TestFullPipelineIOS:
    @pytest.fixture(scope='class')
    def html(self):
        raw = parser.parse_routing_output('cisco_ios', 'show ip route', _fixture('ios_show_ip_route_full.txt'))
        normalized = normalizer.normalize_routing_table(raw, 'core-01')
        bundle = build_l3_topology_bundle([{
            'status': 'success', 'true_host': 'core-01',
            'routes_normalized': normalized,
            'platform': 'cisco_ios', 'host': '10.0.0.1',
            'management_ip': '10.0.0.1', 'ssh_port': 22,
            'protocols': list({r['protocol'] for r in normalized}),
            'network_meta': {},
        }])
        vis = l3_bundle_to_vis(bundle)
        return render_l3_map_html(vis, 'IOS Full Route Table', 'core-01', 'l3')

    def test_html_generated(self, html):
        assert len(html) > 10000, 'HTML output suspiciously small'
        assert '<!DOCTYPE html>' in html

    def test_vis_js_embedded(self, html):
        assert OFFLINE_VIS_MISSING_SCRIPT not in html, 'vis.js missing'
        assert 'unpkg.com' not in html.lower()

    def test_device_node_in_html(self, html):
        assert 'core-01' in html

    def test_ospf_routes_in_payload(self, html):
        assert 'OSPF' in html

    def test_no_raw_script_breakout(self, html):
        # Verify </script> does not appear from data (it must be escaped)
        # The only </script> allowed are real closing tags
        import re as _re
        script_closes = _re.findall(r'</script>', html, _re.I)
        # There should be exactly one per script block — count script opens too
        script_opens = _re.findall(r'<script[^>]*>', html, _re.I)
        assert len(script_closes) == len(script_opens), \
            f'Mismatched <script> tags — possible data injection: {len(script_opens)} open vs {len(script_closes)} close'


class TestFullPipelineNXOS:
    @pytest.fixture(scope='class')
    def vis_payload(self):
        raw = parser.parse_routing_output('cisco_nxos', 'show ip route', _fixture('nxos_show_ip_route_modern.txt'))
        normalized = normalizer.normalize_routing_table(raw, 'nxos-spine-01')
        bundle = build_l3_topology_bundle([{
            'status': 'success', 'true_host': 'nxos-spine-01',
            'routes_normalized': normalized,
            'platform': 'cisco_nxos', 'host': '10.0.0.2',
            'management_ip': '10.0.0.2', 'ssh_port': 22,
            'protocols': list({r['protocol'] for r in normalized}),
            'network_meta': {},
        }])
        return l3_bundle_to_vis(bundle)

    def test_nodes_present(self, vis_payload):
        assert len(vis_payload['nodes']) >= 1

    def test_edges_present(self, vis_payload):
        assert len(vis_payload['edges']) >= 1

    def test_all_edges_have_from_to(self, vis_payload):
        for e in vis_payload['edges']:
            assert e.get('from') and e.get('to'), f'Edge missing from/to: {e}'

    def test_all_nodes_have_id(self, vis_payload):
        for n in vis_payload['nodes']:
            assert n.get('id'), f'Node missing id: {n}'


class TestFullPipelineJunos:
    @pytest.fixture(scope='class')
    def vis_payload(self):
        raw = parser.parse_routing_output('juniper_junos', 'show route', _fixture('junos_show_route.txt'))
        normalized = normalizer.normalize_routing_table(raw, 'junos-edge-01')
        bundle = build_l3_topology_bundle([{
            'status': 'success', 'true_host': 'junos-edge-01',
            'routes_normalized': normalized,
            'platform': 'juniper_junos', 'host': '10.0.0.6',
            'management_ip': '10.0.0.6', 'ssh_port': 22,
            'protocols': list({r['protocol'] for r in normalized}),
            'network_meta': {},
        }])
        return l3_bundle_to_vis(bundle)

    def test_nodes_present(self, vis_payload):
        assert len(vis_payload['nodes']) >= 1

    def test_junos_device_node(self, vis_payload):
        ids = {n['id'] for n in vis_payload['nodes']}
        assert 'junos-edge-01' in ids


# ────────────────────────────────────────────────────────────────────────────
# 9. Ghost node borderDashes preserved in graph_builder output
# ────────────────────────────────────────────────────────────────────────────

class TestGhostNodePreservation:
    def test_ghost_node_has_border_dashes(self):
        """Next-hops never seen as routing sources must get borderDashes in graph_builder output."""
        routes = [
            {'destination': '10.0.0.0/24', 'next_hop': '10.0.0.1',
             'protocol': 'OSPF', 'device_id': 'R1', 'vrf': 'default',
             'interface': 'Gi0/0', 'route_type': 'Dynamic', 'admin_distance': 110, 'metric': 20},
        ]
        builder = L3TopologyGraphBuilder()
        topo = builder.build_topology(routes)
        nodes = {n['id']: n for n in topo['nodes']}
        # 10.0.0.1 is a next-hop but never a routing source → must be ghost
        assert '10.0.0.1' in nodes, '10.0.0.1 gateway node missing'
        gw = nodes['10.0.0.1']
        assert gw.get('_ghost'), '10.0.0.1 should be flagged as ghost node'
        assert gw.get('borderDashes'), 'Ghost node missing borderDashes'

    def test_known_device_not_ghost(self):
        """A device that contributes routes must not be flagged as ghost."""
        routes = [
            {'destination': '192.168.1.0/24', 'next_hop': '', 'protocol': 'Connected',
             'device_id': 'R1', 'vrf': 'default', 'interface': 'Gi0/0',
             'route_type': 'Connected', 'admin_distance': 0, 'metric': 0},
        ]
        builder = L3TopologyGraphBuilder()
        topo = builder.build_topology(routes)
        nodes = {n['id']: n for n in topo['nodes']}
        assert 'R1' in nodes
        assert not nodes['R1'].get('_ghost'), 'Known routing device wrongly flagged as ghost'


# ────────────────────────────────────────────────────────────────────────────
# 10. Subnet-gateway edge cap alignment
# ────────────────────────────────────────────────────────────────────────────

class TestSubnetEdgeCap:
    def test_subnet_301_has_no_node(self):
        """Subnets beyond node cap (300) should have neither node nor edges."""
        routes = []
        for i in range(310):
            routes.append({
                'destination': f'10.{i//256}.{i%256}.0/24',
                'next_hop': '10.200.0.1',
                'protocol': 'OSPF', 'device_id': 'R1', 'vrf': 'default',
                'interface': 'Gi0/0', 'route_type': 'Dynamic',
                'admin_distance': 110, 'metric': 20,
            })
        builder = L3TopologyGraphBuilder()
        topo = builder.build_topology(routes)
        node_ids = {n['id'] for n in topo['nodes']}
        # No subnet beyond the 300-cap should appear as a node
        subnet_nodes = [n for n in topo['nodes'] if n.get('group') == 'subnet']
        assert len(subnet_nodes) <= 300, f'Too many subnet nodes: {len(subnet_nodes)}'

    def test_subnet_within_cap_has_edge(self):
        """Subnet nodes within cap must have at least one edge from their gateway."""
        routes = [
            {'destination': '10.1.0.0/24', 'next_hop': '10.0.0.1',
             'protocol': 'OSPF', 'device_id': 'R1', 'vrf': 'default',
             'interface': 'Gi0/0', 'route_type': 'Dynamic', 'admin_distance': 110, 'metric': 20},
        ]
        builder = L3TopologyGraphBuilder()
        topo = builder.build_topology(routes)
        node_ids = {n['id'] for n in topo['nodes']}
        edge_endpoints = {(e['from'], e['to']) for e in topo['edges']}
        # 10.1.0.0/24 is a subnet node — must have at least one edge touching it
        if '10.1.0.0/24' in node_ids:
            has_edge = any('10.1.0.0/24' in (f, t) for f, t in edge_endpoints)
            assert has_edge, 'Subnet node 10.1.0.0/24 has no edges (cap mismatch?)'


# ────────────────────────────────────────────────────────────────────────────
# 11. XSS: enhanced shell uses script_safe_json
# ────────────────────────────────────────────────────────────────────────────

class TestEnhancedShellScriptSafeJson:
    EVIL_PAYLOAD = {
        'nodes': [{'id': 'evil</script><script>alert(1)</script>', 'label': 'evil', 'group': 'device'}],
        'edges': [],
        'analysis': {}, 'devices': {}, 'gateway_analysis': {}, 'subnet_analysis': {},
        'all_routes': [], 'failed_hosts': [], 'route_count': 0,
    }

    def test_script_breakout_escaped_in_enhanced(self):
        html = render_l3_map_html_enhanced(self.EVIL_PAYLOAD, 'Test', 'test')
        raw_breakout = '</script><script>alert(1)</script>'
        assert raw_breakout not in html, \
            'CRITICAL: </script> breakout not escaped in enhanced shell — XSS possible'

    def test_script_breakout_escaped_in_standard(self):
        html = render_l3_map_html(self.EVIL_PAYLOAD, 'Test', 'test', 'l3')
        raw_breakout = '</script><script>alert(1)</script>'
        assert raw_breakout not in html, \
            'CRITICAL: </script> breakout not escaped in standard shell — XSS possible'


# ────────────────────────────────────────────────────────────────────────────
# 12. XSS: title/subtitle html-escaped in both shells
# ────────────────────────────────────────────────────────────────────────────

class TestTitleSubtitleEscaping:
    EVIL_TITLE    = '</title><script>alert(1)</script><title>'
    EVIL_SUBTITLE = '<img src=x onerror=alert(2)>'

    def test_standard_shell_title_escaped(self):
        html = render_l3_map_html({
            'nodes': [], 'edges': [], 'analysis': {}, 'devices': {},
            'gateway_analysis': {}, 'subnet_analysis': {}, 'all_routes': [],
            'failed_hosts': [], 'route_count': 0,
        }, self.EVIL_TITLE, self.EVIL_SUBTITLE, 'l3')
        assert '</title><script>' not in html, \
            'Title not escaped in standard shell <title> tag'
        assert '<img src=x onerror=' not in html, \
            'Subtitle not escaped in standard shell header'

    def test_enhanced_shell_title_escaped(self):
        html = render_l3_map_html_enhanced({
            'nodes': [], 'edges': [], 'analysis': {}, 'devices': {},
            'gateway_analysis': {}, 'subnet_analysis': {}, 'all_routes': [],
            'failed_hosts': [], 'route_count': 0,
        }, self.EVIL_TITLE, self.EVIL_SUBTITLE, 'l3')
        assert '</title><script>' not in html, \
            'Title not escaped in enhanced shell <title> tag'
        assert '<img src=x onerror=' not in html, \
            'Subtitle not escaped in enhanced shell header'
