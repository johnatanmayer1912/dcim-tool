"""RB-ZT-08: /api/execute requires vault credential_id; plaintext secrets rejected."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.credential_manager import CredentialManager

SECRET = 'execute-plaintext-must-not-work'


class TestExecuteCredentialIdOnly(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cm = CredentialManager(storage_dir=self.tmp)
        self.cm.add_credential('netops', SECRET, label='Ops')
        from vlan_checker_web import app
        import vlan_checker_web as web

        self.web = web
        self._orig = web.credential_manager
        web.credential_manager = self.cm
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.local = {'REMOTE_ADDR': '127.0.0.1'}
        self.inv = '10.0.0.1,cisco_ios'

    def tearDown(self):
        self.web.credential_manager = self._orig

    def _post(self, payload):
        return self.client.post('/api/execute', json=payload, environ_base=self.local)

    def test_execute_logs_audit_without_secret(self):
        with patch('vlan_checker_web.add_log') as log:
            r = self._post({'action': 'connectivity', 'credential_id': 'netops', 'inventory': self.inv})
        self.assertNotEqual(r.status_code, 403)
        joined = ' '.join(str(c) for c in log.call_args_list)
        self.assertIn('[Execute Audit]', joined)
        self.assertIn('credential_id=netops', joined)
        self.assertNotIn(SECRET.lower(), joined.lower())

    def test_cross_origin_execute_rejected(self):
        r = self.client.post(
            '/api/execute',
            json={'action': 'connectivity', 'credential_id': 'netops', 'inventory': self.inv},
            environ_base=self.local,
            headers={'Origin': 'http://evil.example'},
        )
        self.assertEqual(r.status_code, 403)


if __name__ == '__main__':
    unittest.main()
