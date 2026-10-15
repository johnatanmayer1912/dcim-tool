"""Vault credential_id is the username key. Fail closed on stale or invalid ids."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.credential_manager import CredentialManager
from utils.vault_credentials import (
    CredentialResolveError,
    parse_credential_id,
    resolve_execute_credentials,
)


class TestParseCredentialId(unittest.TestCase):
    def test_omitted_and_blank(self):
        self.assertIsNone(parse_credential_id(None))
        self.assertIsNone(parse_credential_id(''))
        self.assertIsNone(parse_credential_id('  '))

    def test_valid(self):
        self.assertEqual(parse_credential_id('netops'), 'netops')

    def test_invalid(self):
        with self.assertRaises(CredentialResolveError):
            parse_credential_id('../admin')
        with self.assertRaises(CredentialResolveError):
            parse_credential_id(12)
        with self.assertRaises(CredentialResolveError):
            parse_credential_id('a' * 200)


class TestResolveExecuteCredentials(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cm = CredentialManager(storage_dir=self.tmp)
        self.cm.add_credential('netops', 'secret1', admin_password='en1', label='Lab A')
        self.cm.add_credential('backup', 'secret2', label='Lab B')

    def test_valid_id_uses_vault_not_payload_password(self):
        out = resolve_execute_credentials(
            {'credential_id': 'netops', 'password': 'wrong'},
            self.cm,
        )
        self.assertEqual(out['source'], 'vault')
        self.assertEqual(out['password'], 'secret1')
        self.assertEqual(out['enable_pwd'], 'en1')
        self.assertEqual(out['credential_id'], 'netops')
        listed = {r['credential_id']: r for r in self.cm.list_credentials()}
        self.assertTrue(listed['netops'].get('last_used_at'))
        self.assertNotIn('password', listed['netops'])

    def test_missing_id_uses_payload_when_not_required(self):
        out = resolve_execute_credentials(
            {'username': 'typed', 'password': 'pw'},
            self.cm,
        )
        self.assertEqual(out['source'], 'payload_or_session')
        self.assertEqual(out['username'], 'typed')
        self.assertEqual(out['password'], 'pw')
        self.assertIsNone(out['credential_id'])

    def test_missing_id_rejected_when_required(self):
        with self.assertRaises(CredentialResolveError) as ctx:
            resolve_execute_credentials(
                {'username': 'typed', 'password': 'pw'},
                self.cm,
                credential_id_required=True,
            )
        self.assertEqual(ctx.exception.status, 400)

    def test_plaintext_body_rejected_when_required(self):
        with self.assertRaises(CredentialResolveError) as ctx:
            resolve_execute_credentials(
                {'credential_id': 'netops', 'password': 'wrong'},
                self.cm,
                credential_id_required=True,
            )
        self.assertEqual(ctx.exception.status, 400)

    def test_unknown_id(self):
        with self.assertRaises(CredentialResolveError) as ctx:
            resolve_execute_credentials({'credential_id': 'ghost'}, self.cm)
        self.assertEqual(ctx.exception.status, 404)

    def test_invalid_id(self):
        with self.assertRaises(CredentialResolveError):
            resolve_execute_credentials({'credential_id': 'a/b'}, self.cm)

    def test_deleted_id(self):
        self.cm.remove_credential('backup')
        with self.assertRaises(CredentialResolveError) as ctx:
            resolve_execute_credentials({'credential_id': 'backup'}, self.cm)
        self.assertEqual(ctx.exception.status, 404)

    def test_rotated_secret(self):
        self.cm.update_credential('netops', password='secret1b')
        out = resolve_execute_credentials({'credential_id': 'netops'}, self.cm)
        self.assertEqual(out['password'], 'secret1b')

    def test_multiple_profiles(self):
        a = resolve_execute_credentials({'credential_id': 'netops'}, self.cm)
        b = resolve_execute_credentials({'credential_id': 'backup'}, self.cm)
        self.assertEqual(a['password'], 'secret1')
        self.assertEqual(b['password'], 'secret2')

    def test_username_mismatch(self):
        with self.assertRaises(CredentialResolveError):
            resolve_execute_credentials(
                {'credential_id': 'netops', 'username': 'other'},
                self.cm,
            )

    def test_locked_vault(self):
        self.cm.set_master_password('master-pass')
        locked = CredentialManager(storage_dir=self.tmp)
        with self.assertRaises(CredentialResolveError) as ctx:
            resolve_execute_credentials({'credential_id': 'netops'}, locked)
        self.assertEqual(ctx.exception.status, 403)


class TestCredentialIdApi(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cm = CredentialManager(storage_dir=self.tmp)
        self.cm.add_credential('netops', 'hunter2', label='Ops')
        from vlan_checker_web import app
        import vlan_checker_web as web
        self.web = web
        self._orig = web.credential_manager
        web.credential_manager = self.cm
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.local = {'REMOTE_ADDR': '127.0.0.1'}

    def tearDown(self):
        self.web.credential_manager = self._orig

    def test_list_includes_id_without_secret(self):
        r = self.client.get('/api/credentials/list', environ_base=self.local)
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertNotIn('hunter2', str(body))
        row = body['credentials'][0]
        self.assertEqual(row['credential_id'], 'netops')
        self.assertNotIn('password', row)

    def test_execute_unknown_id(self):
        r = self.client.post(
            '/api/execute',
            json={'action': 'connectivity', 'credential_id': 'ghost', 'inventory': '10.0.0.1,cisco_ios'},
            environ_base=self.local,
        )
        self.assertEqual(r.status_code, 404)
        body = r.get_json()
        self.assertNotIn('hunter2', str(body).lower())
        self.assertIn('credential_id', body.get('error', '').lower())

    def test_execute_valid_id_does_not_echo_secret(self):
        r = self.client.post(
            '/api/execute',
            json={'action': 'connectivity', 'credential_id': 'netops', 'inventory': '10.0.0.1,cisco_ios'},
            environ_base=self.local,
        )
        self.assertNotEqual(r.status_code, 403)
        self.assertNotEqual(r.status_code, 404)
        body = r.get_json() or {}
        blob = str(body).lower()
        self.assertNotIn('hunter2', blob)
        if r.status_code == 200 and body.get('status') == 'started':
            self.assertEqual(body.get('credential_id'), 'netops')

    def test_execute_invalid_id(self):
        r = self.client.post(
            '/api/execute',
            json={'action': 'connectivity', 'credential_id': '../x', 'inventory': '10.0.0.1,cisco_ios'},
            environ_base=self.local,
        )
        self.assertEqual(r.status_code, 400)
        self.assertNotIn('hunter2', str(r.get_json()).lower())

    def test_get_missing_credential(self):
        r = self.client.get('/api/credentials/get/nope', environ_base=self.local)
        self.assertEqual(r.status_code, 404)
        self.assertNotIn('hunter2', str(r.get_json()).lower())

    def test_resolve_audit_has_no_secret(self):
        with patch('vlan_checker_web.add_log') as log:
            self.client.post(
                '/api/execute',
                json={'action': 'connectivity', 'credential_id': 'netops', 'inventory': '10.0.0.1,cisco_ios'},
                environ_base=self.local,
            )
        joined = ' '.join(str(c) for c in log.call_args_list)
        self.assertNotIn('hunter2', joined.lower())


if __name__ == '__main__':
    unittest.main()
