"""Socket.IO CLI credential_id contract (RB-ZT Socket.IO / F-SOCK-02).

flask_socketio is optional. These tests cover resolver, session isolation,
HTML contract, locality helpers, and adapter-level vault resolve.
They do not claim a live Socket.IO handshake unless flask_socketio imports.
"""
from __future__ import annotations

import os
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.credential_manager import CredentialManager
from modules.cli_manager import (
    CLIConnection,
    bind_cli_owner,
    cli_owner_matches,
    disconnect_all_sessions,
    release_cli_owner,
    remove_cli_session,
    session_ids_owned_by_sid,
)
from utils.vault_credentials import (
    mapping_has_secret_fields,
    public_cli_status_payload,
    resolve_cli_connect_credentials,
)


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, 'vlan_checker_web.py')
CLI_HTML = os.path.join(ROOT, 'modules', 'web', 'templates', 'cli_terminal.html')
SECRET = 'vault-cli-secret-never-echo'


class TestResolveCliConnectCredentials(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cm = CredentialManager(storage_dir=self.tmp)
        self.cm.add_credential('netops', SECRET, admin_password='en1', label='Lab A')

    def test_valid_credential_id_resolves_server_side(self):
        out, err = resolve_cli_connect_credentials(
            {'credential_id': 'netops', 'username': 'netops'},
            self.cm,
        )
        self.assertIsNone(err)
        self.assertEqual(out['source'], 'vault')
        self.assertEqual(out['password'], SECRET)
        self.assertEqual(out['enable_pwd'], 'en1')
        self.assertEqual(out['credential_id'], 'netops')

    def test_credential_id_wins_over_client_password(self):
        out, err = resolve_cli_connect_credentials(
            {
                'credential_id': 'netops',
                'username': 'netops',
                'password': 'client-typed-wrong',
                'enable_password': 'client-en',
            },
            self.cm,
        )
        self.assertIsNone(err)
        self.assertEqual(out['password'], SECRET)
        self.assertEqual(out['enable_pwd'], 'en1')
        self.assertNotEqual(out['password'], 'client-typed-wrong')

    def test_missing_credentials(self):
        _out, err = resolve_cli_connect_credentials({'host': '1.1.1.1'}, self.cm)
        self.assertEqual(err['code'], 'credential_id_required')

    def test_invalid_credential_id(self):
        _out, err = resolve_cli_connect_credentials({'credential_id': '../admin'}, self.cm)
        self.assertEqual(err['code'], 'invalid_credential_id')

    def test_wrong_credential_type(self):
        _out, err = resolve_cli_connect_credentials({'credential_id': 12}, self.cm)
        self.assertEqual(err['code'], 'invalid_credential_id')

    def test_unknown_credential_id(self):
        _out, err = resolve_cli_connect_credentials({'credential_id': 'ghost'}, self.cm)
        self.assertEqual(err['code'], 'unknown_credential_id')

    def test_deleted_credential(self):
        self.cm.remove_credential('netops')
        _out, err = resolve_cli_connect_credentials({'credential_id': 'netops'}, self.cm)
        self.assertEqual(err['code'], 'unknown_credential_id')

    def test_locked_vault(self):
        self.cm.set_master_password('master-pass')
        locked = CredentialManager(storage_dir=self.tmp)
        _out, err = resolve_cli_connect_credentials({'credential_id': 'netops'}, locked)
        self.assertEqual(err['code'], 'vault_locked')

    def test_malformed_payload(self):
        _out, err = resolve_cli_connect_credentials(None, self.cm)
        self.assertEqual(err['code'], 'malformed_payload')
        _out, err = resolve_cli_connect_credentials('not-a-dict', self.cm)
        self.assertEqual(err['code'], 'malformed_payload')

    def test_username_password_only_rejected(self):
        _out, err = resolve_cli_connect_credentials(
            {'username': 'typed', 'password': 'pw-local'},
            self.cm,
        )
        self.assertEqual(err['code'], 'credential_id_required')

    def test_env_cannot_enable_plaintext(self):
        with patch.dict(os.environ, {'NST_CLI_PLAINTEXT_COMPAT': '1'}, clear=False):
            _out, err = resolve_cli_connect_credentials(
                {'username': 'typed', 'password': 'pw-local'},
                self.cm,
            )
        self.assertEqual(err['code'], 'credential_id_required')

    def test_payload_cannot_enable_plaintext(self):
        _out, err = resolve_cli_connect_credentials(
            {
                'username': 'typed',
                'password': 'pw-local',
                'allow_plaintext': True,
                'plaintext_compat': '1',
                'NST_CLI_PLAINTEXT_COMPAT': '1',
            },
            self.cm,
        )
        self.assertEqual(err['code'], 'credential_id_required')

    def test_failed_credential_id_does_not_fallback_to_plaintext(self):
        _out, err = resolve_cli_connect_credentials(
            {
                'credential_id': 'ghost',
                'username': 'ghost',
                'password': SECRET,
            },
            self.cm,
        )
        self.assertEqual(err['code'], 'unknown_credential_id')

    def test_session_ram_password_is_not_used(self):
        _out, err = resolve_cli_connect_credentials(
            {'username': 'typed'},
            self.cm,
            {'username': 'netops', 'password': SECRET},
        )
        self.assertEqual(err['code'], 'credential_id_required')

    def test_session_credential_id_fallback(self):
        out, err = resolve_cli_connect_credentials(
            {'host': 'sw1'},
            self.cm,
            {'credential_id': 'netops'},
        )
        self.assertIsNone(err)
        self.assertEqual(out['source'], 'vault')
        self.assertEqual(out['password'], SECRET)

    def test_username_mismatch_unavailable(self):
        _out, err = resolve_cli_connect_credentials(
            {'credential_id': 'netops', 'username': 'other'},
            self.cm,
        )
        self.assertEqual(err['code'], 'invalid_credential_id')


class TestPublicCliPayload(unittest.TestCase):
    def test_strips_secrets(self):
        leaked = public_cli_status_payload({
            'status': 'connected',
            'message': 'Ready',
            'password': SECRET,
            'enable_password': 'en',
            'become_password': 'b',
            'token': 't',
            'private_key': 'k',
            'credential_id': 'netops',
            'username': 'netops',
        })
        self.assertEqual(leaked['credential_id'], 'netops')
        self.assertNotIn('password', leaked)
        self.assertNotIn('enable_password', leaked)
        self.assertFalse(mapping_has_secret_fields(leaked))
        self.assertNotIn(SECRET, str(leaked))


class TestCliOwnerIsolation(unittest.TestCase):
    def tearDown(self):
        disconnect_all_sessions()

    def test_owners_are_session_and_sid_specific(self):
        bind_cli_owner('sess-a', 'sid-1')
        bind_cli_owner('sess-b', 'sid-2')
        self.assertTrue(cli_owner_matches('sess-a', 'sid-1'))
        self.assertFalse(cli_owner_matches('sess-a', 'sid-2'))
        self.assertFalse(cli_owner_matches('sess-b', 'sid-1'))
        self.assertEqual(session_ids_owned_by_sid('sid-1'), ['sess-a'])
        release_cli_owner('sess-a')
        self.assertFalse(cli_owner_matches('sess-a', 'sid-1'))
        self.assertTrue(cli_owner_matches('sess-b', 'sid-2'))

    def test_disconnect_cleanup_and_reconnect_isolation(self):
        bind_cli_owner('sess-r', 'sid-old')
        remove_cli_session('sess-r')
        self.assertFalse(cli_owner_matches('sess-r', 'sid-old'))
        bind_cli_owner('sess-r', 'sid-new')
        self.assertTrue(cli_owner_matches('sess-r', 'sid-new'))
        self.assertFalse(cli_owner_matches('sess-r', 'sid-old'))

    def test_repeated_bind_release_does_not_leak(self):
        for i in range(5):
            bind_cli_owner('cycle', f'sid-{i}')
            self.assertEqual(session_ids_owned_by_sid(f'sid-{i}'), ['cycle'])
            release_cli_owner('cycle')
            self.assertEqual(session_ids_owned_by_sid(f'sid-{i}'), [])


class TestScrubSecrets(unittest.TestCase):
    def test_scrub_clears_password_fields(self):
        cli = CLIConnection(
            's1',
            {'host': '127.0.0.1', 'password': SECRET, 'secret': 'en'},
            'u',
            SECRET,
            'en',
        )
        cli.scrub_secrets()
        self.assertEqual(cli.pwd, '')
        self.assertEqual(cli.enb_pwd, '')
        self.assertEqual(cli.device.get('password'), '')
        self.assertEqual(cli.device.get('secret'), '')


class TestSocketIoLocalityHelper(unittest.TestCase):
    def setUp(self):
        from vlan_checker_web import app
        self.app = app

    def test_nonlocal_denied(self):
        from vlan_checker_web import _socketio_operator_denied
        with self.app.test_request_context('/', environ_base={'REMOTE_ADDR': '203.0.113.10'}):
            denied = _socketio_operator_denied()
        self.assertEqual(denied['code'], 'nonlocal')

    def test_foreign_origin_denied(self):
        from vlan_checker_web import _socketio_operator_denied
        with self.app.test_request_context(
            '/',
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
            headers={'Origin': 'http://evil.example'},
        ):
            denied = _socketio_operator_denied()
        self.assertEqual(denied['code'], 'foreign_origin')

    def test_malformed_origin_denied(self):
        from vlan_checker_web import _socketio_operator_denied
        with self.app.test_request_context(
            '/',
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
            headers={'Origin': 'http://127.0.0.1:5051.evil.com'},
        ):
            denied = _socketio_operator_denied()
        self.assertEqual(denied['code'], 'foreign_origin')

    def test_empty_origin_on_loopback_allowed(self):
        from vlan_checker_web import _socketio_operator_denied
        with self.app.test_request_context('/', environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            self.assertIsNone(_socketio_operator_denied())

    def test_trusted_origin_on_loopback_allowed(self):
        from vlan_checker_web import _socketio_operator_denied
        with self.app.test_request_context(
            '/',
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
            headers={'Origin': 'http://127.0.0.1:5051'},
        ):
            self.assertIsNone(_socketio_operator_denied())


class TestHtmlAndSourceContract(unittest.TestCase):
    def test_cli_html_requires_credential_id_no_password_fields(self):
        html = open(CLI_HTML, encoding='utf-8').read()
        self.assertIn('connCredentialId', html)
        self.assertIn('connCredentialSelect', html)
        self.assertIn('credential_id: credentialId', html)
        self.assertIn('credential_id required', html)
        self.assertIn('/api/credentials/list', html)
        self.assertNotIn('connPassword', html)
        self.assertNotIn('connEnablePassword', html)
        self.assertNotIn('CLI_PLAINTEXT_COMPAT', html)
        self.assertNotIn('NST_CLI_PLAINTEXT_COMPAT', html)
        self.assertNotIn('plaintextCompat', html)
        self.assertNotIn("?password=", html)
        self.assertNotIn('data-password', html)
        self.assertNotIn('localStorage', html)
        self.assertNotIn('sessionStorage', html)
        connect_fn = html.split('function connect()')[1].split('function sendCommand')[0]
        self.assertNotIn('payload.password', connect_fn)
        self.assertNotIn('enable_password', connect_fn)

    def test_web_handlers_resolve_and_do_not_log_payload_secrets(self):
        src = open(WEB, encoding='utf-8').read()
        self.assertIn('resolve_cli_connect_credentials', src)
        self.assertNotIn('plaintext_compat', src)
        self.assertNotIn('NST_CLI_PLAINTEXT_COMPAT', src)
        self.assertNotIn('cli_plaintext_compat', src)
        self.assertIn('session_isolated', src)
        self.assertIn("bind_cli_owner(session_id, sid)", src)
        self.assertNotIn("@socketio.on('cli_command')", src)
        self.assertIn("audit_credential_access(add_log, 'RESOLVE'", src)
        emit_log = "emit OK [{event_name}] to {target} keys="
        self.assertIn(emit_log, src)
        self.assertNotIn("str(payload)[:80]", src)

    def test_plaintext_compat_symbols_not_reintroduced(self):
        from utils import vault_credentials as vc
        self.assertFalse(hasattr(vc, 'CLI_PLAINTEXT_COMPAT_POLICY'))
        self.assertFalse(hasattr(vc, 'CLI_PLAINTEXT_COMPAT_ENV'))
        self.assertFalse(hasattr(vc, 'cli_plaintext_compat_enabled'))
        blob = open(WEB, encoding='utf-8').read() + open(CLI_HTML, encoding='utf-8').read()
        self.assertNotIn('NST_CLI_PLAINTEXT_COMPAT', blob)
        self.assertNotIn('CLI_PLAINTEXT_COMPAT_POLICY', blob)

    def test_cli_route_does_not_put_password_in_url_template(self):
        src = open(WEB, encoding='utf-8').read()
        start = src.index('def cli_terminal():')
        end = src.index('# WebSocket event handlers for CLI')
        block = src[start:end]
        self.assertNotIn("request.args.get('password'", block)
        self.assertNotIn('password=', block)


class TestAuditAndLogsOmitSecrets(unittest.TestCase):
    def test_resolve_audit_line_has_id_not_secret(self):
        from vlan_checker_web import app
        from utils.api_security import audit_credential_access
        lines = []
        with app.test_request_context('/', environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            audit_credential_access(lines.append, 'RESOLVE', 'netops')
        blob = ' '.join(lines)
        self.assertIn('[Credential Audit] RESOLVE user=netops', blob)
        self.assertNotIn(SECRET, blob)


class TestVaultAdapterCliWithoutClientPassword(unittest.TestCase):
    """Paramiko mock SSH using vault-resolved secrets. Not a Socket.IO runtime test."""

    def test_credential_id_drives_cli_write(self):
        try:
            import paramiko  # noqa: F401
        except ImportError:
            self.skipTest('paramiko not installed')
        from tests.test_cli_smoke import MOCK_HOST, MOCK_PASS, MOCK_USER, MockSSHServer

        tmp = tempfile.mkdtemp()
        cm = CredentialManager(storage_dir=tmp)
        cm.add_credential(MOCK_USER, MOCK_PASS, label='mock')
        resolved, err = resolve_cli_connect_credentials(
            {'credential_id': MOCK_USER, 'username': MOCK_USER},
            cm,
        )
        self.assertIsNone(err)
        self.assertEqual(resolved['password'], MOCK_PASS)

        port = 2303
        server = MockSSHServer(port=port)
        server.start()
        if not server.server_ready.wait(timeout=5):
            server.stop()
            self.skipTest('mock SSH server did not start')
        try:
            with socket.create_connection((MOCK_HOST, port), timeout=3):
                pass
            device = {'host': MOCK_HOST, 'port': port, 'device_type': 'cisco_ios'}
            cli = CLIConnection(
                'vault_cli_001',
                device,
                resolved['username'],
                resolved['password'],
                resolved.get('enable_pwd') or '',
            )
            ok = cli.connect()
            self.assertTrue(ok, cli.error_message)
            cli.scrub_secrets()
            self.assertEqual(cli.pwd, '')
            cli.write('show version\n')
            self.assertTrue(cli.connected)
            cli.disconnect()
        finally:
            server.stop()


class TestSocketIoRuntimeLimitation(unittest.TestCase):
    def test_does_not_claim_live_socketio_handshake(self):
        try:
            import flask_socketio  # noqa: F401
            package_present = True
        except ImportError:
            package_present = False
        from vlan_checker_web import SOCKETIO_AVAILABLE
        self.assertIsInstance(SOCKETIO_AVAILABLE, bool)
        if not package_present:
            self.assertFalse(SOCKETIO_AVAILABLE)


if __name__ == '__main__':
    unittest.main()
