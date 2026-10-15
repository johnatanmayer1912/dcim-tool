"""Path reconstruct follows MAC hits + L2 edges only. Never invents a hop."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.path_trace import next_hop_from_edges, reconstruct_path


class TestPathTrace(unittest.TestCase):
    def test_two_hops_from_edges_no_invented_third(self):
        edges = [
            {'from': 'CORE', 'to': 'DIST', 'f_port': 'Eth1/1', 't_port': 'Eth1/49', 'protocol': 'cdp'},
            {'from': 'DIST', 'to': 'ACCESS', 'f_port': 'Eth1/2', 't_port': 'Gi1/0/24', 'protocol': 'lldp'},
        ]
        hits = [
            {'hostname': 'CORE', 'port': 'Eth1/1', 'vlan': '20', 'found': True,
             'command': 'show mac address-table', 'evidence': 'aa:bb on Eth1/1'},
            {'hostname': 'DIST', 'port': 'Eth1/2', 'vlan': '20', 'found': True,
             'command': 'show mac address-table', 'evidence': 'aa:bb on Eth1/2'},
            {'hostname': 'ACCESS', 'port': 'Gi1/0/1', 'vlan': '20', 'found': True,
             'command': 'show mac address-table', 'evidence': 'aa:bb on Gi1/0/1'},
        ]
        path = reconstruct_path(hits, edges, 'aabb.cccc.dddd')
        hosts = [h['hostname'] for h in path['hops']]
        self.assertEqual(hosts, ['CORE', 'DIST', 'ACCESS'])
        self.assertIsNone(path['hops'][-1]['next_host'])
        self.assertEqual(path['unlinked_hits'], [])
        self.assertIn('not a forwarding path', path['path_note'].lower())

    def test_missing_edge_stops_no_third_hop(self):
        edges = [
            {'from': 'CORE', 'to': 'DIST', 'f_port': 'Eth1/1', 't_port': 'Eth1/49', 'protocol': 'cdp'},
        ]
        hits = [
            {'hostname': 'CORE', 'port': 'Eth1/1', 'found': True},
            {'hostname': 'DIST', 'port': 'Eth1/2', 'found': True},
            {'hostname': 'ACCESS', 'port': 'Gi1/0/1', 'found': True},
        ]
        path = reconstruct_path(hits, edges, 'aa:bb:cc:dd:ee:ff')
        hosts = [h['hostname'] for h in path['hops']]
        self.assertEqual(hosts, ['CORE', 'DIST'])
        self.assertNotIn('ACCESS', hosts)
        self.assertEqual(path['unlinked_hits'], [{'hostname': 'ACCESS', 'port': 'Gi1/0/1'}])
        self.assertFalse(path['complete'])

    def test_overlay_edge_is_not_a_hop(self):
        edges = [
            {'from': 'CORE', 'to': '10.0.0.5', 'f_port': 'nve1', 't_port': 'nve1',
             'layer': 'overlay', 'not_physical': True},
        ]
        self.assertIsNone(next_hop_from_edges('CORE', 'nve1', edges))

    def test_no_hits(self):
        path = reconstruct_path([], [], 'aa:bb')
        self.assertEqual(path['hops'], [])
        self.assertFalse(path['complete'])


if __name__ == '__main__':
    unittest.main()
