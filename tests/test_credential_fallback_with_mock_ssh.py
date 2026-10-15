"""
Credential Fallback Testing with Mock SSH Server

This test validates the credential fallback mechanism using a mock SSH server
to simulate real connection scenarios without requiring actual network devices.

Test Scenarios:
1. All 3 credentials fail - verify error handling
2. Primary credential succeeds - verify no fallback needed
3. Primary fails, secondary succeeds - verify fallback works
4. Primary and secondary fail, tertiary succeeds - verify full fallback chain
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from unittest import mock
import subprocess
import signal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCredentialFallbackWithMockSSH(unittest.TestCase):
    """Test credential fallback with mock SSH server."""

    def setUp(self):
        """Set up test environment."""
        from modules.credential_manager import CredentialManager
        self.tmp = tempfile.mkdtemp()
        self.cm = CredentialManager(storage_dir=self.tmp)
        self.master_password = "test_master_password_123"
        
        import vlan_checker_web as web
        web.app.config['TESTING'] = True
        web.credential_manager = self.cm
        self.client = web.app.test_client()
        self.web = web
        try:
            web.console_log_buffer.clear_for_tests()
        except Exception:
            pass
        
        # Mock SSH server config
        self.mock_ssh_host = '127.0.0.1'
        self.mock_ssh_port = 2222
        
    def tearDown(self):
        """Clean up test environment."""
        pass
        
    def _setup_vault_and_credentials(self):
        """Set up vault with 3 credentials (no master password required)."""
        # Create primary credential
        r = self.client.post('/api/credentials/add', json={
            'username': 'primary_user',
            'password': 'primary_pass',
            'admin_password': 'primary_enable',
            'label': 'Primary Credential',
            'force': True
        })
        self.assertEqual(r.status_code, 200, r.get_json())
        
        # Create secondary credential
        r = self.client.post('/api/credentials/add', json={
            'username': 'secondary_user',
            'password': 'secondary_pass',
            'admin_password': 'secondary_enable',
            'label': 'Secondary Credential',
            'force': True
        })
        self.assertEqual(r.status_code, 200, r.get_json())
        
        # Create tertiary credential
        r = self.client.post('/api/credentials/add', json={
            'username': 'tertiary_user',
            'password': 'tertiary_pass',
            'admin_password': 'tertiary_enable',
            'label': 'Tertiary Credential',
            'force': True
        })
        self.assertEqual(r.status_code, 200, r.get_json())
        
    def _execute_plugin_with_fallback(self, inventory='10.77.77.1,cisco_ios'):
        """Execute cisco_asset_warranty plugin with fallback credentials."""
        r = self.client.post('/api/execute', json={
            'action': 'cisco_asset_warranty',
            'credential_id': 'primary_user',
            'secondary_credential_id': 'secondary_user',
            'third_credential_id': 'tertiary_user',
            'inventory': inventory,
            'inventory_source': 'unsaved',
            'acknowledge_unsaved': True,
            'target_mode': 'all',
            'params': {
                'include_modules': True,
                'collection_policy': 'ssh_only',
                'snmp_fallback': False,
            }
        })
        return r

    def _get_logs(self):
        """Get logs from the application."""
        r = self.client.get('/api/logs?limit=200')
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        return data.get('logs', [])

    def _wait_logs(self, *needles, timeout=20.0):
        """Poll /api/logs until all needles appear (background execute threads)."""
        deadline = time.time() + timeout
        blob = ''
        while time.time() < deadline:
            blob = '\n'.join(self._get_logs())
            if all(n in blob for n in needles):
                return blob
            time.sleep(0.1)
        return blob

    def _fake_connect(self, success_users):
        """Return connect_permissive side_effect that succeeds only for listed usernames."""
        from unittest.mock import MagicMock
        attempts = []

        def fake_connect(target, user, pwd, enb, log_func=None):
            attempts.append(user)
            if user not in success_users:
                raise Exception(f'Authentication failed for {user}')
            m = MagicMock()
            m.disconnect = MagicMock()
            m.find_prompt.return_value = 'sw#'
            m.send_command.return_value = (
                'Cisco IOS Software, C9300 Software\n'
                'Processor board ID FDOMOCK001\n'
                'Serial Number: FDOMOCK001\n'
            )
            return m

        return fake_connect, attempts

    def test_01_all_three_credentials_fail(self):
        """Test scenario: All 3 credentials fail - verify error handling."""
        self._setup_vault_and_credentials()
        fake_connect, attempts = self._fake_connect(success_users=())
        host = '10.77.77.11'

        with mock.patch('modules.network_base.connect_permissive', side_effect=fake_connect):
            r = self._execute_plugin_with_fallback(inventory=f'{host},cisco_ios')
            self.assertEqual(r.status_code, 200, r.get_json())
            self.assertEqual(r.get_json().get('status'), 'started')
            log_text = self._wait_logs(
                f'[{host}] Has fallback_credentials: True',
                f'[{host}] Fallback credentials count: 2',
                f'[{host}] Connecting to device using Primary',
                'attempt 1/3',
                'attempt 3/3',
                f'[{host}] All credential attempts exhausted',
            )

        self.assertIn('secondary_user', log_text)
        self.assertIn('tertiary_user', log_text)
        self.assertEqual(
            attempts[:3],
            ['primary_user', 'secondary_user', 'tertiary_user'],
            attempts,
        )

    def test_02_primary_credential_succeeds(self):
        """Test scenario: Primary credential succeeds - no fallback needed."""
        self._setup_vault_and_credentials()
        fake_connect, attempts = self._fake_connect(success_users={'primary_user'})
        host = '10.77.77.12'

        with mock.patch('modules.network_base.connect_permissive', side_effect=fake_connect):
            r = self._execute_plugin_with_fallback(inventory=f'{host},cisco_ios')
            self.assertEqual(r.status_code, 200, r.get_json())
            log_text = self._wait_logs(
                f'[{host}] Has fallback_credentials: True',
                f'[{host}] Successfully connected using Primary',
                f'[{host}] Collection complete',
            )

        self.assertIn('Fallback credentials count: 2', log_text)
        self.assertEqual(attempts, ['primary_user'], attempts)

    def test_03_primary_fails_secondary_succeeds(self):
        """Test scenario: Primary fails, secondary succeeds - fallback works."""
        self._setup_vault_and_credentials()
        fake_connect, attempts = self._fake_connect(success_users={'secondary_user'})
        host = '10.77.77.13'

        with mock.patch('modules.network_base.connect_permissive', side_effect=fake_connect):
            r = self._execute_plugin_with_fallback(inventory=f'{host},cisco_ios')
            self.assertEqual(r.status_code, 200, r.get_json())
            log_text = self._wait_logs(
                f'[{host}] Has fallback_credentials: True',
                f'[{host}] Connecting to device using Secondary',
                'attempt 2/3',
                f'[{host}] Collection complete',
            )

        self.assertIn('Connecting to device using Secondary', log_text)
        self.assertEqual(attempts[:2], ['primary_user', 'secondary_user'], attempts)

    def test_04_primary_secondary_fail_tertiary_succeeds(self):
        """Test scenario: Primary and secondary fail, tertiary succeeds - full fallback chain."""
        self._setup_vault_and_credentials()
        fake_connect, attempts = self._fake_connect(success_users={'tertiary_user'})
        host = '10.77.77.14'

        with mock.patch('modules.network_base.connect_permissive', side_effect=fake_connect):
            r = self._execute_plugin_with_fallback(inventory=f'{host},cisco_ios')
            self.assertEqual(r.status_code, 200, r.get_json())
            log_text = self._wait_logs(
                f'[{host}] Has fallback_credentials: True',
                'attempt 1/3',
                'attempt 2/3',
                'attempt 3/3',
                f'[{host}] Connecting to device using Third',
                f'[{host}] Collection complete',
            )

        self.assertIn('Connecting to device using Third', log_text)
        self.assertEqual(
            attempts[:3],
            ['primary_user', 'secondary_user', 'tertiary_user'],
            attempts,
        )

    def test_05_ui_sends_fallback_credentials(self):
        """Test that UI sends secondary and tertiary credential IDs to API."""
        self._setup_vault_and_credentials()
        fake_connect, _ = self._fake_connect(success_users={'primary_user'})
        with mock.patch('modules.network_base.connect_permissive', side_effect=fake_connect):
            r = self.client.post('/api/execute', json={
                'action': 'cisco_asset_warranty',
                'credential_id': 'primary_user',
                'secondary_credential_id': 'secondary_user',
                'third_credential_id': 'tertiary_user',
                'inventory': '10.77.77.15,cisco_ios',
                'inventory_source': 'unsaved',
                'acknowledge_unsaved': True,
                'target_mode': 'all',
                'params': {'collection_policy': 'ssh_only', 'snmp_fallback': False},
            })
            self.assertEqual(r.status_code, 200, r.get_json())
            self.assertEqual(r.get_json().get('status'), 'started')
            self._wait_logs('[10.77.77.15] Collection complete')

    def test_06_logs_show_correct_fallback_info(self):
        """Test that logs show correct fallback credential information."""
        self._setup_vault_and_credentials()
        fake_connect, _ = self._fake_connect(success_users={'primary_user'})
        host = '10.77.77.16'
        with mock.patch('modules.network_base.connect_permissive', side_effect=fake_connect):
            r = self._execute_plugin_with_fallback(inventory=f'{host},cisco_ios')
            self.assertEqual(r.status_code, 200, r.get_json())
            log_text = self._wait_logs(
                f'[{host}] Credential bundle keys:',
                f'[{host}] Has fallback_credentials: True',
                f'[{host}] Fallback credentials count: 2',
                f'[{host}] Fallback 1:',
                f'[{host}] Fallback 2:',
                f'[{host}] Collection complete',
            )
        self.assertIn('Credential bundle keys:', log_text)
        self.assertIn('Has fallback_credentials: True', log_text)
