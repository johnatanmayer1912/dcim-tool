"""Phase 2 slice-7 — conditional Link Inventory reveal on map selection.

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
from utils.evidence_inspector import topology_relation_key
from utils.topo_map_shell import link_rows_from_edges, render_topology_page


class TestConditionalLinkInventoryReveal(unittest.TestCase):
    def _discovery_html(self):
        nodes = [
            {'id': 'SW1', 'ip': '10.0.0.1', 'is_scanned': True, 'scan_state': 'scanned'},
            {'id': 'SW2', 'ip': '10.0.0.2', 'is_scanned': True, 'scan_state': 'scanned'},
        ]
        edges = [{
            'from': 'SW1', 'to': 'SW2', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
            'protocol': 'CDP',
            'evidence': [make_observation_evidence(
                protocol='CDP', vendor='cisco', local_port='Gi0/1', remote_port='Gi0/2',
            )],
        }]
        path = os.path.join(tempfile.mkdtemp(), 'reveal.html')
        generate_discovery_html(path, nodes, edges)
        return open(path, encoding='utf-8').read(), topology_relation_key(edges[0])

    def test_reveal_helpers_embedded(self):
        html, key = self._discovery_html()
        self.assertIn('nstRevealLinkInventoryIfNeeded', html)
        self.assertIn('nstLinkInventoryIsHidden', html)
        self.assertIn('discCcTab', html)
        self.assertIn("discCcTab('links')", html)
        self.assertIn('revealInventory', html)
        # sync still present
        self.assertIn('nstSyncHighlightRelation', html)
        self.assertIn('nst-link-row-selected', html)
        self.assertIn(key, html)

    def test_reveal_only_when_matched_and_not_from_table(self):
        html, _ = self._discovery_html()
        # Map path uses selectMap:false then reveal; table path uses selectMap:true
        self.assertIn('!opts.selectMap && opts.revealInventory !== false', html)
        self.assertIn('nstRevealLinkInventoryIfNeeded()', html)
        # Clear/reset must not hide inventory
        self.assertNotIn("discCcTab('overview')", html.split('nstClearRelationSync')[1][:800]
                         if 'nstClearRelationSync' in html else '')
        clear_fn = html.split('function nstClearRelationSync')[1].split('function ')[0]
        self.assertNotIn('discCcTab', clear_fn)
        self.assertNotIn('topoViewTab', clear_fn)

    def test_discovery_panels_and_no_focus_steal(self):
        html, _ = self._discovery_html()
        self.assertIn('id="disc-panel-links"', html)
        self.assertIn('id="disc-tab-links"', html)
        reveal_fn = html.split('function nstRevealLinkInventoryIfNeeded')[1].split('function ')[0]
        self.assertNotIn('.focus(', reveal_fn)
        self.assertIn("discCcTab('links')", reveal_fn)

    def test_standard_topo_shell_uses_topoViewTab(self):
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
        self.assertIn('nstRevealLinkInventoryIfNeeded', html)
        self.assertIn('topoViewTab', html)
        self.assertIn("topoViewTab('links')", html)
        self.assertIn('id="topo-link-inventory"', html)
        self.assertIn('nstClearRelationSync', html)
        # inspector + sync intact
        self.assertIn('nstWhyThisLink', html)
        self.assertIn('nstSyncHighlightRelation', html)
        self.assertIn('Read-only inspector', html)
        self.assertNotIn('credential_id', html)

    def test_hidden_check_is_conservative(self):
        html, _ = self._discovery_html()
        hidden_fn = html.split('function nstLinkInventoryIsHidden')[1].split('function ')[0]
        # Returns null when no surface — callers treat !== true as no-op
        self.assertIn('return null', hidden_fn)
        self.assertIn('disc-panel-links', hidden_fn)
        self.assertIn('topo-link-inventory', hidden_fn)


if __name__ == '__main__':
    unittest.main()
