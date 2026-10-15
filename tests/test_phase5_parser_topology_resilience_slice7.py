"""Phase 5 slice 7 — authority: harness exit/JSON vs shell-timeout noise.

Locks Slice 6 honesty fields and documents that agent/IDE background timeout
is not a pytest or contract failure when the harness already exited 0 with
replay ok=true and live_vendor_validated=false.

Does not expand live SSH or invent topology.
"""
from __future__ import annotations

import inspect
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
REPORT7 = ROOT / 'tests' / 'qa' / 'PHASE5_SLICE7_RESULT_AUTHORITY.md'
QA7 = ROOT / 'tests' / 'qa' / 'PHASE5_SLICE7_RESULT_AUTHORITY.md'
QA6 = ROOT / 'tests' / 'qa' / 'PHASE5_SLICE6_LIVE_LAB_HONESTY.md'


def _load_stdout_json(stdout: str) -> dict:
    start = stdout.find('{')
    if start < 0:
        raise AssertionError(f'no JSON object in stdout: {stdout!r}')
    return json.loads(stdout[start:])


class TestResultAuthorityFields(unittest.TestCase):
    def test_replay_json_declares_result_authority(self):
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
        self.assertEqual(data['mode'], 'replay')
        self.assertFalse(data['live_vendor_validated'])
        self.assertEqual(data['failed_count'], 0)
        self.assertEqual(
            data.get('result_authority'),
            'process_exit_code_and_json_artifact',
        )
        signals = data.get('non_authoritative_signals') or []
        joined = ' '.join(signals).lower()
        self.assertIn('timeout', joined)
        self.assertIn('background', joined)

    def test_not_executed_keeps_authority_and_exit_2(self):
        env = os.environ.copy()
        env['NST_PHASE5_LIVE_LAB'] = '1'
        env.pop('NST_PHASE5_LIVE_LAB_REPLAY', None)
        env['NST_LAB_HOSTS'] = '192.0.2.1'
        env['NST_LAB_USER'] = 'labuser'
        env['NST_LAB_PASSWORD'] = 'labpass-unreachable-host-placeholder'
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
        self.assertEqual(
            data.get('result_authority'),
            'process_exit_code_and_json_artifact',
        )


class TestParserHintIsolation(unittest.TestCase):
    def test_live_ssh_path_does_not_accept_replay_parser_hint(self):
        """Replay-only ``parser`` key must not be reachable from live SSH args."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            'phase5_live_lab_truncated_discovery', SCRIPT,
        )
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        src = inspect.getsource(mod._run_live_ssh)
        self.assertNotIn('parser_hint', src)
        self.assertNotIn('juniper_lldp_alternative', src)
        # Evaluate accepts hint; live runner must not pass it
        sig = inspect.signature(mod._evaluate_output)
        self.assertIn('parser_hint', sig.parameters)


class TestDocumentationAuthority(unittest.TestCase):
    def test_slice7_docs_separate_timeout_from_contract(self):
        for path in (REPORT7, QA7):
            text = path.read_text(encoding='utf-8').lower()
            self.assertIn('result_authority', text)
            self.assertIn('timeout', text)
            self.assertIn('background', text)
            self.assertIn('not', text)
            self.assertIn('pytest', text)
            self.assertIn('live_vendor_validated', text)
            self.assertNotIn('live vendor truncated cdp/lldp validated', text)

    def test_slice6_qa_still_honest(self):
        text = QA6.read_text(encoding='utf-8').lower()
        self.assertIn('not', text)
        self.assertIn('live', text)


if __name__ == '__main__':
    unittest.main()
