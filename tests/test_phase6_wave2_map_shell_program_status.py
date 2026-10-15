"""Phase 6 Wave 2 — Program Status in Discovery Command Center map shell.

Reuses Wave 1 builder; embeds authoritative program_status in offline HTML.
No parallel readiness truth; hard-stop wording preserved.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.plugins import network_discovery as nd
from utils.discovery_map_formatter import generate_discovery_html
from utils.discovery_program_status import (
    build_discovery_program_status,
    program_status_from_map_meta,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'discovery')
MANIFEST = os.path.join(ROOT, 'tests', 'qa', 'MANDATORY_MANIFEST.yaml')
REPORT = os.path.join(ROOT, 'tests', 'qa', 'PHASE6_WAVE2_MAP_SHELL_PROGRAM_STATUS.md')
QA = os.path.join(ROOT, 'tests', 'qa', 'PHASE6_WAVE2_MAP_SHELL_PROGRAM_STATUS.md')


def _read(name: str) -> str:
    with open(os.path.join(FIX, name), encoding='utf-8') as f:
        return f.read()


def _sample_nodes_edges():
    raw = nd._parse_cisco_cdp_detail(
        _read('phase5_ios_cdp_detail_truncated_no_interface.txt'), 'EDGE', None,
    )
    fin = nd._finalize_neighbor(dict(raw[0]))
    nodes = [
        {
            'id': 'EDGE-01',
            'ip': '10.0.0.1',
            'platform': 'C9300',
            'device_type': 'cisco_ios',
            'depth': 0,
            'is_scanned': True,
            'scan_state': 'scanned',
            'incomplete_observations': [fin],
        },
        {
            'id': 'PEER-OK',
            'ip': '10.0.0.2',
            'depth': 1,
            'is_scanned': False,
            'scan_state': 'neighbor_only',
        },
    ]
    edges = [{
        'from': 'EDGE-01',
        'to': 'PEER-OK',
        'f_port': 'Gi1/0/1',
        't_port': 'Gi1/0/2',
        'protocol': 'CDP',
    }]
    return nodes, edges


class TestMapMetaProgramStatusBuilder(unittest.TestCase):
    def test_map_meta_reuses_wave1_builder_and_stays_blocked(self):
        meta = {
            'devices': [{'hostname': 'A', 'incomplete_observation_count': 1}],
            'links': [{'from': 'A', 'to': 'B', 'local_port': 'Gi0/1', 'remote_port': 'Gi0/2'}],
            'incomplete_observation_count': 1,
            'collection_status': 'complete',
        }
        ps = program_status_from_map_meta(meta)
        api = build_discovery_program_status(job={
            'status': 'complete',
            'result': {'data': meta},
        })
        self.assertEqual(ps['schema'], api['schema'])
        self.assertEqual(ps['readiness']['release_gate'], 'BLOCKED')
        self.assertTrue(ps['readiness']['hard_stop'])
        self.assertFalse(ps['readiness']['may_claim_enterprise_ready'])
        self.assertEqual(ps['surface'], 'discovery_command_center_map_shell')
        self.assertEqual(ps['discovery']['incomplete_observation_count'], 1)
        self.assertEqual(ps['discovery']['confirmed_link_count'], 1)


class TestMapShellEmbedsProgramStatus(unittest.TestCase):
    def test_discovery_html_embeds_program_status_hard_stop(self):
        nodes, edges = _sample_nodes_edges()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'disc.html')
            generate_discovery_html(path, nodes, edges)
            html = open(path, encoding='utf-8').read()

        self.assertIn('program_status', html)
        self.assertIn('disc-program-status-banner', html)
        self.assertIn('discRenderProgramStatus', html)
        self.assertIn('HARD STOP — not advisory', html)
        self.assertIn('Discovery Program Status', html)
        self.assertIn('confirmed_topology', html)
        self.assertIn('incomplete_observations', html)
        self.assertIn('readiness_release_gate', html)
        self.assertIn('"release_gate": "BLOCKED"', html)
        self.assertIn('"hard_stop": true', html)
        self.assertIn('"may_claim_enterprise_ready": false', html)
        # Incomplete banner still present and separate
        self.assertIn('disc-incomplete-banner', html)
        self.assertIn('Incomplete observations (not map links)', html)
        self.assertNotIn('almost ready', html.lower())
        self.assertNotIn('Device ID: TRUNC-PEER', html)

    def test_shell_helpers_include_program_status_region(self):
        from utils.discovery_map_shell import discovery_command_center_body, discovery_light_css
        body = discovery_command_center_body('<div></div>')
        self.assertIn('disc-program-status-banner', body)
        self.assertIn('Program Status / release gate is not topology', body)
        css = discovery_light_css()
        self.assertIn('disc-program-status-banner', css)


class TestManifestAndDocs(unittest.TestCase):
    def test_manifest_registers_wave2(self):
        text = open(MANIFEST, encoding='utf-8').read()
        self.assertIn('pytest_phase6_wave2_map_shell_program_status', text)
        self.assertIn('test_phase6_wave2_map_shell_program_status.py', text)

    def test_docs(self):
        for path in (REPORT, QA):
            text = open(path, encoding='utf-8').read().lower()
            self.assertIn('wave 2', text)
            self.assertIn('command center', text)
            self.assertIn('hard stop', text)
            self.assertIn('blocked', text)
            self.assertNotIn('live vendor truncated cdp/lldp validated', text)


if __name__ == '__main__':
    unittest.main()
