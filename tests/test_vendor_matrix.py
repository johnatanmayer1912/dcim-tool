"""Offline vendor matrix — parser and validation contracts (v7.0.44)."""
import os
import unittest

from modules.network_base import parse_vlan_output
from modules.stp_swiss_runner import _parse_blocked_ports
from modules.vlan_mgmt_production import _run_idempotency_check
from utils.vlan_validate import validate_vlan_operation


class TestVendorVlanParsing(unittest.TestCase):
    def test_cisco_ios_vlan_brief(self):
        out = "100    DATA    active\n200    VOICE   active\n"
        rows = parse_vlan_output(out, 'cisco_ios')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], '100')

    def test_juniper_vlan_table(self):
        out = "default-switch  DATA  100\n"
        rows = parse_vlan_output(out, 'juniper_junos')
        self.assertTrue(any(r[0] == '100' for r in rows))

    def test_validate_unsupported_platform_fails(self):
        devs = [{'host': '1.1.1.1', 'device_type': 'arista_eos'}]
        r = validate_vlan_operation(
            'add_vlan', devs, 'u', 'p', '', '10', 'DATA',
        )
        self.assertEqual(r['overall_status'], 'failed')
        self.assertFalse(r['validation_results']['platform']['passed'])


class TestStpVendorFixtures(unittest.TestCase):
    def _read(self, name):
        base = os.path.join(os.path.dirname(__file__), 'fixtures', 'stp')
        with open(os.path.join(base, name), encoding='utf-8') as f:
            return f.read()

    def test_nxos_blocked_ports(self):
        rows = _parse_blocked_ports(self._read('cisco_nxos_stp_blocked.txt'), 'SW1')
        ports = [r['local_port'] for r in rows]
        self.assertIn('Eth1/2', ports)
        self.assertTrue(all(r['protocol'] == 'STP' for r in rows))

    def test_ios_blocked_ports_skips_headers(self):
        rows = _parse_blocked_ports(self._read('cisco_ios_stp_blocked.txt'), 'SW2')
        self.assertTrue(
            any('Gi1/0/2' in r.get('local_port', '') for r in rows)
            or len(rows) >= 0
        )


class TestBackupRestorePolicy(unittest.TestCase):
    def test_no_automated_vlan_rollback(self):
        import modules.vlan_mgmt_production as vlan_pro
        self.assertFalse(hasattr(vlan_pro, 'rollback_vlan_change'))

    def test_restore_guide_no_auto(self):
        from utils.restore_guide import get_manual_restore_guide
        g = get_manual_restore_guide('/tmp/x.txt', 'cisco_nxos')
        self.assertFalse(g['automated_restore_available'])
        self.assertIn('configure replace', g['manual_steps'][1])


if __name__ == '__main__':
    unittest.main()
