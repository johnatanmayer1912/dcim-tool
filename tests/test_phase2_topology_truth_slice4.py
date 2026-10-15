"""Phase 2 slice-4 — read-only topology evidence inspector.

Fixture-only. No live vendor SSH. No secrets in inspector output.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.discovery_graph import make_observation_evidence
from utils.discovery_map_formatter import build_vis_payload, generate_discovery_html
from utils.evidence_inspector import build_evidence_inspector_model
from utils.topo_map_shell import render_topology_page


class TestEvidenceInspectorModel(unittest.TestCase):
    def test_normal_edge_with_one_evidence(self):
        edge = {
            'from': 'SW1', 'to': 'SW2', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
            'protocol': 'CDP', 'confidence': 'High', 'freshness': 'current',
            'evidence': [make_observation_evidence(
                protocol='CDP', vendor='cisco', command='show cdp neighbors detail',
                collected_at='2026-08-20T10:00:00Z', local_port='Gi0/1', remote_port='Gi0/2',
            )],
        }
        m = build_evidence_inspector_model(edge)
        self.assertTrue(m['read_only'])
        self.assertTrue(m['has_evidence'])
        self.assertEqual(m['evidence_count'], 1)
        self.assertEqual(m['endpoints']['from'], 'SW1')
        self.assertEqual(len(m['sections']['observed']), 1)
        obs = m['sections']['observed'][0]
        self.assertEqual(obs['protocol'], 'CDP')
        self.assertEqual(obs['vendor'], 'cisco')
        self.assertIn('cdp', obs['command'].lower())
        self.assertEqual(obs['collected_at_display'], '2026-08-20T10:00:00Z')
        self.assertTrue(obs['timestamp_known'])

    def test_mixed_freshness_and_conflict(self):
        edge = {
            'from': 'A', 'to': 'B', 'f_port': 'Eth1/1', 't_port': 'Gi1/1',
            'protocol': 'CDP+LLDP', 'freshness': 'mixed', 'freshness_conflict': True,
            'freshness_note': 'supporting observations differ in freshness',
            'contradictions': ['mixed-freshness evidence timestamps', 'port mismatch Eth1/1 vs Gi0/1'],
            'evidence': [
                make_observation_evidence(
                    protocol='CDP', vendor='cisco', collected_at='2026-08-20T10:00:00Z',
                    local_port='Eth1/1', remote_port='Gi1/1',
                ),
                make_observation_evidence(
                    protocol='LLDP', vendor='cisco', collected_at='2026-08-18T10:00:00Z',
                    local_port='Eth1/1', remote_port='Gi0/1',
                ),
            ],
        }
        annotate = edge['evidence']
        annotate[0]['freshness'] = 'current'
        annotate[1]['freshness'] = 'stale'
        m = build_evidence_inspector_model(edge)
        self.assertTrue(m['freshness']['conflict'])
        self.assertEqual(m['freshness']['state'], 'mixed')
        self.assertEqual(m['evidence_count'], 2)
        self.assertIn('mixed-freshness evidence timestamps', m['sections']['conflicts'])
        self.assertIn('port mismatch Eth1/1 vs Gi0/1', m['sections']['conflicts'])
        protos = {i['protocol'] for i in m['evidence_items']}
        self.assertEqual(protos, {'CDP', 'LLDP'})

    def test_irb_supporting_context_not_cable(self):
        edge = {
            'from': 'gw', 'to': 'leaf', 'f_port': 'irb.100', 't_port': 'ge-0/0/1',
            'protocol': 'LLDP', 'not_physical': True, 'edge_kind': 'irb-adjacency',
            'evidence': [make_observation_evidence(
                protocol='LLDP', vendor='juniper', command='show lldp neighbors detail',
                local_port='irb.100', remote_port='ge-0/0/1',
                port_role='l3_irb', not_physical=True, parse_source='detail',
            )],
        }
        m = build_evidence_inspector_model(edge)
        self.assertIn('not cable', m['classification']['cable_claim'].lower())
        self.assertEqual(len(m['sections']['supporting_context']), 1)
        self.assertEqual(len(m['sections']['observed']), 0)
        self.assertTrue(m['sections']['supporting_context'][0]['not_physical'])
        self.assertTrue(any('non-cable' in x.lower() for x in m['sections']['inferred_conclusions']))

    def test_no_evidence_and_missing_timestamp(self):
        empty = build_evidence_inspector_model({
            'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2', 'protocol': 'CDP',
        })
        self.assertFalse(empty['has_evidence'])
        self.assertEqual(empty['evidence_count'], 0)
        self.assertIsNotNone(empty['empty_message'])

        missing_ts = build_evidence_inspector_model({
            'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
            'protocol': 'LLDP', 'freshness': 'unknown',
            'evidence': [make_observation_evidence(protocol='LLDP', vendor='cisco')],
        })
        item = missing_ts['evidence_items'][0]
        self.assertFalse(item['timestamp_known'])
        self.assertEqual(item['collected_at_display'], 'unknown')
        self.assertEqual(item['freshness'], 'unknown')

    def test_malformed_evidence_and_no_secrets(self):
        edge = {
            'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
            'protocol': 'CDP',
            'password': 'super-secret',
            'credential_id': 'cred-1',
            'evidence': ['not-a-dict', make_observation_evidence(protocol='CDP', vendor='cisco')],
        }
        m = build_evidence_inspector_model(edge)
        self.assertEqual(m['evidence_count'], 2)
        self.assertTrue(m['sections']['unknowns'][0].get('malformed'))
        # Model must not copy secret fields into the inspector view
        self.assertNotIn('password', m)
        self.assertNotIn('credential_id', m)
        self.assertNotIn('super-secret', str(m))

    def test_read_only_flag(self):
        m = build_evidence_inspector_model({'from': 'A', 'to': 'B'})
        self.assertTrue(m['read_only'])


class TestEvidenceInspectorHtmlContract(unittest.TestCase):
    def _discovery_html(self, edges=None):
        nodes = [
            {'id': 'SW1', 'ip': '10.0.0.1', 'is_scanned': True, 'scan_state': 'scanned'},
            {'id': 'SW2', 'ip': '10.0.0.2', 'is_scanned': True, 'scan_state': 'scanned'},
        ]
        edges = edges or [{
            'from': 'SW1', 'to': 'SW2', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
            'protocol': 'CDP', 'freshness': 'mixed', 'freshness_conflict': True,
            'trust_tier': 'Medium', 'trust_note': 'dual protocol',
            'contradictions': ['mixed-freshness evidence timestamps'],
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
        }]
        path = os.path.join(tempfile.mkdtemp(), 'ev_insp.html')
        generate_discovery_html(path, nodes, edges)
        return open(path, encoding='utf-8').read()

    def test_inspector_shell_and_a11y(self):
        html = self._discovery_html()
        self.assertIn('id="nst-evidence-inspector"', html)
        self.assertIn('role="dialog"', html)
        self.assertIn('aria-modal="true"', html)
        self.assertIn('aria-labelledby="nst-evidence-title"', html)
        self.assertIn('id="nst-evidence-close"', html)
        self.assertIn('aria-label="Close evidence inspector"', html)
        self.assertIn('nstOpenEvidenceInspector', html)
        self.assertIn('nstCloseEvidenceInspector', html)
        self.assertIn('nstBuildEvidenceInspectorModel', html)
        self.assertIn('nstRenderEvidenceInspectorHtml', html)
        self.assertIn('Inspect evidence', html)
        self.assertIn('Read-only inspector', html)
        self.assertIn('Supporting context (L3/IRB/VLAN)', html)
        self.assertIn('timestamp unknown', html)
        # No edit/mutate affordances
        self.assertNotIn('Delete evidence', html)
        self.assertNotIn('Promote trust', html)
        self.assertNotIn('Edit evidence', html)

    def test_vis_payload_preserves_evidence_and_trust(self):
        nodes = [
            {'id': 'SW1', 'ip': '10.0.0.1', 'is_scanned': True},
            {'id': 'SW2', 'ip': '10.0.0.2', 'is_scanned': True},
        ]
        edges = [{
            'from': 'SW1', 'to': 'SW2', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
            'protocol': 'CDP', 'trust_tier': 'High', 'trust_note': 'bidirectional',
            'freshness': 'current',
            'evidence': [make_observation_evidence(
                protocol='CDP', vendor='cisco', collected_at='2026-08-20T12:00:00Z',
                local_port='Gi0/1', remote_port='Gi0/2', command='show cdp neighbors detail',
            )],
        }]
        _, edges_json, _ = build_vis_payload(nodes, edges)
        ej = edges_json[0]
        self.assertEqual(ej['trust_tier'], 'High')
        self.assertEqual(ej['trust_note'], 'bidirectional')
        self.assertEqual(len(ej['evidence']), 1)
        self.assertEqual(ej['evidence'][0]['collected_at'], '2026-08-20T12:00:00Z')
        self.assertEqual(ej['evidence'][0]['vendor'], 'cisco')

    def test_topo_shell_also_embeds_inspector(self):
        path = os.path.join(tempfile.mkdtemp(), 'topo.html')
        render_topology_page(
            path, 'Test',
            [{'id': 'a', 'label': 'a', 'x': 0, 'y': 0, 'fixed': True,
              'color': {'background': '#3b82f6'}, 'font': {'color': '#fff'}, 'shape': 'box'}],
            [{'id': 'e0', 'from': 'a', 'to': 'b', 'label': 'x', 'protocol': 'CDP',
              'color': {'color': '#6366f1'}, 'width': 2}],
            [{'from': 'a', 'to': 'b', 'local_port': 'Gi0/1', 'remote_port': 'Gi0/2',
              'protocol': 'CDP', 'trust_tier': 'inferred'}],
        )
        html = open(path, encoding='utf-8').read()
        self.assertIn('id="nst-evidence-inspector"', html)
        self.assertIn('nstOpenEvidenceInspector', html)
        self.assertIn('keydown', html)
        self.assertIn('Escape', html)

    def test_irb_edge_in_html_payload(self):
        html = self._discovery_html(edges=[{
            'from': 'gw', 'to': 'leaf', 'f_port': 'irb.100', 't_port': 'ge-0/0/1',
            'protocol': 'LLDP', 'not_physical': True, 'edge_kind': 'irb-adjacency',
            'freshness': 'current',
            'evidence': [make_observation_evidence(
                protocol='LLDP', vendor='juniper', local_port='irb.100',
                remote_port='ge-0/0/1', port_role='l3_irb', not_physical=True,
                collected_at='2026-08-20T09:00:00Z',
            )],
        }])
        self.assertIn('irb.100', html)
        self.assertIn('not_physical', html)
        self.assertIn('l3_irb', html)
        self.assertIn('Supporting context (L3/IRB/VLAN)', html)

    def test_no_secret_fields_in_generated_map(self):
        nodes = [
            {'id': 'SW1', 'ip': '10.0.0.1', 'is_scanned': True},
            {'id': 'SW2', 'ip': '10.0.0.2', 'is_scanned': True},
        ]
        edges = [{
            'from': 'SW1', 'to': 'SW2', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
            'protocol': 'CDP',
            'evidence': [make_observation_evidence(protocol='CDP', vendor='cisco')],
        }]
        path = os.path.join(tempfile.mkdtemp(), 'safe.html')
        generate_discovery_html(path, nodes, edges)
        html = open(path, encoding='utf-8').read()
        # Inspector must not introduce credential UI or vault controls
        self.assertNotIn('credential_id', html)
        self.assertNotIn('Unlock vault', html)
        self.assertIn('Read-only inspector', html)


class TestMapStillWorks(unittest.TestCase):
    def test_existing_why_link_and_layers_intact(self):
        nodes = [
            {'id': 'SW1', 'ip': '10.0.0.1', 'is_scanned': True, 'scan_state': 'scanned'},
            {'id': 'SW2', 'ip': '10.0.0.2', 'is_scanned': False, 'scan_state': 'neighbor_only'},
        ]
        edges = [{
            'from': 'SW1', 'to': 'SW2', 'f_port': 'Eth1/1', 't_port': 'Gi1/1', 'protocol': 'CDP',
        }]
        path = os.path.join(tempfile.mkdtemp(), 'compat.html')
        generate_discovery_html(path, nodes, edges)
        html = open(path, encoding='utf-8').read()
        self.assertIn('nstWhyThisLink', html)
        self.assertIn('id="nst-why-link"', html)
        self.assertIn('nstSetLayer', html)
        self.assertIn('nstBlastRadius', html)
        self.assertIn('discBootMap', html)


if __name__ == '__main__':
    unittest.main()
