"""Phase 4 — Zero Trust gate artifact invariants (design-only).

Does not implement transport, auth, persistence, UI, or collectors.
Asserts the architecture gate exists and Phase 3 surface stays frozen.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(ROOT, 'docs', 'telemetry', 'PHASE4_ZERO_TRUST_GATE.md')
PHASE3_ACCEPT = os.path.join(ROOT, 'tests', 'qa', 'PHASE3_TELEMETRY_ACCEPTANCE.md')
TELEMETRY_DIR = os.path.join(ROOT, 'utils', 'telemetry')

# Must match Phase 3 API freeze.
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

ALLOWED_TELEMETRY_MODULES = frozenset({
    '__init__.py',
    'contract.py',
    'normalize.py',
    'catalog.py',
    'store.py',
    'delta.py',
    'snapshot.py',
    'lab_ingest.py',  # Phase 4 lab-only in-process prototype (not package-exported)
    'lab_audit.py',   # Phase 4 lab-only in-memory audit sink (not package-exported)
    'lab_facade.py',  # Phase 4 lab-only Gate D facade (not package-exported)
    '__pycache__',
})

REQUIRED_GATE_HEADINGS = (
    '## 1. Trust boundaries',
    '## 2. Identity',
    '## 3. Authentication and authorization',
    '## 4. Transport security',
    '## 5. Ingestion safety',
    '## 6. Persistence requirements',
    '## 7. Audit and observability',
    '## 8. Topology boundary',
    '## 9. Threat model',
    '## 10. Decision gates',
)

REQUIRED_GATE_CONTROLS = (
    'fail closed',
    'default-deny',
    'mutual authentication',
    'encryption in transit',
    'encryption at rest',
    'source_timestamp',
    'quarantine',
    'topology',
    'Gate A',
    'Gate B',
    'Gate C',
    'Gate D',
    'Gate E',
    'stolen collector',
    'topology poisoning',
    'unauthorized export',
)

# Production code must not gain these implementation modules under utils/telemetry.
FORBIDDEN_NEW_MODULE_PATTERNS = (
    r'grpc',
    r'protobuf',
    r'proto_',
    r'snmp',
    r'netconf',
    r'collector',
    r'transport',
    r'persist',
    r'database',
    r'auth',
    r'alert',
    r'dashboard',
)


class TestZeroTrustGateArtifact(unittest.TestCase):
    def test_gate_artifact_exists_with_required_sections(self):
        self.assertTrue(os.path.isfile(GATE), GATE)
        text = open(GATE, encoding='utf-8').read()
        self.assertIn('Architecture / security **gate only**', text)
        self.assertIn('not implemented', text.lower())
        for heading in REQUIRED_GATE_HEADINGS:
            self.assertIn(heading, text)
        low = text.lower()
        for control in REQUIRED_GATE_CONTROLS:
            self.assertIn(control.lower(), low, f'missing control phrase: {control}')

    def test_gate_states_no_implementation_this_pass(self):
        text = open(GATE, encoding='utf-8').read().lower()
        self.assertIn('no persistence is implemented in this pass', text)
        self.assertIn('must not', text)
        self.assertIn('phase 3', text)


class TestPhase3SurfaceUnchanged(unittest.TestCase):
    def test_phase3_package_exports_unchanged(self):
        import utils.telemetry as tel

        self.assertEqual(tuple(tel.__all__), FROZEN_PACKAGE_EXPORTS)

    def test_phase3_acceptance_checklist_intact(self):
        self.assertTrue(os.path.isfile(PHASE3_ACCEPT), PHASE3_ACCEPT)
        text = open(PHASE3_ACCEPT, encoding='utf-8').read()
        self.assertIn('Phase 3 closed', text)
        self.assertIn('normalize_observation', text)
        self.assertIn('ObservationStore', text)
        self.assertIn('export_series_snapshot', text)
        self.assertIn('Cisco IOS-XE', text)
        self.assertIn('Juniper Junos', text)

    def test_telemetry_package_has_no_live_transport_modules(self):
        names = set(os.listdir(TELEMETRY_DIR))
        unexpected = names - ALLOWED_TELEMETRY_MODULES
        # Allow only .py and package cache; reject any new implementation files.
        for name in sorted(unexpected):
            if name.endswith('.pyc'):
                continue
            self.fail(f'unexpected telemetry path: {name}')
        for name in names:
            if not name.endswith('.py'):
                continue
            for pat in FORBIDDEN_NEW_MODULE_PATTERNS:
                self.assertIsNone(
                    re.search(pat, name, re.I),
                    f'forbidden implementation module name: {name} (~{pat})',
                )


class TestNoLiveIntegrationAdded(unittest.TestCase):
    def test_no_new_top_level_telemetry_transport_packages(self):
        """Guard common future package names under utils/ and modules/."""
        candidates = [
            os.path.join(ROOT, 'utils', 'telemetry_grpc'),
            os.path.join(ROOT, 'utils', 'telemetry_persist'),
            os.path.join(ROOT, 'utils', 'telemetry_auth'),
            os.path.join(ROOT, 'modules', 'telemetry_collector'),
            os.path.join(ROOT, 'modules', 'telemetry_transport'),
        ]
        for path in candidates:
            self.assertFalse(
                os.path.exists(path),
                f'live integration path must not exist yet: {path}',
            )

    def test_mandatory_qa_manifest_still_valid(self):
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
