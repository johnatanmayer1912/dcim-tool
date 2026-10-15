"""Phase 4 — lab-only localhost telemetry ingest prototype tests.

In-process adapter only. No sockets, persistence, topology, or production auth.
"""
from __future__ import annotations

import copy
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.telemetry import ObservationStore, load_fixture_json, normalize_observation
from utils.telemetry.lab_ingest import (
    KIND_COLLECTOR,
    KIND_OPERATOR,
    LabAuthContext,
    LabStubPrincipal,
    LabTelemetryIngestor,
    PERM_EXPORT,
    PERM_INGEST,
    PERM_READ,
    STATUS_ACTIVE,
    assert_loopback_bind_host,
    build_lab_ingestor,
    default_lab_auth_context,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'telemetry')

FROZEN_PACKAGE_EXPORTS = (
    'UNKNOWN',
    'compute_observation_id',
    'empty_observation',
    'observation_field_names',
    'load_fixture_json',
    'normalize_batch',
    'normalize_observation',
    'lookup_metric',
    'apply_catalog_to_observation',
    'ObservationStore',
    'compute_delta',
    'latest_delta',
    'pairwise_deltas',
    'same_series',
    'series_key',
    'export_series_snapshot',
    'snapshot_to_json',
)


def _fix(name: str):
    return load_fixture_json(os.path.join(FIX, name))


def _lab(**kwargs) -> LabTelemetryIngestor:
    kwargs.setdefault('lab_mode', True)
    return LabTelemetryIngestor(**kwargs)


class TestLabModeAndBinding(unittest.TestCase):
    def test_explicit_lab_mode_required(self):
        with self.assertRaises(ValueError):
            LabTelemetryIngestor()
        with self.assertRaises(ValueError):
            LabTelemetryIngestor(lab_mode=False)
        with self.assertRaises(ValueError):
            build_lab_ingestor(lab_mode=True, disable_lab_mode=True)
        ing = _lab()
        self.assertTrue(ing.lab_mode)

    def test_loopback_only_configuration(self):
        self.assertEqual(assert_loopback_bind_host('127.0.0.1'), '127.0.0.1')
        self.assertEqual(assert_loopback_bind_host('::1'), '::1')
        for bad in ('0.0.0.0', '::', '*', '192.168.1.1', '10.0.0.5', '8.8.8.8'):
            with self.assertRaises(ValueError):
                assert_loopback_bind_host(bad)
            with self.assertRaises(ValueError):
                _lab(bind_host=bad)

    def test_persistence_topology_raw_refused(self):
        with self.assertRaises(ValueError):
            _lab(enable_persistence=True)
        with self.assertRaises(ValueError):
            _lab(enable_topology_integration=True)
        with self.assertRaises(ValueError):
            _lab(enable_raw_payload_output=True)

    def test_no_implicit_server_startup(self):
        ing = _lab()
        self.assertFalse(ing.ready)
        self.assertFalse(ing.network_started)
        ing.start()
        self.assertTrue(ing.ready)
        self.assertFalse(ing.network_started)
        with self.assertRaises(RuntimeError):
            ing.start_network_listener()
        self.assertFalse(ing.network_started)


class TestAuthnAuthzDefaultDeny(unittest.TestCase):
    def test_missing_and_unknown_principal_rejected(self):
        ing = _lab()
        payload = _fix('iosxe_interface_counters.json')
        r = ing.ingest(payload)
        self.assertFalse(r.ok)
        self.assertEqual(r.status, 'authn_failed')
        self.assertNotIn('stub-', r.reason)

        r2 = ing.ingest(
            payload,
            principal_id='no-such-principal',
            stub_token_id='stub-collector-token-a',
        )
        self.assertFalse(r2.ok)
        self.assertEqual(r2.status, 'authn_failed')

    def test_revoked_and_expired_stub_rejected(self):
        ing = _lab()
        payload = _fix('iosxe_interface_counters.json')
        for pid, tok in (
            ('lab-collector-expired', 'stub-expired'),
            ('lab-collector-revoked', 'stub-revoked'),
        ):
            r = ing.ingest(payload, principal_id=pid, stub_token_id=tok)
            self.assertFalse(r.ok)
            self.assertEqual(r.status, 'authn_failed')

    def test_token_mismatch_rejected_without_echo(self):
        ing = _lab()
        secret = 'super-secret-token-value'
        r = ing.ingest(
            _fix('iosxe_interface_counters.json'),
            principal_id='lab-collector-a',
            stub_token_id=secret,
        )
        self.assertFalse(r.ok)
        self.assertNotIn(secret, r.reason)
        self.assertNotIn(secret, r.to_dict()['reason'])

    def test_missing_permission_and_unknown_permission(self):
        ctx = LabAuthContext(principals=(
            LabStubPrincipal(
                principal_id='lab-collector-noperm',
                kind=KIND_COLLECTOR,
                permissions=frozenset(),
                device_scope=frozenset({'edge-xe-01'}),
                status=STATUS_ACTIVE,
                stub_token_id='tok-noperm',
            ),
            LabStubPrincipal(
                principal_id='lab-operator-a',
                kind=KIND_OPERATOR,
                permissions=frozenset({PERM_READ, PERM_EXPORT}),
                status=STATUS_ACTIVE,
                stub_token_id='stub-operator-token-a',
            ),
        ))
        ing = _lab(auth_context=ctx)
        r = ing.ingest(
            _fix('iosxe_interface_counters.json'),
            principal_id='lab-collector-noperm',
            stub_token_id='tok-noperm',
        )
        self.assertFalse(r.ok)
        self.assertEqual(r.status, 'authz_denied')

        # Unknown permission name is always denied
        p = ctx.get('lab-collector-noperm')
        self.assertIsNotNone(p)
        err, rc = ing._authorize(p, 'telemetry_admin')
        self.assertEqual(err, 'authorization denied')
        self.assertEqual(rc, 'UNKNOWN_PERMISSION')
        err2, rc2 = ing._authorize(p, 'not_a_real_permission')
        self.assertEqual(err2, 'authorization denied')
        self.assertEqual(rc2, 'UNKNOWN_PERMISSION')

    def test_collector_cannot_snapshot_operator_cannot_ingest(self):
        ing = _lab()
        payload = _fix('iosxe_interface_counters.json')
        # operator ingest denied (wrong kind → authn fail for collector path)
        r = ing.ingest(
            payload,
            principal_id='lab-operator-a',
            stub_token_id='stub-operator-token-a',
        )
        self.assertFalse(r.ok)
        self.assertEqual(r.status, 'authn_failed')

        # collector snapshot denied
        snap = ing.snapshot(
            principal_id='lab-collector-a',
            stub_token_id='stub-collector-token-a',
            generated_at='2026-08-20T21:00:00Z',
        )
        self.assertFalse(snap['ok'])
        self.assertEqual(snap['status'], 'authn_failed')

    def test_cross_device_scope_rejected(self):
        ctx = LabAuthContext(principals=(
            LabStubPrincipal(
                principal_id='lab-collector-narrow',
                kind=KIND_COLLECTOR,
                permissions=frozenset({PERM_INGEST}),
                device_scope=frozenset({'leaf-nx-01'}),
                status=STATUS_ACTIVE,
                stub_token_id='tok-narrow',
            ),
        ))
        ing = _lab(auth_context=ctx)
        r = ing.ingest(
            _fix('iosxe_interface_counters.json'),  # edge-xe-01
            principal_id='lab-collector-narrow',
            stub_token_id='tok-narrow',
        )
        self.assertFalse(r.ok)
        self.assertEqual(r.status, 'authz_denied')

    def test_topology_and_raw_export_denied(self):
        ing = _lab()
        self.assertFalse(ing.topology_access()['ok'])
        self.assertFalse(ing.export_raw_payloads()['ok'])


class TestIngestPipeline(unittest.TestCase):
    def test_fixture_accepted_through_pipeline_and_snapshot(self):
        ing = _lab()
        r = ing.ingest(
            _fix('iosxe_interface_counters.json'),
            principal_id='lab-collector-a',
            stub_token_id='stub-collector-token-a',
            received_at='2026-08-20T19:00:00Z',
        )
        self.assertTrue(r.ok)
        self.assertEqual(r.status, 'inserted')
        self.assertEqual(r.device_id, 'edge-xe-01')
        self.assertEqual(r.catalog_status, 'known')

        out = ing.snapshot(
            principal_id='lab-operator-a',
            stub_token_id='stub-operator-token-a',
            generated_at='2026-08-20T21:00:00Z',
        )
        self.assertTrue(out['ok'])
        snap = out['snapshot']
        self.assertEqual(snap['series_count'], 1)
        s = snap['series'][0]
        self.assertEqual(s['latest_value'], 1048576)
        self.assertEqual(s['latest_source_timestamp'], '2026-08-20T18:00:00Z')
        self.assertEqual(s['latest_received_at'], '2026-08-20T19:00:00Z')
        self.assertEqual(snap['generated_at'], '2026-08-20T21:00:00Z')
        blob = out['json']
        self.assertNotIn('raw_payload', blob)
        self.assertNotIn('password', blob.lower())

    def test_malformed_and_secret_rejected(self):
        ing = _lab()
        bad = ing.ingest(
            _fix('malformed_value.json'),
            principal_id='lab-collector-a',
            stub_token_id='stub-collector-token-a',
        )
        self.assertFalse(bad.ok)
        self.assertEqual(bad.status, 'quarantined')

        sec = ing.ingest(
            _fix('with_secrets.json'),
            principal_id='lab-collector-a',
            stub_token_id='stub-collector-token-a',
        )
        self.assertFalse(sec.ok)
        self.assertEqual(sec.status, 'quarantined')
        self.assertNotIn('should-never-normalize', sec.reason)
        self.assertNotIn('abc123', json.dumps(sec.to_dict()))

        # Raw protocol keys rejected
        raw = ing.ingest(
            {'hostname': 'edge-xe-01', 'raw_cli': 'show run', 'value': 1,
             'sensor_path': 'x', 'timestamp': '2026-08-20T18:00:00Z'},
            principal_id='lab-collector-a',
            stub_token_id='stub-collector-token-a',
        )
        self.assertFalse(raw.ok)

    def test_duplicate_first_wins_and_no_timestamp_invention(self):
        ing = _lab()
        p = _fix('iosxe_interface_counters.json')
        a = ing.ingest(
            p, principal_id='lab-collector-a', stub_token_id='stub-collector-token-a',
        )
        b = ing.ingest(
            copy.deepcopy(p),
            principal_id='lab-collector-a',
            stub_token_id='stub-collector-token-a',
        )
        self.assertEqual(a.status, 'inserted')
        self.assertEqual(b.status, 'duplicate')
        self.assertEqual(a.observation_id, b.observation_id)
        self.assertEqual(ing.store_stats()['stored'], 1)

        # Without received_at, contract leaves it unset / None — not wall clock
        r = normalize_observation(_fix('iosxe_interface_counters.json'))
        self.assertIsNone(r.get('received_at'))

    def test_snapshot_deterministic_and_in_memory_only(self):
        ing = _lab()
        for name in (
            'iosxe_interface_counters.json',
            'nxos_interface_counters.json',
            'junos_interface_optics.json',
        ):
            r = ing.ingest(
                _fix(name),
                principal_id='lab-collector-a',
                stub_token_id='stub-collector-token-a',
            )
            self.assertTrue(r.ok, r)

        gen = '2026-08-20T21:00:00Z'
        s1 = ing.snapshot(
            principal_id='lab-operator-a',
            stub_token_id='stub-operator-token-a',
            generated_at=gen,
        )
        s2 = ing.snapshot(
            principal_id='lab-operator-a',
            stub_token_id='stub-operator-token-a',
            generated_at=gen,
        )
        self.assertEqual(s1['snapshot'], s2['snapshot'])
        self.assertEqual(s1['json'], s2['json'])
        self.assertIsInstance(ing._store, ObservationStore)
        self.assertEqual(ing.store_stats()['stored'], 3)

    def test_no_topology_fields_or_mutations(self):
        from utils.discovery_graph import canonicalize_discovery_graph

        nodes = [{'id': 'A'}, {'id': 'B'}]
        edges = [{
            'from': 'A', 'to': 'B',
            'f_port': 'Gi1/0/1', 't_port': 'Gi1/0/2', 'protocol': 'lldp',
        }]
        before = canonicalize_discovery_graph(copy.deepcopy(nodes), copy.deepcopy(edges))

        ing = _lab()
        ing.ingest(
            _fix('iosxe_interface_counters.json'),
            principal_id='lab-collector-a',
            stub_token_id='stub-collector-token-a',
        )
        out = ing.snapshot(
            principal_id='lab-operator-a',
            stub_token_id='stub-operator-token-a',
            generated_at='2026-08-20T21:00:00Z',
        )
        blob = json.dumps(out['snapshot'])
        for needle in ('trust_tier', 'relation_key', 'not_physical', 'cable'):
            self.assertNotIn(needle, blob)
        self.assertFalse(ing.topology_access()['ok'])

        after = canonicalize_discovery_graph(copy.deepcopy(nodes), copy.deepcopy(edges))
        self.assertEqual(before, after)


class TestPhase3AndGateUnchanged(unittest.TestCase):
    def test_phase3_package_exports_unchanged(self):
        import utils.telemetry as tel

        self.assertEqual(tuple(tel.__all__), FROZEN_PACKAGE_EXPORTS)
        self.assertFalse(hasattr(tel, 'LabTelemetryIngestor') and 'LabTelemetryIngestor' in tel.__all__)

    def test_phase4_zero_trust_gate_intact(self):
        path = os.path.join(ROOT, 'docs', 'telemetry', 'PHASE4_ZERO_TRUST_GATE.md')
        self.assertTrue(os.path.isfile(path))
        text = open(path, encoding='utf-8').read()
        self.assertIn('## 10. Decision gates', text)
        self.assertIn('Gate A', text)
        self.assertIn('default-deny', text.lower())

    def test_lab_module_not_auto_imported_as_transport(self):
        import utils.telemetry.lab_ingest as lab

        self.assertFalse(lab.LabTelemetryIngestor(lab_mode=True).network_started)
        self.assertIn('Lab-only', lab.__doc__ or '')


if __name__ == '__main__':
    unittest.main()
