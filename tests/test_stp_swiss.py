"""STP Swiss Tools runner and HTML contract (v7.0.0)."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.stp_swiss_runner import run_demo_stp_scan, _parse_blocked_ports
from utils.stp_map_formatter import generate_stp_html

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures', 'stp')


class TestStpSwiss(unittest.TestCase):
    def test_demo_job_and_html(self):
        result = run_demo_stp_scan(0)
        self.assertEqual(result['status'], 'success')
        self.assertGreaterEqual(len(result['nodes']), 3)
        self.assertTrue(any(r.get('protocol') == 'STP' for r in result['link_rows']))

        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tf:
            path = tf.name
        try:
            generate_stp_html(path, result['nodes'], result['edges'], result['link_rows'], demo_mode=True)
            with open(path, encoding='utf-8') as f:
                html = f.read()
            self.assertIn('__TOPO_LINKS__', html)
            self.assertIn('topo-search-input', html)
            self.assertIn('enabled: false', html)
            self.assertIn('DEMO', html)
        finally:
            os.unlink(path)

    def test_nxos_blocked_distinct_from_forwarding(self):
        with open(os.path.join(FIXTURES, 'cisco_nxos_stp_blocked.txt'), encoding='utf-8') as f:
            text = f.read()
        rows = _parse_blocked_ports(text, 'N9K-LEAF-01')
        ports = {r['local_port'] for r in rows}
        self.assertEqual(ports, {'Eth1/2'})
        self.assertNotIn('Eth1/1', ports)
        self.assertNotIn('Eth1/3', ports)
        self.assertTrue(all(r.get('link_type') == 'stp-blocked' for r in rows))

    def test_ios_blk_distinct_from_fwd(self):
        with open(os.path.join(FIXTURES, 'cisco_ios_stp_blocked.txt'), encoding='utf-8') as f:
            text = f.read()
        rows = _parse_blocked_ports(text, 'C9300-01')
        ports = {r['local_port'] for r in rows}
        self.assertEqual(ports, {'Gi1/0/2'})
        self.assertNotIn('Gi1/0/1', ports)


if __name__ == '__main__':
    unittest.main()
