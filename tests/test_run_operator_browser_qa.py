"""Smoke checks for scripts/run_operator_browser_qa.py integration surface."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestOperatorBrowserQaPaths(unittest.TestCase):
    def test_paths_exist(self):
        self.assertTrue((ROOT / 'scripts' / 'run_operator_browser_qa.py').is_file())
        self.assertTrue((ROOT / 'tests' / 'browser' / 'operator_program_status.spec.mjs').is_file())
        self.assertTrue((ROOT / 'tests' / 'browser' / 'operator_swiss_tools_overlay.spec.mjs').is_file())
        self.assertTrue((ROOT / 'tests' / 'browser' / 'ux_demo_09_8vendor.spec.mjs').is_file())
        self.assertTrue((ROOT / 'scripts' / 'run_ux_demo_qa.py').is_file())
        self.assertTrue((ROOT / 'scripts' / 'run_playwright_e2e.py').is_file())
        self.assertTrue((ROOT / 'scripts' / 'run_offline_map_html_qa.py').is_file())

    def test_manifest_lists_suite(self):
        text = (ROOT / 'tests' / 'qa' / 'MANDATORY_MANIFEST.yaml').read_text(encoding='utf-8')
        self.assertIn('operator_browser_program_status', text)
        self.assertIn('run_operator_browser_qa.py', text)


if __name__ == '__main__':
    unittest.main()
