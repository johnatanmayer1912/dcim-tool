"""Validate consolidator against real NST HTML/CSV formats and multi-file merge."""
from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from utils.asset_warranty_consolidator import AssetWarrantyConsolidator
from utils.report_formatter import format_asset_warranty_csv, format_asset_warranty_html


class TestAssetWarrantyConsolidatorRealFormats(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.base = Path(self.tmp) / 'reports'
        self.cons = AssetWarrantyConsolidator(base_dir=str(self.base))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _sample_assets(self, host='10.0.0.1', hostname='sw1.lab', serial='FDO1234567'):
        return {
            'host': host,
            'assets': [{
                'host': host,
                'hostname': hostname,
                'pid': 'C9300-48P',
                'serial_number': serial,
                'software_version': '17.9.4a',
                'warranty_status': 'active',
                'end_of_life': '2027-01-01',
                'end_of_support': '2030-01-01',
            }]
        }

    def test_title_case_plugin_csv_parses(self):
        csv_text = format_asset_warranty_csv(self._sample_assets(), '10.0.0.1')
        devices = self.cons._parse_csv_report(csv_text)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['hostname'], 'sw1.lab')
        self.assertEqual(devices[0]['serial'], 'FDO1234567')
        self.assertEqual(devices[0]['model'], 'C9300-48P')
        self.assertEqual(devices[0]['ip'], '10.0.0.1')

    def test_pretty_printed_html_with_newlines_parses(self):
        html = '''<!DOCTYPE html><html><body>
        <table class="nst-asset-table">
          <tr>
            <th>Host</th>
            <th>Hostname</th>
            <th>Product ID (PID)</th>
            <th>Serial Number</th>
            <th>Software Version</th>
            <th>Warranty Status</th>
            <th>End of Life</th>
            <th>End of Support</th>
          </tr>
          <tr>
            <td>
              10.0.0.1
            </td>
            <td>
              sw1.lab
            </td>
            <td><a class="nst-clickable-pid">C9300-48P</a></td>
            <td>
              FDO1234567
            </td>
            <td>17.9.4a</td>
            <td><span class="nst-status-badge">Active</span></td>
            <td>2027-01-01</td>
            <td>2030-01-01</td>
          </tr>
        </table>
        <div id="nst-cisco-eol-modal"><table><tr><td>fake</td><td>FAKE123</td></tr></table></div>
        <script>var x = "<tr><td>evil</td></tr>";</script>
        </body></html>'''
        devices = self.cons._parse_html_report(html)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['hostname'], 'sw1.lab')
        self.assertEqual(devices[0]['serial'], 'FDO1234567')
        self.assertEqual(devices[0]['model'], 'C9300-48P')
        self.assertNotIn('FAKE123', [d.get('serial') for d in devices])

    def test_format_asset_warranty_html_output_parses(self):
        html = format_asset_warranty_html(self._sample_assets(), '10.0.0.1')
        devices = self.cons._parse_html_report(html)
        self.assertGreaterEqual(len(devices), 1)
        serials = {d['serial'] for d in devices}
        self.assertIn('FDO1234567', serials)

    def test_multi_file_html_and_csv_consolidate_emits_both(self):
        csv1 = format_asset_warranty_csv(self._sample_assets('10.0.0.1', 'sw1', 'FDO111'), '10.0.0.1')
        csv2 = format_asset_warranty_csv(self._sample_assets('10.0.0.2', 'sw2', 'FDO222'), '10.0.0.2')
        html = '''<!DOCTYPE html><html><body><table class="nst-asset-table">
          <tr><th>Host</th><th>Hostname</th><th>Product ID (PID)</th><th>Serial Number</th>
          <th>Software Version</th><th>Warranty Status</th><th>End of Life</th><th>End of Support</th></tr>
          <tr><td>10.0.0.3</td><td>sw3</td><td>C9500-40X</td><td>FDO333</td><td>17.6</td>
          <td>active</td><td>2028-01-01</td><td>2031-01-01</td></tr>
        </table></body></html>'''

        (self.cons.input_dir / 'asset_sw1.csv').write_text(csv1, encoding='utf-8')
        (self.cons.input_dir / 'asset_sw2.csv').write_text(csv2, encoding='utf-8')
        (self.cons.input_dir / 'asset_sw3.html').write_text(html, encoding='utf-8')

        result = self.cons.consolidate_reports('mutual')
        self.assertTrue(result['success'])
        self.assertEqual(result['summary']['total_devices'], 3)
        self.assertTrue(result.get('output_csv'))
        html_path = Path(result['output_path'])
        csv_path = Path(result['output_csv_path'])
        self.assertTrue(html_path.exists())
        self.assertTrue(csv_path.exists())
        csv_body = csv_path.read_text(encoding='utf-8')
        self.assertIn('FDO111', csv_body)
        self.assertIn('FDO222', csv_body)
        self.assertIn('FDO333', csv_body)
        html_body = html_path.read_text(encoding='utf-8')
        self.assertTrue(
            re.search(r'(?:Unique|Total)\s+Devices', html_body, re.I),
            'HTML must show Unique Devices or Total Devices summary',
        )
        self.assertIn('>3<', html_body.replace(' ', ''))

    def test_dedupe_by_serial_keeps_richer_row(self):
        devices = [
            {'hostname': 'a', 'serial': 'ABC', 'model': '', 'ip': '', 'warranty_status': 'unknown', 'warranty_end': ''},
            {'hostname': 'a', 'serial': 'ABC', 'model': 'C9300', 'ip': '1.1.1.1', 'warranty_status': 'active', 'warranty_end': '2027'},
        ]
        out = self.cons._dedupe_devices(devices)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]['model'], 'C9300')


if __name__ == '__main__':
    unittest.main()
