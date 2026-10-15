"""Simulated TOPOLOGY_TEST_MATRIX rows (fixtures only — not live lab). Overlay stays uncollected."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.plugins import network_discovery as nd
from modules.routing_analyzer.graph_builder import L3TopologyGraphBuilder, _proto_edge_kind
from utils.discovery_graph import canonicalize_discovery_graph
from utils.discovery_schema import validate_discovery_export

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, 'tests', 'fixtures', 'discovery')


def _read(name: str) -> str:
    with open(os.path.join(FIXTURES, name), encoding='utf-8') as f:
        return f.read()


class TestTopologyMatrixL2(unittest.TestCase):
    def test_t_l2_01_ios_lldp_brief_two_switch(self):
        neighbors = nd._parse_cisco_lldp_brief(_read('ios_lldp_brief.txt'), 'CORE-IOS', None)
        hosts = {n['hostname'] for n in neighbors}
        self.assertIn('DIST-SW01', hosts)
        self.assertNotIn('(W)', hosts)
        self.assertNotIn('(R)', hosts)
        dist = next(n for n in neighbors if n['hostname'] == 'DIST-SW01')
        self.assertEqual(dist['local_port'], 'Gi0/1')
        self.assertEqual(dist['remote_port'], 'Gi0/2')
        self.assertEqual(len(neighbors), 1)

    def test_t_l2_03_one_sided_kept_not_invented(self):
        nodes = [
            {'id': 'A', 'ip': '10.0.0.1', 'is_scanned': True, 'scan_state': 'scanned'},
            {'id': 'B', 'ip': '10.0.0.2', 'is_scanned': False, 'scan_state': 'neighbor_only'},
        ]
        edges = [
            {'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2', 'protocol': 'LLDP'},
        ]
        _m, rewired, _r = canonicalize_discovery_graph(nodes, edges)
        self.assertEqual(len(rewired), 1)
        self.assertTrue(rewired[0].get('one_sided'))
        self.assertNotEqual((rewired[0].get('confidence') or '').lower(), 'high')

    def test_t_l2_04_one_sided_cdp_same_honesty(self):
        nodes = [
            {'id': 'ios1', 'ip': '10.0.0.1', 'is_scanned': True},
            {'id': 'ios2', 'ip': '10.0.0.2', 'is_scanned': False},
        ]
        edges = [
            {'from': 'ios1', 'to': 'ios2', 'f_port': 'Gi1/0/1', 't_port': 'Gi1/0/2', 'protocol': 'CDP'},
        ]
        _m, rewired, _r = canonicalize_discovery_graph(nodes, edges)
        self.assertEqual(len(rewired), 1)
        self.assertTrue(rewired[0].get('one_sided'))

    def test_t_l2_06_nxos_lldp_disabled_no_fake_neighbors(self):
        text = _read('nxos_lldp_disabled.txt')
        self.assertTrue(nd.cisco_neighbor_collection_disabled(text))
        self.assertEqual(nd._parse_cisco_lldp_detail(text, 'LEAF', None), [])

    def test_t_l2_07_junos_lldp_brief_only(self):
        neighbors = nd._parse_juniper_lldp_brief(_read('junos_lldp_brief.txt'), 'QFX-CORE', None)
        hosts = {n['hostname'] for n in neighbors}
        self.assertIn('DIST-QFX-01', hosts)
        self.assertIn('SPINE-QFX-02', hosts)

    def test_t_l2_08_nx_port_id_mac_uses_description(self):
        raw = nd._parse_cisco_lldp_detail(_read('nxos_lldp_mac_portid.txt'), 'LEAF', None)
        n = nd._finalize_neighbor(raw[0])
        self.assertEqual(n['hostname'], 'SPINE-NXOS-02')
        self.assertEqual(n['remote_port'], 'Eth2/11')
        self.assertNotEqual(n['remote_port'], '006b.f1be.deb0')

    def test_t_l2_09_system_name_not_advertised_uses_chassis(self):
        raw = nd._parse_cisco_lldp_detail(_read('nxos_lldp_not_advertised.txt'), 'LEAF', None)
        n = nd._finalize_neighbor(raw[0])
        self.assertEqual(n['hostname'], '0050.5689.12ab')
        self.assertTrue(n['hostname'])


class TestTopologyMatrixL3AndOps(unittest.TestCase):
    def test_t_l3_01_ospf_not_physical_link(self):
        self.assertEqual(_proto_edge_kind('OSPF'), 'ospf-neighbor')
        self.assertNotEqual(_proto_edge_kind('OSPF'), 'physical-link')
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology([
            {
                'destination': '10.1.0.0/24',
                'next_hop': '10.0.0.2',
                'protocol': 'OSPF',
                'route_type': 'Dynamic',
                'device_id': 'r1',
                'interface': 'Gi0/0',
            },
        ])
        for edge in result['edges']:
            self.assertEqual(edge.get('layer'), 'l3')
            self.assertTrue(edge.get('not_physical'))
            self.assertNotEqual(edge.get('edge_kind'), 'physical-link')

    def test_t_l3_02_bgp_not_spine_cable(self):
        self.assertEqual(_proto_edge_kind('BGP'), 'bgp-neighbor')
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology([
            {
                'destination': '192.0.2.0/24',
                'next_hop': '192.0.2.2',
                'protocol': 'BGP',
                'route_type': 'Dynamic',
                'device_id': 'rr',
                'interface': 'Lo0',
            },
        ])
        for edge in result['edges']:
            self.assertEqual(edge.get('edge_kind'), 'bgp-neighbor')
            self.assertTrue(edge.get('not_physical'))

    def test_t_l3_03_vrf_names_preserved_overlay_absent(self):
        builder = L3TopologyGraphBuilder()
        result = builder.build_topology([
            {
                'destination': '10.10.0.0/24',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
                'device_id': 'pe1',
                'interface': 'Vlan10',
                'vrf': 'MGMT',
            },
            {
                'destination': '10.20.0.0/24',
                'next_hop': '0.0.0.0',
                'protocol': 'Connected',
                'device_id': 'pe1',
                'interface': 'Vlan20',
                'vrf': 'PROD',
            },
            {
                'destination': '10.10.0.0/24',
                'next_hop': '10.0.0.2',
                'protocol': 'OSPF',
                'route_type': 'Dynamic',
                'device_id': 'pe1',
                'interface': 'Gi0/0',
                'vrf': 'MGMT',
            },
            {
                'destination': '10.20.0.0/24',
                'next_hop': '10.0.0.2',
                'protocol': 'OSPF',
                'route_type': 'Dynamic',
                'device_id': 'pe1',
                'interface': 'Gi0/1',
                'vrf': 'PROD',
            },
        ])
        vrfs = (result.get('analysis') or {}).get('vrf_distribution') or {}
        self.assertIn('MGMT', vrfs)
        self.assertIn('PROD', vrfs)
        self.assertEqual(
            (result.get('analysis') or {}).get('vrf_isolation'),
            'labeled_not_partitioned',
        )
        pairs = {(e.get('from'), e.get('to')) for e in result['edges']}
        self.assertNotIn(('10.10.0.0/24', '10.20.0.0/24'), pairs)
        self.assertNotIn(('10.20.0.0/24', '10.10.0.0/24'), pairs)
        ospf = [e for e in result['edges'] if e.get('from') == 'pe1' and e.get('to') == '10.0.0.2']
        self.assertEqual(len(ospf), 2)
        self.assertEqual({e.get('vrf') for e in ospf}, {'MGMT', 'PROD'})
        for edge in result['edges']:
            self.assertNotEqual(edge.get('edge_kind'), 'physical-link')
            self.assertTrue(edge.get('vrf'))

    def test_t_ov_01_overlay_collected_from_cli_not_hostname(self):
        ok, errors = validate_discovery_export({
            'devices': [{'id': 'a', 'hostname': 'a', 'scan_state': 'scanned'}],
            'links': [],
            'overlay_links': [{'from': 'a', 'to': 'b', 'layer': 'physical'}],
            'collection_status': 'complete',
            'overlay_collected': True,
        })
        self.assertFalse(ok)
        self.assertTrue(any('overlay' in e for e in errors))
        demo = nd.NetworkDiscoveryPlugin().execute(
            {'host': '10.0.0.1'},
            {'username': 'u', 'password': 'p'},
            {'seed_hosts': ['10.0.0.1'], 'demo_mode': True},
            {},
        )
        self.assertTrue(demo['data'].get('overlay_collected'))
        ov = demo['data'].get('overlay_links') or []
        self.assertTrue(ov)
        self.assertTrue(all(e.get('not_physical') for e in ov))
        self.assertTrue(all(e.get('layer') == 'overlay' for e in ov))

    def test_t_ops_03_missing_mid_path_does_not_hairpin(self):
        nodes = [
            {'id': 'A', 'ip': '10.0.0.1', 'is_scanned': True},
            {'id': 'C', 'ip': '10.0.0.3', 'is_scanned': True},
        ]
        edges = [
            {'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2', 'protocol': 'LLDP'},
            {'from': 'C', 'to': 'D', 'f_port': 'Gi0/1', 't_port': 'Gi0/2', 'protocol': 'LLDP'},
        ]
        _m, rewired, report = canonicalize_discovery_graph(nodes, edges)
        pairs = {(e.get('from'), e.get('to')) for e in rewired}
        self.assertNotIn(('A', 'C'), pairs)
        self.assertNotIn(('C', 'A'), pairs)
        # Path gap must stay visible: do not invent A↔C. Orphan count is informational.


class TestTopologyMatrixRemainingRows(unittest.TestCase):
    def test_t_l2_05_cdp_lldp_same_cable_one_identity(self):
        nodes = [
            {'id': 'A', 'ip': '10.0.0.1', 'is_scanned': True},
            {'id': 'B', 'ip': '10.0.0.2', 'is_scanned': True},
        ]
        edges = [
            {'from': 'A', 'to': 'B', 'f_port': 'Eth1/1', 't_port': 'Gi1/1', 'protocol': 'CDP'},
            {'from': 'B', 'to': 'A', 'f_port': 'Gi1/1', 't_port': 'Eth1/1', 'protocol': 'LLDP'},
        ]
        _m, rewired, _r = canonicalize_discovery_graph(nodes, edges)
        self.assertEqual(len(rewired), 1)
        src = {s.lower() for s in rewired[0].get('sources') or []}
        self.assertIn('cdp', src)
        self.assertIn('lldp', src)

    def test_t_l2_10_stp_blocked_distinct_from_forwarding(self):
        from modules.stp_swiss_runner import _parse_blocked_ports
        nx = open(os.path.join(ROOT, 'tests', 'fixtures', 'stp', 'cisco_nxos_stp_blocked.txt'), encoding='utf-8').read()
        rows = _parse_blocked_ports(nx, 'N9K-LEAF-01')
        self.assertTrue(rows)
        self.assertTrue(all(r.get('link_type') == 'stp-blocked' for r in rows))
        self.assertNotEqual(rows[0].get('link_type'), 'forwarding')

    def test_t_l2_12_duplicate_hostnames_disambiguated(self):
        nodes = [
            {'id': 'EDGE-01', 'ip': '10.0.0.1', 'serial': 'SN-A', 'is_scanned': True},
            {'id': 'EDGE-01', 'ip': '10.0.0.9', 'serial': 'SN-B', 'is_scanned': True},
        ]
        merged, _e, report = canonicalize_discovery_graph(nodes, [])
        self.assertTrue(report.get('duplicate_hostnames') or any(n.get('identity_conflict') for n in merged))
        ids = [n.get('id') for n in merged]
        self.assertEqual(len(set(ids)), len(ids))

    def test_t_ops_01_stale_badge_copy_in_shell(self):
        shell = open(os.path.join(ROOT, 'utils', 'topo_map_shell.py'), encoding='utf-8').read()
        self.assertIn('NST_STALE_HOURS', shell)
        self.assertIn('not current truth', shell)

    def test_t_ui_01_vis_container_id_mynetwork(self):
        topo = open(os.path.join(ROOT, 'utils', 'topo_map_shell.py'), encoding='utf-8').read()
        disc = open(os.path.join(ROOT, 'utils', 'discovery_map_shell.py'), encoding='utf-8').read()
        self.assertIn('id="mynetwork"', topo)
        self.assertIn('id="mynetwork"', disc)
        self.assertNotIn('id="network-canvas"', topo)


if __name__ == '__main__':
    unittest.main()
