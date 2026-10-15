"""LACP oper-state from CLI — never delete a bundle when a member is down."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.lacp_oper import apply_lacp_to_edges, parse_port_channel_summary

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'lacp', 'nxos_port_channel_summary.txt')


class TestLacpOper(unittest.TestCase):
    def test_member_down_keeps_bundle_edge(self):
        summary = parse_port_channel_summary(open(FIX, encoding='utf-8').read())
        self.assertIn('Po1', summary)
        flags = {m['port']: m['up'] for m in summary['Po1']['members']}
        self.assertTrue(flags.get('Eth1/1'))
        self.assertFalse(flags.get('Eth1/2'))

        edges = [
            {'from': 'A', 'to': 'B', 'f_port': 'Eth1/1', 't_port': 'Eth2/1', 'bundle_kind': 'member'},
            {'from': 'A', 'to': 'B', 'f_port': 'Eth1/2', 't_port': 'Eth2/2', 'bundle_kind': 'member'},
            {'from': 'A', 'to': 'B', 'f_port': 'Po1', 't_port': 'Po1', 'bundle_kind': 'bundle'},
        ]
        apply_lacp_to_edges(edges, None, summary)
        bundle = next(e for e in edges if e.get('bundle_kind') == 'bundle')
        down = next(e for e in edges if e.get('f_port') == 'Eth1/2')
        self.assertEqual(len(edges), 3)
        self.assertTrue(down.get('degraded'))
        self.assertEqual(down.get('lacp_oper'), 'down')
        self.assertTrue(down.get('lacp_collected'))
        self.assertTrue(bundle.get('lacp_collected'))
        self.assertIn('LACP', bundle.get('lag_note') or '')
        self.assertNotIn('heuristic', (bundle.get('lag_note') or '').lower())

    def test_ifname_only_stays_heuristic_without_cli(self):
        edges = [
            {'from': 'qfx1', 'to': 'qfx2', 'f_port': 'ae0', 't_port': 'ae0',
             'bundle_kind': 'bundle', 'lag_note': 'LAG/AE ifName heuristic'},
        ]
        apply_lacp_to_edges(edges, None, None)
        self.assertNotEqual(edges[0].get('lacp_collected'), True)
        self.assertIn('heuristic', (edges[0].get('lag_note') or '').lower())


if __name__ == '__main__':
    unittest.main()
