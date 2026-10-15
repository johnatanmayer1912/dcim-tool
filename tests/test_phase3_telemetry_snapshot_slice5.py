"""Phase 3 slice 5 — fixture-only series snapshot export.

No live dashboards, persistence, topology mutation, or secret retention.
"""
from __future__ import annotations

import copy
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.telemetry import (
    UNKNOWN,
    ObservationStore,
    export_series_snapshot,
    load_fixture_json,
    normalize_observation,
    snapshot_to_json,
)
from utils.telemetry.delta import STATUS_COMPUTED, STATUS_RESET, STATUS_UNAVAILABLE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'telemetry')


def _fix(name: str):
    return load_fixture_json(os.path.join(FIX, name))


def _norm(name: str, **kwargs):
    return normalize_observation(_fix(name), **kwargs)


def _store_three_families():
    store = ObservationStore(max_observations=50, default_query_limit=50)
    store.insert(_norm('iosxe_interface_counters.json'))
    store.insert(_norm('nxos_interface_counters.json'))
    store.insert(_norm(
        'junos_interface_optics.json', received_at='2026-08-20T19:00:00Z',
    ))
    return store


class TestSeriesSnapshotBasics(unittest.TestCase):
    def test_one_summary_per_series_and_counts(self):
        store = _store_three_families()
        snap = export_series_snapshot(store, generated_at='2026-08-20T21:00:00Z')
        self.assertEqual(snap['schema_version'], 'p3s5-1')
        self.assertEqual(snap['generated_at'], '2026-08-20T21:00:00Z')
        self.assertEqual(snap['series_count'], 3)
        self.assertEqual(snap['observation_count'], 3)
        keys = [s['series_key'] for s in snap['series']]
        self.assertEqual(keys, sorted(keys))
        self.assertEqual(len(set(keys)), 3)

    def test_generated_at_unknown_when_omitted(self):
        store = _store_three_families()
        snap = export_series_snapshot(store)
        self.assertEqual(snap['generated_at'], UNKNOWN)
        self.assertTrue(any('generated_at' in n for n in snap['export_notes']))

    def test_latest_fields_and_unavailable_delta(self):
        store = _store_three_families()
        snap = export_series_snapshot(store, generated_at='2026-08-20T21:00:00Z')
        by_dev = {s['device_id']: s for s in snap['series']}
        xe = by_dev['edge-xe-01']
        self.assertEqual(xe['latest_value'], 1048576)
        self.assertEqual(xe['latest_source_timestamp'], '2026-08-20T18:00:00Z')
        self.assertIsNone(xe['latest_received_at'])
        self.assertEqual(xe['delta_status'], STATUS_UNAVAILABLE)
        self.assertEqual(xe['last_delta']['delta_status'], STATUS_UNAVAILABLE)
        junos = by_dev['qfx-01']
        self.assertEqual(junos['latest_received_at'], '2026-08-20T19:00:00Z')
        self.assertEqual(junos['latest_source_timestamp'], '2026-08-20T18:02:00.123Z')
        self.assertEqual(junos['catalog_status'], 'known')

    def test_json_serialization(self):
        store = _store_three_families()
        snap = export_series_snapshot(store, generated_at='2026-08-20T21:00:00Z')
        text = snapshot_to_json(snap)
        again = json.loads(text)
        self.assertEqual(again['series_count'], 3)
        # sort_keys deterministic
        self.assertEqual(text, snapshot_to_json(again))


class TestSnapshotDeltas(unittest.TestCase):
    def test_counter_delta_and_reset(self):
        store = ObservationStore(max_observations=20)
        a = _norm('iosxe_interface_counters.json')
        b = copy.deepcopy(a)
        a['observation_id'] = 'c1'
        b['observation_id'] = 'c2'
        a['value'] = 100
        b['value'] = 180
        a['source_timestamp'] = '2026-08-20T18:00:00Z'
        b['source_timestamp'] = '2026-08-20T18:05:00Z'
        store.insert(a)
        store.insert(b)
        snap = export_series_snapshot(
            store, generated_at='2026-08-20T21:00:00Z', device_id=a['device_id'],
        )
        self.assertEqual(snap['series_count'], 1)
        s = snap['series'][0]
        self.assertEqual(s['latest_value'], 180)
        self.assertEqual(s['delta_status'], STATUS_COMPUTED)
        self.assertEqual(s['last_delta']['absolute_delta'], 80)
        self.assertFalse(s['reset_detected'])

        # Reset case
        store2 = ObservationStore(max_observations=20)
        r1 = copy.deepcopy(a)
        r2 = copy.deepcopy(b)
        r1['value'] = 500
        r2['value'] = 3
        store2.insert(r1)
        store2.insert(r2)
        snap2 = export_series_snapshot(store2, generated_at='t', device_id=a['device_id'])
        self.assertEqual(snap2['series'][0]['delta_status'], STATUS_RESET)
        self.assertTrue(snap2['series'][0]['reset_detected'])

    def test_gauge_signed_delta(self):
        store = ObservationStore(max_observations=20)
        a = _norm('junos_interface_optics.json')
        b = copy.deepcopy(a)
        a['observation_id'] = 'g1'
        b['observation_id'] = 'g2'
        a['value'] = -3.0
        b['value'] = -1.0
        a['source_timestamp'] = '2026-08-20T18:02:00Z'
        b['source_timestamp'] = '2026-08-20T18:08:00Z'
        store.insert(a)
        store.insert(b)
        snap = export_series_snapshot(store, generated_at='t')
        s = snap['series'][0]
        self.assertEqual(s['delta_status'], STATUS_COMPUTED)
        self.assertEqual(s['last_delta']['direction'], 'increased')
        self.assertEqual(s['last_delta']['absolute_delta'], 2.0)


class TestSnapshotFiltersAndSafety(unittest.TestCase):
    def test_filters_and_limit(self):
        store = _store_three_families()
        snap = export_series_snapshot(
            store, generated_at='t', catalog_status='known', limit=2,
        )
        self.assertEqual(snap['series_count'], 2)
        snap_dev = export_series_snapshot(
            store, generated_at='t', device_id='leaf-nx-01',
        )
        self.assertEqual(snap_dev['series_count'], 1)
        self.assertEqual(snap_dev['series'][0]['device_id'], 'leaf-nx-01')

    def test_unknown_catalog_exportable(self):
        store = ObservationStore(max_observations=10)
        obs = normalize_observation({
            'platform': 'cisco_xe',
            'hostname': 'lab-u',
            'path': 'no/such/metric',
            'value': 1,
            'timestamp': '2026-08-20T18:00:00Z',
        })
        self.assertEqual(obs['catalog_status'], 'unknown')
        store.insert(obs)
        snap = export_series_snapshot(store, generated_at='t', catalog_status='unknown')
        self.assertEqual(snap['series_count'], 1)
        self.assertEqual(snap['series'][0]['catalog_status'], 'unknown')

    def test_defensive_copy_and_no_store_mutation(self):
        store = _store_three_families()
        before = store.count()
        snap = export_series_snapshot(store, generated_at='t')
        snap['series'][0]['latest_value'] = 'mutated'
        snap['series'][0]['warnings'].append('x')
        self.assertEqual(store.count(), before)
        snap2 = export_series_snapshot(store, generated_at='t')
        self.assertNotEqual(snap2['series'][0]['latest_value'], 'mutated')

    def test_no_secrets_or_topology(self):
        store = _store_three_families()
        text = snapshot_to_json(export_series_snapshot(store, generated_at='t'))
        for needle in ('password', 'token', 'private_key', 'credential_id', 'trust_tier'):
            self.assertNotIn(needle, text)
        snap = export_series_snapshot(store, generated_at='t')
        for s in snap['series']:
            for banned in ('from', 'to', 'f_port', 'not_physical', 'evidence', 'password'):
                self.assertNotIn(banned, s)

    def test_invalid_limit(self):
        store = _store_three_families()
        with self.assertRaises(ValueError):
            export_series_snapshot(store, generated_at='t', limit=-1)


if __name__ == '__main__':
    unittest.main()
