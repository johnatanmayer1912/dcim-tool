"""Phase 5 slice 2 — incomplete observations and placeholder quarantine.

Fixture-only. No live SSH. No Arista. No telemetry-to-topology mutation.
"""
from __future__ import annotations

import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.plugins import network_discovery as nd
from utils.discovery_graph import canonicalize_discovery_graph, normalize_discovery_edges
from utils.evidence_inspector import (
    build_evidence_inspector_model,
    build_incomplete_observation_model,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'discovery')


def _read(name: str) -> str:
    with open(os.path.join(FIX, name), encoding='utf-8') as f:
        return f.read()


def _no_placeholders(rows):
    for n in rows:
        for key in ('hostname', 'local_port', 'remote_port'):
            val = (n.get(key) or '')
            self_msg = (key, val, n)
            assert val.lower() not in ('unknown', 'n/a', 'n\\a'), self_msg


class TestTruncatedCdpIncomplete(unittest.TestCase):
    def test_truncated_cdp_emits_incomplete_not_edge(self):
        ns = nd._parse_cisco_cdp_detail(
            _read('phase5_ios_cdp_detail_truncated_no_interface.txt'), 'EDGE', None,
        )
        self.assertEqual(len(ns), 1)
        obs = ns[0]
        self.assertTrue(obs['incomplete'])
        self.assertFalse(obs['edge_eligible'])
        self.assertEqual(obs['local_port'], '')
        self.assertEqual(obs['remote_port'], '')
        self.assertIn('TRUNC-PEER', obs['hostname'])
        self.assertIn('local_port', obs['evidence_gaps'])
        _no_placeholders(ns)

        fin = nd._finalize_neighbor(dict(obs))
        self.assertTrue(fin['incomplete'])
        self.assertFalse(fin['edge_eligible'])

        # Graph must not invent an edge from incomplete observation
        edges = normalize_discovery_edges([{
            'from': 'EDGE',
            'to': fin['hostname'],
            'f_port': fin['local_port'],
            't_port': fin['remote_port'],
            'protocol': 'CDP',
            'incomplete': True,
            'edge_eligible': False,
        }])
        # Incomplete with empty local port is partial at most; crawl refuses edges without fp
        self.assertEqual(edges[0].get('f_port'), '')
        nodes = [{'id': 'EDGE'}, {'id': fin['hostname']}]
        _n, e2, _r = canonicalize_discovery_graph(
            copy.deepcopy(nodes),
            copy.deepcopy([{
                'from': 'EDGE',
                'to': fin['hostname'],
                'f_port': '',
                't_port': '',
                'protocol': 'cdp',
            }]),
        )
        for e in e2:
            self.assertNotEqual((e.get('f_port') or '').lower(), 'unknown')
            self.assertNotEqual((e.get('t_port') or '').lower(), 'unknown')

    def test_truncated_cdp_with_garbage_still_incomplete(self):
        ns = nd._parse_cisco_cdp_detail(
            _read('phase5_ios_cdp_detail_truncated_garbage.txt'), 'EDGE', None,
        )
        self.assertEqual(len(ns), 1)
        self.assertTrue(ns[0]['incomplete'])
        _no_placeholders(ns)

    def test_valid_cdp_baseline_unchanged(self):
        ns = nd._parse_cisco_cdp_detail(_read('ios_cdp_detail.txt'), 'EDGE', None)
        complete = [n for n in ns if not n.get('incomplete')]
        self.assertGreaterEqual(len(complete), 1)
        dist = next(n for n in complete if 'DIST-SW01' in n['hostname'])
        fin = nd._finalize_neighbor(dict(dist))
        self.assertIsNotNone(fin)
        self.assertNotEqual(fin.get('edge_eligible'), False)
        self.assertTrue(fin['local_port'])
        self.assertTrue(fin['remote_port'])


class TestTruncatedLldpIncomplete(unittest.TestCase):
    def test_lldp_detail_missing_local_is_incomplete(self):
        ns = nd._parse_cisco_lldp_detail(
            _read('phase5_ios_lldp_detail_truncated_no_local.txt'), 'EDGE', None,
        )
        self.assertEqual(len(ns), 1)
        obs = ns[0]
        self.assertTrue(obs['incomplete'])
        self.assertEqual(obs['local_port'], '')
        # Port id without Local Intf: keep resolved remote only when description/id is usable
        self.assertNotEqual(obs.get('remote_port'), 'unknown')
        self.assertIn('TRUNC-LLDP-PEER', obs['hostname'])
        _no_placeholders(ns)


class TestJunosAlternativeNoUnknown(unittest.TestCase):
    def test_alternative_valid_no_unknown_placeholders(self):
        ns = nd._parse_juniper_lldp_alternative(
            _read('phase5_junos_lldp_alternative_valid.txt'), 'QFX', None,
        )
        self.assertGreaterEqual(len(ns), 1)
        _no_placeholders(ns)
        ok = next(n for n in ns if n.get('hostname') == 'ALT-PEER-OK')
        self.assertEqual(ok['local_port'], 'ge-0/0/1')
        self.assertEqual(ok['remote_port'], 'ge-0/0/2')
        self.assertFalse(ok.get('incomplete'))

    def test_alternative_missing_system_name_is_incomplete(self):
        ns = nd._parse_juniper_lldp_alternative(
            _read('phase5_junos_lldp_alternative_partial.txt'), 'QFX', None,
        )
        _no_placeholders(ns)
        incompletes = [n for n in ns if n.get('incomplete')]
        completes = [n for n in ns if not n.get('incomplete')]
        self.assertGreaterEqual(len(incompletes), 1)
        self.assertTrue(any(n.get('local_port') == 'ge-0/0/9' for n in incompletes))
        self.assertTrue(any(n.get('hostname') == 'ALT-PEER-01' for n in completes))
        for n in incompletes:
            self.assertNotEqual(n.get('hostname'), 'unknown')
            self.assertNotEqual(n.get('remote_port'), 'unknown')
            self.assertEqual(n.get('edge_eligible'), False)

    def test_alternative_regression_format_no_unknown(self):
        output = """
ge-0/0/0
  System Name: JUNOS-01
  Management address: 10.1.1.1
xe-0/0/0
  System Name: JUNOS-02
"""
        ns = nd._parse_juniper_lldp_alternative(output, 'test_host', None)
        self.assertGreaterEqual(len(ns), 1)
        _no_placeholders(ns)
        hosts = {n['hostname'] for n in ns}
        self.assertIn('JUNOS-01', hosts)
        self.assertNotIn('unknown', hosts)

    def test_table_never_defaults_port_to_unknown(self):
        output = """
Local Interface  Parent Interface  Chassis Id        Port info      System Name
ge-0/0/0         -                 00:1A:2B:3C:4D:5E  -               JUNOS-ONLY
"""
        ns = nd._parse_juniper_lldp_table(output, 'test_host', None)
        _no_placeholders(ns)
        self.assertGreaterEqual(len(ns), 1)
        for n in ns:
            self.assertNotEqual(n.get('remote_port'), 'unknown')
            if n.get('hostname') == 'JUNOS-ONLY':
                self.assertEqual(n.get('remote_port'), '')


class TestInspectorIncompleteSemantics(unittest.TestCase):
    def test_incomplete_model_uses_unobserved_not_unknown_ports(self):
        ns = nd._parse_cisco_cdp_detail(
            _read('phase5_ios_cdp_detail_truncated_no_interface.txt'), 'EDGE', None,
        )
        fin = nd._finalize_neighbor(dict(ns[0]))
        model = build_incomplete_observation_model(fin)
        self.assertTrue(model['incomplete'])
        self.assertFalse(model['edge_eligible'])
        self.assertEqual(model['ports']['local_port'], '(unobserved)')
        self.assertEqual(model['ports']['remote_port'], '(unobserved)')
        self.assertEqual(model['ports']['local_port_raw'], '')
        self.assertEqual(model['ports']['remote_port_raw'], '')
        self.assertIn('incomplete', model['classification']['cable_claim'].lower())
        self.assertNotIn('unknown', model['ports']['local_port'].lower())

    def test_edge_inspector_still_read_only_for_partial(self):
        fin = nd._finalize_neighbor({
            'hostname': 'PEER',
            'local_port': 'Gi1/0/1',
            'remote_port': '',
            'protocol': 'CDP',
        })
        edge = {
            'from': 'EDGE', 'to': 'PEER',
            'f_port': fin['local_port'], 't_port': '',
            'protocol': 'CDP', 'one_sided': True, 'partial': True,
            'evidence_gaps': ['remote_port'],
        }
        model = build_evidence_inspector_model(edge)
        self.assertTrue(model['read_only'])
        # Graph empty port must not become invented interface name in raw edge
        self.assertEqual(edge['t_port'], '')


class TestTelemetryBoundary(unittest.TestCase):
    def test_incomplete_not_normalized_as_valid_neighbor_edge(self):
        from utils.telemetry import normalize_observation, load_fixture_json
        path = os.path.join(ROOT, 'tests', 'fixtures', 'telemetry', 'iosxe_interface_counters.json')
        obs = normalize_observation(load_fixture_json(path))
        self.assertNotIn('incomplete', obs.get('evidence_gaps') or [])
        ns = nd._parse_cisco_cdp_detail(
            _read('phase5_ios_cdp_detail_truncated_no_interface.txt'), 'EDGE', None,
        )
        # Discovery incomplete remains distinct from telemetry observation
        self.assertTrue(ns[0].get('incomplete'))
        self.assertNotEqual(ns[0].get('observation_kind'), obs.get('quality'))


if __name__ == '__main__':
    unittest.main()
