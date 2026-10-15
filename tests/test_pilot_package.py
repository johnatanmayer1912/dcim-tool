"""Pilot / traceability / offline / live-lab package must exist. Does not prove live lab."""
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, '.cursor', 'docs')


class TestPilotPackage(unittest.TestCase):
    def test_pilot_files(self):
        for name in (
            'PILOT_SCOPE.md',
            'PILOT_SUCCESS_CRITERIA.md',
            'PILOT_KNOWN_LIMITATIONS.md',
            'PILOT_TEST_SCRIPT.md',
            'PILOT_RUNBOOK.md',
            'PILOT_ROLLBACK_PLAN.md',
            'PILOT_ISSUE_TEMPLATE.md',
            'PILOT_EVIDENCE_LOG.md',
        ):
            path = os.path.join(DOCS, 'pilot', name)
            self.assertTrue(os.path.isfile(path), msg=path)
            text = open(path, encoding='utf-8').read()
            self.assertGreater(len(text), 200)

    def test_scope_forbids_overlay_collection(self):
        text = open(os.path.join(DOCS, 'pilot', 'PILOT_SCOPE.md'), encoding='utf-8').read()
        self.assertIn('not collected', text.lower())
        self.assertIn('Playwright', text)

    def test_offline_and_lab_and_traceability(self):
        paths = [
            os.path.join(DOCS, 'READINESS_TRACEABILITY.md'),
            os.path.join(DOCS, 'E2E_ACCEPTANCE_STRATEGY.md'),
            os.path.join(DOCS, 'offline', 'OFFLINE_INSTALL_CHECKLIST.md'),
            os.path.join(DOCS, 'offline', 'OFFLINE_VERIFICATION_SCRIPT.md'),
            os.path.join(DOCS, 'offline', 'EXE_RELEASE_BLOCKERS.md'),
            os.path.join(DOCS, 'live-lab', 'LIVE_LAB_PLAN.md'),
            os.path.join(DOCS, 'live-lab', 'LIVE_LAB_CHECKLIST.md'),
            os.path.join(DOCS, 'live-lab', 'VENDOR_WALKTHROUGH_SCRIPTS.md'),
            os.path.join(DOCS, 'live-lab', 'LIVE_EVIDENCE_CAPTURE_TEMPLATE.md'),
        ]
        for path in paths:
            self.assertTrue(os.path.isfile(path), msg=path)

    def test_signing_is_a_blocker_not_a_todo(self):
        text = open(os.path.join(DOCS, 'offline', 'EXE_RELEASE_BLOCKERS.md'), encoding='utf-8').read()
        self.assertIn('B-SIGN-01', text)
        self.assertIn('release blockers', text.lower())
        self.assertNotIn('TODO: sign later', text)

    def test_e2e_strategy_rejects_playwright_in_exe(self):
        text = open(os.path.join(DOCS, 'E2E_ACCEPTANCE_STRATEGY.md'), encoding='utf-8').read()
        self.assertIn('must not', text.lower())
        self.assertIn('Flask test-client', text)
        self.assertIn('HTML contract', text)

    def test_traceability_does_not_promote(self):
        text = open(os.path.join(DOCS, 'READINESS_TRACEABILITY.md'), encoding='utf-8').read()
        self.assertIn('Conditionally ready', text)
        self.assertIn('live-lab-backed', text)
        self.assertIn('none this campaign', text.lower())

    def test_live_lab_plan_says_not_executed(self):
        text = open(os.path.join(DOCS, 'live-lab', 'LIVE_LAB_PLAN.md'), encoding='utf-8').read()
        self.assertIn('Not executed', text)

    def test_execution_kits_exist_and_are_unsigned(self):
        for rel in (
            os.path.join('FROZEN_BASELINE.md'),
            os.path.join('BLOCKER_BREAKDOWN.md'),
            os.path.join('EVIDENCE_README.md'),
            os.path.join('HONESTY_CHECK.md'),
            os.path.join('named-lab', 'LAB_SCOPE.md'),
            os.path.join('named-lab', 'LAB_PRECHECKS.md'),
            os.path.join('named-lab', 'LAB_DEVICE_MATRIX.md'),
            os.path.join('named-lab', 'LAB_COMMANDS.md'),
            os.path.join('named-lab', 'LAB_EXPECTED_OUTPUTS.md'),
            os.path.join('named-lab', 'LAB_EVIDENCE_CAPTURE.md'),
            os.path.join('named-lab', 'LAB_FAILURE_HANDLING.md'),
            os.path.join('named-lab', 'LAB_SIGNOFF.md'),
            os.path.join('airgap', 'AIRGAP_SCOPE.md'),
            os.path.join('airgap', 'AIRGAP_PRECHECKS.md'),
            os.path.join('airgap', 'AIRGAP_INSTALL_STEPS.md'),
            os.path.join('airgap', 'AIRGAP_SMOKE_TESTS.md'),
            os.path.join('airgap', 'AIRGAP_FAILURES.md'),
            os.path.join('airgap', 'AIRGAP_EVIDENCE_CAPTURE.md'),
            os.path.join('airgap', 'AIRGAP_ROLLBACK.md'),
            os.path.join('airgap', 'AIRGAP_SIGNOFF.md'),
        ):
            path = os.path.join(DOCS, rel)
            self.assertTrue(os.path.isfile(path), msg=path)

    def test_signoff_sheets_are_not_pre_passed(self):
        lab = open(os.path.join(DOCS, 'named-lab', 'LAB_SIGNOFF.md'), encoding='utf-8').read()
        ag = open(os.path.join(DOCS, 'airgap', 'AIRGAP_SIGNOFF.md'), encoding='utf-8').read()
        self.assertIn('B-LIVE-01 still open', lab)
        self.assertIn('B-AIRGAP-01 still open', ag)
        self.assertIn('Conditionally ready', open(os.path.join(DOCS, 'FROZEN_BASELINE.md'), encoding='utf-8').read())

    def test_blocker_breakdown_keeps_minimum_ids(self):
        text = open(os.path.join(DOCS, 'BLOCKER_BREAKDOWN.md'), encoding='utf-8').read()
        for bid in (
            'B-LIVE-01', 'B-SIGN-01', 'B-AIRGAP-01', 'B-OVLY-01',
            'B-LACP-01', 'B-ID-01', 'B-SNMP-01',
        ):
            self.assertIn(bid, text)
        self.assertIn('These blockers are open', text)


if __name__ == '__main__':
    unittest.main()
