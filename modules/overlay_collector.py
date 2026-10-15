"""EVPN/VXLAN overlay collection from device CLI.

Edges are only created from parsed NVE/EVPN output. Hostnames that look like
leaf/spine/vtep are never treated as overlay evidence.
"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional

_INVALID = (
    '% invalid', 'invalid input', 'invalid command', 'syntax error',
    'unknown command', 'error: syntax', 'could not find',
    'no such command', 'is not enabled', 'not configured',
)


def _cli_unsupported(text: str) -> bool:
    low = (text or '').lower()
    if not low.strip():
        return True
    return any(tok in low for tok in _INVALID)


def _send(send_fn: Callable, command: str, timeout: int = 60) -> str:
    try:
        return send_fn(command, timeout) if send_fn.__code__.co_argcount >= 2 else send_fn(command)
    except TypeError:
        return send_fn(command)


def parse_nve_peers(text: str, local_host: str) -> List[Dict[str, Any]]:
    """Parse NX-OS / IOS-XE `show nve peers`."""
    links: List[Dict[str, Any]] = []
    if _cli_unsupported(text):
        return links
    for line in (text or '').splitlines():
        line_s = line.strip()
        if not line_s or line_s.lower().startswith('interface') or set(line_s) <= set('- '):
            continue
        m = re.match(
            r'^(nve\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\S+)',
            line_s,
            re.I,
        )
        if not m:
            m = re.search(r'(nve\d+).+?(\d+\.\d+\.\d+\.\d+)', line_s, re.I)
            if not m:
                continue
            iface, peer = m.group(1), m.group(2)
            state = ''
        else:
            iface, peer, state = m.group(1), m.group(2), m.group(3)
        links.append({
            'from': local_host,
            'to': peer,
            'f_port': iface.lower(),
            't_port': 'nve',
            'protocol': 'EVPN',
            'layer': 'overlay',
            'edge_kind': 'nve-peer',
            'not_physical': True,
            'overlay_kind': 'vxlan-nve',
            'nve_state': state,
            'sources': ['show nve peers'],
        })
    return links


def parse_nve_vni(text: str) -> List[str]:
    """Return VNI ids from `show nve vni` (informational; does not invent peers)."""
    vnis: List[str] = []
    if _cli_unsupported(text):
        return vnis
    for line in (text or '').splitlines():
        m = re.search(r'\b(\d{3,8})\b', line)
        if m and not line.lower().startswith('interface'):
            vni = m.group(1)
            if vni not in vnis and vni not in ('100', '1000'):
                # Keep numeric VNIs; skip tiny header-like numbers when possible
                if int(vni) >= 1000:
                    vnis.append(vni)
    return vnis


def parse_junos_evpn_neighbors(text: str, local_host: str) -> List[Dict[str, Any]]:
    """Parse `show evpn instance` neighbor IPs only."""
    links: List[Dict[str, Any]] = []
    if _cli_unsupported(text):
        return links
    for line in (text or '').splitlines():
        m = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
        if not m:
            continue
        low = line.lower()
        if 'source' in low and 'vtep' in low:
            continue
        if 'neighbor' not in low and 'peer' not in low:
            continue
        peer = m.group(1)
        links.append({
            'from': local_host,
            'to': peer,
            'f_port': 'vtep',
            't_port': 'vtep',
            'protocol': 'EVPN',
            'layer': 'overlay',
            'edge_kind': 'nve-peer',
            'not_physical': True,
            'overlay_kind': 'evpn-instance',
            'sources': ['show evpn instance'],
        })
    return links


def parse_junos_vxlan_remote(text: str, local_host: str) -> List[Dict[str, Any]]:
    """Parse `show ethernet-switching vxlan-tunnel-end-point remote`."""
    links: List[Dict[str, Any]] = []
    if _cli_unsupported(text):
        return links
    for line in (text or '').splitlines():
        m = re.search(r'(?:VTEP|vtep)\s+(?:address|ip)\s*[:=]\s*(\d+\.\d+\.\d+\.\d+)', line, re.I)
        if not m:
            m = re.search(r'\b(\d+\.\d+\.\d+\.\d+)\b', line)
            if not m or 'vtep' not in line.lower():
                continue
        peer = m.group(1)
        links.append({
            'from': local_host,
            'to': peer,
            'f_port': 'vtep',
            't_port': 'vtep',
            'protocol': 'EVPN',
            'layer': 'overlay',
            'edge_kind': 'nve-peer',
            'not_physical': True,
            'overlay_kind': 'vxlan-vtep',
            'sources': ['show ethernet-switching vxlan-tunnel-end-point remote'],
        })
    return links


def collect_overlay(
    conn: Any,
    hostname: str,
    dtype: str,
    send_fn: Optional[Callable] = None,
) -> Dict[str, Any]:
    """Run vendor overlay CLI. collected=True only if a supported command ran."""
    dtype_l = (dtype or '').lower()
    send = send_fn or (lambda cmd, timeout=60: conn.send_command(cmd, read_timeout=timeout))
    links: List[Dict[str, Any]] = []
    ran_supported = False
    commands: List[str] = []

    if 'juniper' in dtype_l:
        commands = [
            'show evpn instance',
            'show ethernet-switching vxlan-tunnel-end-point remote',
        ]
    else:
        commands = ['show nve peers', 'show nve vni']

    raw: Dict[str, str] = {}
    for cmd in commands:
        try:
            out = _send(send, cmd, 60)
        except Exception as exc:
            raw[cmd] = f'error:{exc}'
            continue
        raw[cmd] = out or ''
        if _cli_unsupported(out):
            continue
        ran_supported = True
        if 'nve peers' in cmd:
            links.extend(parse_nve_peers(out, hostname))
        elif 'nve vni' in cmd:
            vnis = parse_nve_vni(out)
            for link in links:
                if vnis and not link.get('vni'):
                    link['vni'] = ','.join(vnis[:8])
        elif 'evpn instance' in cmd:
            links.extend(parse_junos_evpn_neighbors(out, hostname))
        elif 'vxlan-tunnel-end-point' in cmd:
            links.extend(parse_junos_vxlan_remote(out, hostname))

    # Dedupe by (from, to, overlay_kind)
    seen = set()
    uniq = []
    for e in links:
        key = (e.get('from'), e.get('to'), e.get('overlay_kind'))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(e)

    if ran_supported:
        note = (
            'EVPN/NVE CLI ran. Overlay edges are VTEP/NVE peers, not cables.'
            if uniq else
            'EVPN/NVE CLI ran; no overlay peers in this crawl. Empty overlay is not an empty fabric.'
        )
    else:
        note = 'EVPN/VXLAN overlay is not collected — no supported NVE/EVPN CLI on this hop.'

    return {
        'collected': ran_supported,
        'links': uniq,
        'overlay_note': note,
        'raw_commands': list(raw.keys()),
    }
