"""Phase 5 slice 8 — stdout authority parity for all harness modes.

Closes the gap where ``--json-out`` carried ``result_authority`` but operator
stdout on skip/replay paths sometimes did not. No crawl/merge changes.
No live vendor validation claims.
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
REPORT8 = ROOT / 'tests' / 'qa' / 'PHASE5_SLICE8_STDOUT_AUTHORITY.md'
QA8 = ROOT / 'tests' / 'qa' / 'PHASE5_SLICE8_STDOUT_AUTHORITY.md'

AUTHORITY = 'process_exit_code_and_json_artifact'


def _load_stdout_json(stdout: str) -> dict:
    """Parse the first JSON object; harness may append SKIP text after it."""
    start = stdout.find('{')
    if start < 0:
        raise AssertionError(f'no JSON object in stdout: {stdout!r}')
    obj, _end = json.JSONDecoder().raw_decode(stdout[start:])
    return obj


def _assert_authority(console: dict) -> None:
    assert console.get('result_authority') == AUTHORITY, console
    signals = console.get('non_authoritative_signals') or []
    joined = ' '.join(signals).lower()
    assert 'timeout' in joined and 'background' in joined, signals
    assert console.get('live_vendor_validated') is False


class TestStdoutAuthorityParity(unittest.TestCase):
    def test_unauthorized_skip_stdout_has_authority(self):
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
        self.assertEqual(proc.returncode, 2, proc.stderr or proc.stdout)
        console = _load_stdout_json(proc.stdout)
        self.assertEqual(console['mode'], 'unauthorized_skip')
        _assert_authority(console)

    def test_prereq_skip_stdout_has_authority(self):
        env = os.environ.copy()
        env['NST_PHASE5_LIVE_LAB'] = '1'
        env.pop('NST_PHASE5_LIVE_LAB_REPLAY', None)
        env.pop('NST_LAB_HOSTS', None)
        env.pop('NST_LAB_USER', None)
        env.pop('NST_LAB_PASSWORD', None)
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 2, proc.stderr or proc.stdout)
        console = _load_stdout_json(proc.stdout)
        self.assertEqual(console['mode'], 'live_ssh_prereq_skip')
        _assert_authority(console)

    def test_replay_stdout_matches_json_out_authority(self):
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
        _assert_authority(console)
        self.assertEqual(console['result_authority'], data['result_authority'])
        self.assertEqual(
            console['non_authoritative_signals'],
            data['non_authoritative_signals'],
        )
        self.assertFalse(console['live_vendor_validated'])
        self.assertFalse(data['live_vendor_validated'])

    def test_not_executed_stdout_has_authority(self):
        env = os.environ.copy()
        env['NST_PHASE5_LIVE_LAB'] = '1'
        env.pop('NST_PHASE5_LIVE_LAB_REPLAY', None)
        env['NST_LAB_HOSTS'] = '192.0.2.1'
        env['NST_LAB_USER'] = 'labuser'
        env['NST_LAB_PASSWORD'] = 'labpass-unreachable-host-placeholder'
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 2, proc.stderr or proc.stdout)
        console = _load_stdout_json(proc.stdout)
        self.assertEqual(console['mode'], 'live_ssh_not_executed')
        _assert_authority(console)


class TestSlice8Docs(unittest.TestCase):
    def test_docs_state_stdout_parity(self):
        for path in (REPORT8, QA8):
            text = path.read_text(encoding='utf-8').lower()
            self.assertIn('stdout', text)
            self.assertIn('result_authority', text)
            self.assertIn('non_authoritative', text)
            self.assertNotIn('live vendor truncated cdp/lldp validated', text)


if __name__ == '__main__':
    unittest.main()
