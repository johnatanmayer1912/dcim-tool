"""Cable witnesses — description/speed/duplex vs neighbor. Never invents edges."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.cable_witness import (
    apply_cable_witnesses,
    description_matches_neighbor,
    duplex_mismatch,
    speeds_mismatch,
)


class TestCableWitness(unittest.TestCase):
    def test_description_names_neighbor(self):
        self.assertTrue(description_matches_neighbor('uplink to DIST-01 Eth1/1', 'DIST-01', 'Eth1/1'))
        self.assertTrue(description_matches_neighbor('to DIST-01', 'DIST-01', ''))

    def test_leftover_description_is_mismatch(self):
        self.assertFalse(description_matches_neighbor('old-core leftover', 'DIST-01', 'Eth1/1'))

    def test_empty_description_unknown(self):
        self.assertIsNone(description_matches_neighbor('-', 'DIST-01', 'Eth1/1'))
        self.assertIsNone(description_matches_neighbor('', 'DIST-01', 'Eth1/1'))

    def test_speed_mismatch(self):
        self.assertTrue(speeds_mismatch('1000', '10G'))
        self.assertFalse(speeds_mismatch('10G', '10000'))

    def test_duplex_mismatch(self):
        self.assertTrue(duplex_mismatch('full', 'half'))
        self.assertFalse(duplex_mismatch('full-duplex', 'full'))

    def test_apply_stamps_and_skips_overlay(self):
        edges = [
            {
                'from': 'ACCESS-01', 'to': 'DIST-01',
                'f_port': 'Eth1/1', 't_port': 'Eth1/49',
                'f_int_data': {'desc': 'to DIST-01 Eth1/49', 'speed': '10G', 'duplex': 'full'},
                't_int_data': {'desc': 'to ACCESS-01', 'speed': '1G', 'duplex': 'full'},
            },
            {
                'from': 'CORE', 'to': '10.0.0.5',
                'f_port': 'nve1', 't_port': 'nve1',
                'layer': 'overlay', 'not_physical': True,
                'f_int_data': {'desc': 'unused', 'speed': '10G', 'duplex': 'full'},
                't_int_data': {'speed': '1G'},
            },
        ]
        apply_cable_witnesses(edges)
        self.assertEqual(edges[0]['desc_vs_neighbor'], 'match')
        self.assertTrue(edges[0]['speed_mismatch'])
        self.assertIn('speed_mismatch', edges[0]['cable_issues'])
        self.assertNotIn('cable_issues', edges[1])
        self.assertNotEqual(edges[0].get('cable_note', ''), 'Verified cable')


if __name__ == '__main__':
    unittest.main()
