"""Parse Cisco IOS/NX-OS CLI for asset identity (UDI / inventory)."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def _first_match(patterns: List[str], text: str, flags: int = 0) -> Optional[str]:
    for pat in patterns:
        m = re.search(pat, text, flags)
        if m:
            val = (m.group(1) or '').strip()
            if val and val.lower() not in ('none', 'n/a', 'unknown'):
                return val
    return None


def parse_ios_nxos_version(version_output: str) -> Dict[str, str]:
    text = version_output or ''
    hostname = _first_match([
        r'^([A-Za-z0-9_.-]+)\s+uptime\s+is',
        r'Device name:\s*(\S+)',
    ], text, re.MULTILINE) or ''
    software = _first_match([
        r'Version\s+([^,\r\n]+)',
        r'NXOS:\s*version\s+(\S+)',
        r'IOS.*?(\d+\.\S+)',
    ], text, re.IGNORECASE) or ''
    serial = _first_match([
        r'System Serial Number\s*:?\s*(\S+)',
        r'Processor board ID\s+(\S+)',
        r'Chassis Serial Number\s*:?\s*(\S+)',
    ], text) or ''
    pid = _first_match([
        r'Model Number\s*:?\s*(\S+)',
        r'cisco\s+(Nexus\S+|C\d+\S+|ISR\d+\S+)',
    ], text, re.IGNORECASE) or ''
    vid = _first_match([r'VID:\s*(\S+)'], text) or ''
    return {
        'hostname': hostname,
        'software_version': software,
        'serial_number': serial,
        'pid': pid,
        'vid': vid,
    }


def parse_inventory_blocks(inventory_output: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    if not inventory_output:
        return rows
    block_re = re.compile(
        r'NAME:\s*"([^"]+)"\s*,\s*DESCR:\s*"([^"]*)"\s*'
        r'(?:\r?\n|\s)*PID:\s*([^,\s]+)\s*,\s*VID:\s*([^,\s]+)\s*,\s*SN:\s*(\S+)',
        re.IGNORECASE,
    )
    for m in block_re.finditer(inventory_output):
        rows.append({
            'name': m.group(1).strip(),
            'descr': m.group(2).strip(),
            'pid': m.group(3).strip(),
            'vid': m.group(4).strip(),
            'serial_number': m.group(5).strip(),
        })
    return rows


def pick_chassis_row(rows: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    for row in rows:
        name = (row.get('name') or '').lower()
        if 'chassis' in name:
            return row
    return rows[0] if rows else None


def merge_asset_identity(
    version_fields: Dict[str, str],
    inventory_rows: List[Dict[str, str]],
    include_modules: bool = False,
) -> Dict[str, Any]:
    chassis = pick_chassis_row(inventory_rows)
    out: Dict[str, Any] = {
        'hostname': version_fields.get('hostname') or '',
        'software_version': version_fields.get('software_version') or '',
        'pid': (chassis or {}).get('pid') or version_fields.get('pid') or '',
        'vid': (chassis or {}).get('vid') or version_fields.get('vid') or '',
        'serial_number': version_fields.get('serial_number') or (chassis or {}).get('serial_number', ''),
    }
    if include_modules and inventory_rows:
        modules = [r for r in inventory_rows if 'chassis' not in (r.get('name') or '').lower()]
        out['modules'] = modules
        out['module_count'] = len(modules)
    return out
