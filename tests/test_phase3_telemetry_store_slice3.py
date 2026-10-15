"""Phase 3 slice 3 — fixture-only in-process observation store / index.

No persistence, live transport, topology mutation, or secret retention.
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.telemetry import (
    UNKNOWN,
    ObservationStore,
    load_fixture_json,
    normalize_batch,
    normalize_observation,
)
from utils.telemetry.store import INSERT_DUPLICATE, INSERT_INSERTED, INSERT_REJECTED

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'telemetry')


def _fix(name: str):
    return load_fixture_json(os.path.join(FIX, name))


def _norm(name: str, **kwargs):
    return normalize_observation(_fix(name), **kwargs)


class TestObservationStoreInsert(unittest.TestCase):
    def setUp(self):
        self.store = ObservationStore(max_observations=10, default_query_limit=50)

    def test_insert_accepted_from_three_fixtures(self):
        for name in (
            'iosxe_interface_counters.json',
            'nxos_interface_counters.json',
            'junos_interface_optics.json',
        ):
            obs = _norm(name)
            r = self.store.insert(obs)
            self.assertEqual(r['status'], INSERT_INSERTED, r)
        self.assertEqual(self.store.count(), 3)
        ids = self.store.observation_ids()
        self.assertEqual(len(ids), 3)
        self.assertEqual(len(set(ids)), 3)

    def test_duplicate_first_wins(self):
        obs = _norm('iosxe_interface_counters.json')
        self.assertEqual(self.store.insert(obs)['status'], INSERT_INSERTED)
        mutated = dict(obs)
        mutated['value'] = 999999
        r = self.store.insert(mutated)
        self.assertEqual(r['status'], INSERT_DUPLICATE)
        stored = self.store.get(obs['observation_id'])
        self.assertEqual(stored['value'], 1048576)
        self.assertEqual(self.store.count(), 1)
        self.assertEqual(self.store.stats()['duplicates'], 1)

    def test_reject_missing_id_and_quarantined(self):
        bad = _norm('iosxe_interface_counters.json')
        bad['observation_id'] = ''
        self.assertEqual(self.store.insert(bad)['status'], INSERT_REJECTED)
        q = _norm('malformed_value.json')
        self.assertTrue(q.get('quarantined'))
        self.assertEqual(self.store.insert(q)['status'], INSERT_REJECTED)
        self.assertEqual(self.store.count(), 0)

    def test_reject_unknown_observation_id(self):
        obs = _norm('iosxe_interface_counters.json')
        obs['observation_id'] = UNKNOWN
        self.assertEqual(self.store.insert(obs)['status'], INSERT_REJECTED)

    def test_reject_secrets(self):
        obs = _norm('iosxe_interface_counters.json')
        dirty = dict(obs)
        dirty['password'] = 'nope'
        r = self.store.insert(dirty)
        self.assertEqual(r['status'], INSERT_REJECTED)
        self.assertNotIn('nope', str(r))
        self.assertEqual(self.store.count(), 0)


class TestObservationStoreQuery(unittest.TestCase):
    def setUp(self):
        self.store = ObservationStore(max_observations=50, default_query_limit=10)
        self.iosxe = _norm('iosxe_interface_counters.json')
        self.nxos = _norm('nxos_interface_counters.json')
        self.junos = _norm(
            'junos_interface_optics.json', received_at='2026-08-20T19:00:00Z',
        )
        for obs in (self.iosxe, self.nxos, self.junos):
            self.store.insert(obs)

    def test_query_by_device(self):
        rows = self.store.query(device_id='edge-xe-01')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['device_id'], 'edge-xe-01')

    def test_query_by_metric(self):
        rows = self.store.query(metric_name='rx-power')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['platform'], 'juniper_junos')
        self.assertEqual(rows[0]['catalog_entry_id'], 'junos.optics.rx_power')

    def test_query_by_entity_path(self):
        rows = self.store.query(entity_path='Ethernet1/1')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['device_id'], 'leaf-nx-01')

    def test_query_by_catalog_status(self):
        rows = self.store.query(catalog_status='known')
        self.assertEqual(len(rows), 3)

    def test_source_timestamp_range(self):
        rows = self.store.query(
            source_timestamp_start='2026-08-20T18:00:00Z',
            source_timestamp_end='2026-08-20T18:01:30Z',
        )
        devices = {r['device_id'] for r in rows}
        self.assertEqual(devices, {'edge-xe-01', 'leaf-nx-01'})

    def test_received_at_range(self):
        rows = self.store.query(
            received_at_start='2026-08-20T19:00:00Z',
            received_at_end='2026-08-20T19:00:00Z',
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['device_id'], 'qfx-01')
        # Observations without received_at do not match an explicit range
        none_rx = self.store.query(
            received_at_start='2026-08-20T00:00:00Z',
            received_at_end='2026-08-20T23:59:59Z',
        )
        self.assertEqual(len(none_rx), 1)

    def test_deterministic_insertion_order_and_limit(self):
        rows = self.store.query(limit=2)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['observation_id'], self.iosxe['observation_id'])
        self.assertEqual(rows[1]['observation_id'], self.nxos['observation_id'])

    def test_unknown_metric_query(self):
        # Store an observation with unknown metric name (path known to catalog or not)
        obs = normalize_observation({
            'platform': 'cisco_xe',
            'hostname': 'lab-unknown-metric',
            'path': 'no/such/metric',
            'value': 1,
            'timestamp': '2026-08-20T18:00:00Z',
        })
        self.assertEqual(obs['metric_name'], 'metric')  # leaf from path
        # Force explicit UNKNOWN metric for queryability test
        obs['metric_name'] = UNKNOWN
        # Recompute id would change — insert as-is with existing id
        self.store.insert(obs)
        rows = self.store.query(metric_name=UNKNOWN, device_id='lab-unknown-metric')
        self.assertEqual(len(rows), 1)

    def test_defensive_copy(self):
        rows = self.store.query(device_id='edge-xe-01')
        rows[0]['value'] = -1
        rows[0]['warnings'].append('mutated')
        again = self.store.get(self.iosxe['observation_id'])
        self.assertEqual(again['value'], 1048576)
        self.assertNotIn('mutated', again.get('warnings') or [])

    def test_no_topology_fields(self):
        for row in self.store.query(limit=10):
            for banned in ('trust_tier', 'from', 'to', 'f_port', 'not_physical', 'evidence'):
                self.assertNotIn(banned, row)


class TestObservationStoreRetention(unittest.TestCase):
    def test_oldest_first_eviction(self):
        store = ObservationStore(max_observations=2, default_query_limit=10)
        a = _norm('iosxe_interface_counters.json')
        b = _norm('nxos_interface_counters.json')
        c = _norm('junos_interface_optics.json')
        self.assertEqual(store.insert(a)['status'], INSERT_INSERTED)
        self.assertEqual(store.insert(b)['status'], INSERT_INSERTED)
        r = store.insert(c)
        self.assertEqual(r['status'], INSERT_INSERTED)
        self.assertEqual(r.get('evicted'), [a['observation_id']])
        self.assertEqual(store.count(), 2)
        self.assertIsNone(store.get(a['observation_id']))
        self.assertIsNotNone(store.get(b['observation_id']))
        self.assertIsNotNone(store.get(c['observation_id']))
        self.assertEqual(store.stats()['evicted'], 1)
        self.assertEqual(store.stats()['stored'], 2)

    def test_ingest_normalized_batch_skips_quarantine(self):
        store = ObservationStore(max_observations=20)
        batch = normalize_batch([
            _fix('iosxe_interface_counters.json'),
            _fix('malformed_value.json'),
            _fix('junos_interface_optics.json'),
        ])
        summary = store.ingest_normalized_batch(batch)
        self.assertEqual(summary['inserted'], 2)
        self.assertEqual(store.count(), 2)
        self.assertEqual(batch['count_quarantined'], 1)

    def test_clear_resets(self):
        store = ObservationStore(max_observations=5)
        store.insert(_norm('iosxe_interface_counters.json'))
        store.clear()
        self.assertEqual(store.count(), 0)
        self.assertEqual(store.stats()['inserted'], 0)


if __name__ == '__main__':
    unittest.main()
