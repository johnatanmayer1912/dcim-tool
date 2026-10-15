"""Live Flask-SocketIO test_client suite for CLI credential_id (F-SOCK-02 / Stage 1B).

Requires flask-socketio (see requirements-dev.txt / requirements.txt).
Paramiko/SSH is mocked — no live vendor devices, no external network.
Socket.IO CLI auth is credential_id-only; plaintext passwords are not supported.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.test import EnvironBuilder

SECRET = 'live-vault-secret-never-echo'


def _require_socketio():
    try:
        import flask_socketio  # noqa: F401
    except ImportError as exc:
        raise unittest.SkipTest(
            'flask-socketio not installed; pip install -r requirements-dev.txt'
        ) from exc
    import vlan_checker_web as web
    if not web.SOCKETIO_AVAILABLE or web.socketio is None:
        raise unittest.SkipTest('SOCKETIO_AVAILABLE is False after import')
    return web


@contextmanager
def force_remote_addr(addr: str = '127.0.0.1'):
    """EnvironBuilder omits REMOTE_ADDR; empty addr is denied by Zero Trust."""
    orig = EnvironBuilder.get_environ

    def wrapped(self):
        env = orig(self)
        env['REMOTE_ADDR'] = addr
        return env

    with patch.object(EnvironBuilder, 'get_environ', wrapped):
        yield


class _FakeSock:
    def settimeout(self, _t):
        return None

    def connect_ex(self, _addr):
        return 0

    def close(self):
        return None


def _fake_create_cli_session(session_id, device, user, pwd, enb_pwd,
                             log_callback=None, data_callback=None):
    """Register a connected mock shell; assert vault secret when expected."""
    cli = MagicMock()
    cli.connected = True
    cli.hostname = 'MOCK-SW1'
    cli.session_id = session_id
    cli.credential_id = ''
    cli.write = MagicMock()
    cli.resize_pty = MagicMock()
    from modules import cli_manager as cmgr
    with cmgr._session_lock:
        cmgr._cli_sessions[session_id] = cli
    return cli


def _wait_for(client, *, event=None, status=None, code=None, timeout=4.0):
    deadline = time.time() + timeout
    collected = []
    while time.time() < deadline:
        for pkt in client.get_received():
            collected.append(pkt)
            if event and pkt.get('name') != event:
                continue
            args = pkt.get('args') or []
            payload = args[0] if args else {}
            if not isinstance(payload, dict):
                continue
            if status is not None and payload.get('status') != status:
                continue
            if code is not None and payload.get('code') != code:
                continue
            if event or status is not None or code is not None:
                return payload, collected
        time.sleep(0.02)
    return None, collected


def _payloads(collected, name):
    out = []
    for pkt in collected:
        if pkt.get('name') != name:
            continue
        args = pkt.get('args') or []
        if args and isinstance(args[0], dict):
            out.append(args[0])
    return out


def _assert_no_secrets(payload, secret=SECRET):
    from utils.vault_credentials import mapping_has_secret_fields
    blob = str(payload)
    assert secret not in blob
    assert 'enable_password' not in blob or payload.get('enable_password') in (None, '')
    if isinstance(payload, dict):
        assert not mapping_has_secret_fields(payload)
        for key in ('password', 'enable_password', 'enable_pwd', 'become_password',
                    'private_key', 'token', 'admin_password'):
            assert key not in payload


class TestSocketIoLiveHandshake(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.web = _require_socketio()
        cls.app = cls.web.app
        cls.socketio = cls.web.socketio
        cls.app.config['TESTING'] = True

    def setUp(self):
        from flask_socketio import SocketIOTestClient
        from modules.cli_manager import disconnect_all_sessions
        from modules.credential_manager import CredentialManager

        SocketIOTestClient.clients.clear()
        disconnect_all_sessions()
        self.tmp = tempfile.mkdtemp()
        self.cm = CredentialManager(storage_dir=self.tmp)
        self.cm.add_credential('netops', SECRET, admin_password='en1', label='Lab')
        self._orig_cm = self.web.credential_manager
        self.web.credential_manager = self.cm
        self._log_lines = []
        self._orig_add_log = self.web.add_log

        def _capture(msg):
            self._log_lines.append(str(msg))
            try:
                self._orig_add_log(msg)
            except Exception:
                pass

        self.web.add_log = _capture

    def tearDown(self):
        from flask_socketio import SocketIOTestClient
        from modules.cli_manager import disconnect_all_sessions

        self.web.add_log = self._orig_add_log
        self.web.credential_manager = self._orig_cm
        disconnect_all_sessions()
        SocketIOTestClient.clients.clear()

    def _client(self, *, remote_addr='127.0.0.1', origin='http://127.0.0.1:5051'):
        headers = {}
        if origin is not None:
            headers['Origin'] = origin
        with force_remote_addr(remote_addr):
            client = self.socketio.test_client(self.app, headers=headers or None)
        return client

    def _connect_vault(self, client, session_id='sess-live-1', extra=None):
        payload = {
            'session_id': session_id,
            'host': '10.0.0.1',
            'port': 22,
            'device_type': 'cisco_ios',
            'credential_id': 'netops',
            'username': 'netops',
        }
        if extra:
            payload.update(extra)
        with patch('socket.socket', return_value=_FakeSock()), \
             patch.object(self.web, 'create_cli_session', side_effect=_fake_create_cli_session):
            client.emit('cli_connect', payload)
            status, collected = _wait_for(client, event='cli_status', status='connected')
        return status, collected, payload

    def test_connect_with_credential_id_emits_cli_status_connected(self):
        client = self._client()
        self.assertTrue(client.is_connected())
        client.get_received()
        status, collected, payload = self._connect_vault(client)
        self.assertIsNotNone(status, collected)
        self.assertEqual(status['status'], 'connected')
        self.assertEqual(status['credential_id'], 'netops')
        self.assertEqual(status['hostname'], 'MOCK-SW1')
        self.assertNotIn('password', payload)
        for p in _payloads(collected, 'cli_status') + _payloads(collected, 'cli_error'):
            _assert_no_secrets(p)
        client.disconnect()

    def test_connect_without_credential_id_fails_closed(self):
        client = self._client()
        client.get_received()
        client.emit('cli_connect', {
            'session_id': 'sess-missing',
            'host': '10.0.0.1',
            'port': 22,
            'device_type': 'cisco_ios',
            'username': 'netops',
        })
        err, collected = _wait_for(client, event='cli_error', code='credential_id_required')
        self.assertIsNotNone(err, collected)
        self.assertEqual(err['code'], 'credential_id_required')
        _assert_no_secrets(err)
        from modules.cli_manager import get_cli_session
        self.assertIsNone(get_cli_session('sess-missing'))
        client.disconnect()

    def test_username_password_only_rejected(self):
        client = self._client()
        client.get_received()
        client.emit('cli_connect', {
            'session_id': 'sess-plain-off',
            'host': '10.0.0.1',
            'username': 'typed',
            'password': 'typed-secret-value',
        })
        err, collected = _wait_for(client, event='cli_error', code='credential_id_required')
        self.assertIsNotNone(err, collected)
        self.assertEqual(err['code'], 'credential_id_required')
        self.assertNotIn('typed-secret-value', str(err))
        _assert_no_secrets(err, secret='typed-secret-value')
        blob = '\n'.join(self._log_lines)
        self.assertNotIn('typed-secret-value', blob)
        client.disconnect()

    def test_env_and_payload_cannot_enable_plaintext(self):
        client = self._client()
        client.get_received()
        with patch.dict(os.environ, {'NST_CLI_PLAINTEXT_COMPAT': '1'}, clear=False):
            client.emit('cli_connect', {
                'session_id': 'sess-payload-enable',
                'host': '10.0.0.1',
                'username': 'typed',
                'password': 'typed-secret-value',
                'allow_plaintext': True,
                'plaintext_compat': '1',
                'NST_CLI_PLAINTEXT_COMPAT': '1',
            })
            err, collected = _wait_for(client, event='cli_error', code='credential_id_required')
        self.assertIsNotNone(err, collected)
        self.assertEqual(err['code'], 'credential_id_required')
        self.assertNotIn('typed-secret-value', str(collected))
        client.disconnect()

    def test_invalid_credential_id_does_not_fallback_to_plaintext(self):
        client = self._client()
        client.get_received()
        client.emit('cli_connect', {
            'session_id': 'sess-no-fallback',
            'host': '10.0.0.1',
            'credential_id': 'ghost',
            'username': 'ghost',
            'password': SECRET,
        })
        err, collected = _wait_for(client, event='cli_error', code='unknown_credential_id')
        self.assertIsNotNone(err, collected)
        self.assertEqual(err['code'], 'unknown_credential_id')
        self.assertNotIn(SECRET, str(collected))
        client.disconnect()

    def test_connect_with_invalid_credential_id_fails_closed(self):
        client = self._client()
        client.get_received()
        client.emit('cli_connect', {
            'session_id': 'sess-bad',
            'host': '10.0.0.1',
            'credential_id': '../admin',
            'username': 'netops',
        })
        err, collected = _wait_for(client, event='cli_error', code='invalid_credential_id')
        self.assertIsNotNone(err, collected)
        self.assertEqual(err['code'], 'invalid_credential_id')
        _assert_no_secrets(err)
        client.disconnect()

    def test_connect_with_unknown_credential_id_fails_closed(self):
        client = self._client()
        client.get_received()
        client.emit('cli_connect', {
            'session_id': 'sess-ghost',
            'host': '10.0.0.1',
            'credential_id': 'ghost',
            'username': 'ghost',
        })
        err, collected = _wait_for(client, event='cli_error', code='unknown_credential_id')
        self.assertIsNotNone(err, collected)
        self.assertEqual(err['code'], 'unknown_credential_id')
        client.disconnect()

    def test_credential_id_ignores_client_supplied_password(self):
        seen = {}

        def capture_create(session_id, device, user, pwd, enb_pwd,
                           log_callback=None, data_callback=None):
            seen['pwd'] = pwd
            seen['enb'] = enb_pwd
            return _fake_create_cli_session(
                session_id, device, user, pwd, enb_pwd, log_callback, data_callback,
            )

        client = self._client()
        client.get_received()
        with patch('socket.socket', return_value=_FakeSock()), \
             patch.object(self.web, 'create_cli_session', side_effect=capture_create):
            client.emit('cli_connect', {
                'session_id': 'sess-override',
                'host': '10.0.0.1',
                'credential_id': 'netops',
                'username': 'netops',
                'password': 'client-typed-wrong',
                'enable_password': 'client-en',
            })
            status, collected = _wait_for(client, event='cli_status', status='connected')
        self.assertIsNotNone(status, collected)
        self.assertEqual(seen.get('pwd'), SECRET)
        self.assertEqual(seen.get('enb'), 'en1')
        self.assertNotEqual(seen.get('pwd'), 'client-typed-wrong')
        for p in _payloads(collected, 'cli_status'):
            _assert_no_secrets(p)
        client.disconnect()

    def test_two_concurrent_clients_cannot_hijack_sessions(self):
        a = self._client()
        b = self._client()
        a.get_received()
        b.get_received()
        status, _collected, _ = self._connect_vault(a, session_id='sess-owned')
        self.assertIsNotNone(status)
        b.emit('cli_connect', {
            'session_id': 'sess-owned',
            'host': '10.0.0.1',
            'credential_id': 'netops',
            'username': 'netops',
        })
        err, collected = _wait_for(b, event='cli_error', code='session_isolated')
        self.assertIsNotNone(err, collected)
        self.assertEqual(err['code'], 'session_isolated')
        from modules.cli_manager import get_cli_session
        cli = get_cli_session('sess-owned')
        self.assertIsNotNone(cli)
        self.assertTrue(cli.connected)
        a.disconnect()
        b.disconnect()

    def test_cli_data_requires_owner_match(self):
        a = self._client()
        b = self._client()
        a.get_received()
        b.get_received()
        status, _, _ = self._connect_vault(a, session_id='sess-write')
        self.assertIsNotNone(status)
        from modules.cli_manager import get_cli_session
        cli = get_cli_session('sess-write')
        self.assertIsNotNone(cli)
        b.emit('cli_data', {'session_id': 'sess-write', 'data': 'show run\n'})
        time.sleep(0.1)
        cli.write.assert_not_called()
        a.emit('cli_data', {'session_id': 'sess-write', 'data': 'show ver\n'})
        time.sleep(0.1)
        cli.write.assert_called()
        a.disconnect()
        b.disconnect()

    def test_disconnect_releases_owner_sid(self):
        client = self._client()
        client.get_received()
        status, _, _ = self._connect_vault(client, session_id='sess-disc')
        self.assertIsNotNone(status)
        from modules.cli_manager import (
            cli_owner_matches,
            get_cli_session,
            session_ids_owned_by_sid,
        )
        # Owner map non-empty before disconnect
        self.assertIsNotNone(get_cli_session('sess-disc'))
        client.disconnect()
        time.sleep(0.1)
        self.assertIsNone(get_cli_session('sess-disc'))
        self.assertFalse(cli_owner_matches('sess-disc', 'any'))
        # No owners left for abandoned session
        self.assertEqual(session_ids_owned_by_sid('any'), [])

    def test_cli_disconnect_event_clears_session(self):
        client = self._client()
        client.get_received()
        status, _, _ = self._connect_vault(client, session_id='sess-explicit')
        self.assertIsNotNone(status)
        client.emit('cli_disconnect', {'session_id': 'sess-explicit'})
        disc, collected = _wait_for(client, event='cli_status', status='disconnected')
        self.assertIsNotNone(disc, collected)
        from modules.cli_manager import get_cli_session
        self.assertIsNone(get_cli_session('sess-explicit'))
        client.disconnect()

    def test_public_cli_status_payload_drops_secret_keys(self):
        from utils.vault_credentials import public_cli_status_payload
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
        _assert_no_secrets(leaked)
        self.assertEqual(leaked['credential_id'], 'netops')

    def test_audit_log_does_not_leak_credential_values(self):
        client = self._client()
        client.get_received()
        status, collected, _ = self._connect_vault(client, session_id='sess-audit')
        self.assertIsNotNone(status)
        blob = '\n'.join(self._log_lines)
        self.assertIn('RESOLVE', blob)
        self.assertIn('netops', blob)
        self.assertNotIn(SECRET, blob)
        for p in _payloads(collected, 'cli_status') + _payloads(collected, 'cli_error'):
            _assert_no_secrets(p)
            self.assertNotIn(SECRET, str(p))
        client.disconnect()

    def test_foreign_origin_denied_on_connect(self):
        client = self._client(origin='http://evil.example')
        # connect handler should reject
        self.assertFalse(client.is_connected())

    def test_nonlocal_remote_addr_denied_on_connect(self):
        client = self._client(remote_addr='203.0.113.10')
        self.assertFalse(client.is_connected())

    def test_locked_vault_fails_closed(self):
        self.cm.set_master_password('master-pass')
        from modules.credential_manager import CredentialManager
        locked = CredentialManager(storage_dir=self.tmp)
        self.web.credential_manager = locked
        client = self._client()
        client.get_received()
        client.emit('cli_connect', {
            'session_id': 'sess-locked',
            'host': '10.0.0.1',
            'credential_id': 'netops',
            'username': 'netops',
        })
        err, collected = _wait_for(client, event='cli_error', code='vault_locked')
        self.assertIsNotNone(err, collected)
        self.assertEqual(err['code'], 'vault_locked')
        _assert_no_secrets(err)
        client.disconnect()

    def test_malformed_payload_fails_closed(self):
        client = self._client()
        client.get_received()
        client.emit('cli_connect', 'not-a-dict')
        err, collected = _wait_for(client, event='cli_error', code='malformed_payload')
        self.assertIsNotNone(err, collected)
        self.assertEqual(err['code'], 'malformed_payload')
        client.disconnect()

    def test_compat_symbols_removed_from_product_code(self):
        from utils import vault_credentials as vc
        self.assertFalse(hasattr(vc, 'CLI_PLAINTEXT_COMPAT_POLICY'))
        self.assertFalse(hasattr(vc, 'cli_plaintext_compat_enabled'))
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for rel in (
            'utils/vault_credentials.py',
            'vlan_checker_web.py',
            'modules/web/templates/cli_terminal.html',
        ):
            blob = open(os.path.join(root, rel), encoding='utf-8').read()
            self.assertNotIn('NST_CLI_PLAINTEXT_COMPAT', blob, rel)
            self.assertNotIn('CLI_PLAINTEXT_COMPAT_POLICY', blob, rel)
            self.assertNotIn('plaintext_compat', blob, rel)
            self.assertNotIn('compat_warning', blob, rel)

    def test_cli_terminal_template_credential_id_only(self):
        r = self.app.test_client().get(
            '/cli_terminal',
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
            headers={'Origin': 'http://127.0.0.1:5051'},
        )
        self.assertEqual(r.status_code, 200)
        html = r.get_data(as_text=True)
        self.assertIn('connCredentialSelect', html)
        self.assertIn('credential_id required', html.lower())
        self.assertNotIn('connPassword', html)
        self.assertNotIn('connEnablePassword', html)
        self.assertNotIn('CLI_PLAINTEXT_COMPAT', html)
        self.assertNotIn('NST_CLI_PLAINTEXT_COMPAT', html)
        self.assertNotIn('d.credential.password', html)
        self.assertNotIn('localStorage.setItem', html)



if __name__ == '__main__':
    unittest.main()
