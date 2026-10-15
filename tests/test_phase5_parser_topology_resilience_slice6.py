"""Phase 5 slice 6 — honesty: replay ≠ live; unreachable ≠ pass.

Strengthens gated harness diagnostics and multi-family replay coverage.
Does not claim live vendor truncated CDP/LLDP validation.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPLAY = ROOT / 'tests' / 'fixtures' / 'discovery' / 'phase5_live_lab_capture_replay.json'
SCRIPT = ROOT / 'scripts' / 'phase5_live_lab_truncated_discovery.py'
REPORT = ROOT / 'tests' / 'qa' / 'PHASE5_SLICE5_LIVE_LAB_TRUNCATED.md'
QA5 = ROOT / 'tests' / 'qa' / 'PHASE5_SLICE5_LIVE_LAB_TRUNCATED.md'


def _load_stdout_json(stdout: str) -> dict:
    """Harness may print an INFO shim line before JSON."""
    start = stdout.find('{')
    if start < 0:
        raise AssertionError(f'no JSON object in stdout: {stdout!r}')
    return json.loads(stdout[start:])


class TestHarnessHonestyFields(unittest.TestCase):
    def test_replay_declares_not_live_vendor_validated(self):
        env = os.environ.copy()
        env['NST_PHASE5_LIVE_LAB'] = '1'
        env['NST_PHASE5_LIVE_LAB_REPLAY'] = str(REPLAY)
        env.pop('NST_LAB_HOSTS', None)
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
            console = _load_stdout_json(proc.stdout)
        self.assertEqual(data['mode'], 'replay')
        self.assertFalse(data['live_vendor_validated'])
        self.assertFalse(data['live_ssh_executed'])
        self.assertIn('NOT live vendor validation', data['honesty'])
        self.assertIn(
            'live truncated CDP/LLDP vendor validation',
            data.get('claims_forbidden_unless_live_ssh') or [],
        )
        self.assertFalse(console.get('live_vendor_validated'))
        self.assertIn('NOT live', console.get('honesty', ''))

    def test_unreachable_live_hosts_are_not_executed_not_pass(self):
        env = os.environ.copy()
        env['NST_PHASE5_LIVE_LAB'] = '1'
        env.pop('NST_PHASE5_LIVE_LAB_REPLAY', None)
        # RFC 5737 documentation IP — should not accept SSH in this environment
        env['NST_LAB_HOSTS'] = '192.0.2.1'
        env['NST_LAB_USER'] = 'labuser'
        env['NST_LAB_PASSWORD'] = 'labpass-not-a-secret-for-unreachable-host'
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
            self.assertEqual(proc.returncode, 2, proc.stderr or proc.stdout)
            data = json.loads(out.read_text(encoding='utf-8'))
        self.assertEqual(data['mode'], 'live_ssh_not_executed')
        self.assertFalse(data['live_vendor_validated'])
        self.assertFalse(data['live_ssh_executed'])
        self.assertIn('NOT live vendor validation', data['honesty'])
        self.assertTrue((data.get('reachability') or {}).get('unreachable_hosts'))


class TestMultiFamilyReplayCoverage(unittest.TestCase):
    def test_replay_pack_covers_nxos_and_junos_without_placeholders(self):
        env = os.environ.copy()
        env['NST_PHASE5_LIVE_LAB'] = '1'
        env['NST_PHASE5_LIVE_LAB_REPLAY'] = str(REPLAY)
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
            console = _load_stdout_json(proc.stdout)
        self.assertGreaterEqual(console['incomplete_total'], 3)
        self.assertGreaterEqual(console['complete_total'], 1)
        self.assertFalse(console['live_vendor_validated'])
        self.assertFalse(data['live_vendor_validated'])
        # No capture may invent placeholders or promote incompletes
        for row in data.get('results') or []:
            self.assertTrue(row.get('ok'), row.get('errors'))
            for obs in row.get('incomplete_observations') or []:
                self.assertIs(obs.get('edge_eligible'), False)

        pack = json.loads(REPLAY.read_text(encoding='utf-8'))
        self.assertFalse(pack.get('live_vendor_validated'))
        types = {c.get('device_type') for c in pack['captures']}
        self.assertIn('cisco_nxos', types)
        self.assertIn('juniper_junos', types)
        self.assertIn('cisco_ios', types)
        self.assertTrue(
            any(c.get('parser') == 'juniper_lldp_alternative' for c in pack['captures']),
        )


class TestDocumentationHonesty(unittest.TestCase):
    def test_slice5_artifacts_do_not_claim_live_pass(self):
        for path in (REPORT, QA5):
            text = path.read_text(encoding='utf-8').lower()
            self.assertIn('not executed', text)
            self.assertNotIn('live vendor truncated cdp/lldp validated', text)
            # Forbid celebratory false claim
            self.assertNotIn('live ssh truncated cdp/lldp passed', text)


if __name__ == '__main__':
    unittest.main()
