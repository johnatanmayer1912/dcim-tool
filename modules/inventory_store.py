"""
modules/inventory_store.py
--------------------------
Preview, commit, and bak-restore for inventory.txt v1.

Canonical line: IP,device_type[,group] or IP,device_type,port,group
Comments (#) and [Group] headers are preserved on write when they still
apply to accepted rows. filter_inventory() remains the execute-time parser;
this module is stricter (unknown types and duplicates are not silent).

AI_CONTEXT: Phase 0 identity — committed file is the durable device list.
AI_FLOW: preview(text) → commit replace|merge → bak N=10 → restore
AI_IMPACTS: /api/inventory/preview|commit|restore; sidebar Import still GET /api/inventory
AI_OFFLINE_NOTE: Local file only. NST_INVENTORY_PATH overrides path.
AI_SECURITY_NOTE: Write APIs must stay localhost. Never log full inventory or passwords.
AI_SAFE: Allow-list and bak basename checks. Do not execute device output.
"""
from __future__ import annotations

import ipaddress
import os
import re
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

ALLOWED_DEVICE_TYPES = frozenset({
    'cisco_ios',
    'cisco_xe',
    'cisco_nxos',
    'cisco_xr',
    'cisco_aci',
    'juniper_junos',
})

# Aliases operators still type; stored as canonical allow-list ids.
_TYPE_ALIASES = {
    'cisco_ios-xe': 'cisco_xe',
    'cisco_ios_xe': 'cisco_xe',
    'ios-xe': 'cisco_xe',
    'ios_xe': 'cisco_xe',
    'nxos': 'cisco_nxos',
    'junos': 'juniper_junos',
    'aci': 'cisco_aci',
    'apic': 'cisco_aci',
    'cisco_apic': 'cisco_aci',
}

MAX_BYTES = 2 * 1024 * 1024
MAX_LINES = 20000
BAK_KEEP = 10
BAK_PREFIX = 'inventory.txt.bak.'
_GROUP_HEADER = re.compile(r'^\[([\w\-_ ]+)\]$')

DEFAULT_INVENTORY_NAME = 'inventory.txt'


class InventoryError(ValueError):
    """Operator-facing validation failure (HTTP 400)."""


def resolve_inventory_path(explicit: Optional[str] = None) -> str:
    """Path of the committed inventory.txt (CWD-first, matching GET /api/inventory)."""
    if explicit:
        return os.path.abspath(explicit)
    env = (os.environ.get('NST_INVENTORY_PATH') or '').strip()
    if env:
        return os.path.abspath(env)
    cwd = os.path.abspath(os.path.join(os.getcwd(), DEFAULT_INVENTORY_NAME))
    nested = os.path.abspath(os.path.join(os.getcwd(), 'inventory', DEFAULT_INVENTORY_NAME))
    if os.path.isfile(cwd):
        return cwd
    if os.path.isfile(nested):
        return nested
    return cwd


def read_inventory_text(path: Optional[str] = None) -> str:
    target = resolve_inventory_path(path)
    if not os.path.isfile(target):
        raise InventoryError('No local inventory.txt found.')
    with open(target, encoding='utf-8') as f:
        return f.read()


def check_size(text: str) -> None:
    if text is None:
        raise InventoryError('Inventory text is required.')
    if not isinstance(text, str):
        raise InventoryError('Inventory text must be a string.')
    if len(text.encode('utf-8')) > MAX_BYTES:
        raise InventoryError(f'Inventory exceeds {MAX_BYTES} bytes.')
    if text.count('\n') + 1 > MAX_LINES:
        raise InventoryError(f'Inventory exceeds {MAX_LINES} lines.')


def _norm_type(raw: str) -> Tuple[str, Optional[str]]:
    t = (raw or '').strip().lower().replace('-', '_')
    # restore ios_xe style after blanket replace: cisco_ios_xe already handled
    alias_key = (raw or '').strip().lower()
    if alias_key in _TYPE_ALIASES:
        return _TYPE_ALIASES[alias_key], f'normalized from {alias_key}'
    collapsed = alias_key.replace('-', '_')
    if collapsed in _TYPE_ALIASES:
        return _TYPE_ALIASES[collapsed], f'normalized from {alias_key}'
    return t, None


def _normalize_inventory_host(raw: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (canonical_ip, None) or (None, reject_reason). Hostnames are rejected."""
    host = (raw or '').strip()
    if not host:
        return None, 'reject — host must be IPv4 or IPv6'
    # Optional brackets for IPv6 literals: [2001:db8::1]
    if host.startswith('[') and host.endswith(']') and len(host) > 2:
        host = host[1:-1].strip()
    try:
        return str(ipaddress.ip_address(host)), None
    except ValueError:
        return None, 'reject — host must be IPv4 or IPv6 (DNS names are not accepted)'


def preview(text: str) -> Dict[str, Any]:
    """Parse v1 text into per-line accept/warn/reject without writing."""
    check_size(text)
    rows: List[Dict[str, Any]] = []
    seen: Dict[Tuple[str, int], int] = {}
    current_group = 'Default'
    accept = warn = reject = 0

    for idx, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        g_m = _GROUP_HEADER.match(line)
        if g_m:
            current_group = g_m.group(1)
            continue

        row: Dict[str, Any] = {
            'line': idx,
            'raw': raw_line,
            'host': '',
            'device_type': '',
            'port': 22,
            'group': current_group,
            'status': 'reject',
            'reason': '',
        }
        parts = [p.strip() for p in line.split(',')]
        if len(parts) < 2 or not parts[0] or not parts[1]:
            row['reason'] = 'parse error — need IP,device_type[,group]'
            reject += 1
            rows.append(row)
            continue

        host_raw = parts[0]
        host, host_err = _normalize_inventory_host(host_raw)
        if host_err or not host:
            row['host'] = host_raw
            row['reason'] = host_err or 'reject — host must be IPv4 or IPv6'
            reject += 1
            rows.append(row)
            continue

        dtype, alias_note = _norm_type(parts[1])
        port = 22
        grp = current_group
        if len(parts) >= 3:
            if parts[2].isdigit():
                try:
                    port = int(parts[2])
                except ValueError:
                    row['reason'] = 'parse error — invalid port'
                    reject += 1
                    rows.append(row)
                    continue
                if not (1 <= port <= 65535):
                    row['reason'] = 'reject — port out of range'
                    reject += 1
                    rows.append(row)
                    continue
                if len(parts) >= 4 and parts[3]:
                    grp = parts[3]
            elif parts[2]:
                grp = parts[2]

        row['host'] = host
        row['device_type'] = dtype
        row['port'] = port
        row['group'] = grp

        if dtype not in ALLOWED_DEVICE_TYPES:
            row['status'] = 'reject'
            row['reason'] = f'reject — unknown device_type ({parts[1]})'
            reject += 1
            rows.append(row)
            continue

        key = (host.lower(), port)
        if key in seen:
            row['status'] = 'warn'
            row['reason'] = f'warn — duplicate of line {seen[key]} (host, port)'
            warn += 1
            rows.append(row)
            continue

        seen[key] = idx
        row['status'] = 'accept'
        row['reason'] = alias_note or 'accept'
        accept += 1
        rows.append(row)

    accepted_devices = [
        {
            'host': r['host'],
            'device_type': r['device_type'],
            'port': r['port'],
            'group': r['group'],
        }
        for r in rows
        if r['status'] == 'accept'
    ]
    return {
        'rows': rows,
        'counts': {
            'accept': accept,
            'warn': warn,
            'reject': reject,
            'device_rows': len(rows),
        },
        'accepted': accepted_devices,
        'can_commit': accept > 0,
    }


def format_v1(devices: List[Dict[str, Any]]) -> str:
    """Write inventory.txt v1. Group headers when group changes; omit port 22."""
    lines = [
        '# Committed by Network Swiss Tool Pro',
        '# Format: IP,device_type[,group] or IP,device_type,port,group',
        '',
    ]
    current = None
    for d in devices:
        host = str(d.get('host') or '').strip()
        dtype = str(d.get('device_type') or '').strip()
        if not host or not dtype:
            continue
        port = int(d.get('port') or 22)
        grp = str(d.get('group') or 'Default').strip() or 'Default'
        if grp != current:
            lines.append(f'[{grp}]')
            current = grp
        if port == 22:
            lines.append(f'{host},{dtype},{grp}')
        else:
            lines.append(f'{host},{dtype},{port},{grp}')
    lines.append('')
    return '\n'.join(lines)


def _atomic_write(path: str, text: str) -> None:
    directory = os.path.dirname(os.path.abspath(path)) or os.getcwd()
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.inv.', suffix='.tmp', dir=directory)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def _bak_stamp() -> str:
    return datetime.now().strftime('%Y%m%d-%H%M%S')


def _bak_dir(inventory_path: str) -> str:
    return os.path.dirname(os.path.abspath(inventory_path)) or os.getcwd()


def list_baks(inventory_path: Optional[str] = None) -> List[Dict[str, Any]]:
    path = resolve_inventory_path(inventory_path)
    folder = _bak_dir(path)
    if not os.path.isdir(folder):
        return []
    items = []
    for name in os.listdir(folder):
        if not name.startswith(BAK_PREFIX):
            continue
        if '/' in name or '\\' in name or '..' in name:
            continue
        full = os.path.join(folder, name)
        if not os.path.isfile(full):
            continue
        items.append({
            'name': name,
            'mtime': datetime.fromtimestamp(os.path.getmtime(full)).strftime('%Y-%m-%d %H:%M:%S'),
            'bytes': os.path.getsize(full),
        })
    items.sort(key=lambda x: x['name'], reverse=True)
    return items


def prune_baks(inventory_path: str, keep: int = BAK_KEEP) -> None:
    folder = _bak_dir(inventory_path)
    baks = list_baks(inventory_path)
    for extra in baks[keep:]:
        try:
            os.remove(os.path.join(folder, extra['name']))
        except OSError:
            pass


def write_bak(inventory_path: str) -> Optional[str]:
    if not os.path.isfile(inventory_path):
        return None
    folder = _bak_dir(inventory_path)
    stamp = _bak_stamp()
    name = f'{BAK_PREFIX}{stamp}'
    dest = os.path.join(folder, name)
    n = 0
    while os.path.exists(dest):
        n += 1
        name = f'{BAK_PREFIX}{stamp}-{n}'
        dest = os.path.join(folder, name)
    with open(inventory_path, encoding='utf-8') as src:
        _atomic_write(dest, src.read())
    prune_baks(inventory_path)
    return name


def _safe_bak_name(name: str) -> str:
    base = os.path.basename(name or '')
    if not base.startswith(BAK_PREFIX):
        raise InventoryError('Invalid bak name.')
    if base != name or '/' in name or '\\' in name or '..' in name:
        raise InventoryError('Bak path traversal is not allowed.')
    return base


def commit(
    text: str,
    mode: str = 'replace',
    *,
    confirm: bool = False,
    inventory_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Write accepted rows. mode=replace|merge. Requires confirm=True."""
    mode = (mode or 'replace').strip().lower()
    if mode not in ('replace', 'merge'):
        raise InventoryError('mode must be replace or merge.')
    parsed = preview(text)
    if not confirm:
        raise InventoryError(
            'Set confirm=true after preview. '
            f"{parsed['counts']['accept']} accepted, "
            f"{parsed['counts']['reject']} rejected will be omitted, "
            f"{parsed['counts']['warn']} duplicate(s) omitted."
        )
    if not parsed['can_commit']:
        raise InventoryError('Cannot commit: 0 accepted rows.')

    path = resolve_inventory_path(inventory_path)
    incoming = list(parsed['accepted'])

    if mode == 'merge' and os.path.isfile(path):
        existing = preview(read_inventory_text(path))['accepted']
        index = {(d['host'].lower(), int(d['port'])): i for i, d in enumerate(existing)}
        merged = list(existing)
        for d in incoming:
            key = (d['host'].lower(), int(d['port']))
            if key in index:
                merged[index[key]] = d
            else:
                index[key] = len(merged)
                merged.append(d)
        devices = merged
    else:
        devices = incoming

    bak = write_bak(path)
    body = format_v1(devices)
    _atomic_write(path, body)
    return {
        'ok': True,
        'mode': mode,
        'path': path,
        'bak': bak,
        'written': len(devices),
        'accepted': parsed['counts']['accept'],
        'omitted_reject': parsed['counts']['reject'],
        'omitted_duplicate': parsed['counts']['warn'],
        'inventory': body,
        'counts': parsed['counts'],
    }


def restore(bak_name: str, *, confirm: bool = False, inventory_path: Optional[str] = None) -> Dict[str, Any]:
    if not confirm:
        raise InventoryError('Set confirm=true to restore a bak.')
    safe = _safe_bak_name(bak_name)
    path = resolve_inventory_path(inventory_path)
    src = os.path.join(_bak_dir(path), safe)
    if not os.path.isfile(src):
        raise InventoryError('Bak file not found.')
    with open(src, encoding='utf-8') as fh:
        text = fh.read()
    parsed = preview(text)
    bak = write_bak(path)
    _atomic_write(path, text)
    return {
        'ok': True,
        'restored': safe,
        'path': path,
        'bak': bak,
        'written': parsed['counts']['accept'],
        'omitted_reject': parsed['counts']['reject'],
        'inventory': text,
        'counts': parsed['counts'],
    }


class UnsavedInventoryError(InventoryError):
    """Sensitive job refused until operator acknowledges unsaved box."""
    http_status = 409
    code = 'unsaved_inventory'


SENSITIVE_EXECUTE_ACTIONS = frozenset({
    'add_vlan',
    'rename_vlan',
    'delete_vlan',
    'save_config',
})


def _committed_text_or_none(inventory_path: Optional[str] = None) -> Optional[str]:
    try:
        return read_inventory_text(inventory_path)
    except InventoryError:
        return None


def accepted_fingerprint(text: str) -> Tuple[Tuple, int]:
    """Stable identity of accepted rows (host, port, type, group)."""
    if not (text or '').strip():
        return tuple(), 0
    parsed = preview(text)
    keys = tuple(sorted(
        (
            str(d.get('host') or '').lower(),
            int(d.get('port') or 22),
            str(d.get('device_type') or ''),
            str(d.get('group') or '').lower(),
        )
        for d in parsed['accepted']
    ))
    return keys, int(parsed['counts']['accept'])


def describe_inventory_state(
    box_text: str,
    *,
    inventory_path: Optional[str] = None,
    committed_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Compare unsaved box to committed file without writing."""
    if committed_text is None:
        committed_text = _committed_text_or_none(inventory_path)
    box = box_text if isinstance(box_text, str) else ''
    box_fp, box_n = accepted_fingerprint(box)
    if committed_text is None:
        state = 'no_committed' if box_n else 'both_empty'
        return {
            'state': state,
            'box_differs': bool(box_n),
            'box_count': box_n,
            'committed_count': 0,
            'has_committed': False,
        }
    _committed_fp, committed_n = accepted_fingerprint(committed_text)
    if box_n == 0 and committed_n == 0:
        state = 'both_empty'
    elif box_n == 0 and committed_n > 0:
        state = 'committed_only'
    elif committed_n == 0 and box_n > 0:
        state = 'box_only'
    elif box_fp == _committed_fp:
        state = 'match'
    else:
        state = 'differs'
    return {
        'state': state,
        'box_differs': state in ('differs', 'box_only', 'committed_only'),
        'box_count': box_n,
        'committed_count': committed_n,
        'has_committed': True,
    }


def resolve_scope_text(
    box_text: str,
    source: Optional[str] = None,
    *,
    action: str = '',
    acknowledge_unsaved: bool = False,
    inventory_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Pick committed file vs unsaved box. Live UI should send inventory_source.

    Omitted/auto source keeps the historic contract: non-empty request body wins
    (pytest and old clients). The operator console must send source explicitly.
    """
    box = box_text if isinstance(box_text, str) else ''
    raw = (source or '').strip().lower()
    if raw in ('', 'auto'):
        raw = 'auto'
    elif raw not in ('committed', 'unsaved'):
        raise InventoryError('inventory_source must be committed, unsaved, or auto.')

    committed = _committed_text_or_none(inventory_path)
    cmp = describe_inventory_state(box, inventory_path=inventory_path, committed_text=committed)
    legacy = raw == 'auto'

    if raw == 'committed' or (legacy and not box.strip() and committed is not None):
        if committed is None:
            raise InventoryError(
                'No committed inventory.txt. Import or commit first, or set inventory_source=unsaved.'
            )
        used = 'committed'
        text = committed
    elif raw == 'unsaved' or (legacy and box.strip()):
        used = 'unsaved'
        text = box
    elif committed is not None:
        used = 'committed'
        text = committed
    else:
        used = 'none'
        text = ''

    if used == 'unsaved' and not (text or '').strip():
        raise InventoryError('Unsaved inventory box is empty.')

    sensitive = (action or '') in SENSITIVE_EXECUTE_ACTIONS
    if (
        used == 'unsaved'
        and sensitive
        and not acknowledge_unsaved
        and not legacy
        and cmp['state'] in ('differs', 'box_only', 'no_committed', 'committed_only')
    ):
        raise UnsavedInventoryError(
            'Unsaved inventory box is not committed inventory.txt. '
            'Commit first, run with inventory_source=committed, '
            'or set acknowledge_unsaved=true to run the box.'
        )

    warning = None
    if legacy and used == 'unsaved':
        warning = 'legacy_body'
    if used == 'committed' and cmp['state'] == 'differs':
        warning = 'box_differs_using_committed'
    if used == 'unsaved' and cmp['state'] == 'differs':
        warning = 'using_unsaved_box'

    fp, n = accepted_fingerprint(text)
    return {
        'text': text,
        'source_used': used,
        'state': cmp['state'],
        'legacy': legacy,
        'box_differs': cmp['box_differs'],
        'box_count': cmp['box_count'],
        'committed_count': cmp['committed_count'],
        'accepted_count': n,
        'warning': warning,
        'fingerprint_size': len(fp),
    }
