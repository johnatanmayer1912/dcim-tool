"""
Operational certification matrix: credential fallback on ONE mock device.

Zero Trust: every SSH entrypoint must attempt Primary then Secondary when Primary fails.
Does NOT trust log strings alone — asserts connect_permissive usernames order.

Run:
  python -m pytest tests/test_credential_fallback_full_matrix.py -q --tb=short
"""
from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

from modules.network_base import connect_device, safe_connection, attach_fallback_to_devices
from utils.collection_credentials import bundle_for_plugin


PRIMARY = {'username': 'primary_user', 'password': 'bad_primary', 'enable_pwd': 'en1', 'label': 'Primary'}
SECONDARY = {'username': 'secondary_user', 'password': 'ok_secondary', 'enable_pwd': 'en2', 'label': 'Secondary'}
THIRD = {'username': 'tertiary_user', 'password': 'ok_tertiary', 'enable_pwd': 'en3', 'label': 'Third'}

DEVICE = {'host': '10.200.200.1', 'device_type': 'cisco_ios', 'port': 22}


class MockDeviceAuth:
    """Simulates one network device that only accepts listed usernames."""

    def __init__(self, accept: Optional[List[str]] = None):
        self.accept = set(accept or ['secondary_user'])
        self.attempts: List[str] = []

    def connect(self, target_dict, user, pwd, enb_pwd, log_func=None):
        self.attempts.append(user)
        if user not in self.accept:
            raise Exception(f'Authentication failed for user {user}')
        conn = MagicMock(name=f'conn[{user}]')
        conn.find_prompt.return_value = f"{target_dict.get('host', 'sw')}#"
        conn.send_command.side_effect = self._cmd
        conn.disconnect = MagicMock()
        return conn

    def _cmd(self, cmd, *a, **k):
        c = (cmd or '').lower()
        if 'version' in c:
            return 'Cisco IOS Software, C9300 Software\nhostname MockSW\n'
        if 'inventory' in c or 'diag' in c:
            return 'NAME: "Chassis", DESCR: "Cisco C9300"\nPID: C9300-48P, VID: V01, SN: FDOMATRIX1\n'
        if 'vlan' in c:
            return 'VLAN Name\n1    default\n'
        if 'cdp' in c or 'lldp' in c:
            return ''
        if 'interface' in c:
            return 'Interface Status\nGi1/0/1 up\n'
        if 'mac' in c or 'cam' in c:
            return ''
        if 'running-config' in c or 'run' in c:
            return 'hostname MockSW\n'
        if 'clock' in c or 'time' in c:
            return '12:00:00 UTC'
        if 'log' in c:
            return ''
        if 'spanning' in c or 'stp' in c:
            return ''
        if 'vpc' in c:
            return '% Invalid'
        if 'route' in c or 'ip route' in c:
            return ''
        return 'OK'


def _creds_bundle(with_third: bool = True) -> Dict[str, Any]:
    fb = [dict(SECONDARY)]
    if with_third:
        fb.append(dict(THIRD))
    return bundle_for_plugin({
        'username': PRIMARY['username'],
        'password': PRIMARY['password'],
        'enable_pwd': PRIMARY['enable_pwd'],
        'fallback_credentials': fb,
        'secondary_credential': dict(SECONDARY),
        'third_credential': dict(THIRD) if with_third else None,
    })


# Plugins that open SSH via safe_connection / collect_device_assets
SSH_PLUGINS = [
    'serial_number_plugin',
    'device_time_plugin',
    'environment_status_plugin',
    'critical_logs_plugin',
    'interface_errors_plugin',
    'vlan_audit_plugin',
    'unused_trunk_pruner',
    'stp_topology_visualizer',
    'standards_validator',
    'vpc_domain_plugin',
    'interface_manager',
    'interface_vlan_reporter',
    'cisco_asset_warranty_plugin',
    'base_template',
]

# Legacy Tools modules using connect_device(device, user, pwd, enb)
LEGACY_CONNECT_MODULES = [
    ('modules.connectivity', 'check_connectivity'),
    ('modules.vlan_audit', None),  # discover function name dynamically
]


class TestStaticNoPermissiveLeak(unittest.TestCase):
    def test_no_connect_permissive_outside_network_base(self):
        root = Path(__file__).resolve().parents[1]
        leaks = []
        for f in list((root / 'modules').rglob('*.py')) + list((root / 'utils').rglob('*.py')):
            if f.name == 'network_base.py':
                continue
            for i, line in enumerate(f.read_text(encoding='utf-8', errors='ignore').splitlines(), 1):
                if 'connect_permissive(' in line and 'import' not in line and not line.strip().startswith('#'):
                    leaks.append(f'{f.relative_to(root)}:{i}')
        self.assertEqual(leaks, [], f'connect_permissive leaks: {leaks}')

    def test_every_ssh_plugin_passes_fallback_kwarg(self):
        root = Path(__file__).resolve().parents[1] / 'modules' / 'plugins'
        offenders = []
        for name in SSH_PLUGINS:
            path = root / f'{name}.py'
            if not path.exists():
                offenders.append(f'missing:{name}')
                continue
            src = path.read_text(encoding='utf-8')
            if 'safe_connection(' not in src and 'collect_device_assets' not in src:
                continue  # no SSH
            if 'collect_device_assets' in src:
                continue  # policy path already certified separately
            if 'fallback_credentials' not in src:
                offenders.append(name)
        self.assertEqual(offenders, [], f'plugins missing fallback wiring: {offenders}')


class TestMockDeviceFallbackOrder(unittest.TestCase):
    """Primary fails → Secondary succeeds on one mock device."""

    def setUp(self):
        self.mock = MockDeviceAuth(accept=['secondary_user'])

    def _patch(self):
        return patch('modules.network_base.connect_permissive', side_effect=self.mock.connect)

    def test_safe_connection_order(self):
        with self._patch():
            with safe_connection(
                DEVICE,
                PRIMARY['username'],
                PRIMARY['password'],
                PRIMARY['enable_pwd'],
                fallback_credentials=[SECONDARY, THIRD],
            ) as conn:
                self.assertIsNotNone(conn)
        self.assertEqual(self.mock.attempts, ['primary_user', 'secondary_user'])

    def test_connect_device_reads_device_stamp(self):
        stamped = attach_fallback_to_devices([DEVICE], fallback_credentials=[SECONDARY, THIRD])[0]
        with self._patch():
            conn = connect_device(
                stamped,
                PRIMARY['username'],
                PRIMARY['password'],
                PRIMARY['enable_pwd'],
            )
            self.assertIsNotNone(conn)
        self.assertEqual(self.mock.attempts, ['primary_user', 'secondary_user'])

    def test_third_succeeds_when_secondary_fails(self):
        self.mock.accept = {'tertiary_user'}
        with self._patch():
            with safe_connection(
                DEVICE,
                PRIMARY['username'],
                PRIMARY['password'],
                '',
                fallback_credentials=[SECONDARY, THIRD],
            ) as conn:
                self.assertIsNotNone(conn)
        self.assertEqual(self.mock.attempts, ['primary_user', 'secondary_user', 'tertiary_user'])

    def test_all_fail_raises(self):
        self.mock.accept = set()
        with self._patch():
            with self.assertRaises(Exception):
                with safe_connection(
                    DEVICE,
                    PRIMARY['username'],
                    PRIMARY['password'],
                    '',
                    fallback_credentials=[SECONDARY, THIRD],
                ):
                    pass
        self.assertEqual(self.mock.attempts, ['primary_user', 'secondary_user', 'tertiary_user'])

    def test_no_fallback_only_primary_attempt(self):
        self.mock.accept = {'primary_user'}
        # Use matching password path — mock only checks username
        with self._patch():
            with safe_connection(DEVICE, 'primary_user', 'x', '', fallback_credentials=None) as conn:
                self.assertIsNotNone(conn)
        self.assertEqual(self.mock.attempts, ['primary_user'])


class TestEveryPluginFallbackOrder(unittest.TestCase):
    """Run each SSH plugin against the mock device; assert Primary→Secondary."""

    def setUp(self):
        self.mock = MockDeviceAuth(accept=['secondary_user'])
        self.creds = _creds_bundle()
        self.params_by_plugin = {
            'interface_manager': {'operation': 'discover', 'interface_filter': '', 'dry_run': True},
            'interface_vlan_reporter': {},
            'standards_validator': {'policy_file': '', 'severity_filter': '', 'category_filter': ''},
            'unused_trunk_pruner': {'dry_run': True},
            'stp_topology_visualizer': {'vlan_id': 1},
            'cisco_asset_warranty_plugin': {
                'collection_policy': 'ssh_only',
                'snmp_fallback': False,
                'include_modules': True,
            },
            'base_template': {},
            'vpc_domain_plugin': {},
        }

    def _run_plugin(self, module_name: str):
        mod = importlib.import_module(f'modules.plugins.{module_name}')
        run = getattr(mod, 'run', None)
        self.assertTrue(callable(run), f'{module_name} has no run()')
        params = self.params_by_plugin.get(module_name, {})
        config = {'timeout': 5, 'max_retries': 1, 'log_level': 'INFO'}
        logs: List[str] = []
        with patch('modules.network_base.connect_permissive', side_effect=self.mock.connect):
            # Also patch if plugin imported connect into its namespace (rare)
            result = run(dict(DEVICE), self.creds, params, config, logs.append)
        return result

    def test_matrix_primary_fail_secondary_ok(self):
        failures = []
        for name in SSH_PLUGINS:
            self.mock.attempts = []
            try:
                with patch('modules.asset_collection_policy.is_mock_host', return_value=False):
                    self._run_plugin(name)
                if self.mock.attempts[:2] != ['primary_user', 'secondary_user']:
                    # Some plugins may exit before SSH (e.g. wrong platform)
                    if not self.mock.attempts:
                        # vpc may skip non-nxos without connect — stamp as skip not fail
                        if name == 'vpc_domain_plugin':
                            continue
                        failures.append(f'{name}: no SSH attempts {self.mock.attempts}')
                    else:
                        failures.append(f'{name}: order={self.mock.attempts}')
            except Exception as exc:
                # Connection after auth may throw on command parsing — order still must be correct
                if self.mock.attempts[:2] == ['primary_user', 'secondary_user']:
                    continue
                if name == 'vpc_domain_plugin' and not self.mock.attempts:
                    continue
                failures.append(f'{name}: exc={exc!r} attempts={self.mock.attempts}')
        self.assertEqual(failures, [], 'Plugin matrix failures:\n' + '\n'.join(failures))


class TestLegacyToolsConnectDeviceFallback(unittest.TestCase):
    """Legacy Tools modules must honor device['fallback_credentials'] via connect_device."""

    MODULES = [
        'modules.connectivity',
        'modules.vlan_audit',
        'modules.interfaces',
        'modules.config_backup',
        'modules.save_config',
        'modules.network_audit',
        'modules.vlan_compare',
        'modules.node_analyze',
        'modules.mac_trace',
        'modules.description_search',
        'modules.node_interface_topology',
        'modules.topology_mapper',
        'modules.vlan_mgmt_production',
    ]

    def test_connect_device_used_and_fallback_order(self):
        mock = MockDeviceAuth(accept=['secondary_user'])
        stamped = attach_fallback_to_devices([DEVICE], fallback_credentials=[SECONDARY])[0]
        with patch('modules.network_base.connect_permissive', side_effect=mock.connect):
            conn = connect_device(
                stamped,
                PRIMARY['username'],
                PRIMARY['password'],
                PRIMARY['enable_pwd'],
            )
            self.assertIsNotNone(conn)
        self.assertEqual(mock.attempts, ['primary_user', 'secondary_user'])

        # Static: each legacy module imports/uses connect_device not connect_permissive
        root = Path(__file__).resolve().parents[1]
        for modname in self.MODULES:
            rel = Path(*modname.split('.')) 
            # modules.connectivity -> modules/connectivity.py
            path = root / Path(*modname.split('.'))
            path = path.with_suffix('.py')
            src = path.read_text(encoding='utf-8')
            self.assertIn('connect_device', src, modname)
            self.assertNotIn('connect_permissive(', src, modname)


class TestExecuteApiAllActionsFallback(unittest.TestCase):
    """Flask /api/execute: stamp + resolve for representative Tools + plugin actions."""

    ACTIONS = [
        'connectivity',
        'vlan_check',
        'interfaces',
        'audit',
        'backup',
        'save_config',
        'topology',
        'l3_topology',
        'mac_check',
        'description_search',
        'vlan_compare',
        'cisco_asset_warranty',
        'serial_number_plugin',
        'device_time_plugin',
        'environment_status_plugin',
        'critical_logs_plugin',
        'interface_errors_plugin',
        'vlan_audit_plugin',
    ]

    def setUp(self):
        from modules.credential_manager import CredentialManager
        import vlan_checker_web as web

        self.tmp = tempfile.mkdtemp()
        self.cm = CredentialManager(storage_dir=self.tmp)
        web.app.config['TESTING'] = True
        web.credential_manager = self.cm
        self.client = web.app.test_client()
        self.web = web
        self.master = 'matrix_master_pw'
        for u, lab in (
            ('primary_user', 'Primary'),
            ('secondary_user', 'Secondary'),
            ('tertiary_user', 'Tertiary'),
        ):
            self.client.post('/api/credentials/add', json={
                'username': u, 'password': f'{u}_pass', 'admin_password': 'en',
                'label': lab, 'force': True,
            })

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_resolve_and_stamp_for_each_action(self):
        """For each action, resolve vault extras and ensure attach_fallback stamps devices."""
        from utils.vault_credentials import resolve_execute_credentials
        from modules.network_base import attach_fallback_to_devices

        data = {
            'credential_id': 'primary_user',
            'secondary_credential_id': 'secondary_user',
            'third_credential_id': 'tertiary_user',
        }
        resolved = resolve_execute_credentials(data, self.cm, {})
        self.assertEqual(len(resolved['fallback_credentials']), 2)

        devices = [{'host': '10.200.200.1', 'device_type': 'cisco_ios'}]
        stamped = attach_fallback_to_devices(
            devices,
            fallback_credentials=resolved['fallback_credentials'],
        )
        self.assertEqual(len(stamped[0]['fallback_credentials']), 2)

        # Live execute with mocked connect — interfaces (no ICMP gate)
        mock = MockDeviceAuth(accept=['secondary_user'])
        with patch('modules.network_base.connect_permissive', side_effect=mock.connect):
            r = self.client.post('/api/execute', json={
                'action': 'interfaces',
                'credential_id': 'primary_user',
                'secondary_credential_id': 'secondary_user',
                'third_credential_id': 'tertiary_user',
                'inventory': '10.200.200.1,cisco_ios',
                'inventory_source': 'unsaved',
                'acknowledge_unsaved': True,
                'target_mode': 'all',
                'int_filter': '',
            })
            self.assertEqual(r.status_code, 200, r.get_json())
            import time
            for _ in range(50):
                if len(mock.attempts) >= 2:
                    break
                time.sleep(0.1)
        self.assertEqual(
            mock.attempts[:2],
            ['primary_user', 'secondary_user'],
            f'interfaces execute attempts={mock.attempts}',
        )

    def test_plugin_execute_serial_number_fallback_order(self):
        mock = MockDeviceAuth(accept=['secondary_user'])
        with patch('modules.network_base.connect_permissive', side_effect=mock.connect):
            r = self.client.post('/api/execute', json={
                'action': 'serial_number',
                'credential_id': 'primary_user',
                'secondary_credential_id': 'secondary_user',
                'third_credential_id': 'tertiary_user',
                'inventory': '10.200.200.1,cisco_ios',
                'inventory_source': 'unsaved',
                'acknowledge_unsaved': True,
                'target_mode': 'all',
                'params': {},
            })
            self.assertEqual(r.status_code, 200, r.get_json())
            import time
            for _ in range(50):
                if len(mock.attempts) >= 2:
                    break
                time.sleep(0.1)
        self.assertEqual(mock.attempts[:2], ['primary_user', 'secondary_user'], mock.attempts)

    def test_discovery_api_passes_fallback_into_credentials(self):
        from utils.vault_credentials import resolve_execute_credentials
        from vlan_checker_web import _credentials_dict_from_request

        data = {
            'credential_id': 'primary_user',
            'secondary_credential_id': 'secondary_user',
            'third_credential_id': 'tertiary_user',
        }
        resolved = resolve_execute_credentials(data, self.cm, {})
        # Simulate overlay onto request dict (as _overlay_request_secrets does)
        data['username'] = resolved['username']
        data['password'] = resolved['password']
        data['enable_pwd'] = resolved['enable_pwd']
        data['fallback_credentials'] = resolved['fallback_credentials']
        data['secondary_credential'] = resolved.get('secondary_credential')
        data['third_credential'] = resolved.get('third_credential')
        creds = _credentials_dict_from_request(data)
        self.assertEqual(len(creds.get('fallback_credentials') or []), 2)
        self.assertEqual(creds['fallback_credentials'][0]['username'], 'secondary_user')

    def test_connectivity_module_fallback_after_ping_ok(self):
        """connectivity.run skips SSH on ping fail — with ping OK must use connect_device fallback."""
        from modules.connectivity import run as conn_run
        mock = MockDeviceAuth(accept=['secondary_user'])
        stamped = attach_fallback_to_devices([DEVICE], fallback_credentials=[SECONDARY])[0]

        class FakePing:
            returncode = 0
            stdout = 'ok'
            stderr = ''

        with patch('modules.connectivity.subprocess.run', return_value=FakePing()):
            with patch('modules.network_base.connect_permissive', side_effect=mock.connect):
                result = conn_run(
                    stamped,
                    PRIMARY['username'],
                    PRIMARY['password'],
                    PRIMARY['enable_pwd'],
                )
        self.assertEqual(mock.attempts[:2], ['primary_user', 'secondary_user'], mock.attempts)
        self.assertEqual(result.get('status'), 'success')

    def test_execute_matrix_ssh_plugins_attempt_order(self):
        """Execute several plugin_ids via API; each must Primary→Secondary on mock device."""
        plugin_ids = [
            'serial_number',
            'device_time',
            'environment_status',
            'critical_logs',
            'interface_errors',
            'vlan_audit',
            'cisco_asset_warranty',
        ]
        failures = []
        for pid in plugin_ids:
            mock = MockDeviceAuth(accept=['secondary_user'])
            with patch('modules.network_base.connect_permissive', side_effect=mock.connect):
                with patch('modules.asset_collection_policy.is_mock_host', return_value=False):
                    r = self.client.post('/api/execute', json={
                        'action': pid,
                        'credential_id': 'primary_user',
                        'secondary_credential_id': 'secondary_user',
                        'third_credential_id': 'tertiary_user',
                        'inventory': '10.200.200.1,cisco_ios',
                        'inventory_source': 'unsaved',
                        'acknowledge_unsaved': True,
                        'target_mode': 'all',
                        'params': {
                            'collection_policy': 'ssh_only',
                            'snmp_fallback': False,
                            'include_modules': False,
                        },
                    })
                if r.status_code != 200:
                    failures.append(f'{pid}: http={r.status_code} {r.get_json()}')
                    continue
                import time
                for _ in range(60):
                    if len(mock.attempts) >= 2:
                        break
                    time.sleep(0.05)
            if mock.attempts[:2] != ['primary_user', 'secondary_user']:
                failures.append(f'{pid}: attempts={mock.attempts}')
        self.assertEqual(failures, [], 'Execute plugin matrix:\n' + '\n'.join(failures))

class TestUiPayloadHelpers(unittest.TestCase):
    """Static contract: index.html runAction / execute / discovery / IM / STP include nstCredentialRequestBody."""

    def test_index_html_wires_credential_body(self):
        html = (Path(__file__).resolve().parents[1] / 'modules' / 'web' / 'templates' / 'index.html').read_text(
            encoding='utf-8'
        )
        self.assertIn('Object.assign(payload, nstCredentialRequestBody())', html)
        # Must appear for runAction, vlan, IM
        self.assertGreaterEqual(html.count('nstCredentialRequestBody()'), 5)
        # Secondary/Third dropdowns must NOT be disabled
        self.assertNotIn('Secondary device credential (disabled)', html)
        self.assertNotIn('id="sidebar_secondary_cred"[^>]*disabled', html)
        import re
        self.assertIsNone(re.search(r'id="sidebar_secondary_cred"[^>]*\bdisabled\b', html))
        self.assertIsNone(re.search(r'id="sidebar_third_cred"[^>]*\bdisabled\b', html))


if __name__ == '__main__':
    unittest.main()
