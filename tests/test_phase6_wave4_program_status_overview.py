"""Phase 6 Wave 4 — cross-surface Program Status overview strip.

Three surfaces share one authoritative Program Status; identities stay distinct.
No parallel readiness model; hard-stop wording preserved.
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
    CROSS_SURFACE_NOTE,
    PROGRAM_STATUS_SURFACES,
    build_discovery_program_status,
    program_status_cross_surface_overview,
    program_status_for_inventory_standard_l2,
    program_status_from_map_meta,
)
from utils.report_formatter import generate_topology_html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'discovery')
INDEX = os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html')
REPORT = os.path.join(
    ROOT, 'tests', 'qa', 'PHASE6_WAVE4_PROGRAM_STATUS_OVERVIEW.md'
)
QA = os.path.join(ROOT, 'tests', 'qa', 'PHASE6_WAVE4_PROGRAM_STATUS_OVERVIEW.md')
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


class TestCrossSurfaceOverviewBuilder(unittest.TestCase):
    def test_reuses_wave1_readiness_no_parallel_truth(self):
        base = build_discovery_program_status(job=None)
        overview = program_status_cross_surface_overview()
        self.assertEqual(overview['schema'], base['schema'])
        self.assertEqual(overview['readiness'], base['readiness'])
        self.assertEqual(overview['phase'], '6-wave4')
        self.assertEqual(
            overview['overview']['authoritative_source'],
            'build_discovery_program_status',
        )
        self.assertEqual(overview['readiness']['release_gate'], 'BLOCKED')
        self.assertTrue(overview['readiness']['hard_stop'])
        self.assertFalse(overview['readiness']['may_claim_enterprise_ready'])
        self.assertFalse(overview['readiness']['enterprise_operational_ready'])
        self.assertFalse(
            overview['readiness']['live_vendor_truncated_cdp_lldp_validated']
        )

    def test_three_distinct_surfaces_labeled(self):
        payload = build_discovery_program_status(job=None)
        ids = [s['id'] for s in payload['surfaces']]
        self.assertEqual(
            ids,
            [
                'discovery_tab',
                'discovery_command_center',
                'inventory_standard_l2',
            ],
        )
        self.assertEqual(len(PROGRAM_STATUS_SURFACES), 3)
        note = (payload.get('cross_surface_note') or '').lower()
        self.assertIn('hard stop', note)
        self.assertIn('not the same topology', note)
        self.assertIn('not live-validated', note)
        self.assertIn('not enterprise cleared', note)
        self.assertIn('program status is not topology', note)
        self.assertEqual(payload['cross_surface_note'], CROSS_SURFACE_NOTE)

    def test_wave2_and_wave3_carry_same_surfaces(self):
        meta = {
            'job_id': 'j1',
            'devices': [],
            'links': [],
            'incomplete_observation_count': 0,
            'collection_status': 'complete',
        }
        crawl = program_status_from_map_meta(meta)
        inv = program_status_for_inventory_standard_l2(num_devices=1, num_links=0)
        base_ids = [s['id'] for s in build_discovery_program_status(job=None)['surfaces']]
        self.assertEqual([s['id'] for s in crawl['surfaces']], base_ids)
        self.assertEqual([s['id'] for s in inv['surfaces']], base_ids)
        self.assertEqual(crawl['surface'], 'discovery_command_center_map_shell')
        self.assertEqual(inv['surface'], 'inventory_standard_l2_map')
        self.assertNotEqual(crawl['surface'], inv['surface'])


class TestOverviewUiAndMaps(unittest.TestCase):
    def test_index_has_overview_strips_and_hard_stop(self):
        with open(INDEX, encoding='utf-8') as f:
            html = f.read()
        self.assertIn('data-nst-ps-overview', html)
        self.assertIn('nst-ps-overview-tools', html)
        self.assertIn('nst-ps-overview-evidence', html)
        self.assertIn('nst-ps-overview-about', html)
        self.assertIn('disc-program-status-surfaces', html)
        self.assertIn('nstRefreshProgramStatusOverview', html)
        self.assertIn('nstPaintProgramStatusOverview', html)
        self.assertIn('HARD STOP — not advisory', html)
        self.assertIn('three surfaces, one truth', html.lower())

    def test_crawl_map_lists_surfaces(self):
        nodes, edges = _sample_nodes_edges()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'disc.html')
            generate_discovery_html(path, nodes, edges)
            html = open(path, encoding='utf-8').read()
        low = html.lower()
        self.assertIn('program_status', html)
        self.assertIn('surfaces sharing this program status', low)
        self.assertIn('discovery tab', low)
        self.assertIn('inventory standard l2', low)
        self.assertIn('hard stop — not advisory', low)
        self.assertIn('not the inventory standard l2 map', low)
        self.assertIn('"release_gate": "BLOCKED"', html)
        self.assertNotIn('almost ready', low)

    def test_inventory_map_lists_surfaces(self):
        nodes = [
            {"id": "CORE-01", "label": "CORE-01", "shape": "box",
             "color": {"background": "#e67e22", "border": "#333"},
             "font": {"color": "#fff"}},
        ]
        edges = []
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tf:
            path = tf.name
        try:
            generate_topology_html(
                path, 1, 0,
                json.dumps(nodes), json.dumps(edges),
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
        # Inventory L2 embeds compact honesty strip (cross-surface list lives on crawl + console).
        self.assertIn('map honesty', low)
        self.assertIn('nst-program-status-banner', low)
        self.assertIn('hard stop — not advisory', low)
        self.assertIn('not discovery crawl', low)

    def test_api_exposes_surfaces(self):
        import vlan_checker_web as web

        with web.app.test_client() as client:
            r = client.get(
                '/api/discovery/program-status',
                environ_base={'REMOTE_ADDR': '127.0.0.1'},
            )
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(len(data.get('surfaces') or []), 3)
        self.assertIn('hard stop', (data.get('cross_surface_note') or '').lower())
        self.assertEqual(data['readiness']['release_gate'], 'BLOCKED')


class TestWave4Docs(unittest.TestCase):
    def test_report_and_qa_exist(self):
        self.assertTrue(os.path.isfile(QA), QA)
        with open(QA, encoding='utf-8') as f:
            body = f.read().lower()
        self.assertIn('wave 4', body)
        self.assertIn('hard_stop', body)
        self.assertIn('three surfaces', body)

    def test_manifest_lists_wave4(self):
        with open(MANIFEST, encoding='utf-8') as f:
            text = f.read()
        self.assertIn('pytest_phase6_wave4_program_status_overview', text)
        self.assertIn('test_phase6_wave4_program_status_overview.py', text)


if __name__ == '__main__':
    unittest.main()
