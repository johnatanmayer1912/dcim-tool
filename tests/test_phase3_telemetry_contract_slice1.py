"""Phase 3 slice 1 — streaming telemetry observation contract (fixture-only).

No live gRPC/SSH/NETCONF. No topology mutation. No secret retention.
"""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.telemetry import (
    UNKNOWN,
    compute_observation_id,
    empty_observation,
    load_fixture_json,
    normalize_batch,
    normalize_observation,
    observation_field_names,
)
from utils.telemetry.contract import assert_no_secrets_in_observation

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'telemetry')


def _fix(name: str):
    return load_fixture_json(os.path.join(FIX, name))


class TestTelemetryContractShape(unittest.TestCase):
    def test_empty_observation_has_all_fields(self):
        obs = empty_observation()
        for key in observation_field_names():
            self.assertIn(key, obs)
        self.assertIsNone(obs['source_timestamp'])
        self.assertIsNone(obs['received_at'])
        self.assertEqual(obs['device_id'], UNKNOWN)

    def test_identity_deterministic(self):
        a = normalize_observation(_fix('iosxe_interface_counters.json'))
        b = normalize_observation(_fix('iosxe_interface_counters.json'))
        self.assertEqual(a['observation_id'], b['observation_id'])
        self.assertEqual(a['observation_id'], compute_observation_id(a))


class TestVendorFixtures(unittest.TestCase):
    def test_iosxe_fixture(self):
        obs = normalize_observation(_fix('iosxe_interface_counters.json'))
        self.assertFalse(obs['quarantined'])
        self.assertEqual(obs['platform'], 'cisco_xe')
        self.assertEqual(obs['vendor'], 'cisco')
        self.assertEqual(obs['device_id'], 'edge-xe-01')
        self.assertEqual(obs['value'], 1048576)
        self.assertEqual(obs['value_type'], 'int')
        self.assertEqual(obs['unit'], 'octets')
        self.assertEqual(obs['source_timestamp'], '2026-08-20T18:00:00Z')
        self.assertIsNone(obs['received_at'])
        self.assertIn('GigabitEthernet1/0/1', obs['entity_path'])
        self.assertNotEqual(obs['metric_path'], UNKNOWN)
        self.assertEqual(obs['sequence'], 42)

    def test_nxos_fixture(self):
        obs = normalize_observation(_fix('nxos_interface_counters.json'))
        self.assertFalse(obs['quarantined'])
        self.assertEqual(obs['platform'], 'cisco_nxos')
        self.assertEqual(obs['value'], 2048)
        self.assertEqual(obs['value_type'], 'int')
        self.assertEqual(obs['source_timestamp'], '2026-08-20T18:01:00Z')
        self.assertEqual(obs['entity_path'], 'Ethernet1/1')
        self.assertIn('inOctets', obs['metric_path'])

    def test_junos_fixture(self):
        obs = normalize_observation(_fix('junos_interface_optics.json'))
        self.assertFalse(obs['quarantined'])
        self.assertEqual(obs['platform'], 'juniper_junos')
        self.assertEqual(obs['vendor'], 'juniper')
        self.assertEqual(obs['value'], -3.45)
        self.assertEqual(obs['value_type'], 'float')
        self.assertEqual(obs['unit'], 'dBm')
        self.assertEqual(obs['metric_name'], 'rx-power')
        self.assertEqual(obs['entity_path'], 'xe-0/0/0')
        self.assertTrue(str(obs['metric_path_raw']).startswith('/interfaces'))


class TestTimestampSemantics(unittest.TestCase):
    def test_missing_source_timestamp_explicit_unknown(self):
        obs = normalize_observation(_fix('missing_timestamp.json'))
        self.assertIsNone(obs['source_timestamp'])
        self.assertIsNone(obs['received_at'])
        self.assertEqual(obs['quality'], UNKNOWN)
        self.assertTrue(any('source_timestamp' in n for n in obs['notes']))

    def test_received_at_only_when_collector_supplies(self):
        raw = _fix('iosxe_interface_counters.json')
        without = normalize_observation(raw)
        self.assertIsNone(without['received_at'])
        with_rx = normalize_observation(raw, received_at='2026-08-20T18:10:00Z')
        self.assertEqual(with_rx['received_at'], '2026-08-20T18:10:00Z')
        # Source time unchanged / not invented from receipt
        self.assertEqual(with_rx['source_timestamp'], '2026-08-20T18:00:00Z')
        self.assertNotEqual(with_rx['source_timestamp'], with_rx['received_at'])

    def test_never_invents_source_timestamp_from_received_at(self):
        obs = normalize_observation(
            {'hostname': 'x', 'path': 'a/b', 'value': 1},
            received_at='2026-08-20T19:00:00Z',
        )
        self.assertIsNone(obs['source_timestamp'])
        self.assertEqual(obs['received_at'], '2026-08-20T19:00:00Z')


class TestMalformedSecretsDuplicates(unittest.TestCase):
    def test_malformed_value_quarantined(self):
        obs = normalize_observation(_fix('malformed_value.json'))
        self.assertTrue(obs['quarantined'])
        self.assertEqual(obs['quality'], 'error')
        self.assertIsNone(obs['value'])
        # Source timestamp still preserved when present
        self.assertEqual(obs['source_timestamp'], '2026-08-20T18:03:00Z')

    def test_unknown_metric_quarantined(self):
        obs = normalize_observation(_fix('unknown_metric.json'))
        self.assertTrue(obs['quarantined'])
        self.assertEqual(obs['metric_name'], UNKNOWN)

    def test_secrets_rejected_not_copied(self):
        obs = normalize_observation(_fix('with_secrets.json'))
        self.assertTrue(obs['quarantined'])
        blob = json.dumps(obs)
        self.assertNotIn('should-never-normalize', blob)
        self.assertNotIn('abc123', blob)
        self.assertNotIn('password', obs)
        self.assertNotIn('token', obs)
        assert_no_secrets_in_observation(obs)
        self.assertTrue(any('secret' in w.lower() for w in obs['warnings']))

    def test_duplicate_first_wins(self):
        batch = normalize_batch(_fix('duplicate_pair.json'))
        self.assertEqual(batch['count_in'], 2)
        self.assertEqual(batch['count_accepted'], 1)
        self.assertEqual(batch['count_quarantined'], 1)
        self.assertEqual(batch['accepted'][0]['value'], 10)
        dup = batch['quarantined'][0]
        self.assertEqual(dup['duplicate_of'], batch['accepted'][0]['observation_id'])
        self.assertTrue(dup['quarantined'])

    def test_batch_isolates_malformed(self):
        payloads = [
            _fix('iosxe_interface_counters.json'),
            _fix('malformed_value.json'),
            _fix('junos_interface_optics.json'),
        ]
        batch = normalize_batch(payloads, received_at='2026-08-20T20:00:00Z')
        self.assertEqual(batch['count_accepted'], 2)
        self.assertEqual(batch['count_quarantined'], 1)
        for obs in batch['accepted']:
            self.assertEqual(obs['received_at'], '2026-08-20T20:00:00Z')
            self.assertFalse(obs['quarantined'])


class TestTopologyNonGoals(unittest.TestCase):
    def test_does_not_create_topology_edges_or_trust(self):
        obs = normalize_observation(_fix('iosxe_interface_counters.json'))
        # Neutral entity reference only — not cable proof fields
        self.assertNotIn('trust_tier', obs)
        self.assertNotIn('from', obs)
        self.assertNotIn('to', obs)
        self.assertNotIn('f_port', obs)
        self.assertNotIn('not_physical', obs)
        self.assertEqual(obs['entity_path'], 'GigabitEthernet1/0/1')

    def test_non_object_payload_quarantined(self):
        obs = normalize_observation('not-json-object')
        self.assertTrue(obs['quarantined'])
        self.assertEqual(obs['quality'], 'error')


if __name__ == '__main__':
    unittest.main()
