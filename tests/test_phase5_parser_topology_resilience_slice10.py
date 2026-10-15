"""Phase 5 slice 10 — release-gate consumer for readiness register.

Locks: honest register may exit 0 with release_gate=BLOCKED (hard, not soft);
overclaim / soft language fails; mandatory manifest runs the checker.
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
MANIFEST = ROOT / 'tests' / 'qa' / 'MANDATORY_MANIFEST.yaml'
REPORT10 = ROOT / 'tests' / 'qa' / 'PHASE5_SLICE10_READINESS_RELEASE_GATE.md'
QA10 = ROOT / 'tests' / 'qa' / 'PHASE5_SLICE10_READINESS_RELEASE_GATE.md'


def _run_checker(register: Path | None = None) -> tuple[int, dict]:
    cmd = [sys.executable, str(CHECKER)]
    if register is not None:
        cmd.extend(['--register', str(register)])
    proc = subprocess.run(
        cmd, cwd=str(ROOT), capture_output=True, text=True, check=False,
    )
    start = proc.stdout.find('{')
    data = json.loads(proc.stdout[start:]) if start >= 0 else {}
    return proc.returncode, data


class TestReleaseGateHardBlocked(unittest.TestCase):
    def test_honest_register_is_blocked_not_soft(self):
        code, data = _run_checker()
        self.assertEqual(code, 0, data)
        self.assertTrue(data['ok'])
        self.assertFalse(data['enterprise_operational_ready'])
        self.assertFalse(data['live_vendor_truncated_cdp_lldp_validated'])
        self.assertEqual(data['release_gate'], 'BLOCKED')
        self.assertEqual(data['release_gate_severity'], 'hard')
        reason = (data.get('release_gate_reason') or '').lower()
        self.assertIn('not a soft warning', reason)
        summary = (data.get('operator_summary') or '').lower()
        self.assertIn('enterprise operational ready: no', summary)
        self.assertIn('blocked', summary)
        self.assertNotIn('almost ready', summary)

    def test_soft_language_in_operator_summary_fails(self):
        reg = json.loads(REGISTER.read_text(encoding='utf-8'))
        reg['operator_summary'] = (
            'Phase 5 is almost ready for enterprise — soft warning only.'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'soft.json'
            path.write_text(json.dumps(reg), encoding='utf-8')
            code, data = _run_checker(path)
        self.assertEqual(code, 1)
        self.assertFalse(data['ok'])
        self.assertEqual(data['release_gate'], 'FAIL')
        self.assertTrue(any('soft' in e.lower() for e in data.get('errors') or []))

    def test_release_gate_when_not_ready_must_be_blocked(self):
        reg = json.loads(REGISTER.read_text(encoding='utf-8'))
        reg['release_gate_when_not_ready'] = 'WARN'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'warn.json'
            path.write_text(json.dumps(reg), encoding='utf-8')
            code, data = _run_checker(path)
        self.assertEqual(code, 1)
        self.assertTrue(
            any('release_gate_when_not_ready' in e for e in data.get('errors') or []),
        )


class TestManifestWiresGate(unittest.TestCase):
    def test_phase5_readiness_gate_suite_blocking(self):
        text = MANIFEST.read_text(encoding='utf-8')
        self.assertIn('phase5_discovery_readiness_gate', text)
        self.assertIn('phase5_discovery_readiness_check.py', text)
        self.assertIn('test_phase5_parser_topology_resilience_slice10.py', text)
        # Suite is blocking (appears near the gate id)
        idx = text.index('phase5_discovery_readiness_gate')
        chunk = text[idx:idx + 400]
        self.assertIn('blocking: true', chunk)


class TestSlice10Docs(unittest.TestCase):
    def test_docs_forbid_soft_overclaim(self):
        for path in (REPORT10, QA10):
            text = path.read_text(encoding='utf-8').lower()
            self.assertIn('blocked', text)
            self.assertIn('soft', text)
            self.assertIn('release', text)
            self.assertNotIn('live vendor truncated cdp/lldp validated', text)


if __name__ == '__main__':
    unittest.main()
