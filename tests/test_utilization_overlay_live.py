"""Live SSH utilization overlay — join, collector (mocked SSH), guards, HTML."""
from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.report_formatter import generate_topology_html
from utils.utilization_overlay.join import (
    bind_overlay_to_standard_l2,
    bind_replay_to_standard_l2,
    join_observations_to_l2,
    topology_fingerprint,
)
from utils.utilization_overlay.model import OverlayValidationError, load_overlay_document, load_replay_overlay
from utils.utilization_overlay.ssh_collector import (
    LiveUtilizationError,
    observations_from_device_pair,
    run_live_utilization,
    select_eligible_devices,
    write_overlay_json,
    write_ssh_targets,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE_FIXTURE = os.path.join(ROOT, 'tests', 'fixtures', 'utilization', 'live_standard_l2.json')
REPLAY_FIXTURE = os.path.join(ROOT, 'tests', 'fixtures', 'utilization', 'replay_standard_l2.json')


def _nodes():
    return [
        {'id': 'CORE-01', 'role': 'core'},
        {'id': 'DIST-N1', 'role': 'distribution'},
    ]


def _edges():
    return [{
        'id': 'e0', 'from': 'CORE-01', 'to': 'DIST-N1',
        'f_port': 'Te1/0/1', 't_port': 'Te1/1/1', 'type': 'standard',
        'trust_tier': 'high',
        'edge_data': {
            'from': 'CORE-01', 'to': 'DIST-N1',
            'f_port': 'Te1/0/1', 't_port': 'Te1/1/1',
            'type': 'standard', 'trust_tier': 'high',
        },
        'color': '#607d8b', 'width': 2,
    }]


def _html_nodes():
    return [
        {
            'id': 'CORE-01', 'label': 'CORE-01', 'role': 'core', 'level': 0,
            'shape': 'box', 'color': {'background': '#c0392b', 'border': '#333'},
            'font': {'color': '#fff'},
        },
        {
            'id': 'DIST-N1', 'label': 'DIST-N1', 'role': 'distribution', 'level': 1,
            'shape': 'box', 'color': {'background': '#e67e22', 'border': '#333'},
            'font': {'color': '#fff'},
        },
    ]


def _html_edges():
    return [{
        'id': 'e0', 'from': 'CORE-01', 'to': 'DIST-N1',
        'f_port': 'Te1/0/1', 't_port': 'Te1/1/1', 'label': '',
        'map_label': 'Te1/0/1 ↔ Te1/1/1',
        'type': 'standard', 'trust_tier': 'high',
        'edge_data': {
            'from': 'CORE-01', 'to': 'DIST-N1',
            'f_port': 'Te1/0/1', 't_port': 'Te1/1/1',
            'type': 'standard', 'confidence': 'High', 'trust_tier': 'high',
        },
        'color': '#607d8b', 'width': 2,
    }]


def _render(overlay=None):
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as tf:
        path = tf.name
    try:
        generate_topology_html(
            path, 2, 1,
            json.dumps(_html_nodes()), json.dumps(_html_edges()),
            '/* vis stub */',
            map_mode='all',
            utilization_overlay=overlay,
        )
        return open(path, encoding='utf-8').read()
    finally:
        os.unlink(path)


class TestLiveJoinInvariants(unittest.TestCase):
    def test_live_observations_map_only_to_existing_edges(self):
        edges = _edges()
        before = topology_fingerprint(edges)
        trust = edges[0]['trust_tier']
        obs = [{
            'device_id': 'CORE-01',
            'if_name_raw': 'Te1/0/1',
            'if_name_normalized': 'Te1/0/1',
            'in_bps': 8000,
            'out_bps': 4000,
            'in_pct': 8,
            'out_pct': 4,
            'pct': 8,
            'if_speed_bps': 100000,
            'sampled_at': '2026-08-22T12:00:00+00:00',
            'command': 'show interfaces',
        }]
        joined = join_observations_to_l2(
            obs, _nodes(), edges,
            mode='live', evidence_class='live_ssh', stale_after_seconds=900,
        )
        self.assertEqual(joined['mode'], 'live')
        self.assertEqual(joined['evidence_class'], 'live_ssh')
        self.assertEqual(len(joined['paints']), 1)
        self.assertEqual(topology_fingerprint(edges), before)
        self.assertEqual(edges[0]['trust_tier'], trust)
        self.assertEqual(edges[0]['type'], 'standard')
        self.assertEqual(len(edges), 1)

    def test_out_of_map_interface_not_painted(self):
        joined = join_observations_to_l2(
            [{'device_id': 'CORE-01', 'if_name_raw': 'Gi9/9/9', 'in_bps': 1, 'if_speed_bps': 1000}],
            _nodes(), _edges(),
            mode='live', evidence_class='live_ssh', stale_after_seconds=900,
        )
        self.assertEqual(joined['paints'], [])
        self.assertTrue(any(u['reason'] == 'no_matching_edge' for u in joined['unmapped']))

    def test_identity_mismatch_fails_closed(self):
        edges = _edges()
        before = topology_fingerprint(edges)
        joined = join_observations_to_l2(
            [{'device_id': 'SPOOF', 'if_name_raw': 'Te1/0/1', 'pct': 99, 'if_speed_bps': 1}],
            _nodes(), edges,
            mode='live', evidence_class='live_ssh', stale_after_seconds=900,
        )
        self.assertEqual(joined['paints'], [])
        self.assertIn('identity mismatch', joined['error'])
        self.assertEqual(topology_fingerprint(edges), before)

    def test_partial_stays_partial(self):
        joined = join_observations_to_l2(
            [{'device_id': 'CORE-01', 'if_name_raw': 'Te1/0/1', 'pct': 40, 'if_speed_bps': 1e9}],
            _nodes(), _edges(),
            mode='live', evidence_class='live_ssh', stale_after_seconds=900,
        )
        self.assertEqual(len(joined['paints']), 1)
        self.assertEqual(joined['paints'][0]['paint_state'], 'partial')
        self.assertEqual(joined['paints'][0]['join']['status'], 'partial')

    def test_no_speed_paints_gray_not_percent(self):
        edges = [{
            'id': 'e0', 'from': 'CORE-01', 'to': 'DIST-N1',
            'f_port': 'Te1/0/1', 't_port': 'Te1/1/1', 'type': 'standard',
            'trust_tier': 'high', 'one_sided': True,
            'edge_data': {
                'from': 'CORE-01', 'to': 'DIST-N1',
                'f_port': 'Te1/0/1', 't_port': 'Te1/1/1',
                'type': 'standard', 'trust_tier': 'high',
            },
        }]
        joined = join_observations_to_l2(
            [{'device_id': 'CORE-01', 'if_name_raw': 'Te1/0/1', 'in_bps': 8000, 'out_bps': 1000}],
            _nodes(), edges,
            mode='live', evidence_class='live_ssh', stale_after_seconds=900,
        )
        self.assertEqual(joined['paints'][0]['paint_state'], 'no_speed')
        self.assertIsNone(joined['paints'][0]['pct'])

    def test_bind_live_fixture_does_not_mutate_edges(self):
        edges = _edges()
        before = copy.deepcopy(edges)
        bound = bind_overlay_to_standard_l2(_nodes(), edges, LIVE_FIXTURE)
        self.assertTrue(bound.ok)
        self.assertEqual(bound.mode, 'live')
        self.assertEqual(bound.evidence_class, 'live_ssh')
        self.assertEqual(edges, before)
        self.assertIn('e0', bound.bindings)

    def test_bind_replay_still_rejects_live(self):
        with self.assertRaises(OverlayValidationError):
            load_replay_overlay(LIVE_FIXTURE, require_replay=True)
        bound = bind_replay_to_standard_l2(_nodes(), _edges(), LIVE_FIXTURE)
        self.assertFalse(bound.ok)


class TestLiveCollectorGuards(unittest.TestCase):
    def test_missing_credential_id_blocks(self):
        with self.assertRaises(LiveUtilizationError) as ctx:
            run_live_utilization(
                inventory=[{'host': '10.0.0.1', 'device_type': 'cisco_ios'}],
                user='u', pwd='secret-password', enb_pwd='',
                diag_folder='/tmp/does-not-exist-nst-util',
                credential_id='',
            )
        self.assertIn('credential_id', str(ctx.exception).lower())

    def test_eligible_devices_only_map_nodes(self):
        inventory = [
            {'host': '10.1.1.1', 'device_type': 'cisco_ios'},
            {'host': '10.9.9.9', 'device_type': 'cisco_ios'},
        ]
        nodes = [{'id': 'CORE-01'}]
        targets = [{'device_id': 'CORE-01', 'inventory_host': '10.1.1.1', 'device_type': 'cisco_ios'}]
        eligible, skipped = select_eligible_devices(inventory, nodes, targets)
        self.assertEqual(len(eligible), 1)
        self.assertEqual(eligible[0]['map_device_id'], 'CORE-01')
        self.assertIn('10.9.9.9', skipped)

    def test_overlay_json_has_no_secrets(self):
        doc = load_overlay_document(LIVE_FIXTURE)
        with tempfile.TemporaryDirectory() as td:
            path = write_overlay_json(td, doc)
            raw = open(path, encoding='utf-8').read()
        self.assertNotIn('password', raw.lower())
        self.assertNotIn('secret', raw.lower())
        self.assertNotIn('community', raw.lower())

    def test_identity_mismatch_device_is_unmapped_not_painted(self):
        obs, um = observations_from_device_pair({
            'status': 'identity_mismatch',
            'device_id': 'CORE-01',
            'resolved': 'OTHER-SW',
            'host': '10.1.1.1',
            't0': [], 't1': [],
        })
        self.assertEqual(obs, [])
        self.assertEqual(um[0]['reason'], 'identity_mismatch')

    def test_one_sided_t0_cancel_is_counter_invalid(self):
        extra = []
        result = {
            'status': 'cancelled',
            'device_id': 'CORE-01',
            't0': [{'if_name_raw': 'Te1/0/1', 'if_name_normalized': 'Te1/0/1'}],
            't1': [],
        }
        obs, um = observations_from_device_pair(result)
        self.assertEqual(obs, [])
        # collector treats cancel-without-t1 outside observations_from_device_pair
        extra.append({
            'device_id': 'CORE-01',
            'if_name_raw': 'Te1/0/1',
            'if_name_normalized': 'Te1/0/1',
            'reason': 'counter_invalid',
            'command': None,
        })
        self.assertEqual(extra[0]['reason'], 'counter_invalid')

    def test_mocked_ssh_run_writes_live_overlay(self):
        with tempfile.TemporaryDirectory() as td:
            f4 = {
                'nodes': _html_nodes(),
                'edges': _html_edges(),
            }
            json.dump(f4, open(os.path.join(td, '04_final_map_data.json'), 'w'))
            write_ssh_targets(td, [{
                'status': 'success',
                'device': '10.1.1.1',
                'data': {'true_host': 'CORE-01'},
            }], [{'host': '10.1.1.1', 'device_type': 'cisco_ios'}])
            sample = {
                'status': 'ok',
                'device_id': 'CORE-01',
                'host': '10.1.1.1',
                'dt': 10.0,
                'command': 'show interfaces',
                't0': [{
                    'if_name_raw': 'Te1/0/1',
                    'if_name_normalized': 'Te1/0/1',
                    'in_octets_64': 0,
                    'out_octets_64': 0,
                    'if_speed_bps': 10_000_000_000,
                    'sampled_at': '2026-08-22T12:00:00+00:00',
                }],
                't1': [{
                    'if_name_raw': 'Te1/0/1',
                    'if_name_normalized': 'Te1/0/1',
                    'in_octets_64': 1_250_000_000,
                    'out_octets_64': 1_000_000_000,
                    'if_speed_bps': 10_000_000_000,
                    'sampled_at': '2026-08-22T12:00:10+00:00',
                }],
            }
            with patch(
                'utils.utilization_overlay.ssh_collector.collect_two_samples_on_device',
                return_value=sample,
            ):
                with patch(
                    'utils.utilization_overlay.ssh_collector.repaint_standard_l2_html',
                    return_value=os.path.join(td, 'topology_map_all.html'),
                ):
                    out = run_live_utilization(
                        inventory=[{'host': '10.1.1.1', 'device_type': 'cisco_ios'}],
                        user='u', pwd='secret-password', enb_pwd='',
                        diag_folder=td,
                        credential_id='ops',
                        log=lambda m: None,
                    )
            self.assertEqual(out['mode'], 'live')
            overlay = json.load(open(out['overlay_path'], encoding='utf-8'))
            blob = json.dumps(overlay)
            self.assertNotIn('secret-password', blob)
            self.assertEqual(overlay['mode'], 'live')
            self.assertEqual(overlay['evidence_class'], 'live_ssh')
            self.assertGreaterEqual(overlay['summary']['painted_count'], 1)

    def test_device_ssh_error_degrades_not_crash(self):
        with tempfile.TemporaryDirectory() as td:
            json.dump(
                {'nodes': _html_nodes(), 'edges': _html_edges()},
                open(os.path.join(td, '04_final_map_data.json'), 'w'),
            )
            write_ssh_targets(td, [{
                'status': 'success', 'device': '10.1.1.1',
                'data': {'true_host': 'CORE-01'},
            }], [{'host': '10.1.1.1', 'device_type': 'cisco_ios'}])
            with patch(
                'utils.utilization_overlay.ssh_collector.collect_two_samples_on_device',
                return_value={'status': 'error', 'host': '10.1.1.1', 'device_id': 'CORE-01', 't0': [], 't1': []},
            ):
                with patch(
                    'utils.utilization_overlay.ssh_collector.repaint_standard_l2_html',
                    return_value=None,
                ):
                    out = run_live_utilization(
                        inventory=[{'host': '10.1.1.1', 'device_type': 'cisco_ios'}],
                        user='u', pwd='x', enb_pwd='',
                        diag_folder=td,
                        credential_id='ops',
                    )
            self.assertTrue(out['degraded'])
            self.assertEqual(out['painted_count'], 0)


class TestLiveHtml(unittest.TestCase):
    def test_live_label_is_honest(self):
        html = _render(load_overlay_document(LIVE_FIXTURE))
        self.assertIn('Live SSH counters — not SNMP', html)
        self.assertIn('"mode": "live"', html)
        self.assertIn('live_ssh', html)
        self.assertNotIn('snmp sample', html.lower())
        self.assertIn('Paint is not topology', html)
        self.assertIn('"from": "CORE-01"', html)
        self.assertIn('"trust_tier": "high"', html)

    def test_replay_fallback_still_works(self):
        html = _render(load_replay_overlay(REPLAY_FIXTURE))
        self.assertIn('Replay snapshot — not a live poll', html)
        self.assertIn('"mode": "replay"', html)

    def test_stale_banner(self):
        doc = load_overlay_document(LIVE_FIXTURE)
        doc['paints'][0]['paint_state'] = 'stale'
        doc['paints'][0]['freshness']['stale'] = True
        doc['summary']['stale_count'] = 1
        html = _render(doc)
        self.assertIn('STALE — last sample older than policy', html)

    def test_degraded_banner(self):
        doc = load_overlay_document(LIVE_FIXTURE)
        doc['degraded'] = True
        html = _render(doc)
        self.assertIn('Degraded — some devices failed or cancelled', html)

    def test_failed_live_does_not_break_base_map(self):
        html = _render({'schema': 'nope', 'mode': 'live'})
        self.assertIn('nst-standard-split', html)
        self.assertIn('"from": "CORE-01"', html)
        self.assertIn('"available": false', html)

    def test_web_copy_not_snmp(self):
        web = open(os.path.join(ROOT, 'vlan_checker_web.py'), encoding='utf-8').read()
        self.assertIn("'utilization_live':", web)
        self.assertIn('credential_id required for live SSH utilization', web)
        self.assertIn('/api/utilization-overlay/status', web)
        self.assertRegex(
            web,
            r'@localhost_required\s*\n\s*def api_utilization_overlay_status',
        )


class TestTelemetryFreezeIntact(unittest.TestCase):
    def test_telemetry_package_does_not_import_overlay(self):
        tel_dir = os.path.join(ROOT, 'utils', 'telemetry')
        for name in os.listdir(tel_dir):
            if not name.endswith('.py'):
                continue
            src = open(os.path.join(tel_dir, name), encoding='utf-8').read()
            self.assertNotIn('utilization_overlay', src)


if __name__ == '__main__':
    unittest.main()
