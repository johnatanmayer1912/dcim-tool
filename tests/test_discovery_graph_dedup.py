"""Discovery graph deduplication tests (v7.0.1)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.discovery_graph import (
    canonicalize_discovery_graph,
    merge_nodes,
    rewire_edges,
    validate_graph,
)


class TestDiscoveryGraphDedup(unittest.TestCase):
    def test_triangle_three_nodes(self):
        nodes = [
            {'id': 'A', 'ip': '10.0.0.1', 'depth': 0, 'is_scanned': True},
            {'id': 'B', 'ip': '10.0.0.2', 'depth': 1, 'is_scanned': False},
            {'id': 'b', 'ip': '10.0.0.2', 'depth': 1, 'is_scanned': False},
            {'id': 'C', 'ip': '10.0.0.3', 'depth': 2, 'is_scanned': False},
        ]
        edges = [
            {'from': 'A', 'to': 'B', 'f_port': 'Eth1/1', 't_port': 'Gi1/1'},
            {'from': 'A', 'to': 'b', 'f_port': 'Eth1/2', 't_port': 'Gi1/2'},
            {'from': 'B', 'to': 'C', 'f_port': 'Gi1/48', 't_port': 'Gi0/1'},
        ]
        merged, rewired, report = canonicalize_discovery_graph(nodes, edges)
        self.assertEqual(len(merged), 3)
        ids = {n['id'] for n in merged}
        self.assertEqual(len(ids), 3)
        self.assertIn('10.0.0.2', {n.get('ip') for n in merged})

    def test_ip_to_hostname_merge(self):
        nodes = [
            {'id': '10.0.0.1', 'ip': '10.0.0.1', 'depth': 0, 'is_scanned': False},
            {
                'id': 'CORE-NXOS-01', 'ip': '10.0.0.1', 'depth': 0,
                'is_scanned': True, 'device_type': 'cisco_nxos',
            },
        ]
        merged, alias_map = merge_nodes(nodes)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]['id'], 'core-nxos-01')

    def test_rewire_edges(self):
        alias = {'b': 'B', '10.0.0.2': 'B'}
        edges = [{'from': 'A', 'to': 'b', 'f_port': 'e1'}]
        out = rewire_edges(edges, alias)
        self.assertEqual(out[0]['to'], 'B')

    def test_parallel_links_same_pair_different_ports(self):
        nodes = [
            {'id': 'A', 'ip': '10.0.0.1', 'depth': 0, 'is_scanned': True},
            {'id': 'B', 'ip': '10.0.0.2', 'depth': 1, 'is_scanned': True},
        ]
        edges = [
            {'from': 'A', 'to': 'B', 'f_port': 'Eth1/1', 't_port': 'Gi1/1', 'protocol': 'CDP'},
            {'from': 'A', 'to': 'B', 'f_port': 'Eth1/2', 't_port': 'Gi1/2', 'protocol': 'LLDP'},
        ]
        _merged, rewired, _report = canonicalize_discovery_graph(nodes, edges)
        self.assertEqual(len(rewired), 2)

    def test_cdp_lldp_same_cable_merges_provenance(self):
        nodes = [
            {'id': 'A', 'ip': '10.0.0.1', 'depth': 0, 'is_scanned': True},
            {'id': 'B', 'ip': '10.0.0.2', 'depth': 1, 'is_scanned': True},
        ]
        edges = [
            {'from': 'A', 'to': 'B', 'f_port': 'Eth1/1', 't_port': 'Gi1/1', 'protocol': 'CDP'},
            {'from': 'B', 'to': 'A', 'f_port': 'Gi1/1', 't_port': 'Eth1/1', 'protocol': 'LLDP'},
        ]
        _merged, rewired, _report = canonicalize_discovery_graph(nodes, edges)
        self.assertEqual(len(rewired), 1)
        src = {s.lower() for s in rewired[0].get('sources') or []}
        self.assertIn('cdp', src)
        self.assertIn('lldp', src)
        self.assertTrue(rewired[0].get('provenance_merged'))
        self.assertNotEqual(rewired[0].get('edge_type'), 'physical-link')

    def test_validate_graph_case_insensitive_orphans(self):
        nodes = [{'id': 'core-sw01', 'ip': '10.0.0.1'}]
        edges = [{'from': 'CORE-SW01', 'to': 'core-sw01', 'f_port': 'e1', 't_port': 'e2'}]
        report = validate_graph(nodes, edges)
        self.assertEqual(report['orphan_edges'], 0)
        self.assertTrue(report['ok'])

    def test_contradictory_remote_ports_mismatch(self):
        nodes = [
            {'id': 'A', 'ip': '10.0.0.1', 'depth': 0, 'is_scanned': True},
            {'id': 'B', 'ip': '10.0.0.2', 'depth': 1, 'is_scanned': True},
        ]
        edges = [
            {'from': 'A', 'to': 'B', 'f_port': 'Eth1/1', 't_port': 'Gi1/1', 'protocol': 'CDP'},
            {'from': 'A', 'to': 'B', 'f_port': 'Eth1/1', 't_port': 'Gi1/2', 'protocol': 'LLDP'},
        ]
        _merged, rewired, _report = canonicalize_discovery_graph(nodes, edges)
        self.assertEqual(len(rewired), 2)
        for e in rewired:
            self.assertEqual(e.get('confidence'), 'Mismatch')
            self.assertEqual(e.get('trust_tier'), 'mismatch')
            self.assertTrue(e.get('contradictions'))

    def test_duplicate_hostnames_identity_conflict(self):
        nodes = [
            {'id': 'EDGE-01', 'ip': '10.0.0.1', 'serial': 'SN-A', 'is_scanned': True},
            {'id': 'EDGE-01', 'ip': '10.0.0.9', 'serial': 'SN-B', 'is_scanned': True},
        ]
        merged, _alias = merge_nodes(nodes)
        self.assertEqual(len(merged), 2)
        ids = {n['id'] for n in merged}
        self.assertEqual(len(ids), 2)
        report = validate_graph(merged, [])
        self.assertTrue(report['duplicate_hostnames'] or any(n.get('identity_conflict') for n in merged))
        self.assertTrue(any(n.get('identity_conflict') for n in merged))

    def test_duplicate_chassis_ids_conflict_not_silent_merge(self):
        """T-L2-13: same chassis_id, different host/IP → two nodes + chassis_conflict."""
        nodes = [
            {'id': 'LEAF-A', 'ip': '10.0.0.1', 'chassis_id': 'aabb.ccdd.eeff', 'serial': 'SN-1', 'is_scanned': True},
            {'id': 'LEAF-B', 'ip': '10.0.0.2', 'chassis_id': 'aabb.ccdd.eeff', 'serial': 'SN-2', 'is_scanned': True},
        ]
        merged, _alias = merge_nodes(nodes)
        self.assertEqual(len(merged), 2)
        report = validate_graph(merged, [])
        self.assertTrue(report.get('duplicate_chassis'))
        self.assertTrue(any(n.get('chassis_conflict') for n in merged))
        self.assertTrue(any(n.get('identity_conflict') for n in merged))

    def test_lag_member_down_does_not_delete_bundle(self):
        nodes = [
            {'id': 'A', 'ip': '10.0.0.1', 'is_scanned': True},
            {'id': 'B', 'ip': '10.0.0.2', 'is_scanned': True},
        ]
        edges = [
            {
                'from': 'A', 'to': 'B', 'f_port': 'Eth1/1', 't_port': 'Eth1/1',
                'protocol': 'CDP', 'oper_status': 'down',
            },
            {
                'from': 'A', 'to': 'B', 'f_port': 'Po1', 't_port': 'Po1',
                'protocol': 'CDP', 'oper_status': 'up',
            },
        ]
        _merged, rewired, _report = canonicalize_discovery_graph(nodes, edges)
        self.assertEqual(len(rewired), 2)
        kinds = {e.get('bundle_kind') for e in rewired}
        self.assertIn('bundle', kinds)
        self.assertIn('member', kinds)
        member = next(e for e in rewired if e.get('bundle_kind') == 'member')
        bundle = next(e for e in rewired if e.get('bundle_kind') == 'bundle')
        self.assertTrue(member.get('degraded'))
        self.assertFalse(bundle.get('degraded'))

    def test_junos_ae_bundle_naming(self):
        nodes = [
            {'id': 'qfx1', 'ip': '10.0.0.1', 'is_scanned': True},
            {'id': 'qfx2', 'ip': '10.0.0.2', 'is_scanned': True},
        ]
        edges = [
            {'from': 'qfx1', 'to': 'qfx2', 'f_port': 'ae0', 't_port': 'ae0', 'protocol': 'LLDP'},
        ]
        _m, rewired, _r = canonicalize_discovery_graph(nodes, edges)
        self.assertEqual(rewired[0].get('bundle_kind'), 'bundle')
        self.assertIn('heuristic', (rewired[0].get('lag_note') or '').lower())

    def test_large_graph_canonicalize_bounded(self):
        import time
        nodes = [
            {'id': f'sw{i}', 'ip': f'10.0.{i // 250}.{i % 250}', 'is_scanned': True}
            for i in range(1, 201)
        ]
        edges = []
        for i in range(1, 201):
            nxt = i + 1 if i < 200 else 1
            edges.append({
                'from': f'sw{i}', 'to': f'sw{nxt}',
                'f_port': 'Eth1/1', 't_port': 'Eth1/2', 'protocol': 'LLDP',
            })
        t0 = time.perf_counter()
        merged, rewired, report = canonicalize_discovery_graph(nodes, edges)
        elapsed = time.perf_counter() - t0
        self.assertLess(elapsed, 2.0)
        self.assertEqual(len(merged), 200)
        self.assertEqual(len(rewired), 200)
        self.assertTrue(report['ok'] or report.get('edge_count') == 200)


if __name__ == '__main__':
    unittest.main()
