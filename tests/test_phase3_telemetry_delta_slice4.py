"""Phase 3 slice 4 — fixture-only change / delta helpers.

No alerting, live analytics, topology mutation, or secret retention.
"""
from __future__ import annotations

import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.telemetry import (
    ObservationStore,
    compute_delta,
    latest_delta,
    load_fixture_json,
    normalize_observation,
    pairwise_deltas,
    same_series,
    series_key,
)
from utils.telemetry.delta import (
    DIR_DECREASED,
    DIR_INCREASED,
    DIR_UNCHANGED,
    STATUS_COMPUTED,
    STATUS_INCOMPATIBLE,
    STATUS_INVALID,
    STATUS_RESET,
    STATUS_UNAVAILABLE,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'telemetry')


def _fix(name: str):
    return load_fixture_json(os.path.join(FIX, name))


def _counter_pair(prev_val, curr_val, *, ts0='2026-08-20T18:00:00Z', ts1='2026-08-20T18:05:00Z'):
    base = normalize_observation(_fix('iosxe_interface_counters.json'))
    a = copy.deepcopy(base)
    b = copy.deepcopy(base)
    a['value'] = prev_val
    b['value'] = curr_val
    a['source_timestamp'] = ts0
    b['source_timestamp'] = ts1
    a['observation_id'] = 'obs-a'
    b['observation_id'] = 'obs-b'
    a['monotonic'] = 'true'
    b['monotonic'] = 'true'
    a['metric_kind'] = 'counter'
    b['metric_kind'] = 'counter'
    return a, b


def _gauge_pair(prev_val, curr_val, *, ts0='2026-08-20T18:02:00Z', ts1='2026-08-20T18:07:00Z'):
    base = normalize_observation(_fix('junos_interface_optics.json'))
    a = copy.deepcopy(base)
    b = copy.deepcopy(base)
    a['value'] = prev_val
    b['value'] = curr_val
    a['source_timestamp'] = ts0
    b['source_timestamp'] = ts1
    a['observation_id'] = 'g-a'
    b['observation_id'] = 'g-b'
    a['metric_kind'] = 'gauge'
    b['metric_kind'] = 'gauge'
    a['monotonic'] = 'false'
    b['monotonic'] = 'false'
    return a, b


class TestSeriesIdentity(unittest.TestCase):
    def test_same_series_and_key(self):
        a, b = _counter_pair(10, 20)
        self.assertTrue(same_series(a, b))
        self.assertEqual(series_key(a), series_key(b))

    def test_device_mismatch(self):
        a, b = _counter_pair(10, 20)
        b['device_id'] = 'other'
        d = compute_delta(a, b)
        self.assertEqual(d['delta_status'], STATUS_INCOMPATIBLE)
        self.assertIn('device', d['notes'][0])

    def test_metric_mismatch(self):
        a, b = _counter_pair(10, 20)
        b['metric_name'] = 'other_metric'
        d = compute_delta(a, b)
        self.assertEqual(d['delta_status'], STATUS_INCOMPATIBLE)
        self.assertIn('metric', d['notes'][0])

    def test_entity_mismatch(self):
        a, b = _counter_pair(10, 20)
        b['entity_path'] = 'GigabitEthernet9/9'
        d = compute_delta(a, b)
        self.assertEqual(d['delta_status'], STATUS_INCOMPATIBLE)

    def test_unit_mismatch(self):
        a, b = _counter_pair(10, 20)
        b['unit'] = 'packets'
        d = compute_delta(a, b)
        self.assertEqual(d['delta_status'], STATUS_INCOMPATIBLE)

    def test_value_type_mismatch(self):
        a, b = _counter_pair(10, 20)
        b['value_type'] = 'float'
        d = compute_delta(a, b)
        self.assertEqual(d['delta_status'], STATUS_INCOMPATIBLE)


class TestCounterAndGaugeDeltas(unittest.TestCase):
    def test_counter_positive_delta(self):
        a, b = _counter_pair(100, 150)
        d = compute_delta(a, b, comparison_basis='source_timestamp')
        self.assertEqual(d['delta_status'], STATUS_COMPUTED)
        self.assertEqual(d['absolute_delta'], 50)
        self.assertEqual(d['direction'], DIR_INCREASED)
        self.assertFalse(d['reset_detected'])

    def test_counter_unchanged(self):
        a, b = _counter_pair(100, 100)
        d = compute_delta(a, b)
        self.assertEqual(d['delta_status'], STATUS_COMPUTED)
        self.assertEqual(d['direction'], DIR_UNCHANGED)
        self.assertEqual(d['absolute_delta'], 0)

    def test_counter_reset_when_monotonic(self):
        a, b = _counter_pair(1000, 5)
        d = compute_delta(a, b)
        self.assertEqual(d['delta_status'], STATUS_RESET)
        self.assertTrue(d['reset_detected'])
        self.assertIsNone(d['absolute_delta'])

    def test_counter_decrease_without_reset_support(self):
        a, b = _counter_pair(1000, 5)
        a['monotonic'] = 'unknown'
        b['monotonic'] = 'unknown'
        d = compute_delta(a, b)
        self.assertEqual(d['delta_status'], STATUS_UNAVAILABLE)
        self.assertFalse(d['reset_detected'])

    def test_gauge_increased_decreased(self):
        a, b = _gauge_pair(-3.0, -1.0)
        d = compute_delta(a, b)
        self.assertEqual(d['delta_status'], STATUS_COMPUTED)
        self.assertEqual(d['direction'], DIR_INCREASED)
        a2, b2 = _gauge_pair(-1.0, -3.0)
        d2 = compute_delta(a2, b2)
        self.assertEqual(d2['direction'], DIR_DECREASED)

    def test_string_state_changed(self):
        a, b = _counter_pair(1, 1)
        a['value'] = 'up'
        b['value'] = 'down'
        a['value_type'] = 'str'
        b['value_type'] = 'str'
        a['metric_kind'] = 'gauge'
        b['metric_kind'] = 'gauge'
        d = compute_delta(a, b)
        self.assertEqual(d['delta_status'], STATUS_COMPUTED)
        self.assertIn('changed', d['notes'][0])

    def test_no_self_comparison(self):
        a, _ = _counter_pair(1, 2)
        d = compute_delta(a, a)
        self.assertEqual(d['delta_status'], STATUS_INVALID)


class TestOrdering(unittest.TestCase):
    def test_source_timestamp_precedes_received_at(self):
        a, b = _counter_pair(10, 20)
        # Intentionally reverse received_at vs source
        a['received_at'] = '2026-08-20T20:00:00Z'
        b['received_at'] = '2026-08-20T17:00:00Z'
        d = latest_delta([b, a])  # unsorted input
        self.assertEqual(d['comparison_basis'], 'source_timestamp')
        self.assertEqual(d['absolute_delta'], 10)
        self.assertEqual(d['previous_observation_id'], 'obs-a')

    def test_received_at_fallback(self):
        a, b = _counter_pair(10, 30)
        a['source_timestamp'] = None
        b['source_timestamp'] = None
        a['received_at'] = '2026-08-20T18:00:00Z'
        b['received_at'] = '2026-08-20T18:10:00Z'
        d = latest_delta([b, a])
        self.assertEqual(d['comparison_basis'], 'received_at')
        self.assertEqual(d['absolute_delta'], 20)

    def test_pairwise(self):
        a, b = _counter_pair(10, 20)
        c = copy.deepcopy(b)
        c['observation_id'] = 'obs-c'
        c['value'] = 35
        c['source_timestamp'] = '2026-08-20T18:10:00Z'
        deltas = pairwise_deltas([c, a, b])
        self.assertEqual(len(deltas), 2)
        self.assertEqual(deltas[0]['absolute_delta'], 10)
        self.assertEqual(deltas[1]['absolute_delta'], 15)


class TestStoreIntegration(unittest.TestCase):
    def test_store_latest_delta_three_families_series(self):
        store = ObservationStore(max_observations=20)
        # Two iosxe samples same series
        a, b = _counter_pair(100, 180)
        store.insert(a)
        store.insert(b)
        # Other fixtures do not pollute this series query
        store.insert(normalize_observation(_fix('nxos_interface_counters.json')))
        store.insert(normalize_observation(
            _fix('junos_interface_optics.json'), received_at='2026-08-20T19:00:00Z',
        ))
        d = store.latest_delta(
            device_id=a['device_id'],
            metric_name=a['metric_name'],
            entity_path=a['entity_path'],
        )
        self.assertEqual(d['delta_status'], STATUS_COMPUTED)
        self.assertEqual(d['absolute_delta'], 80)
        # Immutability
        before = store.get(a['observation_id'])['value']
        _ = store.pairwise_deltas(device_id=a['device_id'], metric_name=a['metric_name'])
        self.assertEqual(store.get(a['observation_id'])['value'], before)

    def test_no_topology_fields_in_delta(self):
        a, b = _counter_pair(1, 2)
        d = compute_delta(a, b)
        for banned in ('trust_tier', 'from', 'to', 'f_port', 'not_physical', 'evidence'):
            self.assertNotIn(banned, d)

    def test_unknown_metric_kind_gauge_like(self):
        a, b = _counter_pair(5, 8)
        a['metric_kind'] = 'unknown'
        b['metric_kind'] = 'unknown'
        a['monotonic'] = 'unknown'
        b['monotonic'] = 'unknown'
        d = compute_delta(a, b)
        self.assertEqual(d['delta_status'], STATUS_COMPUTED)
        self.assertTrue(any('unknown' in w for w in d['warnings']))


if __name__ == '__main__':
    unittest.main()
