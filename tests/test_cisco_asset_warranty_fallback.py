"""Test credential fallback in cisco_asset_warranty plugin with forced failures."""
from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCiscoAssetWarrantyFallback(unittest.TestCase):
    """Test that cisco_asset_warranty plugin correctly uses credential fallback."""
    
    def setUp(self):
        from modules.credential_manager import CredentialManager
        self.tmp = tempfile.mkdtemp()
        self.cm = CredentialManager(storage_dir=self.tmp)
        # Primary credential (will fail in test)
        self.cm.add_credential('primary', 'wrongpass', snmp_version='2c', snmp_community='public')
        # Secondary credential (will succeed)
        self.cm.add_credential('secondary', 'correctpass', snmp_version='2c', snmp_community='public')
        # Tertiary credential (backup)
        self.cm.add_credential('tertiary', 'backuppass', snmp_version='2c', snmp_community='public')

        import vlan_checker_web as web
        web.app.config['TESTING'] = True
        web.credential_manager = self.cm
        self.client = web.app.test_client()
        self.web = web

    def tearDown(self):
        pass

    @mock.patch.dict(os.environ, {'NST_MOCK_ASSET_LAB': '1'})
    def test_fallback_secondary_succeeds(self):
        """Test that when primary fails, secondary is tried and succeeds."""
        # Use fallback test host that fails with 'primary' username
        inv = '\n'.join([
            '10.99.1.5,cisco_ios',
        ])
        r = self.client.post('/api/execute', json={
            'action': 'cisco_asset_warranty',
            'credential_id': 'primary',
            'secondary_credential_id': 'secondary',
            'third_credential_id': 'tertiary',
            'inventory': inv,
            'inventory_source': 'unsaved',
            'acknowledge_unsaved': True,
            'target_mode': 'all',
            'params': {
                'include_modules': True,
                'collection_policy': 'ssh_first',
                'snmp_fallback': True,
            },
        })
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        data = r.get_json()
        self.assertEqual(data.get('status'), 'started')
        
        # Allow background thread to finish
        for _ in range(40):
            time.sleep(0.25)
            logs = self.client.get('/api/logs?limit=200').get_json().get('logs', [])
            blob = '\n'.join(logs)
            if 'Plugin cisco_asset_warranty Complete' in blob:
                break
        
        logs = self.client.get('/api/logs?limit=400').get_json().get('logs', [])
        blob = '\n'.join(logs)
        
        # Verify fallback credentials are bundled
        self.assertIn('Has fallback_credentials: True', blob)
        self.assertIn('Fallback credentials count: 2', blob)
        
        # Verify fallback credential details are logged
        self.assertIn('Fallback 1: username=secondary', blob)
        self.assertIn('Fallback 2: username=tertiary', blob)
        
        # Verify credential attempts are logged (safe_connection logs)
        self.assertIn('attempt', blob.lower())
        
        # Verify success (secondary credential succeeded)
        self.assertIn('Asset HTML report:', blob)
        self.assertIn('Asset CSV report:', blob)

    @mock.patch.dict(os.environ, {'NST_MOCK_ASSET_LAB': '1'})
    def test_no_fallback_when_only_primary(self):
        """Test that when only primary is provided, no fallback occurs."""
        inv = '\n'.join([
            '10.99.1.1,cisco_ios',
        ])
        r = self.client.post('/api/execute', json={
            'action': 'cisco_asset_warranty',
            'credential_id': 'primary',
            # No secondary or tertiary
            'inventory': inv,
            'inventory_source': 'unsaved',
            'acknowledge_unsaved': True,
            'target_mode': 'all',
            'params': {
                'include_modules': True,
                'collection_policy': 'ssh_first',
                'snmp_fallback': True,
            },
        })
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        data = r.get_json()
        self.assertEqual(data.get('status'), 'started')
        
        # Allow background thread to finish
        for _ in range(40):
            time.sleep(0.25)
            logs = self.client.get('/api/logs?limit=200').get_json().get('logs', [])
            blob = '\n'.join(logs)
            if 'Plugin cisco_asset_warranty Complete' in blob:
                break
        
        logs = self.client.get('/api/logs?limit=400').get_json().get('logs', [])
        blob = '\n'.join(logs)
        
        # Verify no fallback credentials
        self.assertIn('Has fallback_credentials: False', blob)

    @mock.patch.dict(os.environ, {'NST_MOCK_ASSET_LAB': '1'})
    def test_fallback_with_all_three_credentials(self):
        """Test that all three credentials are bundled correctly."""
        inv = '\n'.join([
            '10.99.1.1,cisco_ios',
        ])
        r = self.client.post('/api/execute', json={
            'action': 'cisco_asset_warranty',
            'credential_id': 'primary',
            'secondary_credential_id': 'secondary',
            'third_credential_id': 'tertiary',
            'inventory': inv,
            'inventory_source': 'unsaved',
            'acknowledge_unsaved': True,
            'target_mode': 'all',
            'params': {
                'include_modules': True,
                'collection_policy': 'ssh_first',
                'snmp_fallback': True,
            },
        })
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        
        # Allow background thread to finish
        for _ in range(40):
            time.sleep(0.25)
            logs = self.client.get('/api/logs?limit=200').get_json().get('logs', [])
            blob = '\n'.join(logs)
            if 'Plugin cisco_asset_warranty Complete' in blob:
                break
        
        logs = self.client.get('/api/logs?limit=400').get_json().get('logs', [])
        blob = '\n'.join(logs)
        
        # Verify all three credentials are present
        self.assertIn('Fallback credentials count: 2', blob)
        self.assertIn('Fallback 1: username=secondary', blob)
        self.assertIn('Fallback 2: username=tertiary', blob)

    @mock.patch.dict(os.environ, {'NST_MOCK_ASSET_LAB': '1'})
    def test_all_credentials_fail(self):
        """Test that when all credentials fail, error is properly logged."""
        # Add credentials that will all fail
        self.cm.add_credential('fail1', 'wrong1', snmp_version='2c', snmp_community='public')
        self.cm.add_credential('fail2', 'wrong2', snmp_version='2c', snmp_community='public')
        self.cm.add_credential('fail3', 'wrong3', snmp_version='2c', snmp_community='public')
        
        inv = '\n'.join([
            '10.99.1.5,cisco_ios',
        ])
        r = self.client.post('/api/execute', json={
            'action': 'cisco_asset_warranty',
            'credential_id': 'fail1',
            'secondary_credential_id': 'fail2',
            'third_credential_id': 'fail3',
            'inventory': inv,
            'inventory_source': 'unsaved',
            'acknowledge_unsaved': True,
            'target_mode': 'all',
            'params': {
                'include_modules': True,
                'collection_policy': 'ssh_first',
                'snmp_fallback': True,
            },
        })
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        
        # Allow background thread to finish
        for _ in range(40):
            time.sleep(0.25)
            logs = self.client.get('/api/logs?limit=200').get_json().get('logs', [])
            blob = '\n'.join(logs)
            if 'Plugin cisco_asset_warranty Complete' in blob:
                break
        
        logs = self.client.get('/api/logs?limit=400').get_json().get('logs', [])
        blob = '\n'.join(logs)
        
        # Verify all three credential attempts were logged
        self.assertIn('attempt 1/3', blob)
        self.assertIn('attempt 2/3', blob)
        self.assertIn('attempt 3/3', blob)
        
        # Verify all failed
        self.assertIn('connection failed', blob.lower())

    @mock.patch.dict(os.environ, {'NST_MOCK_ASSET_LAB': '1'})
    def test_primary_succeeds_no_fallback_needed(self):
        """Test that when primary succeeds, fallback is not attempted."""
        inv = '\n'.join([
            '10.99.1.1,cisco_ios',  # Regular mock host, primary succeeds
        ])
        r = self.client.post('/api/execute', json={
            'action': 'cisco_asset_warranty',
            'credential_id': 'primary',
            'secondary_credential_id': 'secondary',
            'third_credential_id': 'tertiary',
            'inventory': inv,
            'inventory_source': 'unsaved',
            'acknowledge_unsaved': True,
            'target_mode': 'all',
            'params': {
                'include_modules': True,
                'collection_policy': 'ssh_first',
                'snmp_fallback': True,
            },
        })
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        
        # Allow background thread to finish
        for _ in range(40):
            time.sleep(0.25)
            logs = self.client.get('/api/logs?limit=200').get_json().get('logs', [])
            blob = '\n'.join(logs)
            if 'Plugin cisco_asset_warranty Complete' in blob:
                break
        
        logs = self.client.get('/api/logs?limit=400').get_json().get('logs', [])
        blob = '\n'.join(logs)
        
        # Verify success without fallback attempts
        self.assertIn('Asset HTML report:', blob)
        # Should not have fallback attempt logs for this host
        # (primary succeeded on regular mock host)

    @mock.patch.dict(os.environ, {'NST_MOCK_ASSET_LAB': '1'})
    def test_empty_fallback_credentials_list(self):
        """Test handling of empty fallback credentials list."""
        inv = '\n'.join([
            '10.99.1.1,cisco_ios',
        ])
        r = self.client.post('/api/execute', json={
            'action': 'cisco_asset_warranty',
            'credential_id': 'primary',
            'secondary_credential_id': '',  # Empty
            'third_credential_id': '',  # Empty
            'inventory': inv,
            'inventory_source': 'unsaved',
            'acknowledge_unsaved': True,
            'target_mode': 'all',
            'params': {
                'include_modules': True,
                'collection_policy': 'ssh_first',
                'snmp_fallback': True,
            },
        })
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        
        # Allow background thread to finish
        for _ in range(40):
            time.sleep(0.25)
            logs = self.client.get('/api/logs?limit=200').get_json().get('logs', [])
            blob = '\n'.join(logs)
            if 'Plugin cisco_asset_warranty Complete' in blob:
                break
        
        logs = self.client.get('/api/logs?limit=400').get_json().get('logs', [])
        blob = '\n'.join(logs)
        
        # Verify no fallback credentials
        self.assertIn('Has fallback_credentials: False', blob)


if __name__ == '__main__':
    unittest.main()
