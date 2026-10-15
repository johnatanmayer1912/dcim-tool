"""Phase 2 slice-6 — map ↔ Link Inventory selection sync.

Fixture-only. No live vendor SSH.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.discovery_graph import make_observation_evidence
from utils.discovery_map_formatter import build_vis_payload, generate_discovery_html
from utils.evidence_inspector import (
    link_row_as_inspector_edge,
    topology_relation_key,
)
from utils.topo_map_shell import link_rows_from_edges, render_topology_page


class TestTopologyRelationKey(unittest.TestCase):
    def test_undirected_and_stable(self):
        a = {'from': 'SW1', 'to': 'SW2', 'f_port': 'Gi0/1', 't_port': 'Gi0/2'}
        b = {'from': 'SW2', 'to': 'SW1', 'local_port': 'Gi0/2', 'remote_port': 'Gi0/1'}
        self.assertEqual(topology_relation_key(a), topology_relation_key(b))
        self.assertTrue(topology_relation_key(a))

    def test_parallel_links_distinct(self):
        e1 = {'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/1'}
        e2 = {'from': 'A', 'to': 'B', 'f_port': 'Gi0/2', 't_port': 'Gi0/2'}
        self.assertNotEqual(topology_relation_key(e1), topology_relation_key(e2))

    def test_irb_kind_distinct_from_l2(self):
        phys = {'from': 'gw', 'to': 'leaf', 'f_port': 'ge-0/0/0', 't_port': 'ge-0/0/1'}
        irb = {
            'from': 'gw', 'to': 'leaf', 'f_port': 'irb.100', 't_port': 'ge-0/0/1',
            'not_physical': True, 'edge_kind': 'irb-adjacency',
        }
        self.assertNotEqual(topology_relation_key(phys), topology_relation_key(irb))
        self.assertIn('irb-adjacency', topology_relation_key(irb))

    def test_empty_and_no_secrets(self):
        self.assertEqual(topology_relation_key({}), '')
        self.assertEqual(topology_relation_key(None), '')
        key = topology_relation_key({
            'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
            'password': 'secret', 'credential_id': 'c1',
        })
        self.assertNotIn('secret', key)
        self.assertNotIn('credential', key)

    def test_row_and_edge_share_key(self):
        edge = {
            'from': 'SW1', 'to': 'SW2', 'f_port': 'Eth1/1', 't_port': 'Gi1/1',
            'protocol': 'CDP',
            'evidence': [make_observation_evidence(protocol='CDP', vendor='cisco')],
        }
        row = link_rows_from_edges([edge])[0]
        self.assertTrue(row.get('relation_key'))
        self.assertEqual(row['relation_key'], topology_relation_key(edge))
        adapted = link_row_as_inspector_edge(row)
        self.assertEqual(adapted['relation_key'], row['relation_key'])


class TestVisPayloadRelationKey(unittest.TestCase):
    def test_vis_edge_and_link_row_keys_match(self):
        nodes = [
            {'id': 'SW1', 'ip': '10.0.0.1', 'is_scanned': True},
            {'id': 'SW2', 'ip': '10.0.0.2', 'is_scanned': True},
        ]
        edges = [{
            'from': 'SW1', 'to': 'SW2', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
            'protocol': 'CDP',
        }]
        _, edges_json, link_rows = build_vis_payload(nodes, edges)
        self.assertEqual(edges_json[0]['relation_key'], link_rows[0]['relation_key'])

    def test_legacy_payload_without_key_still_renders(self):
        # link_rows_from_edges always adds key when endpoints exist; empty hosts stay empty
        rows = link_rows_from_edges([{'protocol': 'CDP'}])
        self.assertEqual(rows[0].get('relation_key', ''), '')


class TestSelectionSyncHtmlContract(unittest.TestCase):
    def test_discovery_html_embeds_sync_hooks(self):
        nodes = [
            {'id': 'SW1', 'ip': '10.0.0.1', 'is_scanned': True, 'scan_state': 'scanned'},
            {'id': 'SW2', 'ip': '10.0.0.2', 'is_scanned': True, 'scan_state': 'scanned'},
        ]
        edges = [{
            'from': 'SW1', 'to': 'SW2', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
            'protocol': 'LLDP',
            'evidence': [make_observation_evidence(
                protocol='LLDP', vendor='cisco', collected_at='2026-08-20T10:00:00Z',
                local_port='Gi0/1', remote_port='Gi0/2',
            )],
        }]
        path = os.path.join(tempfile.mkdtemp(), 'sync.html')
        generate_discovery_html(path, nodes, edges)
        html = open(path, encoding='utf-8').read()
        self.assertIn('nstRelationKey', html)
        self.assertIn('nstSyncHighlightRelation', html)
        self.assertIn('nstClearRelationSync', html)
        self.assertIn('nst-link-row-selected', html)
        self.assertIn('data-relation-key', html)
        self.assertIn('aria-selected', html)
        self.assertIn('_nstSyncSelecting', html)
        # inspector path intact
        self.assertIn('nstWhyThisLink', html)
        self.assertIn('nstInspectLinkRowByIndex', html)
        self.assertIn('nstOpenEvidenceInspector', html)
        self.assertIn('Read-only inspector', html)
        self.assertNotIn('Promote trust', html)
        self.assertNotIn('credential_id', html)
        # relation key present in embedded JSON
        key = topology_relation_key(edges[0])
        self.assertIn(key, html)

    def test_topo_shell_sync_hooks(self):
        path = os.path.join(tempfile.mkdtemp(), 'topo.html')
        edge = {'from': 'a', 'to': 'b', 'f_port': 'e1', 't_port': 'e2', 'protocol': 'CDP'}
        rows = link_rows_from_edges([edge])
        render_topology_page(
            path, 'Test',
            [{'id': 'a', 'label': 'a', 'x': 0, 'y': 0, 'fixed': True,
              'color': {'background': '#3b82f6'}, 'font': {'color': '#fff'}, 'shape': 'box'}],
            [{'id': 'e0', 'from': 'a', 'to': 'b', 'label': 'x', 'protocol': 'CDP',
              'relation_key': rows[0]['relation_key'],
              'color': {'color': '#6366f1'}, 'width': 2}],
            rows,
        )
        html = open(path, encoding='utf-8').read()
        self.assertIn('nstSyncHighlightRelation', html)
        self.assertIn('nstClearRelationSync', html)
        self.assertIn('data-relation-key', html)


if __name__ == '__main__':
    unittest.main()
