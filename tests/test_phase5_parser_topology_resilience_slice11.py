"""Phase 5 slice 11 — downstream hard-stop consumer for release_gate.

Locks: ok=true never clears enterprise claims; BLOCKED requires hard_stop;
--require-release-pass exits 1 while blocked; soft advisory reinterpretation fails.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / 'scripts' / 'phase5_discovery_readiness_check.py'
CONSUMER = ROOT / 'scripts' / 'phase5_discovery_release_consumer.py'
MANIFEST = ROOT / 'tests' / 'qa' / 'MANDATORY_MANIFEST.yaml'
REPORT11 = ROOT / 'tests' / 'qa' / 'PHASE5_SLICE11_HARD_STOP_CONSUMER.md'
QA11 = ROOT / 'tests' / 'qa' / 'PHASE5_SLICE11_HARD_STOP_CONSUMER.md'


def _json_out(cmd: list[str]) -> tuple[int, dict]:
    proc = subprocess.run(
        cmd, cwd=str(ROOT), capture_output=True, text=True, check=False,
    )
    start = proc.stdout.find('{')
    data = json.loads(proc.stdout[start:]) if start >= 0 else {}
    return proc.returncode, data


class TestCheckerConsumerFields(unittest.TestCase):
    def test_blocked_emits_hard_stop_and_claim_denials(self):
        code, data = _json_out([sys.executable, str(CHECKER)])
        self.assertEqual(code, 0, data)
        self.assertTrue(data['ok'])
        self.assertEqual(data['release_gate'], 'BLOCKED')
        self.assertTrue(data['hard_stop'])
        self.assertTrue(data['ok_alone_insufficient_for_enterprise_claim'])
        self.assertFalse(data['may_claim_enterprise_ready'])
        self.assertFalse(data['may_claim_live_vendor_validated'])
        rule = (data.get('consumer_rule') or '').lower()
        self.assertIn('hard stop', rule)
        self.assertIn('never advisory', rule)

    def test_require_release_pass_fails_while_blocked(self):
        code, data = _json_out([
            sys.executable, str(CHECKER), '--require-release-pass',
        ])
        self.assertEqual(code, 1, data)
        self.assertEqual(data['release_gate'], 'BLOCKED')
        self.assertTrue(data['hard_stop'])


class TestNormativeConsumer(unittest.TestCase):
    def test_consumer_accepts_blocked_as_hard_stop(self):
        code, data = _json_out([sys.executable, str(CONSUMER)])
        self.assertEqual(code, 0, data)
        self.assertTrue(data['ok'])
        self.assertEqual(data['release_gate'], 'BLOCKED')
        self.assertTrue(data['hard_stop'])
        self.assertIn('HARD STOP', data.get('interpretation', ''))
        self.assertEqual(data.get('interpretation'), 'HARD STOP — not advisory')

    def test_consumer_require_release_pass_exits_1(self):
        code, data = _json_out([
            sys.executable, str(CONSUMER), '--require-release-pass',
        ])
        self.assertEqual(code, 1, data)
        self.assertEqual(data['release_gate'], 'BLOCKED')

    def test_consumer_rejects_missing_hard_stop_on_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = {
                'ok': True,
                'release_gate': 'BLOCKED',
                'release_gate_severity': 'hard',
                'hard_stop': False,
                'may_claim_enterprise_ready': False,
                'may_claim_live_vendor_validated': False,
                'ok_alone_insufficient_for_enterprise_claim': True,
                'consumer_rule': 'hard stop — never advisory',
                'operator_summary': 'Enterprise operational ready: NO. NOT VALIDATED.',
                'release_gate_reason': 'not a soft warning',
            }
            path = Path(tmp) / 'bad.json'
            path.write_text(json.dumps(bad), encoding='utf-8')
            code, data = _json_out([
                sys.executable, str(CONSUMER), '--from-json', str(path),
            ])
        self.assertEqual(code, 1)
        self.assertTrue(any('hard_stop' in e for e in data.get('errors') or []))

    def test_consumer_rejects_soft_severity(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = {
                'ok': True,
                'release_gate': 'BLOCKED',
                'release_gate_severity': 'advisory',
                'hard_stop': True,
                'may_claim_enterprise_ready': False,
                'may_claim_live_vendor_validated': False,
                'ok_alone_insufficient_for_enterprise_claim': True,
                'consumer_rule': 'hard stop — never advisory',
                'honesty': 'NOT enterprise',
                'operator_summary': 'Enterprise operational ready: NO. NOT VALIDATED. BLOCKED.',
                'release_gate_reason': 'blocked',
            }
            path = Path(tmp) / 'soft.json'
            path.write_text(json.dumps(bad), encoding='utf-8')
            code, data = _json_out([
                sys.executable, str(CONSUMER), '--from-json', str(path),
            ])
        self.assertEqual(code, 1)
        self.assertTrue(any('severity' in e.lower() for e in data.get('errors') or []))


class TestManifestAndDocs(unittest.TestCase):
    def test_manifest_wires_consumer(self):
        text = MANIFEST.read_text(encoding='utf-8')
        self.assertIn('phase5_discovery_release_consumer', text)
        self.assertIn('test_phase5_parser_topology_resilience_slice11.py', text)
        idx = text.index('phase5_discovery_release_consumer')
        self.assertIn('blocking: true', text[idx:idx + 350])

    def test_docs(self):
        for path in (REPORT11, QA11):
            text = path.read_text(encoding='utf-8').lower()
            self.assertIn('hard stop', text)
            self.assertIn('ok', text)
            self.assertIn('blocked', text)
            self.assertNotIn('live vendor truncated cdp/lldp validated', text)


if __name__ == '__main__':
    unittest.main()
