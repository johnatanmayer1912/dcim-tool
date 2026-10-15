"""API-level tests for Asset Warranty consolidator endpoints."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class TestAssetWarrantyConsolidateAPI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.base = Path(self.tmp) / 'reports'
        self.base.mkdir(parents=True)
        # Import app lazily
        import vlan_checker_web as web
        self.web = web
        self.client = web.app.test_client()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_consolidate_api_returns_html_and_csv(self):
        from utils.asset_warranty_consolidator import AssetWarrantyConsolidator
        cons = AssetWarrantyConsolidator(base_dir=str(self.base))
        (cons.input_dir / 'asset_a.csv').write_text(
            'Host,Hostname,Product ID (PID),Serial Number,Software Version,Warranty Status,End of Life,End of Support\n'
            '10.0.0.1,sw1,C9300-48P,FDOAAA,17.9,active,2027-01-01,2030-01-01\n',
            encoding='utf-8',
        )
        (cons.input_dir / 'asset_b.html').write_text(
            '''<html><body><table class="nst-asset-table">
            <tr><th>Host</th><th>Hostname</th><th>Product ID (PID)</th><th>Serial Number</th>
            <th>Software Version</th><th>Warranty Status</th><th>End of Life</th><th>End of Support</th></tr>
            <tr><td>10.0.0.2</td><td>sw2</td><td>C9500</td><td>FDOBBB</td><td>17.6</td><td>active</td><td>2028-01-01</td><td>2031-01-01</td></tr>
            </table></body></html>''',
            encoding='utf-8',
        )

        with patch('utils.asset_warranty_consolidator.AssetWarrantyConsolidator',
                   lambda *a, **k: AssetWarrantyConsolidator(base_dir=str(self.base))):
            # Direct consolidator path (API uses default install root; we validate logic + response shape)
            result = cons.consolidate_reports('api_mutual')
            self.assertTrue(result['success'])
            self.assertEqual(result['summary']['total_devices'], 2)
            self.assertTrue(result['output_csv'])
            self.assertTrue(Path(result['output_csv_path']).exists())
            self.assertTrue(Path(result['output_path']).exists())

            # Exercise Flask route with patched consolidator
            with patch.object(self.web, 'AssetWarrantyConsolidator', create=True):
                pass
            # Call route by patching import inside handler
            with patch('utils.asset_warranty_consolidator.AssetWarrantyConsolidator',
                       side_effect=lambda *a, **k: AssetWarrantyConsolidator(base_dir=str(self.base))):
                resp = self.client.post(
                    '/api/reports/asset-warranty/consolidate',
                    data=json.dumps({'report_name': 'api_mutual'}),
                    content_type='application/json',
                )
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data['success'])
            self.assertGreaterEqual(data['summary']['total_devices'], 2)
            self.assertIn('output_csv', data)


if __name__ == '__main__':
    unittest.main()
