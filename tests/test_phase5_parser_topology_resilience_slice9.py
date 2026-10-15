"""Phase 5 slice 9 — enterprise readiness register (honest, machine-checkable).

Closes the post–stdout-authority gap: a release-consumable readiness register
that keeps enterprise_operational_ready and live vendor truncated CDP/LLDP
explicitly false until a retained live_ssh artifact exists.

Does not change discovery parsers, crawl, or merge behavior.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / 'tests' / 'qa' / 'PHASE5_DISCOVERY_READINESS.json'
CHECKER = ROOT / 'scripts' / 'phase5_discovery_readiness_check.py'
REPLAY = ROOT / 'tests' / 'fixtures' / 'discovery' / 'phase5_live_lab_capture_replay.json'
REPORT9 = ROOT / 'tests' / 'qa' / 'PHASE5_SLICE9_DISCOVERY_READINESS.md'
QA9 = ROOT / 'tests' / 'qa' / 'PHASE5_SLICE9_DISCOVERY_READINESS.md'


class TestReadinessRegisterHonesty(unittest.TestCase):
    def test_register_blocks_enterprise_and_live_claims(self):
        reg = json.loads(REGISTER.read_text(encoding='utf-8'))
        self.assertEqual(reg['schema'], 'nst.phase5.discovery_readiness.v1')
        self.assertFalse(reg['enterprise_operational_ready'])
        self.assertFalse(reg['live_vendor_truncated_cdp_lldp_validated'])
        self.assertIsNone(reg['evidence_paths']['live_evidence_artifact'])
        self.assertIn('NOT', (reg.get('verdict') or '').upper().replace('—', '-'))
        forbidden = ' '.join(reg.get('forbidden_claims_until_live') or []).lower()
        self.assertIn('live vendor', forbidden)
        self.assertIn('enterprise operational ready', forbidden)
        for row in reg['proven']:
            self.assertNotEqual(row.get('evidence_class'), 'live-lab-backed')
        caps = {r['capability'] for r in reg['unproven']}
        self.assertIn('live_truncated_cdp_lldp_ssh', caps)

    def test_checker_passes_on_honest_register(self):
        proc = subprocess.run(
            [sys.executable, str(CHECKER)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        start = proc.stdout.find('{')
        data = json.loads(proc.stdout[start:])
        self.assertTrue(data['ok'])
        self.assertFalse(data['enterprise_operational_ready'])
        self.assertFalse(data['live_vendor_truncated_cdp_lldp_validated'])

    def test_checker_rejects_enterprise_true_without_live(self):
        reg = json.loads(REGISTER.read_text(encoding='utf-8'))
        reg['enterprise_operational_ready'] = True
        # leave live false → must fail
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.json'
            path.write_text(json.dumps(reg), encoding='utf-8')
            proc = subprocess.run(
                [sys.executable, str(CHECKER), '--register', str(path)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 1, proc.stdout)
            data = json.loads(proc.stdout[proc.stdout.find('{'):])
            self.assertFalse(data['ok'])
            self.assertTrue(any('enterprise_operational_ready' in e for e in data['errors']))

    def test_checker_rejects_live_true_without_artifact(self):
        reg = json.loads(REGISTER.read_text(encoding='utf-8'))
        reg['live_vendor_truncated_cdp_lldp_validated'] = True
        reg['enterprise_operational_ready'] = True
        reg['evidence_paths']['live_evidence_artifact'] = None
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.json'
            path.write_text(json.dumps(reg), encoding='utf-8')
            proc = subprocess.run(
                [sys.executable, str(CHECKER), '--register', str(path)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 1, proc.stdout)

    def test_replay_pack_still_not_live(self):
        pack = json.loads(REPLAY.read_text(encoding='utf-8'))
        self.assertFalse(pack.get('live_vendor_validated'))


class TestSlice9Docs(unittest.TestCase):
    def test_docs_name_the_gap(self):
        for path in (REPORT9, QA9):
            text = path.read_text(encoding='utf-8').lower()
            self.assertIn('enterprise', text)
            self.assertIn('readiness', text)
            self.assertIn('not', text)
            self.assertIn('live', text)
            self.assertNotIn('live vendor truncated cdp/lldp validated', text)


if __name__ == '__main__':
    unittest.main()
