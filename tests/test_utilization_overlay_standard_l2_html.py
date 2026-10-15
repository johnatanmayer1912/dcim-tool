"""Standard L2 HTML contract for replay utilization overlay."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.report_formatter import generate_topology_html
from utils.utilization_overlay.model import load_replay_overlay

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, 'tests', 'fixtures', 'utilization', 'replay_standard_l2.json')


def _nodes():
    return [
        {
            'id': 'CORE-01', 'label': 'CORE-01', 'role': 'core', 'level': 0,
            'shape': 'box', 'color': {'background': '#c0392b', 'border': '#333'},
            'font': {'color': '#fff'},
        },
        {
            'id': 'DIST-N1', 'label': 'DIST-N1', 'role': 'distribution', 'level': 1,
            'shape': 'box', 'color': {'background': '#e67e22', 'border': '#333'},
            'font': {'color': '#fff'},
        },
    ]


def _edges():
    return [{
        'id': 'e0', 'from': 'CORE-01', 'to': 'DIST-N1',
        'f_port': 'Te1/0/1', 't_port': 'Te1/1/1', 'label': '',
        'map_label': 'Te1/0/1 ↔ Te1/1/1',
        'type': 'standard',
        'trust_tier': 'high',
        'edge_data': {
            'from': 'CORE-01', 'to': 'DIST-N1',
            'f_port': 'Te1/0/1', 't_port': 'Te1/1/1',
            'type': 'standard', 'confidence': 'High', 'trust_tier': 'high',
            'f_int_data': {'vlan': 'trunk', 'speed': '10G', 'status': 'up'},
        },
        'color': '#607d8b', 'width': 2,
    }]


def _render(overlay=None):
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as tf:
        path = tf.name
    try:
        generate_topology_html(
            path, 2, 1,
            json.dumps(_nodes()), json.dumps(_edges()),
            '/* vis stub */',
            map_mode='all',
            utilization_overlay=overlay,
        )
        return open(path, encoding='utf-8').read()
    finally:
        os.unlink(path)


class TestStandardL2OverlayHtml(unittest.TestCase):
    def test_overlay_off_path_preserves_standard_map(self):
        html = _render(None)
        self.assertIn('nst-standard-split', html)
        self.assertIn('nstBootStandardMap', html)
        self.assertIn('__NST_LINKS__', html)
        self.assertIn('Utilization overlay', html)
        self.assertIn('Replay snapshot — not a live poll', html)
        self.assertIn('Live SSH', html)
        self.assertNotIn('snmp sample', html.lower())
        self.assertIn('"available": false', html)
        # vis topology payload still has the original edge
        self.assertIn('"from": "CORE-01"', html)
        self.assertIn('"to": "DIST-N1"', html)
        self.assertIn('"trust_tier": "high"', html)

    def test_overlay_on_embed_paints_without_new_edges(self):
        html = _render(load_replay_overlay(FIXTURE))
        self.assertIn('"available": true', html)
        self.assertIn('"ok": true', html)
        self.assertIn('core-01|te1/0/1|dist-n1|te1/1/1|l2', html)
        self.assertIn('nstSetUtilOverlay', html)
        self.assertIn('unsampled (gray dashed — not down)', html)
        self.assertIn('70–90%', html)
        self.assertIn('Unmapped interfaces (not drawn)', html)
        self.assertIn('Paint is not topology', html)
        self.assertIn('Replay snapshot — not a live poll', html)
        self.assertIn('"mode": "replay"', html)
        self.assertIn('"id": "e0"', html)
        # join key is cable_key, not vis id
        self.assertNotIn('"cable_key": "e0"', html)
        self.assertIn('no_matching_edge', html)
        self.assertIn('nst-util-legend', html)

    def test_invalid_fixture_does_not_break_base_map(self):
        html = _render({'schema': 'nope'})
        self.assertIn('nst-standard-split', html)
        self.assertIn('nstBootStandardMap', html)
        self.assertIn('"available": false', html)
        self.assertTrue(
            'document missing' in html
            or 'unsupported schema' in html
            or 'utilization overlay unavailable' in html
        )
        self.assertIn('"from": "CORE-01"', html)
        self.assertIn('"to": "DIST-N1"', html)

    def test_overlay_does_not_claim_live_or_snmp_poll(self):
        html = _render(load_replay_overlay(FIXTURE))
        self.assertNotIn('live poll', html.lower().replace('not a live poll', ''))
        self.assertNotIn('snmp sample', html.lower())
        self.assertIn('not a live poll', html.lower())

    def test_vpc_mode_does_not_require_overlay(self):
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as tf:
            path = tf.name
        try:
            generate_topology_html(
                path, 2, 1,
                json.dumps(_nodes()), json.dumps(_edges()),
                '/* vis stub */',
                map_mode='vpc',
            )
            html = open(path, encoding='utf-8').read()
            self.assertNotIn('nstSetUtilOverlay', html)
        finally:
            os.unlink(path)


if __name__ == '__main__':
    unittest.main()
