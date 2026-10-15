"""Phase 6 Wave 5 — related-surface deep-links (navigation polish only).

No parallel Program Status / readiness model. Jumps preserve surface identity.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.plugins import network_discovery as nd
from utils.discovery_map_formatter import generate_discovery_html
from utils.discovery_program_status import (
    RELATED_SURFACE_JUMPS,
    build_discovery_program_status,
    program_status_for_inventory_standard_l2,
    program_status_related_surface_jumps,
)
from utils.report_formatter import generate_topology_html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'discovery')
INDEX = os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html')
REPORT = os.path.join(
    ROOT, 'tests', 'qa', 'PHASE6_WAVE5_RELATED_SURFACE_DEEPLINKS.md'
)
QA = os.path.join(ROOT, 'tests', 'qa', 'PHASE6_WAVE5_RELATED_SURFACE_DEEPLINKS.md')
MANIFEST = os.path.join(ROOT, 'tests', 'qa', 'MANDATORY_MANIFEST.yaml')


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


class TestRelatedSurfaceJumpsMetadata(unittest.TestCase):
    def test_jumps_are_navigation_only_and_gate_unchanged(self):
        base = build_discovery_program_status(job=None)
        jumps = program_status_related_surface_jumps()
        self.assertEqual(len(RELATED_SURFACE_JUMPS), 4)
        self.assertEqual(len(jumps), 4)
        self.assertEqual(base['related_surface_jumps'], jumps)
        self.assertEqual(base['readiness']['release_gate'], 'BLOCKED')
        self.assertTrue(base['readiness']['hard_stop'])
        self.assertFalse(base['readiness']['may_claim_enterprise_ready'])
        ids = [j['id'] for j in jumps]
        self.assertEqual(
            ids,
            [
                'discovery_tab',
                'discovery_command_center',
                'inventory_standard_l2',
                'evidence_overview',
            ],
        )
        # No readiness keys on jump records
        for j in jumps:
            self.assertNotIn('release_gate', j)
            self.assertNotIn('hard_stop', j)
            self.assertIn('label', j)

    def test_inventory_payload_keeps_same_jumps_and_identity(self):
        inv = program_status_for_inventory_standard_l2(num_devices=2, num_links=1)
        base = build_discovery_program_status(job=None)
        self.assertEqual(inv['related_surface_jumps'], base['related_surface_jumps'])
        self.assertEqual(inv['readiness'], base['readiness'])
        self.assertTrue(inv['map_identity']['not_discovery_crawl_graph'])


class TestDeepLinkUiAndMaps(unittest.TestCase):
    def test_index_has_jump_helpers(self):
        html = open(INDEX, encoding='utf-8').read()
        self.assertIn('nstOpenRelatedSurface', html)
        self.assertIn('nstRelatedSurfaceJumpsHtml', html)
        self.assertIn('nstApplyRelatedSurfaceHash', html)
        self.assertIn('nst-ps-overview-jumps', html)
        self.assertIn('disc-program-status-jumps', html)
        self.assertIn('data-nst-related-surface', html)
        self.assertIn('Open Discovery tab', html)
        self.assertIn('Open Command Center', html)
        self.assertIn('Open Inventory L2 entry', html)
        self.assertIn('View Evidence', html)
        self.assertIn('HARD STOP — not advisory', html)
        # Inventory jump must not auto-run topology from the jump helper text
        self.assertIn('does not change Program Status', html)

    def test_api_exposes_jumps_without_softening_gate(self):
        import vlan_checker_web as web

        with web.app.test_client() as client:
            r = client.get(
                '/api/discovery/program-status',
                environ_base={'REMOTE_ADDR': '127.0.0.1'},
            )
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(len(data.get('related_surface_jumps') or []), 4)
        self.assertEqual(data['readiness']['release_gate'], 'BLOCKED')
        self.assertTrue(data['readiness']['hard_stop'])

    def test_crawl_map_embeds_related_surface_links(self):
        nodes, edges = _sample_nodes_edges()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'disc.html')
            generate_discovery_html(path, nodes, edges)
            html = open(path, encoding='utf-8').read()
        low = html.lower()
        self.assertIn('related_surface_jumps', html)
        self.assertIn('nst-discovery', html)
        self.assertIn('nst-inventory-l2', html)
        self.assertIn('nst-evidence', html)
        self.assertIn('related surfaces (operator console)', low)
        self.assertIn('same program status; not the same topology', low)
        self.assertIn('hard stop — not advisory', low)
        self.assertIn('"release_gate": "BLOCKED"', html)

    def test_inventory_map_embeds_related_surface_links(self):
        nodes = [
            {"id": "CORE-01", "label": "CORE-01", "shape": "box",
             "color": {"background": "#e67e22", "border": "#333"},
             "font": {"color": "#fff"}},
        ]
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tf:
            path = tf.name
        try:
            generate_topology_html(
                path, 1, 0,
                json.dumps(nodes), json.dumps([]),
                "/* vis stub */",
                map_mode="all",
            )
            html = open(path, encoding="utf-8").read()
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
        low = html.lower()
        # Related-surface jump list is on crawl/console; inventory L2 keeps honesty + crawl identity.
        self.assertIn('map honesty', low)
        self.assertIn('not discovery crawl', low)
        self.assertIn('hard stop — not advisory', low)
        self.assertIn('nst-program-status-banner', low)


class TestWave5Docs(unittest.TestCase):
    def test_report_and_qa(self):
        self.assertTrue(os.path.isfile(REPORT), REPORT)
        self.assertTrue(os.path.isfile(QA), QA)
        body = open(REPORT, encoding='utf-8').read().lower()
        self.assertIn('wave 5', body)
        self.assertIn('deep-link', body)
        self.assertIn('freeze', body)
        self.assertTrue('hard stop' in body or 'hard-stop' in body)
        qa = open(QA, encoding='utf-8').read().lower()
        self.assertIn('navigation polish', qa)

    def test_manifest(self):
        text = open(MANIFEST, encoding='utf-8').read()
        self.assertIn('pytest_phase6_wave5_related_surface_deeplinks', text)
        self.assertIn('test_phase6_wave5_related_surface_deeplinks.py', text)


if __name__ == '__main__':
    unittest.main()
