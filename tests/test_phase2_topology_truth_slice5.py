"""Phase 2 slice-5 — Link Inventory Inspect parity for evidence inspector.

Fixture-only. No live vendor SSH.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.discovery_graph import make_observation_evidence
from utils.discovery_map_formatter import generate_discovery_html
from utils.evidence_inspector import (
    build_evidence_inspector_model,
    link_row_as_inspector_edge,
)
from utils.topo_map_shell import link_rows_from_edges, render_topology_page


def _mixed_edge():
    return {
        'from': 'SW1', 'to': 'SW2', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
        'protocol': 'CDP+LLDP', 'trust_tier': 'Medium', 'trust_note': 'dual protocol',
        'freshness': 'mixed', 'freshness_conflict': True,
        'freshness_note': 'supporting observations differ in freshness',
        'contradictions': ['mixed-freshness evidence timestamps'],
        'sources': ['cdp', 'lldp'],
        'evidence': [
            make_observation_evidence(
                protocol='CDP', vendor='cisco', collected_at='2026-08-20T10:00:00Z',
                local_port='Gi0/1', remote_port='Gi0/2',
            ),
            make_observation_evidence(
                protocol='LLDP', vendor='cisco', collected_at='2026-08-18T10:00:00Z',
                local_port='Gi0/1', remote_port='Gi0/2',
            ),
        ],
        'evidence_summary': {'count': 2, 'protocols': ['CDP', 'LLDP']},
        'collected_at': '2026-08-18T10:00:00Z',
        'collected_at_latest': '2026-08-20T10:00:00Z',
    }


class TestLinkRowInspectorParity(unittest.TestCase):
    def test_link_rows_carry_evidence_fields(self):
        rows = link_rows_from_edges([_mixed_edge()])
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(len(r['evidence']), 2)
        self.assertEqual(r['freshness'], 'mixed')
        self.assertTrue(r['freshness_conflict'])
        self.assertEqual(r['trust_tier'], 'Medium')
        self.assertIn('mixed-freshness', r['contradictions'][0])

    def test_row_path_matches_map_model_for_normal_edge(self):
        edge = {
            'from': 'A', 'to': 'B', 'f_port': 'Eth1/1', 't_port': 'Gi1/1',
            'protocol': 'CDP', 'freshness': 'current', 'confidence': 'High',
            'evidence': [make_observation_evidence(
                protocol='CDP', vendor='cisco', collected_at='2026-08-20T12:00:00Z',
                local_port='Eth1/1', remote_port='Gi1/1',
                command='show cdp neighbors detail',
            )],
        }
        row = link_rows_from_edges([edge])[0]
        from_row = build_evidence_inspector_model(link_row_as_inspector_edge(row))
        from_map = build_evidence_inspector_model(edge)
        self.assertEqual(from_row['evidence_count'], from_map['evidence_count'])
        self.assertEqual(from_row['endpoints']['from'], from_map['endpoints']['from'])
        self.assertEqual(
            from_row['sections']['observed'][0]['collected_at_display'],
            from_map['sections']['observed'][0]['collected_at_display'],
        )
        self.assertEqual(from_row['sections']['observed'][0]['vendor'], 'cisco')
        self.assertTrue(from_row['read_only'])

    def test_row_path_mixed_freshness_and_conflict(self):
        row = link_rows_from_edges([_mixed_edge()])[0]
        m = build_evidence_inspector_model(link_row_as_inspector_edge(row))
        self.assertTrue(m['freshness']['conflict'])
        self.assertEqual(m['freshness']['state'], 'mixed')
        self.assertEqual(m['evidence_count'], 2)
        self.assertIn('mixed-freshness evidence timestamps', m['sections']['conflicts'])

    def test_row_path_irb_supporting_context(self):
        edge = {
            'from': 'gw', 'to': 'leaf', 'f_port': 'irb.100', 't_port': 'ge-0/0/1',
            'protocol': 'LLDP', 'not_physical': True, 'edge_kind': 'irb-adjacency',
            'evidence': [make_observation_evidence(
                protocol='LLDP', vendor='juniper', local_port='irb.100',
                remote_port='ge-0/0/1', port_role='l3_irb', not_physical=True,
                collected_at='2026-08-20T09:00:00Z',
            )],
        }
        row = link_rows_from_edges([edge])[0]
        self.assertTrue(row['not_physical'])
        m = build_evidence_inspector_model(link_row_as_inspector_edge(row))
        self.assertEqual(len(m['sections']['supporting_context']), 1)
        self.assertIn('not cable', m['classification']['cable_claim'].lower())

    def test_no_evidence_row_honest_empty(self):
        row = link_rows_from_edges([{
            'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2', 'protocol': 'CDP',
        }])[0]
        self.assertEqual(row.get('evidence') or [], [])
        m = build_evidence_inspector_model(link_row_as_inspector_edge(row))
        self.assertFalse(m['has_evidence'])
        self.assertIsNotNone(m['empty_message'])

    def test_row_helper_does_not_invent_or_copy_secrets(self):
        edge = link_row_as_inspector_edge({
            'from': 'A', 'to': 'B', 'local_port': 'Gi0/1', 'remote_port': 'Gi0/2',
            'password': 'secret', 'credential_id': 'c1',
        })
        self.assertEqual(edge['evidence'], [])
        self.assertNotIn('password', edge)
        self.assertNotIn('credential_id', edge)
        self.assertNotIn('secret', str(edge))


class TestLinkInventoryInspectHtml(unittest.TestCase):
    def test_discovery_html_has_inspect_affordance(self):
        nodes = [
            {'id': 'SW1', 'ip': '10.0.0.1', 'is_scanned': True, 'scan_state': 'scanned'},
            {'id': 'SW2', 'ip': '10.0.0.2', 'is_scanned': True, 'scan_state': 'scanned'},
        ]
        edges = [_mixed_edge()]
        path = os.path.join(tempfile.mkdtemp(), 'inv.html')
        generate_discovery_html(path, nodes, edges)
        html = open(path, encoding='utf-8').read()
        self.assertIn('>Inspect</th>', html)
        self.assertIn('nst-ev-inspect-btn', html)
        self.assertIn('nstInspectLinkRowByIndex', html)
        self.assertIn('nstLinkRowToEdge', html)
        self.assertIn('aria-label="Inspect link evidence', html)
        self.assertIn('nstOpenEvidenceInspector', html)
        self.assertIn('nstWhyThisLink', html)
        # evidence still in embedded link rows
        self.assertIn('2026-08-20T10:00:00Z', html)
        self.assertIn('mixed-freshness evidence timestamps', html)
        # read-only / no mutate
        self.assertIn('Read-only inspector', html)
        self.assertNotIn('Promote trust', html)
        self.assertNotIn('Delete evidence', html)
        self.assertNotIn('credential_id', html)

    def test_topo_shell_inspect_and_map_path_intact(self):
        path = os.path.join(tempfile.mkdtemp(), 'topo.html')
        rows = link_rows_from_edges([_mixed_edge()])
        render_topology_page(
            path, 'Test',
            [{'id': 'SW1', 'label': 'SW1', 'x': 0, 'y': 0, 'fixed': True,
              'color': {'background': '#3b82f6'}, 'font': {'color': '#fff'}, 'shape': 'box'}],
            [{'id': 'e0', 'from': 'SW1', 'to': 'SW2', 'label': 'x', 'protocol': 'CDP',
              'color': {'color': '#6366f1'}, 'width': 2, 'evidence': _mixed_edge()['evidence']}],
            rows,
        )
        html = open(path, encoding='utf-8').read()
        self.assertIn('nstInspectLinkRowByIndex', html)
        self.assertIn('>Inspect</th>', html)
        self.assertIn('id="nst-evidence-inspector"', html)
        self.assertIn('nstWhyThisLink', html)
        self.assertIn('keydown', html)
        self.assertIn('Escape', html)

    def test_keyboard_focus_hooks_present(self):
        nodes = [
            {'id': 'SW1', 'ip': '10.0.0.1', 'is_scanned': True},
            {'id': 'SW2', 'ip': '10.0.0.2', 'is_scanned': True},
        ]
        path = os.path.join(tempfile.mkdtemp(), 'a11y.html')
        generate_discovery_html(path, nodes, [_mixed_edge()])
        html = open(path, encoding='utf-8').read()
        self.assertIn('nst-ev-inspect-btn:focus', html)
        self.assertIn('aria-label="Close evidence inspector"', html)
        self.assertIn('nstCloseEvidenceInspector', html)


if __name__ == '__main__':
    unittest.main()
