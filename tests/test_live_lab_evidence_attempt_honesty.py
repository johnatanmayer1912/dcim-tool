"""Live-lab evidence attempt honesty — not-executed must not clear the gate.

Locks: attempt artifacts exist, secrets-free, register pointer stays null,
wiring not-executed into the register fails the readiness checker.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTER = os.path.join(ROOT, 'tests', 'qa', 'PHASE5_DISCOVERY_READINESS.json')
PROBE = os.path.join(
    ROOT, 'tests', 'qa', 'evidence', 'phase5_live_ssh_probe_2026-08-21.json'
)
PREREQ = os.path.join(
    ROOT, 'tests', 'qa', 'evidence', 'phase5_live_lab_prereq_skip_2026-08-21.json'
)
CHECKER = os.path.join(ROOT, 'scripts', 'phase5_discovery_readiness_check.py')
REPORT = os.path.join(ROOT, 'reports', 'LIVE_LAB_EVIDENCE_FAILURE_CLOSEOUT_2026-08-21.md')


class TestLiveLabAttemptNotPass(unittest.TestCase):
    def test_register_pointer_still_null(self):
        reg = json.load(open(REGISTER, encoding='utf-8'))
        self.assertIsNone(reg['evidence_paths']['live_evidence_artifact'])
        self.assertFalse(reg['live_vendor_truncated_cdp_lldp_validated'])
        self.assertFalse(reg['enterprise_operational_ready'])

    def test_probe_artifact_is_not_executed_and_secrets_free(self):
        self.assertTrue(os.path.isfile(PROBE), PROBE)
        data = json.load(open(PROBE, encoding='utf-8'))
        self.assertEqual(data['mode'], 'live_ssh_not_executed')
        self.assertFalse(data['live_vendor_validated'])
        self.assertFalse(data.get('live_ssh_executed'))
        blob = json.dumps(data).lower()
        self.assertNotIn('password', blob)
        self.assertNotIn('credential_key', blob)

    def test_prereq_skip_artifact_documented(self):
        self.assertTrue(os.path.isfile(PREREQ), PREREQ)
        data = json.load(open(PREREQ, encoding='utf-8'))
        self.assertEqual(data['mode'], 'live_ssh_prereq_skip')
        self.assertFalse(data['live_vendor_validated'])

    def test_wiring_not_executed_fails_checker(self):
        reg = json.load(open(REGISTER, encoding='utf-8'))
        reg = dict(reg)
        reg['evidence_paths'] = dict(reg['evidence_paths'])
        reg['evidence_paths']['live_evidence_artifact'] = (
            'tests/qa/evidence/phase5_live_ssh_probe_2026-08-21.json'
        )
        with tempfile.NamedTemporaryFile(
            'w', suffix='.json', delete=False, encoding='utf-8'
        ) as tf:
            json.dump(reg, tf)
            path = tf.name
        try:
            r = subprocess.run(
                [sys.executable, CHECKER, '--register', path],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
        self.assertEqual(r.returncode, 1)
        self.assertIn('live_evidence_artifact must be null', r.stdout.lower())

    def test_attempt_report_exists(self):
        self.assertTrue(os.path.isfile(REPORT), REPORT)
        body = open(REPORT, encoding='utf-8').read().lower()
        self.assertIn('pass-eligible', body)
        self.assertIn('blocked', body)

    def test_failure_closeout_exists_and_denies_pass(self):
        path = os.path.join(
            ROOT, 'reports', 'LIVE_LAB_EVIDENCE_FAILURE_CLOSEOUT_2026-08-21.md'
        )
        self.assertTrue(os.path.isfile(path), path)
        body = open(path, encoding='utf-8').read().lower()
        self.assertIn('closed', body)
        self.assertIn('pass supported?', body)
        self.assertIn('**no**', body)
        self.assertIn('attempt-only', body)
        self.assertNotIn('almost ready', body)
        self.assertNotIn('nearly ready', body)


if __name__ == '__main__':
    unittest.main()
