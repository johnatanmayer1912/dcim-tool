"""Narrow show-interfaces counter parsers for live utilization.

Does not import interface_manager or discovery plugins (paramiko freeze / blast).
Golden fixtures live under tests/fixtures/utilization/cli/.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from utils.cisco_iface import normalize_cisco_iface
from utils.juniper_iface import split_junos_unit

# Cisco / NX-OS interface header
_CISCO_HDR = re.compile(
    r'^([A-Za-z][A-Za-z0-9._:-]*\d[\w./:-]*)\s+is\s+',
    re.I,
)
_IOS_IN = re.compile(
    r'(\d+)\s+packets input,\s+(\d+)\s+bytes',
    re.I,
)
_IOS_OUT = re.compile(
    r'(\d+)\s+packets output,\s+(\d+)\s+bytes',
    re.I,
)
_NX_IN_BYTES = re.compile(
    r'(\d+)\s+input packets\s+(\d+)\s+bytes',
    re.I,
)
_NX_OUT_BYTES = re.compile(
    r'(\d+)\s+output packets\s+(\d+)\s+bytes',
    re.I,
)
_BW_KBIT = re.compile(
    r'\bBW\s+(\d+)\s*Kbit',
    re.I,
)
_SPEED_GB = re.compile(
    r'\b(\d+(?:\.\d+)?)\s*Gb/?s\b',
    re.I,
)
_SPEED_MB = re.compile(
    r'\b(\d+(?:\.\d+)?)\s*Mb/?s\b',
    re.I,
)
_JUNOS_PHYS = re.compile(
    r'^Physical interface:\s+(\S+),',
    re.I,
)
_JUNOS_SPEED = re.compile(
    r'\bSpeed:\s+(\d+(?:\.\d+)?)\s*(mbps|gbps|kbps)',
    re.I,
)
_JUNOS_IN_BYTES = re.compile(
    r'Input\s+bytes\s*:\s*(\d+)',
    re.I,
)
_JUNOS_OUT_BYTES = re.compile(
    r'Output\s+bytes\s*:\s*(\d+)',
    re.I,
)

COMMANDS = {
    'cisco_ios': 'show interfaces',
    'cisco_xe': 'show interfaces',
    'cisco_nxos': 'show interface',
    'juniper_junos': 'show interfaces statistics',
}


def command_for_device_type(device_type: str) -> str:
    key = (device_type or '').strip().lower()
    return COMMANDS.get(key) or COMMANDS['cisco_ios']


def _speed_bps_from_cisco_block(block: str) -> Optional[int]:
    m = _BW_KBIT.search(block)
    if m:
        return int(m.group(1)) * 1000
    m = _SPEED_GB.search(block)
    if m:
        return int(float(m.group(1)) * 1_000_000_000)
    m = _SPEED_MB.search(block)
    if m:
        return int(float(m.group(1)) * 1_000_000)
    return None


def _flush_cisco(name: str, block: str, rows: List[Dict[str, Any]]) -> None:
    if not name:
        return
    in_m = _IOS_IN.search(block) or _NX_IN_BYTES.search(block)
    out_m = _IOS_OUT.search(block) or _NX_OUT_BYTES.search(block)
    in_octets = int(in_m.group(2)) if in_m else None
    out_octets = int(out_m.group(2)) if out_m else None
    speed = _speed_bps_from_cisco_block(block)
    rows.append({
        'if_name_raw': name,
        'if_name_normalized': normalize_cisco_iface(name) or name,
        'in_octets': in_octets,
        'out_octets': out_octets,
        'in_octets_64': in_octets,
        'out_octets_64': out_octets,
        'if_speed_bps': speed,
        'counter_width': '64',
    })


def parse_cisco_interfaces(output: str, device_type: str = 'cisco_ios') -> List[Dict[str, Any]]:
    """Parse IOS / IOS-XE / NX-OS `show interface(s)` counter blocks."""
    rows: List[Dict[str, Any]] = []
    current = ''
    buf: List[str] = []
    for line in (output or '').splitlines():
        hdr = _CISCO_HDR.match(line.strip())
        if hdr and not line.strip().lower().startswith('hardware'):
            token = hdr.group(1)
            # Skip continuation lines like "is up" mid-block descriptions
            if token.lower() in ('hardware', 'description', 'encapsulation'):
                buf.append(line)
                continue
            if current:
                _flush_cisco(current, '\n'.join(buf), rows)
            current = token
            buf = [line]
        else:
            buf.append(line)
    if current:
        _flush_cisco(current, '\n'.join(buf), rows)
    return rows


def parse_junos_interfaces(output: str) -> List[Dict[str, Any]]:
    """Parse `show interfaces statistics` physical Traffic statistics."""
    rows: List[Dict[str, Any]] = []
    current = ''
    speed = None
    in_octets = None
    out_octets = None
    in_logical = False

    def flush():
        nonlocal current, speed, in_octets, out_octets
        if current and not current.lower().startswith(('irb', 'vlan', 'lo', 'me0', 'fxp', 'em0')):
            phys, _ = split_junos_unit(current)
            rows.append({
                'if_name_raw': phys or current,
                'if_name_normalized': phys or current,
                'in_octets': in_octets,
                'out_octets': out_octets,
                'in_octets_64': in_octets,
                'out_octets_64': out_octets,
                'if_speed_bps': speed,
                'counter_width': '64',
            })
        current = ''
        speed = None
        in_octets = None
        out_octets = None

    for raw in (output or '').splitlines():
        line = raw.rstrip()
        phys = _JUNOS_PHYS.match(line.strip())
        if phys:
            if current:
                flush()
            current = phys.group(1).rstrip(',')
            in_logical = False
            continue
        if line.strip().startswith('Logical interface'):
            in_logical = True
            continue
        if in_logical:
            continue
        sm = _JUNOS_SPEED.search(line)
        if sm and current:
            n = float(sm.group(1))
            unit = sm.group(2).lower()
            if unit == 'gbps':
                speed = int(n * 1_000_000_000)
            elif unit == 'mbps':
                speed = int(n * 1_000_000)
            else:
                speed = int(n * 1000)
        im = _JUNOS_IN_BYTES.search(line)
        if im and current and in_octets is None:
            in_octets = int(im.group(1))
        om = _JUNOS_OUT_BYTES.search(line)
        if om and current and out_octets is None:
            out_octets = int(om.group(1))
    if current:
        flush()
    return rows


def parse_interface_counters(output: str, device_type: str) -> List[Dict[str, Any]]:
    dtype = (device_type or '').strip().lower()
    if 'juniper' in dtype or dtype == 'juniper_junos':
        return parse_junos_interfaces(output)
    return parse_cisco_interfaces(output, dtype)
