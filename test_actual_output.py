#!/usr/bin/env python3
"""Test actual plugin output to verify enrichment is working."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.plugins.cisco_asset_warranty_plugin import run
from utils.report_formatter import format_asset_warranty_csv, format_asset_warranty_html

# Mock data - simulate collected device
mock_assets = [
    {
        'hostname': 'SWITCH-01',
        'collection_method': 'SSH',
        'pid': 'WS-C2960X-48TS-L',  # Catalyst 2960X
        'vid': 'V03',
        'serial_number': 'FOC1234ABCD',
        'software_version': '15.2(2)E7',
        'device_type': 'Switch',
    },
    {
        'hostname': 'SWITCH-02',
        'collection_method': 'SNMP',
        'pid': 'N9K-C93180YC-EX',  # Nexus 93180
        'vid': 'V01',
        'serial_number': 'JAF1234ABCD',
        'software_version': '9.3(5)',
        'device_type': 'Switch',
    }
]

# Mock log function
def log_func(msg):
    print(f"[LOG] {msg}")

# Test enrichment
print("=" * 60)
print("TESTING ACTUAL ENRICHMENT")
print("=" * 60)

from modules.cisco_eol_database import enrich_asset_data

for asset in mock_assets:
    print(f"\nBefore enrichment: PID={asset.get('pid')}")
    print(f"  end_of_life: {asset.get('end_of_life', 'NOT SET')}")
    print(f"  end_of_support: {asset.get('end_of_support', 'NOT SET')}")
    print(f"  warranty_status: {asset.get('warranty_status', 'NOT SET')}")
    
    enrich_asset_data(asset, log_func)
    
    print(f"\nAfter enrichment: PID={asset.get('pid')}")
    print(f"  end_of_life: {asset.get('end_of_life', 'NOT SET')}")
    print(f"  end_of_support: {asset.get('end_of_support', 'NOT SET')}")
    print(f"  warranty_status: {asset.get('warranty_status', 'NOT SET')}")
    print(f"  model_name: {asset.get('model_name', 'NOT SET')}")

# Test CSV output
print("\n" + "=" * 60)
print("TESTING CSV OUTPUT")
print("=" * 60)

data = {
    'host': '192.168.1.1',
    'timestamp': '2026-09-06 12:00:00',
    'assets': mock_assets
}

csv_output = format_asset_warranty_csv(data, '192.168.1.1')
print("\nCSV Output (first 500 chars):")
print(csv_output[:500])

# Check if CSV has EOL columns
if 'End of Life Date' in csv_output and 'End of Support Date' in csv_output:
    print("\n✅ CSV has EOL/EOS columns")
else:
    print("\n❌ CSV MISSING EOL/EOS columns")

# Check if CSV has enriched data
if '2027' in csv_output or '2029' in csv_output or '2025' in csv_output:
    print("✅ CSV has enriched date data")
else:
    print("❌ CSV MISSING enriched date data")

# Test HTML output
print("\n" + "=" * 60)
print("TESTING HTML OUTPUT")
print("=" * 60)

html_output = format_asset_warranty_html(data, '192.168.1.1')
print("\nHTML Output (first 500 chars):")
print(html_output[:500])

# Check if HTML has database loading
if 'Data loaded from Cisco EOL/EOS database' in html_output:
    print("\n✅ HTML loads from database")
else:
    print("\n❌ HTML NOT loading from database")

# Check if HTML has clickable PIDs
if 'nst-clickable-pid' in html_output:
    print("✅ HTML has clickable PIDs")
else:
    print("❌ HTML MISSING clickable PIDs")

# Check HTML modal
if 'nst-cisco-eol-modal' in html_output:
    print("✅ HTML has modal")
else:
    print("❌ HTML MISSING modal")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
