"""Contract validation for nst.utilization_overlay.v1 (replay)."""
from __future__ import annotations

import copy
import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.utilization_overlay.model import (
    OverlayValidationError,
    load_replay_overlay,
    parse_cable_key,
    validate_overlay_document,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLE = os.path.join(
    ROOT, 'docs', '21-utilization-overlay', 'examples', 'replay-fixture.example.json',
)
FIXTURE = os.path.join(ROOT, 'tests', 'fixtures', 'utilization', 'replay_standard_l2.json')


def _example():
    with open(EXAMPLE, encoding='utf-8') as fh:
        return json.load(fh)


class TestOverlayContractValidation(unittest.TestCase):
    def test_docs_example_replay_fixture_accepted(self):
        doc = validate_overlay_document(_example())
        self.assertEqual(doc['schema'], 'nst.utilization_overlay.v1')
        self.assertEqual(doc['mode'], 'replay')
        self.assertEqual(doc['evidence_class'], 'fixture')
        parse_cable_key(doc['paints'][0]['cable_key'])

    def test_standard_l2_replay_fixture_accepted(self):
        doc = load_replay_overlay(FIXTURE, require_replay=True)
        self.assertEqual(doc['mode'], 'replay')
        self.assertNotIn('live', doc['evidence_class'])

    def test_invalid_mode_evidence_replay_with_live_ssh_rejected(self):
        data = _example()
        data['evidence_class'] = 'live_ssh'
        with self.assertRaises(OverlayValidationError) as ctx:
            validate_overlay_document(data)
        self.assertIn('mode/evidence', str(ctx.exception))

    def test_invalid_mode_evidence_live_with_fixture_rejected(self):
        data = _example()
        data['mode'] = 'live'
        data['evidence_class'] = 'fixture'
        with self.assertRaises(OverlayValidationError) as ctx:
            validate_overlay_document(data)
        self.assertIn('mode/evidence', str(ctx.exception))

    def test_malformed_cable_key_rejected(self):
        data = _example()
        data['paints'][0]['cable_key'] = 'not-a-key'
        with self.assertRaises(OverlayValidationError) as ctx:
            validate_overlay_document(data)
        self.assertIn('malformed cable_key', str(ctx.exception))

    def test_vis_display_id_rejected_as_cable_key(self):
        data = _example()
        data['paints'][0]['cable_key'] = 'e0'
        with self.assertRaises(OverlayValidationError) as ctx:
            validate_overlay_document(data)
        self.assertIn('vis display id', str(ctx.exception))

    def test_invalid_paint_status_rejected(self):
        data = _example()
        data['paints'][0]['paint_state'] = 'down'
        with self.assertRaises(OverlayValidationError) as ctx:
            validate_overlay_document(data)
        self.assertIn('invalid paint status', str(ctx.exception))

    def test_unsupported_kind_rejected(self):
        data = _example()
        data['paints'][0]['cable_key'] = 'core-01|eth1/1|core-02|eth1/1|evpn'
        with self.assertRaises(OverlayValidationError) as ctx:
            validate_overlay_document(data)
        self.assertIn('unsupported kind', str(ctx.exception))

    def test_unsupported_collector_kind_rejected(self):
        data = _example()
        data['collector'] = {'kind': 'snmp'}
        with self.assertRaises(OverlayValidationError):
            validate_overlay_document(data)

    def test_load_replay_rejects_live_mode(self):
        data = _example()
        data['mode'] = 'live'
        data['evidence_class'] = 'live_ssh'
        data['stale_after_seconds'] = 900
        data['collector'] = {'kind': 'ssh_cli'}
        data['paints'][0]['provenance']['mode'] = 'live'
        data['paints'][0]['provenance']['evidence_class'] = 'live_ssh'
        with self.assertRaises(OverlayValidationError) as ctx:
            load_replay_overlay(data, require_replay=True)
        self.assertIn('replay only', str(ctx.exception))

    def test_validate_does_not_mutate_input(self):
        data = _example()
        original = copy.deepcopy(data)
        validate_overlay_document(data)
        self.assertEqual(data, original)

    def test_empty_paints_valid(self):
        data = _example()
        data['paints'] = []
        data['summary']['painted_count'] = 0
        validate_overlay_document(data)

    def test_live_fixture_accepted_by_load_overlay_document(self):
        live = os.path.join(ROOT, 'tests', 'fixtures', 'utilization', 'live_standard_l2.json')
        from utils.utilization_overlay.model import load_overlay_document
        doc = load_overlay_document(live)
        self.assertEqual(doc['mode'], 'live')
        self.assertEqual(doc['evidence_class'], 'live_ssh')
        self.assertEqual(doc['collector']['kind'], 'ssh_cli')

    def test_live_without_ssh_cli_rejected(self):
        data = _example()
        data['mode'] = 'live'
        data['evidence_class'] = 'live_ssh'
        data['stale_after_seconds'] = 900
        data['collector'] = {'kind': 'none'}
        data['paints'][0]['provenance']['mode'] = 'live'
        data['paints'][0]['provenance']['evidence_class'] = 'live_ssh'
        with self.assertRaises(OverlayValidationError) as ctx:
            validate_overlay_document(data)
        self.assertIn('ssh_cli', str(ctx.exception))

    def test_docs_do_not_claim_live_ssh_unimplemented(self):
        """Product code ships M4/M5; contract docs must not contradict that."""
        contract = Path(ROOT, 'docs', '21-utilization-overlay', 'FEATURE_CONTRACT.md').read_text(
            encoding='utf-8'
        )
        readme = Path(ROOT, 'docs', '21-utilization-overlay', 'README.md').read_text(encoding='utf-8')
        self.assertNotIn('live SSH not implemented', contract)
        self.assertNotRegex(readme, r'Status.*not implemented')


if __name__ == '__main__':
    unittest.main()
