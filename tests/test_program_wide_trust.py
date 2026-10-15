"""Program-wide trust validation — topology, discovery, link rows, scroll CSS."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.discovery_graph import canonicalize_discovery_graph
from utils.topo_map_shell import link_rows_from_edges
from utils.topology_trust import apply_discovery_edge_trust, apply_topology_trust


def _norm(p):
    return p.replace('Ethernet', 'Eth').replace('Port-channel', 'Po')


def _safe(n):
    return (n or '').strip()


class TestProgramWideTrust(unittest.TestCase):
    def test_discovery_edges_get_trust_fields(self):
        edges = [
            {'from': 'A', 'to': 'B', 'local_port': 'Eth1/1', 'remote_port': 'Eth1/1', 'protocol': 'CDP'},
            {'from': 'B', 'to': 'A', 'local_port': 'Eth1/1', 'remote_port': 'Eth1/1', 'protocol': 'CDP'},
        ]
        nodes = [{'id': 'A'}, {'id': 'B'}]
        _, rewired, _ = canonicalize_discovery_graph(nodes, edges)
        self.assertTrue(all('trust_score' in e for e in rewired))
        self.assertTrue(any(e.get('bidirectional') for e in rewired))

    def test_link_rows_carry_trust(self):
        edges = [{
            'from': 'SW1', 'to': 'SW2', 'f_port': 'Eth1/1', 't_port': 'Eth1/2',
            'confidence': 'Verified', 'trust_tier': 'verified', 'trust_score': 95,
            'bidirectional': True, 'type': 'standard',
        }]
        rows = link_rows_from_edges(edges)
        self.assertEqual(rows[0]['confidence'], 'Verified')
        self.assertEqual(rows[0]['trust_tier'], 'verified')
        self.assertTrue(rows[0]['bidirectional'])
        self.assertIn('sources', rows[0])

    def test_topology_trust_on_mapper_edges(self):
        edges = [
            {'from': 'A', 'f_port': 'Eth1/1', 'to': 'B', 't_port': 'Eth1/1', 'discovery': 'cdp'},
            {'from': 'B', 'f_port': 'Eth1/1', 'to': 'A', 't_port': 'Eth1/1', 'discovery': 'cdp'},
        ]
        meta = {
            'A': {'interfaces': {'Eth1/1': {'status': 'up'}}, 'bundles': {}},
            'B': {'interfaces': {'Eth1/1': {'status': 'up'}}, 'bundles': {}},
        }
        summary = apply_topology_trust(edges, meta, _norm, _safe)
        self.assertGreaterEqual(summary['verified_edges'], 1)
        self.assertIn('trust_score', edges[0])


if __name__ == '__main__':
    unittest.main()
