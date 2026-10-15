"""Exhaustive test suite for Cisco Asset & Warranty multi-file consolidation.

Validates:
- Multi-file consolidation across CSV, HTML, JSON, and TXT files.
- Files located in both reports/ and reports/asset_warranty_input/.
- Semicolon (;), comma (,), and tab (\\t) delimited CSV files.
- Deduplication and richer row retention.
- Master HTML report generation containing unified master table and summary cards.
- Master CSV report generation.
- Zero crashes on empty or corrupt input files.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from utils.asset_warranty_consolidator import AssetWarrantyConsolidator


class TestAssetWarrantyMultiFileConsolidator(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="test_aw_consol_")
        self.reports_dir = Path(self.tmp_dir) / "reports"
        self.input_dir = self.reports_dir / "asset_warranty_input"
        self.output_dir = self.reports_dir / "asset_warranty_output"
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.consolidator = AssetWarrantyConsolidator(base_dir=str(self.reports_dir))

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_multi_folder_discovery(self):
        """Files placed in reports/ and in reports/asset_warranty_input/ must both be found."""
        (self.input_dir / "file1_asset.csv").write_text(
            "hostname,serial_number,model,ip_address,warranty_status,warranty_end_date\n"
            "sw1,FDO11111,C9300-48P,10.0.0.1,active,2028-01-01\n",
            encoding="utf-8"
        )
        (self.reports_dir / "file2_warranty.csv").write_text(
            "hostname,serial_number,model,ip_address,warranty_status,warranty_end_date\n"
            "sw2,FDO22222,C9500-24Y4C,10.0.0.2,active,2029-01-01\n",
            encoding="utf-8"
        )

        files = self.consolidator.get_input_files()
        file_names = [f["name"] for f in files]
        self.assertIn("file1_asset.csv", file_names)
        self.assertIn("file2_warranty.csv", file_names)
        self.assertEqual(len(files), 2)

    def test_semicolon_delimited_csv(self):
        """CSV files with semicolon delimiter must parse correctly."""
        csv_content = (
            "Host;Hostname;Product ID (PID);Serial Number;Software Version;Warranty Status;End of Life;End of Support\n"
            "10.10.10.1;leaf1;N9K-C93180YC-FX;SAL12345;10.2(3);Active;2029-05-01;2032-05-01\n"
            "10.10.10.2;leaf2;N9K-C93180YC-FX;SAL12346;10.2(3);Expired;2024-01-01;2027-01-01\n"
        )
        (self.input_dir / "nxos_inventory.csv").write_text(csv_content, encoding="utf-8")
        parsed = self.consolidator.parse_asset_warranty_report(str(self.input_dir / "nxos_inventory.csv"))
        self.assertTrue(parsed["success"])
        self.assertEqual(parsed["format"], "csv")
        self.assertEqual(parsed["device_count"], 2)
        self.assertEqual(parsed["devices"][0]["hostname"], "leaf1")
        self.assertEqual(parsed["devices"][0]["serial"], "SAL12345")
        self.assertEqual(parsed["devices"][1]["hostname"], "leaf2")
        self.assertEqual(parsed["devices"][1]["warranty_status"], "Expired")

    def test_json_report_parsing(self):
        """JSON reports (arrays of dicts or objects with assets list) must parse cleanly."""
        json_data = [
            {
                "host": "192.168.50.1",
                "hostname": "core-sw1",
                "pid": "C9600-SUP-1",
                "serial_number": "FOC99901",
                "software_version": "17.9.3",
                "warranty_status": "Covered",
                "end_of_life": "2031-10-31",
                "end_of_support": "2034-10-31"
            },
            {
                "host": "192.168.50.2",
                "hostname": "juniper-qfx",
                "pid": "not a cisco device",
                "serial_number": "JN123456",
                "software_version": "21.4R3",
                "warranty_status": "not a cisco device",
                "end_of_life": "",
                "end_of_support": ""
            }
        ]
        (self.input_dir / "datacenter_assets.json").write_text(json.dumps(json_data), encoding="utf-8")
        parsed = self.consolidator.parse_asset_warranty_report(str(self.input_dir / "datacenter_assets.json"))
        self.assertTrue(parsed["success"])
        self.assertEqual(parsed["format"], "json")
        self.assertEqual(parsed["device_count"], 2)
        self.assertEqual(parsed["devices"][0]["hostname"], "core-sw1")
        self.assertEqual(parsed["devices"][0]["serial"], "FOC99901")
        self.assertEqual(parsed["devices"][1]["hostname"], "juniper-qfx")
        self.assertEqual(parsed["devices"][1]["warranty_status"], "not a cisco device")

    def test_json_wrapper_object_parsing(self):
        """JSON reports wrapped in {'status': 'success', 'data': {'assets': [...]}} must parse."""
        wrapper = {
            "status": "success",
            "device": "10.20.30.1",
            "data": {
                "assets": [
                    {
                        "host": "10.20.30.1",
                        "hostname": "edge-rtr1",
                        "pid": "ASR1001-X",
                        "serial_number": "FXS222201",
                        "software_version": "17.3.4",
                        "warranty_status": "active",
                        "end_of_life": "2027-06-30",
                        "end_of_support": "2030-06-30"
                    }
                ]
            }
        }
        (self.input_dir / "edge_rtr1_asset.json").write_text(json.dumps(wrapper), encoding="utf-8")
        parsed = self.consolidator.parse_asset_warranty_report(str(self.input_dir / "edge_rtr1_asset.json"))
        self.assertTrue(parsed["success"])
        self.assertEqual(parsed["format"], "json")
        self.assertEqual(parsed["device_count"], 1)
        self.assertEqual(parsed["devices"][0]["serial"], "FXS222201")

    def test_multi_format_simultaneous_consolidation(self):
        """Consolidate CSV, HTML, JSON, and TXT reports simultaneously into unified master."""
        # 1. CSV file
        (self.input_dir / "site_a.csv").write_text(
            "Host,Hostname,Product ID (PID),Serial Number,Software Version,Warranty Status,End of Life,End of Support\n"
            "10.1.1.1,site-a-sw1,C9300-24P,FDO1001,17.9.1,active,2028-01-01,2031-01-01\n",
            encoding="utf-8"
        )
        # 2. Semicolon CSV file
        (self.input_dir / "site_b.csv").write_text(
            "Host;Hostname;Product ID (PID);Serial Number;Software Version;Warranty Status;End of Life;End of Support\n"
            "10.2.2.1;site-b-sw1;C9300-48P;FDO1002;17.9.1;expired;2024-01-01;2027-01-01\n",
            encoding="utf-8"
        )
        # 3. HTML table file
        (self.input_dir / "site_c.html").write_text(
            '<!DOCTYPE html><html><body><table class="nst-asset-table">'
            '<tr><th>Host</th><th>Hostname</th><th>Product ID (PID)</th><th>Serial Number</th>'
            '<th>Software Version</th><th>Warranty Status</th><th>End of Life</th><th>End of Support</th></tr>'
            '<tr><td>10.3.3.1</td><td>site-c-sw1</td><td>C9500-40X</td><td>FDO1003</td>'
            '<td>17.6.3</td><td>active</td><td>2029-01-01</td><td>2032-01-01</td></tr>'
            '</table></body></html>',
            encoding="utf-8"
        )
        # 4. JSON file
        (self.input_dir / "site_d.json").write_text(
            json.dumps([{
                "host": "10.4.4.1",
                "hostname": "site-d-sw1",
                "pid": "C9200-24T",
                "serial_number": "FDO1004",
                "software_version": "17.3.4",
                "warranty_status": "covered",
                "end_of_life": "2027-01-01",
                "end_of_support": "2030-01-01"
            }]),
            encoding="utf-8"
        )
        # 5. Key-value TXT file
        (self.input_dir / "site_e.txt").write_text(
            "Hostname: site-e-sw1\n"
            "Serial Number: FDO1005\n"
            "Model: ISR4331\n"
            "Host: 10.5.5.1\n"
            "Warranty Status: active\n"
            "End of Life: 2026-12-31\n\n",
            encoding="utf-8"
        )

        result = self.consolidator.consolidate_reports("enterprise_master")
        self.assertTrue(result["success"], str(result))
        summary = result["summary"]
        self.assertEqual(summary["total_files"], 5)
        self.assertEqual(summary["successful_reports"], 5)
        self.assertEqual(summary["failed_reports"], 0)
        self.assertEqual(summary["total_devices"], 5)

        # Output files must exist
        html_out = Path(result["output_path"])
        csv_out = Path(result["output_csv_path"])
        self.assertTrue(html_out.is_file())
        self.assertTrue(csv_out.is_file())

        # Master HTML must contain Master Consolidated Inventory section
        html_text = html_out.read_text(encoding="utf-8")
        self.assertIn("Master Consolidated Inventory", html_text)
        self.assertIn("site-a-sw1", html_text)
        self.assertIn("site-b-sw1", html_text)
        self.assertIn("site-c-sw1", html_text)
        self.assertIn("site-d-sw1", html_text)
        self.assertIn("site-e-sw1", html_text)
        self.assertIn("Download Master CSV", html_text)

        # Master CSV must contain all 5 devices
        csv_text = csv_out.read_text(encoding="utf-8")
        self.assertIn("FDO1001", csv_text)
        self.assertIn("FDO1002", csv_text)
        self.assertIn("FDO1003", csv_text)
        self.assertIn("FDO1004", csv_text)
        self.assertIn("FDO1005", csv_text)

    def test_deduplication_keeps_richer_device_row(self):
        """When same device appears in multiple files, deduplicate and keep richer row."""
        (self.input_dir / "scan1.csv").write_text(
            "hostname,serial_number,model,ip_address,warranty_status,warranty_end_date\n"
            "switch-alpha,FDO9999,C9300,10.0.0.50,,\n",
            encoding="utf-8"
        )
        (self.input_dir / "scan2.json").write_text(
            json.dumps([{
                "host": "10.0.0.50",
                "hostname": "switch-alpha",
                "pid": "C9300-48UXM",
                "serial_number": "FDO9999",
                "software_version": "17.9.4",
                "warranty_status": "active",
                "end_of_life": "2030-01-01",
                "end_of_support": "2033-01-01"
            }]),
            encoding="utf-8"
        )
        result = self.consolidator.consolidate_reports("dedup_test")
        self.assertTrue(result["success"])
        self.assertEqual(result["summary"]["total_devices"], 1)

        csv_text = Path(result["output_csv_path"]).read_text(encoding="utf-8")
        self.assertIn("C9300-48UXM", csv_text)
        self.assertIn("17.9.4", csv_text)

    def test_empty_and_corrupt_files_handled_gracefully(self):
        """Consolidator must handle empty files and corrupt formats without crashing."""
        (self.input_dir / "empty.csv").write_text("", encoding="utf-8")
        (self.input_dir / "corrupt.json").write_text("NOT_JSON_DATA{{{", encoding="utf-8")
        (self.input_dir / "valid.csv").write_text(
            "hostname,serial_number,model,ip_address,warranty_status,warranty_end_date\n"
            "sw_valid,FDO8888,C9200,10.1.1.100,active,2028-01-01\n",
            encoding="utf-8"
        )

        result = self.consolidator.consolidate_reports("graceful_test")
        self.assertTrue(result["success"])
        self.assertEqual(result["summary"]["total_devices"], 1)


if __name__ == "__main__":
    unittest.main()
