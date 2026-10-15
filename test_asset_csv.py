"""Test script for asset warranty CSV generation."""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.report_formatter import format_asset_warranty_csv

# Test data simulating plugin output
test_data = {
    'host': '192.168.1.1',
    'timestamp': '2026-09-06T10:30:00',
    'collection_summary': 'ssh',
    'assets': [
        {
            'hostname': 'switch-core-01',
            'collection_method': 'ssh',
            'pid': 'C9300-48P',
            'vid': 'V01',
            'serial_number': 'FOC1234ABCD',
            'software_version': '17.9.4',
            'device_type': 'cisco_ios',
            'warranty_end': '',
            'warranty_status': 'unknown',
            'contract_status': 'Requires Cisco SN2INFO/EoX API or portal',
            'severity': 'info',
            'error': '',
        },
        {
            'hostname': 'switch-core-01',
            'collection_method': 'ssh',
            'pid': 'C9300-48P',
            'vid': 'V01',
            'serial_number': 'FOC1234ABCE',
            'software_version': '17.9.4',
            'device_type': 'cisco_ios',
            'warranty_end': '',
            'warranty_status': 'unknown',
            'contract_status': 'Requires Cisco SN2INFO/EoX API or portal',
            'severity': 'info',
            'error': '',
        }
    ],
    'asset_count': 2
}

# Generate CSV
csv_content = format_asset_warranty_csv(test_data, '192.168.1.1')

print("=== CSV Content ===")
print(csv_content)
print("\n=== Verification ===")

# Verify CSV has proper structure
lines = csv_content.strip().split('\n')
print(f"Total lines: {len(lines)}")
print(f"Header line: {lines[0]}")
print(f"Number of data rows: {len(lines) - 1}")

# Check for proper column separation
header_columns = lines[0].split(',')
print(f"Number of columns in header: {len(header_columns)}")
print(f"Column names: {header_columns}")

# Verify each data row has same number of columns
for i, line in enumerate(lines[1:], 1):
    columns = line.split(',')
    if len(columns) != len(header_columns):
        print(f"ERROR: Row {i} has {len(columns)} columns, expected {len(header_columns)}")
    else:
        print(f"Row {i}: OK ({len(columns)} columns)")

print("\n=== Test Complete ===")
