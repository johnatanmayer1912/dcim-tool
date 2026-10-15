"""Swiss Tools topology — parallel link dedup regression (v7.0.31)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.adapters import _topology_edge_link_key


class TestTopologyParallelEdges(unittest.TestCase):
    def _norm(self, n):
        return (str(n or '')
                .replace('GigabitEthernet', 'Gi')
                .replace('Ethernet', 'Eth')
                .replace('FastEthernet', 'Fa')
                .strip())

    def test_distinct_ports_keep_separate_keys(self):
        k1 = _topology_edge_link_key('A', 'Eth1/1', 'B', 'Gi1/1', self._norm)
        k2 = _topology_edge_link_key('A', 'Eth1/2', 'B', 'Gi1/2', self._norm)
        self.assertNotEqual(k1, k2)

    def test_same_link_same_key(self):
        k1 = _topology_edge_link_key('A', 'Ethernet1/1', 'B', 'GigabitEthernet1/1', self._norm)
        k2 = _topology_edge_link_key('A', 'Eth1/1', 'B', 'Gi1/1', self._norm)
        self.assertEqual(k1, k2)

    def test_unknown_ports_use_raw_labels(self):
        k1 = _topology_edge_link_key('A', 'Eth1/1', 'B', 'unknown', self._norm)
        k2 = _topology_edge_link_key('A', 'Eth1/1', 'B', 'Gi1/2', self._norm)
        self.assertNotEqual(k1, k2)


if __name__ == '__main__':
    unittest.main()
