"""GET /api/credentials/get must not return plaintext secrets (RB-ZT credential exposure).

Loopback is not identity. The Use flow selects credential_id; the server
resolves vault secrets in process memory immediately before adapter use.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.credential_manager import CredentialManager
from utils.vault_credentials import (
    mapping_has_secret_fields,
    public_credential_view,
    resolve_execute_credentials,
)

SECRET = 'hunter2-secret-xyz'
ENABLE = 'enable-secret-xyz'
BECOME = 'become-secret-xyz'
HTML = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'modules', 'web', 'templates', 'index.html',
)

_FORBIDDEN_KEYS = {
    'password',
    'admin_password',
    'become_password',
    'enable_password',
    'enable_pwd',
    'secret',
    'private_key',
    'privatekey',
    'token',
    'api_key',
    'apikey',
    'passphrase',
    'master_password',
    'credential_key',
    'snmp_community',
    'snmp_v3_auth_key',
    'snmp_v3_priv_key',
}


def _blob(obj) -> str:
    return str(obj).lower()


def _assert_no_secrets(testcase, obj, *extra):
    blob = _blob(obj)
    testcase.assertNotIn(SECRET.lower(), blob)
    testcase.assertNotIn(ENABLE.lower(), blob)
    testcase.assertNotIn(BECOME.lower(), blob)
    for needle in extra:
        testcase.assertNotIn(str(needle).lower(), blob)
    testcase.assertFalse(mapping_has_secret_fields(obj))


class TestPublicCredentialView(unittest.TestCase):
    def test_whitelist_drops_secret_and_unknown_fields(self):
        view = public_credential_view({
            'username': 'netops',
            'password': SECRET,
            'admin_password': ENABLE,
            'become_password': BECOME,
            'private_key': '-----BEGIN KEY-----',
            'token': 'tok',
            'api_key': 'ak',
            'extra_secret': 'should-not-copy',
            'label': 'Ops',
            'created_at': '2026-01-01T00:00:00',
            'updated_at': '2026-01-02T00:00:00',
            'last_used_at': None,
        }, 'netops')
        self.assertEqual(view['credential_id'], 'netops')
        self.assertEqual(view['username'], 'netops')
        self.assertEqual(view['label'], 'Ops')
        self.assertTrue(view['has_admin'])
        self.assertTrue(view['has_become'])
        self.assertTrue(view['available'])
        self.assertEqual(set(view), {
            'credential_id', 'username', 'label', 'has_admin', 'has_become',
            'has_snmp', 'snmp_version', 'profile_type', 'has_ssh',
            'created_at', 'updated_at', 'last_used_at', 'available',
        })
        _assert_no_secrets(self, view)
        self.assertNotIn('extra_secret', view)

    def test_mapping_detector_ignores_has_flags(self):
        self.assertFalse(mapping_has_secret_fields({'has_password': True, 'has_admin': False}))
        self.assertTrue(mapping_has_secret_fields({'password': SECRET}))
        self.assertTrue(mapping_has_secret_fields({'passwd_password': 'x'}))
        self.assertTrue(mapping_has_secret_fields({'private_key': 'k'}))
        self.assertTrue(mapping_has_secret_fields({'nested': {'token': 't'}}))


class TestCredentialSecretApi(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cm = CredentialManager(storage_dir=self.tmp)
        self.cm.add_credential(
            'netops', SECRET, admin_password=ENABLE, become_password=BECOME, label='Ops',
        )
        self.cm.add_credential('backup', 'backup-secret-xyz', label='Lab B')
        from vlan_checker_web import app
        import vlan_checker_web as web
        self.web = web
        self._orig = web.credential_manager
        web.credential_manager = self.cm
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.local = {'REMOTE_ADDR': '127.0.0.1'}
        from utils.session_cred_cache import clear_session_credentials
        clear_session_credentials()

    def tearDown(self):
        self.web.credential_manager = self._orig
        from utils.session_cred_cache import clear_session_credentials
        clear_session_credentials()

    def _get(self, path, **kw):
        kw.setdefault('environ_base', dict(self.local))
        return self.client.get(path, **kw)

    def _post(self, path, json=None, **kw):
        kw.setdefault('environ_base', dict(self.local))
        if json is not None:
            kw['json'] = json
        return self.client.post(path, **kw)

    def test_list_is_metadata_only(self):
        r = self._get('/api/credentials/list')
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        _assert_no_secrets(self, body)
        rows = {row['credential_id']: row for row in body['credentials']}
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows['netops']['label'], 'Ops')
        self.assertTrue(rows['netops']['has_admin'])
        self.assertTrue(rows['netops']['available'])
        self.assertNotIn('password', rows['netops'])
        self.assertNotIn('private_key', rows['netops'])
        self.assertEqual(rows['backup']['username'], 'backup')
        self.assertNotEqual(rows['netops']['credential_id'], rows['backup']['credential_id'])

    def test_get_is_metadata_only(self):
        r = self._get('/api/credentials/get/netops')
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        cred = body['credential']
        _assert_no_secrets(self, body)
        self.assertEqual(cred['credential_id'], 'netops')
        self.assertEqual(cred['username'], 'netops')
        for key in _FORBIDDEN_KEYS:
            self.assertNotIn(key, cred)
        self.assertNotIn('password', cred)
        self.assertNotIn('admin_password', cred)
        self.assertNotIn('become_password', cred)
        self.assertNotIn('private_key', cred)
        self.assertNotIn('token', cred)

    def test_get_strips_secrets_even_if_vault_record_is_leaky(self):
        leaky = dict(self.cm.get_credential('netops'))
        leaky['private_key'] = 'FAKE-PRIVATE-KEY'
        leaky['api_key'] = 'FAKE-API-KEY'
        leaky['token'] = 'FAKE-TOKEN'
        with patch.object(self.cm, 'get_credential', return_value=leaky):
            r = self._get('/api/credentials/get/netops')
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        _assert_no_secrets(self, body, 'FAKE-PRIVATE-KEY', 'FAKE-API-KEY', 'FAKE-TOKEN')
        cred = body['credential']
        for key in _FORBIDDEN_KEYS:
            self.assertNotIn(key, cred)

    def test_get_missing_and_deleted(self):
        r = self._get('/api/credentials/get/nope')
        self.assertEqual(r.status_code, 404)
        _assert_no_secrets(self, r.get_json())
        self.cm.remove_credential('backup')
        r2 = self._get('/api/credentials/get/backup')
        self.assertEqual(r2.status_code, 404)
        _assert_no_secrets(self, r2.get_json())

    def test_get_locked_vault(self):
        self.cm.set_master_password('master-pass')
        locked = CredentialManager(storage_dir=self.tmp)
        self.web.credential_manager = locked
        r = self._get('/api/credentials/get/netops')
        self.assertEqual(r.status_code, 403)
        body = r.get_json()
        _assert_no_secrets(self, body)
        self.assertIn('locked', (body.get('error') or '').lower())

    def test_execute_missing_credential_id_is_400(self):
        inv = '10.0.0.1,cisco_ios'
        r = self._post('/api/execute', json={'action': 'connectivity', 'inventory': inv})
        self.assertEqual(r.status_code, 400)
        body = r.get_json() or {}
        _assert_no_secrets(self, body)
        self.assertIn('credential_id', (body.get('error') or '').lower())

    def test_execute_rejects_plaintext_password_in_body(self):
        inv = '10.0.0.1,cisco_ios'
        r = self._post('/api/execute', {
            'action': 'connectivity',
            'inventory': inv,
            'username': 'netops',
            'password': SECRET,
        })
        self.assertEqual(r.status_code, 400)
        body = r.get_json() or {}
        _assert_no_secrets(self, body)
        self.assertIn('plaintext', (body.get('error') or '').lower())

    def test_execute_missing_invalid_deleted_locked(self):
        inv = '10.0.0.1,cisco_ios'
        r = self._post('/api/execute', {'action': 'connectivity', 'credential_id': 'ghost', 'inventory': inv})
        self.assertEqual(r.status_code, 404)
        _assert_no_secrets(self, r.get_json())

        r = self._post('/api/execute', {'action': 'connectivity', 'credential_id': '../x', 'inventory': inv})
        self.assertEqual(r.status_code, 400)
        _assert_no_secrets(self, r.get_json())

        self.cm.remove_credential('backup')
        r = self._post('/api/execute', {'action': 'connectivity', 'credential_id': 'backup', 'inventory': inv})
        self.assertEqual(r.status_code, 404)
        _assert_no_secrets(self, r.get_json())

        self.cm.set_master_password('master-pass')
        locked = CredentialManager(storage_dir=self.tmp)
        self.web.credential_manager = locked
        r = self._post('/api/execute', {'action': 'connectivity', 'credential_id': 'netops', 'inventory': inv})
        self.assertEqual(r.status_code, 403)
        _assert_no_secrets(self, r.get_json())

    def test_execute_resolves_server_side_without_echo(self):
        r = self._post(
            '/api/execute',
            {'action': 'connectivity', 'credential_id': 'netops', 'inventory': '10.0.0.1,cisco_ios'},
        )
        self.assertNotIn(r.status_code, (403, 404))
        body = r.get_json() or {}
        _assert_no_secrets(self, body)
        if r.status_code == 200 and body.get('status') == 'started':
            self.assertEqual(body.get('credential_id'), 'netops')

    def test_rotated_credential_remains_usable(self):
        self.cm.update_credential('netops', password='rotated-secret-xyz')
        out = resolve_execute_credentials({'credential_id': 'netops'}, self.cm)
        self.assertEqual(out['password'], 'rotated-secret-xyz')
        r = self._post(
            '/api/execute',
            {'action': 'connectivity', 'credential_id': 'netops', 'inventory': '10.0.0.1,cisco_ios'},
        )
        blob = _blob(r.get_json() or {})
        self.assertNotIn('rotated-secret-xyz', blob)
        self.assertNotIn(SECRET.lower(), blob)

    def test_vlan_validate_accepts_credential_id_without_password(self):
        r = self._post(
            '/api/vlan/validate',
            {
                'action': 'add_vlan',
                'vlan_id': 10,
                'credential_id': 'netops',
                'inventory': '10.0.0.1,cisco_ios',
            },
        )
        body = r.get_json() or {}
        _assert_no_secrets(self, body)
        self.assertNotEqual((body.get('error') or '').lower(), 'credentials required')

    def test_im_discover_missing_body_and_session_is_400(self):
        from utils.session_cred_cache import clear_session_credentials
        clear_session_credentials()
        r = self._post('/api/interface/discover', {'host': 'test'})
        self.assertEqual(r.status_code, 400)
        body = r.get_json() or {}
        _assert_no_secrets(self, body)
        self.assertIn('required', (body.get('error') or '').lower())

    def test_execute_logs_and_audit_omit_secret(self):
        with patch('vlan_checker_web.add_log') as log:
            self._get('/api/credentials/get/netops')
            self._post(
                '/api/execute',
                {'action': 'connectivity', 'credential_id': 'netops', 'inventory': '10.0.0.1,cisco_ios'},
            )
        joined = ' '.join(str(c) for c in log.call_args_list)
        self.assertNotIn(SECRET.lower(), joined.lower())
        self.assertNotIn(ENABLE.lower(), joined.lower())
        logs = self._get('/api/logs')
        _assert_no_secrets(self, logs.get_json() or {})

    def test_malformed_json_and_duplicate_submit(self):
        r = self.client.post(
            '/api/execute',
            data='{not json',
            content_type='application/json',
            environ_base=self.local,
        )
        self.assertEqual(r.status_code, 400)
        _assert_no_secrets(self, r.get_json() or {})
        payload = {'action': 'connectivity', 'credential_id': 'netops', 'inventory': '10.0.0.1,cisco_ios'}
        a = self._post('/api/execute', payload)
        b = self._post('/api/execute', payload)
        _assert_no_secrets(self, a.get_json() or {})
        _assert_no_secrets(self, b.get_json() or {})

    def test_nonlocal_denied(self):
        remote = {'REMOTE_ADDR': '203.0.113.10'}
        r = self.client.get('/api/credentials/get/netops', environ_base=remote)
        self.assertEqual(r.status_code, 403)
        _assert_no_secrets(self, r.get_json() or {})
        r2 = self.client.post(
            '/api/execute',
            json={'action': 'connectivity', 'credential_id': 'netops', 'inventory': '10.0.0.1,cisco_ios'},
            environ_base=remote,
        )
        self.assertEqual(r2.status_code, 403)
        _assert_no_secrets(self, r2.get_json() or {})

    def test_foreign_origin_denied_on_mutate_get_skips_origin(self):
        r = self._post(
            '/api/execute',
            {'action': 'connectivity', 'credential_id': 'netops', 'inventory': '10.0.0.1,cisco_ios'},
            headers={'Origin': 'http://evil.example'},
        )
        self.assertEqual(r.status_code, 403)
        _assert_no_secrets(self, r.get_json() or {})
        # GET skips Origin (documented dual-mode). Metadata-only so CSRF GET cannot steal secrets.
        r2 = self._get('/api/credentials/get/netops', headers={'Origin': 'http://evil.example'})
        self.assertEqual(r2.status_code, 200)
        _assert_no_secrets(self, r2.get_json())

    def test_empty_origin_loopback_allowed(self):
        r = self._post(
            '/api/execute',
            {'action': 'connectivity', 'credential_id': 'netops', 'inventory': '10.0.0.1,cisco_ios'},
        )
        self.assertNotEqual(r.status_code, 403)
        _assert_no_secrets(self, r.get_json() or {})

    def test_session_view_includes_id_not_secret(self):
        r = self._post(
            '/api/session/credentials',
            {'username': 'netops', 'credential_id': 'netops', 'password': SECRET, 'label': 'Ops'},
        )
        self.assertEqual(r.status_code, 200)
        got = self._get('/api/session/credentials')
        body = got.get_json()
        self.assertEqual(body.get('credential_id'), 'netops')
        self.assertFalse(body.get('has_password'))
        _assert_no_secrets(self, body)


class TestCredentialFrontendContract(unittest.TestCase):
    def setUp(self):
        with open(HTML, encoding='utf-8') as fh:
            self.html = fh.read()

    def test_use_selects_credential_id_without_secret_copy(self):
        self.assertIn('function useCredential', self.html)
        self.assertIn('function nstCredentialRequestBody', self.html)
        self.assertIn('nstApplyCredentialMetadata', self.html)
        self.assertNotIn('d.credential.password', self.html)
        self.assertNotIn('d.credential.admin_password', self.html)
        self.assertNotIn('d.credential.become_password', self.html)
        self.assertNotIn('data-password', self.html.lower())
        self.assertNotIn('data-private-key', self.html.lower())
        start = self.html.index('async function useCredential')
        end = self.html.index('function clearCredentialLabel')
        use_fn = self.html[start:end]
        self.assertIn('credential_id', use_fn)
        self.assertNotIn('.password', use_fn)
        self.assertNotIn('admin_password', use_fn)
        self.assertIn('nstApplyCredentialMetadata', use_fn)
        self.assertIn('Credential is unavailable', use_fn)
        apply_start = self.html.index('function nstApplyCredentialMetadata')
        apply_end = self.html.index('async function loadCredentials')
        apply_fn = self.html[apply_start:apply_end]
        self.assertIn("pwd.value = ''", apply_fn)
        self.assertNotIn('cred.password', apply_fn)

    def test_execute_payload_sends_credential_id(self):
        self.assertIn('credential_id: creds.credential_id', self.html)
        self.assertIn('nstRequireTaskCredentials', self.html)
        self.assertNotIn('password: creds.password', self.html.split('function runAction', 1)[1][:2500])

    def test_no_secret_in_query_or_storage(self):
        start = self.html.index('async function useCredential')
        end = self.html.index('function clearCredentialLabel')
        use_fn = self.html[start:end]
        self.assertNotIn('?password', use_fn)
        self.assertNotIn('localStorage', use_fn)
        self.assertNotIn('sessionStorage', use_fn)


if __name__ == '__main__':
    unittest.main()
