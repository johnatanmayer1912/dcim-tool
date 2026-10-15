"""Phase 5 slice 3 — operator-facing incomplete observations (API + UI contract).

Fixture-only. Incomplete observations stay diagnosable and never edge-eligible.
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.plugins import network_discovery as nd
from utils.discovery_graph import merge_nodes
from utils.evidence_inspector import build_incomplete_observation_model

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'discovery')
INDEX = os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html')


def _read(name: str) -> str:
    with open(os.path.join(FIX, name), encoding='utf-8') as f:
        return f.read()


class TestOperatorIncompleteApi(unittest.TestCase):
    def test_nodes_to_api_devices_surfaces_incomplete(self):
        raw = nd._parse_cisco_cdp_detail(
            _read('phase5_ios_cdp_detail_truncated_no_interface.txt'), 'EDGE', None,
        )
        fin = nd._finalize_neighbor(dict(raw[0]))
        self.assertTrue(fin.get('incomplete'))
        devices = nd._nodes_to_api_devices([{
            'id': 'EDGE-01',
            'ip': '10.0.0.1',
            'is_scanned': True,
            'scan_state': 'scanned',
            'neighbor_evidence': 'collected',
            'incomplete_observations': [fin],
        }])
        self.assertEqual(devices[0]['incomplete_observation_count'], 1)
        row = devices[0]['incomplete_observations'][0]
        self.assertTrue(row['incomplete'])
        self.assertFalse(row['edge_eligible'])
        self.assertEqual(row['local_port'], '')
        self.assertEqual(row['remote_port'], '')
        self.assertEqual(row['local_port_display'], '(unobserved)')
        self.assertEqual(row['remote_port_display'], '(unobserved)')
        self.assertNotIn('raw_fragment', row)
        self.assertNotEqual(row.get('hostname'), 'unknown')
        self.assertIn('incomplete', (row.get('cable_claim') or '').lower())

    def test_operator_incomplete_strips_placeholder_host(self):
        row = nd._operator_incomplete_observation({
            'hostname': 'unknown',
            'local_port': 'n/a',
            'remote_port': 'unknown',
            'protocol': 'CDP',
            'incomplete': True,
            'evidence_gaps': ['local_port'],
            'parse_warning': 'incomplete CDP detail: missing Interface',
            'raw_fragment': 'Device ID: secret-should-not-export',
        })
        self.assertEqual(row['hostname'], '')
        self.assertEqual(row['local_port'], '')
        self.assertEqual(row['remote_port'], '')
        self.assertTrue(row['raw_fragment_present'])
        self.assertNotIn('secret-should-not-export', str(row))

    def test_edges_to_api_links_empty_ports_not_n_a(self):
        links = nd._edges_to_api_links([{
            'from': 'A', 'to': 'B',
            'f_port': 'Gi0/1', 't_port': '',
            'protocol': 'CDP', 'one_sided': True,
        }])
        self.assertEqual(links[0]['local_port'], 'Gi0/1')
        self.assertEqual(links[0]['remote_port'], '')
        self.assertNotEqual(links[0]['remote_port'], 'n/a')
        self.assertNotEqual(links[0]['remote_port'], 'unknown')

        blank = nd._edges_to_api_links([{
            'from': 'A', 'to': 'B',
            'f_port': 'unknown', 't_port': 'n/a',
            'protocol': 'LLDP',
        }])
        self.assertEqual(blank[0]['local_port'], '')
        self.assertEqual(blank[0]['remote_port'], '')


class TestMergePreservesIncomplete(unittest.TestCase):
    def test_merge_nodes_keeps_incomplete_observations(self):
        nodes = [
            {
                'id': 'EDGE-01',
                'ip': '10.0.0.1',
                'is_scanned': True,
                'scan_state': 'scanned',
                'incomplete_observations': [{
                    'hostname': 'TRUNC-PEER.example.com',
                    'local_port': '',
                    'remote_port': '',
                    'protocol': 'CDP',
                    'incomplete': True,
                    'edge_eligible': False,
                    'parse_warning': 'incomplete CDP detail: missing Interface',
                    'evidence_gaps': ['local_port', 'remote_port'],
                }],
            },
            {
                'id': 'EDGE-01',
                'ip': '10.0.0.1',
                'is_scanned': False,
                'scan_state': 'seed',
            },
        ]
        merged, _alias = merge_nodes(nodes)
        self.assertEqual(len(merged), 1)
        incompletes = merged[0].get('incomplete_observations') or []
        self.assertEqual(len(incompletes), 1)
        self.assertEqual(incompletes[0]['hostname'], 'TRUNC-PEER.example.com')
        self.assertTrue(incompletes[0].get('incomplete'))
        self.assertFalse(incompletes[0].get('edge_eligible'))


class TestOperatorUiContract(unittest.TestCase):
    def test_index_html_has_incomplete_panel_and_helpers(self):
        html = open(INDEX, encoding='utf-8').read()
        self.assertIn('disc-incomplete-panel', html)
        self.assertIn('discRenderIncompletePanel', html)
        self.assertIn('incomplete observation(s) — not link(s)', html)
        self.assertIn('(unobserved)', html)
        self.assertIn('not map links', html.lower().replace('—', '-'))

    def test_incomplete_model_still_distinct_from_edge_inspector(self):
        model = build_incomplete_observation_model({
            'hostname': 'PEER',
            'local_port': '',
            'remote_port': '',
            'protocol': 'CDP',
            'incomplete': True,
            'evidence_gaps': ['local_port'],
        })
        self.assertTrue(model['incomplete'])
        self.assertFalse(model['edge_eligible'])
        self.assertEqual(model['ports']['local_port_raw'], '')


if __name__ == '__main__':
    unittest.main()
