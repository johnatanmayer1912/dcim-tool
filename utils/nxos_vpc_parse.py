"""
Shared NX-OS vPC / port-channel parsing for topology_mapper, vpc_domain_plugin, adapters.

Handles multi-line table headers (Nexus 9.x), Identifier column rows, dual show vpc + brief merge,
and peer-status text variants ('peer adjacency formed ok').
"""
from __future__ import annotations

import re

_VALID_STATUS = frozenset({'up', 'down', 'suspended', 'active', 'inactive'})
_VALID_CONSISTENCY = frozenset({
    'success', 'failed', 'not-checked', 'consistent', 'inconsistent', 'unknown',
})


def norm_po(name: str) -> str:
    n = (name or '').strip()
    n = re.sub(r'(?i)port-channel', 'Po', n)
    m = re.match(r'(?i)^(po)(\d+.*)$', n)
    if m:
        return 'Po' + m.group(2)
    return n


def normalize_vpc_peer_status(status_raw: str) -> str:
    low = (status_raw or '').lower()
    if any(x in low for x in (
        'up', 'alive', 'ok', 'formed', 'adjacency', 'operational', 'peer is up',
    )):
        return 'up'
    if any(x in low for x in ('down', 'not ok', 'failed', 'not established', 'not alive')):
        return 'down'
    return status_raw or 'unknown'


def normalize_vpc_keepalive_status(status_raw: str) -> str:
    low = (status_raw or '').lower()
    if any(x in low for x in ('alive', 'connected', 'peer is alive', 'operational')):
        return 'up'
    if 'up' in low and 'not' not in low:
        return 'up'
    if any(x in low for x in (
        'suspended', 'not reachable', 'failed', 'down', 'not alive',
        'not established', 'connection failed',
    )):
        return 'down'
    return status_raw or 'unknown'


def extract_vpc_domain_id(text: str) -> str:
    if not text:
        return ''
    for pat in (
        r'vPC\s+domain\s+id\s*[:=]\s*(\d+)',
        r'vpc\s+domain\s+id\s*[:=]?\s*(\d+)',
        r'Domain\s+ID\s*[:]\s*(\d+)',
    ):
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return ''


def extract_nxos_version(version_out: str) -> str:
    """Extract NX-OS version string from show version (5.x–10.x patterns)."""
    if not version_out:
        return ''
    for pat in (
        r'system:\s*version\s+([\d\.()\w]+)',
        r'NXOS:\s*version\s+([\d\.()\w]+)',
        r'kickstart:\s*version\s+([\d\.()\w]+)',
        r'(?:NX-OS|Cisco Nexus Operating System).*?version\s+([\d\.()\w]+)',
        r'Version\s+([\d\.()A-Za-z]+)',
    ):
        m = re.search(pat, version_out, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ''


def nxos_major_version(version_str: str) -> int | None:
    m = re.match(r'(\d+)', version_str or '')
    return int(m.group(1)) if m else None


def parse_vpc_table_row_classic(parts: list[str]) -> dict | None:
    """Classic NX-OS 7.x table: id  Port  Status  Consistency  ... (no Identifier column)."""
    if len(parts) < 4 or not parts[0].isdigit():
        return None
    po_raw = parts[1]
    if not re.match(r'^(Po\d+|Port-channel\d+)', po_raw, re.IGNORECASE):
        return None
    status = parts[2].lower()
    if status not in _VALID_STATUS:
        return None
    consistency = parts[3].lower() if len(parts) > 3 else 'unknown'
    if consistency not in _VALID_CONSISTENCY:
        consistency = 'unknown'
    active_vlans = parts[4] if len(parts) > 4 else '-'
    return {
        'vpc_id': parts[0],
        'po': norm_po(po_raw),
        'status': status,
        'consistency': consistency,
        'active_vlans': active_vlans,
    }


def parse_vpc_table_row(parts: list[str]) -> dict | None:
    """Parse one whitespace-split vPC table row (classic or Identifier-column NX-OS 9.x)."""
    if len(parts) < 3 or not parts[0].isdigit():
        return None
    po_raw = parts[1]
    if not re.match(r'^(Po\d+|Port-channel\d+)', po_raw, re.IGNORECASE):
        return None

    # Classic 7.x: third token is status (not numeric Identifier)
    if len(parts) >= 4 and parts[2].lower() in _VALID_STATUS:
        return parse_vpc_table_row_classic(parts)

    status_idx = 2
    if len(parts) > 3 and parts[2].isdigit():
        status_idx = 3

    status = parts[status_idx].lower() if len(parts) > status_idx else ''
    if status not in _VALID_STATUS:
        for i in range(2, len(parts)):
            if parts[i].lower() in _VALID_STATUS:
                status_idx = i
                status = parts[i].lower()
                break
        else:
            classic = parse_vpc_table_row_classic(parts)
            if classic:
                return classic
            return None

    consistency = 'unknown'
    if len(parts) > status_idx + 1:
        cand = parts[status_idx + 1].lower()
        if cand in _VALID_CONSISTENCY:
            consistency = cand

    active_vlans = '-'
    tail = parts[status_idx + 2:]
    if tail:
        active_vlans = ' '.join(tail)

    return {
        'vpc_id': parts[0],
        'po': norm_po(po_raw),
        'status': status,
        'consistency': consistency,
        'active_vlans': active_vlans,
    }


def _is_vpc_table_header(line: str) -> bool:
    low = line.lower()
    if 'legend' in low:
        return False
    if re.search(r'vpc\s+(id|pc)\b', low) and any(x in low for x in ('port', 'name', 'identifier', 'status')):
        return True
    if re.search(r'^\s*id\s+', low) and ('port' in low or 'name' in low):
        return True
    if 'id' in low and 'port' in low and 'status' in low:
        return True
    return False


def parse_vpc_table_from_cli(vpc_out: str, brief_out: str = '') -> list[dict]:
    """Extract vPC member rows from show vpc and/or show vpc brief."""
    table: list[dict] = []
    seen: set[tuple] = set()

    def _add_rows(text: str):
        if not text:
            return
        lines = text.splitlines()
        in_section = False
        past_header = False
        for line in lines:
            stripped = line.strip()
            low = stripped.lower()
            if not stripped:
                continue
            if 'legend' in low:
                continue
            if re.search(r'vPC\s+status', stripped, re.I) or _is_vpc_table_header(stripped):
                in_section = True
                past_header = False
                continue
            if in_section and re.match(r'^[-\s]+$', stripped) and '-' in stripped:
                past_header = True
                continue
            if in_section and _is_vpc_table_header(stripped):
                past_header = False
                continue
            if not in_section and _is_vpc_table_header(stripped):
                in_section = True
                past_header = True
                continue
            if in_section and (past_header or not _is_vpc_table_header(stripped)):
                if _is_vpc_table_header(stripped):
                    past_header = True
                    continue
                row = parse_vpc_table_row(stripped.split())
                if row:
                    key = (row['vpc_id'], row['po'])
                    if key not in seen:
                        seen.add(key)
                        table.append(row)

    _add_rows(vpc_out)
    if not table:
        _add_rows(brief_out)
    elif brief_out:
        _add_rows(brief_out)

    return table


def parse_vpc_full(vpc_out: str, brief_out: str = '', peer_link_out: str = '', nxos_version: str = '') -> dict:
    """Structured vPC domain state from NX-OS show commands."""
    result = {
        'domain_id': '',
        'role': 'unknown',
        'peer_status': 'unknown',
        'keepalive_status': 'unknown',
        'peer_link_po': '',
        'vpc_table': [],
        'nxos_version': nxos_version or '',
    }
    combined = (vpc_out or '') + '\n' + (brief_out or '')
    result['domain_id'] = extract_vpc_domain_id(combined)

    for line in (vpc_out or '').splitlines():
        low = line.lower()
        if 'vpc role' in low or (low.strip().startswith('role') and 'primary' in low):
            m = re.search(r'(primary|secondary)', line, re.I)
            if m:
                result['role'] = m.group(1).lower()
        if re.search(r'peer\s+status\s*:', line, re.I):
            m = re.search(r'peer\s+status\s*:\s*(.+)', line, re.I)
            if m:
                result['peer_status'] = normalize_vpc_peer_status(m.group(1).strip())
        if re.search(r'vPC\s+keep-?alive\s+status\s*:', line, re.I):
            m = re.search(r'vPC\s+keep-?alive\s+status\s*:\s*(.+)', line, re.I)
            if m:
                result['keepalive_status'] = normalize_vpc_keepalive_status(m.group(1).strip())

    for line in (peer_link_out or '').splitlines():
        m = re.search(r'(Port-channel\d+|Po\d+)', line, re.I)
        if m:
            result['peer_link_po'] = norm_po(m.group(1))
            break

    result['vpc_table'] = parse_vpc_table_from_cli(vpc_out, brief_out)

    if not result['peer_link_po'] and result['vpc_table']:
        for line in (vpc_out or '').splitlines():
            if re.search(r'peer-?link', line, re.I):
                m = re.search(r'(Po\d+|Port-channel\d+)', line, re.I)
                if m:
                    result['peer_link_po'] = norm_po(m.group(1))
                    break

    return result


def merge_vpc_structured(primary: dict, secondary: dict) -> dict:
    """Merge two vpc_structured dicts (dual collection / resync)."""
    out = dict(primary or {})
    sec = secondary or {}
    for key in ('domain_id', 'role', 'peer_status', 'keepalive_status', 'peer_link_po'):
        if not out.get(key) and sec.get(key):
            out[key] = sec[key]
    seen = {(r.get('vpc_id'), r.get('po')) for r in out.get('vpc_table', [])}
    for row in sec.get('vpc_table', []):
        k = (row.get('vpc_id'), row.get('po'))
        if k not in seen:
            out.setdefault('vpc_table', []).append(row)
            seen.add(k)
    return out


def vpc_details_from_structured(vpc_structured: dict, peer_link_out: str = '') -> tuple[list, dict]:
    """Build vpcs list and vpc_details dict from structured parse."""
    vpc_ids = []
    vpc_details = {}
    vs = vpc_structured or {}
    pl_status = 'up' if vs.get('peer_status') == 'up' else 'down'
    ka_status = 'up' if vs.get('keepalive_status') == 'up' else 'down'

    for row in vs.get('vpc_table', []):
        po_name = row['po']
        vpc_ids.append(po_name)
        vpc_details[po_name] = {
            'vpc_id': row['vpc_id'],
            'status': row['status'],
            'consistency': row.get('consistency', 'unknown'),
            'active_vlans': row.get('active_vlans', '-'),
            'type': 'vpc',
        }

    peer_link_po = vs.get('peer_link_po', '')
    if peer_link_po:
        vpc_details[peer_link_po] = {
            'type': 'peer-link',
            'status': pl_status,
            'keepalive': ka_status,
        }
    elif peer_link_out:
        for line in peer_link_out.splitlines():
            pl_match = re.search(r'(Port-channel\d+|Po\d+)', line, re.I)
            if pl_match:
                peer_link_int = norm_po(pl_match.group(1))
                vpc_details[peer_link_int] = {
                    'type': 'peer-link',
                    'status': pl_status,
                    'keepalive': ka_status,
                }
                break
    return vpc_ids, vpc_details
