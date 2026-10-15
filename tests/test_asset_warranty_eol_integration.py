"""Integration tests for Cisco Asset & Warranty plugin with EOL/EOS enrichment."""
import unittest
import os
import sys
import csv
import io

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.report_formatter import format_asset_warranty_csv, format_asset_warranty_html


class TestAssetWarrantyEolIntegration(unittest.TestCase):
    """Integration tests for EOL/EOS enrichment in asset warranty plugin."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_assets = [
            {
                'hostname': 'switch1',
                'collection_method': 'ssh',
                'pid': 'N9K-C93180YC-EX',
                'vid': 'V01',
                'serial_number': 'FOC1234ABCD',
                'software_version': '17.3(1)',
                'device_type': 'cisco_nxos',
                'model_name': 'Nexus 93180YC-EX 48p 10/25G & 6p 100G',
                'end_of_life': '2027-08-31',
                'end_of_support': '2027-08-31',
                'end_of_service': '2027-08-31',
                'warranty_status': 'active',
                'warranty_end': '',
                'contract_status': '',
                'severity': 'info',
                'error': '',
            },
            {
                'hostname': 'switch2',
                'collection_method': 'ssh',
                'pid': 'N9K-C92160YC-X',
                'vid': 'V02',
                'serial_number': 'FOC5678EFGH',
                'software_version': '9.3(5)',
                'device_type': 'cisco_nxos',
                'model_name': 'Nexus 92160YC-X 48p 10G SFP+ & 6p 40G OR 4p 100G',
                'end_of_life': '2026-03-31',
                'end_of_support': '2026-03-31',
                'end_of_service': '2026-03-31',
                'warranty_status': 'warning',
                'warranty_end': '',
                'contract_status': '',
                'severity': 'warning',
                'error': '',
            },
            {
                'hostname': 'switch3',
                'collection_method': 'ssh',
                'pid': 'WS-C3750X-48S',
                'vid': 'V03',
                'serial_number': 'FOC9999ZZZZ',
                'software_version': '15.2(4)',
                'device_type': 'cisco_ios',
                'model_name': 'Catalyst 3750X 48-port',
                'end_of_life': '2019-11-30',
                'end_of_support': '2019-11-30',
                'end_of_service': '2019-11-30',
                'warranty_status': 'expired',
                'warranty_end': '',
                'contract_status': '',
                'severity': 'critical',
                'error': '',
            },
        ]
        
        self.result_data = {
            'host': '192.168.1.1',
            'timestamp': '2026-09-06T12:00:00',
            'collection_summary': '3 assets collected',
            'assets': self.sample_assets,
            'asset_count': 3,
        }

    def test_csv_generation_with_eol_columns(self):
        """Test CSV generation includes EOL/EOS columns (demo-aligned format)."""
        csv_content = format_asset_warranty_csv(self.result_data, '192.168.1.1')
        
        self.assertIsNotNone(csv_content)
        self.assertGreater(len(csv_content), 0)
        
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        header = rows[0]
        self.assertIn('Product ID (PID)', header)
        self.assertIn('End of Life', header)
        self.assertIn('End of Support', header)
        self.assertIn('Warranty Status', header)
        
        self.assertEqual(len(rows), 4)  # header + 3 data rows
        
        first_row = rows[1]
        pid_idx = header.index('Product ID (PID)')
        eol_idx = header.index('End of Life')
        eos_idx = header.index('End of Support')
        status_idx = header.index('Warranty Status')
        
        self.assertEqual(first_row[pid_idx], 'N9K-C93180YC-EX')
        self.assertEqual(first_row[eol_idx], '2027-08-31')
        self.assertEqual(first_row[eos_idx], '2027-08-31')
        self.assertEqual(first_row[status_idx], 'active')

    def test_csv_warranty_status_values(self):
        """Test CSV contains correct warranty status values."""
        csv_content = format_asset_warranty_csv(self.result_data, '192.168.1.1')
        
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)
        header = rows[0]
        status_idx = header.index('Warranty Status')
        
        self.assertEqual(rows[1][status_idx], 'active')  # N9K-C93180YC-EX
        self.assertEqual(rows[2][status_idx], 'warning')  # N9K-C92160YC-X
        self.assertEqual(rows[3][status_idx], 'expired')  # WS-C3750X-48S

    def test_csv_empty_assets(self):
        """Test CSV generation with empty assets list."""
        empty_data = {
            'host': '192.168.1.1',
            'timestamp': '2026-09-06T12:00:00',
            'collection_summary': 'No assets',
            'assets': [],
            'asset_count': 0,
        }
        
        csv_content = format_asset_warranty_csv(empty_data, '192.168.1.1')
        self.assertEqual(csv_content, "")

    def test_html_generation_with_clickable_pids(self):
        """Test HTML generation includes clickable PIDs."""
        html_content = format_asset_warranty_html(self.result_data, '192.168.1.1')
        
        self.assertIsNotNone(html_content)
        self.assertGreater(len(html_content), 0)
        
        self.assertIn('nst-clickable-pid', html_content)
        self.assertIn('nst-cisco-eol-modal', html_content)
        self.assertIn('openCiscoEolCatalog', html_content)
        self.assertIn('nst-eol-search', html_content)
        self.assertIn('filterCiscoEolCatalog', html_content)

    def test_html_status_badges(self):
        """Test HTML includes status badges."""
        html_content = format_asset_warranty_html(self.result_data, '192.168.1.1')
        
        self.assertIn('nst-status-badge', html_content)
        self.assertIn('nst-status-active', html_content)
        self.assertIn('nst-status-warning', html_content)
        self.assertIn('nst-status-expired', html_content)

    def test_html_modal_structure(self):
        """Test HTML modal has proper structure."""
        html_content = format_asset_warranty_html(self.result_data, '192.168.1.1')
        
        self.assertIn('nst-modal-overlay', html_content)
        self.assertIn('nst-modal-content', html_content)
        self.assertIn('nst-modal-header', html_content)
        self.assertIn('nst-modal-body', html_content)
        self.assertIn('nst-toolbar', html_content)
        self.assertIn('nst-btn-all', html_content)
        self.assertIn('nst-btn-active', html_content)
        self.assertIn('nst-btn-expired', html_content)
        self.assertIn('nst-btn-warning', html_content)

    def test_html_javascript_functions(self):
        """Test HTML includes required JavaScript functions."""
        html_content = format_asset_warranty_html(self.result_data, '192.168.1.1')
        
        self.assertIn('function openCiscoEolCatalog', html_content)
        self.assertIn('function closeCiscoEolCatalog', html_content)
        self.assertIn('function renderCiscoEolCatalog', html_content)
        self.assertIn('function filterCiscoEolCatalog', html_content)
        self.assertIn('function setCiscoEolFilter', html_content)
        self.assertIn('function highlightCiscoEolRow', html_content)

    def test_html_empty_assets(self):
        """Test HTML generation with empty assets list."""
        empty_data = {
            'host': '192.168.1.1',
            'timestamp': '2026-09-06T12:00:00',
            'collection_summary': 'No assets',
            'assets': [],
            'asset_count': 0,
        }
        
        html_content = format_asset_warranty_html(empty_data, '192.168.1.1')
        self.assertIn('No assets collected', html_content)

    def test_csv_column_order(self):
        """Test CSV columns are in correct order (demo-aligned consolidator format)."""
        csv_content = format_asset_warranty_csv(self.result_data, '192.168.1.1')
        
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)
        header = rows[0]
        
        expected_columns = [
            'Host',
            'Hostname',
            'Product ID (PID)',
            'Serial Number',
            'Software Version',
            'Warranty Status',
            'End of Life',
            'End of Support',
        ]
        
        self.assertEqual(header, expected_columns)

    def test_html_demo_data_inclusion(self):
        """Test HTML includes demo data in JavaScript."""
        html_content = format_asset_warranty_html(self.result_data, '192.168.1.1')
        
        self.assertIn('const ciscoEolData', html_content)
        self.assertIn('N9K-C93180YC-EX', html_content)
        self.assertIn('N9K-C9336C-FX2', html_content)


if __name__ == '__main__':
    unittest.main()
