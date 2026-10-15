"""
Explicit job target sources — Discovery seeds and IM single-host.

Not bulk inventory.txt. Do not silently convert one source into another.

AI_CONTEXT: Phase 0 identity for crawl/IM vs execute inventory scope.
AI_SECURITY_NOTE: No passwords. Reject path-like hosts. Localhost APIs only.
AI_SAFE: Allow-list device types. Empty/malformed seeds fail closed.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from modules.inventory_store import ALLOWED_DEVICE_TYPES, InventoryError, preview, read_inventory_text

# Catalog / API values stored in job_index.inventory_source
SOURCE_DISCOVERY_SEEDS = 'discovery_seeds'
SOURCE_COMMITTED_INVENTORY = 'committed_inventory'
SOURCE_UNSAVED_INVENTORY = 'unsaved_inventory'
SOURCE_SINGLE_HOST = 'single_host'
SOURCE_LEGACY_BODY = 'legacy_body'
SOURCE_CIDR_SCAN = 'cidr_scan'
SOURCE_EXPLICIT_HOST_LIST = 'explicit_host_list'
SOURCE_DEMO = 'demo'

MAX_PING_HOSTS = 256

DISCOVERY_SOURCES = frozenset({
    SOURCE_DISCOVERY_SEEDS,
    SOURCE_COMMITTED_INVENTORY,
    SOURCE_UNSAVED_INVENTORY,
    SOURCE_LEGACY_BODY,
})
IM_SOURCES = frozenset({
    SOURCE_SINGLE_HOST,
    SOURCE_COMMITTED_INVENTORY,
    SOURCE_UNSAVED_INVENTORY,
    SOURCE_LEGACY_BODY,
})

_HOST_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._:\-]{0,252}$')
_TYPE_ALIASES = {
    'cisco_ios-xe': 'cisco_xe',
    'cisco_ios_xe': 'cisco_xe',
    'ios-xe': 'cisco_xe',
    'ios_xe': 'cisco_xe',
    'nxos': 'cisco_nxos',
    'junos': 'juniper_junos',
}


class JobSourceError(InventoryError):
    """Operator-facing target/source validation failure."""


def _canon_type(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    t = raw.strip().lower().replace(' ', '_')
    t = _TYPE_ALIASES.get(t, t)
    if t not in ALLOWED_DEVICE_TYPES:
        return None
    return t


def validate_host_token(host: str) -> str:
    h = (host or '').strip()
    if not h:
        raise JobSourceError('Host is required.')
    if '..' in h or '/' in h or '\\' in h or '\x00' in h:
        raise JobSourceError('Host contains a path or traversal token.')
    if any(x in h.lower() for x in ('password', 'enable_pwd', 'secret=')):
        raise JobSourceError('Host token rejected.')
    if not _HOST_RE.match(h):
        raise JobSourceError(f'Malformed host: {h[:80]}')
    return h


def parse_seed_line(raw: str) -> Tuple[str, str]:
    """Return (host, device_type). Type defaults to cisco_ios when omitted."""
    line = (raw or '').strip()
    if not line or line.startswith('#'):
        raise JobSourceError('Empty seed line.')
    if ',' in line:
        host, dtype = [p.strip() for p in line.split(',', 1)]
        extra = dtype.split(',')[0].strip() if dtype else ''
        dtype = extra.split()[0] if extra else 'cisco_ios'
    else:
        parts = line.split()
        host = parts[0]
        dtype = parts[1] if len(parts) >= 2 else 'cisco_ios'
    host = validate_host_token(host)
    if dtype and _canon_type(dtype) is None:
        raise JobSourceError(f'Unknown device_type for seed {host}: {dtype}')
    canon = _canon_type(dtype) or 'cisco_ios'
    return host, canon


def _unique_seeds(rows: List[Tuple[str, str]]) -> Tuple[List[Tuple[str, str]], int]:
    seen = set()
    out: List[Tuple[str, str]] = []
    dup = 0
    for host, dtype in rows:
        key = host.lower()
        if key in seen:
            dup += 1
            continue
        seen.add(key)
        out.append((host, dtype))
    return out, dup


def _hosts_from_inventory_text(text: str) -> List[Tuple[str, str]]:
    parsed = preview(text)
    rows = []
    for rec in parsed.get('accepted') or []:
        host = validate_host_token(str(rec.get('host') or ''))
        dtype = _canon_type(rec.get('device_type')) or 'cisco_ios'
        rows.append((host, dtype))
    rows, _ = _unique_seeds(rows)
    return rows


def resolve_discovery_targets(data: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve crawl seeds. Never writes inventory.txt. Never uses box unless explicit."""
    raw_src = (data.get('target_source') or data.get('inventory_source') or '').strip().lower()
    legacy = not raw_src
    if legacy:
        raw_src = SOURCE_DISCOVERY_SEEDS
        if not data.get('seed_hosts') and (data.get('inventory') or '').strip():
            raise JobSourceError(
                'Inventory text is not Discovery seeds. '
                'Set target_source=committed_inventory or unsaved_inventory, '
                'or pass seed_hosts.'
            )
    aliases = {
        'committed': SOURCE_COMMITTED_INVENTORY,
        'unsaved': SOURCE_UNSAVED_INVENTORY,
        'seeds': SOURCE_DISCOVERY_SEEDS,
        'seed': SOURCE_DISCOVERY_SEEDS,
        'auto': SOURCE_DISCOVERY_SEEDS,
    }
    source = aliases.get(raw_src, raw_src)
    if source not in DISCOVERY_SOURCES:
        raise JobSourceError(
            'target_source must be discovery_seeds, committed_inventory, or unsaved_inventory.'
        )

    rejected: List[str] = []
    seeds: List[Tuple[str, str]] = []
    dup = 0

    if source == SOURCE_COMMITTED_INVENTORY:
        try:
            text = read_inventory_text()
        except InventoryError as exc:
            raise JobSourceError(str(exc)) from exc
        seeds = _hosts_from_inventory_text(text)
        if not seeds:
            raise JobSourceError('Committed inventory.txt has no accepted hosts to use as seeds.')
    elif source == SOURCE_UNSAVED_INVENTORY:
        box = data.get('inventory')
        if box is None:
            box = ''
        if not str(box).strip():
            raise JobSourceError('Unsaved inventory box is empty; cannot use it as Discovery seeds.')
        seeds = _hosts_from_inventory_text(str(box))
        if not seeds:
            raise JobSourceError('Unsaved inventory has no accepted hosts to use as seeds.')
    else:
        raw_seeds = data.get('seed_hosts') or []
        if isinstance(raw_seeds, str):
            raw_seeds = [s for s in re.split(r'[,\n]+', raw_seeds) if s.strip()]
        if not raw_seeds:
            raise JobSourceError('At least one seed host is required.')
        parsed: List[Tuple[str, str]] = []
        for item in raw_seeds:
            try:
                parsed.append(parse_seed_line(str(item)))
            except JobSourceError as exc:
                rejected.append(str(exc))
        if rejected:
            raise JobSourceError('Malformed seeds: ' + '; '.join(rejected[:8]))
        seeds, dup = _unique_seeds(parsed)
        source = SOURCE_LEGACY_BODY if legacy else SOURCE_DISCOVERY_SEEDS

    seed_hosts = [h for h, _ in seeds]
    seed_typed = [f'{h},{t}' for h, t in seeds]
    warning = None
    if source == SOURCE_COMMITTED_INVENTORY:
        warning = 'committed_hosts_as_seeds_not_census'
    if source == SOURCE_UNSAVED_INVENTORY:
        warning = 'unsaved_hosts_as_seeds_not_census'
    if source == SOURCE_LEGACY_BODY:
        warning = 'legacy_seed_hosts'
    return {
        'target_source': source,
        'legacy': legacy and source == SOURCE_LEGACY_BODY,
        'seed_hosts': seed_hosts,
        'seed_typed': seed_typed,
        'seed_count': len(seed_hosts),
        'duplicates_omitted': dup,
        'device_count': len(seed_hosts),
        'warning': warning,
    }


def resolve_im_target(data: Dict[str, Any]) -> Dict[str, Any]:
    """One host. Never substitute committed inventory for a typed host."""
    raw_src = (data.get('target_source') or data.get('inventory_source') or '').strip().lower()
    legacy = not raw_src
    aliases = {
        'committed': SOURCE_COMMITTED_INVENTORY,
        'unsaved': SOURCE_UNSAVED_INVENTORY,
        'host': SOURCE_SINGLE_HOST,
        'single': SOURCE_SINGLE_HOST,
        'auto': SOURCE_SINGLE_HOST,
    }
    source = aliases.get(raw_src, raw_src) if raw_src else SOURCE_SINGLE_HOST
    if source not in IM_SOURCES:
        raise JobSourceError(
            'target_source must be single_host, committed_inventory, or unsaved_inventory.'
        )

    host_raw = data.get('host')
    if host_raw is None or not str(host_raw).strip():
        raise JobSourceError('Host is required. Interface Manager targets one device, not bulk inventory.')
    host = validate_host_token(str(host_raw))

    dtype_in = data.get('device_type') or 'cisco_ios'

    if source == SOURCE_COMMITTED_INVENTORY:
        try:
            text = read_inventory_text()
        except InventoryError as exc:
            raise JobSourceError(str(exc)) from exc
        rows = _hosts_from_inventory_text(text)
        match = next((r for r in rows if r[0].lower() == host.lower()), None)
        if not match:
            raise JobSourceError(
                f'Host {host} is not in committed inventory.txt. '
                'Use target_source=single_host for a typed host.'
            )
        dtype_in = match[1]
    elif source == SOURCE_UNSAVED_INVENTORY:
        box = data.get('inventory') or ''
        rows = _hosts_from_inventory_text(str(box))
        match = next((r for r in rows if r[0].lower() == host.lower()), None)
        if not match:
            raise JobSourceError(
                f'Host {host} is not in the unsaved inventory box. '
                'IM does not take the first inventory line automatically.'
            )
        dtype_in = match[1]
    elif legacy:
        source = SOURCE_SINGLE_HOST

    if source == SOURCE_SINGLE_HOST:
        dtype_out = str(data.get('device_type') or 'cisco_ios')
    else:
        dtype_out = _canon_type(str(dtype_in)) or 'cisco_ios'
    return {
        'target_source': source,
        'legacy': legacy,
        'host': host,
        'device_type': dtype_out,
        'device_count': 1,
        'warning': 'legacy_host_field' if legacy else None,
    }


def _cidr_host_count(net) -> int:
    n = int(net.num_addresses)
    if net.version == 4 and net.prefixlen < 31:
        n = max(0, n - 2)
    return n


def resolve_cidr_scan(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ping Scan is ICMP CIDR only. Never inventory.txt or Discovery seeds."""
    import ipaddress

    raw_src = (data.get('target_source') or data.get('inventory_source') or '').strip().lower()
    legacy = not raw_src
    aliases = {
        'cidr': SOURCE_CIDR_SCAN,
        'ping_scan': SOURCE_CIDR_SCAN,
        'ping': SOURCE_CIDR_SCAN,
        'auto': SOURCE_CIDR_SCAN,
    }
    if raw_src in ('committed', 'unsaved', SOURCE_COMMITTED_INVENTORY, SOURCE_UNSAVED_INVENTORY,
                   SOURCE_DISCOVERY_SEEDS, SOURCE_SINGLE_HOST):
        raise JobSourceError(
            'Ping Scan is a CIDR sweep, not an inventory or Discovery job. '
            'Set target_source=cidr_scan and pass network= (e.g. 192.168.1.0/24).'
        )
    if legacy:
        source = SOURCE_LEGACY_BODY
    else:
        source = aliases.get(raw_src, raw_src)
        if source not in (SOURCE_CIDR_SCAN, SOURCE_LEGACY_BODY):
            raise JobSourceError('Ping Scan target_source must be cidr_scan.')

    network = (data.get('network') or data.get('cidr') or '').strip()
    if not network:
        raise JobSourceError('CIDR network is required (e.g. 192.168.1.0/24).')
    if '..' in network or '\\' in network or '\x00' in network:
        raise JobSourceError('Network contains a path or traversal token.')
    if network.count('/') != 1:
        raise JobSourceError('Network must be CIDR (address/prefix), not a host list or inventory line.')
    if any(tok in network.lower() for tok in ('password', 'secret=', 'inventory')):
        raise JobSourceError('Network token rejected.')
    try:
        net = ipaddress.ip_network(network, strict=False)
    except ValueError as exc:
        raise JobSourceError(f'Invalid CIDR: {exc}') from exc
    host_count = _cidr_host_count(net)
    if host_count < 1:
        raise JobSourceError('CIDR has no host addresses to scan.')
    if host_count > MAX_PING_HOSTS:
        raise JobSourceError(
            f'CIDR too large ({host_count} hosts). Max {MAX_PING_HOSTS} hosts '
            f'(typically IPv4 /24 or longer prefix). This is not an inventory map.'
        )
    warning = 'legacy_cidr_scan' if source == SOURCE_LEGACY_BODY else None
    return {
        'target_source': source,
        'legacy': source == SOURCE_LEGACY_BODY,
        'network': str(net),
        'device_count': host_count,
        'warning': warning,
    }


def _devices_from_inventory_text(text: str) -> List[Dict[str, Any]]:
    parsed = preview(text)
    devices: List[Dict[str, Any]] = []
    for rec in parsed.get('accepted') or []:
        host = validate_host_token(str(rec.get('host') or ''))
        dtype = _canon_type(rec.get('device_type')) or 'cisco_ios'
        port = int(rec.get('port') or 22)
        devices.append({'host': host, 'device_type': dtype, 'port': port})
    return devices


def _devices_from_explicit_list(raw: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw, list) or not raw:
        raise JobSourceError('explicit_host_list requires a non-empty devices array.')
    devices: List[Dict[str, Any]] = []
    seen = set()
    for item in raw:
        if isinstance(item, str):
            host, dtype = parse_seed_line(item)
            port = 22
        elif isinstance(item, dict):
            host = validate_host_token(str(item.get('host') or ''))
            dtype = _canon_type(item.get('device_type')) or 'cisco_ios'
            try:
                port = int(item.get('port') or 22)
            except (TypeError, ValueError):
                port = 22
        else:
            raise JobSourceError('Each device must be a host string or {host, device_type} object.')
        key = host.lower()
        if key in seen:
            continue
        seen.add(key)
        devices.append({'host': host, 'device_type': dtype, 'port': port})
    if not devices:
        raise JobSourceError('explicit_host_list has no valid hosts.')
    return devices


def resolve_stp_targets(data: Dict[str, Any]) -> Dict[str, Any]:
    """STP is inventory-scope SSH (or demo). Not a Discovery crawl and not CIDR."""
    if data.get('demo_mode'):
        return {
            'target_source': SOURCE_DEMO,
            'legacy': False,
            'devices': [],
            'device_count': 3,
            'warning': 'stp_demo_synthetic',
        }

    raw_src = (data.get('target_source') or data.get('inventory_source') or '').strip().lower()
    devices_in = data.get('devices') or []
    legacy = not raw_src
    aliases = {
        'committed': 'committed',
        SOURCE_COMMITTED_INVENTORY: 'committed',
        'unsaved': 'unsaved',
        SOURCE_UNSAVED_INVENTORY: 'unsaved',
        SOURCE_EXPLICIT_HOST_LIST: SOURCE_EXPLICIT_HOST_LIST,
        'hosts': SOURCE_EXPLICIT_HOST_LIST,
        SOURCE_LEGACY_BODY: SOURCE_LEGACY_BODY,
    }

    if legacy:
        if devices_in:
            devices = _devices_from_explicit_list(devices_in)
            return {
                'target_source': SOURCE_LEGACY_BODY,
                'legacy': True,
                'devices': devices,
                'device_count': len(devices),
                'warning': 'legacy_stp_devices_body',
            }
        raise JobSourceError(
            'STP needs inventory_source=committed or unsaved, '
            'target_source=explicit_host_list, or demo_mode=true. '
            'The unsaved box is not used unless source is unsaved.'
        )

    source = aliases.get(raw_src, raw_src)
    if source in (SOURCE_CIDR_SCAN, 'cidr', SOURCE_DISCOVERY_SEEDS):
        raise JobSourceError(
            'STP is an inventory-scope (or explicit host list) scan, not CIDR or Discovery seeds.'
        )

    if source == SOURCE_EXPLICIT_HOST_LIST:
        devices = _devices_from_explicit_list(devices_in)
        return {
            'target_source': SOURCE_EXPLICIT_HOST_LIST,
            'legacy': False,
            'devices': devices,
            'device_count': len(devices),
            'warning': None,
        }

    if source not in ('committed', 'unsaved'):
        raise JobSourceError(
            'STP inventory_source must be committed or unsaved '
            '(or target_source=explicit_host_list / demo_mode).'
        )

    from modules.inventory_store import resolve_scope_text
    box = data.get('inventory')
    if box is None:
        box = ''
    resolved = resolve_scope_text(
        box,
        source,
        action='stp',
        acknowledge_unsaved=bool(data.get('acknowledge_unsaved')),
    )
    devices = _devices_from_inventory_text(resolved['text'])
    if not devices:
        raise JobSourceError('STP scope has 0 accepted hosts.')
    label = SOURCE_COMMITTED_INVENTORY if resolved['source_used'] == 'committed' else SOURCE_UNSAVED_INVENTORY
    return {
        'target_source': label,
        'legacy': False,
        'devices': devices,
        'device_count': len(devices),
        'warning': resolved.get('warning'),
        'inventory_state': resolved.get('state'),
    }
