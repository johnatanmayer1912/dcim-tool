"""Zero-trust: non-Cisco platforms must report 'not a cisco device' (never vague unknown)."""
from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from modules.asset_collection_policy import (
    NON_CISCO_DEVICE_LABEL,
    collect_device_assets,
    is_cisco_platform,
)
from modules.plugins.cisco_asset_warranty_plugin import run as warranty_run
from utils.report_formatter import format_asset_warranty_csv, format_asset_warranty_html, _get_warranty_status_badge


class TestNonCiscoAssetWarrantyLabel(unittest.TestCase):
    def test_platform_detection(self):
        self.assertTrue(is_cisco_platform('cisco_ios'))
        self.assertTrue(is_cisco_platform('cisco_nxos'))
        self.assertTrue(is_cisco_platform(''))
        self.assertFalse(is_cisco_platform('juniper_junos'))
        self.assertFalse(is_cisco_platform('arista_eos'))
        self.assertFalse(is_cisco_platform('linux'))

    def test_collect_juniper_skips_ssh_and_labels(self):
        logs = []
        bundle = collect_device_assets(
            {'host': '10.9.9.9', 'device_type': 'juniper_junos'},
            {'username': 'u', 'password': 'p'},
            {'collection_policy': 'ssh_only'},
            log_func=logs.append,
        )
        assets = bundle['assets']
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0]['warranty_status'], NON_CISCO_DEVICE_LABEL)
        self.assertEqual(assets[0]['model_name'], NON_CISCO_DEVICE_LABEL)
        self.assertEqual(bundle['collection_summary'], 'not_a_cisco_device')
        blob = '\n'.join(logs)
        self.assertRegex(blob, re.compile(r'not a cisco device', re.I))
        self.assertNotRegex(blob, re.compile(r'Connecting to device'))

    def test_plugin_reports_contain_label_not_unknown_for_juniper(self):
        device = {'host': '10.8.8.8', 'device_type': 'juniper_junos'}
        result = warranty_run(device, {'username': 'u', 'password': 'p'}, {}, {}, None)
        self.assertEqual(result['status'], 'success')
        assets = result['data']['assets']
        self.assertEqual(assets[0]['warranty_status'], NON_CISCO_DEVICE_LABEL)
        # Must not invent Cisco demo EOL for Juniper
        self.assertNotEqual(assets[0].get('warranty_status'), 'demo')
        self.assertNotEqual(assets[0].get('warranty_status'), 'unknown')

        html = format_asset_warranty_html(result['data'], device['host'])
        csv = format_asset_warranty_csv(result['data'], device['host'])
        self.assertRegex(html, re.compile(r'not a cisco device', re.I))
        self.assertRegex(csv, re.compile(r'not a cisco device', re.I))
        # Badge path
        badge = _get_warranty_status_badge(NON_CISCO_DEVICE_LABEL)
        self.assertIn('not a cisco device', badge)

    def test_arista_also_labeled(self):
        bundle = collect_device_assets(
            {'host': '10.7.7.7', 'device_type': 'arista_eos'},
            {'username': 'u', 'password': 'p'},
            {},
            None,
        )
        self.assertEqual(bundle['assets'][0]['warranty_status'], NON_CISCO_DEVICE_LABEL)


class TestCredentialFallbackMockSSHZeroTrust(unittest.TestCase):
    """Assert SSH attempt order with mocked connect_permissive — not log-only trust."""

    def setUp(self):
        from modules.credential_manager import CredentialManager
        import vlan_checker_web as web
        self.tmp = tempfile.mkdtemp()
        self.cm = CredentialManager(storage_dir=self.tmp)
        web.app.config['TESTING'] = True
        web.credential_manager = self.cm
        self.client = web.app.test_client()
        self.web = web
        self.master = 'zt_master_pw_9f3a'
        try:
            web.console_log_buffer.clear_for_tests()
        except Exception:
            pass

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _vault_three(self):
        for user, label in (
            ('primary_user', 'Primary'),
            ('secondary_user', 'Secondary'),
            ('tertiary_user', 'Tertiary'),
        ):
            r = self.client.post('/api/credentials/add', json={
                'username': user, 'password': f'{user}_pass', 'admin_password': 'en',
                'label': label, 'force': True,
            })
            self.assertEqual(r.status_code, 200, r.get_json())

    def test_api_resolve_includes_fallback_bundle(self):
        self._vault_three()
        from utils.vault_credentials import resolve_execute_credentials
        data = {
            'credential_id': 'primary_user',
            'secondary_credential_id': 'secondary_user',
            'third_credential_id': 'tertiary_user',
        }
        resolved = resolve_execute_credentials(data, self.cm, {})
        self.assertEqual(resolved['username'], 'primary_user')
        self.assertEqual(len(resolved['fallback_credentials']), 2)
        self.assertEqual(resolved['fallback_credentials'][0]['username'], 'secondary_user')
        self.assertEqual(resolved['fallback_credentials'][1]['username'], 'tertiary_user')
        # Zero trust: secrets present in resolved but must not appear in public session view
        view = self.client.get('/api/session/credentials').get_json()
        blob = str(view)
        self.assertNotIn('primary_pass', blob)
        self.assertNotIn('secondary_pass', blob)

    def test_session_persists_secondary_third_ids(self):
        self._vault_three()
        r = self.client.post('/api/session/credentials', json={
            'username': 'primary_user',
            'credential_id': 'primary_user',
            'secondary_credential_id': 'secondary_user',
            'secondary_label': 'Secondary',
            'third_credential_id': 'tertiary_user',
            'third_label': 'Tertiary',
        })
        self.assertEqual(r.status_code, 200)
        view = self.client.get('/api/session/credentials').get_json()
        self.assertEqual(view.get('credential_id'), 'primary_user')
        self.assertEqual(view.get('secondary_credential_id'), 'secondary_user')
        self.assertEqual(view.get('third_credential_id'), 'tertiary_user')
        self.assertFalse(view.get('has_password'))

    def test_mock_ssh_primary_fail_secondary_success_order(self):
        from modules.network_base import safe_connection
        from tests.mock_ssh_server import MockSSHServer, mock_connect_permissive_with_fallback
        from unittest.mock import patch

        server = MockSSHServer()
        server.add_valid_credential('secondary_user', 'secondary_pass')
        attempts = []

        def log(msg):
            attempts.append(msg)

        device = {'host': '10.1.1.1', 'device_type': 'cisco_ios'}
        fb = [{'username': 'secondary_user', 'password': 'secondary_pass', 'enable_pwd': '', 'label': 'Secondary'}]
        with patch('modules.network_base.connect_permissive', mock_connect_permissive_with_fallback(server, log)):
            with safe_connection(device, 'primary_user', 'wrong', '', log_func=log, fallback_credentials=fb) as conn:
                self.assertIsNotNone(conn)
        users = [a['username'] for a in server.get_connection_attempts()]
        self.assertEqual(users, ['primary_user', 'secondary_user'])

    def test_execute_payload_reaches_plugin_with_fallback(self):
        """Zero trust: execute with secondary/third → plugin logs + mock path uses fallback."""
        self._vault_three()
        from unittest.mock import patch

        captured = {}

        def fake_collect(device, credentials, params=None, log_func=None):
            captured['credentials'] = credentials
            captured['device'] = device
            if log_func:
                log_func(f"[{device.get('host')}] Has fallback_credentials: {bool(credentials.get('fallback_credentials'))}")
                log_func(f"[{device.get('host')}] Fallback credentials count: {len(credentials.get('fallback_credentials') or [])}")
            return {
                'assets': [{
                    'host': device.get('host'),
                    'device_type': 'cisco_ios',
                    'pid': 'C9300-48P',
                    'serial_number': 'FDOZT001',
                    'hostname': 'sw-zt',
                    'warranty_status': 'active',
                    'collection_method': 'ssh',
                }],
                'collection_summary': 'ssh',
            }

        from modules.plugin_registry import PluginRegistry
        reg = PluginRegistry()
        cisco_plugin_mod = reg.get_plugin('cisco_asset_warranty')['module']

        with patch.object(cisco_plugin_mod, 'collect_device_assets', fake_collect), \
             patch.object(cisco_plugin_mod, 'enrich_asset_data', lambda a, *x, **k: a), \
             patch('modules.asset_collection_policy.collect_device_assets', fake_collect):
            r = self.client.post('/api/execute', json={
                'action': 'cisco_asset_warranty',
                'credential_id': 'primary_user',
                'secondary_credential_id': 'secondary_user',
                'third_credential_id': 'tertiary_user',
                'inventory': '10.50.50.50,cisco_ios',
                'inventory_source': 'unsaved',
                'acknowledge_unsaved': True,
                'target_mode': 'all',
                'params': {'collection_policy': 'ssh_only', 'snmp_fallback': False},
            })
            import time
            for _ in range(60):
                if captured:
                    break
                time.sleep(0.05)
        self.assertEqual(r.status_code, 200, r.get_json())
        fb = captured.get('credentials', {}).get('fallback_credentials') or []
        self.assertEqual(len(fb), 2, captured)
        self.assertEqual(fb[0].get('username'), 'secondary_user')

    def test_execute_juniper_inventory_labels_report(self):
        """Execute API must label Juniper as non-Cisco (report + logs)."""
        self._vault_three()
        # Prefer direct plugin truth (no shared-buffer race); then smoke execute API.
        from modules.plugins.cisco_asset_warranty_plugin import run as warranty_run
        direct = warranty_run(
            {'host': '10.60.60.60', 'device_type': 'juniper_junos'},
            {'username': 'primary_user', 'password': 'x'},
            {'collection_policy': 'ssh_only'},
            {},
            None,
        )
        self.assertEqual(direct['status'], 'success')
        self.assertEqual(
            direct['data']['assets'][0]['warranty_status'],
            'not a cisco device',
        )

        r = self.client.post('/api/execute', json={
            'action': 'cisco_asset_warranty',
            'credential_id': 'primary_user',
            'inventory': '10.60.60.61,juniper_junos',
            'inventory_source': 'unsaved',
            'acknowledge_unsaved': True,
            'target_mode': 'all',
            'params': {'collection_policy': 'ssh_only'},
        })
        self.assertEqual(r.status_code, 200, r.get_json())
        import time
        blob = ''
        for _ in range(120):
            logs = self.client.get('/api/logs?limit=200').get_json().get('logs') or []
            blob = '\n'.join(str(x) for x in logs)
            if '10.60.60.61' in blob and 'not a cisco device' in blob.lower():
                break
            time.sleep(0.05)
        self.assertIn('10.60.60.61', blob)
        self.assertRegex(blob, re.compile(r'not a cisco device', re.I))


class TestConsolidatorZeroTrustMultiFile(unittest.TestCase):
    def test_multi_file_html_csv_regex_contract(self):
        from utils.asset_warranty_consolidator import AssetWarrantyConsolidator
        from utils.report_formatter import format_asset_warranty_csv

        tmp = tempfile.mkdtemp()
        try:
            cons = AssetWarrantyConsolidator(base_dir=str(Path(tmp) / 'reports'))
            # Cisco CSV
            cisco = {
                'host': '10.0.0.1',
                'assets': [{
                    'host': '10.0.0.1', 'hostname': 'c1', 'pid': 'C9300-48P',
                    'serial_number': 'FDOC1', 'software_version': '17.9',
                    'warranty_status': 'active', 'end_of_life': '2030-01-01',
                    'end_of_support': '2033-01-01',
                }],
            }
            # Non-cisco CSV row
            noncisco_csv = (
                'Host,Hostname,Product ID (PID),Serial Number,Software Version,'
                'Warranty Status,End of Life,End of Support\n'
                '10.0.0.2,j1,,JNPR1,,not a cisco device,,\n'
            )
            pretty_html = '''<!DOCTYPE html><html><body>
            <table class="nst-asset-table">
            <tr>
              <th>Host</th><th>Hostname</th><th>Product ID (PID)</th><th>Serial Number</th>
              <th>Software Version</th><th>Warranty Status</th><th>End of Life</th><th>End of Support</th>
            </tr>
            <tr>
              <td>
                10.0.0.3
              </td>
              <td>
                c2
              </td>
              <td>C9500</td>
              <td>
                FDOC2
              </td>
              <td>17.6</td><td>active</td><td>2028-01-01</td><td>2031-01-01</td>
            </tr>
            </table>
            <div id="nst-cisco-eol-modal"><table><tr><td>bogus</td><td>FAKE</td></tr></table></div>
            </body></html>'''
            (cons.input_dir / 'a_cisco.csv').write_text(format_asset_warranty_csv(cisco, '10.0.0.1'), encoding='utf-8')
            (cons.input_dir / 'b_juniper.csv').write_text(noncisco_csv, encoding='utf-8')
            (cons.input_dir / 'c_pretty.html').write_text(pretty_html, encoding='utf-8')
            (cons.input_dir / 'd_extra.html').write_text(
                '<table class="nst-asset-table"><tr><th>Hostname</th><th>Serial</th><th>Model</th></tr>'
                '<tr><td>c3</td><td>FDOC3</td><td>ISR4331</td></tr></table>',
                encoding='utf-8',
            )
            result = cons.consolidate_reports('zt_mutual')
            self.assertTrue(result['success'])
            self.assertGreaterEqual(result['summary']['total_devices'], 4)
            html = Path(result['output_path']).read_text(encoding='utf-8')
            csv = Path(result['output_csv_path']).read_text(encoding='utf-8')
            for serial in ('FDOC1', 'FDOC2', 'FDOC3', 'JNPR1'):
                self.assertIn(serial, csv)
            self.assertRegex(csv, re.compile(r'not a cisco device', re.I))
            self.assertNotIn('FAKE', csv)
            self.assertRegex(html, re.compile(r'(?:Unique|Total)\s+Devices', re.I))
            self.assertIsNone(result.get('warning'))
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
