"""Phase 6 Wave 1 — Discovery Program Status (operator workspace).

Protects: confirmed vs incomplete vs readiness hard-stop stay separated;
API/UI reuse Phase 5 register; no enterprise/live overclaim.
"""
from __future__ import annotations

import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html')
REPORT = os.path.join(ROOT, 'tests', 'qa', 'PHASE6_WAVE1_DISCOVERY_PROGRAM_STATUS.md')
QA = os.path.join(ROOT, 'tests', 'qa', 'PHASE6_WAVE1_DISCOVERY_PROGRAM_STATUS.md')


class TestBuildProgramStatus(unittest.TestCase):
    def test_no_job_keeps_gate_blocked(self):
        from utils.discovery_program_status import build_discovery_program_status

        payload = build_discovery_program_status(job=None)
        self.assertEqual(payload['schema'], 'nst.phase6.discovery_program_status.v1')
        self.assertFalse(payload['readiness']['enterprise_operational_ready'])
        self.assertFalse(payload['readiness']['live_vendor_truncated_cdp_lldp_validated'])
        self.assertEqual(payload['readiness']['release_gate'], 'BLOCKED')
        self.assertTrue(payload['readiness']['hard_stop'])
        self.assertFalse(payload['readiness']['may_claim_enterprise_ready'])
        self.assertFalse(payload['discovery']['job_present'])
        self.assertEqual(payload['discovery']['confirmed_link_count'], 0)
        ids = [c['id'] for c in payload['categories']]
        self.assertEqual(
            ids,
            ['confirmed_topology', 'incomplete_observations', 'readiness_release_gate'],
        )
        self.assertIn('hard stop', (payload['honesty']['note'] or '').lower())

    def test_job_counts_do_not_clear_gate(self):
        from utils.discovery_program_status import build_discovery_program_status

        job = {
            'status': 'complete',
            'scan_profile': 'standard',
            'max_depth': 2,
            'result': {
                'data': {
                    'devices': [
                        {'hostname': 'A', 'incomplete_observation_count': 2},
                        {'hostname': 'B', 'incomplete_observation_count': 0},
                    ],
                    'links': [
                        {'from': 'A', 'to': 'B', 'local_port': 'Gi1/0/1', 'remote_port': 'Gi1/0/2'},
                        {'from': 'A', 'to': 'X', 'incomplete': True, 'edge_eligible': False},
                    ],
                    'incomplete_observation_count': 2,
                    'collection_status': 'complete',
                }
            },
        }
        payload = build_discovery_program_status(job=job)
        self.assertTrue(payload['discovery']['job_present'])
        self.assertEqual(payload['discovery']['confirmed_device_count'], 2)
        self.assertEqual(payload['discovery']['confirmed_link_count'], 1)
        self.assertEqual(payload['discovery']['incomplete_observation_count'], 2)
        self.assertEqual(payload['readiness']['release_gate'], 'BLOCKED')
        self.assertTrue(payload['readiness']['hard_stop'])
        self.assertFalse(payload['honesty']['enterprise_operational_ready'])


class TestProgramStatusApi(unittest.TestCase):
    def test_api_returns_blocked_without_job(self):
        import vlan_checker_web as web

        with web.app.test_client() as client:
            r = client.get(
                '/api/discovery/program-status',
                environ_base={'REMOTE_ADDR': '127.0.0.1'},
            )
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(data['schema'], 'nst.phase6.discovery_program_status.v1')
        self.assertEqual(data['readiness']['release_gate'], 'BLOCKED')
        self.assertTrue(data['readiness']['hard_stop'])
        self.assertFalse(data['readiness']['may_claim_enterprise_ready'])


class TestUiAndDocs(unittest.TestCase):
    def test_index_has_program_status_panel(self):
        text = open(INDEX, encoding='utf-8').read()
        self.assertIn('disc-program-status', text)
        self.assertIn('discRefreshProgramStatus', text)
        self.assertIn('/api/discovery/program-status', text)
        self.assertIn('HARD STOP — not advisory', text)
        self.assertNotIn('almost ready', text.lower())

    def test_docs(self):
        for path in (REPORT, QA):
            text = open(path, encoding='utf-8').read().lower()
            self.assertIn('phase 6', text)
            self.assertIn('program status', text)
            self.assertIn('blocked', text)
            self.assertIn('hard stop', text)
            self.assertNotIn('live vendor truncated cdp/lldp validated', text)


if __name__ == '__main__':
    unittest.main()
