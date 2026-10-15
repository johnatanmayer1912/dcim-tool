"""Phase 3 slice 2 — fixture-only metric catalog / path registry.

No live transport. No topology mutation. No secret retention.
"""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.telemetry import (
    UNKNOWN,
    apply_catalog_to_observation,
    load_fixture_json,
    lookup_metric,
    normalize_observation,
)
from utils.telemetry.catalog import (
    STATUS_AMBIGUOUS,
    STATUS_INVALID,
    STATUS_KNOWN,
    STATUS_UNKNOWN,
    get_catalog_entries,
)
from utils.telemetry.contract import assert_no_secrets_in_observation

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'telemetry')


def _fix(name: str):
    return load_fixture_json(os.path.join(FIX, name))


class TestCatalogLookup(unittest.TestCase):
    def test_exact_known_iosxe(self):
        r = lookup_metric(
            'Cisco-IOS-XE-interfaces-oper:interfaces/interface/statistics/in-octets',
            platform='cisco_xe',
        )
        self.assertEqual(r['status'], STATUS_KNOWN)
        self.assertEqual(r['entry']['entry_id'], 'iosxe.if.in_octets')
        self.assertEqual(r['entry']['unit'], 'octets')
        self.assertEqual(r['entry']['metric_kind'], 'counter')
        self.assertEqual(r['entry']['entity_kind'], 'interface')

    def test_vendor_specific_precedence_and_other_platform_unknown(self):
        path = 'Cisco-IOS-XE-interfaces-oper:interfaces/interface/statistics/in-octets'
        self.assertEqual(lookup_metric(path, platform='cisco_xe')['status'], STATUS_KNOWN)
        # Same path on NX-OS is not a catalog hit for that platform
        other = lookup_metric(path, platform='cisco_nxos')
        self.assertEqual(other['status'], STATUS_UNKNOWN)
        self.assertTrue(other['matches'])  # known elsewhere

    def test_unknown_path(self):
        r = lookup_metric('totally/unknown/sensor', platform='cisco_xe')
        self.assertEqual(r['status'], STATUS_UNKNOWN)
        self.assertIsNone(r['entry'])

    def test_ambiguous_path(self):
        r = lookup_metric('test/ambiguous/sensor', platform='cisco_xe')
        self.assertEqual(r['status'], STATUS_AMBIGUOUS)
        self.assertIsNone(r['entry'])
        self.assertEqual(sorted(r['matches']), ['test.ambiguous.a', 'test.ambiguous.b'])

    def test_malformed_empty_path(self):
        r = lookup_metric('', platform='cisco_xe')
        self.assertEqual(r['status'], STATUS_INVALID)

    def test_secret_like_path_rejected(self):
        r = lookup_metric('interfaces/password/hash', platform='cisco_xe')
        self.assertEqual(r['status'], STATUS_INVALID)
        blob = json.dumps(r)
        self.assertNotIn('hunter2', blob)
        self.assertTrue(any('secret' in w.lower() for w in r['warnings']))

    def test_deterministic(self):
        a = lookup_metric(
            'sys/intf/phys-[eth1/1]/dbgStats/inOctets', platform='cisco_nxos',
        )
        b = lookup_metric(
            'sys/intf/phys-[eth1/1]/dbgStats/inOctets', platform='cisco_nxos',
        )
        self.assertEqual(a, b)


class TestNormalizeCatalogIntegration(unittest.TestCase):
    def test_three_fixture_families_known(self):
        iosxe = normalize_observation(_fix('iosxe_interface_counters.json'))
        nxos = normalize_observation(_fix('nxos_interface_counters.json'))
        junos = normalize_observation(_fix('junos_interface_optics.json'))
        self.assertEqual(iosxe['catalog_status'], STATUS_KNOWN)
        self.assertEqual(iosxe['catalog_entry_id'], 'iosxe.if.in_octets')
        self.assertEqual(iosxe['metric_kind'], 'counter')
        self.assertEqual(nxos['catalog_status'], STATUS_KNOWN)
        self.assertEqual(nxos['unit'], 'bytes')  # source retained; matches catalog
        self.assertEqual(junos['catalog_status'], STATUS_KNOWN)
        self.assertEqual(junos['metric_kind'], 'gauge')
        self.assertEqual(junos['entity_kind'], 'interface')
        for obs in (iosxe, nxos, junos):
            self.assertIsNotNone(obs['source_timestamp'])
            assert_no_secrets_in_observation(obs)

    def test_out_octets_missing_timestamp_still_known_catalog(self):
        obs = normalize_observation(_fix('missing_timestamp.json'))
        self.assertEqual(obs['catalog_status'], STATUS_KNOWN)
        self.assertEqual(obs['catalog_entry_id'], 'iosxe.if.out_octets')
        self.assertIsNone(obs['source_timestamp'])
        self.assertEqual(obs['quality'], UNKNOWN)

    def test_unit_conflict_keeps_source(self):
        raw = dict(_fix('iosxe_interface_counters.json'))
        raw['unit'] = 'packets'
        obs = normalize_observation(raw)
        self.assertEqual(obs['unit'], 'packets')
        self.assertTrue(any('unit conflict' in w for w in obs['warnings']))
        self.assertEqual(obs['catalog_status'], STATUS_KNOWN)

    def test_value_type_conflict_keeps_source(self):
        # Force float value while catalog expects int
        raw = dict(_fix('iosxe_interface_counters.json'))
        raw['value'] = 1.5
        obs = normalize_observation(raw)
        self.assertEqual(obs['value_type'], 'float')
        self.assertTrue(any('value_type conflict' in w for w in obs['warnings']))

    def test_ambiguous_via_normalize(self):
        obs = normalize_observation({
            'platform': 'cisco_xe',
            'hostname': 'lab',
            'path': 'test/ambiguous/sensor',
            'value': 1,
            'timestamp': '2026-08-20T18:00:00Z',
        })
        self.assertEqual(obs['catalog_status'], STATUS_AMBIGUOUS)
        self.assertIsNone(obs['catalog_entry_id'])
        self.assertEqual(sorted(obs['catalog_matches']), ['test.ambiguous.a', 'test.ambiguous.b'])

    def test_unknown_path_status(self):
        obs = normalize_observation({
            'platform': 'cisco_xe',
            'hostname': 'lab',
            'path': 'no/such/metric',
            'value': 1,
            'timestamp': '2026-08-20T18:00:00Z',
        })
        self.assertEqual(obs['catalog_status'], STATUS_UNKNOWN)
        self.assertFalse(obs['quarantined'])

    def test_legacy_fields_intact(self):
        obs = normalize_observation(_fix('iosxe_interface_counters.json'))
        for key in (
            'observation_id', 'device_id', 'source_timestamp', 'received_at',
            'metric_path_raw', 'quarantined', 'duplicate_of',
        ):
            self.assertIn(key, obs)
        self.assertIsNone(obs['received_at'])
        self.assertFalse(obs['quarantined'])

    def test_no_topology_mutation_fields(self):
        obs = normalize_observation(_fix('junos_interface_optics.json'))
        for banned in ('trust_tier', 'from', 'to', 'f_port', 'not_physical', 'evidence'):
            self.assertNotIn(banned, obs)

    def test_apply_catalog_standalone(self):
        obs = {
            'platform': 'juniper_junos',
            'metric_path_raw': "/interfaces/interface[name='xe-0/0/0']/optics/rx-power",
            'metric_path': "/interfaces/interface[name='xe-0/0/0']/optics/rx-power",
            'metric_name': UNKNOWN,
            'unit': UNKNOWN,
            'value_type': 'float',
            'entity_path': 'xe-0/0/0',
            'warnings': [],
            'notes': [],
        }
        out = apply_catalog_to_observation(obs)
        self.assertEqual(out['catalog_status'], STATUS_KNOWN)
        self.assertEqual(out['metric_name'], 'optics_rx_power')
        self.assertEqual(out['unit'], 'dBm')

    def test_catalog_has_no_secrets(self):
        blob = json.dumps(list(get_catalog_entries()))
        for needle in ('password', 'token', 'private_key', 'community'):
            self.assertNotIn(needle, blob)


if __name__ == '__main__':
    unittest.main()
