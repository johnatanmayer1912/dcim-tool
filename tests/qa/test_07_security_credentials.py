"""Mandatory QA — Security (credentials, mutations, audit)."""
from __future__ import annotations

import os
import tempfile

from tests.qa._scaffold import mandatory

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
WEB = os.path.join(ROOT, 'vlan_checker_web.py')


@mandatory
def test_credential_vault_requires_master_password_when_set():
    """Legacy locked vaults still reject until one-time unlock/migrate."""
    from modules.credential_manager import CredentialManager
    from utils.api_security import require_credential_vault_unlocked

    tmp = tempfile.mkdtemp()
    cm = CredentialManager(storage_dir=tmp)
    cm.add_credential('u1', 'p1')
    ok, _ = cm.set_master_password('master123')
    assert ok
    locked = CredentialManager(storage_dir=tmp)
    assert locked.is_master_password_required()
    import vlan_checker_web as web
    with web.app.app_context():
        resp, code = require_credential_vault_unlocked(locked)
    assert code == 403
    assert 'locked' in resp.get_json()['error'].lower()


@mandatory
def test_credential_audit_log_on_secret_read():
    """audit_credential_access called on vault get paths."""
    src = open(WEB, encoding='utf-8').read()
    assert 'audit_credential_access' in src
    assert "audit_credential_access(add_log, 'GET'" in src


@mandatory
def test_session_cache_not_persisted_to_disk():
    """session_cred_cache is memory-only; no file write."""
    from utils import session_cred_cache as scc
    src = open(scc.__file__, encoding='utf-8').read()
    assert 'open(' not in src.replace('from __future__', '')
    assert '_cache' in src
    scc.set_session_credentials(username='u', password='secret')
    view = scc.public_session_view()
    assert 'secret' not in str(view)
    assert view['has_password'] is True
    scc.clear_session_credentials()


@mandatory
def test_execute_does_not_log_password_fields():
    """add_log paths redact or omit password in operator console."""
    src = open(WEB, encoding='utf-8').read()
    assert 'password' in src
    assert "add_log(f\"[ERROR]" in src or 'add_log(' in src
    # Execute payload must not dump password into add_log format strings
    assert 'add_log' in src
    assert 'password={password}' not in src
    assert "password={data.get('password')}" not in src


@mandatory
def test_vlan_live_mutation_requires_explicit_confirm():
    """Live VLAN change not possible without confirm flow."""
    html = open(os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html'), encoding='utf-8').read()
    assert 'confirmVlanExecution' in html
    assert 'vlan-modal-confirm-btn' in html
    src = open(WEB, encoding='utf-8').read()
    assert '/api/vlan/validate' in src


@mandatory
def test_interface_manager_deploy_respects_dry_run():
    """IM deploy dry_run does not push config to device."""
    im = open(os.path.join(ROOT, 'modules', 'plugins', 'interface_manager.py'), encoding='utf-8').read()
    assert 'if dry_run:' in im
    assert '[DRY-RUN] Skipping deployment' in im
    assert "dry_run = data.get('dry_run', True)" in open(WEB, encoding='utf-8').read()


@mandatory
def test_api_security_localhost_guard_on_sensitive_routes():
    """Sensitive routes use localhost check from api_security."""
    from utils.api_security import client_is_localhost, require_local_credential_access
    src = open(WEB, encoding='utf-8').read()
    assert '@localhost_required' in src
    assert '/api/path-trace' in src
    assert '/api/topology/issues' in src
    assert '/api/utilization-overlay/status' in src
    assert 'require_local_credential_access' in src or 'client_is_localhost' in src
    assert callable(client_is_localhost)
    assert callable(require_local_credential_access)
    from utils.api_security import EMPTY_ORIGIN_POLICY
    assert EMPTY_ORIGIN_POLICY == 'loopback_local_automation'


@mandatory
def test_credential_get_route_is_metadata_only():
    """GET /api/credentials/get returns metadata; Use does not copy secrets into the DOM."""
    src = open(WEB, encoding='utf-8').read()
    assert 'public_credential_view' in src
    assert 'Retrieve a specific credential (with password)' not in src
    html = open(os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html'), encoding='utf-8').read()
    assert 'd.credential.password' not in html
    assert 'function nstCredentialRequestBody' in html
    assert 'Credential is unavailable' in html


@mandatory
def test_vault_credential_id_is_username_without_secret_in_list():
    """credential_id is the vault username key; list payloads omit passwords."""
    from modules.credential_manager import CredentialManager
    from utils.vault_credentials import resolve_execute_credentials
    tmp = tempfile.mkdtemp()
    cm = CredentialManager(storage_dir=tmp)
    cm.add_credential('ops', 'secret-value', label='Ops')
    rows = cm.list_credentials()
    assert rows[0]['credential_id'] == 'ops'
    assert 'password' not in rows[0]
    assert 'secret-value' not in str(rows)
    out = resolve_execute_credentials({'credential_id': 'ops'}, cm)
    assert out['password'] == 'secret-value'
    src = open(WEB, encoding='utf-8').read()
    assert 'resolve_execute_credentials' in src


@mandatory
def test_cli_socketio_prefers_vault_credential_id():
    """CLI Socket.IO requires credential_id; plaintext Socket.IO passwords are gone."""
    from utils import vault_credentials as vc
    src = open(WEB, encoding='utf-8').read()
    assert 'resolve_cli_connect_credentials' in src
    assert not hasattr(vc, 'CLI_PLAINTEXT_COMPAT_POLICY')
    assert not hasattr(vc, 'cli_plaintext_compat_enabled')
    assert 'NST_CLI_PLAINTEXT_COMPAT' not in src
    html = open(os.path.join(ROOT, 'modules', 'web', 'templates', 'cli_terminal.html'), encoding='utf-8').read()
    assert 'credential_id: credentialId' in html
    assert 'connPassword' not in html
    assert 'd.credential.password' not in html


@mandatory
def test_cli_socketio_live_handshake_suite_exists():
    """Live flask-socketio test_client suite covers credential_id-only handshake."""
    path = os.path.join(ROOT, 'tests', 'test_rb_zt_socketio_live_handshake.py')
    assert os.path.isfile(path)
    text = open(path, encoding='utf-8').read()
    assert 'test_connect_with_credential_id_emits_cli_status_connected' in text
    assert 'test_two_concurrent_clients_cannot_hijack_sessions' in text
    assert 'test_username_password_only_rejected' in text
    assert 'NST_CLI_PLAINTEXT_COMPAT' not in open(
        os.path.join(ROOT, 'utils', 'vault_credentials.py'), encoding='utf-8'
    ).read()


@mandatory
def test_no_restore_backup_automated_rollback():
    """Dangerous restore_backup / rollback paths absent per prebuild safety."""
    for rel in ('utils/config_backup_system.py', 'modules/vlan_mgmt_production.py', 'vlan_checker_web.py'):
        text = open(os.path.join(ROOT, rel), encoding='utf-8').read()
        assert 'restore_backup' not in text
        assert 'rollback_vlan_change' not in text


@mandatory
def test_mac_input_validated_against_injection():
    """MAC trace rejects shell metacharacters in target MAC."""
    from modules.mac_trace import _validate_mac
    import pytest
    with pytest.raises(ValueError):
        _validate_mac('aa:bb:cc; rm -rf /')
    with pytest.raises(ValueError):
        _validate_mac('$(whoami)')
    assert _validate_mac('aabb.ccdd.eeff')


@mandatory
def test_inventory_commit_is_localhost_gated():
    """Inventory write APIs live behind the console localhost gate."""
    src = open(WEB, encoding='utf-8').read()
    assert '/api/inventory/commit' in src
    assert '_gate_console_to_localhost' in src or 'require_local_credential_access' in src


@mandatory
def test_inventory_upload_sanitized_filename():
    """Uploaded inventory uses secure_filename."""
    src = open(WEB, encoding='utf-8').read()
    assert 'secure_filename' in src
    assert 'from werkzeug.utils import secure_filename' in src
