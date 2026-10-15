"""Phase 3 slice 6 — fixture-only telemetry regression pack.

End-to-end invariants across contract → catalog → store → delta → snapshot.

NON-GOALS
---------
- No live collectors, gRPC, SSH, SNMP, UI, auth, persistence, or alerting.
- No new vendor fixtures, Arista, packaging, or topology mutation.
- Does not claim production durability, performance, or security certification.
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
    compute_delta,
    empty_observation,
    export_series_snapshot,
    latest_delta,
    load_fixture_json,
    lookup_metric,
    normalize_batch,
    normalize_observation,
    same_series,
    series_key,
    snapshot_to_json,
)
from utils.telemetry.catalog import STATUS_AMBIGUOUS, STATUS_KNOWN, STATUS_UNKNOWN
from utils.telemetry.delta import (
    DIR_DECREASED,
    DIR_INCREASED,
    STATUS_COMPUTED,
    STATUS_INCOMPATIBLE,
    STATUS_RESET,
    STATUS_UNAVAILABLE,
)
from utils.telemetry.store import INSERT_DUPLICATE, INSERT_INSERTED, INSERT_REJECTED

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'telemetry')

_TOPOLOGY_FORBIDDEN = (
    'trust_tier',
    'from',
    'to',
    'f_port',
    't_port',
    'not_physical',
    'edges',
    'topology',
    'cable',
    'link_status',
    'relation_key',
)

_SECRET_MARKERS = (
    'should-never-normalize',
    'password',
    'token',
    'credential_id',
    'credential_key',
)


def _fix(name: str):
    return load_fixture_json(os.path.join(FIX, name))


def _norm(name: str, **kwargs):
    return normalize_observation(_fix(name), **kwargs)


def _assert_no_topology_keys(obj, path='root'):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in _TOPOLOGY_FORBIDDEN, f'topology key {k!r} at {path}'
            _assert_no_topology_keys(v, f'{path}.{k}')
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _assert_no_topology_keys(item, f'{path}[{i}]')


def _assert_no_secret_markers(blob: str):
    low = blob.lower()
    for needle in _SECRET_MARKERS:
        assert needle not in low, f'secret marker found: {needle}'


def _pipeline_three_families(*, generated_at='2026-08-20T21:00:00Z'):
    """Normalize → store → snapshot for the three existing fixture families."""
    store = ObservationStore(max_observations=50, default_query_limit=50)
    iosxe = _norm('iosxe_interface_counters.json')
    nxos = _norm('nxos_interface_counters.json')
    junos = _norm('junos_interface_optics.json', received_at='2026-08-20T19:00:00Z')
    for obs in (iosxe, nxos, junos):
        r = store.insert(obs)
        assert r['status'] == INSERT_INSERTED, r
    snap = export_series_snapshot(store, generated_at=generated_at)
    return {
        'iosxe': iosxe,
        'nxos': nxos,
        'junos': junos,
        'store': store,
        'snap': snap,
        'json': snapshot_to_json(snap),
    }


def _counter_pair_from_iosxe(prev_val, curr_val):
    base = _norm('iosxe_interface_counters.json')
    a = copy.deepcopy(base)
    b = copy.deepcopy(base)
    a['observation_id'] = 'reg-c1'
    b['observation_id'] = 'reg-c2'
    a['value'] = prev_val
    b['value'] = curr_val
    a['source_timestamp'] = '2026-08-20T18:00:00Z'
    b['source_timestamp'] = '2026-08-20T18:05:00Z'
    a['received_at'] = '2026-08-20T18:10:00Z'
    b['received_at'] = '2026-08-20T18:01:00Z'  # earlier received, later source
    return a, b


def _gauge_pair_from_junos(prev_val, curr_val):
    base = _norm('junos_interface_optics.json')
    a = copy.deepcopy(base)
    b = copy.deepcopy(base)
    a['observation_id'] = 'reg-g1'
    b['observation_id'] = 'reg-g2'
    a['value'] = prev_val
    b['value'] = curr_val
    a['source_timestamp'] = '2026-08-20T18:02:00Z'
    b['source_timestamp'] = '2026-08-20T18:07:00Z'
    a['metric_kind'] = 'gauge'
    b['metric_kind'] = 'gauge'
    a['monotonic'] = 'false'
    b['monotonic'] = 'false'
    return a, b


class TestIosXeEndToEnd(unittest.TestCase):
    def test_ios_xe_end_to_end_contract_catalog_store_delta_snapshot(self):
        raw = _fix('iosxe_interface_counters.json')
        obs = normalize_observation(raw)
        self.assertFalse(obs['quarantined'])
        self.assertTrue(obs['observation_id'])
        self.assertEqual(obs['source_timestamp'], '2026-08-20T18:00:00Z')
        self.assertIsNone(obs.get('received_at'))
        self.assertEqual(obs['catalog_status'], STATUS_KNOWN)
        self.assertEqual(obs['platform'], 'cisco_xe')

        store = ObservationStore(max_observations=10)
        self.assertEqual(store.insert(obs)['status'], INSERT_INSERTED)
        rows = store.query(device_id=obs['device_id'])
        self.assertEqual(len(rows), 1)
        rows[0]['value'] = 999
        self.assertEqual(store.query(device_id=obs['device_id'])[0]['value'], obs['value'])

        # Single observation → unavailable delta in snapshot
        snap = export_series_snapshot(store, generated_at='2026-08-20T21:00:00Z')
        self.assertEqual(snap['series_count'], 1)
        s = snap['series'][0]
        self.assertEqual(s['latest_value'], 1048576)
        self.assertEqual(s['latest_source_timestamp'], '2026-08-20T18:00:00Z')
        self.assertEqual(s['delta_status'], STATUS_UNAVAILABLE)
        self.assertEqual(s['catalog_status'], STATUS_KNOWN)

        # Pairwise counter delta after second point
        a, b = _counter_pair_from_iosxe(100, 180)
        d = compute_delta(a, b)
        self.assertEqual(d['delta_status'], STATUS_COMPUTED)
        self.assertEqual(d['absolute_delta'], 80)
        self.assertEqual(d['direction'], DIR_INCREASED)

        text = snapshot_to_json(snap)
        json.loads(text)
        _assert_no_topology_keys(snap)
        _assert_no_secret_markers(text)


class TestNxOsEndToEnd(unittest.TestCase):
    def test_nx_os_end_to_end_contract_catalog_store_delta_snapshot(self):
        obs = _norm('nxos_interface_counters.json')
        self.assertFalse(obs['quarantined'])
        self.assertEqual(obs['platform'], 'cisco_nxos')
        self.assertEqual(obs['device_id'], 'leaf-nx-01')
        self.assertEqual(obs['catalog_status'], STATUS_KNOWN)
        self.assertEqual(obs['source_timestamp'], '2026-08-20T18:01:00Z')

        lu = lookup_metric(obs['metric_path_raw'], platform=obs['platform'])
        self.assertEqual(lu['status'], STATUS_KNOWN)

        store = ObservationStore(max_observations=10)
        store.insert(obs)
        a = copy.deepcopy(obs)
        b = copy.deepcopy(obs)
        a['observation_id'] = 'nx-a'
        b['observation_id'] = 'nx-b'
        a['value'] = 1000
        b['value'] = 1500
        a['source_timestamp'] = '2026-08-20T18:01:00Z'
        b['source_timestamp'] = '2026-08-20T18:06:00Z'
        store2 = ObservationStore(max_observations=10)
        store2.insert(a)
        store2.insert(b)
        d = latest_delta(store2.query(device_id='leaf-nx-01'))
        self.assertEqual(d['delta_status'], STATUS_COMPUTED)
        self.assertEqual(d['absolute_delta'], 500)

        snap = export_series_snapshot(store2, generated_at='2026-08-20T21:00:00Z')
        self.assertEqual(snap['series'][0]['delta_status'], STATUS_COMPUTED)
        self.assertEqual(snap['series'][0]['last_delta']['absolute_delta'], 500)
        _assert_no_topology_keys(snap)


class TestJunosEndToEnd(unittest.TestCase):
    def test_junos_end_to_end_contract_catalog_store_delta_snapshot(self):
        obs = _norm(
            'junos_interface_optics.json',
            received_at='2026-08-20T19:00:00Z',
        )
        self.assertFalse(obs['quarantined'])
        self.assertEqual(obs['platform'], 'juniper_junos')
        self.assertEqual(obs['device_id'], 'qfx-01')
        self.assertEqual(obs['catalog_status'], STATUS_KNOWN)
        self.assertEqual(obs['source_timestamp'], '2026-08-20T18:02:00.123Z')
        self.assertEqual(obs['received_at'], '2026-08-20T19:00:00Z')
        self.assertNotEqual(obs['source_timestamp'], obs['received_at'])

        store = ObservationStore(max_observations=10)
        store.insert(obs)
        a, b = _gauge_pair_from_junos(-3.45, -4.10)
        store.insert(a)
        # a/b share series with fixture obs — use fresh store for gauge pair only
        gstore = ObservationStore(max_observations=10)
        gstore.insert(a)
        gstore.insert(b)
        d = compute_delta(a, b)
        self.assertEqual(d['delta_status'], STATUS_COMPUTED)
        self.assertEqual(d['direction'], DIR_DECREASED)
        self.assertAlmostEqual(d['absolute_delta'], -0.65, places=5)

        snap = export_series_snapshot(gstore, generated_at='2026-08-20T21:00:00Z')
        self.assertEqual(snap['series_count'], 1)
        self.assertEqual(snap['series'][0]['delta_status'], STATUS_COMPUTED)
        self.assertEqual(snap['series'][0]['latest_value'], -4.10)
        self.assertFalse(snap['series'][0]['reset_detected'])


class TestCrossSliceIdentityAndDedup(unittest.TestCase):
    def test_cross_slice_identity_and_dedup_invariants(self):
        obs = _norm('iosxe_interface_counters.json')
        again = _norm('iosxe_interface_counters.json')
        self.assertEqual(obs['observation_id'], again['observation_id'])

        store = ObservationStore(max_observations=10)
        self.assertEqual(store.insert(obs)['status'], INSERT_INSERTED)
        dup = store.insert(again)
        self.assertEqual(dup['status'], INSERT_DUPLICATE)
        self.assertEqual(store.count(), 1)

        # First-wins: mutating a re-insert candidate must not replace stored value
        mutated = copy.deepcopy(obs)
        mutated['value'] = 0
        store.insert(mutated)
        self.assertEqual(store.query()[0]['value'], 1048576)

        # Oldest-first eviction
        tiny = ObservationStore(max_observations=2)
        x = _norm('iosxe_interface_counters.json')
        y = _norm('nxos_interface_counters.json')
        z = _norm('junos_interface_optics.json')
        tiny.insert(x)
        tiny.insert(y)
        ev = tiny.insert(z)
        self.assertIn('evicted', ev)
        self.assertEqual(ev['evicted'], [x['observation_id']])
        ids = {r['observation_id'] for r in tiny.query()}
        self.assertEqual(ids, {y['observation_id'], z['observation_id']})

        # Quarantined / secret never stored
        bad = _norm('malformed_value.json')
        self.assertTrue(bad['quarantined'])
        self.assertEqual(tiny.insert(bad)['status'], INSERT_REJECTED)
        secret = _norm('with_secrets.json')
        self.assertTrue(secret['quarantined'])
        self.assertEqual(tiny.insert(secret)['status'], INSERT_REJECTED)

        # Unknown remains exportable; ambiguous never silently selected
        unk = _norm('unknown_metric.json')
        self.assertEqual(unk['catalog_status'], STATUS_UNKNOWN)
        amb = normalize_observation({
            'platform': 'cisco_xe',
            'hostname': 'amb-01',
            'path': 'test/ambiguous/sensor',
            'value': 1,
            'timestamp': '2026-08-20T18:00:00Z',
        })
        self.assertEqual(amb['catalog_status'], STATUS_AMBIGUOUS)
        self.assertEqual(sorted(amb['catalog_matches']), ['test.ambiguous.a', 'test.ambiguous.b'])

        # Legacy empty_observation remains compatible shape
        legacy = empty_observation(observation_id='legacy-1', device_id='d1', metric_name='m')
        self.assertIn('observation_id', legacy)
        self.assertIn('source_timestamp', legacy)


class TestCrossSliceTimestampAndOrdering(unittest.TestCase):
    def test_cross_slice_timestamp_and_ordering_invariants(self):
        a, b = _counter_pair_from_iosxe(50, 90)
        # source_timestamp order precedes received_at (b has earlier received_at)
        self.assertGreater(b['source_timestamp'], a['source_timestamp'])
        self.assertLess(b['received_at'], a['received_at'])
        order_store = ObservationStore(max_observations=10)
        # Insert later-source first so insertion order alone would reverse chronology
        order_store.insert(b)
        order_store.insert(a)
        d = latest_delta(order_store.query())
        self.assertEqual(d['delta_status'], STATUS_COMPUTED)
        self.assertEqual(d['absolute_delta'], 40)
        self.assertEqual(d['previous_observation_id'], 'reg-c1')
        self.assertEqual(d['current_observation_id'], 'reg-c2')
        self.assertEqual(d['comparison_basis'], 'source_timestamp')

        # Gauge signed direction
        g0, g1 = _gauge_pair_from_junos(1.0, 2.5)
        gd = compute_delta(g0, g1)
        self.assertEqual(gd['direction'], DIR_INCREASED)
        self.assertAlmostEqual(gd['absolute_delta'], 1.5, places=5)

        # Explicit monotonic reset
        r0, r1 = _counter_pair_from_iosxe(500, 3)
        rd = compute_delta(r0, r1)
        self.assertEqual(rd['delta_status'], STATUS_RESET)
        self.assertTrue(rd['reset_detected'])

        # Unsupported wrap / non-monotonic decrease stays unavailable
        u0, u1 = _counter_pair_from_iosxe(500, 3)
        u0['monotonic'] = 'false'
        u1['monotonic'] = 'false'
        ud = compute_delta(u0, u1)
        self.assertEqual(ud['delta_status'], STATUS_UNAVAILABLE)
        self.assertFalse(ud['reset_detected'])

        # Incompatible series: no numeric delta
        x = _norm('iosxe_interface_counters.json')
        y = _norm('nxos_interface_counters.json')
        self.assertFalse(same_series(x, y))
        inc = compute_delta(x, y)
        self.assertEqual(inc['delta_status'], STATUS_INCOMPATIBLE)
        self.assertIsNone(inc.get('absolute_delta'))

        # Snapshot: source vs received preserved; series_key ordering
        pipe = _pipeline_three_families()
        keys = [s['series_key'] for s in pipe['snap']['series']]
        self.assertEqual(keys, sorted(keys))
        by_dev = {s['device_id']: s for s in pipe['snap']['series']}
        self.assertEqual(by_dev['qfx-01']['latest_received_at'], '2026-08-20T19:00:00Z')
        self.assertEqual(by_dev['qfx-01']['latest_source_timestamp'], '2026-08-20T18:02:00.123Z')
        self.assertIsNone(by_dev['edge-xe-01']['latest_received_at'])
        self.assertEqual(pipe['snap']['generated_at'], '2026-08-20T21:00:00Z')

        omit = export_series_snapshot(pipe['store'])
        self.assertEqual(omit['generated_at'], UNKNOWN)


class TestCrossSliceSecretSafety(unittest.TestCase):
    def test_cross_slice_secret_safety(self):
        secret = _norm('with_secrets.json')
        self.assertTrue(secret['quarantined'])
        blob = json.dumps(secret, sort_keys=True)
        self.assertNotIn('should-never-normalize', blob)
        self.assertNotIn('abc123', blob)

        store = ObservationStore(max_observations=10)
        self.assertEqual(store.insert(secret)['status'], INSERT_REJECTED)
        store.insert(_norm('iosxe_interface_counters.json'))
        snap = export_series_snapshot(store, generated_at='2026-08-20T21:00:00Z')
        text = snapshot_to_json(snap)
        _assert_no_secret_markers(text)
        self.assertNotIn('raw_payload', text)
        self.assertNotIn('"payload"', text)
        for s in snap['series']:
            self.assertNotIn('raw_payload', s)
            self.assertNotIn('password', s)
            self.assertNotIn('token', s)

        # Catalog lookup of secret-like path stays invalid without echoing secret
        lu = lookup_metric('interfaces/password/hash', platform='cisco_xe')
        self.assertEqual(lu['status'], 'invalid')
        lu_blob = json.dumps(lu)
        self.assertNotIn('interfaces/password/hash', lu_blob.lower())


class TestCrossSliceNoTopologyMutation(unittest.TestCase):
    def test_cross_slice_no_topology_mutation(self):
        # Import topology helpers and freeze a small canonicalize result
        from utils.discovery_graph import canonicalize_discovery_graph

        nodes = [{'id': 'A'}, {'id': 'B'}]
        edges = [{
            'from': 'A',
            'to': 'B',
            'f_port': 'Gi1/0/1',
            't_port': 'Gi1/0/2',
            'protocol': 'lldp',
        }]
        before = canonicalize_discovery_graph(
            copy.deepcopy(nodes), copy.deepcopy(edges),
        )

        pipe = _pipeline_three_families()
        _assert_no_topology_keys(pipe['iosxe'])
        _assert_no_topology_keys(pipe['snap'])
        for s in pipe['snap']['series']:
            self.assertNotIn('edges', s)
            self.assertNotIn('trust_tier', s)
            self.assertNotIn('relation_key', s)

        after = canonicalize_discovery_graph(
            copy.deepcopy(nodes), copy.deepcopy(edges),
        )
        self.assertEqual(before, after)

        # Telemetry must not invent link/cable claims on observations
        for key in ('cable', 'link', 'neighbor', 'edges'):
            self.assertNotIn(key, pipe['iosxe'])
            self.assertNotIn(key, pipe['nxos'])
            self.assertNotIn(key, pipe['junos'])


class TestCrossSliceDeterminism(unittest.TestCase):
    def test_cross_slice_determinism(self):
        gen = '2026-08-20T21:00:00Z'
        a = _pipeline_three_families(generated_at=gen)
        b = _pipeline_three_families(generated_at=gen)

        self.assertEqual(a['iosxe']['catalog_status'], b['iosxe']['catalog_status'])
        self.assertEqual(a['nxos']['observation_id'], b['nxos']['observation_id'])
        self.assertEqual(a['junos']['metric_name'], b['junos']['metric_name'])

        qa = a['store'].query()
        qb = b['store'].query()
        self.assertEqual(
            [r['observation_id'] for r in qa],
            [r['observation_id'] for r in qb],
        )

        # Delta determinism on identical counter pairs
        c0, c1 = _counter_pair_from_iosxe(10, 25)
        d1 = compute_delta(c0, c1)
        d2 = compute_delta(copy.deepcopy(c0), copy.deepcopy(c1))
        self.assertEqual(d1, d2)

        self.assertEqual(a['snap'], b['snap'])
        self.assertEqual(a['json'], b['json'])
        self.assertEqual(a['json'], snapshot_to_json(json.loads(a['json'])))

        # Batch normalize path remains stable
        batch1 = normalize_batch([
            _fix('iosxe_interface_counters.json'),
            _fix('nxos_interface_counters.json'),
            _fix('junos_interface_optics.json'),
        ], received_at='2026-08-20T20:00:00Z')
        batch2 = normalize_batch([
            _fix('iosxe_interface_counters.json'),
            _fix('nxos_interface_counters.json'),
            _fix('junos_interface_optics.json'),
        ], received_at='2026-08-20T20:00:00Z')
        self.assertEqual(
            [o['observation_id'] for o in batch1['accepted']],
            [o['observation_id'] for o in batch2['accepted']],
        )
        self.assertEqual(len(batch1['accepted']), 3)

        # series_key stability across copies
        for obs in (a['iosxe'], a['nxos'], a['junos']):
            self.assertEqual(series_key(obs), series_key(copy.deepcopy(obs)))


if __name__ == '__main__':
    unittest.main()
