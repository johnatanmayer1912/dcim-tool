"""DOM/optics parsers and both-end apply. Snapshot only."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.optics_dom import (
    apply_optics_to_edges,
    collect_optics,
    optics_alarm,
    parse_ios_transceiver_table,
    parse_junos_optics,
    parse_nxos_transceiver,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'optics')


def _read(name):
    return open(os.path.join(FIX, name), encoding='utf-8').read()


class TestOpticsDom(unittest.TestCase):
    def test_parse_nxos_and_alarm(self):
        parsed = parse_nxos_transceiver(_read('nxos_transceiver_details.txt'))
        self.assertIn('Eth1/49', parsed)
        self.assertAlmostEqual(parsed['Eth1/49']['rx_dbm'], -3.45)
        self.assertTrue(optics_alarm(parsed['Eth1/50']))
        self.assertFalse(optics_alarm(parsed['Eth1/49']))

    def test_parse_ios_table(self):
        parsed = parse_ios_transceiver_table(_read('ios_transceiver.txt'))
        self.assertIn('Gi1/0/1', parsed)
        self.assertTrue(optics_alarm(parsed['Te1/1/1']))

    def test_parse_junos(self):
        parsed = parse_junos_optics(_read('junos_optics.txt'))
        self.assertIn('xe-0/0/0', parsed)
        self.assertTrue(optics_alarm(parsed['xe-0/0/1']))

    def test_collect_skips_unsupported(self):
        out = collect_optics('cisco_nxos', lambda *_a, **_k: '% Invalid command')
        self.assertEqual(out, {})

    def test_apply_both_end_and_skip_overlay(self):
        edges = [
            {
                'from': 'SW1', 'to': 'SW2',
                'f_port': 'Ethernet1/49', 't_port': 'Eth1/50',
            },
            {
                'from': 'SW1', 'to': '10.0.0.5',
                'layer': 'overlay', 'not_physical': True,
                'f_port': 'nve1', 't_port': 'nve1',
            },
        ]
        optics = {
            'SW1': parse_nxos_transceiver(_read('nxos_transceiver_details.txt')),
            'SW2': {'Eth1/50': {'rx_dbm': -20.0, 'tx_dbm': -2.0, 'alarm': True}},
        }
        apply_optics_to_edges(edges, optics)
        self.assertTrue(edges[0]['optics_collected'])
        self.assertIn('dom_alarm_remote', edges[0]['cable_issues'])
        self.assertFalse(edges[1].get('optics_collected'))


if __name__ == '__main__':
    unittest.main()
