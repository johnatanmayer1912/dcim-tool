"""Phase 5 slice 4 — map-shell incomplete surface + mandatory manifest registration.

Fixture-only. No live SSH. Incomplete remains non-edge-eligible.
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.plugins import network_discovery as nd
from utils.discovery_map_formatter import generate_discovery_html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'discovery')
MANIFEST = os.path.join(ROOT, 'tests', 'qa', 'MANDATORY_MANIFEST.yaml')


def _read(name: str) -> str:
    with open(os.path.join(FIX, name), encoding='utf-8') as f:
        return f.read()


class TestMapShellIncompleteSurface(unittest.TestCase):
    def test_discovery_html_embeds_sanitized_incompletes_not_edges(self):
        raw = nd._parse_cisco_cdp_detail(
            _read('phase5_ios_cdp_detail_truncated_no_interface.txt'), 'EDGE', None,
        )
        fin = nd._finalize_neighbor(dict(raw[0]))
        self.assertTrue(fin.get('incomplete'))
        self.assertFalse(fin.get('edge_eligible'))

        nodes = [{
            'id': 'EDGE-01',
            'ip': '10.0.0.1',
            'platform': 'C9300',
            'device_type': 'cisco_ios',
            'depth': 0,
            'is_scanned': True,
            'scan_state': 'scanned',
            'incomplete_observations': [fin],
        }]
        # Real link only — incompletes must not invent a second edge
        edges = [{
            'from': 'EDGE-01',
            'to': 'PEER-OK',
            'f_port': 'Gi1/0/1',
            't_port': 'Gi1/0/2',
            'protocol': 'CDP',
        }]
        # Peer-ok node for the real edge endpoint
        nodes.append({
            'id': 'PEER-OK',
            'ip': '10.0.0.2',
            'depth': 1,
            'is_scanned': False,
            'scan_state': 'neighbor_only',
        })

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'disc.html')
            generate_discovery_html(path, nodes, edges)
            html = open(path, encoding='utf-8').read()

        self.assertIn('incomplete_observation_count', html)
        self.assertIn('Incomplete observations (not map links)', html)
        self.assertIn('disc-incomplete-banner', html)
        self.assertIn('discRenderIncompleteBanner', html)
        self.assertIn('(unobserved)', html)
        self.assertIn('not drawn on the map', html)
        # Sanitized: no raw CDP fragment body
        self.assertNotIn('Device ID: TRUNC-PEER', html)
        # Real edge still present; truncated peer is not an edge endpoint in vis payload
        self.assertIn('PEER-OK', html)
        self.assertNotRegex(html, r'"from"\s*:\s*"EDGE-01"[^]]*TRUNC-PEER')

        # Count in meta/subtitle
        self.assertRegex(html, r'1 incomplete observation\(s\) — not map links')

    def test_map_shell_helpers_escape_and_legend(self):
        from utils.discovery_map_shell import discovery_command_center_body, discovery_light_css
        body = discovery_command_center_body('<div></div>')
        self.assertIn('disc-incomplete-banner', body)
        self.assertIn('disc-program-status-banner', body)
        self.assertIn('Incomplete observations = diagnostics only', body)
        css = discovery_light_css()
        self.assertIn('disc-incomplete-banner', css)
        self.assertIn('disc-program-status-banner', css)


class TestLiveLikeTruncatedFixtureParity(unittest.TestCase):
    """Safe fixture model of truncated live CDP — same incomplete contract (no SSH)."""

    def test_truncated_cdp_fixture_matches_operator_contract(self):
        ns = nd._parse_cisco_cdp_detail(
            _read('phase5_ios_cdp_detail_truncated_no_interface.txt'), 'LIVE-LIKE', None,
        )
        self.assertEqual(len(ns), 1)
        fin = nd._finalize_neighbor(dict(ns[0]))
        row = nd._operator_incomplete_observation(fin)
        self.assertTrue(row['incomplete'])
        self.assertFalse(row['edge_eligible'])
        self.assertEqual(row['local_port'], '')
        self.assertEqual(row['local_port_display'], '(unobserved)')
        self.assertNotIn('raw_fragment', row)


class TestMandatoryManifestPhase5(unittest.TestCase):
    def test_phase5_suite_registered(self):
        text = open(MANIFEST, encoding='utf-8').read()
        self.assertIn('pytest_phase5_parser_topology_resilience', text)
        self.assertIn('test_phase5_parser_topology_resilience_slice4.py', text)
        self.assertIn('test_phase5_parser_topology_resilience_slice5.py', text)
        self.assertIn('test_phase5_parser_topology_resilience_slice6.py', text)
        self.assertIn('test_phase5_parser_topology_resilience_slice7.py', text)
        self.assertIn('test_phase5_parser_topology_resilience_slice8.py', text)
        self.assertIn('test_phase5_parser_topology_resilience_slice9.py', text)
        self.assertIn('test_phase5_parser_topology_resilience_slice10.py', text)
        self.assertIn('test_phase5_parser_topology_resilience_slice11.py', text)
        self.assertIn('phase5_discovery_readiness_gate', text)
        self.assertIn('phase5_discovery_release_consumer', text)
        self.assertIn('blocking: true', text)
        # Suite files exist
        for name in (
            'test_phase5_parser_topology_resilience_slice1.py',
            'test_phase5_parser_topology_resilience_slice2.py',
            'test_phase5_parser_topology_resilience_slice3.py',
            'test_phase5_parser_topology_resilience_slice4.py',
            'test_phase5_parser_topology_resilience_slice5.py',
            'test_phase5_parser_topology_resilience_slice6.py',
            'test_phase5_parser_topology_resilience_slice7.py',
            'test_phase5_parser_topology_resilience_slice8.py',
            'test_phase5_parser_topology_resilience_slice9.py',
            'test_phase5_parser_topology_resilience_slice10.py',
            'test_phase5_parser_topology_resilience_slice11.py',
        ):
            self.assertTrue(os.path.isfile(os.path.join(ROOT, 'tests', name)), name)


if __name__ == '__main__':
    unittest.main()
