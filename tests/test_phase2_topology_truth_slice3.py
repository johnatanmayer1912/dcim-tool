"""Phase 2 slice-3 — per-evidence timestamps + mixed-freshness visibility.

Fixture-only. No live vendor SSH.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.plugins import network_discovery as nd
from utils.discovery_graph import (
    annotate_edge_freshness,
    canonicalize_discovery_graph,
    make_observation_evidence,
    merge_protocol_duplicate_edges,
)
from utils.discovery_map_formatter import build_vis_payload, generate_discovery_html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, 'tests', 'fixtures', 'discovery')


def _read(name: str) -> str:
    with open(os.path.join(FIXTURES, name), encoding='utf-8') as f:
        return f.read()


class TestPerEvidenceTimestamps(unittest.TestCase):
    def test_make_observation_preserves_unknown_timestamp(self):
        ev = make_observation_evidence(protocol='LLDP', vendor='cisco')
        self.assertIsNone(ev['collected_at'])
        self.assertEqual(ev['protocol'], 'LLDP')
        self.assertIn('lldp', ev['command'].lower())

    def test_merge_keeps_separate_evidence_timestamps(self):
        fresh = '2026-08-20T10:00:00Z'
        stale = '2026-08-18T10:00:00Z'
        edges = [
            {
                'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
                'protocol': 'CDP', 'collected_at': fresh,
                'evidence': [make_observation_evidence(
                    protocol='CDP', vendor='cisco', collected_at=fresh,
                    local_port='Gi0/1', remote_port='Gi0/2',
                    command='show cdp neighbors detail',
                )],
            },
            {
                'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
                'protocol': 'LLDP', 'collected_at': stale,
                'evidence': [make_observation_evidence(
                    protocol='LLDP', vendor='cisco', collected_at=stale,
                    local_port='Gi0/1', remote_port='Gi0/2',
                )],
            },
        ]
        merged = merge_protocol_duplicate_edges(edges)
        self.assertEqual(len(merged), 1)
        ev = merged[0]['evidence']
        self.assertEqual(len(ev), 2)
        stamps = {e['collected_at'] for e in ev}
        self.assertEqual(stamps, {fresh, stale})
        self.assertTrue(merged[0].get('mixed_source_timestamps'))
        self.assertEqual(merged[0]['collected_at'], min(fresh, stale))
        self.assertEqual(merged[0]['collected_at_latest'], max(fresh, stale))
        protos = {e['protocol'].upper() for e in ev}
        self.assertEqual(protos, {'CDP', 'LLDP'})
        self.assertIn('cisco', {e.get('vendor') for e in ev})

    def test_missing_source_timestamp_stays_unknown(self):
        edges = [{
            'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
            'protocol': 'CDP',
            'evidence': [make_observation_evidence(protocol='CDP')],
        }]
        annotate_edge_freshness(edges)
        self.assertEqual(edges[0]['freshness'], 'unknown')
        self.assertEqual(edges[0]['evidence'][0]['freshness'], 'unknown')

    def test_current_plus_stale_is_mixed_conflict_visible(self):
        now = datetime(2026, 8, 20, 12, 0, 0)
        fresh = (now - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S')
        stale = (now - timedelta(hours=40)).strftime('%Y-%m-%dT%H:%M:%S')
        edges = [{
            'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
            'protocol': 'CDP+LLDP',
            'evidence': [
                make_observation_evidence(protocol='CDP', collected_at=fresh),
                make_observation_evidence(protocol='LLDP', collected_at=stale),
            ],
        }]
        annotate_edge_freshness(edges, now=now, stale_hours=24)
        self.assertEqual(edges[0]['freshness'], 'mixed')
        self.assertTrue(edges[0].get('freshness_conflict'))
        self.assertIn('mixed-freshness', ' '.join(edges[0].get('contradictions') or []))
        kinds = {ev['freshness'] for ev in edges[0]['evidence']}
        self.assertEqual(kinds, {'current', 'stale'})
        # Mixed freshness alone must not force Mismatch confidence
        self.assertNotEqual(edges[0].get('confidence'), 'Mismatch')

    def test_conflicting_remote_ports_still_mismatch(self):
        nodes = [
            {'id': 'A', 'ip': '10.0.0.1', 'is_scanned': True},
            {'id': 'B', 'ip': '10.0.0.2', 'is_scanned': False},
        ]
        edges = [
            {
                'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
                'protocol': 'CDP', 'collected_at': '2026-08-20T10:00:00Z',
                'evidence': [make_observation_evidence(
                    protocol='CDP', collected_at='2026-08-20T10:00:00Z',
                    local_port='Gi0/1', remote_port='Gi0/2',
                )],
            },
            {
                'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/9',
                'protocol': 'LLDP', 'collected_at': '2026-08-20T11:00:00Z',
                'evidence': [make_observation_evidence(
                    protocol='LLDP', collected_at='2026-08-20T11:00:00Z',
                    local_port='Gi0/1', remote_port='Gi0/9',
                )],
            },
        ]
        _m, rewired, _r = canonicalize_discovery_graph(nodes, edges)
        # Distinct remote ports remain parallel OR mismatch — not silently one winner inventing agreement
        if len(rewired) == 1:
            self.assertEqual((rewired[0].get('confidence') or '').lower(), 'mismatch')
        else:
            self.assertEqual(len(rewired), 2)
            for e in rewired:
                self.assertTrue(e.get('evidence'))

    def test_legacy_edge_without_evidence_backward_compatible(self):
        edges = [{
            'from': 'A', 'to': 'B', 'f_port': 'Eth1/1', 't_port': 'Eth1/2',
            'protocol': 'LLDP', 'collected_at': '2026-08-20T10:00:00',
        }]
        annotate_edge_freshness(edges, now=datetime(2026, 8, 20, 12, 0, 0))
        self.assertTrue(edges[0].get('evidence'))
        self.assertIn(edges[0]['freshness'], ('current', 'stale', 'unknown'))


class TestJunosLldpDetailIrb(unittest.TestCase):
    def test_detail_physical_and_irb(self):
        neighbors = nd._parse_juniper_lldp_detail(
            _read('junos_lldp_detail_irb.txt'), 'QFX', None,
        )
        hosts = {n['hostname'] for n in neighbors}
        self.assertIn('edge-junos-04', hosts)
        self.assertIn('gw-host-01', hosts)
        irb = next(n for n in neighbors if str(n.get('local_port', '')).startswith('irb'))
        self.assertTrue(irb.get('not_physical'))
        self.assertEqual(irb.get('port_role'), 'irb_l3')
        self.assertIn('raw_fragment', irb)
        phys = next(n for n in neighbors if n['hostname'] == 'edge-junos-04')
        self.assertFalse(phys.get('not_physical'))
        self.assertNotEqual(phys.get('local_port'), 'unknown')

    def test_irb_detail_not_physical_after_canonicalize(self):
        neighbors = nd._parse_juniper_lldp_detail(
            _read('junos_lldp_detail_irb.txt'), 'QFX', None,
        )
        irb = next(n for n in neighbors if n.get('not_physical'))
        nodes = [
            {'id': 'QFX', 'ip': '10.0.0.1', 'is_scanned': True},
            {'id': irb['hostname'], 'ip': '10.0.0.50', 'is_scanned': False},
        ]
        edges = [{
            'from': 'QFX', 'to': irb['hostname'],
            'f_port': irb['local_port'], 't_port': irb['remote_port'],
            'protocol': 'LLDP', 'not_physical': True, 'layer': 'l3-logical',
            'evidence': [make_observation_evidence(
                protocol='LLDP', vendor='juniper',
                local_port=irb['local_port'], remote_port=irb['remote_port'],
                not_physical=True, port_role='irb_l3',
                command='show lldp neighbors detail',
            )],
        }]
        _m, rewired, _r = canonicalize_discovery_graph(nodes, edges)
        self.assertTrue(rewired[0].get('not_physical'))
        self.assertEqual(rewired[0].get('edge_kind'), 'irb-adjacency')
        self.assertTrue(rewired[0]['evidence'][0].get('not_physical'))


class TestMapEvidencePayload(unittest.TestCase):
    def test_vis_payload_exposes_evidence_and_mixed_freshness(self):
        nodes = [
            {'id': 'A', 'ip': '10.0.0.1', 'depth': 0, 'is_scanned': True},
            {'id': 'B', 'ip': '10.0.0.2', 'depth': 1, 'is_scanned': False},
        ]
        edges = [{
            'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
            'protocol': 'CDP+LLDP',
            'freshness': 'mixed', 'freshness_conflict': True,
            'contradictions': ['mixed-freshness evidence timestamps'],
            'evidence': [
                make_observation_evidence(protocol='CDP', collected_at='2026-08-20T10:00:00Z', vendor='cisco'),
                make_observation_evidence(protocol='LLDP', collected_at='2026-08-18T10:00:00Z', vendor='cisco'),
            ],
            'evidence_summary': {'count': 2, 'protocols': ['CDP', 'LLDP']},
            'collected_at': '2026-08-18T10:00:00Z',
            'collected_at_latest': '2026-08-20T10:00:00Z',
        }]
        _nj, ej, _lr = build_vis_payload(nodes, edges)
        self.assertEqual(len(ej), 1)
        self.assertEqual(len(ej[0]['evidence']), 2)
        self.assertTrue(ej[0]['freshness_conflict'])
        self.assertIn('MIXED FRESHNESS', ej[0]['title'])
        self.assertEqual(ej[0]['freshness'], 'mixed')

    def test_html_meta_retains_evidence_fields(self):
        nodes = [{'id': 'A', 'ip': '10.0.0.1', 'depth': 0, 'is_scanned': True}]
        edges = [{
            'from': 'A', 'to': 'B', 'f_port': 'ge-0/0/0', 't_port': 'ge-0/0/1',
            'protocol': 'LLDP', 'freshness': 'current',
            'evidence': [make_observation_evidence(
                protocol='LLDP', vendor='juniper',
                collected_at='2026-08-20T10:00:00Z',
                command='show lldp neighbors detail',
            )],
            'collected_at': '2026-08-20T10:00:00Z',
        }]
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, 'm.html')
            generate_discovery_html(path, nodes, edges, extra_meta={
                'collected_at': '2026-08-20T10:00:00Z',
            })
            html = open(path, encoding='utf-8').read()
            self.assertIn('evidence', html)
            self.assertIn('show lldp neighbors detail', html)
            self.assertIn('collected_at', html)


if __name__ == '__main__':
    unittest.main()
