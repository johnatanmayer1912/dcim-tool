"""Issues list from edge witnesses. Does not invent links."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.cable_witness import apply_cable_witnesses
from utils.link_issues import build_link_issues


class TestLinkIssues(unittest.TestCase):
    def test_one_sided_and_desc_and_lacp(self):
        edges = [
            {
                'from': 'A', 'to': 'B', 'f_port': 'Eth1/1', 't_port': 'Eth1/2',
                'one_sided': True,
                'f_int_data': {'desc': 'leftover-core', 'status': 'up'},
                't_int_data': {'status': 'down'},
            },
            {
                'from': 'A', 'to': 'B', 'f_port': 'Eth1/3', 't_port': 'Eth1/4',
                'lacp_collected': True, 'lacp_oper': 'down',
                'f_int_data': {'desc': 'to B Eth1/4'},
            },
        ]
        apply_cable_witnesses(edges)
        rows = build_link_issues(edges)
        kinds = {r['kind'] for r in rows}
        self.assertIn('one_sided', kinds)
        self.assertIn('description_vs_neighbor', kinds)
        self.assertIn('updown_mismatch', kinds)
        self.assertIn('lacp_member_down', kinds)
        self.assertEqual(len(rows), len({(r['kind'], r['from'], r['f_port'], r['to'], r['t_port']) for r in rows}))


if __name__ == '__main__':
    unittest.main()
