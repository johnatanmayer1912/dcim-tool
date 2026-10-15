"""Phase 4 telemetry closeout — acceptance freeze and manifest invariants."""
from __future__ import annotations

import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCEPT = os.path.join(ROOT, 'tests', 'qa', 'PHASE4_TELEMETRY_ACCEPTANCE.md')
MANIFEST = os.path.join(ROOT, 'tests', 'qa', 'MANDATORY_MANIFEST.yaml')
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
    '## 1. Gate A/B',
    '## 2. Authentication and authorization',
    '## 3. Gate C',
    '## 4. Gate D',
    '## 5. Lab audit sink',
    '## 6. Lab facade',
    '## 7. Frozen boundaries',
    '## 9. Validation commands',
)

REQUIRED_PHRASES = (
    'phase 4',
    'lab_mode',
    'in-process',
    'no sockets',
    'default-deny',
    'telemetry_audit_read',
    'encrypted-at-rest',
    'no durable',
    'no http',
    'labauditsink',
    'labgatedfacade',
    'fail closed',
    'topology',
    'phase 3',
    'arista',
    'pytest_phase4_telemetry_lab',
)


class TestPhase4AcceptanceArtifact(unittest.TestCase):
    def test_acceptance_exists_with_required_content(self):
        self.assertTrue(os.path.isfile(ACCEPT), ACCEPT)
        text = open(ACCEPT, encoding='utf-8').read()
        self.assertIn('Phase 4 **closed**', text)
        for section in REQUIRED_SECTIONS:
            self.assertIn(section, text)
        low = text.lower().replace('`', '').replace('_', '')
        # Normalize for LabAuditSink / LabGateDFacade mentions
        compact = text.lower().replace('`', '').replace('_', '').replace(' ', '')
        self.assertIn('labauditsink', compact)
        self.assertIn('labgatedfacade', compact)
        for phrase in (
            'lab_mode',
            'in-process',
            'default-deny',
            'encrypted-at-rest',
            'no durable',
            'topology',
            'arista',
            'pytest_phase4_telemetry_lab',
            'lab_ingest',
            'lab_audit',
            'lab_facade',
            'gate a/b',
            'gate c',
            'gate d',
            'zero trust',
            'no sockets',
            'wildcard',
            'fail-closed',
            'fixture',
        ):
            self.assertIn(phrase, text.lower(), f'missing: {phrase}')

    def test_no_listener_no_persistence_topology_boundaries(self):
        text = open(ACCEPT, encoding='utf-8').read().lower()
        self.assertIn('no http', text)
        self.assertIn('no durable', text)
        self.assertIn('no mutation', text)
        self.assertIn('topology', text)
        self.assertIn('listener', text)


class TestManifestAndFreeze(unittest.TestCase):
    def test_manifest_contains_phase4_blocking_suite(self):
        text = open(MANIFEST, encoding='utf-8').read()
        self.assertIn('pytest_phase4_telemetry_lab', text)
        self.assertIn('tests/test_phase4_telemetry_closeout.py', text)
        self.assertIn('tests/test_phase4_telemetry_lab_facade.py', text)
        self.assertIn('tests/test_phase4_telemetry_lab_audit.py', text)
        self.assertIn('tests/test_phase4_telemetry_lab_ingest.py', text)
        self.assertIn('tests/test_phase3_telemetry_api_freeze.py', text)
        # Narrow: must not silently pull unrelated UI/packaging suites into this id
        block = text.split('pytest_phase4_telemetry_lab', 1)[1].split('- id:', 1)[0]
        for banned in (
            'test_ui_execute_contract',
            'cli_browser_credential_id',
            'audit_frozen_plugin_sim',
            'test_map_acceptance',
        ):
            self.assertNotIn(banned, block)
        self.assertIn('blocking: true', block)
        self.assertIn('pre_release', block)

    def test_manifest_validator_passes(self):
        script = os.path.join(ROOT, 'scripts', 'validate_mandatory_qa_manifest.py')
        proc = subprocess.run(
            [sys.executable, script],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn('OK', proc.stdout)

    def test_phase3_exports_unchanged(self):
        import utils.telemetry as tel

        self.assertEqual(tuple(tel.__all__), FROZEN_PACKAGE_EXPORTS)
        for name in ('LabTelemetryIngestor', 'LabAuditSink', 'LabGateDFacade'):
            self.assertNotIn(name, tel.__all__)

    def test_no_forbidden_production_modules(self):
        names = [n for n in os.listdir(TELEMETRY_DIR) if n.endswith('.py')]
        for name in names:
            self.assertIn(name, ALLOWED_TELEMETRY_PY)
        for banned in ('http', 'grpc', 'mtls', 'listener', 'server', 'persist', 'flask'):
            for name in names:
                self.assertNotIn(banned, name.lower())
        for path in (
            os.path.join(ROOT, 'utils', 'telemetry_http.py'),
            os.path.join(ROOT, 'utils', 'telemetry', 'listener.py'),
            os.path.join(ROOT, 'utils', 'telemetry', 'persist.py'),
        ):
            self.assertFalse(os.path.exists(path), path)

    def test_lab_modules_remain_in_process(self):
        from utils.telemetry.lab_audit import LabAuditSink
        from utils.telemetry.lab_facade import LabGateDFacade
        from utils.telemetry.lab_ingest import LabTelemetryIngestor

        sink = LabAuditSink(lab_mode=True)
        ing = LabTelemetryIngestor(lab_mode=True, audit_sink=sink)
        fac = LabGateDFacade(lab_mode=True, ingestor=ing)
        self.assertFalse(ing.network_started)
        self.assertFalse(fac.network_started)
        with self.assertRaises(RuntimeError):
            ing.start_network_listener()
        with self.assertRaises(RuntimeError):
            fac.start_network_listener()
        with self.assertRaises(ValueError):
            LabTelemetryIngestor(lab_mode=True, enable_persistence=True)


if __name__ == '__main__':
    unittest.main()
