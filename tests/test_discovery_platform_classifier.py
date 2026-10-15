"""Platform classifier tests (v7.0.1 BUG-0007)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.discovery_graph import classify_os_family


class TestPlatformClassifier(unittest.TestCase):
    def test_nexus_not_junos_substring_trap(self):
        self.assertFalse('ex' in 'nexus' and classify_os_family('Nexus9000') == 'juniper_junos')
        self.assertEqual(classify_os_family('Nexus9000'), 'cisco_nxos')
        self.assertEqual(classify_os_family('N9K-C93180YC'), 'cisco_nxos')
        self.assertEqual(classify_os_family('Cisco Nexus 7000'), 'cisco_nxos')

    def test_juniper_models(self):
        self.assertEqual(classify_os_family('EX4300-48T'), 'juniper_junos')
        self.assertEqual(classify_os_family('QFX5100'), 'juniper_junos')

    def test_ios(self):
        self.assertEqual(classify_os_family('C9300-48P'), 'cisco_ios')

    def test_show_version_nxos(self):
        ver = (
            'Cisco Nexus Operating System (NX-OS) Software\n'
            'Device name: N9K-CORE-01\n'
        )
        self.assertEqual(classify_os_family(ver_output=ver), 'cisco_nxos')

    def test_show_version_junos(self):
        ver = 'Hostname: edge01\nJuniper Networks, Inc. ex4300 internet router, kernel JUNOS'
        self.assertEqual(classify_os_family(ver_output=ver), 'juniper_junos')

    def test_iosxe_and_unknown_not_invented(self):
        self.assertEqual(classify_os_family('C8000V'), 'cisco_xe')
        self.assertEqual(classify_os_family(ver_output='Cisco IOS XE Software, Version 17.09'), 'cisco_xe')
        self.assertEqual(classify_os_family('toaster-appliance'), 'unknown')
        self.assertEqual(classify_os_family(dtype_hint='cisco_ios'), 'cisco_ios')

    def test_bare_cisco_not_ios_fallback(self):
        self.assertEqual(classify_os_family('Cisco Systems'), 'unknown')
        self.assertEqual(classify_os_family('Cisco'), 'unknown')


if __name__ == '__main__':
    unittest.main()
