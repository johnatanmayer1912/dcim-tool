"""Phase 4 — lab-only in-memory audit-event sink tests."""
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
from utils.telemetry.lab_audit import (
    EVENT_KEYS,
    ET_AUTHN,
    ET_CONFIG,
    ET_DENY,
    ET_INGEST,
    ET_SNAPSHOT,
    LabAuditSink,
    OUT_DENIED,
    OUT_DUPLICATE,
    OUT_FAILURE,
    OUT_QUARANTINED,
    OUT_REJECTED,
    OUT_SUCCESS,
    RC_AUTHN_OK,
    RC_AUTHZ_DENIED,
    RC_BIND_REFUSED,
    RC_DUPLICATE_FIRST_WINS,
    RC_INGEST_ACCEPTED,
    RC_LAB_MODE_REQUIRED,
    RC_MISSING_PRINCIPAL,
    RC_QUARANTINED,
    RC_RAW_EXPORT_DENIED,
    RC_SECRET_LIKE,
    RC_SNAPSHOT_OK,
    RC_TOKEN_MISMATCH,
    RC_TOPOLOGY_DENIED,
    REDACTED,
    redact_event_fields,
    safe_actor_id,
)
from utils.telemetry.lab_ingest import LabTelemetryIngestor

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


class _FailingSink(LabAuditSink):
    def record(self, **fields):
        self._write_failures += 1
        return False


class TestLabAuditSinkBasics(unittest.TestCase):
    def test_explicit_lab_only_construction(self):
        with self.assertRaises(ValueError):
            LabAuditSink()
        with self.assertRaises(ValueError):
            LabAuditSink(lab_mode=False)
        sink = LabAuditSink(lab_mode=True, max_events=10)
        self.assertTrue(sink.lab_only)

    def test_no_disk_sockets_threads(self):
        sink = LabAuditSink(lab_mode=True, max_events=5)
        before_threads = threading.active_count()
        sink.record(event_type=ET_INGEST, outcome=OUT_SUCCESS, operation='t', reason_code=RC_INGEST_ACCEPTED)
        self.assertEqual(threading.active_count(), before_threads)
        # No new files under a temp cwd marker
        with tempfile.TemporaryDirectory() as td:
            marker = os.path.join(td, 'should_not_appear.json')
            self.assertFalse(os.path.exists(marker))
            sink.record(
                event_type=ET_INGEST, outcome=OUT_SUCCESS, operation='t',
                reason_code=RC_INGEST_ACCEPTED, password='nope', raw_payload={'x': 1},
            )
            self.assertEqual(os.listdir(td), [])

    def test_bounded_eviction_and_order(self):
        sink = LabAuditSink(lab_mode=True, max_events=3)
        for i in range(5):
            sink.record(
                event_type=ET_INGEST,
                outcome=OUT_SUCCESS,
                operation='ingest',
                reason_code=RC_INGEST_ACCEPTED,
                actor_id_safe=f'p{i}',
            )
        rows = sink.query()
        self.assertLessEqual(len(rows), 3)
        self.assertGreater(sink.overflow_count, 0)
        seqs = [r['sequence'] for r in rows]
        self.assertEqual(seqs, sorted(seqs))

    def test_copy_on_read_and_extra_fields_discarded(self):
        sink = LabAuditSink(lab_mode=True)
        sink.record(
            event_type=ET_AUTHN,
            outcome=OUT_FAILURE,
            operation='ingest',
            reason_code=RC_TOKEN_MISMATCH,
            actor_id_safe='lab-collector-a',
            password='secret-value',
            token='tok-value',
            raw_payload={'a': 1},
            authorization='Bearer xyz',
            extra_noise='drop-me',
        )
        rows = sink.query()
        self.assertEqual(len(rows), 1)
        ev = rows[0]
        self.assertEqual(set(ev.keys()), set(EVENT_KEYS))
        blob = json.dumps(ev)
        self.assertNotIn('secret-value', blob)
        self.assertNotIn('tok-value', blob)
        self.assertNotIn('Bearer', blob)
        self.assertNotIn('drop-me', blob)
        self.assertNotIn('raw_payload', blob)
        ev['reason_code'] = 'MUTATED'
        self.assertEqual(sink.query()[0]['reason_code'], RC_TOKEN_MISMATCH)

    def test_redaction_helpers(self):
        self.assertEqual(safe_actor_id(''), REDACTED)
        a = safe_actor_id('lab-collector-a')
        self.assertTrue(a.startswith('actor:'))
        self.assertNotIn('lab-collector-a', a)
        dirty = redact_event_fields({
            'event_type': ET_INGEST,
            'outcome': OUT_REJECTED,
            'reason_code': RC_SECRET_LIKE,
            'password': 'x',
            'actor_id_safe': 'lab-collector-a',
        })
        self.assertEqual(set(dirty.keys()), set(EVENT_KEYS))
        self.assertEqual(dirty['actor_id_safe'], a)


class TestIngestorAuditIntegration(unittest.TestCase):
    def test_authn_success_and_failure_events(self):
        ing = _lab()
        missing = ing.ingest(_fix('iosxe_interface_counters.json'))
        self.assertFalse(missing.ok)
        fails = ing.audit_sink.query(event_type=ET_AUTHN, outcome=OUT_FAILURE)
        self.assertTrue(any(e['reason_code'] == RC_MISSING_PRINCIPAL for e in fails))

        ok = ing.ingest(
            _fix('iosxe_interface_counters.json'),
            principal_id='lab-collector-a',
            stub_token_id='stub-collector-token-a',
        )
        self.assertTrue(ok.ok)
        auths = ing.audit_sink.query(event_type=ET_AUTHN, outcome=OUT_SUCCESS)
        self.assertTrue(any(e['reason_code'] == RC_AUTHN_OK for e in auths))
        accepts = ing.audit_sink.query(reason_code=RC_INGEST_ACCEPTED)
        self.assertEqual(len(accepts), 1)

    def test_authz_failure_and_duplicate(self):
        from utils.telemetry.lab_ingest import (
            KIND_COLLECTOR, LabAuthContext, LabStubPrincipal, PERM_INGEST, STATUS_ACTIVE,
        )
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
                principal_id='lab-collector-a',
                kind=KIND_COLLECTOR,
                permissions=frozenset({PERM_INGEST}),
                device_scope=frozenset({'edge-xe-01', 'leaf-nx-01', 'qfx-01'}),
                status=STATUS_ACTIVE,
                stub_token_id='stub-collector-token-a',
            ),
        ))
        ing = _lab(auth_context=ctx)
        denied = ing.ingest(
            _fix('iosxe_interface_counters.json'),
            principal_id='lab-collector-noperm',
            stub_token_id='tok-noperm',
        )
        self.assertEqual(denied.status, 'authz_denied')
        self.assertTrue(ing.audit_sink.query(reason_code=RC_AUTHZ_DENIED))

        a = ing.ingest(
            _fix('iosxe_interface_counters.json'),
            principal_id='lab-collector-a',
            stub_token_id='stub-collector-token-a',
        )
        b = ing.ingest(
            copy.deepcopy(_fix('iosxe_interface_counters.json')),
            principal_id='lab-collector-a',
            stub_token_id='stub-collector-token-a',
        )
        self.assertEqual(a.status, 'inserted')
        self.assertEqual(b.status, 'duplicate')
        self.assertTrue(ing.audit_sink.query(reason_code=RC_DUPLICATE_FIRST_WINS))

    def test_quarantine_secret_snapshot_topology(self):
        ing = _lab()
        q = ing.ingest(
            _fix('malformed_value.json'),
            principal_id='lab-collector-a',
            stub_token_id='stub-collector-token-a',
        )
        self.assertEqual(q.status, 'quarantined')
        self.assertTrue(
            ing.audit_sink.query(outcome=OUT_QUARANTINED)
            or ing.audit_sink.query(reason_code=RC_QUARANTINED)
        )

        sec = ing.ingest(
            _fix('with_secrets.json'),
            principal_id='lab-collector-a',
            stub_token_id='stub-collector-token-a',
        )
        self.assertEqual(sec.status, 'quarantined')
        secret_events = ing.audit_sink.query(reason_code=RC_SECRET_LIKE)
        self.assertTrue(secret_events)
        blob = json.dumps(secret_events)
        self.assertNotIn('should-never-normalize', blob)
        self.assertNotIn('abc123', blob)

        ing.ingest(
            _fix('iosxe_interface_counters.json'),
            principal_id='lab-collector-a',
            stub_token_id='stub-collector-token-a',
        )
        snap = ing.snapshot(
            principal_id='lab-operator-a',
            stub_token_id='stub-operator-token-a',
            generated_at='2026-08-20T21:00:00Z',
        )
        self.assertTrue(snap['ok'])
        self.assertTrue(ing.audit_sink.query(event_type=ET_SNAPSHOT, reason_code=RC_SNAPSHOT_OK))

        self.assertFalse(ing.topology_access()['ok'])
        self.assertFalse(ing.export_raw_payloads()['ok'])
        self.assertTrue(ing.audit_sink.query(reason_code=RC_TOPOLOGY_DENIED))
        self.assertTrue(ing.audit_sink.query(reason_code=RC_RAW_EXPORT_DENIED))

    def test_config_rejection_audited(self):
        sink = LabAuditSink(lab_mode=True)
        with self.assertRaises(ValueError):
            LabTelemetryIngestor(lab_mode=False, audit_sink=sink)
        self.assertTrue(sink.query(event_type=ET_CONFIG, reason_code=RC_LAB_MODE_REQUIRED))

        sink2 = LabAuditSink(lab_mode=True)
        with self.assertRaises(ValueError):
            LabTelemetryIngestor(lab_mode=True, bind_host='0.0.0.0', audit_sink=sink2)
        self.assertTrue(sink2.query(reason_code=RC_BIND_REFUSED))

    def test_audit_read_permissions_and_fail_closed_write(self):
        ing = _lab()
        # Operator snapshot perms do not grant audit read
        denied = ing.read_audit_events(
            principal_id='lab-operator-a',
            stub_token_id='stub-operator-token-a',
        )
        self.assertFalse(denied['ok'])

        # Collector cannot read audit
        denied2 = ing.read_audit_events(
            principal_id='lab-collector-a',
            stub_token_id='stub-collector-token-a',
        )
        self.assertFalse(denied2['ok'])

        ok = ing.read_audit_events(
            principal_id='lab-auditor-a',
            stub_token_id='stub-auditor-token-a',
        )
        self.assertTrue(ok['ok'])

        failing = _FailingSink(lab_mode=True)
        bad = LabTelemetryIngestor(lab_mode=True, audit_sink=failing)
        r = bad.ingest(
            _fix('iosxe_interface_counters.json'),
            principal_id='lab-collector-a',
            stub_token_id='stub-collector-token-a',
        )
        self.assertFalse(r.ok)
        self.assertEqual(r.status, 'audit_failed')
        self.assertEqual(bad.store_stats()['stored'], 0)

    def test_phase3_and_gate_c_and_topology_untouched(self):
        import utils.telemetry as tel
        from utils.discovery_graph import canonicalize_discovery_graph

        self.assertEqual(tuple(tel.__all__), FROZEN_PACKAGE_EXPORTS)
        gate_c = os.path.join(ROOT, 'docs', 'telemetry', 'PHASE4_GATE_C_ENCRYPTED_AT_REST.md')
        self.assertTrue(os.path.isfile(gate_c))
        self.assertIn('Encryption at rest', open(gate_c, encoding='utf-8').read())

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
        after = canonicalize_discovery_graph(copy.deepcopy(nodes), copy.deepcopy(edges))
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
