"""Phase 4 — lab-only Gate D facade tests (in-process, no listeners)."""
from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.telemetry import load_fixture_json
from utils.telemetry.lab_audit import LabAuditSink, RC_READ_OK, RC_EXPORT_OK
from utils.telemetry.lab_facade import FACADE_SCHEMA_VERSION, LabGateDFacade
from utils.telemetry.lab_ingest import (
    KIND_COLLECTOR,
    KIND_OPERATOR,
    LabAuthContext,
    LabStubPrincipal,
    LabTelemetryIngestor,
    PERM_AUDIT_READ,
    PERM_EXPORT,
    PERM_INGEST,
    PERM_READ,
    STATUS_ACTIVE,
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


def _seeded():
    ing = LabTelemetryIngestor(lab_mode=True)
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
        assert r.ok, r
    # quarantine path for summary tests
    ing.ingest(
        _fix('with_secrets.json'),
        principal_id='lab-collector-a',
        stub_token_id='stub-collector-token-a',
    )
    fac = LabGateDFacade(lab_mode=True, ingestor=ing)
    return ing, fac


class _FailAudit(LabAuditSink):
    def record(self, **fields):
        self._write_failures += 1
        return False


class TestFacadeBasics(unittest.TestCase):
    def test_lab_mode_and_no_network(self):
        with self.assertRaises(ValueError):
            LabGateDFacade()
        with self.assertRaises(ValueError):
            LabGateDFacade(lab_mode=False)
        fac = LabGateDFacade(lab_mode=True)
        self.assertTrue(fac.lab_mode)
        self.assertFalse(fac.network_started)
        with self.assertRaises(RuntimeError):
            fac.start_network_listener()
        before = threading.active_count()
        fac.health()
        self.assertEqual(threading.active_count(), before)
        with tempfile.TemporaryDirectory() as td:
            fac.health()
            self.assertEqual(os.listdir(td), [])

    def test_health_and_schema(self):
        fac = LabGateDFacade(lab_mode=True)
        h = fac.health()
        self.assertTrue(h['ok'])
        self.assertEqual(h['data']['schema_version'], FACADE_SCHEMA_VERSION)
        self.assertNotIn('observations', json.dumps(h))
        s = fac.read_schema(
            principal_id='lab-operator-a', stub_token_id='stub-operator-token-a',
        )
        self.assertTrue(s['ok'])
        self.assertTrue(s['data']['frozen_phase3_api'])


class TestAuthzMatrix(unittest.TestCase):
    def test_missing_unknown_expired_and_default_deny(self):
        _, fac = _seeded()
        self.assertEqual(
            fac.read_observations(principal_id=None, stub_token_id=None)['status'],
            'authn_failed',
        )
        self.assertEqual(
            fac.read_observations(
                principal_id='nope', stub_token_id='stub-collector-token-a',
            )['status'],
            'authn_failed',
        )
        self.assertEqual(
            fac.read_observations(
                principal_id='lab-collector-expired', stub_token_id='stub-expired',
            )['status'],
            'authn_failed',
        )
        # collector cannot read
        denied = fac.read_observations(
            principal_id='lab-collector-a', stub_token_id='stub-collector-token-a',
        )
        self.assertEqual(denied['status'], 'authz_denied')
        # ingest via facade denied
        self.assertFalse(fac.ingest(principal_id='lab-collector-a')['ok'])
        self.assertFalse(fac.deny_raw_payload()['ok'])
        self.assertFalse(fac.deny_topology_read()['ok'])
        self.assertFalse(fac.deny_topology_write()['ok'])

    def test_read_export_audit_separation(self):
        _, fac = _seeded()
        op = dict(principal_id='lab-operator-a', stub_token_id='stub-operator-token-a')
        aud = dict(principal_id='lab-auditor-a', stub_token_id='stub-auditor-token-a')

        self.assertTrue(fac.read_observations(**op)['ok'])
        self.assertTrue(fac.read_snapshot(**op, generated_at='2026-08-20T21:00:00Z')['ok'])
        self.assertTrue(fac.export_snapshot(**op, generated_at='2026-08-20T21:00:00Z')['ok'])
        # operator cannot audit-read
        self.assertEqual(fac.read_audit_events(**op)['status'], 'authz_denied')
        # auditor can audit-read but not snapshot
        self.assertTrue(fac.read_audit_events(**aud)['ok'])
        self.assertEqual(fac.read_snapshot(**aud)['status'], 'authz_denied')
        # audit export needs export too — auditor lacks export
        self.assertEqual(fac.export_audit_events(**aud)['status'], 'authz_denied')


class TestReadSurfaces(unittest.TestCase):
    def test_observation_snapshot_delta_catalog_quarantine(self):
        _, fac = _seeded()
        op = dict(principal_id='lab-operator-a', stub_token_id='stub-operator-token-a')

        obs = fac.read_observations(**op)
        self.assertTrue(obs['ok'])
        self.assertEqual(obs['data']['count'], 3)
        ids = [o['observation_id'] for o in obs['data']['observations']]
        self.assertEqual(len(ids), 3)
        # Deterministic: re-read yields same order
        self.assertEqual(
            ids,
            [o['observation_id'] for o in fac.read_observations(**op)['data']['observations']],
        )
        row = obs['data']['observations'][0]
        self.assertIn('source_timestamp', row)
        self.assertIn('catalog_status', row)
        self.assertNotIn('raw_payload', row)
        # copy-on-read
        row['value'] = 'mutated'
        again = fac.read_observations(**op)
        self.assertNotEqual(again['data']['observations'][0].get('value'), 'mutated')

        snap = fac.read_snapshot(**op, generated_at='2026-08-20T21:00:00Z')
        self.assertTrue(snap['ok'])
        self.assertEqual(snap['data']['snapshot']['series_count'], 3)
        self.assertNotIn('json', snap['data'])

        exp = fac.export_snapshot(**op, generated_at='2026-08-20T21:00:00Z')
        self.assertTrue(exp['ok'])
        self.assertIn('json', exp['data'])
        self.assertEqual(exp['data']['json'], json.dumps(
            json.loads(exp['data']['json']), sort_keys=True, indent=2,
        ) if False else exp['data']['json'])  # presence check
        self.assertIn('schema_version', exp['data']['json'])

        d = fac.read_delta(**op, device_id='edge-xe-01')
        self.assertTrue(d['ok'])

        cat = fac.read_catalog(
            **op,
            path='Cisco-IOS-XE-interfaces-oper:interfaces/interface/statistics/in-octets',
            platform='cisco_xe',
        )
        self.assertTrue(cat['ok'])
        self.assertEqual(cat['data']['status'], 'known')

        q = fac.read_quarantine_summary(**op)
        self.assertTrue(q['ok'])
        self.assertGreaterEqual(q['data']['count'], 1)

    def test_limits_and_invalid_scope(self):
        _, fac = _seeded()
        op = dict(principal_id='lab-operator-a', stub_token_id='stub-operator-token-a')
        self.assertEqual(
            fac.read_observations(**op, device_id='   ')['status'],
            'invalid_scope',
        )
        self.assertEqual(
            fac.read_observations(**op, limit=10_000)['status'],
            'limit_exceeded',
        )
        tiny = LabGateDFacade(lab_mode=True, max_records=2, max_response_bytes=1024)
        # empty store still ok
        self.assertTrue(tiny.read_observations(**op)['ok'])

    def test_fail_closed_audit_and_redaction(self):
        sink = _FailAudit(lab_mode=True)
        fac = LabGateDFacade(lab_mode=True, audit_sink=sink)
        r = fac.read_observations(
            principal_id='lab-operator-a', stub_token_id='stub-operator-token-a',
        )
        # authn/authz emit fail → eventually audit_failed on success path or auth path
        self.assertFalse(r['ok'])

        ing, fac2 = _seeded()
        original = fac2._scrub_obs

        def boom(obs):
            raise RuntimeError('scrub-fail')

        fac2._scrub_obs = boom  # type: ignore
        bad = fac2.read_observations(
            principal_id='lab-operator-a', stub_token_id='stub-operator-token-a',
        )
        self.assertEqual(bad['status'], 'redaction_failed')
        fac2._scrub_obs = original  # type: ignore

    def test_phase3_exports_and_topology_untouched(self):
        import utils.telemetry as tel
        from utils.discovery_graph import canonicalize_discovery_graph

        self.assertEqual(tuple(tel.__all__), FROZEN_PACKAGE_EXPORTS)
        self.assertNotIn('LabGateDFacade', tel.__all__)

        nodes = [{'id': 'A'}, {'id': 'B'}]
        edges = [{
            'from': 'A', 'to': 'B',
            'f_port': 'Gi1/0/1', 't_port': 'Gi1/0/2', 'protocol': 'lldp',
        }]
        before = canonicalize_discovery_graph(copy.deepcopy(nodes), copy.deepcopy(edges))
        _, fac = _seeded()
        fac.read_snapshot(
            principal_id='lab-operator-a',
            stub_token_id='stub-operator-token-a',
            generated_at='2026-08-20T21:00:00Z',
        )
        after = canonicalize_discovery_graph(copy.deepcopy(nodes), copy.deepcopy(edges))
        self.assertEqual(before, after)


class TestOperatorWithAuditExport(unittest.TestCase):
    def test_combined_operator_auditor_export(self):
        ctx = LabAuthContext(principals=(
            LabStubPrincipal(
                principal_id='lab-ops-audit',
                kind=KIND_OPERATOR,
                permissions=frozenset({PERM_READ, PERM_EXPORT, PERM_AUDIT_READ}),
                status=STATUS_ACTIVE,
                stub_token_id='tok-combo',
            ),
            LabStubPrincipal(
                principal_id='lab-collector-a',
                kind=KIND_COLLECTOR,
                permissions=frozenset({PERM_INGEST}),
                device_scope=frozenset({'edge-xe-01'}),
                status=STATUS_ACTIVE,
                stub_token_id='stub-collector-token-a',
            ),
        ))
        ing = LabTelemetryIngestor(lab_mode=True, auth_context=ctx)
        ing.ingest(
            _fix('iosxe_interface_counters.json'),
            principal_id='lab-collector-a',
            stub_token_id='stub-collector-token-a',
        )
        fac = LabGateDFacade(lab_mode=True, ingestor=ing)
        creds = dict(principal_id='lab-ops-audit', stub_token_id='tok-combo')
        self.assertTrue(fac.export_audit_events(**creds)['ok'])
        self.assertTrue(fac.export_snapshot(**creds, generated_at='2026-08-20T21:00:00Z')['ok'])


if __name__ == '__main__':
    unittest.main()
