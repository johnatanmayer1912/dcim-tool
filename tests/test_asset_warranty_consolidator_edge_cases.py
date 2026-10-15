"""Edge case tests for Asset Warranty Consolidator HTML parser"""
import unittest
import tempfile
import os
from pathlib import Path
from utils.asset_warranty_consolidator import AssetWarrantyConsolidator


class TestAssetWarrantyConsolidatorEdgeCases(unittest.TestCase):
    """Test edge cases for the asset warranty consolidator HTML parser"""

    def setUp(self):
        """Set up test fixtures"""
        self.consolidator = AssetWarrantyConsolidator()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_html_parser_multiline_table(self):
        """Test HTML parser with multi-line table structure"""
        html_content = """<!DOCTYPE html>
<html>
<body>
    <table>
        <tr>
            <td>switch1</td>
            <td>FDO12345</td>
            <td>Catalyst 9300</td>
        </tr>
        <tr>
            <td>switch2</td>
            <td>FDO12346</td>
            <td>Catalyst 3850</td>
        </tr>
    </table>
</body>
</html>"""
        
        devices = self.consolidator._parse_html_report(html_content)
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]['hostname'], 'switch1')
        self.assertEqual(devices[1]['hostname'], 'switch2')

    def test_html_parser_with_headers(self):
        """Test HTML parser properly skips header rows"""
        html_content = """<!DOCTYPE html>
<html>
<body>
    <table>
        <tr>
            <th>Hostname</th>
            <th>Serial</th>
            <th>Model</th>
        </tr>
        <tr>
            <td>switch1</td>
            <td>FDO12345</td>
            <td>Catalyst 9300</td>
        </tr>
    </table>
</body>
</html>"""
        
        devices = self.consolidator._parse_html_report(html_content)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['hostname'], 'switch1')

    def test_html_parser_with_html_entities(self):
        """Test HTML parser handles HTML entities correctly"""
        html_content = """<!DOCTYPE html>
<html>
<body>
    <table>
        <tr>
            <td>switch&amp;1</td>
            <td>FDO12345</td>
            <td>Catalyst&nbsp;9300</td>
        </tr>
    </table>
</body>
</html>"""
        
        devices = self.consolidator._parse_html_report(html_content)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['hostname'], 'switch&1')
        self.assertEqual(devices[0]['model'], 'Catalyst 9300')

    def test_html_parser_with_nested_tags(self):
        """Test HTML parser handles nested tags in cells"""
        html_content = """<!DOCTYPE html>
<html>
<body>
    <table>
        <tr>
            <td><strong>switch1</strong></td>
            <td><span>FDO12345</span></td>
            <td>Catalyst 9300</td>
        </tr>
    </table>
</body>
</html>"""
        
        devices = self.consolidator._parse_html_report(html_content)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['hostname'], 'switch1')
        self.assertEqual(devices[0]['serial'], 'FDO12345')

    def test_html_parser_empty_table(self):
        """Test HTML parser with empty table"""
        html_content = """<!DOCTYPE html>
<html>
<body>
    <table>
        <tr>
            <th>Hostname</th>
            <th>Serial</th>
        </tr>
    </table>
</body>
</html>"""
        
        devices = self.consolidator._parse_html_report(html_content)
        self.assertEqual(len(devices), 0)

    def test_html_parser_malformed_html(self):
        """Test HTML parser with malformed HTML (missing closing tag)"""
        html_content = """<!DOCTYPE html>
<html>
<body>
    <table>
        <tr>
            <td>switch1</td>
            <td>FDO12345</td>
        </tr>
        <tr>
            <td>switch2</td>
            <td>FDO12346</td>
        </tr>
    </table>
</body>
</html>"""
        
        devices = self.consolidator._parse_html_report(html_content)
        # Should extract both complete rows
        self.assertEqual(len(devices), 2)

    def test_html_parser_with_attributes(self):
        """Test HTML parser handles table/cell attributes"""
        html_content = """<!DOCTYPE html>
<html>
<body>
    <table class="data-table">
        <tr style="color: red;">
            <td class="hostname">switch1</td>
            <td data-serial="FDO12345">FDO12345</td>
            <td>Catalyst 9300</td>
        </tr>
    </table>
</body>
</html>"""
        
        devices = self.consolidator._parse_html_report(html_content)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['hostname'], 'switch1')

    def test_html_parser_case_insensitive(self):
        """Test HTML parser is case insensitive"""
        html_content = """<!DOCTYPE html>
<html>
<body>
    <TABLE>
        <TR>
            <TD>switch1</TD>
            <TD>FDO12345</TD>
            <TD>Catalyst 9300</TD>
        </TR>
    </TABLE>
</body>
</html>"""
        
        devices = self.consolidator._parse_html_report(html_content)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['hostname'], 'switch1')

    def test_html_parser_extra_whitespace(self):
        """Test HTML parser handles extra whitespace"""
        html_content = """<!DOCTYPE html>
<html>
<body>
    <table>
        <tr>
            <td>  switch1  </td>
            <td>  FDO12345  </td>
            <td>  Catalyst 9300  </td>
        </tr>
    </table>
</body>
</html>"""
        
        devices = self.consolidator._parse_html_report(html_content)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['hostname'], 'switch1')
        self.assertEqual(devices[0]['serial'], 'FDO12345')

    def test_html_parser_multiple_tables(self):
        """Test HTML parser with multiple tables"""
        html_content = """<!DOCTYPE html>
<html>
<body>
    <table>
        <tr>
            <td>switch1</td>
            <td>FDO12345</td>
            <td>Catalyst 9300</td>
        </tr>
    </table>
    <table>
        <tr>
            <td>switch2</td>
            <td>FDO12346</td>
            <td>Catalyst 3850</td>
        </tr>
    </table>
</body>
</html>"""
        
        devices = self.consolidator._parse_html_report(html_content)
        self.assertEqual(len(devices), 2)

    def test_csv_parser_standard(self):
        """Test CSV parser with standard format"""
        csv_content = """hostname,serial_number,model,ip_address,warranty_status,warranty_end_date
switch1,FDO12345,Catalyst 9300,192.168.1.1,Active,2028-12-31
switch2,FDO12346,Catalyst 3850,192.168.1.2,Expired,2023-06-30"""
        
        devices = self.consolidator._parse_csv_report(csv_content)
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]['hostname'], 'switch1')
        self.assertEqual(devices[1]['hostname'], 'switch2')

    def test_csv_parser_alternate_columns(self):
        """Test CSV parser with alternate column names"""
        csv_content = """device,serial,product_id,ip,coverage,end_date
switch1,FDO12345,Catalyst 9300,192.168.1.1,Covered,2028-12-31
switch2,FDO12346,Catalyst 3850,192.168.1.2,Expired,2023-06-30"""
        
        devices = self.consolidator._parse_csv_report(csv_content)
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]['hostname'], 'switch1')

    def test_text_parser_standard(self):
        """Test text parser with standard format"""
        text_content = """Hostname: switch1
Serial: FDO12345
Model: Catalyst 9300
IP: 192.168.1.1
Warranty: Active

Hostname: switch2
Serial: FDO12346
Model: Catalyst 3850
IP: 192.168.1.2
Warranty: Expired"""
        
        devices = self.consolidator._parse_text_report(text_content)
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]['hostname'], 'switch1')
        self.assertEqual(devices[1]['hostname'], 'switch2')

    def test_consolidator_mixed_formats(self):
        """Test consolidator with mixed CSV and HTML files"""
        # Create test files
        csv_file = Path(self.temp_dir) / "test.csv"
        csv_file.write_text("""hostname,serial_number,model,ip_address,warranty_status,warranty_end_date
switch1,FDO12345,Catalyst 9300,192.168.1.1,Active,2028-12-31""")
        
        html_file = Path(self.temp_dir) / "test.html"
        html_file.write_text("""<!DOCTYPE html>
<html>
<body>
    <table>
        <tr>
            <td>switch2</td>
            <td>FDO12346</td>
            <td>Catalyst 3850</td>
        </tr>
    </table>
</body>
</html>""")
        
        # Test parsing individual files
        csv_result = self.consolidator.parse_asset_warranty_report(str(csv_file))
        html_result = self.consolidator.parse_asset_warranty_report(str(html_file))
        
        self.assertTrue(csv_result['success'])
        self.assertTrue(html_result['success'])
        self.assertEqual(csv_result['device_count'], 1)
        self.assertEqual(html_result['device_count'], 1)

    def test_consolidator_empty_hostname(self):
        """Test consolidator handles empty hostname but valid serial"""
        html_content = """<!DOCTYPE html>
<html>
<body>
    <table>
        <tr>
            <td></td>
            <td>FDO12345</td>
            <td>Catalyst 9300</td>
        </tr>
    </table>
</body>
</html>"""
        
        devices = self.consolidator._parse_html_report(html_content)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['serial'], 'FDO12345')

    def test_consolidator_minimal_data(self):
        """Test consolidator with minimal valid data"""
        html_content = """<!DOCTYPE html>
<html>
<body>
    <table>
        <tr>
            <td>switch1</td>
            <td>FDO12345</td>
            <td>Catalyst 9300</td>
        </tr>
    </table>
</body>
</html>"""
        
        devices = self.consolidator._parse_html_report(html_content)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['hostname'], 'switch1')
        self.assertEqual(devices[0]['serial'], 'FDO12345')
        self.assertEqual(devices[0]['model'], 'Catalyst 9300')


if __name__ == '__main__':
    unittest.main()