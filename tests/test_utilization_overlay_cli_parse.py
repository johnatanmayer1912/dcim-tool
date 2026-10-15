"""CLI parser fixtures for live utilization (IOS / NX-OS / Junos)."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.cisco_iface import normalize_cisco_iface
from utils.juniper_iface import split_junos_unit
from utils.utilization_overlay.cli_parse import (
    command_for_device_type,
    parse_interface_counters,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI = os.path.join(ROOT, 'tests', 'fixtures', 'utilization', 'cli')


def _load(name: str) -> str:
    return open(os.path.join(CLI, name), encoding='utf-8').read()


class TestCliParsers(unittest.TestCase):
    def test_commands_are_narrow(self):
        self.assertEqual(command_for_device_type('cisco_ios'), 'show interfaces')
        self.assertEqual(command_for_device_type('cisco_xe'), 'show interfaces')
        self.assertEqual(command_for_device_type('cisco_nxos'), 'show interface')
        self.assertEqual(command_for_device_type('juniper_junos'), 'show interfaces statistics')

    def test_cisco_ios_fixture(self):
        rows = parse_interface_counters(_load('cisco_ios_show_interfaces.txt'), 'cisco_ios')
        by_name = {r['if_name_raw']: r for r in rows}
        self.assertIn('GigabitEthernet1/0/1', by_name)
        gi = by_name['GigabitEthernet1/0/1']
        self.assertEqual(gi['in_octets'], 1000000)
        self.assertEqual(gi['out_octets'], 2000000)
        self.assertEqual(gi['if_speed_bps'], 1_000_000_000)
        self.assertEqual(gi['if_name_normalized'], normalize_cisco_iface('GigabitEthernet1/0/1'))
        self.assertIn('Vlan100', by_name)

    def test_cisco_nxos_fixture(self):
        rows = parse_interface_counters(_load('cisco_nxos_show_interface.txt'), 'cisco_nxos')
        by_name = {r['if_name_raw']: r for r in rows}
        self.assertIn('Ethernet1/1', by_name)
        eth = by_name['Ethernet1/1']
        self.assertEqual(eth['in_octets'], 8000000000)
        self.assertEqual(eth['out_octets'], 1000000000)
        self.assertEqual(eth['in_octets_64'], 8000000000)
        self.assertEqual(eth['if_name_normalized'], normalize_cisco_iface('Ethernet1/1'))

    def test_juniper_fixture(self):
        rows = parse_interface_counters(
            _load('juniper_show_interfaces_statistics.txt'), 'juniper_junos',
        )
        by_name = {r['if_name_raw']: r for r in rows}
        self.assertIn('ge-0/0/0', by_name)
        ge = by_name['ge-0/0/0']
        self.assertEqual(ge['in_octets'], 3000000)
        self.assertEqual(ge['out_octets'], 4000000)
        self.assertEqual(ge['if_speed_bps'], 1_000_000_000)
        phys, _ = split_junos_unit('ge-0/0/0.0')
        self.assertEqual(ge['if_name_normalized'], phys)
        self.assertNotIn('irb.100', by_name)


if __name__ == '__main__':
    unittest.main()
