"""NAPALM-inspired getters over Netmiko + ntc-templates (no NAPALM dependency).

Provides a thin, offline-friendly facts/interfaces layer so operators get
structured device state without requiring a full NAPALM multi-driver install.
Secrets never leave the session credential path.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from modules.ntc_parse import parse_cli


LogFn = Optional[Callable[[str], None]]


def _log(log: LogFn, msg: str) -> None:
    if log:
        try:
            log(msg)
        except Exception:
            pass


def _platform(device: Dict[str, Any]) -> str:
    return (device.get('device_type') or device.get('platform') or 'cisco_ios').strip().lower()


def get_facts_from_cli(platform: str, version_output: str, hostname: str = '') -> Dict[str, Any]:
    """Normalize show version into NAPALM-like facts dict."""
    rows, _ = parse_cli(platform, 'show version', version_output)
    facts: Dict[str, Any] = {
        'hostname': hostname or '',
        'vendor': '',
        'model': '',
        'serial_number': '',
        'os_version': '',
        'uptime': '',
        'source': 'cli+ntc' if rows else 'cli',
    }
    if rows:
        row = rows[0] if isinstance(rows[0], dict) else {}
        facts['hostname'] = row.get('hostname') or row.get('HOST') or facts['hostname']
        facts['model'] = row.get('hardware') or row.get('model') or row.get('PLATFORM') or ''
        facts['serial_number'] = row.get('serial') or row.get('serial_number') or ''
        facts['os_version'] = row.get('version') or row.get('os') or ''
        facts['uptime'] = row.get('uptime') or ''
        if 'cisco' in platform:
            facts['vendor'] = 'Cisco'
        elif 'juniper' in platform or 'junos' in platform:
            facts['vendor'] = 'Juniper'
        elif 'arista' in platform:
            facts['vendor'] = 'Arista'
    # Lightweight regex fallbacks when ntc misses
    if not facts['os_version'] and version_output:
        import re
        m = re.search(r'Version\s+([^\s,]+)', version_output, re.I)
        if m:
            facts['os_version'] = m.group(1)
        m2 = re.search(r'[Pp]rocessor board ID\s+(\S+)', version_output)
        if m2:
            facts['serial_number'] = m2.group(1)
        m3 = re.search(r'cisco\s+(\S+)', version_output, re.I)
        if m3 and not facts['model']:
            facts['model'] = m3.group(1)
            facts['vendor'] = facts['vendor'] or 'Cisco'
    return facts


def get_interfaces_from_cli(platform: str, iface_output: str) -> Dict[str, Dict[str, Any]]:
    """Parse show interfaces / show interface brief into NAPALM-like interfaces map."""
    cmd = 'show interfaces'
    if 'juniper' in platform or 'junos' in platform:
        cmd = 'show interfaces'
    rows, _ = parse_cli(platform, cmd, iface_output)
    out: Dict[str, Dict[str, Any]] = {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        name = row.get('interface') or row.get('port') or row.get('INTF') or ''
        if not name:
            continue
        out[name] = {
            'is_up': str(row.get('link_status') or row.get('status') or '').lower() in ('up', 'connected', 'true', '1'),
            'is_enabled': str(row.get('protocol_status') or row.get('admin') or 'up').lower() not in ('admin down', 'down', 'disabled'),
            'description': row.get('description') or row.get('desc') or '',
            'speed': row.get('bandwidth') or row.get('speed') or '',
            'mtu': row.get('mtu') or '',
            'mac_address': row.get('address') or row.get('mac_address') or row.get('bia') or '',
        }
    return out


def collect_device_snapshot(
    device: Dict[str, Any],
    connection,
    log: LogFn = None,
) -> Dict[str, Any]:
    """Collect facts + interfaces via an open Netmiko-like connection."""
    platform = _platform(device)
    host = device.get('host') or device.get('ip') or ''
    snapshot: Dict[str, Any] = {
        'host': host,
        'platform': platform,
        'facts': {},
        'interfaces': {},
        'errors': [],
    }
    try:
        ver_cmd = 'show version'
        if 'juniper' in platform or 'junos' in platform:
            ver_cmd = 'show version'
        ver = connection.send_command(ver_cmd, read_timeout=60)
        snapshot['facts'] = get_facts_from_cli(platform, ver or '', hostname=device.get('hostname') or '')
        _log(log, f"[{host}] NAPALM-style facts collected")
    except Exception as exc:
        snapshot['errors'].append(f'facts: {exc}')
        _log(log, f"[{host}] facts error: {exc}")
    try:
        if_cmd = 'show interfaces'
        if 'nxos' in platform:
            if_cmd = 'show interface'
        iface = connection.send_command(if_cmd, read_timeout=90)
        snapshot['interfaces'] = get_interfaces_from_cli(platform, iface or '')
        _log(log, f"[{host}] interfaces: {len(snapshot['interfaces'])} parsed")
    except Exception as exc:
        snapshot['errors'].append(f'interfaces: {exc}')
        _log(log, f"[{host}] interfaces error: {exc}")
    return snapshot


def capability_report() -> Dict[str, Any]:
    from modules.ntc_parse import capability_report as ntc_cap
    return {
        'layer': 'napalm_style',
        'full_napalm': False,
        'drivers': ['cisco_ios', 'cisco_xe', 'cisco_nxos', 'juniper_junos', 'arista_eos'],
        'getters': ['get_facts', 'get_interfaces'],
        'ntc': ntc_cap(),
        'note': 'Structured CLI getters via Netmiko + ntc-templates. Not a full NAPALM multi-driver install.',
    }
