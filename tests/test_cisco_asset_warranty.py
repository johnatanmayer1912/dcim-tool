"""Cisco asset/warranty inventory — parsers, SSH/SNMP fallback, mock lab, reports."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.asset_collection_policy import collect_device_assets
from modules.credential_manager import CredentialManager
from modules.mock_asset_lab import mock_enabled
from modules.parsers.cisco_asset_inventory import (
    merge_asset_identity,
    parse_inventory_blocks,
    parse_ios_nxos_version,
)
from modules.plugins import cisco_asset_warranty_plugin
from modules.snmp_asset_collector import snmp_credentials_configured
from utils.cisco_asset_reports import generate_cisco_asset_consolidated_reports
from utils.vault_credentials import mapping_has_secret_fields, public_credential_view, resolve_execute_credentials

_FIXTURE = os.path.join(os.path.dirname(__file__), 'fixtures', 'asset')


def _read(name: str) -> str:
    with open(os.path.join(_FIXTURE, name), 'r', encoding='utf-8') as fh:
        return fh.read()


class TestCiscoAssetParsers(unittest.TestCase):
    def test_parse_ios_version_and_inventory(self):
        version = _read('ios_show_version.txt')
        inventory = _read('ios_show_inventory.txt')
        vf = parse_ios_nxos_version(version)
        self.assertEqual(vf['serial_number'], 'FCW2345A1B2')
        self.assertIn('C9200L', vf['pid'])
        rows = parse_inventory_blocks(inventory)
        merged = merge_asset_identity(vf, rows, include_modules=True)
        self.assertEqual(merged['serial_number'], 'FCW2345A1B2')
        self.assertGreaterEqual(merged.get('module_count', 0), 2)

    def test_parse_nxos_inventory(self):
        inventory = _read('nxos_show_inventory.txt')
        rows = parse_inventory_blocks(inventory)
        chassis = rows[0]
        self.assertEqual(chassis['pid'], 'N9K-C93180YC-FX')
        self.assertEqual(chassis['serial_number'], 'FOC12345678')


class TestSnmpCredentials(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cm = CredentialManager(storage_dir=self.tmp)

    def test_vault_snmp_not_exposed_via_public_view(self):
        self.cm.add_credential(
            'snmpop', 'ssh-pass', snmp_version='2c', snmp_community='public-lab',
        )
        cred = self.cm.get_credential('snmpop')
        view = public_credential_view(cred, 'snmpop')
        self.assertTrue(view['has_snmp'])
        self.assertEqual(view['snmp_version'], '2c')
        self.assertNotIn('snmp_community', view)
        self.assertFalse(mapping_has_secret_fields(view))

    def test_resolve_execute_includes_snmp_secrets_in_process_only(self):
        self.cm.add_credential(
            'snmpop', 'ssh-pass', snmp_version='2c', snmp_community='secret-community',
        )
        resolved = resolve_execute_credentials(
            {'credential_id': 'snmpop'}, self.cm, None,
        )
        self.assertEqual(resolved['snmp_community'], 'secret-community')
        self.assertTrue(snmp_credentials_configured(resolved))


class TestMockAssetLab(unittest.TestCase):
    def setUp(self):
        self._env = os.environ.get('NST_MOCK_ASSET_LAB')
        os.environ['NST_MOCK_ASSET_LAB'] = '1'
        self.credentials = {
            'username': 'lab',
            'password': 'lab',
            'secret': None,
            'snmp_version': '2c',
            'snmp_community': 'public',
        }

    def tearDown(self):
        if self._env is None:
            os.environ.pop('NST_MOCK_ASSET_LAB', None)
        else:
            os.environ['NST_MOCK_ASSET_LAB'] = self._env

    def test_ios_ssh_collection(self):
        device = {'host': '10.99.1.1', 'device_type': 'cisco_ios'}
        bundle = collect_device_assets(device, self.credentials, {'include_modules': True})
        assets = bundle['assets']
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0]['collection_method'], 'ssh')
        self.assertEqual(assets[0]['serial_number'], 'FCW2345A1B2')

    def test_nxos_ssh_collection(self):
        device = {'host': '10.99.1.2', 'device_type': 'cisco_nxos'}
        bundle = collect_device_assets(device, self.credentials, {'include_modules': True})
        self.assertEqual(bundle['assets'][0]['pid'], 'N9K-C93180YC-FX')

    def test_aci_rest_collection(self):
        device = {'host': '10.99.1.3', 'device_type': 'cisco_aci'}
        bundle = collect_device_assets(device, self.credentials, {})
        self.assertGreaterEqual(len(bundle['assets']), 2)
        self.assertEqual(bundle['assets'][0]['collection_method'], 'aci_rest')

    def test_snmp_fallback_when_ssh_fails(self):
        device = {'host': '10.99.1.4', 'device_type': 'cisco_ios'}
        bundle = collect_device_assets(
            device, self.credentials,
            {'collection_policy': 'ssh_first', 'snmp_fallback': True},
        )
        self.assertEqual(bundle['collection_summary'], 'snmp_fallback')
        self.assertEqual(bundle['assets'][0]['collection_method'], 'snmp')
        self.assertEqual(bundle['assets'][0]['serial_number'], 'FCW2345A1B2')


class TestCiscoAssetPlugin(unittest.TestCase):
    def setUp(self):
        os.environ['NST_MOCK_ASSET_LAB'] = '1'

    def tearDown(self):
        os.environ.pop('NST_MOCK_ASSET_LAB', None)

    def test_plugin_run_ios(self):
        device = {'host': '10.99.1.1', 'device_type': 'cisco_ios'}
        creds = {'username': 'u', 'password': 'p', 'snmp_version': '2c', 'snmp_community': 'c'}
        out = cisco_asset_warranty_plugin.run(device, creds, {'include_modules': True}, {}, print)
        self.assertEqual(out['status'], 'success')
        self.assertGreaterEqual(out['data']['asset_count'], 1)

    def test_consolidated_html_csv_reports(self):
        results = [
            {
                'status': 'success',
                'device': '10.99.1.1',
                'data': {
                    'assets': [{
                        'host': '10.99.1.1',
                        'hostname': 'MOCK-IOS-01',
                        'device_type': 'cisco_ios',
                        'collection_method': 'ssh',
                        'pid': 'C9200L-48P-4G',
                        'vid': 'V02',
                        'serial_number': 'FCW2345A1B2',
                        'software_version': '17.9.4a',
                        'warranty_end': '2027-01-01',
                        'warranty_status': 'active',
                        'contract_status': 'Active (mock lab)',
                        'severity': 'ok',
                        'enrichment_source': 'mock_lab',
                    }],
                },
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            with patch('utils.cisco_asset_reports.prepare_run_output') as prep:
                from utils.output_paths import prepare_run_output as real_prep
                paths = real_prep('plugins', 'test_asset')
                paths['run_dir'] = tmp
                paths['manifest_path'] = os.path.join(tmp, 'manifest.json')
                prep.return_value = paths
                with patch('utils.cisco_asset_reports.path_in_run', side_effect=lambda p, name: os.path.join(tmp, name)):
                    out = generate_cisco_asset_consolidated_reports(results)
            self.assertTrue(os.path.isfile(out['csv']))
            self.assertTrue(os.path.isfile(out['html']))
            html = open(out['html'], encoding='utf-8').read()
            self.assertIn('Export as PDF', html)
            self.assertIn('FCW2345A1B2', html)
            csv_body = open(out['csv'], encoding='utf-8').read()
            self.assertIn('serial_number', csv_body)
            self.assertIn('FCW2345A1B2', csv_body)


class TestPluginRegistry(unittest.TestCase):
    def test_plugin_registered(self):
        from modules.plugin_registry import get_registry
        reg = get_registry()
        self.assertTrue(reg.exists('cisco_asset_warranty'))


if __name__ == '__main__':
    unittest.main()
