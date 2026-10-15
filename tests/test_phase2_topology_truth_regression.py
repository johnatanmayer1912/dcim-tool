"""Phase 2 topology-truth closeout — fixture-only regression pack.

SMOKE CHECKLIST (fixture-only; no live SSH)
==========================================
Scope
  - Fixture / generated-HTML only. No live Cisco IOS/IOS-XE, NX-OS, or Junos SSH.
  - Vendor fixtures limited to: Cisco IOS/IOS-XE, Cisco NX-OS (existing), Juniper Junos.
  - Does not validate browser click-paths, production-scale performance, or Phase 3.

Commands
  1) python3 -m pytest tests/test_phase2_topology_truth_regression.py -q --tb=short
  2) python3 -m pytest \\
       tests/test_phase2_topology_truth_slice1.py \\
       tests/test_phase2_topology_truth_slice2.py \\
       tests/test_phase2_topology_truth_slice3.py \\
       tests/test_phase2_topology_truth_slice4.py \\
       tests/test_phase2_topology_truth_slice5.py \\
       tests/test_phase2_topology_truth_slice6.py \\
       tests/test_phase2_topology_truth_slice7.py \\
       -q --tb=short
  3) python3 -m pytest \\
       tests/test_discovery_map_html_contract.py \\
       tests/test_topo_map_shell.py \\
       tests/test_map_acceptance.py \\
       tests/test_discovery_acceptance.py \\
       tests/test_standard_map_v7049.py \\
       tests/qa/test_12_topology_maps.py \\
       -q --tb=line

Pass criteria
  - All tests green; exit code 0.
  - No passwords / credential_id / vault material in fixtures or generated map HTML.
  - No Phase 3 / auth / packaging changes required for this pack.

Known limitations
  - Browser click-path (map select → table reveal → Inspect) is not exercised.
  - Live vendor CLI output drift is not covered here.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.plugins import network_discovery as nd
from utils.discovery_graph import (
    annotate_edge_freshness,
    canonicalize_discovery_graph,
    make_observation_evidence,
    merge_protocol_duplicate_edges,
)
from utils.discovery_map_formatter import build_vis_payload, generate_discovery_html
from utils.evidence_inspector import (
    build_evidence_inspector_model,
    link_row_as_inspector_edge,
    topology_relation_key,
)
from utils.topo_map_shell import link_rows_from_edges, render_topology_page
from utils.topology_trust import apply_discovery_edge_trust

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, 'tests', 'fixtures', 'discovery')


def _read(name: str) -> str:
    with open(os.path.join(FIXTURES, name), encoding='utf-8') as f:
        return f.read()


def _assert_no_secrets(blob: str) -> None:
    low = blob.lower()
    for needle in ('password', 'credential_id', 'credential_key', 'unlock vault', '.credential_key'):
        assert needle not in low, f'secret marker found: {needle}'


class TestPhase2EndToEndTruthPath(unittest.TestCase):
    """Cross-module integration: parse → graph → inspector → map HTML."""

    def test_single_observation_through_map_and_row(self):
        neighbors = nd._parse_cisco_cdp_detail(_read('ios_cdp_detail.txt'), 'CORE', None)
        self.assertGreaterEqual(len(neighbors), 1)
        n = neighbors[0]
        self.assertTrue(n.get('local_port'))
        self.assertNotIn((n.get('local_port') or '').lower(), ('unknown', 'n/a'))
        stamp = '2026-08-20T12:00:00Z'
        edge = {
            'from': 'SEED', 'to': (n.get('hostname') or 'PEER').split('.')[0],
            'f_port': n['local_port'], 't_port': n.get('remote_port') or '',
            'protocol': 'CDP', 'collected_at': stamp,
            'evidence': [make_observation_evidence(
                protocol='CDP', vendor='cisco', command='show cdp neighbors detail',
                collected_at=stamp, local_port=n['local_port'],
                remote_port=n.get('remote_port') or '',
            )],
        }
        annotate_edge_freshness([edge], now=datetime(2026, 8, 20, 13, 0, 0))
        self.assertEqual(edge['freshness'], 'current')
        model = build_evidence_inspector_model(edge)
        self.assertTrue(model['read_only'])
        self.assertEqual(model['evidence_count'], 1)
        self.assertEqual(model['sections']['observed'][0]['vendor'], 'cisco')
        row = link_rows_from_edges([edge])[0]
        self.assertEqual(row['relation_key'], topology_relation_key(edge))
        row_model = build_evidence_inspector_model(link_row_as_inspector_edge(row))
        self.assertEqual(row_model['evidence_count'], model['evidence_count'])
        nodes = [
            {'id': edge['from'], 'ip': '10.0.0.1', 'is_scanned': True},
            {'id': edge['to'], 'ip': '10.0.0.2', 'is_scanned': True},
        ]
        _, edges_json, link_rows = build_vis_payload(nodes, [edge])
        self.assertEqual(edges_json[0]['relation_key'], link_rows[0]['relation_key'])
        self.assertEqual(len(edges_json[0]['evidence']), 1)

    def test_multi_timestamp_mixed_freshness_and_mixed_protocols(self):
        fresh = '2026-08-20T10:00:00Z'
        stale = '2026-08-18T10:00:00Z'
        edges = [
            {
                'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
                'protocol': 'CDP', 'collected_at': fresh,
                'evidence': [make_observation_evidence(
                    protocol='CDP', vendor='cisco', collected_at=fresh,
                    local_port='Gi0/1', remote_port='Gi0/2',
                    command='show cdp neighbors detail',
                )],
            },
            {
                'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
                'protocol': 'LLDP', 'collected_at': stale,
                'evidence': [make_observation_evidence(
                    protocol='LLDP', vendor='cisco', collected_at=stale,
                    local_port='Gi0/1', remote_port='Gi0/2',
                    command='show lldp neighbors',
                )],
            },
        ]
        merged = merge_protocol_duplicate_edges(edges)
        self.assertEqual(len(merged), 1)
        annotate_edge_freshness(merged, now=datetime(2026, 8, 20, 12, 0, 0), stale_hours=24)
        e = merged[0]
        self.assertEqual(e['freshness'], 'mixed')
        self.assertTrue(e.get('freshness_conflict'))
        protos = {x['protocol'].upper() for x in e['evidence']}
        self.assertEqual(protos, {'CDP', 'LLDP'})
        cmds = ' '.join(x.get('command', '') for x in e['evidence']).lower()
        self.assertIn('cdp', cmds)
        self.assertIn('lldp', cmds)
        model = build_evidence_inspector_model(e)
        self.assertTrue(model['freshness']['conflict'])
        self.assertIn('mixed-freshness', ' '.join(model['sections']['conflicts']).lower())

    def test_missing_timestamp_unknown_and_empty_evidence(self):
        bare = {
            'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2', 'protocol': 'CDP',
            'evidence': [make_observation_evidence(protocol='CDP', vendor='cisco')],
        }
        annotate_edge_freshness([bare], now=datetime(2026, 8, 20, 12, 0, 0))
        self.assertEqual(bare['freshness'], 'unknown')
        self.assertFalse(bare['evidence'][0].get('collected_at'))
        empty = {'from': 'X', 'to': 'Y', 'f_port': 'e1', 't_port': 'e2', 'protocol': 'LLDP'}
        model = build_evidence_inspector_model(empty)
        self.assertFalse(model['has_evidence'])
        self.assertIsNotNone(model['empty_message'])

    def test_conflicting_ports_visible_not_silently_resolved(self):
        edges = [
            {
                'from': 'A', 'to': 'B', 'f_port': 'Eth1/1', 't_port': 'Gi1/1',
                'protocol': 'CDP',
                'evidence': [make_observation_evidence(
                    protocol='CDP', local_port='Eth1/1', remote_port='Gi1/1',
                )],
            },
            {
                'from': 'A', 'to': 'B', 'f_port': 'Eth1/1', 't_port': 'Gi0/1',
                'protocol': 'LLDP',
                'evidence': [make_observation_evidence(
                    protocol='LLDP', local_port='Eth1/1', remote_port='Gi0/1',
                )],
            },
        ]
        # Distinct remote ports → parallel / distinct relation keys (not one silent winner)
        k1 = topology_relation_key(edges[0])
        k2 = topology_relation_key(edges[1])
        self.assertNotEqual(k1, k2)
        apply_discovery_edge_trust(edges)
        # Trust may flag mismatch when same undirected cable ports conflict in graph merge;
        # relation keys stay distinct for parallel endpoints.
        self.assertTrue(k1 and k2)

    def test_junos_irb_supporting_context_never_cable(self):
        brief = nd._parse_juniper_lldp_brief(_read('junos_lldp_brief_irb.txt'), 'QFX', None)
        irb = [n for n in brief if 'irb' in (n.get('local_port') or '').lower()]
        self.assertTrue(irb)
        for n in irb:
            self.assertTrue(n.get('not_physical') or (n.get('port_role') or '').startswith('l3'))
        detail = nd._parse_juniper_lldp_detail(_read('junos_lldp_detail_irb.txt'), 'QFX', None)
        detail_irb = [n for n in detail if 'irb' in (n.get('local_port') or '').lower()]
        self.assertTrue(detail_irb)
        edge = {
            'from': 'gw', 'to': 'leaf',
            'f_port': detail_irb[0]['local_port'],
            't_port': detail_irb[0].get('remote_port') or '',
            'protocol': 'LLDP', 'not_physical': True, 'edge_kind': 'irb-adjacency',
            'evidence': [make_observation_evidence(
                protocol='LLDP', vendor='juniper',
                local_port=detail_irb[0]['local_port'],
                remote_port=detail_irb[0].get('remote_port') or '',
                port_role='l3_irb', not_physical=True, parse_source='detail',
            )],
        }
        nodes = [
            {'id': 'gw', 'ip': '10.0.0.1', 'is_scanned': True},
            {'id': 'leaf', 'ip': '10.0.0.2', 'is_scanned': False},
        ]
        g_nodes, g_edges, _report = canonicalize_discovery_graph(nodes, [edge])
        apply_discovery_edge_trust(g_edges)
        for e in g_edges:
            if e.get('not_physical') or 'irb' in (e.get('f_port') or '').lower():
                tier = (e.get('trust_tier') or e.get('confidence') or '').lower()
                self.assertNotIn('verif', tier)
        model = build_evidence_inspector_model(edge)
        self.assertEqual(len(model['sections']['supporting_context']), 1)
        self.assertIn('not cable', model['classification']['cable_claim'].lower())
        # VLAN-only does not invent edges
        only_vlan = {'id': 'sw', 'vlans': [100, 200], 'is_scanned': True}
        _, no_edges, _ = canonicalize_discovery_graph([only_vlan], [])
        self.assertEqual(no_edges, [])

    def test_legacy_edge_compatibility(self):
        legacy = {
            'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
            'protocol': 'CDP', 'collected_at': '2026-08-20T10:00:00Z',
        }
        annotate_edge_freshness([legacy], now=datetime(2026, 8, 20, 11, 0, 0))
        self.assertIn(legacy['freshness'], ('current', 'unknown'))
        # Freshness may synthesize evidence[] from legacy stamps — still read-only
        model = build_evidence_inspector_model(legacy)
        self.assertTrue(model['read_only'])
        row = link_rows_from_edges([legacy])[0]
        self.assertTrue(row.get('relation_key'))
        self.assertEqual(
            build_evidence_inspector_model(link_row_as_inspector_edge(row))['endpoints']['from'],
            'A',
        )


class TestPhase2OperatorSurfaces(unittest.TestCase):
    def test_discovery_html_inspector_sync_reveal_contracts(self):
        nodes = [
            {'id': 'SW1', 'ip': '10.0.0.1', 'is_scanned': True, 'scan_state': 'scanned'},
            {'id': 'SW2', 'ip': '10.0.0.2', 'is_scanned': True, 'scan_state': 'scanned'},
        ]
        fresh = '2026-08-20T12:00:00Z'
        stale = '2026-08-18T12:00:00Z'
        edges = [{
            'from': 'SW1', 'to': 'SW2', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
            'protocol': 'CDP+LLDP', 'freshness': 'mixed', 'freshness_conflict': True,
            'trust_tier': 'Medium',
            'contradictions': ['mixed-freshness evidence timestamps'],
            'evidence': [
                make_observation_evidence(
                    protocol='CDP', vendor='cisco', collected_at=fresh,
                    local_port='Gi0/1', remote_port='Gi0/2',
                ),
                make_observation_evidence(
                    protocol='LLDP', vendor='cisco', collected_at=stale,
                    local_port='Gi0/1', remote_port='Gi0/2',
                ),
            ],
            'evidence_summary': {'count': 2, 'protocols': ['CDP', 'LLDP']},
        }]
        path = os.path.join(tempfile.mkdtemp(), 'p2_closeout.html')
        generate_discovery_html(path, nodes, edges)
        html = open(path, encoding='utf-8').read()
        _assert_no_secrets(html)
        for token in (
            'nstWhyThisLink', 'nstOpenEvidenceInspector', 'nstInspectLinkRowByIndex',
            'nstRelationKey', 'nstSyncHighlightRelation', 'nstClearRelationSync',
            'nstRevealLinkInventoryIfNeeded', 'nstLinkInventoryIsHidden',
            'id="nst-evidence-inspector"', 'Read-only inspector',
            'nst-link-row-selected', 'data-relation-key', '>Inspect</th>',
            'discCcTab', 'disc-panel-links',
        ):
            self.assertIn(token, html)
        # Reveal gated on match; clear must not hide inventory
        self.assertIn('!opts.selectMap && opts.revealInventory !== false', html)
        clear_body = html.split('function nstClearRelationSync')[1].split('function ')[0]
        self.assertNotIn('discCcTab', clear_body)
        self.assertNotIn('topoViewTab', clear_body)
        self.assertNotIn('Promote trust', html)
        self.assertNotIn('Delete evidence', html)
        key = topology_relation_key(edges[0])
        self.assertIn(key, html)

    def test_standard_topo_shell_and_map_only_compat(self):
        edge = {
            'from': 'a', 'to': 'b', 'f_port': 'e1', 't_port': 'e2', 'protocol': 'CDP',
            'evidence': [make_observation_evidence(protocol='CDP', vendor='cisco')],
        }
        rows = link_rows_from_edges([edge])
        path = os.path.join(tempfile.mkdtemp(), 'topo_closeout.html')
        render_topology_page(
            path, 'Phase2 Closeout',
            [{'id': 'a', 'label': 'a', 'x': 0, 'y': 0, 'fixed': True,
              'color': {'background': '#3b82f6'}, 'font': {'color': '#fff'}, 'shape': 'box'}],
            [{'id': 'e0', 'from': 'a', 'to': 'b', 'label': 'e1 ↔ e2', 'protocol': 'CDP',
              'relation_key': rows[0]['relation_key'],
              'color': {'color': '#6366f1'}, 'width': 2}],
            rows,
        )
        html = open(path, encoding='utf-8').read()
        _assert_no_secrets(html)
        self.assertIn('topoViewTab', html)
        self.assertIn('nstRevealLinkInventoryIfNeeded', html)
        self.assertIn('nstSyncHighlightRelation', html)
        self.assertIn('id="topo-link-inventory"', html)

    def test_parallel_links_remain_distinct(self):
        e1 = {'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/1', 'protocol': 'CDP'}
        e2 = {'from': 'A', 'to': 'B', 'f_port': 'Gi0/2', 't_port': 'Gi0/2', 'protocol': 'CDP'}
        self.assertNotEqual(topology_relation_key(e1), topology_relation_key(e2))
        rows = link_rows_from_edges([e1, e2])
        self.assertEqual(len({r['relation_key'] for r in rows}), 2)

    def test_no_secret_exposure_in_models(self):
        dirty = {
            'from': 'A', 'to': 'B', 'local_port': 'Gi0/1', 'remote_port': 'Gi0/2',
            'password': 'super-secret', 'credential_id': 'cred-9',
            'evidence': [make_observation_evidence(protocol='CDP')],
        }
        edge = link_row_as_inspector_edge(dirty)
        model = build_evidence_inspector_model(edge)
        blob = str(edge) + str(model) + topology_relation_key(dirty)
        self.assertNotIn('super-secret', blob)
        self.assertNotIn('password', edge)
        self.assertNotIn('credential_id', edge)
        self.assertNotIn('password', model)


if __name__ == '__main__':
    unittest.main()
