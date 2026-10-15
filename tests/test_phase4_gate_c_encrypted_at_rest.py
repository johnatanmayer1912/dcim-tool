"""Phase 4 Gate C — encrypted-at-rest design artifact invariants.

Design-only: no durable store, crypto implementation, or transport.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE_C = os.path.join(ROOT, 'docs', 'telemetry', 'PHASE4_GATE_C_ENCRYPTED_AT_REST.md')
TELEMETRY_DIR = os.path.join(ROOT, 'utils', 'telemetry')
LAB = os.path.join(TELEMETRY_DIR, 'lab_ingest.py')

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

FORBIDDEN_PERSIST_FILENAMES = frozenset({
    'persist.py',
    'persistence.py',
    'database.py',
    'db.py',
    'sqlite_store.py',
    'telemetry_db.py',
    'repository_sql.py',
})
FORBIDDEN_PERSIST_MODULE_RE = re.compile(
    r'^(persist|persistence|database|sqlite|sqlalchemy|redis|rocksdb|leveldb)_',
    re.I,
)

REQUIRED_SECTIONS = (
    '## 1. Persistence scope',
    '## 2. Encryption at rest',
    '## 3. Key management',
    '## 4. Access control',
    '## 5. Integrity and replay',
    '## 6. Retention and deletion',
    '## 7. Backup and recovery',
    '## 8. Failure modes',
    '## 9. Topology boundary',
    '## 10. Migration path',
    '## 11. Decision checklist',
)

REQUIRED_PHRASES = (
    'fail closed',
    'fail-closed',
    'authenticated encryption',
    'key rotation',
    'default-deny',
    'raw payload',
    'observation_id',
    'never invent',
    'topology',
    'create topology edges',
    'no persistence code',
    'not implemented',
    'telemetry_export',
    'crypto-shred',
)


class TestGateCArtifact(unittest.TestCase):
    def test_artifact_exists_with_required_sections(self):
        self.assertTrue(os.path.isfile(GATE_C), GATE_C)
        text = open(GATE_C, encoding='utf-8').read()
        for section in REQUIRED_SECTIONS:
            self.assertIn(section, text)
        low = text.lower()
        for phrase in REQUIRED_PHRASES:
            self.assertIn(phrase.lower(), low, f'missing: {phrase}')

    def test_raw_payload_and_secret_restrictions(self):
        text = open(GATE_C, encoding='utf-8').read().lower()
        self.assertIn('forbidden', text)
        self.assertIn('raw payload', text)
        self.assertIn('hard-coded keys', text)
        self.assertIn('prohibited', text)
        self.assertIn('never', text)
        self.assertIn('secrets', text)

    def test_topology_non_write_and_fail_closed(self):
        text = open(GATE_C, encoding='utf-8').read().lower()
        self.assertIn('create topology edges', text)
        self.assertIn('mutate topology', text)
        self.assertIn('fail closed', text)
        self.assertIn('gate e', text)
        self.assertIn('no telemetry record is topology evidence', text)


class TestNoPersistenceImplementation(unittest.TestCase):
    def test_no_new_persistence_modules_under_telemetry(self):
        names = [n for n in os.listdir(TELEMETRY_DIR) if n.endswith('.py')]
        for name in names:
            self.assertIn(name, ALLOWED_TELEMETRY_PY)
            self.assertNotIn(name.lower(), FORBIDDEN_PERSIST_FILENAMES)
            self.assertIsNone(
                FORBIDDEN_PERSIST_MODULE_RE.search(name),
                f'persistence-like module not allowed: {name}',
            )

    def test_lab_ingest_remains_in_process_and_refuses_persistence(self):
        self.assertTrue(os.path.isfile(LAB))
        src = open(LAB, encoding='utf-8').read()
        self.assertIn('lab_mode=True', src)
        self.assertIn('enable_persistence', src)
        self.assertIn('persistence refused', src)
        self.assertIn('network listener refused', src)
        self.assertIn('Never opens sockets', src)

        from utils.telemetry.lab_ingest import LabTelemetryIngestor

        with self.assertRaises(ValueError):
            LabTelemetryIngestor(lab_mode=True, enable_persistence=True)
        ing = LabTelemetryIngestor(lab_mode=True)
        self.assertFalse(ing.network_started)

    def test_phase3_exports_unchanged(self):
        import utils.telemetry as tel

        self.assertEqual(tuple(tel.__all__), FROZEN_PACKAGE_EXPORTS)
        self.assertNotIn('LabTelemetryIngestor', tel.__all__)

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
