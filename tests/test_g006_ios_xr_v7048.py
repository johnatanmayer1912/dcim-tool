"""G-006 IOS-XR first-class VLAN support (v7.0.48)."""
import unittest
from unittest.mock import patch

from modules.network_base import parse_vlan_output
from modules.vlan_mgmt_production import (
    _is_commit_platform,
    _is_ios_xr,
    _vlan_section_cmd,
    _vlan_show_cmd,
)
from utils.vlan_validate import validate_vlan_operation


class TestIosXrDetection(unittest.TestCase):
    def test_is_ios_xr_aliases(self):
        for dt in ('cisco_xr', 'ios_xr', 'iosxr', 'ios-xr', 'Cisco_XR'):
            self.assertTrue(_is_ios_xr(dt), dt)
        self.assertFalse(_is_ios_xr('cisco_ios'))
        self.assertFalse(_is_ios_xr('cisco_nxos'))

    def test_vlan_show_not_brief(self):
        self.assertEqual(_vlan_show_cmd('cisco_xr'), 'show vlan')
        self.assertEqual(_vlan_show_cmd('ios_xr'), 'show vlan')
        self.assertNotIn('brief', _vlan_show_cmd('cisco_xr'))

    def test_vlan_section_cmd(self):
        self.assertEqual(_vlan_section_cmd('cisco_xr'), 'show running-config vlan')

    def test_commit_platform(self):
        self.assertTrue(_is_commit_platform('cisco_xr'))


class TestIosXrParseAndValidate(unittest.TestCase):
    def test_parse_vlan_cisco_xr_output(self):
        sample = (
            "VLAN  Name                             Status\n"
            "-----  -------------------------------- ------\n"
            "10     DATA                             active\n"
        )
        parsed = parse_vlan_output(sample, 'cisco_xr')
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0][0], '10')
        self.assertEqual(parsed[0][1], 'DATA')

    def test_validate_platform_note(self):
        devs = [{'host': 'xr1', 'device_type': 'cisco_xr'}]
        with patch('utils.vlan_validate.add_vlan') as mock_add:
            mock_add.return_value = {'status': 'success', 'data': {'commands': ['vlan 10']}}
            r = validate_vlan_operation('add_vlan', devs, 'u', 'p', '', '10', 'DATA')
        self.assertTrue(r['validation_results']['platform']['passed'])
        notes = ' '.join(r['validation_results']['platform'].get('warnings') or [])
        self.assertIn('IOS-XR', notes)


if __name__ == '__main__':
    unittest.main()
