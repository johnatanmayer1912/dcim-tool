"""Regression: VLAN validation, control plane, search relevance, missing VLAN HTML."""
import os
import tempfile
import unittest

from utils.missing_vlan_formatter import write_missing_vlan_html
from utils.search_relevance import description_row_score, sort_description_rows
from utils.task_control_plane import (
    complete_task,
    list_tasks,
    register_task,
    request_cancel,
)
from utils.vlan_validate import validate_vlan_operation


class TestVlanValidate(unittest.TestCase):
    def test_validate_empty_devices(self):
        r = validate_vlan_operation('add_vlan', [], 'u', 'p', '', '10', 'DATA')
        self.assertEqual(r['overall_status'], 'failed')
        self.assertFalse(r['validation_results']['dry_run']['passed'])

    def test_rename_juniper_does_not_ssh(self):
        from unittest.mock import patch
        devs = [{'host': '10.0.0.1', 'device_type': 'juniper_junos'}]
        with patch('utils.vlan_validate.rename_vlan') as mock_rename:
            r = validate_vlan_operation('rename_vlan', devs, 'u', 'p', '', '10', 'NEW')
        mock_rename.assert_not_called()
        self.assertEqual(r['overall_status'], 'failed')

    def test_invalid_vlan_id(self):
        r = validate_vlan_operation('add_vlan', [{'host': '1.1.1.1', 'device_type': 'cisco_ios'}],
                                    'u', 'p', '', '99999', 'X')
        self.assertFalse(r['validation_results']['vendor_syntax']['passed'])


class TestTaskControlPlane(unittest.TestCase):
    def test_register_and_complete(self):
        tid = register_task('add_vlan', label='test')
        self.assertTrue(tid)
        complete_task(tid, 'complete')
        tasks = list_tasks()
        self.assertTrue(any(t['id'] == tid for t in tasks))

    def test_cancel(self):
        tid = register_task('vlan_check', label='cancel-me')
        self.assertTrue(request_cancel(tid))
        t = next(x for x in list_tasks() if x['id'] == tid)
        self.assertIn(t['status'], ('cancelling', 'cancelled', 'running'))


class TestSearchRelevance(unittest.TestCase):
    def test_exact_beats_partial(self):
        rows = [
            {'hostname': 'sw1', 'description': 'uplink to core', 'interface': 'Gi1/0/1'},
            {'hostname': 'sw2', 'description': 'CORE-UPLINK', 'interface': 'Gi1/0/2'},
        ]
        ranked = sort_description_rows('core', rows)
        self.assertEqual(ranked[0]['hostname'], 'sw2')

    def test_score_exact(self):
        s = description_row_score('uplink', {'description': 'uplink', 'interface': ''})
        self.assertGreaterEqual(s, 100)


class TestMissingVlanHtml(unittest.TestCase):
    def test_writes_html(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, 'report.html')
            write_missing_vlan_html(path, '100', ['a'], ['b'], [])
            self.assertTrue(os.path.isfile(path))
            content = open(path, encoding='utf-8').read()
            self.assertIn('Missing VLAN 100', content)
            self.assertIn('b', content)


class TestParseVlanOutput(unittest.TestCase):
    def test_junos_does_not_skip_vlan_named_default(self):
        from modules.network_base import parse_vlan_output
        out = "VLAN Name\nDEFAULT 100\n"
        rows = parse_vlan_output(out, 'juniper_junos')
        self.assertTrue(any(r[1] == 'DEFAULT' for r in rows))


class TestJunosImHelpers(unittest.TestCase):
    def test_normalize_display_set(self):
        from modules.plugins.interface_manager import _normalize_junos_set_config
        raw = "## comment\nset interfaces ge-0/0/1 description test\n"
        self.assertIn('set interfaces ge-0/0/1', _normalize_junos_set_config(raw))

    def test_extract_interface_from_set(self):
        from modules.plugins.interface_manager import _extract_interface_from_config
        cfg = 'set interfaces ge-0/0/1 description "x"\n'
        self.assertEqual(_extract_interface_from_config(cfg), 'ge-0/0/1')


class TestOutputPathsDemo(unittest.TestCase):
    def test_demo_vpc_path_under_data_root(self):
        from utils.output_paths import get_data_root, get_demo_vpc_topology_path
        p = get_demo_vpc_topology_path()
        self.assertTrue(p.startswith(get_data_root()))


class TestVlanMgmtHtml(unittest.TestCase):
    def test_writes_html(self):
        from utils.vlan_mgmt_formatter import write_vlan_mgmt_html
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, 'vlan.html')
            write_vlan_mgmt_html(path, 'add', '10', 'DATA', [
                {'device': 'sw1', 'status': 'success', 'data': {}},
            ])
            self.assertIn('VLAN Add', open(path, encoding='utf-8').read())


class TestVlanResultStatus(unittest.TestCase):
    def test_verification_failed_status(self):
        from modules.vlan_mgmt_production import _result_status
        self.assertEqual(_result_status(verification_passed=False), 'verification_failed')
        self.assertEqual(_result_status(skipped=True), 'skipped')


class TestCredentialSecurity(unittest.TestCase):
    def test_restore_guide_module(self):
        from utils.restore_guide import get_manual_restore_guide
        g = get_manual_restore_guide('x', 'juniper_junos')
        self.assertFalse(g['automated_restore_available'])


if __name__ == '__main__':
    unittest.main()
