"""Integration: /api/execute cisco_asset_warranty with mock asset lab."""
from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestExecuteCiscoAssetWarranty(unittest.TestCase):
    def setUp(self):
        from modules.credential_manager import CredentialManager
        self.tmp = tempfile.mkdtemp()
        self.cm = CredentialManager(storage_dir=self.tmp)
        self.cm.add_credential('lab', 'labpass', snmp_version='2c', snmp_community='public')
        # Add secondary and tertiary credentials for fallback testing
        self.cm.add_credential('lab_secondary', 'labpass2', snmp_version='2c', snmp_community='public')
        self.cm.add_credential('lab_tertiary', 'labpass3', snmp_version='2c', snmp_community='public')

        import vlan_checker_web as web
        web.app.config['TESTING'] = True
        web.credential_manager = self.cm
        self.client = web.app.test_client()
        self.web = web

    def tearDown(self):
        pass

    @mock.patch.dict(os.environ, {'NST_MOCK_ASSET_LAB': '1'})
    def test_execute_starts_plugin(self):
        inv = '\n'.join([
            '10.99.1.1,cisco_ios',
            '10.99.1.2,cisco_nxos',
            '10.99.1.3,cisco_aci',
            '10.99.1.4,cisco_ios',
        ])
        r = self.client.post('/api/execute', json={
            'action': 'cisco_asset_warranty',
            'credential_id': 'lab',
            'secondary_credential_id': 'lab_secondary',
            'third_credential_id': 'lab_tertiary',
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
        self.assertGreaterEqual(data.get('device_count', 0), 4)
        # Allow background thread to finish
        for _ in range(40):
            time.sleep(0.25)
            logs = self.client.get('/api/logs?limit=200').get_json().get('logs', [])
            blob = '\n'.join(logs)
            if 'Plugin cisco_asset_warranty Complete' in blob:
                break
        logs = self.client.get('/api/logs?limit=400').get_json().get('logs', [])
        blob = '\n'.join(logs)
        self.assertIn('Asset HTML report:', blob)
        self.assertIn('Asset CSV report:', blob)
        # Verify fallback credentials are logged
        self.assertIn('Has fallback_credentials: True', blob)
        self.assertIn('Fallback credentials count: 2', blob)


if __name__ == '__main__':
    unittest.main()
