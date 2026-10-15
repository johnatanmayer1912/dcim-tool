"""CLI path reconstruction with evidence.

Follows MAC hits and existing L2 edges only. Never invents a hop.
Not a forwarding-plane / ACL path and not DNA Path Trace.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _norm_port(name: str) -> str:
    s = (name or '').strip()
    # Junos: strip unit suffix for physical matching (ge-0/0/0.0 → ge-0/0/0)
    try:
        from utils.juniper_iface import is_junos_interface, split_junos_unit
        if is_junos_interface(s):
            phys, _logical = split_junos_unit(s)
            return phys.strip().lower()
    except Exception:
        pass
    # Longer Cisco names first so GigabitEthernet is not mangled by Ethernet→Eth
    return (
        s.replace('TwentyFiveGigabitEthernet', 'Twe')
        .replace('HundredGigabitEthernet', 'Hu')
        .replace('FortyGigabitEthernet', 'Fo')
        .replace('TenGigabitEthernet', 'Te')
        .replace('GigabitEthernet', 'Gi')
        .replace('FastEthernet', 'Fa')
        .replace('Ethernet', 'Eth')
        .replace('Port-channel', 'Po')
        .replace('port-channel', 'Po')
        .strip()
        .lower()
    )


def _edge_key_port(e: Dict[str, Any], which: str) -> str:
    if which == 'f':
        return _norm_port(str(e.get('f_port') or e.get('local_port') or ''))
    return _norm_port(str(e.get('t_port') or e.get('remote_port') or ''))


def next_hop_from_edges(
    host: str,
    port: str,
    edges: List[Dict[str, Any]],
) -> Optional[Tuple[str, str, Dict[str, Any]]]:
    """If an L2 edge exists from host:port, return (peer, peer_port, edge)."""
    h = (host or '').strip().lower()
    p = _norm_port(port)
    if not h or not p:
        return None
    for e in edges or []:
        if e.get('not_physical') or str(e.get('layer') or '').lower() in ('overlay', 'l3'):
            continue
        frm = str(e.get('from') or '').strip().lower()
        to = str(e.get('to') or '').strip().lower()
        fp, tp = _edge_key_port(e, 'f'), _edge_key_port(e, 't')
        if frm == h and fp == p and to:
            return e.get('to'), e.get('t_port') or '', e
        if to == h and tp == p and frm:
            return e.get('from'), e.get('f_port') or '', e
    return None


def reconstruct_path(
    mac_hits: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    target_mac: str = '',
) -> Dict[str, Any]:
    """Order MAC hits by following L2 edges between hits. Gaps stay visible.

    A hop is added only when a MAC hit exists and (for the next hop) a CDP/LLDP
    edge exists from that hit's port. No third hop is invented.
    """
    found = [h for h in (mac_hits or []) if h.get('found') and h.get('port') and h.get('hostname')]
    note = (
        'Reconstructed from MAC table CLI + existing CDP/LLDP edges. '
        'Not a forwarding path. Hops without an edge are not invented.'
    )
    if not found:
        return {
            'target_mac': target_mac,
            'hops': [],
            'complete': False,
            'unlinked_hits': [],
            'path_note': note,
            'gap': 'MAC not found on any provided hit',
        }

    by_host: Dict[str, Dict[str, Any]] = {}
    for h in found:
        by_host.setdefault(str(h.get('hostname') or '').lower(), h)

    successors: Dict[int, Tuple[Dict[str, Any], Tuple[str, str, Dict[str, Any]]]] = {}
    predecessor_ids = set()
    for h in found:
        nxt = next_hop_from_edges(h.get('hostname'), h.get('port'), edges)
        if not nxt:
            continue
        peer_hit = by_host.get(str(nxt[0] or '').lower())
        if peer_hit and id(peer_hit) != id(h):
            successors[id(h)] = (peer_hit, nxt)
            predecessor_ids.add(id(peer_hit))

    starts = [h for h in found if id(h) in successors and id(h) not in predecessor_ids]
    if not starts:
        starts = [h for h in found if id(h) in successors]
    current = starts[0] if starts else found[0]

    hops: List[Dict[str, Any]] = []
    used = set()
    while current and id(current) not in used:
        used.add(id(current))
        host, port = current.get('hostname'), current.get('port')
        hop = {
            'hostname': host,
            'port': port,
            'vlan': current.get('vlan'),
            'found': True,
            'command': current.get('command') or 'show mac address-table',
            'evidence': current.get('evidence') or f"{target_mac} on {port}",
            'next_host': None,
            'next_port': None,
            'edge_protocol': None,
        }
        linked = successors.get(id(current))
        if linked:
            peer_hit, nxt = linked
            hop['next_host'], hop['next_port'], edge = nxt[0], nxt[1], nxt[2]
            hop['edge_protocol'] = edge.get('protocol') or edge.get('discovery') or 'cdp'
            hop['evidence'] = (
                f"{hop['evidence']}; L2 edge {host}:{port} ↔ {hop['next_host']}:{hop['next_port']} "
                f"({hop['edge_protocol']})"
            )
            hops.append(hop)
            current = peer_hit
            continue
        hops.append(hop)
        break

    leftover = [h for h in found if id(h) not in used]
    return {
        'target_mac': target_mac,
        'hops': hops,
        'complete': bool(hops) and not leftover,
        'unlinked_hits': [
            {'hostname': h.get('hostname'), 'port': h.get('port')} for h in leftover
        ],
        'path_note': note,
    }


def collect_path_trace_from_mac_results(
    mac_results: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    target_mac: str,
) -> Dict[str, Any]:
    """Turn mac_trace-style per-device results into an evidenced path."""
    hits = []
    for res in mac_results or []:
        data = res.get('data') or res
        if not data.get('found') and res.get('status') not in ('success', None):
            continue
        if not data.get('found') and not res.get('found'):
            if not (res.get('found') or data.get('found')):
                continue
        hits.append({
            'hostname': data.get('true_host') or res.get('host') or data.get('hostname'),
            'port': data.get('port') or res.get('port'),
            'vlan': data.get('vlan') or res.get('vlan'),
            'found': bool(data.get('found') or res.get('found')),
            'command': data.get('command') or 'show mac address-table',
            'evidence': data.get('evidence') or (
                f"MAC on {data.get('port') or res.get('port')}"
                if (data.get('found') or res.get('found')) else 'not found'
            ),
        })
    return reconstruct_path(hits, edges, target_mac)
