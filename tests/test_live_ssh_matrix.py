"""
Live SSH / Netmiko vendor matrix tests (G-016).

Offline tests always run. Live tests require:
  NST_LIVE_SSH=1
  NST_LIVE_HOST, NST_LIVE_USER, NST_LIVE_PASS
  optional: NST_LIVE_DEVICE_TYPE (default cisco_ios)
"""
import os
import unittest

import pytest

from modules.mac_trace import _build_mac_commands
from modules.vlan_mgmt_production import _is_commit_platform, _vlan_show_cmd


class TestOfflineVendorMatrix(unittest.TestCase):
    """Always-on vendor command / platform contracts."""

    def test_vlan_show_ios_nxos_junos_xr(self):
        self.assertIn('brief', _vlan_show_cmd('cisco_ios'))
        self.assertEqual(_vlan_show_cmd('cisco_nxos'), 'show vlan')
        self.assertIn('vlans', _vlan_show_cmd('juniper_junos'))
        self.assertEqual(_vlan_show_cmd('cisco_xr'), 'show vlan')
        self.assertEqual(_vlan_show_cmd('ios_xr'), 'show vlan')

    def test_commit_platforms(self):
        self.assertTrue(_is_commit_platform('juniper_junos'))
        self.assertTrue(_is_commit_platform('cisco_xr'))
        self.assertFalse(_is_commit_platform('cisco_ios'))

    def test_mac_cmd_matrix(self):
        for dtype in ('cisco_ios', 'cisco_nxos', 'juniper_junos', 'cisco_xr'):
            cmds = _build_mac_commands(dtype, 'aabbccddeeff')
            self.assertTrue(len(cmds) >= 1, dtype)


@pytest.mark.skipif(
    os.environ.get('NST_LIVE_SSH') != '1',
    reason='Set NST_LIVE_SSH=1 and NST_LIVE_HOST/USER/PASS for live Netmiko probe',
)
class TestLiveSshProbe(unittest.TestCase):
    """Optional live SSH connectivity smoke (containerlab / lab switch)."""

    def test_live_connect_and_prompt(self):
        from modules.network_base import connect_permissive

        host = os.environ['NST_LIVE_HOST']
        user = os.environ['NST_LIVE_USER']
        pwd = os.environ['NST_LIVE_PASS']
        dtype = os.environ.get('NST_LIVE_DEVICE_TYPE', 'cisco_ios')
        dev = {'host': host, 'device_type': dtype}
        conn = connect_permissive(dev, user, pwd, os.environ.get('NST_LIVE_ENABLE', ''))
        try:
            prompt = conn.find_prompt()
            self.assertTrue(len(prompt) > 0)
        finally:
            conn.disconnect()


if __name__ == '__main__':
    unittest.main()
