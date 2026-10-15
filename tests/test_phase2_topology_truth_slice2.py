"""Phase 2 slice-2 — Junos IRB/VLAN honesty + edge freshness attribution.

Fixture-only. No live Junos / Cisco SSH.
"""
from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.plugins import network_discovery as nd
from utils.discovery_graph import (
    annotate_edge_freshness,
    annotate_logical_l3_edges,
    canonicalize_discovery_graph,
)
from utils.discovery_map_formatter import generate_discovery_html
from utils.juniper_iface import (
    classify_junos_port_role,
    is_junos_interface,
    is_junos_irb,
    is_junos_irb_or_l3_svi,
)
from utils.topology_trust import apply_discovery_edge_trust

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, 'tests', 'fixtures', 'discovery')


def _read(name: str) -> str:
    with open(os.path.join(FIXTURES, name), encoding='utf-8') as f:
        return f.read()


class TestJunosIrbNormalization(unittest.TestCase):
    def test_irb_dot_and_hyphen_recognized(self):
        self.assertTrue(is_junos_irb('irb.100'))
        self.assertTrue(is_junos_irb('irb-0/0/0'))
        self.assertTrue(is_junos_irb_or_l3_svi('vlan.200'))
        self.assertTrue(is_junos_interface('irb.100'))
        self.assertEqual(classify_junos_port_role('irb.100'), 'irb_l3')
        self.assertEqual(classify_junos_port_role('ge-0/0/0'), 'physical')
        self.assertEqual(classify_junos_port_role('ae0'), 'ae_bundle')

    def test_brief_parses_irb_as_non_physical_evidence(self):
        neighbors = nd._parse_juniper_lldp_brief(
            _read('junos_lldp_brief_irb.txt'), 'QFX-CORE', None,
        )
        hosts = {n['hostname'] for n in neighbors}
        self.assertIn('DIST-QFX-01', hosts)
        self.assertIn('GW-HOST-01', hosts)
        self.assertIn('SPINE-QFX-02', hosts)
        irb = next(n for n in neighbors if n['local_port'].startswith('irb'))
        self.assertTrue(irb.get('not_physical'))
        self.assertEqual(irb.get('port_role'), 'irb_l3')
        self.assertIn('physical_link', irb.get('evidence_gaps') or [])
        phys = next(n for n in neighbors if n['hostname'] == 'DIST-QFX-01')
        self.assertFalse(phys.get('not_physical'))
        self.assertEqual(phys.get('port_role'), 'physical')

    def test_irb_edge_not_scored_as_physical_cable(self):
        nodes = [
            {'id': 'QFX', 'ip': '10.0.0.1', 'is_scanned': True},
            {'id': 'GW', 'ip': '10.0.0.2', 'is_scanned': False},
        ]
        edges = [
            {
                'from': 'QFX', 'to': 'GW',
                'f_port': 'irb.100', 't_port': 'ge-0/0/24',
                'protocol': 'LLDP', 'not_physical': True, 'layer': 'l3-logical',
            },
        ]
        _m, rewired, _r = canonicalize_discovery_graph(nodes, edges)
        self.assertEqual(len(rewired), 1)
        e = rewired[0]
        self.assertTrue(e.get('not_physical'))
        self.assertEqual(e.get('edge_kind'), 'irb-adjacency')
        self.assertNotEqual((e.get('confidence') or '').lower(), 'high')
        self.assertNotEqual((e.get('confidence') or '').lower(), 'verified')
        self.assertNotEqual(e.get('bundle_kind'), 'member')

    def test_vlan_membership_alone_does_not_invent_edge(self):
        """Shared VLAN context must not become a topology edge without neighbor evidence."""
        nodes = [
            {'id': 'A', 'ip': '10.0.0.1', 'is_scanned': True, 'vlans': ['100']},
            {'id': 'B', 'ip': '10.0.0.2', 'is_scanned': True, 'vlans': ['100']},
        ]
        _m, rewired, _r = canonicalize_discovery_graph(nodes, [])
        self.assertEqual(rewired, [])

    def test_mixed_lldp_physical_plus_irb_keeps_physical(self):
        nodes = [
            {'id': 'QFX', 'ip': '10.0.0.1', 'is_scanned': True},
            {'id': 'DIST', 'ip': '10.0.0.2', 'is_scanned': False},
            {'id': 'GW', 'ip': '10.0.0.3', 'is_scanned': False},
        ]
        edges = [
            {'from': 'QFX', 'to': 'DIST', 'f_port': 'ge-0/0/0', 't_port': 'ge-0/0/1', 'protocol': 'LLDP'},
            {
                'from': 'QFX', 'to': 'GW', 'f_port': 'irb.100', 't_port': 'ge-0/0/24',
                'protocol': 'LLDP', 'not_physical': True, 'layer': 'l3-logical',
            },
        ]
        _m, rewired, _r = canonicalize_discovery_graph(nodes, edges)
        phys = next(
            e for e in rewired
            if 'dist' in (str(e.get('to') or '').lower(), str(e.get('from') or '').lower())
        )
        irb = next(
            e for e in rewired
            if 'gw' in (str(e.get('to') or '').lower(), str(e.get('from') or '').lower())
        )
        self.assertFalse(phys.get('not_physical'))
        self.assertTrue(irb.get('not_physical'))


class TestEdgeFreshness(unittest.TestCase):
    def test_missing_timestamp_is_unknown(self):
        edges = [{'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2'}]
        annotate_edge_freshness(edges)
        self.assertEqual(edges[0]['freshness'], 'unknown')
        self.assertIn('no observation', edges[0].get('freshness_note', '').lower())

    def test_current_and_stale_stamps(self):
        now = datetime(2026, 8, 20, 12, 0, 0)
        fresh_ts = (now - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S')
        stale_ts = (now - timedelta(hours=30)).strftime('%Y-%m-%dT%H:%M:%S')
        edges = [
            {'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2', 'collected_at': fresh_ts},
            {'from': 'A', 'to': 'C', 'f_port': 'Gi0/3', 't_port': 'Gi0/4', 'collected_at': stale_ts},
        ]
        annotate_edge_freshness(edges, now=now, stale_hours=24)
        self.assertEqual(edges[0]['freshness'], 'current')
        self.assertFalse(edges[0].get('stale'))
        self.assertEqual(edges[1]['freshness'], 'stale')
        self.assertTrue(edges[1].get('stale'))
        self.assertEqual(edges[0].get('freshness_graph'), 'mixed')
        self.assertEqual(edges[1].get('freshness_graph'), 'mixed')

    def test_canonicalize_propagates_freshness(self):
        now = datetime(2026, 8, 20, 12, 0, 0)
        ts = (now - timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%SZ')
        nodes = [
            {'id': 'A', 'ip': '10.0.0.1', 'is_scanned': True},
            {'id': 'B', 'ip': '10.0.0.2', 'is_scanned': False},
        ]
        edges = [
            {
                'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
                'protocol': 'CDP', 'collected_at': ts,
            },
        ]
        _m, rewired, _r = canonicalize_discovery_graph(nodes, edges)
        # Age depends on wall clock — only assert field exists and is not inventing a stamp
        self.assertIn(rewired[0].get('freshness'), ('current', 'stale', 'unknown'))
        self.assertEqual(rewired[0].get('collected_at'), ts)

    def test_map_meta_prefers_collected_at(self):
        import tempfile
        nodes = [{'id': 'A', 'ip': '10.0.0.1', 'depth': 0, 'is_scanned': True}]
        edges = [{
            'from': 'A', 'to': 'B', 'f_port': 'ge-0/0/0', 't_port': 'ge-0/0/1',
            'protocol': 'LLDP', 'collected_at': '2026-08-19T10:00:00Z',
            'freshness': 'stale',
        }]
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, 'map.html')
            generate_discovery_html(
                path, nodes, edges,
                extra_meta={'collected_at': '2026-08-19T10:00:00Z'},
            )
            html = open(path, encoding='utf-8').read()
            self.assertIn('2026-08-19T10:00:00Z', html)
            self.assertIn('collected_at', html)
            self.assertIn('freshness_basis', html)

    def test_trust_does_not_verified_irb(self):
        edges = [
            {
                'from': 'A', 'to': 'B', 'f_port': 'irb.10', 't_port': 'ge-0/0/1',
                'protocol': 'LLDP', 'not_physical': True, 'layer': 'l3-logical',
            },
        ]
        annotate_logical_l3_edges(edges)
        apply_discovery_edge_trust(edges)
        self.assertTrue(edges[0].get('not_physical'))
        self.assertEqual(edges[0].get('confidence'), 'Low')
        self.assertFalse(edges[0].get('bidirectional'))


if __name__ == '__main__':
    unittest.main()
