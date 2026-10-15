# ============================================================================
# AI_NAVIGATION_BREADCRUMBS - utils/asset_warranty_consolidator.py
# ============================================================================
# PURPOSE:
#   Multi-File Cisco Asset & Warranty Consolidator and Quad-Format Master Exporter.
#   Ingests multiple reports (CSV, HTML, JSON, TXT) across input directories,
#   performs intelligent Hardware UUID (Serial Number) deduplication, attribute
#   merging/enrichment, conflict detection, and generates synchronized Master reports
#   in HTML, CSV, JSON, and XLSX with an exhaustive Duplicates Audit.
#
# ARCHITECTURAL ROLE:
#   Hardware lifecycle management, inventory consolidation, and multi-file audit engine.
#
# KEY FUNCTIONS:
#   - consolidate_reports(report_name, file_paths): Main orchestrator
#   - deduplicate_devices_with_audit(devices): UUID-based deduplication & attribute merging
#   - _dedupe_devices(devices): Backward-compatible list wrapper
#   - parse_asset_warranty_report(file_path): Multi-format parser (CSV/HTML/JSON/TXT)
#   - _generate_master_html(...): Master HTML report with Duplicate Audit section
#   - _generate_master_csv(all_devices): Unified comma-delimited Master CSV
#   - _generate_master_json(all_devices, summary, ...): Master JSON with duplicates_audit
#   - _generate_master_xlsx(all_devices, path, ...): Multi-sheet Excel export via openpyxl
#
# CONNECTIONS:
#   - Called by: vlan_checker_web.py (POST /api/reports/asset-warranty/consolidate)
#   - Tested by: tests/test_asset_warranty_uuid_dedup.py, tests/browser/
#
# INVARIANTS:
#   - Serial Number is the primary Hardware UUID.
#   - Never drop metadata: merge non-empty attributes across duplicate records.
#   - Discrepancies across duplicate occurrences are logged as audit conflicts.
# ============================================================================
from __future__ import annotations

import csv
import io
import json
import re
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional



class AssetWarrantyConsolidator:
    """Consolidates multiple Cisco Asset Warranty reports into a single master report."""

    _HEADER_ALIASES = {
        'hostname': 'hostname',
        'device': 'hostname',
        'host name': 'hostname',
        'host': 'ip',
        'ip': 'ip',
        'ip_address': 'ip',
        'ip address': 'ip',
        'management ip': 'ip',
        'serial': 'serial',
        'serial_number': 'serial',
        'serial number': 'serial',
        'sn': 'serial',
        'model': 'model',
        'product_id': 'model',
        'product id': 'model',
        'product id (pid)': 'model',
        'pid': 'model',
        'warranty_status': 'warranty_status',
        'warranty status': 'warranty_status',
        'coverage': 'warranty_status',
        'status': 'warranty_status',
        'warranty_end': 'warranty_end',
        'warranty_end_date': 'warranty_end',
        'warranty end': 'warranty_end',
        'end_date': 'warranty_end',
        'end date': 'warranty_end',
        'end_of_life': 'end_of_life',
        'end of life': 'end_of_life',
        'eol': 'end_of_life',
        'software_version': 'software_version',
        'software version': 'software_version',
        'end_of_support': 'end_of_support',
        'end of support': 'end_of_support',
        'eos': 'end_of_support',
        'end_of_service': 'end_of_service',
        'end of service': 'end_of_service',
        'model_name': 'model_name',
        'model name': 'model_name',
    }

    _HEADER_TOKENS = {
        'hostname', 'device', 'serial', 'model', 'host', 'product', 'pid',
        'warranty', 'coverage', 'software', 'end of life', 'end of support',
    }

    def __init__(
        self,
        base_dir: Optional[str] = None,
        input_dir: Optional[str] = None,
        output_dir: Optional[str] = None,
    ):
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            if getattr(sys, 'frozen', False):
                install_root = Path(sys.executable).parent
            else:
                install_root = Path(__file__).parent.parent
            self.base_dir = install_root / "reports"

        self.input_dir = Path(input_dir) if input_dir else self.base_dir / "asset_warranty_input"
        self.output_dir = Path(output_dir) if output_dir else self.base_dir / "asset_warranty_output"
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_input_files(self) -> List[Dict[str, Any]]:
        files = []
        seen_paths = set()

        # Scan input_dir (e.g. reports/asset_warranty_input/)
        if self.input_dir.exists():
            for file_path in self.input_dir.iterdir():
                if file_path.is_file() and not file_path.name.startswith('.'):
                    if self._is_asset_warranty_file(file_path):
                        resolved = str(file_path.resolve())
                        if resolved not in seen_paths:
                            seen_paths.add(resolved)
                            files.append({
                                'name': file_path.name,
                                'path': str(file_path),
                                'size': file_path.stat().st_size,
                                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                            })

        # Also scan base_dir (e.g. reports/) for files placed directly under reports/
        if self.base_dir.exists():
            for file_path in self.base_dir.iterdir():
                if file_path.is_file() and not file_path.name.startswith('.'):
                    if self._is_asset_warranty_file(file_path):
                        resolved = str(file_path.resolve())
                        if resolved not in seen_paths:
                            seen_paths.add(resolved)
                            files.append({
                                'name': file_path.name,
                                'path': str(file_path),
                                'size': file_path.stat().st_size,
                                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                            })

        return sorted(files, key=lambda x: x['name'])

    def _is_asset_warranty_file(self, file_path: Path) -> bool:
        if file_path.suffix.lower() in ['.md', '.py', '.log', '.tmp', '.marker', '.pyc', '.bak']:
            return False
        name_lower = file_path.name.lower()
        if any(tok in name_lower for tok in ('asset', 'warranty', 'site', 'switch', 'inventory', 'hardware', 'device')):
            return True
        if file_path.suffix.lower() in ['.csv', '.html', '.txt', '.json']:
            return True
        return False

    def parse_asset_warranty_report(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        result = {
            'file_name': path.name,
            'file_path': str(path),
            'success': True,
            'error': None,
            'device_count': 0,
            'devices': [],
            'raw_content': '',
            'format': 'unknown'
        }

        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            result['raw_content'] = content

            if path.suffix.lower() == '.csv':
                result['format'] = 'csv'
                result['devices'] = self._parse_csv_report(content)
            elif path.suffix.lower() == '.html':
                result['format'] = 'html'
                result['devices'] = self._parse_html_report(content)
            elif path.suffix.lower() == '.json':
                result['format'] = 'json'
                result['devices'] = self._parse_json_report(content)
            else:
                stripped = content.strip()
                if stripped.startswith('{') or stripped.startswith('['):
                    try:
                        result['devices'] = self._parse_json_report(content)
                        result['format'] = 'json'
                    except Exception:
                        result['format'] = 'text'
                        result['devices'] = self._parse_text_report(content)
                else:
                    result['format'] = 'text'
                    result['devices'] = self._parse_text_report(content)

            for d in result['devices']:
                if isinstance(d, dict) and not d.get('source_file'):
                    d['source_file'] = path.name

            result['device_count'] = len(result['devices'])

        except Exception as e:
            result['success'] = False
            result['error'] = str(e)

        return result

    def _normalize_header(self, raw: str) -> str:
        key = re.sub(r'\s+', ' ', (raw or '').strip().lower())
        key = key.replace('_', ' ')
        key = re.sub(r'\s*\(pid\)\s*', ' (pid)', key).strip()
        return key

    def _map_header(self, raw: str) -> Optional[str]:
        key = self._normalize_header(raw)
        if key in self._HEADER_ALIASES:
            return self._HEADER_ALIASES[key]
        if 'product id' in key or key == 'pid':
            return 'model'
        if 'serial' in key:
            return 'serial'
        if key in ('hostname', 'device name'):
            return 'hostname'
        if 'warranty' in key and 'end' in key:
            return 'warranty_end'
        if 'warranty' in key or 'coverage' in key:
            return 'warranty_status'
        if 'end of life' in key or key in ('eol', 'end_of_life'):
            return 'end_of_life'
        if 'end of support' in key or key in ('eos', 'end_of_support'):
            return 'end_of_support'
        if 'end of service' in key or key == 'end_of_service':
            return 'end_of_service'
        if 'software' in key:
            return 'software_version'
        if key in ('ip', 'ip address'):
            return 'ip'
        if key == 'host':
            return 'ip'
        return None

    def _is_header_row(self, cells: List[str]) -> bool:
        if not cells:
            return False
        joined = ' '.join(c.lower() for c in cells)
        hits = sum(1 for tok in self._HEADER_TOKENS if tok in joined)
        first = (cells[0] or '').strip().lower()
        if first in {
            'hostname', 'device', 'serial', 'model', 'host',
            'product id (pid)', 'serial number', 'warranty status',
        }:
            return True
        return hits >= 2

    def _clean_cell_text(self, cell: str) -> str:
        cell_clean = re.sub(r'<[^>]+>', ' ', cell or '', flags=re.DOTALL)
        cell_clean = (
            cell_clean.replace('&nbsp;', ' ')
            .replace('&amp;', '&')
            .replace('&lt;', '<')
            .replace('&gt;', '>')
            .replace('&#39;', "'")
            .replace('&quot;', '"')
        )
        return re.sub(r'\s+', ' ', cell_clean).strip()

    def _device_from_mapped(self, mapped: Dict[str, str], line_number: int) -> Optional[Dict[str, Any]]:
        device = {
            'hostname': mapped.get('hostname', ''),
            'serial': mapped.get('serial', ''),
            'model': mapped.get('model', ''),
            'ip': mapped.get('ip', ''),
            'warranty_status': mapped.get('warranty_status', '') or 'unknown',
            'warranty_end': mapped.get('warranty_end', ''),
            'software_version': mapped.get('software_version', ''),
            'end_of_life': mapped.get('end_of_life', ''),
            'end_of_support': mapped.get('end_of_support', ''),
            'end_of_service': mapped.get('end_of_service', ''),
            'model_name': mapped.get('model_name', ''),
            'line_number': line_number,
        }
        if device['hostname'] or device['serial']:
            return device
        return None

    def _parse_csv_report(self, content: str) -> List[Dict[str, Any]]:
        devices: List[Dict[str, Any]] = []
        lines = [line for line in content.splitlines() if line.strip()]
        if not lines:
            return devices

        try:
            # Auto-detect delimiter (comma, semicolon, or tab)
            first_line = lines[0]
            delim = ','
            if ';' in first_line and first_line.count(';') > first_line.count(','):
                delim = ';'
            elif '\t' in first_line and first_line.count('\t') > first_line.count(','):
                delim = '\t'

            rows = list(csv.reader(lines, delimiter=delim))
            if not rows:
                return devices

            header_cells = [self._clean_cell_text(c) for c in rows[0]]
            col_map: Dict[int, str] = {}
            for idx, cell in enumerate(header_cells):
                field = self._map_header(cell)
                if field:
                    col_map[idx] = field

            if col_map and self._is_header_row(header_cells):
                start = 1
            elif col_map:
                start = 1
            else:
                start = 0
                positional = ['hostname', 'serial', 'model', 'ip', 'warranty_status', 'warranty_end']
                for idx, field in enumerate(positional):
                    col_map[idx] = field

            for row_num, row in enumerate(rows[start:], start=start + 1):
                mapped: Dict[str, str] = {}
                for idx, raw in enumerate(row):
                    field = col_map.get(idx)
                    if not field:
                        continue
                    val = (raw or '').strip()
                    if val and field not in mapped:
                        mapped[field] = val
                device = self._device_from_mapped(mapped, row_num)
                if device:
                    devices.append(device)
        except Exception:
            devices = self._parse_text_report(content)

        return devices

    def _parse_json_report(self, content: str) -> List[Dict[str, Any]]:
        devices: List[Dict[str, Any]] = []
        try:
            data = json.loads(content)
        except Exception:
            return devices

        items: List[Dict[str, Any]] = []
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    if 'assets' in entry and isinstance(entry['assets'], list):
                        items.extend(entry['assets'])
                    elif 'devices' in entry and isinstance(entry['devices'], list):
                        items.extend(entry['devices'])
                    elif 'data' in entry and isinstance(entry['data'], dict) and 'assets' in entry['data']:
                        items.extend(entry['data']['assets'])
                    else:
                        items.append(entry)
        elif isinstance(data, dict):
            if 'assets' in data and isinstance(data['assets'], list):
                items.extend(data['assets'])
            elif 'devices' in data and isinstance(data['devices'], list):
                items.extend(data['devices'])
            elif 'data' in data and isinstance(data['data'], dict) and 'assets' in data['data']:
                items.extend(data['data']['assets'])
            else:
                items.append(data)

        for row_num, item in enumerate(items, start=1):
            mapped: Dict[str, str] = {}
            for k, v in item.items():
                field = self._map_header(str(k))
                if field and v is not None:
                    mapped[field] = str(v).strip()
            # fallback field names if not caught by _map_header
            if 'ip' not in mapped and 'host' in item and item['host'] is not None:
                mapped['ip'] = str(item['host']).strip()
            if 'model' not in mapped and 'pid' in item and item['pid'] is not None:
                mapped['model'] = str(item['pid']).strip()
            if 'serial' not in mapped and 'serial_number' in item and item['serial_number'] is not None:
                mapped['serial'] = str(item['serial_number']).strip()
            device = self._device_from_mapped(mapped, row_num)
            if device:
                devices.append(device)
        return devices

    def _strip_non_inventory_html(self, content: str) -> str:
        cleaned = re.sub(r'<script\b[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
        cleaned = re.sub(r'<style\b[^>]*>.*?</style>', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
        cleaned = re.sub(
            r'<div[^>]*id=["\']nst-cisco-eol-modal["\'][^>]*>.*?</div>',
            '',
            cleaned,
            flags=re.IGNORECASE | re.DOTALL,
        )
        return cleaned

    def _extract_inventory_tables(self, content: str) -> List[str]:
        preferred = re.findall(
            r'<table[^>]*class=["\'][^"\']*nst-asset-table[^"\']*["\'][^>]*>(.*?)</table>',
            content,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if preferred:
            return preferred
        return re.findall(r'<table[^>]*>(.*?)</table>', content, flags=re.IGNORECASE | re.DOTALL)

    def _looks_like_serial(self, value: str) -> bool:
        v = (value or '').strip()
        return bool(re.match(r'^[A-Z0-9]{6,}$', v, re.IGNORECASE))

    def _looks_like_ip_or_host(self, value: str) -> bool:
        v = (value or '').strip()
        if re.match(r'^\d{1,3}(?:\.\d{1,3}){3}$', v):
            return True
        return bool(v) and not self._looks_like_serial(v)

    def _parse_html_report(self, content: str) -> List[Dict[str, Any]]:
        devices: List[Dict[str, Any]] = []
        content = self._strip_non_inventory_html(content)
        tables = self._extract_inventory_tables(content) or [content]

        for table_html in tables:
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.IGNORECASE | re.DOTALL)
            col_map: Dict[int, str] = {}
            header_seen = False

            for row_idx, row in enumerate(rows):
                cells_raw = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.IGNORECASE | re.DOTALL)
                cleaned_cells = [self._clean_cell_text(c) for c in cells_raw]
                if not any(cleaned_cells):
                    continue

                if not header_seen and self._is_header_row(cleaned_cells):
                    col_map = {}
                    for idx, cell in enumerate(cleaned_cells):
                        field = self._map_header(cell)
                        if field:
                            col_map[idx] = field
                    header_seen = True
                    continue

                mapped: Dict[str, str] = {}
                if col_map:
                    for idx, val in enumerate(cleaned_cells):
                        field = col_map.get(idx)
                        if field and val and field not in mapped:
                            mapped[field] = val
                else:
                    if (
                        len(cleaned_cells) >= 6
                        and self._looks_like_ip_or_host(cleaned_cells[0])
                        and not self._looks_like_serial(cleaned_cells[1])
                    ):
                        positional = [
                            'ip', 'hostname', 'model', 'serial',
                            'software_version', 'warranty_status', 'end_of_life', 'end_of_support',
                        ]
                    else:
                        positional = [
                            'hostname', 'serial', 'model', 'ip', 'warranty_status', 'warranty_end',
                        ]
                    for idx, field in enumerate(positional):
                        if idx < len(cleaned_cells) and cleaned_cells[idx]:
                            mapped[field] = cleaned_cells[idx]

                if len(cleaned_cells) >= 2 and not mapped.get('hostname') and not mapped.get('serial'):
                    mapped.setdefault('hostname', cleaned_cells[0])
                    mapped.setdefault('serial', cleaned_cells[1])

                device = self._device_from_mapped(mapped, row_idx + 1)
                if device:
                    devices.append(device)

        return devices

    def _parse_text_report(self, content: str) -> List[Dict[str, Any]]:
        devices = []
        lines = content.split('\n')
        current_device = None

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                if current_device and (current_device.get('hostname') or current_device.get('serial')):
                    devices.append(current_device)
                current_device = None
                continue

            hostname_match = re.match(r'^Hostname:\s*(.+)$', line, re.IGNORECASE)
            if hostname_match:
                if current_device and (current_device.get('hostname') or current_device.get('serial')):
                    devices.append(current_device)
                current_device = {
                    'hostname': hostname_match.group(1).strip(),
                    'serial': '',
                    'model': '',
                    'ip': '',
                    'warranty_status': 'unknown',
                    'warranty_end': '',
                    'end_of_life': '',
                    'end_of_support': '',
                    'end_of_service': '',
                    'line_number': i + 1,
                }
                continue

            if current_device is None:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 2 and not line.lower().startswith(('serial', 'model', 'ip', 'warranty')):
                    current_device = {
                        'hostname': parts[0],
                        'serial': parts[1] if len(parts) > 1 else '',
                        'model': parts[2] if len(parts) > 2 else '',
                        'ip': parts[3] if len(parts) > 3 else '',
                        'warranty_status': parts[4] if len(parts) > 4 else 'unknown',
                        'warranty_end': parts[5] if len(parts) > 5 else '',
                        'line_number': i + 1,
                    }
                    continue
                current_device = {
                    'hostname': '', 'serial': '', 'model': '', 'ip': '',
                    'warranty_status': 'unknown', 'warranty_end': '', 'line_number': i + 1,
                }

            serial_match = re.match(r'^Serial(?:\s+Number)?:\s*(.+)$', line, re.IGNORECASE)
            if serial_match:
                current_device['serial'] = serial_match.group(1).strip()
                continue

            model_match = re.match(r'^(?:Model|PID|Product ID):\s*(.+)$', line, re.IGNORECASE)
            if model_match:
                current_device['model'] = model_match.group(1).strip()
                continue

            ip_match = re.match(r'^(?:IP|Host):\s*(.+)$', line, re.IGNORECASE)
            if ip_match:
                current_device['ip'] = ip_match.group(1).strip()
                continue

            warranty_match = re.match(r'^Warranty(?:\s+Status)?:\s*(.+)$', line, re.IGNORECASE)
            if warranty_match:
                current_device['warranty_status'] = warranty_match.group(1).strip()
                continue

            eol_match = re.match(r'^(?:End of Life|EOL):\s*(.+)$', line, re.IGNORECASE)
            if eol_match:
                current_device['end_of_life'] = eol_match.group(1).strip()
                continue

            eos_match = re.match(r'^(?:End of Support|EOS):\s*(.+)$', line, re.IGNORECASE)
            if eos_match:
                current_device['end_of_support'] = eos_match.group(1).strip()
                continue

            eose_match = re.match(r'^(?:End of Service|EOSe):\s*(.+)$', line, re.IGNORECASE)
            if eose_match:
                current_device['end_of_service'] = eose_match.group(1).strip()
                continue

            end_match = re.match(r'^(?:Warranty End|End Date):\s*(.+)$', line, re.IGNORECASE)
            if end_match:
                current_device['warranty_end'] = end_match.group(1).strip()
                continue

        if current_device and (current_device.get('hostname') or current_device.get('serial')):
            devices.append(current_device)

        return devices

    def enrich_devices_from_eol_database(
        self,
        devices: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Re-enrich deduplicated devices from the local Cisco EOL/EOS SQLite catalog.

        Authoritative lifecycle dates (EOL/EOS/EOSe) come from the bundled DB when
        the Product ID is known. Contract warranty_end from source files is preserved.
        """
        from modules.cisco_eol_database import get_model_info, _calculate_warranty_status

        enriched = 0
        missing_pid = 0
        unknown_pid = 0

        for device in devices:
            pid = (device.get('model') or device.get('pid') or '').strip()
            if not pid:
                missing_pid += 1
                continue

            info = get_model_info(pid)
            if not info:
                unknown_pid += 1
                continue

            device['model'] = info.get('pid') or pid
            if info.get('model_name'):
                device['model_name'] = info['model_name']
            if info.get('end_of_life'):
                device['end_of_life'] = info['end_of_life']
            if info.get('end_of_support'):
                device['end_of_support'] = info['end_of_support']
            if info.get('end_of_service'):
                device['end_of_service'] = info['end_of_service']

            status_lower = (device.get('warranty_status') or '').lower()
            if 'not a cisco' not in status_lower:
                device['warranty_status'] = _calculate_warranty_status(
                    device.get('end_of_life', ''),
                    device.get('end_of_support', ''),
                    model_found=True,
                )
            device['eol_enrichment_source'] = 'cisco_eol_database'
            enriched += 1

        stats = {
            'eol_db_enriched': enriched,
            'eol_db_missing_pid': missing_pid,
            'eol_db_unknown_pid': unknown_pid,
            'eol_db_total': len(devices),
        }
        return devices, stats

    def deduplicate_devices_with_audit(
        self,
        devices: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Deduplicate devices using Hardware Serial Number as the immutable UUID.
        
        Performs intelligent attribute merging across duplicate occurrences
        and records an exhaustive audit log of all merged duplicates and conflicts.
        """
        groups: Dict[str, List[Dict[str, Any]]] = {}
        order: List[str] = []
        score_keys = (
            'hostname', 'serial', 'model', 'ip', 'software_version',
            'warranty_status', 'warranty_end', 'end_of_life',
            'end_of_support', 'end_of_service', 'model_name',
        )

        for d in devices:
            raw_serial = (d.get('serial') or '').strip().upper()
            is_placeholder = not raw_serial or raw_serial in (
                'UNKNOWN', 'N/A', 'NA', 'NONE', '-', '--', 'NULL', 'UNDEFINED', 'NOT APPLICABLE'
            )
            if not is_placeholder:
                key = f"SN:{raw_serial}"
            else:
                host_part = (d.get('hostname') or '').strip().lower()
                ip_part = (d.get('ip') or '').strip()
                if host_part or ip_part:
                    key = f"HOST_IP:{host_part}|{ip_part}"
                else:
                    key = f"ROW:{d.get('line_number', 0)}:{id(d)}"

            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(d)

        deduped_devices: List[Dict[str, Any]] = []
        duplicates_audit: List[Dict[str, Any]] = []
        raw_count = len(devices)

        for key in order:
            records = groups[key]
            if len(records) == 1:
                deduped_devices.append(records[0])
                continue

            # Sort records by richness (descending count of filled fields)
            records.sort(
                key=lambda r: sum(
                    1 for k in score_keys
                    if (r.get(k) or '').strip() and (r.get(k) or '').strip().lower() not in ('unknown', 'n/a', 'none', '-')
                ),
                reverse=True,
            )
            merged = dict(records[0])

            # Attribute merging & conflict detection
            conflicts: List[str] = []
            seen_hostnames = set()
            seen_ips = set()

            for r in records:
                h = (r.get('hostname') or '').strip()
                if h and h.lower() not in ('unknown', 'n/a', 'none', '-'):
                    seen_hostnames.add(h)
                ip_val = (r.get('ip') or '').strip()
                if ip_val and ip_val.lower() not in ('unknown', 'n/a', 'none', '-'):
                    seen_ips.add(ip_val)

                # Enrich missing or blank fields from duplicate occurrences
                for k in score_keys:
                    val = (r.get(k) or '').strip()
                    if val and val.lower() not in ('unknown', 'n/a', 'none', '-'):
                        curr_val = (merged.get(k) or '').strip()
                        if not curr_val or curr_val.lower() in ('unknown', 'n/a', 'none', '-'):
                            merged[k] = val

            if len(seen_hostnames) > 1:
                conflicts.append(f"Differing hostnames: {', '.join(sorted(seen_hostnames))}")
            if len(seen_ips) > 1:
                conflicts.append(f"Differing IPs: {', '.join(sorted(seen_ips))}")

            sources = sorted(list(set(r.get('source_file') for r in records if r.get('source_file'))))
            if not sources:
                sources = ['unknown']

            serial_val = (merged.get('serial') or '').strip().upper()
            duplicates_audit.append({
                'uuid': serial_val if serial_val and serial_val not in ('UNKNOWN', 'N/A') else key,
                'serial': serial_val,
                'occurrences': len(records),
                'source_files': sources,
                'sources_display': ', '.join(sources),
                'merged_hostname': merged.get('hostname', ''),
                'merged_ip': merged.get('ip', ''),
                'merged_model': merged.get('model', ''),
                'conflicts': conflicts,
                'conflicts_display': '; '.join(conflicts) if conflicts else 'None',
                'raw_variants': records,
            })

            deduped_devices.append(merged)

        duplicates_summary = {
            'raw_devices_count': raw_count,
            'unique_devices_count': len(deduped_devices),
            'duplicate_serials_count': len(duplicates_audit),
            'duplicate_occurrences_removed': raw_count - len(deduped_devices),
        }

        self.last_duplicates_audit = duplicates_audit
        self.last_duplicates_summary = duplicates_summary

        return deduped_devices, duplicates_audit, duplicates_summary

    def _dedupe_devices(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Backward-compatible wrapper returning deduped devices list."""
        deduped, _, _ = self.deduplicate_devices_with_audit(devices)
        return deduped

    def _generate_master_csv(self, all_devices: List[Dict[str, Any]]) -> str:
        fieldnames = [
            'Host', 'Hostname', 'Product ID (PID)', 'Serial Number',
            'Software Version', 'Warranty Status', 'End of Life', 'End of Support',
        ]
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for d in all_devices:
            writer.writerow({
                'Host': d.get('ip', ''),
                'Hostname': d.get('hostname', ''),
                'Product ID (PID)': d.get('model', ''),
                'Serial Number': d.get('serial', ''),
                'Software Version': d.get('software_version', ''),
                'Warranty Status': d.get('warranty_status', ''),
                'End of Life': d.get('end_of_life', '') or d.get('warranty_end', ''),
                'End of Support': d.get('end_of_support', ''),
            })
        return buf.getvalue()

    def _generate_master_json(
        self,
        all_devices: List[Dict[str, Any]],
        summary_info: Dict[str, Any],
        duplicates_audit: Optional[List[Dict[str, Any]]] = None,
        duplicates_summary: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate structured JSON master inventory export with Duplicates Audit."""
        export_payload = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'total_devices': len(all_devices),
            'duplicates_summary': duplicates_summary or {},
            'summary': summary_info,
            'devices': [
                {
                    'host': d.get('ip', ''),
                    'hostname': d.get('hostname', ''),
                    'product_id': d.get('model', ''),
                    'model_name': d.get('model_name', ''),
                    'serial_number': d.get('serial', ''),
                    'software_version': d.get('software_version', ''),
                    'warranty_status': d.get('warranty_status', ''),
                    'warranty_end': d.get('warranty_end', ''),
                    'end_of_life': d.get('end_of_life', '') or d.get('warranty_end', ''),
                    'end_of_support': d.get('end_of_support', ''),
                    'end_of_service': d.get('end_of_service', ''),
                    'eol_enrichment_source': d.get('eol_enrichment_source', ''),
                }
                for d in all_devices
            ],
            'duplicates_audit': duplicates_audit or [],
        }
        return json.dumps(export_payload, indent=2)

    def _generate_master_xlsx(
        self,
        all_devices: List[Dict[str, Any]],
        xlsx_path: Path,
        duplicates_audit: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """Generate styled Excel XLSX master inventory export with Duplicates Audit sheet using openpyxl."""
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Master Inventory"

            headers = [
                'Host', 'Hostname', 'Product ID (PID)', 'Serial Number',
                'Software Version', 'Warranty Status', 'End of Life', 'End of Support',
            ]
            ws.append(headers)

            header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
            header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
            thin_border = Border(
                left=Side(style='thin', color='CBD5E1'),
                right=Side(style='thin', color='CBD5E1'),
                top=Side(style='thin', color='CBD5E1'),
                bottom=Side(style='thin', color='CBD5E1')
            )

            for col_idx in range(1, len(headers) + 1):
                cell = ws.cell(row=1, column=col_idx)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = thin_border

            fill_active = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
            fill_expired = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
            fill_warning = PatternFill(start_color="FFEDD5", end_color="FFEDD5", fill_type="solid")

            for r_idx, d in enumerate(all_devices, start=2):
                status = str(d.get('warranty_status', '')).lower()
                row_vals = [
                    d.get('ip', ''),
                    d.get('hostname', ''),
                    d.get('model', ''),
                    d.get('serial', ''),
                    d.get('software_version', ''),
                    d.get('warranty_status', ''),
                    d.get('end_of_life', '') or d.get('warranty_end', ''),
                    d.get('end_of_support', ''),
                ]
                ws.append(row_vals)
                for col_idx in range(1, len(headers) + 1):
                    cell = ws.cell(row=r_idx, column=col_idx)
                    cell.border = thin_border
                    if col_idx == 6:
                        if 'active' in status or 'covered' in status:
                            cell.fill = fill_active
                        elif 'expired' in status:
                            cell.fill = fill_expired
                        elif 'non-cisco' in status or 'unknown' in status:
                            cell.fill = fill_warning

            for col in ws.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

            ws.freeze_panes = "A2"

            # -------------------------------------------------------------
            # Sheet 2: Duplicates Audit (Dedicated hardware UUID audit log)
            # -------------------------------------------------------------
            if duplicates_audit:
                ws_audit = wb.create_sheet(title="Duplicates Audit")
                audit_headers = [
                    'Hardware UUID (Serial)', 'Occurrences', 'Source Files',
                    'Resolved Hostname', 'Resolved IP', 'Resolved Model (PID)', 'Discrepancies / Conflicts',
                ]
                ws_audit.append(audit_headers)
                audit_header_fill = PatternFill(start_color="B45309", end_color="B45309", fill_type="solid")
                for col_idx in range(1, len(audit_headers) + 1):
                    cell = ws_audit.cell(row=1, column=col_idx)
                    cell.fill = audit_header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                    cell.border = thin_border

                for r_idx, dup in enumerate(duplicates_audit, start=2):
                    row_vals = [
                        dup.get('serial') or dup.get('uuid') or '',
                        dup.get('occurrences', 1),
                        dup.get('sources_display', ''),
                        dup.get('merged_hostname', ''),
                        dup.get('merged_ip', ''),
                        dup.get('merged_model', ''),
                        dup.get('conflicts_display', 'None'),
                    ]
                    ws_audit.append(row_vals)
                    for col_idx in range(1, len(audit_headers) + 1):
                        cell = ws_audit.cell(row=r_idx, column=col_idx)
                        cell.border = thin_border
                        if col_idx == 2:
                            cell.fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
                            cell.alignment = Alignment(horizontal="center")

                for col in ws_audit.columns:
                    max_len = max(len(str(cell.value or '')) for cell in col)
                    col_letter = get_column_letter(col[0].column)
                    ws_audit.column_dimensions[col_letter].width = max(max_len + 4, 14)

                ws_audit.freeze_panes = "A2"

            wb.save(str(xlsx_path))
            return True
        except Exception as err:
            sys.stderr.write(f"[CONSOLIDATOR] Notice: XLSX export skipped or error: {err}\n")
            return False

    def consolidate_reports(
        self,
        report_name: Optional[str] = None,
        file_paths: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if file_paths:
            input_files = [{'name': Path(p).name, 'path': str(p)} for p in file_paths]
        else:
            input_files = self.get_input_files()

        if not input_files:
            return {
                'success': False,
                'error': 'No Asset Warranty report files found in input directory',
                'input_dir': str(self.input_dir)
            }

        parsed_reports = []
        for file_info in input_files:
            parsed_reports.append(self.parse_asset_warranty_report(file_info['path']))

        successful_reports = 0
        failed_reports = []
        all_devices: List[Dict[str, Any]] = []
        per_file_counts: List[Dict[str, Any]] = []

        for report in parsed_reports:
            if report['success']:
                successful_reports += 1
                for d in report['devices']:
                    if not d.get('source_file'):
                        d['source_file'] = report['file_name']
                    all_devices.append(d)
                per_file_counts.append({
                    'file_name': report['file_name'],
                    'format': report['format'],
                    'device_count': report['device_count'],
                })
            else:
                failed_reports.append({
                    'file_name': report['file_name'],
                    'error': report['error']
                })

        raw_devices_count = len(all_devices)
        all_devices, duplicates_audit, duplicates_summary = self.deduplicate_devices_with_audit(all_devices)
        all_devices, eol_enrichment_stats = self.enrich_devices_from_eol_database(all_devices)
        total_devices = len(all_devices)

        # Compute model_counts and warranty_status_counts ON THE CLEAN DEDUPLICATED DEVICES
        model_counts: Dict[str, int] = {}
        warranty_status_counts: Dict[str, int] = {}
        for device in all_devices:
            model = device.get('model', 'unknown') or 'unknown'
            model_counts[model] = model_counts.get(model, 0) + 1
            status = (device.get('warranty_status') or 'unknown').lower()
            if 'not a cisco' in status:
                warranty_status_counts['not_a_cisco_device'] = warranty_status_counts.get('not_a_cisco_device', 0) + 1
            elif 'expired' in status:
                warranty_status_counts['expired'] = warranty_status_counts.get('expired', 0) + 1
            elif 'warning' in status:
                warranty_status_counts['warning'] = warranty_status_counts.get('warning', 0) + 1
            elif 'active' in status or 'covered' in status:
                warranty_status_counts['covered'] = warranty_status_counts.get('covered', 0) + 1
            else:
                warranty_status_counts['unknown'] = warranty_status_counts.get('unknown', 0) + 1

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = report_name.strip() if report_name else 'asset_warranty_consolidated'
        base_name = re.sub(r'[^\w\-]+', '_', base_name).strip('_') or 'asset_warranty_consolidated'
        output_filename = f"{base_name}_{timestamp}.html"
        csv_filename = f"{base_name}_{timestamp}.csv"
        json_filename = f"{base_name}_{timestamp}.json"
        xlsx_filename = f"{base_name}_{timestamp}.xlsx"

        output_path = self.output_dir / output_filename
        csv_path = self.output_dir / csv_filename
        json_path = self.output_dir / json_filename
        xlsx_path = self.output_dir / xlsx_filename

        summary_meta = {
            'total_files': len(input_files),
            'successful_reports': successful_reports,
            'failed_reports': len(failed_reports),
            'raw_devices_count': raw_devices_count,
            'total_devices': total_devices,
            'unique_devices': total_devices,
            'duplicate_serials_count': duplicates_summary['duplicate_serials_count'],
            'duplicate_occurrences_removed': duplicates_summary['duplicate_occurrences_removed'],
            'duplicates_summary': duplicates_summary,
            'model_counts': model_counts,
            'warranty_status_counts': warranty_status_counts,
            'eol_enrichment': eol_enrichment_stats,
            'per_file_counts': per_file_counts,
            'timestamp': timestamp,
        }

        html_content = self._generate_master_html(
            parsed_reports,
            all_devices,
            total_devices,
            model_counts,
            warranty_status_counts,
            successful_reports,
            failed_reports,
            timestamp,
            csv_filename=csv_filename,
            json_filename=json_filename,
            xlsx_filename=xlsx_filename,
            duplicates_audit=duplicates_audit,
            duplicates_summary=duplicates_summary,
            raw_devices_count=raw_devices_count,
        )

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                f.write(self._generate_master_csv(all_devices))
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write(self._generate_master_json(
                    all_devices,
                    summary_meta,
                    duplicates_audit=duplicates_audit,
                    duplicates_summary=duplicates_summary,
                ))
            self._generate_master_xlsx(all_devices, xlsx_path, duplicates_audit=duplicates_audit)
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to write output file: {str(e)}'
            }

        warning = None
        if total_devices == 0:
            warning = (
                'Parsed 0 devices from input files. '
                'Verify files are NST Asset Warranty HTML/CSV exports.'
            )

        return {
            'success': True,
            'output_file': output_filename,
            'output_path': str(output_path),
            'master_file': str(output_path),
            'output_html': output_filename,
            'output_html_path': str(output_path),
            'output_csv': csv_filename,
            'output_csv_path': str(csv_path),
            'csv_file': str(csv_path),
            'output_json': json_filename,
            'output_json_path': str(json_path),
            'json_file': str(json_path),
            'output_xlsx': xlsx_filename,
            'output_xlsx_path': str(xlsx_path),
            'xlsx_file': str(xlsx_path),
            'total_devices': total_devices,
            'raw_devices_count': raw_devices_count,
            'duplicate_serials_count': duplicates_summary['duplicate_serials_count'],
            'duplicate_occurrences_removed': duplicates_summary['duplicate_occurrences_removed'],
            'duplicates_audit': duplicates_audit,
            'duplicates_summary': duplicates_summary,
            'total_reports': len(parsed_reports),
            'warning': warning,
            'summary': summary_meta,
            'failed_reports': failed_reports
        }


    def _generate_master_html(
        self,
        parsed_reports: List[Dict[str, Any]],
        all_devices: List[Dict[str, Any]],
        total_devices: int,
        model_counts: Dict[str, int],
        warranty_status_counts: Dict[str, int],
        successful_reports: int,
        failed_reports: List[Dict[str, Any]],
        timestamp: str,
        csv_filename: Optional[str] = None,
        json_filename: Optional[str] = None,
        xlsx_filename: Optional[str] = None,
        duplicates_audit: Optional[List[Dict[str, Any]]] = None,
        duplicates_summary: Optional[Dict[str, Any]] = None,
        raw_devices_count: int = 0,
    ) -> str:
        """Generate the master HTML report with Duplicates Audit section."""

        # Build Master Consolidated Devices HTML table
        master_rows_html = ''
        for d in all_devices:
            status = (d.get('warranty_status') or 'unknown').strip()
            status_lower = status.lower()
            if 'not a cisco' in status_lower:
                badge_style = 'background-color:#fef3c7; color:#92400e; padding:3px 8px; border-radius:12px; font-weight:600; font-size:11px;'
            elif 'expired' in status_lower:
                badge_style = 'background-color:#fee2e2; color:#b91c1c; padding:3px 8px; border-radius:12px; font-weight:600; font-size:11px;'
            elif 'active' in status_lower or 'covered' in status_lower:
                badge_style = 'background-color:#dcfce7; color:#15803d; padding:3px 8px; border-radius:12px; font-weight:600; font-size:11px;'
            else:
                badge_style = 'background-color:#f1f5f9; color:#475569; padding:3px 8px; border-radius:12px; font-weight:600; font-size:11px;'

            pid = d.get('model', '') or '-'
            serial = d.get('serial', '') or '-'
            hostname = d.get('hostname', '') or '-'
            ip = d.get('ip', '') or '-'
            ver = d.get('software_version', '') or '-'
            eol = d.get('end_of_life', '') or d.get('warranty_end', '') or '-'
            eos = d.get('end_of_support', '') or '-'

            master_rows_html += f'''
            <tr>
                <td>{escape(ip)}</td>
                <td><strong>{escape(hostname)}</strong></td>
                <td>{escape(pid)}</td>
                <td><code>{escape(serial)}</code></td>
                <td>{escape(ver)}</td>
                <td><span style="{badge_style}">{escape(status)}</span></td>
                <td>{escape(eol)}</td>
                <td>{escape(eos)}</td>
            </tr>'''

        download_links = []
        if csv_filename:
            download_links.append(f'<a href="{escape(csv_filename)}" download style="display:inline-block; background-color:#2563eb; color:white; padding:6px 12px; border-radius:6px; text-decoration:none; font-weight:600; font-size:12px;">📊 Download Master CSV</a>')
        if json_filename:
            download_links.append(f'<a href="{escape(json_filename)}" download style="display:inline-block; background-color:#7c3aed; color:white; padding:6px 12px; border-radius:6px; text-decoration:none; font-weight:600; font-size:12px;">📦 Download Master JSON</a>')
        if xlsx_filename:
            download_links.append(f'<a href="{escape(xlsx_filename)}" download style="display:inline-block; background-color:#16a34a; color:white; padding:6px 12px; border-radius:6px; text-decoration:none; font-weight:600; font-size:12px;">📑 Download Master XLSX</a>')
        download_btn = f'<div style="display:flex; gap:6px; flex-wrap:wrap; margin-left:auto;">{"".join(download_links)}</div>'

        master_table_html = f'''
        <div class="report-section" style="border: 2px solid #3b82f6; background-color:#ffffff; margin-top:25px;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:15px; border-bottom:1px solid #e2e8f0; padding-bottom:10px;">
                <div>
                    <h2 style="margin:0; color:#1e3a8a; font-size:18px;">Master Consolidated Inventory ({total_devices} Unique Devices)</h2>
                    <p style="margin:4px 0 0 0; color:#64748b; font-size:12px;">Unified view deduplicated across all ingested files</p>
                </div>
                {download_btn}
            </div>
            <div class="device-table">
                <table>
                    <thead>
                        <tr>
                            <th>Host (IP)</th>
                            <th>Hostname</th>
                            <th>Product ID (PID)</th>
                            <th>Serial Number</th>
                            <th>Software Version</th>
                            <th>Warranty Status</th>
                            <th>End of Life</th>
                            <th>End of Support</th>
                        </tr>
                    </thead>
                    <tbody>
                        {master_rows_html if master_rows_html else '<tr><td colspan="8" style="text-align:center; padding:20px; color:#94a3b8;">No devices found</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
        '''

        # Build Duplicates Audit HTML table if any duplicates were detected
        duplicates_audit_html = ''
        dup_count = len(duplicates_audit) if duplicates_audit else 0
        if duplicates_audit:
            dup_rows = ''
            for dup in duplicates_audit:
                conflicts = dup.get('conflicts', [])
                conflict_badge = '<span style="color:#b91c1c; font-weight:600;">' + escape('; '.join(conflicts)) + '</span>' if conflicts else '<span style="color:#16a34a;">None</span>'
                sources = dup.get('sources_display', '')
                dup_rows += f'''
                <tr>
                    <td><code>{escape(dup.get('serial') or dup.get('uuid') or '-')}</code></td>
                    <td style="text-align:center;"><span style="background-color:#fef3c7; color:#92400e; padding:3px 8px; border-radius:12px; font-weight:700;">{dup.get('occurrences', 1)}x</span></td>
                    <td>{escape(sources)}</td>
                    <td><strong>{escape(dup.get('merged_hostname') or '-')}</strong> ({escape(dup.get('merged_ip') or '-')})</td>
                    <td>{escape(dup.get('merged_model') or '-')}</td>
                    <td>{conflict_badge}</td>
                </tr>'''
            duplicates_audit_html = f'''
            <div class="report-section" style="border: 2px solid #f59e0b; background-color:#fffbeb; margin-top:25px;">
                <div style="margin-bottom:15px; border-bottom:1px solid #fcd34d; padding-bottom:10px;">
                    <h2 style="margin:0; color:#92400e; font-size:18px;">⚠️ Duplicate Hardware Audit ({dup_count} Devices with Multi-File Occurrences)</h2>
                    <p style="margin:4px 0 0 0; color:#78350f; font-size:12px;">Identified by physical Serial Number UUID. Attributes intelligently merged across reports with conflicts logged below.</p>
                </div>
                <div class="device-table">
                    <table>
                        <thead>
                            <tr style="background-color:#b45309;">
                                <th>Hardware UUID (Serial)</th>
                                <th style="text-align:center;">Occurrences</th>
                                <th>Ingested Files</th>
                                <th>Merged Host / IP</th>
                                <th>Merged Model</th>
                                <th>Discrepancy / Conflicts</th>
                            </tr>
                        </thead>
                        <tbody>
                            {dup_rows}
                        </tbody>
                    </table>
                </div>
            </div>'''
        
        # Build model summary HTML
        model_html = '<ul>'
        for model, count in sorted(model_counts.items(), key=lambda x: x[1], reverse=True):
            model_html += f'<li>{model}: {count} devices</li>'
        model_html += '</ul>'
        
        # Build warranty status summary HTML
        warranty_html = '<ul>'
        for status, count in warranty_status_counts.items():
            color = 'green' if status == 'covered' else 'red' if status == 'expired' else 'gray'
            warranty_html += f'<li style="color: {color}">{status.capitalize()}: {count} devices</li>'
        warranty_html += '</ul>'
        
        # Build individual reports HTML
        reports_html = ''
        for report in parsed_reports:
            if report['success']:
                reports_html += f'''
                <div class="report-section">
                    <h3>Report: {report['file_name']}</h3>
                    <p><strong>Format:</strong> {report['format']}</p>
                    <p><strong>Devices:</strong> {report['device_count']}</p>
                    <div class="device-table">
                        <table>
                            <thead>
                                <tr>
                                    <th>Hostname</th>
                                    <th>Serial</th>
                                    <th>Model</th>
                                    <th>IP</th>
                                    <th>Warranty Status</th>
                                    <th>Warranty End</th>
                                </tr>
                            </thead>
                            <tbody>
                '''
                for device in report['devices']:
                    warranty_color = 'green' if 'covered' in device.get('warranty_status', '').lower() else 'red' if 'expired' in device.get('warranty_status', '').lower() else 'gray'
                    reports_html += f'''
                                <tr>
                                    <td>{device.get('hostname', '')}</td>
                                    <td>{device.get('serial', '')}</td>
                                    <td>{device.get('model', '')}</td>
                                    <td>{device.get('ip', '')}</td>
                                    <td style="color: {warranty_color}">{device.get('warranty_status', '')}</td>
                                    <td>{device.get('warranty_end', '')}</td>
                                </tr>
                    '''
                reports_html += '''
                            </tbody>
                        </table>
                    </div>
                </div>
                '''
            else:
                reports_html += f'''
                <div class="report-section error">
                    <h3>Report: {report['file_name']} (FAILED)</h3>
                    <p><strong>Error:</strong> {report['error']}</p>
                </div>
                '''
        
        # Build failed reports HTML
        failed_html = ''
        if failed_reports:
            failed_html = '<div class="error-section"><h3>Failed Reports</h3><ul>'
            for failed in failed_reports:
                failed_html += f'<li><strong>{failed['file_name']}</strong>: {failed['error']}</li>'
            failed_html += '</ul></div>'
        
        dups_removed = duplicates_summary.get('duplicate_occurrences_removed', 0) if duplicates_summary else max(0, raw_devices_count - total_devices)

        # Complete HTML template
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cisco Asset Warranty - Consolidated Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1e3a8a;
            border-bottom: 2px solid #1e3a8a;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #374151;
            margin-top: 30px;
        }}
        .summary {{
            background-color: #f0f9ff;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .summary-item {{
            background-color: white;
            padding: 10px;
            border-radius: 4px;
            border-left: 4px solid #3b82f6;
        }}
        .summary-item h3 {{
            margin: 0 0 5px 0;
            font-size: 14px;
            color: #64748b;
        }}
        .summary-item p {{
            margin: 0;
            font-size: 18px;
            font-weight: bold;
            color: #1e293b;
        }}
        .report-section {{
            margin: 30px 0;
            padding: 20px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
        }}
        .report-section.error {{
            background-color: #fef2f2;
            border-color: #ef4444;
        }}
        .device-table {{
            overflow-x: auto;
            margin-top: 15px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }}
        th {{
            background-color: #1e3a8a;
            color: white;
            padding: 10px;
            text-align: left;
        }}
        td {{
            padding: 8px;
            border-bottom: 1px solid #e5e7eb;
        }}
        tr:hover {{
            background-color: #f9fafb;
        }}
        .error-section {{
            background-color: #fef2f2;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border: 1px solid #ef4444;
        }}
        .timestamp {{
            color: #64748b;
            font-size: 12px;
            margin-top: 30px;
            text-align: right;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Cisco Asset Warranty - Consolidated Report</h1>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <h3>Source Files</h3>
                    <p>{len(parsed_reports)}</p>
                </div>
                <div class="summary-item">
                    <h3>Raw Rows</h3>
                    <p>{raw_devices_count}</p>
                </div>
                <div class="summary-item" style="border-left-color: #f59e0b;">
                    <h3>Duplicates Merged</h3>
                    <p style="color:#d97706;">{dups_removed}</p>
                </div>
                <div class="summary-item" style="border-left-color: #10b981;">
                    <h3>Unique Devices</h3>
                    <p style="color:#059669;">{total_devices}</p>
                </div>
            </div>
        </div>
        
        <div class="summary">
            <h2>Device Models</h2>
            {model_html}
        </div>
        
        <div class="summary">
            <h2>Warranty Status</h2>
            {warranty_html}
        </div>
        
        {failed_html}
        
        {master_table_html}

        {duplicates_audit_html}

        <h2>Individual Reports</h2>
        {reports_html}
        
        <div class="timestamp">
            Generated: {timestamp}
        </div>
    </div>
</body>
</html>'''
        
        return html


def consolidate_reports(
    file_paths: Optional[List[str]] = None,
    output_dir: Optional[str] = None,
    base_dir: Optional[str] = None,
    report_name: Optional[str] = None,
    input_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Top-level convenience function to run consolidation on files and output to directory."""
    consolidator = AssetWarrantyConsolidator(base_dir=base_dir, input_dir=input_dir, output_dir=output_dir)
    return consolidator.consolidate_reports(report_name=report_name, file_paths=file_paths)
