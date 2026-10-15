"""Reality-loop API contracts — loopback only, no live SSH."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.session_cred_cache import clear_session_credentials


class TestProgramStatusApiHonesty(unittest.TestCase):
    def setUp(self):
        import vlan_checker_web as web
        self.web = web
        self.client = web.app.test_client()
        self.env = {'REMOTE_ADDR': '127.0.0.1'}
        clear_session_credentials()

    def tearDown(self):
        clear_session_credentials()

    def test_program_status_blocked_hard_stop(self):
        resp = self.client.get('/api/discovery/program-status', environ_base=self.env)
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        ready = body.get('readiness') or {}
        self.assertEqual(ready.get('release_gate'), 'BLOCKED')
        self.assertTrue(ready.get('hard_stop'))
        self.assertFalse(ready.get('may_claim_enterprise_ready'))
        self.assertFalse(ready.get('may_claim_live_vendor_validated'))
        blob = str(body)
        self.assertNotIn('s3cret', blob)
        self.assertNotRegex(blob, r'"password"\s*:\s*"[^"]+"')

    def test_jobs_empty_or_list_without_secrets(self):
        resp = self.client.get('/api/jobs', environ_base=self.env)
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        blob = str(body)
        self.assertNotIn('s3cret', blob)
        self.assertNotIn('-----BEGIN', blob)
        self.assertNotRegex(blob, r'"password"\s*:\s*"[^"]+"')

    def test_version_present(self):
        resp = self.client.get('/api/version', environ_base=self.env)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue((resp.get_json() or {}).get('version'))

    def test_missing_discovery_report_is_client_error(self):
        resp = self.client.get(
            '/api/discovery/report/no-such-job-id',
            environ_base=self.env,
        )
        self.assertGreaterEqual(resp.status_code, 400)
        self.assertLess(resp.status_code, 500)

    def test_remote_program_status_not_required_secret(self):
        """Program status is diagnostic; still no vault dump if remotely fetched."""
        resp = self.client.get(
            '/api/discovery/program-status',
            environ_base={'REMOTE_ADDR': '203.0.113.10'},
        )
        self.assertIn(resp.status_code, (200, 403))
        if resp.status_code == 200:
            blob = str(resp.get_json())
            self.assertNotIn('credential_key', blob)
            self.assertNotIn('.credential_key', blob)


if __name__ == '__main__':
    unittest.main()
