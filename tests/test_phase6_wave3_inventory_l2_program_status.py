"""Phase 6 Wave 3 — Program Status on inventory Standard L2 map.

Reuses Wave 1 builder; inventory map labeled distinct from Discovery crawl graph.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.discovery_program_status import (
    build_discovery_program_status,
    program_status_for_inventory_standard_l2,
)
from utils.report_formatter import generate_topology_html
from utils import standard_map_shell as sms

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, 'tests', 'qa', 'MANDATORY_MANIFEST.yaml')
REPORT = os.path.join(ROOT, 'tests', 'qa', 'PHASE6_WAVE3_INVENTORY_L2_PROGRAM_STATUS.md')
QA = os.path.join(ROOT, 'tests', 'qa', 'PHASE6_WAVE3_INVENTORY_L2_PROGRAM_STATUS.md')


class TestInventoryProgramStatusBuilder(unittest.TestCase):
    def test_reuses_wave1_readiness_and_stays_blocked(self):
        ps = program_status_for_inventory_standard_l2(num_devices=3, num_links=2)
        base = build_discovery_program_status(job=None)
        self.assertEqual(ps['schema'], base['schema'])
        self.assertEqual(ps['readiness']['release_gate'], 'BLOCKED')
        self.assertTrue(ps['readiness']['hard_stop'])
        self.assertFalse(ps['readiness']['may_claim_enterprise_ready'])
        self.assertEqual(ps['surface'], 'inventory_standard_l2_map')
        self.assertTrue(ps['map_identity']['not_discovery_crawl_graph'])
        ids = [c['id'] for c in ps['categories']]
        self.assertEqual(ids[0], 'inventory_l2_map_view')
        self.assertIn('confirmed_topology', ids)
        self.assertIn('readiness_release_gate', ids)
        self.assertIn('not Discovery crawl', ps['categories'][0]['summary'])


class TestInventoryMapHtmlEmbed(unittest.TestCase):
    def test_standard_l2_html_embeds_program_status_and_identity(self):
        nodes = [
            {"id": "CORE-01", "label": "CORE-01", "shape": "box",
             "color": {"background": "#e67e22", "border": "#333"},
             "font": {"color": "#fff"}},
            {"id": "DIST-N1", "label": "DIST-N1", "shape": "box",
             "color": {"background": "#e67e22", "border": "#333"},
             "font": {"color": "#fff"}},
        ]
        edges = [{
            "id": "e0", "from": "CORE-01", "to": "DIST-N1",
            "f_port": "Te1/0/1", "t_port": "Te1/1/1", "label": "",
            "type": "standard",
            "edge_data": {
                "from": "CORE-01", "to": "DIST-N1",
                "f_port": "Te1/0/1", "t_port": "Te1/1/1",
                "type": "standard", "confidence": "High",
            },
            "color": "#607d8b", "width": 2,
        }]
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tf:
            path = tf.name
        try:
            generate_topology_html(
                path, 2, 1,
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

        self.assertIn('nst-program-status-banner', html)
        # Inventory L2 uses compact Map honesty banner (full Discovery Program Status stays on crawl).
        self.assertIn('Map honesty', html)
        self.assertIn('HARD STOP — not advisory', html)
        low = html.lower()
        self.assertIn('not discovery crawl', low)
        self.assertIn('inventory standard l2', low)
        self.assertIn('not discovery crawl command center', low)
        self.assertIn('this view: inventory standard l2 map', low)
        self.assertIn('program readiness / release gate', low)
        self.assertNotIn('almost ready', low)

    def test_chrome_helper_includes_banner(self):
        ps = program_status_for_inventory_standard_l2(num_devices=1, num_links=0)
        chrome = sms.embed_standard_map_top_chrome('vtest', 1, 0, program_status=ps)
        self.assertIn('nst-program-status-banner', chrome)
        self.assertIn('HARD STOP — not advisory', chrome)
        self.assertIn('not Discovery crawl Command Center', chrome)
        css = sms.standard_map_shell_css()
        self.assertIn('nst-program-status-banner', css)


class TestManifestAndDocs(unittest.TestCase):
    def test_manifest(self):
        text = open(MANIFEST, encoding='utf-8').read()
        self.assertIn('pytest_phase6_wave3_inventory_l2_program_status', text)
        self.assertIn('test_phase6_wave3_inventory_l2_program_status.py', text)

    def test_docs(self):
        for path in (REPORT, QA):
            text = open(path, encoding='utf-8').read().lower()
            self.assertIn('wave 3', text)
            self.assertIn('inventory', text)
            self.assertIn('hard stop', text)
            self.assertIn('crawl', text)
            self.assertNotIn('live vendor truncated cdp/lldp validated', text)


if __name__ == '__main__':
    unittest.main()
