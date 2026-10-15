"""Topology trust validation — bidirectional CDP, vPC cross-check, edge scoring."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.topology_trust import (
    apply_discovery_edge_trust,
    apply_topology_trust,
    build_directed_link_index,
    cross_check_vpc_members,
    is_bidirectional,
    score_edge_trust,
    trust_tier_from_score,
    validate_vpc_domain_completeness,
)


def _norm(p):
    return p.replace('Ethernet', 'Eth').replace('Port-channel', 'Po')


def _safe(n):
    return (n or '').strip()


class TestTopologyTrust(unittest.TestCase):
    def test_bidirectional_detection(self):
        edges = [
            {'from': 'A', 'f_port': 'Eth1/1', 'to': 'B', 't_port': 'Eth1/1', 'discovery': 'cdp'},
            {'from': 'B', 'f_port': 'Eth1/1', 'to': 'A', 't_port': 'Eth1/1', 'discovery': 'cdp'},
        ]
        idx = build_directed_link_index(edges, _safe, _norm)
        self.assertTrue(is_bidirectional('A', 'Eth1/1', 'B', 'Eth1/1', idx, _norm))

    def test_discovery_bidi_score_matches_high_tier(self):
        edges = [
            {'from': 'A', 'to': 'B', 'local_port': 'Eth1/1', 'remote_port': 'Eth1/1', 'protocol': 'LLDP'},
            {'from': 'B', 'to': 'A', 'local_port': 'Eth1/1', 'remote_port': 'Eth1/1', 'protocol': 'LLDP'},
        ]
        apply_discovery_edge_trust(edges)
        self.assertTrue(edges[0]['bidirectional'])
        self.assertEqual(edges[0]['confidence'], 'High')
        self.assertEqual(edges[0]['trust_tier'], 'high')
        self.assertGreaterEqual(edges[0]['trust_score'], 80)
        self.assertIn('lldp', [s.lower() for s in edges[0]['sources']])

    def test_discovery_one_sided_not_verified(self):
        edges = [
            {'from': 'A', 'to': 'B', 'local_port': 'Eth1/1', 'remote_port': 'Eth1/1', 'protocol': 'CDP'},
        ]
        apply_discovery_edge_trust(edges)
        self.assertTrue(edges[0]['one_sided'])
        self.assertNotEqual(edges[0]['confidence'], 'Verified')
        self.assertLess(edges[0]['trust_score'], 80)
        self.assertIn(edges[0]['trust_tier'], ('medium', 'low', 'inferred'))
        self.assertTrue(edges[0]['spoof_risk'])
        self.assertIn('spoofable', edges[0].get('trust_note', '').lower())

    def test_unidirectional_not_bidirectional(self):
        edges = [
            {'from': 'A', 'f_port': 'Eth1/1', 'to': 'B', 't_port': 'Eth1/1', 'discovery': 'cdp'},
        ]
        idx = build_directed_link_index(edges, _safe, _norm)
        self.assertFalse(is_bidirectional('A', 'Eth1/1', 'B', 'Eth1/1', idx, _norm))

    def test_verified_edge_score(self):
        edges = [
            {'from': 'N9K-A', 'f_port': 'Eth1/1', 'to': 'N9K-B', 't_port': 'Eth1/1', 'discovery': 'cdp'},
            {'from': 'N9K-B', 'f_port': 'Eth1/1', 'to': 'N9K-A', 't_port': 'Eth1/1', 'discovery': 'cdp'},
        ]
        meta = {
            'N9K-A': {'interfaces': {'Eth1/1': {'status': 'up'}}, 'bundles': {}},
            'N9K-B': {'interfaces': {'Eth1/1': {'status': 'up'}}, 'bundles': {}},
        }
        idx = build_directed_link_index(edges, _safe, _norm)
        trust = score_edge_trust(edges[0], idx, meta, _norm, _safe)
        self.assertEqual(trust['confidence'], 'Verified')
        self.assertGreaterEqual(trust['trust_score'], 90)

    def test_vpc_member_cross_check_alerts(self):
        meta = {
            'vpc_structured': {
                'domain_id': '1',
                'peer_link_po': 'Po1',
                'vpc_table': [{'vpc_id': '10', 'po': 'Po10', 'status': 'up', 'consistency': 'success'}],
            },
            'port_channel_detail': {
                'Po1': {'members': [{'intf': 'Eth1/49'}], 'protocol': 'LACP'},
                'Po10': {'members': [{'intf': 'Eth1/1'}], 'protocol': 'LACP'},
            },
            'bundles': {'Eth1/1': 'Po10', 'Eth1/49': 'Po1'},
            'lacp_neighbors': {'Po10': [{'local_port': 'Eth1/1'}]},
            'vpc_domain_id': '1',
        }
        cdp_map = {}  # no CDP witness
        chains, alerts = cross_check_vpc_members('N9K-A', meta, cdp_map, {'N9K-B'}, _norm)
        self.assertTrue(any('no CDP/LACP' in a or 'unidirectional' in a for a in alerts) or len(chains) >= 1)
        self.assertGreaterEqual(len(chains), 1)

    def test_domain_completeness_unscanned_peer(self):
        vpc_domains = {'1': ['N9K-A', 'N9K-B']}
        meta = {
            'N9K-A': {
                'vpc_structured': {'domain_id': '1', 'vpc_table': [{'vpc_id': '10', 'po': 'Po10'}]},
                'vpc_details': {'Po10': {'type': 'vpc', 'vpc_id': '10'}},
            },
        }
        dc = validate_vpc_domain_completeness(vpc_domains, meta)
        self.assertIn('N9K-B', dc['1']['unscanned_members'])
        self.assertFalse(dc['1']['fully_scanned'])

    def test_apply_topology_trust_mutates_metadata(self):
        edges = [
            {'from': 'A', 'f_port': 'Eth1/1', 'to': 'B', 't_port': 'Eth1/1', 'discovery': 'cdp'},
            {'from': 'B', 'f_port': 'Eth1/1', 'to': 'A', 't_port': 'Eth1/1', 'discovery': 'cdp'},
        ]
        meta = {
            'A': {'interfaces': {'Eth1/1': {'status': 'up'}}, 'bundles': {}, 'vpc_domain_id': ''},
            'B': {'interfaces': {'Eth1/1': {'status': 'up'}}, 'bundles': {}, 'vpc_domain_id': ''},
        }
        summary = apply_topology_trust(edges, meta, _norm, _safe)
        self.assertEqual(summary['bidirectional_edges'], 2)
        self.assertIn('Eth1/1', meta['A']['cdp_validation_map'])
        self.assertTrue(meta['A']['cdp_validation_map']['Eth1/1']['bidirectional'])

    def test_trust_tier_from_score(self):
        self.assertEqual(trust_tier_from_score(96), 'verified')
        self.assertEqual(trust_tier_from_score(50), 'low')
        self.assertEqual(trust_tier_from_score(5), 'untrusted')


    def test_discovery_edge_trust(self):
        edges = [
            {'from': 'A', 'to': 'B', 'local_port': 'Eth1/1', 'remote_port': 'Eth1/1'},
            {'from': 'B', 'to': 'A', 'local_port': 'Eth1/1', 'remote_port': 'Eth1/1'},
        ]
        summary = apply_discovery_edge_trust(edges)
        self.assertEqual(summary['bidirectional_edges'], 2)
        self.assertTrue(edges[0]['bidirectional'])
        self.assertEqual(edges[0]['confidence'], 'High')


if __name__ == '__main__':
    unittest.main()
