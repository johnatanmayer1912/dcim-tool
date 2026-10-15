"""Reality-loop device-fidelity — fixture/replay only.

Device-like samples for legacy IOS 12.x wrap, Local Interface LLDP,
NX-OS 'mac ' chassis prefix, Junos 11.x brief without Parent Interface.
Not live SSH. Not enterprise clearance.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.plugins import network_discovery as nd
from utils.discovery_graph import canonicalize_discovery_graph
from utils.discovery_map_formatter import generate_discovery_html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'discovery')


def _read(name: str) -> str:
    with open(os.path.join(FIX, name), encoding='utf-8') as f:
        return f.read()


def _no_placeholder_ports(neighs):
    for n in neighs:
        for key in ('local_port', 'remote_port'):
            val = (n.get(key) or '')
            assert val.lower() not in ('unknown', 'n/a', 'n\\a', 'mac'), (key, val)


class TestSpacedCdpAbbreviationNormalize(unittest.TestCase):
    def test_gig_space_matches_gigabitethernet(self):
        self.assertEqual(nd._normalize_interface_name('Gig 1/0/1'), 'Gi1/0/1')
        self.assertEqual(
            nd._normalize_interface_name('GigabitEthernet1/0/1'), 'Gi1/0/1',
        )
        self.assertEqual(nd._normalize_interface_name('Fas 0/24'), 'Fa0/24')
        self.assertEqual(nd._normalize_interface_name('FastEthernet0/24'), 'Fa0/24')
        self.assertEqual(nd._normalize_interface_name('Ten 1/1/1'), 'Te1/1/1')
        self.assertEqual(nd._normalize_interface_name('Ethernet1/2'), 'Eth1/2')

    def test_does_not_invent_from_empty_or_n_a(self):
        self.assertEqual(nd._normalize_interface_name(''), '')
        self.assertEqual(nd._normalize_interface_name('n/a'), '')
        self.assertEqual(nd._normalize_interface_name('unknown'), '')

    def test_brief_and_detail_same_adjacency_after_finalize(self):
        brief = nd._parse_cisco_cdp_brief(_read('ios_cdp_brief.txt'), 'CORE', None)
        detail = nd._parse_cisco_cdp_detail(_read('ios_cdp_detail.txt'), 'CORE', None)
        b = nd._finalize_neighbor(dict(next(n for n in brief if 'DIST-SW01' in n['hostname'])))
        d = nd._finalize_neighbor(dict(next(n for n in detail if 'DIST-SW01' in n['hostname'])))
        self.assertEqual(b['local_port'], d['local_port'])
        self.assertEqual(b['remote_port'], d['remote_port'])
        self.assertEqual(b['local_port'], 'Gi1/0/1')


class TestIos12WrappedCdpDeviceId(unittest.TestCase):
    def test_wrapped_device_id_is_neighbor_not_invented_port(self):
        ns = nd._parse_cisco_cdp_brief(
            _read('legacy_ios12_cdp_brief_wrapped_device_id.txt'), 'EDGE', None,
        )
        hosts = {n['hostname'] for n in ns}
        self.assertIn('core-dist-sw01.corp.example.invalid', hosts)
        self.assertIn('access-2960-floor2.lab.invalid', hosts)
        core = next(n for n in ns if n['hostname'].startswith('core-dist'))
        self.assertEqual(core['local_port'], 'Gig 1/0/1')
        self.assertEqual(core['remote_port'], 'Gig 1/0/48')
        fin = nd._finalize_neighbor(dict(core))
        self.assertTrue(fin['edge_eligible'])
        self.assertEqual(fin['local_port'], 'Gi1/0/1')
        self.assertEqual(fin['remote_port'], 'Gi1/0/48')
        _no_placeholder_ports(ns)

    def test_hostname_only_without_continuation_is_not_a_neighbor(self):
        orphan = (
            'Device ID        Local Intrfce     Holdtme    Capability  Platform  Port ID\n'
            'lonely-host.invalid\n'
        )
        ns = nd._parse_cisco_cdp_brief(orphan, 'EDGE', None)
        self.assertEqual(ns, [])


class TestIos12LldpLocalInterface(unittest.TestCase):
    def test_local_interface_keyword_is_local_port(self):
        ns = nd._parse_cisco_lldp_detail(
            _read('legacy_ios12_lldp_detail_local_interface.txt'), 'EDGE', None,
        )
        self.assertEqual(len(ns), 1)
        self.assertFalse(ns[0].get('incomplete'))
        self.assertEqual(ns[0]['local_port'], 'GigabitEthernet1/0/1')
        self.assertEqual(ns[0]['hostname'], 'DIST-SW01')
        fin = nd._finalize_neighbor(dict(ns[0]))
        self.assertEqual(fin['local_port'], 'Gi1/0/1')
        self.assertEqual(fin['remote_port'], 'Gi0/1')
        self.assertTrue(fin['edge_eligible'])


class TestNxosMacPrefixAndLocalPortId(unittest.TestCase):
    def test_mac_prefix_not_used_as_hostname(self):
        ns = nd._parse_cisco_lldp_detail(
            _read('legacy_nxos_lldp_detail_mac_prefix.txt'), 'LEAF', None,
        )
        self.assertEqual(len(ns), 1)
        fin = nd._finalize_neighbor(dict(ns[0]))
        self.assertNotEqual((fin['hostname'] or '').lower(), 'mac')
        self.assertEqual(fin['hostname'], '00.1a.2b.3c.4d.5e')
        self.assertEqual(fin['local_port'], 'Eth1/1')
        self.assertEqual(fin['remote_port'], 'Eth1/48')
        self.assertNotIn('mac', (fin.get('remote_port') or '').lower())

    def test_local_port_id_is_not_stolen_as_remote_port(self):
        ns = nd._parse_cisco_lldp_detail(
            _read('legacy_nxos_lldp_detail_mac_prefix.txt'), 'LEAF', None,
        )
        self.assertEqual(ns[0]['local_port'], 'Eth1/1')
        self.assertNotEqual(ns[0]['local_port'], ns[0]['remote_port'])


class TestJunos11BriefNoParent(unittest.TestCase):
    def test_chassis_id_column_is_not_treated_as_parent(self):
        ns = nd._parse_juniper_lldp_brief(
            _read('legacy_junos11_lldp_brief_no_parent.txt'), 'EDGE', None,
        )
        hosts = {n['hostname'] for n in ns}
        self.assertIn('dist-ex4200-01', hosts)
        self.assertIn('spine-qfx-02', hosts)
        dist = next(n for n in ns if n['hostname'] == 'dist-ex4200-01')
        self.assertEqual(dist['local_port'], 'ge-0/0/0')
        self.assertEqual(dist['remote_port'], 'ge-0/0/1')
        self.assertNotEqual(dist['remote_port'], '507')
        self.assertNotEqual(dist['hostname'], '507')
        _no_placeholder_ports(ns)


class TestNxosLldpBriefDeviceIdFirst(unittest.TestCase):
    def test_official_nxos_column_order(self):
        ns = nd._parse_cisco_lldp_brief(
            _read('device_like_nxos_lldp_brief_device_id_first.txt'), 'LEAF', None,
        )
        hosts = {n['hostname'] for n in ns}
        self.assertIn('SPINE-NXOS-01', hosts)
        self.assertIn('DIST-IOS-02', hosts)
        spine = next(n for n in ns if n['hostname'] == 'SPINE-NXOS-01')
        self.assertEqual(spine['local_port'], 'Eth1/1')
        self.assertEqual(spine['remote_port'], 'Eth1/2')


class TestIosCdpIpv4AndBlankIp(unittest.TestCase):
    def test_ipv4_address_and_missing_ip_both_parse(self):
        ns = nd._parse_cisco_cdp_detail(
            _read('legacy_ios_cdp_detail_ipv4_and_blank_ip.txt'), 'EDGE', None,
        )
        self.assertEqual(len(ns), 2)
        core = next(n for n in ns if n['hostname'].startswith('CORE-R1'))
        self.assertEqual(core['ip'], '10.9.9.1')
        silent = next(n for n in ns if n['hostname'] == 'SILENT-SW')
        self.assertIsNone(silent['ip'])
        fin = nd._finalize_neighbor(dict(silent))
        self.assertEqual(fin['local_port'], 'Fa0/1')
        self.assertTrue(fin['edge_eligible'])


class TestCrlfAndMixedCase(unittest.TestCase):
    def test_cdp_detail_crlf_same_as_lf(self):
        body = _read('ios_cdp_detail.txt')
        crlf = body.replace('\n', '\r\n')
        a = nd._parse_cisco_cdp_detail(body, 'CORE', None)
        b = nd._parse_cisco_cdp_detail(crlf, 'CORE', None)
        self.assertEqual([n['hostname'] for n in a], [n['hostname'] for n in b])

    def test_lldp_mixed_case_headers(self):
        block = (
            'CHASSIS ID: 0011.2233.4455\n'
            'local intf: Gi1/0/2\n'
            'PORT ID: Gi0/24\n'
            'system name: MixedCase-SW\n'
        )
        ns = nd._parse_cisco_lldp_detail(block, 'EDGE', None)
        self.assertEqual(len(ns), 1)
        self.assertEqual(ns[0]['hostname'], 'MixedCase-SW')
        self.assertEqual(ns[0]['local_port'], 'Gi1/0/2')


class TestIncompleteNeverPromoted(unittest.TestCase):
    def test_truncated_cdp_detail_not_edge_eligible(self):
        ns = nd._parse_cisco_cdp_detail(
            _read('phase5_ios_cdp_detail_truncated_no_interface.txt'), 'EDGE', None,
        )
        self.assertGreaterEqual(len(ns), 1)
        fin = nd._finalize_neighbor(dict(ns[0]))
        self.assertIsNotNone(fin)
        self.assertFalse(fin.get('edge_eligible'))
        self.assertTrue(fin.get('incomplete'))
        nodes = [{
            'id': 'EDGE', 'ip': '10.0.0.1', 'device_type': 'cisco_ios',
            'incomplete_observations': [fin],
        }]
        canon_n, canon_e, _meta = canonicalize_discovery_graph(nodes, [])
        self.assertEqual(canon_e, [])
        for n in canon_n:
            for obs in n.get('incomplete_observations') or []:
                self.assertNotEqual(obs.get('edge_eligible'), True)
        # Empty-port incomplete rows must not become cables
        self.assertFalse(fin.get('local_port'))
        self.assertFalse(fin.get('edge_eligible'))


class TestMapDoesNotDrawIncompleteAsCable(unittest.TestCase):
    def test_fixture_map_html_labels_incomplete_not_edge(self):
        raw = nd._parse_cisco_cdp_detail(
            _read('phase5_ios_cdp_detail_truncated_no_interface.txt'), 'EDGE', None,
        )
        fin = nd._finalize_neighbor(dict(raw[0]))
        nodes = [{
            'id': 'EDGE-01', 'ip': '10.0.0.1', 'device_type': 'cisco_ios',
            'depth': 0, 'is_scanned': True, 'scan_state': 'scanned',
            'incomplete_observations': [fin],
        }]
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, 'map.html')
            generate_discovery_html(path, nodes, [])
            html = open(path, encoding='utf-8').read()
        self.assertIn('incomplete', html.lower())
        # No vis.js edge from the seed — incomplete is not a cable
        self.assertNotIn('"from": "EDGE-01"', html)


class TestGraphPortNormalizeMatchesParser(unittest.TestCase):
    def test_discovery_graph_collapses_spaced_cdp_abbrev(self):
        from utils.discovery_graph import normalize_discovery_edges
        edges = normalize_discovery_edges([{
            'from': 'A', 'to': 'B',
            'f_port': 'Gig 1/0/1', 't_port': 'GigabitEthernet1/0/48',
            'protocol': 'CDP', 'sources': ['CDP'],
        }])
        self.assertEqual(edges[0]['f_port'], 'Gi1/0/1')
        self.assertEqual(edges[0]['t_port'], 'Gi1/0/48')

    def test_canonicalize_does_not_import_paramiko(self):
        """Phase 4 freeze: graph canonicalize must not pull SSH stacks."""
        import sys
        sys.modules.pop('paramiko', None)
        from utils.discovery_graph import canonicalize_discovery_graph
        canonicalize_discovery_graph(
            [{'id': 'A', 'ip': '10.0.0.1', 'device_type': 'cisco_ios'}],
            [{'from': 'A', 'to': 'B', 'f_port': 'Gig 1/0/1', 't_port': 'Gi1/0/2',
              'protocol': 'CDP', 'sources': ['CDP']}],
        )
        self.assertNotIn('paramiko', sys.modules)
    def test_hyphen_and_colon_mac(self):
        self.assertTrue(nd._is_mac_like('00:1a:2b:3c:4d:5e'))
        self.assertTrue(nd._is_mac_like('00-1A-2B-3C-4D-5E'))
        self.assertTrue(nd._is_mac_like('mac 00:1a:2b:3c:4d:5e'))
        self.assertFalse(nd._is_mac_like('mac'))
        self.assertFalse(nd._is_mac_like('507'))


if __name__ == '__main__':
    unittest.main()
