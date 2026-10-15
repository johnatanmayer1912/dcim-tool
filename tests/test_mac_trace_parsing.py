"""MAC trace parsing and normalization regression tests (v7.0.28)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.mac_trace import _parse_mac_match_line, _build_mac_commands
from utils.mac_utils import (
    normalize_mac_hex,
    to_cisco_dotted,
    to_junos_colon,
    cisco_search_terms,
    junos_search_terms,
    line_contains_mac,
    extract_junos_interface,
)
from utils.juniper_iface import resolve_junos_iface_key, split_junos_unit, apply_juniper_bundles


class TestMacNormalization(unittest.TestCase):
    def test_colon_to_cisco_dotted(self):
        self.assertEqual(to_cisco_dotted('00:11:22:33:44:55'), '0011.2233.4455')
        self.assertEqual(normalize_mac_hex('aa-bb-cc-dd-ee-ff'), 'aabbccddeeff')

    def test_colon_to_junos(self):
        self.assertEqual(to_junos_colon('0011.2233.4455'), '00:11:22:33:44:55')

    def test_cisco_search_terms_include_dotted(self):
        terms = cisco_search_terms('00:11:22:33:44:55')
        self.assertIn('0011.2233.4455', terms)
        self.assertIn('2233.4455', terms)

    def test_junos_search_terms_include_colon(self):
        terms = junos_search_terms('0011.2233.4455')
        self.assertIn('00:11:22:33:44:55', terms)


class TestCiscoMacParsing(unittest.TestCase):
    def test_ios_xe_cam_row(self):
        line = '10    0011.2233.4455    DYNAMIC     Gi1/0/24'
        vlan, port, ok = _parse_mac_match_line(line, 'cisco_ios_xe')
        self.assertTrue(ok)
        self.assertEqual(vlan, '10')
        self.assertEqual(port, 'Gi1/0/24')

    def test_ios_xe_po_row(self):
        line = '20    aabb.ccdd.eeff    STATIC      Po1'
        vlan, port, ok = _parse_mac_match_line(line, 'cisco_xe')
        self.assertTrue(ok)
        self.assertEqual(port, 'Po1')

    def test_cisco_commands_use_dotted_format(self):
        cmds = _build_mac_commands('cisco_ios_xe', '00:11:22:33:44:55')
        self.assertTrue(any('0011.2233.4455' in c for c in cmds))


class TestJunosMacParsing(unittest.TestCase):
    def test_qfx_ethernet_switching_row(self):
        line = 'DATA    00:11:22:33:44:55    Learn    0    xe-0/0/0.0'
        vlan, port, ok = _parse_mac_match_line(line, 'juniper_junos')
        self.assertTrue(ok)
        self.assertEqual(vlan, 'DATA')
        self.assertEqual(port, 'xe-0/0/0.0')

    def test_junos_14_ge_unit_suffix(self):
        line = 'VOICE  aa:bb:cc:00:11:22  Learn  0  ge-0/0/1.0*'
        vlan, port, ok = _parse_mac_match_line(line, 'juniper_junos')
        self.assertTrue(ok)
        self.assertEqual(port, 'ge-0/0/1.0')

    def test_junos_ae_bundle_row(self):
        line = 'TRUNK   00:11:22:aa:bb:cc   Learn   0   ae0.0'
        vlan, port, ok = _parse_mac_match_line(line, 'juniper_junos')
        self.assertTrue(ok)
        self.assertEqual(port, 'ae0.0')

    def test_junos_default_switch_row(self):
        line = 'default-switch  00:11:22:33:44:55  Learn  0  xe-0/0/12.0'
        vlan, port, ok = _parse_mac_match_line(line, 'juniper_junos')
        self.assertTrue(ok)
        self.assertIn('default-switch', vlan)
        self.assertEqual(port, 'xe-0/0/12.0')

    def test_junos_commands_multi_syntax(self):
        cmds = _build_mac_commands('juniper_junos', '00:11:22:33:44:55')
        self.assertTrue(any('ethernet-switching table | match 00:11:22:33:44:55' in c for c in cmds))
        self.assertIn('show bridge mac-table', cmds)

    def test_line_contains_mac_formats(self):
        self.assertTrue(line_contains_mac('DATA  00:11:22:33:44:55  xe-0/0/0.0', '0011.2233.4455'))
        self.assertTrue(line_contains_mac('10  0011.2233.4455  DYNAMIC  Gi1/0/1', '00:11:22:33:44:55'))

    def test_extract_junos_interface(self):
        self.assertEqual(extract_junos_interface('Learn 0 xe-0/0/0.0*'), 'xe-0/0/0.0')


class TestJunosInterfaceCorrelation(unittest.TestCase):
    def test_split_unit(self):
        phys, logical = split_junos_unit('ge-0/0/0.0')
        self.assertEqual(phys, 'ge-0/0/0')
        self.assertEqual(logical, 'ge-0/0/0.0')

    def test_resolve_mac_table_to_physical(self):
        keys = ['ge-0/0/0', 'xe-0/0/1', 'ae0']
        self.assertEqual(resolve_junos_iface_key('ge-0/0/0.0', keys), 'ge-0/0/0')
        self.assertEqual(resolve_junos_iface_key('ae0.0', keys), 'ae0')

    def test_apply_bundles_enriches_int_meta(self):
        int_meta = {
            'xe-0/0/0': {'desc': 'uplink', 'op_status': 'up'},
            'xe-0/0/1': {'desc': 'uplink2', 'op_status': 'up'},
        }
        lag = {
            'ae0': {
                'protocol': 'LACP',
                'members': [
                    {'intf': 'xe-0/0/0', 'status': 'bundled'},
                    {'intf': 'xe-0/0/1', 'status': 'bundled'},
                ],
            },
        }
        bundles = apply_juniper_bundles(int_meta, lag)
        self.assertIn('ae0', int_meta)
        self.assertEqual(int_meta['xe-0/0/0']['ae_bundle'], 'ae0')
        self.assertEqual(bundles['xe-0/0/0'], 'ae0')


if __name__ == '__main__':
    unittest.main()
