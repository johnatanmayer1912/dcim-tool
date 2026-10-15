"""Enterprise readiness release-gate integration — evidence-backed, no claim inflation.

Verifies normative checker/consumer, Program Status API, register honesty,
and attempt-only live-lab artifacts. Does not assert enterprise PASS.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTER = os.path.join(ROOT, 'tests', 'qa', 'PHASE5_DISCOVERY_READINESS.json')
CHECKER = os.path.join(ROOT, 'scripts', 'phase5_discovery_readiness_check.py')
CONSUMER = os.path.join(ROOT, 'scripts', 'phase5_discovery_release_consumer.py')
REPORT = os.path.join(ROOT, 'docs', 'review_folder', '2026.08.23', 'QA', 'enterprise_validation_rendering_and_ship_readiness', 'EXECUTIVE_SUMMARY.md')
OPERATOR_QA = os.path.join(ROOT, 'scripts', 'run_operator_browser_qa.py')


def _run_json(cmd: list[str]) -> dict:
    out = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if out.returncode not in (0, 1) and 'readiness_check' in cmd[1]:
        raise AssertionError(f'{cmd}: {out.stderr or out.stdout}')
    return json.loads(out.stdout)


class TestReleaseGateStack(unittest.TestCase):
    def test_checker_blocked_hard_stop(self):
        data = _run_json([sys.executable, CHECKER])
        self.assertTrue(data['ok'])
        self.assertEqual(data['release_gate'], 'BLOCKED')
        self.assertTrue(data['hard_stop'])
        self.assertFalse(data['may_claim_enterprise_ready'])
        self.assertFalse(data['may_claim_live_vendor_validated'])
        self.assertIn('hard stop', data['consumer_rule'].lower())

    def test_consumer_matches_checker(self):
        chk = _run_json([sys.executable, CHECKER])
        con = _run_json([sys.executable, CONSUMER])
        self.assertEqual(con['release_gate'], chk['release_gate'])
        self.assertEqual(con['hard_stop'], chk['hard_stop'])
        self.assertIn('HARD STOP', con['interpretation'])

    def test_require_release_pass_exits_one(self):
        for script in (CHECKER, CONSUMER):
            r = subprocess.run(
                [sys.executable, script, '--require-release-pass'],
                cwd=ROOT,
                capture_output=True,
            )
            self.assertEqual(r.returncode, 1, script)


class TestRegisterAndProgramStatus(unittest.TestCase):
    def test_register_null_live_artifact(self):
        reg = json.load(open(REGISTER, encoding='utf-8'))
        self.assertIsNone(reg['evidence_paths']['live_evidence_artifact'])
        self.assertFalse(reg['live_vendor_truncated_cdp_lldp_validated'])
        self.assertFalse(reg['enterprise_operational_ready'])

    def test_program_status_api_matches_register(self):
        import vlan_checker_web as web

        with web.app.test_client() as client:
            r = client.get(
                '/api/discovery/program-status',
                environ_base={'REMOTE_ADDR': '127.0.0.1'},
            )
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        reg = json.load(open(REGISTER, encoding='utf-8'))
        self.assertEqual(
            body['readiness']['release_gate'],
            'BLOCKED' if not reg['enterprise_operational_ready'] else 'PASS',
        )
        self.assertEqual(
            body['readiness']['live_vendor_truncated_cdp_lldp_validated'],
            reg['live_vendor_truncated_cdp_lldp_validated'],
        )
        self.assertEqual(len(body.get('surfaces') or []), 3)
        self.assertEqual(len(body.get('related_surface_jumps') or []), 4)
        blob = json.dumps(body).lower()
        self.assertNotIn('enterprise operational ready: yes', blob)

    def test_program_status_no_parallel_truth(self):
        from utils.discovery_program_status import (
            build_discovery_program_status,
            program_status_cross_surface_overview,
        )

        base = build_discovery_program_status(job=None)
        overview = program_status_cross_surface_overview()
        self.assertEqual(base['readiness'], overview['readiness'])


class TestEnterpriseQaArtifacts(unittest.TestCase):
    def test_report_exists(self):
        self.assertTrue(os.path.isfile(REPORT), REPORT)
        body = open(REPORT, encoding='utf-8').read().lower()
        self.assertIn('verdict', body)
        self.assertIn('blocked', body)

    def test_operator_browser_runner_exists(self):
        self.assertTrue(os.path.isfile(OPERATOR_QA), OPERATOR_QA)
        self.assertTrue(
            os.path.isfile(os.path.join(ROOT, 'tests', 'browser', 'operator_program_status.spec.mjs'))
        )


if __name__ == '__main__':
    unittest.main()
