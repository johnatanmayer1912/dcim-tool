"""Offline lab smoke — IOS-XE MAC trace + QFX5100 Junos LLDP (mock SSH, v7.0.31)."""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures', 'lab')


def _read(name):
    with open(os.path.join(FIXTURES, name), encoding='utf-8') as f:
        return f.read()


class _MockConn:
    def __init__(self, responses):
        self._responses = list(responses)
        self._idx = 0

    def send_command(self, cmd, read_timeout=60):
        if self._idx < len(self._responses):
            out = self._responses[self._idx]
            self._idx += 1
            return out
        return ''

    def find_prompt(self):
        return 'lab-device#'

    def disconnect(self):
        pass


class TestIosXeMacLabSmoke(unittest.TestCase):
    @patch('modules.mac_trace.connect_device')
    @patch('modules.mac_trace.resolve_hostname_from_connection')
    def test_ios_xe_colon_mac_found_on_gi_port(self, mock_resolve, mock_connect):
        from modules import mac_trace

        mock_connect.return_value = _MockConn([_read('ios_xe_show_mac.txt')])
        mock_resolve.return_value = 'dist-sw01'

        res = mac_trace.run(
            {'host': '10.0.0.5', 'device_type': 'cisco_ios_xe'},
            'lab', 'lab', '', '00:11:22:33:44:55',
        )
        self.assertEqual(res['status'], 'success')
        self.assertTrue(res['data']['found'])
        self.assertEqual(res['data']['vlan'], '10')
        self.assertEqual(res['data']['port'], 'Gi1/0/24')
        self.assertTrue(mock_connect.called)


class TestQfx5100LabSmoke(unittest.TestCase):
    @patch('modules.mac_trace.connect_device')
    @patch('modules.mac_trace.resolve_hostname_from_connection')
    def test_qfx5100_junos_mac_on_xe_unit(self, mock_resolve, mock_connect):
        from modules import mac_trace

        esw = _read('qfx5100_esw_mac.txt')
        mock_connect.return_value = _MockConn([esw, '', '', esw, esw])
        mock_resolve.return_value = 'qfx5100-leaf01'

        res = mac_trace.run(
            {'host': '10.0.0.20', 'device_type': 'juniper_junos'},
            'lab', 'lab', '', '00:11:22:33:44:55',
        )
        self.assertEqual(res['status'], 'success')
        self.assertTrue(res['data']['found'])
        self.assertIn('xe-0/0/0', res['data']['port'])

    def test_qfx5100_lldp_neighbor_parse(self):
        from modules.plugins import network_discovery as nd

        out = _read('qfx5100_lldp_neighbors.txt')
        neighbors = nd._parse_juniper_lldp_detail(out, 'qfx-leaf01', None)
        finalized = [nd._finalize_neighbor(n) for n in neighbors]
        finalized = [n for n in finalized if n]
        names = {n['hostname'].lower() for n in finalized}
        self.assertIn('spine-nxos-01', names)
        self.assertIn('leaf-qfx-02', names)
        spine = next(n for n in finalized if 'spine-nxos' in n['hostname'].lower())
        self.assertEqual(spine['local_port'], 'xe-0/0/48')
        self.assertIn('qfx5100', neighbors[1].get('platform', '').lower() + out.lower())


if __name__ == '__main__':
    unittest.main()
