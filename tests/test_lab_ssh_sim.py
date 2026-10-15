"""Lab SSH/SNMP simulators — handler unit tests (no live TCP required)."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lab.ssh_sim.handler import DEFAULT_PORT_MAP, LAB_DEVICES, device_for_port, handle_command


class TestLabSshSimHandler(unittest.TestCase):
    def test_port_device_map_fabric(self):
        self.assertEqual(device_for_port(2201), 'ios_access')
        self.assertEqual(device_for_port(2202), 'nxos_leaf1')
        self.assertEqual(device_for_port(2203), 'nxos_leaf2')
        self.assertIsNone(device_for_port(9999))

    def test_ios_show_version(self):
        out = handle_command('ios_access', 'show version')
        self.assertIn('C9300', out)

    def test_nxos_show_inventory(self):
        out = handle_command('nxos_leaf1', 'show inventory')
        self.assertIn('N9K-C93180YC-EX', out)

    def test_terminal_prep_is_noop(self):
        self.assertEqual(handle_command('ios_access', 'terminal width 511'), '')
        self.assertEqual(handle_command('nxos_leaf1', 'terminal length 0'), '')

    def test_unknown_command_returns_invalid(self):
        out = handle_command('ios_access', 'show foo')
        self.assertIn('Invalid input', out)

    def test_all_lab_devices_defined(self):
        for port, key in DEFAULT_PORT_MAP.items():
            self.assertIn(key, LAB_DEVICES)


if __name__ == '__main__':
    unittest.main()
