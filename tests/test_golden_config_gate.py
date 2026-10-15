"""Golden-config gate — VLAN/IM mutations. Fail-closed when enabled."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.golden_config_gate import (
    evaluate_interface_change,
    evaluate_vlan_change,
    load_golden_policy,
    raise_if_blocked,
)
from utils.vlan_validate import validate_vlan_operation


class TestGoldenConfigGate(unittest.TestCase):
    def test_policy_file_loads(self):
        pol = load_golden_policy()
        self.assertTrue(pol.get('enabled'))
        self.assertIn(1002, {int(x) for x in pol.get('forbidden_vlan_ids') or []})

    def test_vlan_1002_fails_without_ssh(self):
        step = evaluate_vlan_change('add', '1002', 'DATA')
        self.assertFalse(step['passed'])
        r = validate_vlan_operation(
            'add_vlan', [{'host': '10.0.0.1', 'device_type': 'cisco_ios'}],
            'u', 'p', '', '1002', 'DATA',
        )
        self.assertEqual(r['overall_status'], 'failed')
        self.assertFalse(r['validation_results']['golden_config']['passed'])

    def test_good_vlan_name_passes_gate(self):
        step = evaluate_vlan_change('add', '20', 'USERS_VLAN')
        self.assertTrue(step['passed'], step)

    def test_bad_vlan_name_fails(self):
        step = evaluate_vlan_change('add', '20', 'bad name!')
        self.assertFalse(step['passed'])

    def test_im_access_vlan_requires_description(self):
        bad = evaluate_interface_change('interface Gi1/0/1\n switchport access vlan 20\n')
        self.assertFalse(bad['passed'])
        good = evaluate_interface_change(
            'interface Gi1/0/1\n description access-user\n switchport access vlan 20\n'
        )
        self.assertTrue(good['passed'], good)

    def test_default_interface_forbidden(self):
        step = evaluate_interface_change('default interface Gi1/0/1')
        self.assertFalse(step['passed'])

    def test_disabled_policy_passes(self):
        step = evaluate_vlan_change('add', '1002', 'X', policy={'enabled': False})
        self.assertTrue(step['passed'])

    def test_raise_if_blocked(self):
        with self.assertRaises(RuntimeError):
            raise_if_blocked({'passed': False, 'errors': [{'message': 'no'}]})


if __name__ == '__main__':
    unittest.main()
