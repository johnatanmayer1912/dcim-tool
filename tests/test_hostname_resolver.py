"""Hostname resolver contract tests (v7.0.0)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.network_base import (
    _hostname_from_ver_output,
    resolve_device_hostname,
    resolve_hostname_from_prompt,
    safe_node_name,
)

FIX = os.path.join(os.path.dirname(__file__), 'fixtures', 'discovery', 'nxos_show_version.txt')


class TestHostnameResolver(unittest.TestCase):
    def test_nxos_device_name_from_version(self):
        with open(FIX, encoding='utf-8') as f:
            ver = f.read()
        self.assertEqual(_hostname_from_ver_output(ver, 'cisco_nxos'), 'n9k-core-01')

    def test_banner_rejected(self):
        blob = 'cisco nexus operating system (nx-os) software tac support http://www.cisco.com'
        self.assertIsNone(safe_node_name(blob))

    def test_prompt_path(self):
        class C:
            def find_prompt(self):
                return 'N9K-CORE-01#'
        self.assertEqual(resolve_hostname_from_prompt(C(), '10.0.0.1'), 'n9k-core-01')

    def test_auth_prompt_rejected_not_used_as_hostname(self):
        class PasswordPrompt:
            def find_prompt(self):
                return 'Password:'
        class UsernamePrompt:
            def find_prompt(self):
                return 'Username:'
        self.assertEqual(resolve_hostname_from_prompt(PasswordPrompt(), '10.0.0.50'), '10.0.0.50')
        self.assertEqual(resolve_hostname_from_prompt(UsernamePrompt(), '192.168.1.18'), '192.168.1.18')

    def test_version_preferred_over_bad_prompt(self):
        class C:
            def find_prompt(self):
                return 'login:'
        ver = 'switchname : DIST-SW-18\n'
        self.assertEqual(
            resolve_device_hostname(C(), ver, '10.0.0.18', 'cisco_nxos'),
            'dist-sw-18',
        )


if __name__ == '__main__':
    unittest.main()
