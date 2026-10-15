"""Map acceptance hardening — HTML + graph contracts. Fixture/simulation only."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.discovery_graph import canonicalize_discovery_graph, merge_nodes
from utils.discovery_map_formatter import generate_discovery_html
from utils.map_acceptance import (
    BLOCKED_CONDITIONS,
    SUPPORTED_VIEWS,
    assert_html_map_acceptance,
    blast_neighborhood,
    identity_ids,
)
from utils.topo_map_shell import (
    NST_BLAST_SEMANTICS,
    NST_STALE_HOURS,
    OFFLINE_VIS_MISSING_SCRIPT,
    link_rows_from_edges,
    render_topology_page,
)


class TestMapAcceptanceViews(unittest.TestCase):
    def test_supported_views(self):
        self.assertEqual(SUPPORTED_VIEWS, ('physical', 'l2', 'l3', 'overlay'))
        self.assertTrue(BLOCKED_CONDITIONS)

    def _html(self, nodes=None, edges=None, extra=None):
        nodes = nodes or [
            {'id': 'sw1', 'ip': '10.0.0.1', 'is_scanned': True, 'scan_state': 'scanned'},
            {'id': 'sw2', 'ip': '10.0.0.2', 'is_scanned': False, 'scan_state': 'neighbor_only'},
        ]
        edges = edges or [
            {'from': 'sw1', 'to': 'sw2', 'f_port': 'Eth1/1', 't_port': 'Eth1/2', 'protocol': 'CDP'},
        ]
        path = os.path.join(tempfile.mkdtemp(), 'map.html')
        generate_discovery_html(path, nodes, edges, extra_meta=extra)
        return open(path, encoding='utf-8').read()

    def test_shell_acceptance_and_blocked_overlay_claims(self):
        html = self._html()
        assert_html_map_acceptance(html)
        self.assertIn('Hostnames that look like leaf, spine, or vtep', html)
        self.assertIn('not proof the fabric has no overlay', html)
        self.assertNotIn('VTEP discovered', html)

    def test_blast_1_and_2_hop_neighborhood_not_path(self):
        edges = [
            {'from': 'A', 'to': 'B'},
            {'from': 'B', 'to': 'C'},
        ]
        one = blast_neighborhood(edges, 'A', 1)
        two = blast_neighborhood(edges, 'A', 2)
        self.assertEqual(set(one), {'A', 'B'})
        self.assertEqual(set(two), {'A', 'B', 'C'})
        html = self._html()
        self.assertIn(NST_BLAST_SEMANTICS, html)
        self.assertIn('not a forwarding path', html)
        self.assertIn('nstBlastRadius(2)', html)

    def test_stale_threshold_embedded(self):
        self.assertEqual(NST_STALE_HOURS, 24)
        html = self._html()
        self.assertIn(f'window.NST_STALE_HOURS = {NST_STALE_HOURS}', html)

    def test_conflict_strip_wording(self):
        html = self._html()
        self.assertIn('CONFLICT', html)
        self.assertIn('nstWhyThisLink', html)

    def test_identity_conflict_persists_in_html(self):
        nodes = [
            {'id': 'EDGE-01', 'ip': '10.0.0.1', 'serial': 'SN-A', 'is_scanned': True},
            {'id': 'EDGE-01', 'ip': '10.0.0.9', 'serial': 'SN-B', 'is_scanned': True},
        ]
        merged, _alias = merge_nodes(nodes)
        self.assertEqual(len(identity_ids(merged)), 2)
        self.assertTrue(any(n.get('identity_conflict') for n in merged))
        html = self._html(nodes=merged, edges=[])
        for nid in identity_ids(merged):
            self.assertIn(nid, html)
        self.assertIn('identity_conflict', html)

    def test_bundle_member_stability_in_canonicalize(self):
        nodes = [
            {'id': 'A', 'ip': '10.0.0.1', 'is_scanned': True},
            {'id': 'B', 'ip': '10.0.0.2', 'is_scanned': True},
        ]
        edges = [
            {'from': 'A', 'to': 'B', 'f_port': 'Eth1/1', 't_port': 'Eth1/1',
             'protocol': 'CDP', 'oper_status': 'down'},
            {'from': 'A', 'to': 'B', 'f_port': 'Po1', 't_port': 'Po1',
             'protocol': 'CDP', 'oper_status': 'up'},
        ]
        _m, rewired, _r = canonicalize_discovery_graph(nodes, edges)
        self.assertEqual(len(rewired), 2)
        self.assertTrue(any(e.get('bundle_kind') == 'bundle' for e in rewired))
        self.assertTrue(any(e.get('degraded') for e in rewired))

    def test_partial_graph_does_not_invent_edges(self):
        nodes = [
            {'id': 'seed', 'ip': '10.0.0.1', 'is_scanned': True, 'scan_state': 'scanned'},
            {'id': 'ghost', 'ip': '10.0.0.2', 'is_scanned': False, 'scan_state': 'failed'},
        ]
        edges = [
            {'from': 'seed', 'to': 'ghost', 'f_port': 'Eth1/1', 't_port': 'Eth1/1', 'protocol': 'LLDP'},
        ]
        html = self._html(nodes, edges, extra={'cancelled': True, 'collection_status': 'cancelled', 'partial': True})
        self.assertIn('CANCELLED collection — not complete truth', html)
        self.assertEqual(html.count('Eth1/1'), html.count('Eth1/1'))
        self.assertNotIn('"from": "ghost", "to": "invented"', html)

    def test_overlay_empty_forbids_hostname_inference(self):
        nodes = [
            {'id': 'leaf-01', 'ip': '10.0.0.1', 'is_scanned': True},
            {'id': 'spine-01', 'ip': '10.0.0.2', 'is_scanned': True},
            {'id': 'vtep-01', 'ip': '10.0.0.3', 'is_scanned': False},
        ]
        html = self._html(nodes, [])
        self.assertIn('not</em> overlay evidence', html)
        self.assertIn('not proof the fabric has no overlay', html)
        self.assertNotIn('VTEP discovered', html)

    def test_vis_fallback_is_offline_honest(self):
        self.assertNotIn('unpkg', OFFLINE_VIS_MISSING_SCRIPT.lower())
        self.assertNotIn('https://', OFFLINE_VIS_MISSING_SCRIPT)
        self.assertIn('NST_VIS_MISSING', OFFLINE_VIS_MISSING_SCRIPT)


class TestTopoPageAcceptance(unittest.TestCase):
    def test_render_topology_page_layers(self):
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as tf:
            path = tf.name
        try:
            render_topology_page(
                path, 'Test',
                [{'id': 'a', 'label': 'a', 'x': 0, 'y': 0, 'fixed': True}],
                [{'id': 'e0', 'from': 'a', 'to': 'b'}],
                link_rows_from_edges([{'from': 'a', 'to': 'b', 'f_port': 'e1', 't_port': 'e2'}]),
            )
            html = open(path, encoding='utf-8').read()
            assert_html_map_acceptance(html)
        finally:
            os.unlink(path)


if __name__ == '__main__':
    unittest.main()
