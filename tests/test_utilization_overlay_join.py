"""Join safety and topology invariants for the Standard L2 utilization overlay."""
from __future__ import annotations

import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.utilization_overlay.join import (
    bind_replay_to_standard_l2,
    is_paint_eligible_l2_edge,
    join_observations_to_l2,
    l2_cable_key,
    topology_fingerprint,
)
from utils.utilization_overlay.model import load_replay_overlay
from utils.utilization_overlay.paint import NO_SAMPLE_COLOR, NO_SAMPLE_DASH, stroke_for_paint

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, 'tests', 'fixtures', 'utilization', 'replay_standard_l2.json')


def _nodes():
    return [
        {'id': 'CORE-01', 'role': 'core'},
        {'id': 'DIST-N1', 'role': 'distribution'},
        {'id': 'ACC-01', 'role': 'access'},
    ]


def _l2_edges():
    return [
        {
            'id': 'e0',
            'from': 'CORE-01',
            'to': 'DIST-N1',
            'f_port': 'Te1/0/1',
            't_port': 'Te1/1/1',
            'type': 'standard',
            'trust_tier': 'high',
            'confidence': 'High',
            'edge_data': {
                'from': 'CORE-01',
                'to': 'DIST-N1',
                'f_port': 'Te1/0/1',
                't_port': 'Te1/1/1',
                'type': 'standard',
                'trust_tier': 'high',
                'confidence': 'High',
            },
            'color': '#607d8b',
            'width': 2,
        },
        {
            'id': 'e1',
            'from': 'DIST-N1',
            'to': 'ACC-01',
            'f_port': 'Gi1/0/48',
            't_port': 'Gi1/0/1',
            'type': 'standard',
            'trust_tier': 'high',
            'confidence': 'High',
            'one_sided': False,
            'color': '#607d8b',
            'width': 2,
        },
    ]


class TestJoinSafety(unittest.TestCase):
    def test_exact_existing_cable_match_paints_correct_edge(self):
        edges = _l2_edges()
        bound = bind_replay_to_standard_l2(_nodes(), edges, FIXTURE)
        self.assertTrue(bound.ok)
        self.assertIn('e0', bound.bindings)
        self.assertNotIn('e1', bound.bindings)
        self.assertEqual(bound.bindings['e0']['paint_state'], 'hot')
        self.assertEqual(bound.bindings['e0']['cable_key'], l2_cable_key(edges[0]))
        self.assertNotEqual(bound.bindings['e0']['cable_key'], 'e0')

    def test_unknown_cable_stays_unmapped_fail_closed(self):
        doc = load_replay_overlay(FIXTURE)
        doc['paints'][0]['cable_key'] = 'core-01|te1/0/9|dist-n1|te1/1/9|l2'
        bound = bind_replay_to_standard_l2(_nodes(), _l2_edges(), doc)
        self.assertFalse(bound.ok)
        self.assertEqual(bound.bindings, {})
        self.assertIn('not in bound L2 set', bound.error)

    def test_vis_ids_are_not_durable_join_keys(self):
        key = l2_cable_key(_l2_edges()[0])
        self.assertNotRegex(key, r'^e\d+$')
        self.assertIn('|l2', key)
        bound = bind_replay_to_standard_l2(_nodes(), _l2_edges(), FIXTURE)
        for ck in [v['cable_key'] for v in bound.bindings.values()]:
            self.assertFalse(ck.startswith('e') and ck[1:].isdigit())

    def test_ambiguous_mapping_stays_unmapped(self):
        edges = _l2_edges() + [
            {
                'id': 'e2',
                'from': 'CORE-01',
                'to': 'ACC-01',
                'f_port': 'Te1/0/1',
                't_port': 'Gi1/0/24',
                'type': 'standard',
            }
        ]
        obs = [{
            'device_id': 'CORE-01',
            'if_name_raw': 'Te1/0/1',
            'in_pct': 40,
            'out_pct': 40,
            'pct': 40,
            'if_speed_bps': 10000000000,
        }]
        result = join_observations_to_l2(obs, _nodes(), edges)
        self.assertEqual(result['paints'], [])
        self.assertEqual(result['unmapped'][0]['reason'], 'ambiguous_edges')

    def test_unknown_ifname_unmapped(self):
        obs = [{
            'device_id': 'CORE-01',
            'if_name_raw': 'Eth1/99',
            'in_pct': 10,
            'pct': 10,
            'if_speed_bps': 1000000000,
        }]
        result = join_observations_to_l2(obs, _nodes(), _l2_edges())
        self.assertEqual(result['paints'], [])
        self.assertEqual(result['unmapped'][0]['reason'], 'no_matching_edge')

    def test_one_sided_observation_yields_partial_not_new_edge(self):
        edges = _l2_edges()
        before = topology_fingerprint(edges)
        obs = [{
            'device_id': 'DIST-N1',
            'if_name_raw': 'Gi1/0/48',
            'in_pct': 55,
            'out_pct': 20,
            'pct': 55,
            'if_speed_bps': 1000000000,
        }]
        result = join_observations_to_l2(obs, _nodes(), edges)
        self.assertEqual(len(result['paints']), 1)
        self.assertEqual(result['paints'][0]['paint_state'], 'partial')
        self.assertEqual(result['paints'][0]['join']['status'], 'partial')
        self.assertEqual(len(edges), 2)
        self.assertEqual(topology_fingerprint(edges), before)

    def test_mismatched_device_identity_fails_closed(self):
        obs = [{
            'device_id': 'SPOOF-99',
            'if_name_raw': 'Te1/0/1',
            'in_pct': 90,
            'pct': 90,
            'if_speed_bps': 10000000000,
        }]
        result = join_observations_to_l2(obs, _nodes(), _l2_edges())
        self.assertEqual(result['paints'], [])
        self.assertIn('identity mismatch', result['error'])
        self.assertEqual(result['unmapped'][0]['reason'], 'identity_mismatch')

    def test_bind_mismatched_paint_host_fails_closed(self):
        doc = load_replay_overlay(FIXTURE)
        doc['paints'][0]['cable_key'] = 'alien|te1/0/1|dist-n1|te1/1/1|l2'
        bound = bind_replay_to_standard_l2(_nodes(), _l2_edges(), doc)
        self.assertFalse(bound.ok)
        self.assertIn('identity mismatch', bound.error)
        self.assertEqual(bound.bindings, {})

    def test_mgmt_irb_svi_dropped(self):
        for name in ('mgmt0', 'irb.100', 'Vlan100', 'Loopback0'):
            result = join_observations_to_l2(
                [{'device_id': 'CORE-01', 'if_name_raw': name, 'pct': 10, 'if_speed_bps': 1}],
                _nodes(),
                _l2_edges(),
            )
            self.assertEqual(result['paints'], [], msg=name)
            self.assertEqual(result['unmapped'][0]['reason'], 'mgmt_or_l3_svi', msg=name)

    def test_cisco_subinterface_no_parent_fallback(self):
        result = join_observations_to_l2(
            [{'device_id': 'CORE-01', 'if_name_raw': 'Te1/0/1.100', 'pct': 12, 'if_speed_bps': 1e9}],
            _nodes(),
            _l2_edges(),
        )
        self.assertEqual(result['paints'], [])
        self.assertEqual(result['unmapped'][0]['reason'], 'subinterface_no_parent_edge')

    def test_bundle_member_does_not_paint_po(self):
        edges = [{
            'id': 'e-po',
            'from': 'CORE-01',
            'to': 'DIST-N1',
            'f_port': 'Po10',
            't_port': 'Po10',
            'type': 'port-channel',
        }]
        result = join_observations_to_l2(
            [{
                'device_id': 'CORE-01',
                'if_name_raw': 'Gi1/0/1',
                'member_of': 'Po10',
                'pct': 80,
                'if_speed_bps': 1e9,
            }],
            _nodes(),
            edges,
        )
        self.assertEqual(result['paints'], [])
        self.assertEqual(result['unmapped'][0]['reason'], 'bundle_member_not_on_graph')

    def test_junos_unit_fallback_only_if_unique(self):
        edges = [{
            'id': 'e-j',
            'from': 'CORE-01',
            'to': 'DIST-N1',
            'f_port': 'ge-0/0/0',
            't_port': 'ge-0/0/1',
            'type': 'standard',
        }]
        result = join_observations_to_l2(
            [{
                'device_id': 'CORE-01',
                'if_name_raw': 'ge-0/0/0.0',
                'in_pct': 22,
                'pct': 22,
                'if_speed_bps': 1e9,
            }],
            _nodes(),
            edges,
        )
        self.assertEqual(len(result['paints']), 1)
        self.assertEqual(result['paints'][0]['join']['status'], 'partial')


class TestTopologyInvariants(unittest.TestCase):
    def test_overlay_never_creates_or_deletes_edges(self):
        edges = _l2_edges()
        before = copy.deepcopy(edges)
        fp = topology_fingerprint(edges)
        bound = bind_replay_to_standard_l2(_nodes(), edges, FIXTURE)
        self.assertTrue(bound.ok)
        self.assertEqual(len(edges), len(before))
        self.assertEqual(topology_fingerprint(edges), fp)
        self.assertEqual(bound.edge_count_before, bound.edge_count_after)
        self.assertEqual(
            [(e['from'], e['to'], e['f_port'], e['t_port']) for e in edges],
            [(e['from'], e['to'], e['f_port'], e['t_port']) for e in before],
        )

    def test_overlay_never_changes_trust_tier_or_classification(self):
        edges = _l2_edges()
        join_observations_to_l2(
            [{'device_id': 'CORE-01', 'if_name_raw': 'Te1/0/1', 'pct': 10, 'if_speed_bps': 1}],
            _nodes(),
            edges,
        )
        bind_replay_to_standard_l2(_nodes(), edges, FIXTURE)
        self.assertEqual(edges[0]['trust_tier'], 'high')
        self.assertEqual(edges[0]['type'], 'standard')
        self.assertEqual(edges[0]['confidence'], 'High')

    def test_overlay_edges_not_paint_eligible_stay_out(self):
        edges = _l2_edges() + [{
            'id': 'e-ov',
            'from': 'CORE-01',
            'to': 'DIST-N1',
            'f_port': 'nve1',
            't_port': 'nve1',
            'layer': 'overlay',
            'not_physical': True,
            'type': 'overlay',
        }]
        self.assertFalse(is_paint_eligible_l2_edge(edges[-1]))
        self.assertTrue(is_paint_eligible_l2_edge(edges[0]))

    def test_stp_blocked_not_paint_eligible(self):
        edge = {
            'id': 'e-stp',
            'from': 'CORE-01',
            'to': 'DIST-N1',
            'f_port': 'Gi1/0/2',
            't_port': 'Gi1/0/2',
            'protocol': 'STP',
            'link_type': 'stp-blocked',
            'type': 'stp-blocked',
            'layer': 'l2',
        }
        self.assertFalse(is_paint_eligible_l2_edge(edge))

    def test_unsampled_stroke_is_gray_dashed_not_down(self):
        st = stroke_for_paint({'paint_state': 'no_sample'})
        self.assertEqual(st['color'], NO_SAMPLE_COLOR)
        self.assertEqual(st['dashes'], NO_SAMPLE_DASH)
        self.assertEqual(st['meaning'], 'no_sample')
        self.assertNotEqual(st['meaning'], 'down')


if __name__ == '__main__':
    unittest.main()
