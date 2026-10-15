"""Discovery Command Center host for the existing utilization overlay.

Viewer only: paints existing L2 cable keys. EVPN / incomplete stay non-edges.
Standard L2 replay/live path is not modified by this host adapter.
"""
from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.discovery_map_formatter import build_vis_payload, generate_discovery_html
from utils.report_formatter import generate_topology_html
from utils.utilization_overlay.discovery_host import (
    bind_overlay_to_discovery,
    discovery_embed_payload,
)
from utils.utilization_overlay.join import is_paint_eligible_l2_edge, topology_fingerprint
from utils.utilization_overlay.model import load_overlay_document, load_replay_overlay

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPLAY = os.path.join(ROOT, 'tests', 'fixtures', 'utilization', 'replay_standard_l2.json')
LIVE = os.path.join(ROOT, 'tests', 'fixtures', 'utilization', 'live_standard_l2.json')


def _nodes():
    return [
        {
            'id': 'CORE-01',
            'ip': '10.0.0.1',
            'platform': 'N9K',
            'device_type': 'cisco_nxos',
            'depth': 0,
            'is_scanned': True,
            'scan_state': 'seed',
            'incomplete_observations': [{
                'incomplete': True,
                'edge_eligible': False,
                'hostname': '',
                'protocol': 'CDP',
                'local_port': '',
                'remote_port': '',
                'parse_warning': 'peer identity missing — not a cable',
            }],
        },
        {
            'id': 'DIST-N1',
            'ip': '10.0.0.2',
            'platform': 'C9300',
            'device_type': 'cisco_ios',
            'depth': 1,
            'is_scanned': True,
            'scan_state': 'scanned',
        },
    ]


def _edges():
    return [
        {
            'from': 'CORE-01',
            'to': 'DIST-N1',
            'f_port': 'Te1/0/1',
            't_port': 'Te1/1/1',
            'protocol': 'CDP',
            'trust_tier': 'high',
            'layer': 'l2',
        },
        {
            'from': 'CORE-01',
            'to': 'DIST-N1',
            'f_port': 'nve1',
            't_port': 'nve1',
            'protocol': 'EVPN',
            'layer': 'overlay',
            'not_physical': True,
            'edge_kind': 'evpn-peer',
            'trust_tier': 'inferred',
        },
    ]


def _payload_from_html(html: str) -> dict:
    marker = 'window.__NST_UTIL_PAYLOAD__ = '
    start = html.index(marker) + len(marker)
    payload, _end = json.JSONDecoder().raw_decode(html[start:])
    return payload


def _vis_edges_from_html(html: str) -> list:
    marker = 'var edges = new vis.DataSet('
    start = html.index(marker) + len(marker)
    edges, _end = json.JSONDecoder().raw_decode(html[start:])
    return edges


def _render_discovery(overlay=None, extra=None):
    extra_meta = dict(extra or {})
    if overlay is not None:
        extra_meta['utilization_overlay'] = overlay
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as tf:
        path = tf.name
    try:
        generate_discovery_html(path, _nodes(), _edges(), extra_meta=extra_meta)
        return open(path, encoding='utf-8').read()
    finally:
        os.unlink(path)


class TestDiscoveryOverlayBind(unittest.TestCase):
    def test_discovery_loads_overlay_json_and_paints_existing_cable_only(self):
        nodes_json, edges_json, _ = build_vis_payload(_nodes(), _edges())
        before = topology_fingerprint(edges_json)
        edge_n = len(edges_json)
        bound = bind_overlay_to_discovery(nodes_json, edges_json, REPLAY)
        self.assertTrue(bound.ok)
        self.assertTrue(bound.available)
        self.assertEqual(bound.mode, 'replay')
        self.assertIn('e0', bound.bindings)
        self.assertNotIn('e1', bound.bindings)
        self.assertEqual(bound.bindings['e0']['paint_state'], 'hot')
        self.assertNotEqual(bound.bindings['e0']['cable_key'], 'e0')
        self.assertFalse(is_paint_eligible_l2_edge(edges_json[1]))
        self.assertEqual(len(edges_json), edge_n)
        self.assertEqual(topology_fingerprint(edges_json), before)
        self.assertEqual(edges_json[0]['trust_tier'], 'high')
        self.assertEqual(edges_json[1]['trust_tier'], 'inferred')

    def test_evpn_and_incomplete_never_become_edges_or_bindings(self):
        nodes_json, edges_json, _ = build_vis_payload(_nodes(), _edges())
        vis_ids = [e['id'] for e in edges_json]
        self.assertEqual(vis_ids, ['e0', 'e1'])
        self.assertEqual(edges_json[1]['protocol'], 'EVPN')
        self.assertTrue(edges_json[1]['not_physical'])
        bound = bind_overlay_to_discovery(nodes_json, edges_json, REPLAY)
        payload = discovery_embed_payload(bound)
        self.assertEqual(payload['host'], 'discovery')
        self.assertIs(payload['live_controls'], False)
        self.assertNotIn('e1', payload['bindings'])
        from_to = {(e['from'], e['to'], e['f_port'], e['t_port']) for e in edges_json}
        self.assertEqual(len(from_to), 2)
        # Incomplete observations live on nodes, not vis edges.
        self.assertTrue(any(n.get('incomplete_observations') for n in _nodes()))
        self.assertEqual(len(edges_json), 2)

    def test_evpn_cable_key_in_overlay_fails_closed(self):
        doc = load_replay_overlay(REPLAY)
        doc = copy.deepcopy(doc)
        doc['paints'][0]['cable_key'] = 'core-01|nve1|dist-n1|nve1|l2'
        nodes_json, edges_json, _ = build_vis_payload(_nodes(), _edges())
        before = topology_fingerprint(edges_json)
        bound = bind_overlay_to_discovery(nodes_json, edges_json, doc)
        self.assertFalse(bound.ok)
        self.assertFalse(bound.available)
        self.assertEqual(bound.bindings, {})
        self.assertEqual(topology_fingerprint(edges_json), before)


class TestDiscoveryOverlayHtml(unittest.TestCase):
    def test_overlay_off_keeps_discovery_truth_model(self):
        html = _render_discovery(None)
        self.assertIn('discovery-command-center', html)
        self.assertIn('discCommandCenterInit', html)
        self.assertIn('Overlay layer = NVE/EVPN CLI peers only (not cables).', html)
        self.assertIn('Incomplete observations = diagnostics only (not map links).', html)
        self.assertIn('Utilization overlay', html)
        self.assertIn('Viewer only — Live SSH is Standard L2', html)
        self.assertNotIn('id="nst-util-live-btn"', html)
        payload = _payload_from_html(html)
        self.assertEqual(payload['host'], 'discovery')
        self.assertIs(payload['live_controls'], False)
        self.assertFalse(payload['available'])
        vis = _vis_edges_from_html(html)
        self.assertEqual(len(vis), 2)
        evpn = [e for e in vis if e.get('protocol') == 'EVPN'][0]
        self.assertEqual(evpn['color']['color'], '#a855f7')
        self.assertIn('not map links', html)
        self.assertIn('release_gate', html)
        self.assertIn('BLOCKED', html)

    def test_replay_overlay_paints_l2_only_and_lists_unmapped(self):
        html = _render_discovery(load_replay_overlay(REPLAY))
        payload = _payload_from_html(html)
        self.assertTrue(payload['ok'])
        self.assertTrue(payload['available'])
        self.assertEqual(payload['host'], 'discovery')
        self.assertIs(payload['live_controls'], False)
        self.assertEqual(payload['mode'], 'replay')
        self.assertIn('e0', payload['bindings'])
        self.assertNotIn('e1', payload['bindings'])
        self.assertIn('Replay snapshot — not a live poll', html)
        self.assertIn('Unmapped interfaces (not drawn)', html)
        self.assertIn('no_matching_edge', html)
        self.assertIn('nstUtilEdgeIsNonCable', html)
        vis = _vis_edges_from_html(html)
        self.assertEqual(len(vis), 2)
        self.assertEqual(vis[0]['from'], 'CORE-01')
        self.assertEqual(vis[0]['to'], 'DIST-N1')
        self.assertEqual(vis[0]['trust_tier'], 'high')
        self.assertEqual(vis[1]['protocol'], 'EVPN')
        self.assertEqual(vis[1]['color']['color'], '#a855f7')
        self.assertIn('incomplete observation', html.lower())
        self.assertNotIn('snmp sample', html.lower())
        self.assertIn('Release gate is unchanged', html)

    def test_live_overlay_json_is_viewer_only_on_discovery(self):
        html = _render_discovery(load_overlay_document(LIVE))
        payload = _payload_from_html(html)
        self.assertTrue(payload['available'])
        self.assertEqual(payload['mode'], 'live')
        self.assertIs(payload['live_controls'], False)
        self.assertNotIn('id="nst-util-live-btn"', html)
        self.assertIn('Live SSH counters — not SNMP', html)
        self.assertIn('e0', payload['bindings'])
        self.assertNotIn('e1', payload['bindings'])
        vis = _vis_edges_from_html(html)
        self.assertEqual(len(vis), 2)
        self.assertEqual(vis[1]['color']['color'], '#a855f7')

    def test_invalid_overlay_does_not_break_discovery_map(self):
        html = _render_discovery({'schema': 'nope'})
        self.assertIn('discovery-command-center', html)
        self.assertIn('discBootMap', html)
        payload = _payload_from_html(html)
        self.assertFalse(payload['available'])
        vis = _vis_edges_from_html(html)
        self.assertEqual(len(vis), 2)
        self.assertEqual(vis[0]['trust_tier'], 'high')


class TestStandardL2Unchanged(unittest.TestCase):
    def test_standard_l2_replay_html_still_has_live_controls(self):
        nodes = [
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
        edges = [{
            'id': 'e0', 'from': 'CORE-01', 'to': 'DIST-N1',
            'f_port': 'Te1/0/1', 't_port': 'Te1/1/1', 'label': '',
            'map_label': 'Te1/0/1 ↔ Te1/1/1',
            'type': 'standard',
            'trust_tier': 'high',
            'edge_data': {
                'from': 'CORE-01', 'to': 'DIST-N1',
                'f_port': 'Te1/0/1', 't_port': 'Te1/1/1',
                'type': 'standard', 'confidence': 'High', 'trust_tier': 'high',
            },
            'color': '#607d8b', 'width': 2,
        }]
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as tf:
            path = tf.name
        try:
            generate_topology_html(
                path, 2, 1,
                json.dumps(nodes), json.dumps(edges),
                '/* vis stub */',
                map_mode='all',
                utilization_overlay=load_replay_overlay(REPLAY),
            )
            html = open(path, encoding='utf-8').read()
        finally:
            os.unlink(path)
        payload = _payload_from_html(html)
        self.assertNotEqual(payload.get('host'), 'discovery')
        self.assertNotIn('live_controls', payload)
        self.assertIn('id="nst-util-live-btn"', html)
        self.assertIn('nst-standard-split', html)
        self.assertTrue(payload['available'])
        self.assertIn('e0', payload['bindings'])
        self.assertIn('Replay snapshot — not a live poll', html)


if __name__ == '__main__':
    unittest.main()
