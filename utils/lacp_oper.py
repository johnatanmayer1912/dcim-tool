"""LACP / port-channel oper-state from device CLI (not ifName heuristics)."""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Tuple


def _norm_port(name: str) -> str:
    s = (name or '').strip()
    return (
        s.replace('Ethernet', 'Eth')
        .replace('GigabitEthernet', 'Gi')
        .replace('FastEthernet', 'Fa')
        .replace('TenGigabitEthernet', 'Te')
        .replace('Port-channel', 'Po')
        .replace('port-channel', 'Po')
        .strip()
    )


def parse_port_channel_summary(text: str) -> Dict[str, Dict[str, Any]]:
    """Parse NX-OS/IOS `show port-channel summary` / `show etherchannel summary`.

    Returns { 'Po1': { 'members': [{'port': 'Eth1/1', 'up': True}, ...] } }
    """
    result: Dict[str, Dict[str, Any]] = {}
    current = None
    for line in (text or '').splitlines():
        line_s = line.strip()
        po_m = re.search(r'(Po\d+|port-channel\d+)\s*\(([A-Za-z]+)\)', line_s, re.I)
        if po_m:
            current = _norm_port(po_m.group(1))
            result.setdefault(current, {'members': [], 'bundle_flags': po_m.group(2)})
        if not current:
            continue
        for mem in re.finditer(
            r'((?:Eth|Gi|Te|Fa|Hu|Fo|Twe)\S+)\(([PDHRsI]+)\)',
            line_s,
            re.I,
        ):
            flags = mem.group(2).upper()
            result[current]['members'].append({
                'port': _norm_port(mem.group(1)),
                'up': 'P' in flags or 'H' in flags,
                'flags': flags,
            })
    return result


def parse_lacp_neighbor_index(lacp_neighbors: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """Flatten topology_mapper lacp_neighbors {Po: [members]} to port → state."""
    index: Dict[str, Dict[str, Any]] = {}
    for bundle, members in (lacp_neighbors or {}).items():
        for mem in members or []:
            port = _norm_port(str(mem.get('local_port') or ''))
            if not port:
                continue
            state = str(mem.get('partner_state') or '').lower()
            bundled = any(tok in state for tok in ('col', 'dist', 'collect', 'distrib', 'bndl'))
            if not state:
                bundled = True  # partner present without state → treat as collected, unknown oper
            index[port.lower()] = {
                'bundle': _norm_port(bundle),
                'partner_id': mem.get('partner_id') or '',
                'partner_port': mem.get('partner_port') or '',
                'partner_state': mem.get('partner_state') or '',
                'lacp_oper': 'bundled' if bundled and state else ('unknown' if not state else 'down'),
                'collected': True,
            }
    return index


def apply_lacp_to_edges(
    edges: List[Dict[str, Any]],
    lacp_index: Optional[Dict[str, Dict[str, Any]]] = None,
    pc_summary: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Stamp LACP oper-state onto LAG edges. Never deletes a bundle edge (T-L2-11)."""
    index = dict(lacp_index or {})
    if pc_summary:
        for bundle, data in pc_summary.items():
            for mem in data.get('members') or []:
                port = _norm_port(mem.get('port') or '').lower()
                if not port:
                    continue
                entry = index.setdefault(port, {'bundle': bundle, 'collected': True})
                entry['collected'] = True
                entry['bundle'] = entry.get('bundle') or bundle
                if mem.get('up') is False:
                    entry['lacp_oper'] = 'down'
                    entry['member_status'] = 'down'
                elif mem.get('up') and entry.get('lacp_oper') != 'down':
                    entry['lacp_oper'] = entry.get('lacp_oper') or 'bundled'
                    entry['member_status'] = 'up'

    collected_any = bool(index)
    for e in edges:
        fp = _norm_port(str(e.get('f_port') or e.get('local_port') or ''))
        info = index.get(fp.lower()) if fp else None
        if info and info.get('collected'):
            e['lacp_collected'] = True
            e['lacp_oper'] = info.get('lacp_oper') or 'unknown'
            e['lacp_bundle'] = info.get('bundle') or ''
            if info.get('partner_id'):
                e['lacp_partner'] = {
                    'partner_id': info.get('partner_id'),
                    'partner_port': info.get('partner_port'),
                    'partner_state': info.get('partner_state'),
                }
            if (info.get('lacp_oper') == 'down') or (info.get('member_status') == 'down'):
                e['degraded'] = True
            e['lag_note'] = (
                'LACP oper-state from show lacp neighbor / port-channel summary '
                f"({e.get('lacp_oper')}). Bundle edge is kept if present."
            )
        elif collected_any and e.get('bundle_kind') == 'bundle':
            e['lacp_collected'] = True
            e.setdefault('lacp_oper', 'bundle')
            e['lag_note'] = (
                'Bundle/AE ifName plus LACP collection on this hop. '
                'Member oper-state is on member edges.'
            )
    return edges


def collect_lacp(
    conn: Any,
    dtype: str,
    send_fn: Optional[Callable] = None,
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """Fetch LACP neighbor + port-channel summary. Returns (port_index, pc_summary)."""
    dtype_l = (dtype or '').lower()
    send = send_fn or (lambda cmd, timeout=60: conn.send_command(cmd, read_timeout=timeout))

    def _run(cmd: str) -> str:
        try:
            try:
                return send(cmd, 60)
            except TypeError:
                return send(cmd)
        except Exception:
            return ''

    from modules.topology_mapper import (
        _parse_juniper_lag_detail,
        _parse_lacp_neighbors_ios,
        _parse_lacp_neighbors_nxos,
    )

    neighbors: Dict[str, List[Dict[str, Any]]] = {}
    summary: Dict[str, Dict[str, Any]] = {}
    if 'juniper' in dtype_l:
        out = _run('show lacp interfaces')
        parsed = _parse_juniper_lag_detail(out)
        for ae, data in (parsed or {}).items():
            neighbors[_norm_port(ae)] = [
                {
                    'local_port': m.get('intf'),
                    'partner_id': m.get('partner_id'),
                    'partner_port': m.get('partner_port'),
                    'partner_state': m.get('status'),
                }
                for m in data.get('members') or []
            ]
    elif 'nxos' in dtype_l or 'nexus' in dtype_l:
        neighbors = _parse_lacp_neighbors_nxos(_run('show lacp neighbor'))
        summary = parse_port_channel_summary(_run('show port-channel summary'))
    else:
        neighbors = _parse_lacp_neighbors_ios(_run('show lacp neighbor'))
        summary = parse_port_channel_summary(_run('show etherchannel summary'))
        if not summary:
            summary = parse_port_channel_summary(_run('show port-channel summary'))

    return parse_lacp_neighbor_index(neighbors), summary
