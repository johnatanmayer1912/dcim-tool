"""Phase 4 Gate D — operator/API exposure design artifact invariants.

Design-only: no HTTP/listener/UI/persistence implementation.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE_D = os.path.join(ROOT, 'docs', 'telemetry', 'PHASE4_GATE_D_OPERATOR_API_EXPOSURE.md')
TELEMETRY_DIR = os.path.join(ROOT, 'utils', 'telemetry')

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

ALLOWED_TELEMETRY_PY = frozenset({
    '__init__.py',
    'contract.py',
    'normalize.py',
    'catalog.py',
    'store.py',
    'delta.py',
    'snapshot.py',
    'lab_ingest.py',
    'lab_audit.py',
    'lab_facade.py',
})

REQUIRED_SECTIONS = (
    '## 1. Exposure principles',
    '## 2. Principal classes',
    '## 3. Endpoint / surface inventory',
    '## 4. Permission matrix',
    '## 5. Response contracts',
    '## 6. Export rules',
    '## 7. Query controls',
    '## 8. Error behavior',
    '## 9. Audit requirements',
    '## 10. Listener boundary',
    '## 11. Topology boundary',
    '## 12. Gate D decision checklist',
)

REQUIRED_PERMISSIONS = (
    'telemetry_ingest',
    'telemetry_read',
    'telemetry_export',
    'telemetry_audit_read',
    'telemetry_admin',
    'topology_read',
    'topology_write',
    'raw_payload_read',
)

REQUIRED_PHRASES = (
    'default deny',
    'read-only',
    'least privilege',
    'no raw payload',
    'loopback',
    'snapshot read',
    'audit read',
    'export',
    'fail-closed',
    'topology_write',
    '0.0.0.0',
    'gate e',
    'not implemented',
    'no listener',
)


class TestGateDArtifact(unittest.TestCase):
    def test_artifact_sections_and_permissions(self):
        self.assertTrue(os.path.isfile(GATE_D), GATE_D)
        text = open(GATE_D, encoding='utf-8').read()
        for section in REQUIRED_SECTIONS:
            self.assertIn(section, text)
        for perm in REQUIRED_PERMISSIONS:
            self.assertIn(f'`{perm}`', text)
        low = text.lower()
        for phrase in REQUIRED_PHRASES:
            self.assertIn(phrase.lower(), low, f'missing: {phrase}')

    def test_export_and_audit_separated_from_read(self):
        text = open(GATE_D, encoding='utf-8').read().lower()
        self.assertIn('imply audit read', text)
        self.assertIn('no implicit export', text)
        self.assertIn('read and export separate', text)
        self.assertIn('telemetry_audit_read', text)
        self.assertIn('telemetry_export', text)

    def test_raw_payload_and_topology_denied(self):
        text = open(GATE_D, encoding='utf-8').read().lower()
        self.assertIn('raw_payload_read', text)
        self.assertIn('denied', text)
        self.assertIn('topology_write', text)
        self.assertIn('unavailable', text)
        self.assertIn('cannot', text)
        self.assertIn('topology edges', text)


class TestNoListenerImplementation(unittest.TestCase):
    def test_telemetry_modules_unchanged_surface(self):
        names = [n for n in os.listdir(TELEMETRY_DIR) if n.endswith('.py')]
        for name in names:
            self.assertIn(name, ALLOWED_TELEMETRY_PY)
        for banned in ('http', 'https', 'grpc', 'mtls', 'flask', 'listener', 'server'):
            for name in names:
                self.assertNotIn(banned, name.lower())

    def test_no_new_listener_paths(self):
        candidates = [
            os.path.join(ROOT, 'utils', 'telemetry_http.py'),
            os.path.join(ROOT, 'utils', 'telemetry_api.py'),
            os.path.join(ROOT, 'utils', 'telemetry', 'http_server.py'),
            os.path.join(ROOT, 'utils', 'telemetry', 'listener.py'),
            os.path.join(ROOT, 'modules', 'telemetry_api.py'),
        ]
        for path in candidates:
            self.assertFalse(os.path.exists(path), path)

    def test_lab_remains_in_process(self):
        from utils.telemetry.lab_audit import LabAuditSink
        from utils.telemetry.lab_ingest import LabTelemetryIngestor

        sink = LabAuditSink(lab_mode=True, max_events=5)
        self.assertTrue(sink.lab_only)
        ing = LabTelemetryIngestor(lab_mode=True, audit_sink=sink)
        self.assertFalse(ing.network_started)
        with self.assertRaises(RuntimeError):
            ing.start_network_listener()

    def test_phase3_exports_unchanged(self):
        import utils.telemetry as tel

        self.assertEqual(tuple(tel.__all__), FROZEN_PACKAGE_EXPORTS)
        for name in ('LabTelemetryIngestor', 'LabAuditSink'):
            self.assertNotIn(name, tel.__all__)

    def test_mandatory_qa_manifest_valid(self):
        script = os.path.join(ROOT, 'scripts', 'validate_mandatory_qa_manifest.py')
        proc = subprocess.run(
            [sys.executable, script],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn('OK', proc.stdout)


if __name__ == '__main__':
    unittest.main()
