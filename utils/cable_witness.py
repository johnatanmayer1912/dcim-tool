"""Cable witnesses from already-collected interface + neighbor data.

Does not prove a physical pair. Compares description / speed / duplex to CDP/LLDP.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def _norm(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', (s or '').lower())


def _norm_port(name: str) -> str:
    s = (name or '').strip()
    return (
        s.replace('Ethernet', 'Eth')
        .replace('GigabitEthernet', 'Gi')
        .replace('TenGigabitEthernet', 'Te')
        .replace('FastEthernet', 'Fa')
        .replace('Port-channel', 'Po')
        .replace('port-channel', 'Po')
        .strip()
    )


def description_matches_neighbor(desc: str, neighbor_host: str, neighbor_port: str = '') -> Optional[bool]:
    """True if description appears to name the neighbor. None if no usable description."""
    d = (desc or '').strip()
    if not d or d in ('-', '--', 'none', 'n/a'):
        return None
    host = (neighbor_host or '').strip()
    if not host:
        return None
    dn, hn = _norm(d), _norm(host)
    if hn and hn in dn:
        if neighbor_port:
            pn = _norm(_norm_port(neighbor_port))
            if pn and pn in dn:
                return True
        return True
    return False


def _speed_token(raw: str) -> str:
    s = (raw or '').lower().replace(' ', '')
    m = re.search(r'(\d+)\s*(g|m|gb|mb)?', s)
    if not m:
        return s
    n, unit = m.group(1), (m.group(2) or '')
    if unit.startswith('g') or (not unit and int(n) <= 100 and 'g' in s):
        return f'{n}g'
    if unit.startswith('m'):
        return f'{n}m'
    if int(n) >= 1000:
        return f'{int(n) // 1000}g'
    return f'{n}m'


def speeds_mismatch(a: str, b: str) -> bool:
    ta, tb = _speed_token(a), _speed_token(b)
    if not ta or not tb:
        return False
    return ta != tb


def duplex_mismatch(a: str, b: str) -> bool:
    da = (a or '').lower()
    db = (b or '').lower()
    if not da or not db:
        return False
    full_a = 'full' in da
    full_b = 'full' in db
    half_a = 'half' in da
    half_b = 'half' in db
    if (full_a and half_b) or (half_a and full_b):
        return True
    return False


def apply_cable_witnesses(edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Stamp desc/speed/duplex witnesses. Never invents an edge."""
    for e in edges:
        if e.get('not_physical') or str(e.get('layer') or '').lower() in ('overlay', 'l3'):
            continue
        f_int = e.get('f_int_data') or {}
        t_int = e.get('t_int_data') or {}
        desc = f_int.get('desc') or e.get('f_desc') or ''
        peer = e.get('to') or ''
        t_port = e.get('t_port') or ''
        match = description_matches_neighbor(desc, peer, t_port)
        witnesses: List[str] = list(e.get('cable_witnesses') or [])
        issues: List[str] = list(e.get('cable_issues') or [])
        if match is True:
            e['desc_vs_neighbor'] = 'match'
            witnesses.append('description names neighbor')
        elif match is False:
            e['desc_vs_neighbor'] = 'mismatch'
            issues.append('description_vs_neighbor')
            witnesses.append('description does not name neighbor — leftover or wrong patch intent')
        else:
            e['desc_vs_neighbor'] = 'unknown'

        fs, ts = f_int.get('speed') or '', t_int.get('speed') or ''
        if speeds_mismatch(fs, ts):
            e['speed_mismatch'] = True
            issues.append('speed_mismatch')
            witnesses.append(f'speed mismatch {fs or "?"} vs {ts or "?"}')
        fd, td = f_int.get('duplex') or '', t_int.get('duplex') or ''
        if duplex_mismatch(fd, td):
            e['duplex_mismatch'] = True
            issues.append('duplex_mismatch')
            witnesses.append(f'duplex mismatch {fd or "?"} vs {td or "?"}')
        e['cable_witnesses'] = witnesses
        e['cable_issues'] = issues
        e['cable_note'] = (
            'Witnesses from CLI (description/speed/duplex). Not a certified cable.'
        )
    return edges
