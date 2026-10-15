"""Phase 3 closeout — fixture-only telemetry public API freeze.

Verifies package exports and module importability without transport,
auth, topology, UI, persistence, or alerting symbols.
"""
from __future__ import annotations

import importlib
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Frozen surface — must match utils.telemetry.__all__ and acceptance checklist.
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

FORBIDDEN_EXPORT_NEEDLES = (
    'grpc',
    'protobuf',
    'proto',
    'snmp',
    'netconf',
    'ssh',
    'socket',
    'alert',
    'dashboard',
    'persist',
    'database',
    'sqlite',
    'redis',
    'queue',
    'topology',
    'trust_tier',
    'discovery_graph',
    'flask',
    'socketio',
    'auth',
    'credential',
    'vault',
)

MODULE_PUBLIC = {
    'utils.telemetry.contract': (
        'UNKNOWN',
        'compute_observation_id',
        'empty_observation',
        'observation_field_names',
    ),
    'utils.telemetry.normalize': (
        'load_fixture_json',
        'normalize_observation',
        'normalize_batch',
    ),
    'utils.telemetry.catalog': (
        'lookup_metric',
        'apply_catalog_to_observation',
    ),
    'utils.telemetry.store': (
        'ObservationStore',
    ),
    'utils.telemetry.delta': (
        'same_series',
        'series_key',
        'compute_delta',
        'pairwise_deltas',
        'latest_delta',
    ),
    'utils.telemetry.snapshot': (
        'export_series_snapshot',
        'snapshot_to_json',
    ),
}

STORE_METHODS = (
    'insert',
    'query',
    'stats',
    'clear',
    'ingest_normalized_batch',
    'latest_delta',
    'pairwise_deltas',
)


class TestPackageExportFreeze(unittest.TestCase):
    def test_package_all_matches_frozen_surface(self):
        import utils.telemetry as tel

        self.assertEqual(tuple(tel.__all__), FROZEN_PACKAGE_EXPORTS)

    def test_package_exports_importable(self):
        import utils.telemetry as tel

        for name in FROZEN_PACKAGE_EXPORTS:
            self.assertTrue(hasattr(tel, name), f'missing package export: {name}')
            self.assertIsNotNone(getattr(tel, name))

    def test_no_forbidden_transport_or_product_exports(self):
        import utils.telemetry as tel

        names = set(tel.__all__) | {
            n for n in dir(tel) if not n.startswith('_')
        }
        lowered = {n.lower() for n in names}
        for needle in FORBIDDEN_EXPORT_NEEDLES:
            hits = [n for n in lowered if needle in n]
            self.assertEqual(hits, [], f'forbidden export needle {needle!r}: {hits}')


class TestModuleImportSurface(unittest.TestCase):
    def test_module_symbols_importable_without_optional_deps(self):
        for mod_name, symbols in MODULE_PUBLIC.items():
            mod = importlib.import_module(mod_name)
            for sym in symbols:
                self.assertTrue(hasattr(mod, sym), f'{mod_name}.{sym}')
                self.assertIsNotNone(getattr(mod, sym))

    def test_store_public_methods_present(self):
        from utils.telemetry import ObservationStore

        store = ObservationStore(max_observations=2)
        for method in STORE_METHODS:
            self.assertTrue(callable(getattr(store, method)), method)

    def test_legacy_contract_imports_compatible(self):
        from utils.telemetry.contract import (
            UNKNOWN,
            compute_observation_id,
            empty_observation,
            observation_field_names,
        )
        from utils.telemetry import (
            UNKNOWN as U2,
            compute_observation_id as cid2,
            empty_observation as eo2,
            observation_field_names as ofn2,
        )

        self.assertIs(UNKNOWN, U2)
        self.assertIs(compute_observation_id, cid2)
        self.assertIs(empty_observation, eo2)
        self.assertIs(observation_field_names, ofn2)
        obs = empty_observation(observation_id='freeze-1', device_id='d1')
        self.assertEqual(obs['observation_id'], 'freeze-1')
        self.assertEqual(UNKNOWN, 'unknown')

    def test_import_side_effects_do_not_open_network(self):
        # Re-import package; must not newly load transport stacks.
        before = set(sys.modules)
        mod = importlib.reload(importlib.import_module('utils.telemetry'))
        after = set(sys.modules)
        self.assertTrue(hasattr(mod, 'ObservationStore'))
        newly_loaded = after - before
        for banned in ('grpc', 'protobuf', 'pysnmp', 'paramiko'):
            self.assertFalse(
                any(name == banned or name.startswith(banned + '.') for name in newly_loaded),
                f'{banned} loaded during utils.telemetry reload: {sorted(newly_loaded)[:20]}',
            )


class TestAcceptanceArtifactPresent(unittest.TestCase):
    def test_acceptance_checklist_exists(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root, 'tests', 'qa', 'PHASE3_TELEMETRY_ACCEPTANCE.md')
        self.assertTrue(os.path.isfile(path), path)
        text = open(path, encoding='utf-8').read()
        for needle in (
            'normalize_observation',
            'ObservationStore',
            'export_series_snapshot',
            'generated_at',
            'non-goals',
            'Cisco IOS-XE',
            'Cisco NX-OS',
            'Juniper Junos',
        ):
            self.assertIn(needle, text)


if __name__ == '__main__':
    unittest.main()
