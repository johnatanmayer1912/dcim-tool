"""Tests for v7.0.45 gap remediation (G-003, G-006, G-008–G-014, G-016 offline)."""
import os
import unittest
from unittest.mock import MagicMock, patch

from utils.mac_utils import (
    distinct_macs_matching_query,
    format_mac_for_display,
    is_partial_mac_query,
)
from utils.search_relevance import sort_description_rows
from utils.task_control_plane import register_task, update_task_progress, get_task
from utils.vlan_validate import validate_vlan_operation


class TestDescriptionSearchRanking(unittest.TestCase):
    def test_run_ranks_matches(self):
        from modules import description_search as ds

        entries = [
            {'interface': 'Gi1/0/1', 'description': 'core uplink', 'status': 'up', 'source': 't'},
            {'interface': 'Gi1/0/2', 'description': 'access port', 'status': 'up', 'source': 't'},
            {'interface': 'Gi1/0/3', 'description': 'CORE switch', 'status': 'up', 'source': 't'},
        ]
        with patch.object(ds, 'connect_device') as mock_conn:
            conn = MagicMock()
            mock_conn.return_value = conn
            conn.find_prompt.return_value = 'SW1#'
            with patch.object(ds, '_try_command_with_fallback') as mock_cmd:
                mock_cmd.return_value = (
                    'Gi1/0/1 up up core uplink\nGi1/0/2 up up access\nGi1/0/3 up up CORE switch\n',
                    'show interfaces description',
                    [],
                )
                with patch.object(ds, '_parse_descriptions', return_value=entries):
                    res = ds.run(
                        {'host': '1.1.1.1', 'device_type': 'cisco_ios'},
                        'u', 'p', '', 'core', log_func=None, diag_dir=os.path.join('tests', '_tmp_desc'),
                    )
        self.assertEqual(res['status'], 'success')
        matches = res['data']['matches']
        self.assertGreaterEqual(matches[0].get('match_score', 0), matches[-1].get('match_score', 0))


class TestIosXrVlanValidation(unittest.TestCase):
    def test_iosxr_supported_in_validation(self):
        devs = [{'host': '10.0.0.1', 'device_type': 'cisco_xr'}]
        with patch('utils.vlan_validate.add_vlan') as mock_add:
            mock_add.return_value = {'status': 'success', 'commands': ['vlan 10']}
            r = validate_vlan_operation('add_vlan', devs, 'u', 'p', '', '10', 'DATA')
        self.assertNotIn('unsupported', str(r).lower())
        self.assertTrue(r['validation_results']['platform']['passed'])


class TestMacAmbiguity(unittest.TestCase):
    def test_partial_multi_mac_detected(self):
        lines = [
            '100    aaaa.bbbb.cccc    Gi1/0/1',
            '200    aaaa.bbbb.dddd    Gi1/0/2',
        ]
        distinct = distinct_macs_matching_query(lines, 'bbbb')
        self.assertEqual(len(distinct), 2)
        self.assertTrue(is_partial_mac_query('bbbb'))

    def test_format_mac_display(self):
        self.assertEqual(format_mac_for_display('aabbccddeeff'), 'aa:bb:cc:dd:ee:ff')


class TestTaskProgress(unittest.TestCase):
    def test_devices_done_total(self):
        tid = register_task('mac_trace', meta={'devices_total': 5})
        update_task_progress(tid, devices_done=2, devices_total=5, message='sw1 (2/5)')
        t = get_task(tid)
        self.assertEqual(t['devices_done'], 2)
        self.assertEqual(t['devices_total'], 5)


class TestImConflictHardFail(unittest.TestCase):
    def test_vlan_removal_is_conflict(self):
        from modules.plugins import interface_manager as im
        with patch.object(im, '_determine_vendor', return_value='cisco_ios'):
            with patch.object(im, '_extract_interface_from_config', return_value='Gi1/0/1'):
                conn = MagicMock()
                conn.send_command.return_value = ' switchport trunk allowed vlan 10 20\n'
                proposed = 'interface Gi1/0/1\n switchport trunk allowed vlan 10\n'
                r = im._validate_conflicts(conn, 'SW1', 'cisco_ios', 'Gi1/0/1', proposed, None)
        self.assertFalse(r['passed'])
        self.assertTrue(any(c['type'] == 'vlan_removal' for c in r['conflicts']))


class TestVendorCommandMatrix(unittest.TestCase):
    def test_mac_commands_per_vendor(self):
        from modules.mac_trace import _build_mac_commands
        ios = _build_mac_commands('cisco_ios', 'aabbccddeeff')
        nx = _build_mac_commands('cisco_nxos', 'aabbccddeeff')
        jun = _build_mac_commands('juniper_junos', 'aabbccddeeff')
        self.assertTrue(any('mac address-table' in c for c in ios))
        self.assertTrue(any('mac address-table' in c for c in nx))
        self.assertTrue(any('ethernet-switching' in c for c in jun))


if __name__ == '__main__':
    unittest.main()
