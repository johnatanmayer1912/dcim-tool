"""Phase 2 slice-1 — CDP/LLDP truth: no invented ports, dual-stack CDP parity.

Fixture-only. No live Cisco / NX-OS / Junos SSH.
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.plugins import network_discovery as nd
from modules import topology_mapper as tm
from utils.discovery_graph import (
    canonicalize_discovery_graph,
    normalize_discovery_edges,
    _normalize_edge_port,
)
from utils.topology_trust import apply_discovery_edge_trust

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, 'tests', 'fixtures', 'discovery')


def _read(name: str) -> str:
    with open(os.path.join(FIXTURES, name), encoding='utf-8') as f:
        return f.read()


def _short_host(h: str) -> str:
    return (h or '').split('.')[0].strip().lower()


def _norm_port(p: str) -> str:
    return nd._normalize_interface_name(p or '')


class TestNoInventedPorts(unittest.TestCase):
    def test_finalize_drops_missing_local_port(self):
        n = nd._finalize_neighbor({
            'hostname': 'PEER-A',
            'local_port': '',
            'remote_port': 'Gi1/0/1',
            'protocol': 'CDP',
        })
        self.assertIsNone(n)

    def test_finalize_keeps_partial_without_n_a(self):
        n = nd._finalize_neighbor({
            'hostname': 'PEER-A',
            'local_port': 'GigabitEthernet1/0/1',
            'remote_port': '',
            'protocol': 'CDP',
        })
        self.assertIsNotNone(n)
        self.assertEqual(n['local_port'], 'Gi1/0/1')
        self.assertEqual(n['remote_port'], '')
        self.assertTrue(n.get('partial'))
        self.assertNotIn('n/a', n['remote_port'])
        self.assertNotEqual(n['local_port'], 'unknown')

    def test_normalize_edge_port_never_invents_placeholder(self):
        self.assertEqual(_normalize_edge_port(''), '')
        self.assertEqual(_normalize_edge_port('unknown'), '')
        self.assertEqual(_normalize_edge_port('n/a'), '')
        self.assertEqual(_normalize_edge_port('Gi1/0/1'), 'Gi1/0/1')

    def test_normalize_discovery_edges_marks_partial(self):
        edges = normalize_discovery_edges([
            {'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': '', 'protocol': 'CDP'},
        ])
        self.assertEqual(edges[0]['t_port'], '')
        self.assertTrue(edges[0].get('partial'))
        self.assertIn('remote_port', edges[0].get('evidence_gaps') or [])
        self.assertNotIn('n/a', edges[0]['label'])


class TestCiscoCdpTruth(unittest.TestCase):
    def test_ios_cdp_detail_raw_evidence_and_ports(self):
        text = _read('ios_cdp_detail.txt')
        neighbors = nd._parse_cisco_cdp_detail(text, 'CORE', None)
        dist = next(n for n in neighbors if 'DIST' in n['hostname'])
        self.assertEqual(dist['local_port'], 'GigabitEthernet1/0/1')
        self.assertEqual(dist['remote_port'], 'GigabitEthernet1/0/48')
        self.assertIn('raw_fragment', dist)
        self.assertIn('Device ID', dist['raw_fragment'])
        finalized = nd._finalize_neighbor(dist)
        self.assertEqual(finalized['local_port'], 'Gi1/0/1')
        self.assertEqual(finalized['remote_port'], 'Gi1/0/48')
        self.assertNotIn(finalized['local_port'], ('unknown', 'n/a'))

    def test_ios_cdp_brief_filters_ap_keeps_switch(self):
        neighbors = nd._parse_cisco_cdp_brief(_read('ios_cdp_brief.txt'), 'CORE', None)
        hosts = {n['hostname'] for n in neighbors}
        self.assertIn('DIST-SW01', hosts)
        # AP platform filtered
        self.assertNotIn('AP-FLOOR2', hosts)

    def test_nxos_cdp_detail_two_neighbors(self):
        neighbors = nd._parse_cisco_cdp_detail(_read('nxos_cdp_detail.txt'), 'LEAF', None)
        hosts = {n['hostname'] for n in neighbors}
        self.assertEqual(hosts, {'SPINE-NXOS-05', 'LEAF-NXOS-11'})
        spine = next(n for n in neighbors if n['hostname'] == 'SPINE-NXOS-05')
        self.assertEqual(spine['local_port'], 'Ethernet1/2')
        self.assertEqual(spine['remote_port'], 'Ethernet1/1')
        fin = nd._finalize_neighbor(spine)
        self.assertEqual(fin['local_port'], 'Eth1/2')
        self.assertEqual(fin['remote_port'], 'Eth1/1')


class TestDualStackCdpParity(unittest.TestCase):
    def _identity_discovery(self, text: str, local: str):
        out = []
        for n in nd._parse_cisco_cdp_detail(text, local, None):
            f = nd._finalize_neighbor(n)
            if not f:
                continue
            out.append((
                _short_host(f['hostname']),
                _norm_port(f['local_port']),
                _norm_port(f['remote_port']),
            ))
        return sorted(out)

    def _identity_mapper(self, text: str, local: str):
        out = []
        for e in tm._parse_cdp_detail(text, local):
            out.append((
                _short_host(e['to']),
                _norm_port(e['f_port']),
                _norm_port(e['t_port']),
            ))
        return sorted(out)

    def test_ios_cdp_detail_discovery_matches_mapper(self):
        text = _read('ios_cdp_detail.txt')
        d = self._identity_discovery(text, 'CORE')
        m = self._identity_mapper(text, 'CORE')
        self.assertEqual(d, m)
        self.assertEqual(d, [('dist-sw01', 'Gi1/0/1', 'Gi1/0/48')])

    def test_nxos_cdp_detail_discovery_matches_mapper(self):
        text = _read('nxos_cdp_detail.txt')
        d = self._identity_discovery(text, 'LEAF')
        m = self._identity_mapper(text, 'LEAF')
        self.assertEqual(d, m)
        self.assertEqual(len(d), 2)

    def test_mapper_cdp_rejects_lldp_only_fields(self):
        """LLDP detail must not produce CDP edges via _parse_cdp_detail."""
        lldp = _read('nxos_lldp_detail.txt')
        edges = tm._parse_cdp_detail(lldp, 'LEAF')
        self.assertEqual(edges, [])


class TestLldpNormalizationCiscoJunos(unittest.TestCase):
    def test_iosxe_lldp_brief_ports(self):
        neighbors = nd._parse_cisco_lldp_brief(_read('iosxe_lldp_brief.txt'), 'CORE-XE', None)
        dist = next(n for n in neighbors if n['hostname'] == 'DIST-C9300')
        fin = nd._finalize_neighbor(dist)
        self.assertIsNotNone(fin)
        self.assertTrue(fin['local_port'])
        self.assertTrue(fin['remote_port'])
        self.assertNotIn(fin['local_port'], ('unknown', 'n/a'))

    def test_junos_lldp_brief_finalize(self):
        neighbors = nd._parse_juniper_lldp_brief(_read('junos_lldp_brief.txt'), 'QFX', None)
        for raw in neighbors:
            fin = nd._finalize_neighbor(raw)
            self.assertIsNotNone(fin)
            self.assertTrue(fin['local_port'])
            self.assertNotEqual(fin['local_port'], 'unknown')


class TestDuplicateAndConflict(unittest.TestCase):
    def test_cdp_lldp_same_cable_merges_sources(self):
        nodes = [
            {'id': 'A', 'ip': '10.0.0.1', 'is_scanned': True},
            {'id': 'B', 'ip': '10.0.0.2', 'is_scanned': False},
        ]
        edges = [
            {'from': 'A', 'to': 'B', 'f_port': 'Gi1/0/1', 't_port': 'Gi1/0/2', 'protocol': 'CDP'},
            {'from': 'A', 'to': 'B', 'f_port': 'Gi1/0/1', 't_port': 'Gi1/0/2', 'protocol': 'LLDP'},
        ]
        _m, rewired, _r = canonicalize_discovery_graph(nodes, edges)
        self.assertEqual(len(rewired), 1)
        sources = {str(s).lower() for s in (rewired[0].get('sources') or [])}
        self.assertIn('cdp', sources)
        self.assertIn('lldp', sources)
        self.assertTrue(rewired[0].get('provenance_merged') or 'CDP' in str(rewired[0].get('protocol')))

    def test_conflicting_remote_ports_mismatch(self):
        nodes = [
            {'id': 'A', 'ip': '10.0.0.1', 'is_scanned': True},
            {'id': 'B', 'ip': '10.0.0.2', 'is_scanned': False},
        ]
        edges = [
            {'from': 'A', 'to': 'B', 'f_port': 'Gi1/0/1', 't_port': 'Gi1/0/2', 'protocol': 'CDP'},
            {'from': 'A', 'to': 'B', 'f_port': 'Gi1/0/1', 't_port': 'Gi1/0/9', 'protocol': 'LLDP'},
        ]
        _m, rewired, _r = canonicalize_discovery_graph(nodes, edges)
        # Distinct remote ports → parallel or mismatch-flagged; must not invent a third port
        ports = {(e.get('f_port'), e.get('t_port')) for e in rewired}
        self.assertTrue(all(tp not in ('n/a', 'unknown') for _, tp in ports))
        if len(rewired) == 1:
            self.assertEqual((rewired[0].get('confidence') or '').lower(), 'mismatch')
        else:
            self.assertEqual(len(rewired), 2)

    def test_unattributed_protocol_not_defaulted_to_cdp(self):
        edges = [
            {'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2'},
        ]
        apply_discovery_edge_trust(edges)
        self.assertEqual(edges[0].get('discovery'), 'unattributed')
        self.assertIn('protocol', edges[0].get('evidence_gaps') or [])
        self.assertNotEqual(edges[0].get('discovery'), 'cdp')
        # Ports present → still High when bidirectional pair absent (one-sided Medium)
        self.assertIn(edges[0].get('confidence'), ('Medium', 'High', 'Low'))


if __name__ == '__main__':
    unittest.main()
