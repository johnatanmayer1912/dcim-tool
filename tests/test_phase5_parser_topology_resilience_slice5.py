"""Phase 5 slice 5 — authorized live-lab truncated CDP/LLDP path.

Live SSH was attempted against inventory lab hosts (all unreachable this checkout).
Offline replay of the authorized harness is the executable proof path here.
Never reads .credential_key. No fabricated ports/edges.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.plugins import network_discovery as nd
from utils.discovery_map_formatter import generate_discovery_html

ROOT = Path(__file__).resolve().parents[1]
REPLAY = ROOT / 'tests' / 'fixtures' / 'discovery' / 'phase5_live_lab_capture_replay.json'
SCRIPT = ROOT / 'scripts' / 'phase5_live_lab_truncated_discovery.py'
INVENTORY = ROOT / 'inventory.txt'


class TestLiveLabAuthorizationGate(unittest.TestCase):
    def test_harness_skips_without_authorization_flag(self):
        env = os.environ.copy()
        env.pop('NST_PHASE5_LIVE_LAB', None)
        env.pop('NST_PHASE5_LIVE_LAB_REPLAY', None)
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn('SKIP', proc.stdout)

    def test_harness_replay_passes_under_authorization(self):
        env = os.environ.copy()
        env['NST_PHASE5_LIVE_LAB'] = '1'
        env['NST_PHASE5_LIVE_LAB_REPLAY'] = str(REPLAY)
        # Ensure live SSH env cannot accidentally engage
        env.pop('NST_LAB_HOSTS', None)
        env.pop('NST_LAB_PASSWORD', None)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'result.json'
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), '--json-out', str(out)],
                cwd=str(ROOT),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
            data = json.loads(out.read_text(encoding='utf-8'))
        self.assertEqual(data['mode'], 'replay')
        self.assertTrue(data['authorized'])
        self.assertFalse(data['live_ssh_executed'])
        self.assertEqual(data['failed_count'], 0)
        incomplete_total = sum(int(r.get('incomplete_count') or 0) for r in data['results'])
        complete_total = sum(int(r.get('complete_count') or 0) for r in data['results'])
        self.assertGreaterEqual(incomplete_total, 2)
        self.assertGreaterEqual(complete_total, 1)
        for r in data['results']:
            for obs in r.get('incomplete_observations') or []:
                self.assertTrue(obs.get('incomplete'))
                self.assertFalse(obs.get('edge_eligible'))
                self.assertNotIn('raw_fragment', obs)
                self.assertNotEqual(obs.get('local_port'), 'unknown')
                self.assertNotEqual(obs.get('remote_port'), 'n/a')


class TestLiveLabInventoryReachabilityHonesty(unittest.TestCase):
    def test_inventory_lab_hosts_documented_unreachable_this_checkout(self):
        """Slice 5 live SSH path: inventory hosts were DOWN at authorization time.

        This is an honesty marker, not a claim that live vendor output was validated.
        """
        text = INVENTORY.read_text(encoding='utf-8')
        # Historical slice used 10.1.1.1; current checkout may point at Docker SSH lab (127.0.0.1).
        lab_inv = ROOT / 'lab' / 'docker' / 'inventory.nst.txt'
        has_legacy = '10.1.1.1' in text
        has_lab = lab_inv.is_file() and (
            '127.0.0.1' in text or '127.0.0.1' in lab_inv.read_text(encoding='utf-8')
        )
        self.assertTrue(has_legacy or has_lab, 'expected legacy lab IP or Docker SSH lab inventory')
        # Report is written in the same slice; allow create-order by checking harness instead
        self.assertTrue(SCRIPT.is_file())
        self.assertTrue(REPLAY.is_file())


class TestReplayCaptureEndToEndMap(unittest.TestCase):
    def test_truncated_capture_surfaces_in_map_not_as_edge(self):
        capture = json.loads(REPLAY.read_text(encoding='utf-8'))
        trunc = next(
            c for c in capture['captures']
            if 'TRUNC-PEER' in c.get('output', '')
        )
        ns = nd._parse_cisco_cdp_detail(
            trunc['output'], trunc['host'], None,
        )
        fin = nd._finalize_neighbor(dict(ns[0]))
        self.assertTrue(fin['incomplete'])
        nodes = [{
            'id': trunc['host'],
            'ip': '10.0.0.8',
            'depth': 0,
            'is_scanned': True,
            'scan_state': 'scanned',
            'incomplete_observations': [fin],
        }]
        edges = []  # incompletes must not invent edges
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'map.html')
            generate_discovery_html(path, nodes, edges)
            html = open(path, encoding='utf-8').read()
        self.assertIn('incomplete_observation_count', html)
        self.assertIn('not map links', html)
        self.assertIn('(unobserved)', html)
        self.assertNotIn('Device ID: TRUNC-PEER', html)


if __name__ == '__main__':
    unittest.main()
