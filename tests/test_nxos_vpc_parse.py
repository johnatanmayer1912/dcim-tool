"""Regression tests for NX-OS 9.x vPC table parsing (Identifier column, multi-line header)."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.nxos_vpc_parse import (
    extract_nxos_version,
    extract_vpc_domain_id,
    normalize_vpc_peer_status,
    parse_vpc_full,
    parse_vpc_table_from_cli,
    parse_vpc_table_row,
    vpc_details_from_structured,
)


class TestNxosVpcParse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = os.path.join(
            os.path.dirname(__file__), 'simulation', 'device_data.json'
        )
        with open(fixture, encoding='utf-8') as f:
            data = json.load(f)
        cls.vpc_out = data['cisco_nxos']['show vpc']

    def test_identifier_column_row(self):
        parts = '10  Po10  10  up  success  success  up'.split()
        row = parse_vpc_table_row(parts)
        self.assertIsNotNone(row)
        self.assertEqual(row['vpc_id'], '10')
        self.assertEqual(row['po'], 'Po10')
        self.assertEqual(row['status'], 'up')
        self.assertEqual(row['consistency'], 'success')

    def test_parse_table_from_simulation_fixture(self):
        table = parse_vpc_table_from_cli(self.vpc_out)
        self.assertEqual(len(table), 1)
        self.assertEqual(table[0]['po'], 'Po10')
        self.assertEqual(table[0]['status'], 'up')

    def test_domain_id_and_peer_status(self):
        structured = parse_vpc_full(self.vpc_out)
        self.assertEqual(structured['domain_id'], '1')
        self.assertEqual(structured['role'], 'primary')
        self.assertEqual(structured['peer_status'], 'up')
        self.assertEqual(structured['keepalive_status'], 'up')
        self.assertEqual(len(structured['vpc_table']), 1)

    def test_vpc_details_from_structured(self):
        structured = parse_vpc_full(self.vpc_out)
        vpc_ids, details = vpc_details_from_structured(structured)
        self.assertIn('Po10', vpc_ids)
        self.assertEqual(details['Po10']['type'], 'vpc')
        self.assertEqual(details['Po10']['status'], 'up')

    def test_peer_adjacency_formed_ok(self):
        self.assertEqual(
            normalize_vpc_peer_status('peer adjacency formed ok'),
            'up',
        )

    def test_extract_domain_id_variants(self):
        text = 'vPC domain id                     : 42'
        self.assertEqual(extract_vpc_domain_id(text), '42')

    def test_classic_7x_table_row(self):
        classic = (
            'vPC status\n'
            '----\n'
            'id   Port   Status Consistency Reason\n'
            '10   Po10   up     success     -\n'
        )
        table = parse_vpc_table_from_cli(classic)
        self.assertEqual(len(table), 1)
        self.assertEqual(table[0]['vpc_id'], '10')
        self.assertEqual(table[0]['status'], 'up')

    def test_extract_nxos_version(self):
        ver = 'Cisco Nexus Operating System (NX-OS) Software\n  system:      version 9.3(5)'
        self.assertEqual(extract_nxos_version(ver), '9.3(5)')


if __name__ == '__main__':
    unittest.main()
