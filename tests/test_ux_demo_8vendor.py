"""Honesty + control-id contracts for UX demo 09 (8-vendor lab)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO09 = ROOT / 'docs' / '11-ux' / 'demos' / '09-offline-8vendor-lab.html'
DEMO07 = ROOT / 'docs' / '11-ux' / 'demos' / '07-maps-utilization.html'
INDEX = ROOT / 'docs' / '11-ux' / 'demos' / 'index.html'
LAB = ROOT / 'tests' / 'fixtures' / 'demo_lab' / 'unified_e2e_lab.json'


class TestUxDemo8VendorLab(unittest.TestCase):
    def setUp(self):
        self.html = DEMO09.read_text(encoding='utf-8')
        self.idx = INDEX.read_text(encoding='utf-8')
        self.d07 = DEMO07.read_text(encoding='utf-8')

    def test_demo_files_exist(self):
        self.assertTrue(DEMO09.is_file())
        self.assertTrue(LAB.is_file())

    def test_gallery_lists_09(self):
        self.assertIn('09-offline-8vendor-lab.html', self.idx)

    def test_eight_devices(self):
        for name in (
            'NX-CORE-01', 'NX-CORE-02', 'NX-AGG-01',
            'IOS-DIST-01', 'IOS-XE-DIST-02', 'IOS-ACC-01',
            'JN-ACC-01', 'JN-ACC-02',
        ):
            self.assertIn(name, self.html)

    def test_overlay_honesty_ssh_not_snmp_collector(self):
        self.assertIn('Replay is not a live poll', self.html)
        self.assertIn('Live SSH is not SNMP', self.html)
        self.assertNotRegex(self.html, r'(?i)snmp snapshot')
        self.assertNotRegex(self.html, r'(?i)ifxtable')

    def test_controls_exist(self):
        for cid in (
            'overlay-on', 'btn-replay', 'btn-live', 'btn-overlay-off',
            'btn-std-l2', 'btn-discovery', 'cred-select', 'e-core', 'e-evpn', 'e-stp',
        ):
            self.assertIn(f'id="{cid}"', self.html)

    def test_no_password_inputs(self):
        self.assertNotRegex(self.html, r'type=["\']password["\']')

    def test_demo07_no_longer_teaches_snmp_collector(self):
        self.assertNotRegex(self.d07, r'(?i)snmp snapshot')
        self.assertIn('Not SNMP', self.d07)
        self.assertIn('09-offline-8vendor-lab.html', self.d07)


if __name__ == '__main__':
    unittest.main()
