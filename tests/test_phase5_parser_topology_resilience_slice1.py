"""Phase 5 slice 1 — fixture-only parser/topology resilience baseline.

Documents current behavior for malformed and drifting discovery CLI.
No live SSH. No Arista. No telemetry-to-topology mutation.
"""
from __future__ import annotations

import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.plugins import network_discovery as nd
from utils.discovery_graph import (
    annotate_logical_l3_edges,
    canonicalize_discovery_graph,
    make_observation_evidence,
    normalize_discovery_edges,
)
from utils.evidence_inspector import build_evidence_inspector_model
from utils.topology_trust import apply_discovery_edge_trust

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'discovery')


def _read(name: str) -> str:
    with open(os.path.join(FIX, name), encoding='utf-8') as f:
        return f.read()


def _no_placeholder_ports(neighs):
    for n in neighs:
        for key in ('local_port', 'remote_port'):
            val = (n.get(key) or '')
            assert val.lower() not in ('unknown', 'n/a', 'n\\a'), (key, val)


def _edge_from_neigh(local_host, n, protocol=None):
    proto = protocol or n.get('protocol') or 'LLDP'
    return {
        'from': local_host,
        'to': n.get('hostname') or '',
        'f_port': n.get('local_port') or '',
        't_port': n.get('remote_port') or '',
        'protocol': proto,
        'sources': [proto],
        'not_physical': bool(n.get('not_physical')),
        'port_role': n.get('port_role') or '',
        'partial': bool(n.get('partial')),
        'evidence_gaps': list(n.get('evidence_gaps') or []),
        'evidence': [make_observation_evidence(
            protocol=proto,
            local_port=n.get('local_port') or '',
            remote_port=n.get('remote_port') or '',
            parse_source=n.get('parse_source') or '',
            raw_fragment=n.get('raw_fragment') or '',
            not_physical=bool(n.get('not_physical')),
            port_role=n.get('port_role') or '',
        )],
    }


class TestNoCrashAndEmpty(unittest.TestCase):
    def test_empty_outputs_are_safe(self):
        empty = _read('phase5_empty_show_output.txt')
        self.assertEqual(nd._parse_cisco_cdp_detail('', 'H', None), [])
        self.assertEqual(nd._parse_cisco_cdp_brief('', 'H', None), [])
        self.assertEqual(nd._parse_cisco_lldp_brief('', 'H', None), [])
        self.assertEqual(nd._parse_cisco_lldp_detail('', 'H', None), [])
        self.assertEqual(nd._parse_juniper_lldp_brief('', 'H', None), [])
        self.assertEqual(nd._parse_juniper_lldp_detail('', 'H', None), [])
        self.assertEqual(nd._parse_cisco_cdp_detail(empty, 'H', None), [])
        self.assertEqual(nd._parse_cisco_lldp_brief(empty, 'H', None), [])
        self.assertEqual(nd._parse_juniper_lldp_brief(empty, 'H', None), [])

    def test_comment_only_output_does_not_crash(self):
        comment = _read('phase5_empty_show_output.txt')
        parsers = (
            nd._parse_cisco_cdp_detail,
            nd._parse_cisco_cdp_brief,
            nd._parse_cisco_lldp_brief,
            nd._parse_cisco_lldp_detail,
            nd._parse_juniper_lldp_brief,
            nd._parse_juniper_lldp_detail,
        )
        for parse in parsers:
            ns = parse(comment, 'H', None)
            self.assertIsInstance(ns, list)
            _no_placeholder_ports(ns)

    def test_parsers_do_not_crash_on_garbage_only(self):
        junk = '@@@ totally not neighbor output ###\nfoo bar baz\n'
        self.assertIsInstance(nd._parse_cisco_cdp_detail(junk, 'H', None), list)
        self.assertIsInstance(nd._parse_cisco_lldp_brief(junk, 'H', None), list)
        self.assertIsInstance(nd._parse_juniper_lldp_brief(junk, 'H', None), list)
        _no_placeholder_ports(nd._parse_cisco_cdp_detail(junk, 'H', None))


class TestIosIosXeResilience(unittest.TestCase):
    def test_valid_baseline_ios_cdp_detail(self):
        ns = nd._parse_cisco_cdp_detail(_read('ios_cdp_detail.txt'), 'EDGE-XE-01', None)
        self.assertGreaterEqual(len(ns), 1)
        _no_placeholder_ports(ns)
        hosts = [n['hostname'] for n in ns]
        self.assertTrue(any('DIST-SW01' in h for h in hosts))

    def test_missing_remote_port_preserved_not_fabricated(self):
        ns = nd._parse_cisco_cdp_detail(
            _read('phase5_ios_cdp_detail_missing_remote_port.txt'), 'EDGE-XE-01', None,
        )
        self.assertEqual(len(ns), 1)
        fin = nd._finalize_neighbor(dict(ns[0]))
        self.assertIsNotNone(fin)
        self.assertEqual(fin['remote_port'], '')
        self.assertTrue(fin.get('partial'))
        self.assertIn('remote_port', fin.get('evidence_gaps') or [])
        self.assertNotIn('n/a', fin['remote_port'])
        self.assertNotEqual(fin['remote_port'], 'unknown')
        edges = normalize_discovery_edges([_edge_from_neigh('EDGE-XE-01', fin, 'CDP')])
        self.assertEqual(edges[0]['t_port'], '')
        self.assertTrue(edges[0].get('partial'))

    def test_truncated_cdp_no_interface_does_not_invent_ports(self):
        ns = nd._parse_cisco_cdp_detail(
            _read('phase5_ios_cdp_detail_truncated_no_interface.txt'), 'EDGE-XE-01', None,
        )
        # Slice 2 contract: explicit incomplete observation, not silent [] / fabricated ports
        self.assertEqual(len(ns), 1)
        obs = ns[0]
        self.assertTrue(obs.get('incomplete'))
        self.assertEqual(obs.get('edge_eligible'), False)
        self.assertEqual(obs.get('local_port'), '')
        self.assertEqual(obs.get('remote_port'), '')
        self.assertIn('local_port', obs.get('evidence_gaps') or [])
        _no_placeholder_ports(ns)
        fin = nd._finalize_neighbor(dict(obs))
        self.assertIsNotNone(fin)
        self.assertTrue(fin.get('incomplete'))
        self.assertEqual(fin.get('edge_eligible'), False)
        self.assertEqual(fin.get('local_port'), '')
        self.assertEqual(fin.get('remote_port'), '')

    def test_garbage_injection_preserves_valid_cdp_neighbor(self):
        base = nd._parse_cisco_cdp_detail(_read('ios_cdp_detail.txt'), 'EDGE-XE-01', None)
        mixed = nd._parse_cisco_cdp_detail(
            _read('phase5_ios_cdp_detail_garbage_injected.txt'), 'EDGE-XE-01', None,
        )
        self.assertGreaterEqual(len(mixed), 1)
        _no_placeholder_ports(mixed)
        base_sw = [n for n in base if 'DIST-SW01' in (n.get('hostname') or '')]
        mix_sw = [n for n in mixed if 'DIST-SW01' in (n.get('hostname') or '')]
        self.assertEqual(len(base_sw), 1)
        self.assertEqual(len(mix_sw), 1)
        self.assertEqual(mix_sw[0]['local_port'], base_sw[0]['local_port'])
        self.assertEqual(mix_sw[0]['remote_port'], base_sw[0]['remote_port'])

    def test_duplicate_cdp_blocks_deterministic(self):
        a = nd._parse_cisco_cdp_detail(
            _read('phase5_ios_cdp_detail_duplicate_blocks.txt'), 'EDGE-XE-01', None,
        )
        b = nd._parse_cisco_cdp_detail(
            _read('phase5_ios_cdp_detail_duplicate_blocks.txt'), 'EDGE-XE-01', None,
        )
        self.assertEqual(
            [(n.get('hostname'), n.get('local_port'), n.get('remote_port')) for n in a],
            [(n.get('hostname'), n.get('local_port'), n.get('remote_port')) for n in b],
        )
        self.assertEqual(len(a), 2)

    def test_iosxe_lldp_brief_garbage_and_missing_port_id(self):
        base = nd._parse_cisco_lldp_brief(_read('iosxe_lldp_brief.txt'), 'EDGE-XE-01', None)
        mixed = nd._parse_cisco_lldp_brief(
            _read('phase5_iosxe_lldp_brief_garbage_injected.txt'), 'EDGE-XE-01', None,
        )
        self.assertEqual(len(base), len(mixed))
        _no_placeholder_ports(mixed)
        miss = nd._parse_cisco_lldp_brief(
            _read('phase5_iosxe_lldp_brief_missing_port_id.txt'), 'EDGE-XE-01', None,
        )
        _no_placeholder_ports(miss)
        self.assertEqual(len(miss), 1)
        fin = nd._finalize_neighbor(dict(miss[0]))
        self.assertIsNotNone(fin)
        self.assertEqual(fin['hostname'], 'DIST-C9300')
        self.assertEqual(fin['local_port'], 'Gi1/0/1')
        self.assertEqual(fin['remote_port'], '')
        self.assertTrue(fin.get('partial'))
        self.assertNotEqual(fin['remote_port'], '120')


class TestNxosResilience(unittest.TestCase):
    def test_valid_nxos_cdp_baseline(self):
        ns = nd._parse_cisco_cdp_detail(_read('nxos_cdp_detail.txt'), 'LEAF-NX-01', None)
        self.assertGreaterEqual(len(ns), 1)
        _no_placeholder_ports(ns)

    def test_cdp_disabled_is_empty_and_explainable(self):
        ns = nd._parse_cisco_cdp_detail(_read('nxos_cdp_disabled.txt'), 'LEAF-NX-01', None)
        self.assertEqual(ns, [])
        # LLDP-only remaining is a separate parse — not promoted to CDP cable
        lldp = nd._parse_cisco_lldp_brief(_read('nxos_lldp_brief.txt'), 'LEAF-NX-01', None)
        for n in lldp:
            self.assertNotEqual((n.get('protocol') or '').upper(), 'CDP')

    def test_nxos_garbage_preserves_spine(self):
        mixed = nd._parse_cisco_cdp_detail(
            _read('phase5_nxos_cdp_detail_garbage_injected.txt'), 'LEAF-NX-01', None,
        )
        self.assertTrue(any('SPINE-NXOS-05' in (n.get('hostname') or '') for n in mixed))
        _no_placeholder_ports(mixed)

    def test_chassis_only_does_not_use_n_a_placeholder(self):
        ns = nd._parse_cisco_lldp_detail(_read('nxos_lldp_chassis_only.txt'), 'LEAF-NX-01', None)
        _no_placeholder_ports(ns)
        for n in ns:
            self.assertNotEqual(n.get('remote_port'), 'n/a')
            self.assertNotEqual(n.get('remote_port'), 'unknown')


class TestJunosResilience(unittest.TestCase):
    def test_valid_junos_brief_baseline(self):
        ns = nd._parse_juniper_lldp_brief(_read('junos_lldp_brief.txt'), 'QFX-01', None)
        self.assertGreaterEqual(len(ns), 1)
        _no_placeholder_ports(ns)

    def test_irb_only_not_physical_cable(self):
        ns = nd._parse_juniper_lldp_brief(_read('junos_lldp_brief_irb.txt'), 'QFX-01', None)
        irb = [n for n in ns if (n.get('local_port') or '').startswith('irb.')]
        self.assertGreaterEqual(len(irb), 1)
        n = nd._finalize_neighbor(dict(irb[0]))
        self.assertTrue(n.get('not_physical'))
        self.assertIn('physical_link', n.get('evidence_gaps') or [])
        edges = annotate_logical_l3_edges(
            normalize_discovery_edges([_edge_from_neigh('QFX-01', n, 'LLDP')])
        )
        apply_discovery_edge_trust(edges)
        self.assertTrue(edges[0].get('not_physical') or edges[0].get('edge_kind'))
        # Must not look like a verified physical cable
        self.assertNotEqual((edges[0].get('trust_tier') or '').lower(), 'verified')

    def test_junos_garbage_preserves_physical_peers(self):
        base = nd._parse_juniper_lldp_brief(_read('junos_lldp_brief.txt'), 'QFX-01', None)
        mixed = nd._parse_juniper_lldp_brief(
            _read('phase5_junos_lldp_brief_garbage.txt'), 'QFX-01', None,
        )
        base_hosts = sorted(n['hostname'] for n in base)
        mix_hosts = sorted(n['hostname'] for n in mixed)
        self.assertEqual(base_hosts, mix_hosts)
        _no_placeholder_ports(mixed)

    def test_incomplete_junos_neighbor_no_invented_port(self):
        ns = nd._parse_juniper_lldp_brief(
            _read('phase5_junos_lldp_brief_incomplete_neighbor.txt'), 'QFX-01', None,
        )
        _no_placeholder_ports(ns)
        self.assertEqual(len(ns), 1)
        fin = nd._finalize_neighbor(dict(ns[0]))
        self.assertIsNotNone(fin)
        self.assertEqual(fin['hostname'], 'INCOMPLETE-PEER')
        self.assertEqual(fin['remote_port'], '')
        self.assertTrue(fin.get('partial'))
        self.assertIn('remote_port', fin.get('evidence_gaps') or [])
        self.assertNotIn(fin.get('remote_port'), ('unknown', 'n/a'))


class TestOneSidedNotCableAndInspector(unittest.TestCase):
    def test_one_sided_cdp_not_promoted_to_verified_cable(self):
        ns = nd._parse_cisco_cdp_detail(_read('ios_cdp_detail.txt'), 'EDGE-XE-01', None)
        sw = next(n for n in ns if 'DIST-SW01' in n['hostname'])
        fin = nd._finalize_neighbor(dict(sw))
        edges = normalize_discovery_edges([_edge_from_neigh('EDGE-XE-01', fin, 'CDP')])
        apply_discovery_edge_trust(edges)
        e = edges[0]
        tier = (e.get('trust_tier') or e.get('confidence') or '').lower()
        self.assertNotIn(tier, ('verified', 'high'))
        self.assertTrue(e.get('one_sided') or e.get('spoof_risk') or tier in ('medium', 'low', ''))

    def test_inspector_explains_unresolved_remote_port(self):
        ns = nd._parse_cisco_cdp_detail(
            _read('phase5_ios_cdp_detail_missing_remote_port.txt'), 'EDGE-XE-01', None,
        )
        fin = nd._finalize_neighbor(dict(ns[0]))
        edges = normalize_discovery_edges([_edge_from_neigh('EDGE-XE-01', fin, 'CDP')])
        apply_discovery_edge_trust(edges)
        model = build_evidence_inspector_model(edges[0])
        self.assertTrue(model.get('read_only'))
        claim = (model.get('classification') or {}).get('cable_claim') or ''
        self.assertTrue(
            'one-sided' in claim.lower()
            or 'inspect evidence' in claim.lower()
            or 'not a verified cable' in claim.lower()
        )
        # Graph port remains empty; inspector may display the word unknown for empty
        self.assertEqual(edges[0]['t_port'], '')
        self.assertNotEqual(edges[0]['t_port'], 'n/a')

    def test_canonicalize_does_not_invent_ports_on_partial(self):
        nodes = [{'id': 'A'}, {'id': 'B'}]
        edges = [{
            'from': 'A', 'to': 'B',
            'f_port': 'Gi1/0/1', 't_port': '',
            'protocol': 'lldp',
        }]
        _n, e2, _meta = canonicalize_discovery_graph(
            copy.deepcopy(nodes), copy.deepcopy(edges),
        )
        for e in e2:
            tp = (e.get('t_port') or '')
            self.assertNotIn(tp.lower(), ('n/a',))
            self.assertNotEqual(tp.lower(), 'unknown')


class TestTelemetryAndAristaBoundary(unittest.TestCase):
    def test_no_telemetry_topology_mutation(self):
        from utils.telemetry import normalize_observation, load_fixture_json
        tel_fix = os.path.join(ROOT, 'tests', 'fixtures', 'telemetry', 'iosxe_interface_counters.json')
        obs = normalize_observation(load_fixture_json(tel_fix))
        self.assertNotIn('trust_tier', obs)
        self.assertNotIn('f_port', obs)
        nodes = [{'id': 'A'}, {'id': 'B'}]
        edges = [{
            'from': 'A', 'to': 'B',
            'f_port': 'Gi1/0/1', 't_port': 'Gi1/0/2', 'protocol': 'lldp',
        }]
        before = canonicalize_discovery_graph(copy.deepcopy(nodes), copy.deepcopy(edges))
        _ = obs  # telemetry unused for graph
        after = canonicalize_discovery_graph(copy.deepcopy(nodes), copy.deepcopy(edges))
        self.assertEqual(before, after)

    def test_no_arista_fixtures_added(self):
        names = os.listdir(FIX)
        self.assertFalse(any('arista' in n.lower() or 'eos' in n.lower() for n in names))


if __name__ == '__main__':
    unittest.main()
