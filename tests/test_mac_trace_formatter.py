"""MAC trace HTML report — partial search highlighting."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.mac_trace_formatter import write_mac_trace_html


class TestMacTraceFormatter(unittest.TestCase):
    def test_partial_search_shows_full_mac_highlighted(self):
        td = tempfile.mkdtemp()
        path = os.path.join(td, 'trace.html')
        hops = [{
            'hop_index': 1,
            'hostname': 'sw1',
            'device_ip': '10.0.0.1',
            'vlan': '100',
            'port': 'Gi1/0/1',
            'status': 'found',
            'resolved_mac': 'aa:bb:cc:dd:ee:ff',
        }]
        write_mac_trace_html(
            path, 'aabb', hops,
            found_endpoint='aa:bb:cc:dd:ee:ff @ sw1 — Gi1/0/1 (VLAN 100)',
        )
        html = open(path, encoding='utf-8').read()
        self.assertIn('Searched for:', html)
        self.assertIn('MAC found:', html)
        self.assertIn('<mark class="nst-match">', html)
        self.assertIn('aa:bb:cc:dd:ee:ff', html)
        self.assertIn('>MAC found<', html)

    def test_ambiguous_shows_distinct_macs(self):
        td = tempfile.mkdtemp()
        path = os.path.join(td, 'trace.html')
        hops = [{
            'hop_index': 1,
            'hostname': 'sw1',
            'device_ip': '10.0.0.1',
            'status': 'ambiguous',
            'ambiguous': True,
            'distinct_macs': ['aabbccddeeff', 'aabbccddee01'],
        }]
        write_mac_trace_html(path, 'aabb', hops, ambiguous_summary='sw1: 2 distinct MAC(s)')
        html = open(path, encoding='utf-8').read()
        self.assertIn('Partial MAC', html)
        self.assertIn('multiple matches', html)
        self.assertIn('<mark class="nst-match">', html)


if __name__ == '__main__':
    unittest.main()
