"""Governance artifacts for the acceptance gate — no live lab implied."""
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, '.cursor', 'docs')


class TestAcceptanceArtifacts(unittest.TestCase):
    def test_required_docs_exist(self):
        for name in (
            'BASELINE_ASSERTIONS.md',
            'ACCEPTANCE_CRITERIA.md',
            'AI_NAVIGATION.md',
            'TOPOLOGY_TEST_MATRIX.md',
        ):
            path = os.path.join(DOCS, name)
            self.assertTrue(os.path.isfile(path), msg=path)

    def test_baseline_does_not_inflate_verdict(self):
        text = open(os.path.join(DOCS, 'BASELINE_ASSERTIONS.md'), encoding='utf-8').read()
        self.assertIn('Conditionally ready', text)
        self.assertIn('Playwright **does not exist**', text)
        self.assertIn('EVPN/VXLAN', text)
        self.assertNotIn('Ready for GA', text)

    def test_acceptance_forbids_fake_overlay(self):
        text = open(os.path.join(DOCS, 'ACCEPTANCE_CRITERIA.md'), encoding='utf-8').read()
        self.assertIn('Invented overlay', text)
        self.assertIn('Playwright alternative', text)
        self.assertIn('fixture', text.lower())

    def test_ai_navigation_hot_spots(self):
        text = open(os.path.join(DOCS, 'AI_NAVIGATION.md'), encoding='utf-8').read()
        self.assertIn('discovery_graph.py', text)
        self.assertIn('dangerous to modify', text)

    def test_traceability_and_e2e_strategy_exist(self):
        self.assertTrue(os.path.isfile(os.path.join(DOCS, 'READINESS_TRACEABILITY.md')))
        self.assertTrue(os.path.isfile(os.path.join(DOCS, 'E2E_ACCEPTANCE_STRATEGY.md')))
        e2e = open(os.path.join(DOCS, 'E2E_ACCEPTANCE_STRATEGY.md'), encoding='utf-8').read()
        self.assertIn('Playwright', e2e)
        self.assertIn('not the product', e2e.lower())
        self.assertTrue(os.path.isfile(os.path.join(DOCS, 'FROZEN_BASELINE.md')))
        self.assertTrue(os.path.isfile(os.path.join(DOCS, 'EVIDENCE_README.md')))
        frozen = open(os.path.join(DOCS, 'FROZEN_BASELINE.md'), encoding='utf-8').read()
        self.assertIn('Conditionally ready', frozen)
        self.assertIn('236 passed', frozen)
        self.assertIn('277 passed', frozen)


if __name__ == '__main__':
    unittest.main()
