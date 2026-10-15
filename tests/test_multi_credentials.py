"""
Comprehensive Test Suite for Multi-Credential Connection Fallback & Vault Resolution
(Primary, Secondary, Third Credentials)
"""

import pytest
from unittest.mock import MagicMock, patch
from modules.network_base import safe_connection
from utils.session_cred_cache import (
    set_session_credentials,
    get_session_credentials,
    public_session_view,
    update_from_execute_payload,
    clear_session_credentials,
)
from utils.vault_credentials import resolve_execute_credentials


class MockCredentialManager:
    def __init__(self, creds=None):
        self.creds = creds or {}

    def is_master_password_required(self):
        return False

    def get_credential(self, cid):
        return self.creds.get(cid)

    def record_use(self, cid):
        pass


def test_safe_connection_primary_success():
    device = {'host': '10.0.0.1', 'device_type': 'cisco_ios'}
    log_messages = []
    def log_func(msg):
        log_messages.append(msg)

    mock_conn = MagicMock()
    with patch('modules.network_base.connect_permissive', return_value=mock_conn) as mock_cp:
        with safe_connection(device, 'admin', 'pass1', '', log_func=log_func) as conn:
            assert conn == mock_conn
        
        # Primary attempted once
        assert mock_cp.call_count == 1
        assert mock_cp.call_args[0][1] == 'admin'
        assert mock_cp.call_args[0][2] == 'pass1'


def test_safe_connection_fallback_to_secondary_success():
    device = {'host': '10.0.0.2', 'device_type': 'cisco_ios'}
    fallback_creds = [
        {'username': 'sec_user', 'password': 'sec_pass', 'enable_pwd': 'sec_enable', 'label': 'Secondary Profile'},
        {'username': 'third_user', 'password': 'third_pass', 'enable_pwd': '', 'label': 'Third Profile'},
    ]
    log_messages = []
    def log_func(msg):
        log_messages.append(msg)

    mock_conn = MagicMock()

    # Fail first call (primary), succeed on second call (secondary)
    def side_effect(dev, u, p, e, log_func=None):
        if u == 'admin':
            raise Exception("Authentication failed for primary admin")
        return mock_conn

    with patch('modules.network_base.connect_permissive', side_effect=side_effect) as mock_cp:
        with safe_connection(device, 'admin', 'pass1', '', log_func=log_func, fallback_credentials=fallback_creds) as conn:
            assert conn == mock_conn

        assert mock_cp.call_count == 2
        # First call was primary
        assert mock_cp.call_args_list[0][0][1] == 'admin'
        # Second call was secondary
        assert mock_cp.call_args_list[1][0][1] == 'sec_user'
        assert mock_cp.call_args_list[1][0][2] == 'sec_pass'
        assert any("Secondary (Secondary Profile) [sec_user]" in m for m in log_messages)


def test_safe_connection_fallback_to_third_success():
    device = {'host': '10.0.0.3', 'device_type': 'cisco_ios'}
    fallback_creds = [
        {'username': 'sec_user', 'password': 'sec_pass', 'enable_pwd': '', 'label': 'Secondary Profile'},
        {'username': 'third_user', 'password': 'third_pass', 'enable_pwd': 'third_enb', 'label': 'Third Profile'},
    ]
    log_messages = []
    def log_func(msg):
        log_messages.append(msg)

    mock_conn = MagicMock()

    def side_effect(dev, u, p, e, log_func=None):
        if u in ('admin', 'sec_user'):
            raise Exception(f"Auth failed for {u}")
        return mock_conn

    with patch('modules.network_base.connect_permissive', side_effect=side_effect) as mock_cp:
        with safe_connection(device, 'admin', 'pass1', '', log_func=log_func, fallback_credentials=fallback_creds) as conn:
            assert conn == mock_conn

        assert mock_cp.call_count == 3
        assert mock_cp.call_args_list[0][0][1] == 'admin'
        assert mock_cp.call_args_list[1][0][1] == 'sec_user'
        assert mock_cp.call_args_list[2][0][1] == 'third_user'
        assert mock_cp.call_args_list[2][0][2] == 'third_pass'
        assert any("Third (Third Profile) [third_user]" in m for m in log_messages)


def test_safe_connection_all_credentials_fail():
    device = {'host': '10.0.0.4', 'device_type': 'cisco_ios'}
    fallback_creds = [
        {'username': 'sec_user', 'password': 'sec_pass', 'label': 'Secondary Profile'},
        {'username': 'third_user', 'password': 'third_pass', 'label': 'Third Profile'},
    ]
    log_messages = []
    def log_func(msg):
        log_messages.append(msg)

    with patch('modules.network_base.connect_permissive', side_effect=Exception("Connection refused")) as mock_cp:
        with pytest.raises(Exception) as exc_info:
            with safe_connection(device, 'admin', 'pass1', '', log_func=log_func, fallback_credentials=fallback_creds):
                pass

        assert "Connection refused" in str(exc_info.value)
        assert mock_cp.call_count == 3


def test_resolve_execute_credentials_multi_credentials():
    mock_vault = MockCredentialManager({
        'primary_cred': {
            'username': 'netadmin',
            'password': 'p1',
            'admin_password': 'e1',
            'label': 'Primary Profile',
            'profile_type': 'ssh_and_snmp'
        },
        'secondary_cred': {
            'username': 'backupadmin',
            'password': 'p2',
            'admin_password': 'e2',
            'label': 'Secondary Profile',
            'profile_type': 'ssh_and_snmp'
        },
        'third_cred': {
            'username': 'fallbackadmin',
            'password': 'p3',
            'admin_password': 'e3',
            'label': 'Third Profile',
            'profile_type': 'ssh_and_snmp'
        }
    })

    payload = {
        'credential_id': 'primary_cred',
        'secondary_credential_id': 'secondary_cred',
        'third_credential_id': 'third_cred'
    }

    resolved = resolve_execute_credentials(payload, mock_vault)
    assert resolved['username'] == 'netadmin'
    assert resolved['credential_id'] == 'primary_cred'
    assert resolved['secondary_credential_id'] == 'secondary_cred'
    assert resolved['third_credential_id'] == 'third_cred'
    assert resolved['secondary_credential']['username'] == 'backupadmin'
    assert resolved['third_credential']['username'] == 'fallbackadmin'
    assert len(resolved['fallback_credentials']) == 2
    assert resolved['fallback_credentials'][0]['username'] == 'backupadmin'
    assert resolved['fallback_credentials'][1]['username'] == 'fallbackadmin'


def test_session_cred_cache_multi_credentials():
    clear_session_credentials()
    set_session_credentials(
        username='admin',
        credential_id='cred_p',
        secondary_credential_id='cred_s',
        secondary_label='Backup Cred',
        third_credential_id='cred_t',
        third_label='Emergency Cred'
    )

    creds = get_session_credentials()
    assert creds['credential_id'] == 'cred_p'
    assert creds['secondary_credential_id'] == 'cred_s'
    assert creds['third_credential_id'] == 'cred_t'

    view = public_session_view()
    assert view['credential_id'] == 'cred_p'
    assert view['secondary_credential_id'] == 'cred_s'
    assert view['third_credential_id'] == 'cred_t'
    assert view['secondary_label'] == 'Backup Cred'
    assert view['third_label'] == 'Emergency Cred'

    clear_session_credentials()
