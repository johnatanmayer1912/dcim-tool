"""MAC trace path HTML contract (v7.0.0)."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.mac_trace_formatter import write_mac_trace_html


class TestMacTracePath(unittest.TestCase):
    def test_html_contains_hop_table(self):
        hops = [
            {'hop_index': 1, 'hostname': 'sw1', 'device_ip': '10.0.0.1', 'vlan': '10', 'port': 'Eth1/1', 'status': 'found'},
            {'hop_index': 2, 'hostname': 'sw2', 'device_ip': '10.0.0.2', 'vlan': None, 'port': None, 'status': 'not_found'},
        ]
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tf:
            path = tf.name
        try:
            write_mac_trace_html(path, '00:11:22:aa:bb:cc', hops, found_endpoint='sw1 — Eth1/1')
            with open(path, encoding='utf-8') as f:
                html = f.read()
            self.assertIn('MAC Path Trace', html)
            self.assertIn('sw1', html)
            self.assertIn('Eth1/1', html)
            self.assertNotIn('fonts.googleapis.com', html)
        finally:
            os.unlink(path)


if __name__ == '__main__':
    unittest.main()
