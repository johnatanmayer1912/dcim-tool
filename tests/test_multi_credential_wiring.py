"""Zero-trust / wiring tests: fallback credentials reach every SSH entrypoint."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from modules.network_base import (
    attach_fallback_to_devices,
    connect_device,
    safe_connection,
    safe_connection_from_credentials,
)


ROOT = Path(__file__).resolve().parents[1]


class TestMultiCredentialWiring(unittest.TestCase):
    def test_attach_fallback_stamps_devices(self):
        fb = [{'username': 'sec', 'password': 'p2', 'label': 'Secondary'}]
        out = attach_fallback_to_devices([{'host': '1.1.1.1'}], fallback_credentials=fb)
        self.assertEqual(out[0]['fallback_credentials'], fb)

    def test_connect_device_tries_secondary(self):
        device = {'host': '10.0.0.1', 'device_type': 'cisco_ios'}
        fb = [{'username': 'sec', 'password': 'ok', 'enable_pwd': '', 'label': 'lab2'}]
        calls = []

        def fake_connect(dev, user, pwd, enb, log_func=None):
            calls.append(user)
            if user != 'sec':
                raise Exception('auth failed')
            return MagicMock()

        with patch('modules.network_base.connect_permissive', side_effect=fake_connect):
            conn = connect_device(device, 'primary', 'bad', '', fallback_credentials=fb)
            self.assertIsNotNone(conn)
        self.assertEqual(calls, ['primary', 'sec'])

    def test_safe_connection_from_credentials_passes_fallback(self):
        device = {'host': '10.0.0.1', 'device_type': 'cisco_ios'}
        creds = {
            'username': 'primary',
            'password': 'bad',
            'secret': '',
            'fallback_credentials': [
                {'username': 'sec', 'password': 'ok', 'enable_pwd': '', 'label': 'lab2'},
            ],
        }
        calls = []

        def fake_connect(dev, user, pwd, enb, log_func=None):
            calls.append(user)
            if user != 'sec':
                raise Exception('auth failed')
            m = MagicMock()
            m.disconnect = MagicMock()
            return m

        with patch('modules.network_base.connect_permissive', side_effect=fake_connect):
            with safe_connection_from_credentials(device, creds) as conn:
                self.assertIsNotNone(conn)
        self.assertEqual(calls, ['primary', 'sec'])

    def test_plugins_pass_fallback_kwarg(self):
        """Static check: every modules/plugins safe_connection call includes fallback."""
        plugin_dir = ROOT / 'modules' / 'plugins'
        offenders = []
        for path in plugin_dir.glob('*.py'):
            src = path.read_text(encoding='utf-8')
            if 'safe_connection(' not in src:
                continue
            # Rough: each with safe_connection( ... ) block should mention fallback
            idx = 0
            while True:
                i = src.find('safe_connection(', idx)
                if i < 0:
                    break
                # skip import lines
                line_start = src.rfind('\n', 0, i) + 1
                line = src[line_start:src.find('\n', i)]
                if line.strip().startswith('from ') or line.strip().startswith('import '):
                    idx = i + 1
                    continue
                # find matching close paren (naive depth)
                depth = 0
                j = i + len('safe_connection')
                end = None
                while j < len(src):
                    ch = src[j]
                    if ch == '(':
                        depth += 1
                    elif ch == ')':
                        depth -= 1
                        if depth == 0:
                            end = j
                            break
                    j += 1
                block = src[i:end + 1] if end else src[i:i + 400]
                if 'fallback_credentials' not in block:
                    offenders.append(f'{path.name}:{src[:i].count(chr(10))+1}')
                idx = i + 1
        self.assertEqual(offenders, [], f'Plugins missing fallback_credentials: {offenders}')

    def test_legacy_modules_use_connect_device(self):
        legacy = [
            'topology_mapper.py', 'connectivity.py', 'vlan_mgmt_production.py',
            'mac_trace.py', 'config_backup.py', 'interfaces.py', 'save_config.py',
        ]
        for name in legacy:
            src = (ROOT / 'modules' / name).read_text(encoding='utf-8')
            self.assertIn('connect_device', src, name)
            self.assertNotIn('connect_permissive(', src, name)


if __name__ == '__main__':
    unittest.main()
