"""God-mode enterprise pass — packaging, surfaces truth, release gate."""
from __future__ import annotations

import glob
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REVIEW = os.path.join(
    ROOT, 'docs', 'review_folder', '2026.08.22', 'QA', 'god_mode_enterprise_pass'
)
INDEX = os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html')


class TestPackagingAlignment(unittest.TestCase):
    def test_version_has_matching_spec(self):
        ver = open(os.path.join(ROOT, 'VERSION'), encoding='utf-8').read().strip()
        spec = os.path.join(ROOT, f'NetworkSwissToolPro_v{ver}.spec')
        self.assertTrue(os.path.isfile(spec), f'missing spec for VERSION {ver}')

    def test_spec_includes_phase6_program_status(self):
        ver = open(os.path.join(ROOT, 'VERSION'), encoding='utf-8').read().strip()
        body = open(
            os.path.join(ROOT, f'NetworkSwissToolPro_v{ver}.spec'), encoding='utf-8'
        ).read()
        self.assertIn('utils.discovery_program_status', body)


class TestSurfaceTruthLabels(unittest.TestCase):
    def test_no_utilization_overclaim_in_ui(self):
        html = open(INDEX, encoding='utf-8').read().lower()
        self.assertIn('replay is not a live poll', html)
        self.assertIn('live ssh is not snmp', html)
        self.assertNotIn('live ssh collection is not in this release', html)
        self.assertNotIn('no utilization in this release', html)
        self.assertIn('not a certified cable', html)
        self.assertIn('not a discovery crawl', html)

    def test_overlay_not_cables_wording(self):
        html = open(INDEX, encoding='utf-8').read().lower()
        self.assertIn('not cables', html)


class TestGodModeReviewFolder(unittest.TestCase):
    def test_collect_script_exists(self):
        self.assertTrue(os.path.isfile(os.path.join(ROOT, 'scripts', 'god_mode_collect_evidence.py')))

    def test_review_readme_after_collect(self):
        readme = os.path.join(REVIEW, 'README.md')
        if os.path.isfile(readme):
            body = open(readme, encoding='utf-8').read().lower()
            self.assertIn('blocked', body)
            self.assertIn('shumoku', body.replace('utilization', 'shumoku') if 'shumoku' in body else 'traffic')
            self.assertTrue(
                'traffic' in body or 'utilization' in body or 'not implemented' in body
            )


class TestTrafficUtilizationAbsent(unittest.TestCase):
    def test_no_shumoku_module(self):
        hits = glob.glob(os.path.join(ROOT, '**', '*shumoku*'), recursive=True)
        hits = [h for h in hits if 'node_modules' not in h and '.git' not in h]
        self.assertEqual(hits, [])

    def test_overlay_collector_not_traffic_map(self):
        from modules import overlay_collector as oc
        doc = (oc.__doc__ or '').lower()
        self.assertNotIn('shumoku', doc)
        self.assertNotIn('snmp utilization', doc)


if __name__ == '__main__':
    unittest.main()
