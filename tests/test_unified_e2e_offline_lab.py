"""Offline 8-vendor demo lab invariants (fixture-only, not live)."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.discovery_map_formatter import build_vis_payload
from utils.utilization_overlay.discovery_host import bind_overlay_to_discovery
from utils.utilization_overlay.join import (
    bind_overlay_to_standard_l2,
    is_paint_eligible_l2_edge,
    topology_fingerprint,
)
from utils.link_issues import build_link_issues

import runpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAB = os.path.join(ROOT, 'tests', 'fixtures', 'demo_lab', 'unified_e2e_lab.json')
GEN = os.path.join(ROOT, 'scripts', 'generate_unified_e2e_demo.py')


def _lab():
    return json.load(open(LAB, encoding='utf-8'))


def _genmod():
    return runpy.run_path(GEN)


class TestUnifiedE2EOfflineLab(unittest.TestCase):
    def test_vendor_and_counts(self):
        lab = _lab()
        types = [n['device_type'] for n in lab['nodes']]
        self.assertEqual(len(lab['nodes']), 8)
        self.assertEqual(types.count('cisco_nxos'), 3)
        self.assertEqual(types.count('cisco_ios'), 2)
        self.assertEqual(types.count('cisco_xe'), 1)
        self.assertEqual(types.count('juniper_junos'), 2)
        self.assertEqual(len(lab['l2_edges']), 7)
        self.assertEqual(sum(1 for e in lab['non_cable_edges'] if e.get('protocol') == 'EVPN'), 1)

    def test_evpn_and_incomplete_are_not_cables(self):
        lab = _lab()
        evpn = [e for e in lab['non_cable_edges'] if e.get('protocol') == 'EVPN'][0]
        self.assertTrue(evpn['not_physical'])
        self.assertEqual(evpn['layer'], 'overlay')
        self.assertFalse(is_paint_eligible_l2_edge(evpn))
        inc = 0
        for n in lab['nodes']:
            for o in n.get('incomplete_observations') or []:
                self.assertFalse(o.get('edge_eligible'))
                inc += 1
        self.assertEqual(inc, 1)

    def test_overlay_paints_only_existing_l2_cable(self):
        g = _genmod()
        lab = _lab()
        nodes = g['_std_nodes'](lab)
        edges = g['_std_edges'](lab, include_non_cable=False)
        before = topology_fingerprint(edges)
        bound = bind_overlay_to_standard_l2(nodes, edges, g['_overlay_doc'](lab))
        self.assertTrue(bound.ok)
        self.assertEqual(sorted(bound.bindings.keys()), ['e0'])
        self.assertEqual(edges[0]['trust_tier'], 'high')
        self.assertEqual(topology_fingerprint(edges), before)
        self.assertEqual(len(edges), 7)

    def test_discovery_does_not_paint_evpn(self):
        g = _genmod()
        lab = _lab()
        edges = list(lab['l2_edges']) + list(lab['non_cable_edges'])
        vis_n, vis_e, _ = build_vis_payload(lab['nodes'], edges)
        self.assertEqual(len(vis_e), 9)
        evpn = [e for e in vis_e if e.get('protocol') == 'EVPN'][0]
        stp = [e for e in vis_e if (e.get('protocol') or '').upper() == 'STP'][0]
        self.assertFalse(is_paint_eligible_l2_edge(stp))
        self.assertEqual(evpn['color']['color'], '#a855f7')
        bound = bind_overlay_to_discovery(vis_n, vis_e, g['_overlay_doc'](lab))
        self.assertTrue(bound.ok)
        self.assertNotIn(evpn['id'], bound.bindings)
        self.assertEqual(evpn['trust_tier'], 'inferred')

    def test_one_sided_listed_in_diagnostics(self):
        lab = _lab()
        issues = build_link_issues(lab['l2_edges'])
        kinds = {i['kind'] for i in issues}
        self.assertIn('one_sided', kinds)
        self.assertTrue(any('not a verified cable' in i['summary'] for i in issues))


if __name__ == '__main__':
    unittest.main()
