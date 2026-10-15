"""
Discovery graph identity and validation (v7.0.1).

AI_CONTEXT: Canonical device merge + CDP/LLDP cable identity before vis.js render.
AI_FLOW: merge_nodes → rewire_edges → trust → contradictions → protocol merge → LAG/AE annotate → validate
AI_DEPENDS_ON: utils.topology_trust.apply_discovery_edge_trust
AI_IMPACTS: discovery HTML maps, link inventory, crawl JSON
AI_MAP_NOTE: Never merge unlike ports; CDP+LLDP same cable → sources[] only. Overlay not built here.
AI_CRAWL_NOTE: Neighbor-only nodes stay until scanned; failed SSH is scan_state=failed
AI_RISKS: Hostname-only merge hides two devices; duplicate chassis must conflict not silent-merge
AI_DANGEROUS: Changing merge keys or cable keys can invent or drop links — run test_discovery_graph_dedup.py
AI_BREADCRUMB: parsers in modules/plugins/network_discovery.py → here → utils/discovery_map_formatter.py
AI_TEST_NOTE: tests/test_discovery_graph_dedup.py
"""
import re
from typing import Any, Dict, List, Optional, Tuple

_IP_RE = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')

# JunOS: token boundaries — never match 'ex' inside 'nexus'
_JUNOS_PLATFORM_RE = re.compile(
    r'(junos|juniper|qfx\d*|srx\d*|mx\d+|ex\d{3,}|ex-\d|ex4\d{3})',
    re.I,
)
_NXOS_PLATFORM_RE = re.compile(
    r'(nx-os|nxos|nexus\d*|n5k|n7k|n9k|n3k|mds)',
    re.I,
)
_IOSXE_PLATFORM_RE = re.compile(
    r'(ios-xe|iosxe|ios xe|asr9\d*|asr1\d*|isr4\d*|cat8k|c8000v|catalyst 8)',
    re.I,
)
_IOS_PLATFORM_RE = re.compile(
    r'(catalyst|cat\d|ws-c|c9\d{3}|c3\d{3}|cisco ios|\bios\b)',
    re.I,
)

_OS_FAMILY_LABEL = {
    'cisco_nxos': 'NX-OS',
    'cisco_xe': 'IOS-XE',
    'cisco_ios': 'IOS',
    'juniper_junos': 'JunOS',
}


def _norm_host(name: Optional[str]) -> str:
    if not name:
        return ''
    h = str(name).strip().split('(')[0].strip()
    h = re.sub(r'[:>#\]\)]+$', '', h).strip().lower()
    if _IP_RE.match(h):
        return h
    return h.split('.')[0] if h else ''


def _valid_ip(ip: Optional[str]) -> Optional[str]:
    if not ip or str(ip).lower() in ('unknown', 'none', ''):
        return None
    ip = str(ip).strip()
    return ip.lower() if _IP_RE.match(ip) else None


def classify_os_family(
    platform_str: Optional[str] = None,
    ver_output: Optional[str] = None,
    dtype_hint: Optional[str] = None,
) -> str:
    """
    Classify to cisco_nxos | cisco_ios | juniper_junos.
    NX-OS is checked before JunOS; JunOS uses word-boundary tokens (not bare 'ex').
    """
    if ver_output:
        low = ver_output.lower()
        if 'kernel junos' in low or 'juniper networks' in low or re.search(
            r'\bjunos\b', low,
        ):
            if 'cisco' not in low[:200] or 'juniper' in low:
                return 'juniper_junos'
        if 'nx-os' in low or 'cisco nexus' in low or (
            'nexus' in low and 'juniper' not in low
        ):
            return 'cisco_nxos'
        if 'ios-xe' in low or 'ios xe software' in low or re.search(r'\bios-xe\b', low):
            return 'cisco_xe'
        if re.search(r'\bios\s+software\b', low) or (
            'cisco ios' in low and 'nexus' not in low
        ):
            return 'cisco_ios'
        if re.search(r'\bios\s+software\b', low) or 'cisco ios' in low:
            return 'cisco_ios'

    p = (platform_str or '').strip()
    if p:
        pl = p.lower()
        # NX-OS before JunOS; explicit nexus substring (not bare 'ex' — BUG-0007)
        if _NXOS_PLATFORM_RE.search(p) or (
            'nexus' in pl and 'juniper' not in pl
        ):
            return 'cisco_nxos'
        if _JUNOS_PLATFORM_RE.search(p):
            return 'juniper_junos'
        if _IOSXE_PLATFORM_RE.search(p):
            return 'cisco_xe'
        if _IOS_PLATFORM_RE.search(p):
            return 'cisco_ios'

    hint = (dtype_hint or '').lower()
    if 'nxos' in hint or 'nexus' in hint:
        return 'cisco_nxos'
    if 'juniper' in hint or 'junos' in hint:
        return 'juniper_junos'
    if 'xe' in hint or hint in ('cisco_xe', 'iosxe'):
        return 'cisco_xe'
    if 'ios' in hint:
        return 'cisco_ios'
    if dtype_hint:
        return dtype_hint
    return 'unknown'


def os_family_display(device_type: Optional[str]) -> str:
    dt = (device_type or '').lower()
    for key, label in _OS_FAMILY_LABEL.items():
        if key in dt or key.replace('cisco_', '') in dt:
            return label
    if 'nxos' in dt or 'nexus' in dt:
        return 'NX-OS'
    if 'junos' in dt or 'juniper' in dt:
        return 'JunOS'
    if 'xe' in dt:
        return 'IOS-XE'
    if 'ios' in dt:
        return 'IOS'
    return 'Unknown'


def node_map_label(node: Dict[str, Any]) -> str:
    """Offline map label: hostname + OS family · model."""
    nid = node.get('id', '?')
    family = os_family_display(node.get('device_type'))
    model = (node.get('platform') or 'unknown').strip()
    if len(model) > 22:
        model = model[:22]
    return f"{nid}\n{family} · {model}"


def canonical_device_key(
    hostname: Optional[str],
    ip: Optional[str],
    serial: Optional[str] = None,
) -> str:
    """Prefer stable hostname over IP for graph id."""
    hn = _norm_host(hostname)
    if hn and not _IP_RE.match(hn):
        return hn
    vip = _valid_ip(ip)
    if vip:
        return vip
    if hn:
        return hn
    return 'unknown'


def _node_score(node: Dict[str, Any]) -> Tuple[int, int, int]:
    """Higher is better for merge winner."""
    scanned = 1 if node.get('is_scanned') else 0
    serial = 1 if node.get('serial') else 0
    depth = -int(node.get('depth', 99))
    return (scanned, serial, depth)


def merge_nodes(nodes: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Merge nodes that share IP or normalized hostname alias.
    Returns merged node list and alias_map {old_id_lower: canonical_id}.
    """
    if not nodes:
        return [], {}

    groups: Dict[str, List[Dict[str, Any]]] = {}

    def group_key(node: Dict[str, Any]) -> str:
        ip = _valid_ip(node.get('ip'))
        hn = _norm_host(node.get('id'))
        if ip:
            return f"ip:{ip}"
        if hn:
            return f"host:{hn}"
        return f"id:{node.get('id', '').lower()}"

    for node in nodes:
        gk = group_key(node)
        groups.setdefault(gk, []).append(dict(node))

    # Union groups that share IP or hostname across different keys
    parent: Dict[str, str] = {k: k for k in groups}

    def find(k: str) -> str:
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    def union(a: str, b: str):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    ip_to_key: Dict[str, str] = {}
    host_to_key: Dict[str, str] = {}
    serial_to_key: Dict[str, str] = {}
    for k, members in groups.items():
        n0 = members[0]
        ip = _valid_ip(n0.get('ip'))
        hn = _norm_host(n0.get('id'))
        if ip and ip in ip_to_key:
            union(k, ip_to_key[ip])
        elif ip:
            ip_to_key[ip] = k
        serial = (n0.get('serial') or '').strip()
        if serial:
            sk = serial.lower()
            if sk in serial_to_key:
                union(k, serial_to_key[sk])
            else:
                serial_to_key[sk] = k
        if hn and not _IP_RE.match(hn):
            if hn in host_to_key:
                other_key = host_to_key[hn]
                other_ip = _valid_ip(groups[other_key][0].get('ip') if other_key in groups else None)
                same_ip = ip and other_ip and ip == other_ip
                serials = {m.get('serial') for m in groups.get(k, []) + groups.get(other_key, [])}
                serials.discard(None)
                serials.discard('')
                same_serial = len(serials) == 1 and len(serials) > 0
                if same_ip or same_serial:
                    union(k, other_key)
            else:
                host_to_key[hn] = k

    merged_groups: Dict[str, List[Dict[str, Any]]] = {}
    for k, members in groups.items():
        rk = find(k)
        merged_groups.setdefault(rk, []).extend(members)

    final_nodes: List[Dict[str, Any]] = []
    alias_map: Dict[str, str] = {}
    seen_cids: Dict[str, str] = {}

    for _rk, members in merged_groups.items():
        winner = max(members, key=_node_score)
        # Canonical id: scanned hostname > normalized id > ip
        if winner.get('is_scanned'):
            raw_id = winner.get('id', '')
            cid = _norm_host(raw_id) if not _IP_RE.match(_norm_host(raw_id) or '') else raw_id
            if _IP_RE.match(str(cid)):
                cid = _norm_host(raw_id) or canonical_device_key(
                    raw_id, winner.get('ip'), winner.get('serial'),
                )
            elif not cid:
                cid = raw_id
        else:
            cid = canonical_device_key(winner.get('id'), winner.get('ip'))
            if cid == 'unknown':
                cid = _norm_host(winner.get('id')) or winner.get('id', 'unknown')

        cid_key = str(cid).lower()
        conflict = cid_key in seen_cids
        if conflict:
            suffix = _valid_ip(winner.get('ip')) or str(winner.get('serial') or '')[:12] or 'dup'
            cid = f"{cid}-{suffix}"
            for n in final_nodes:
                if str(n.get('id') or '').lower() == cid_key or _norm_host(n.get('id')) == _norm_host(cid_key):
                    n['identity_conflict'] = True
        seen_cids[str(cid).lower()] = cid

        merged = dict(winner)
        merged['id'] = cid
        merged['label'] = cid
        if conflict:
            merged['identity_conflict'] = True
        if winner.get('is_scanned') and winner.get('device_type'):
            merged['device_type'] = winner['device_type']
            merged['os_source'] = winner.get('os_source', 'scanned')
        _prio = {'scanned': 4, 'seed': 3, 'failed': 2, 'neighbor_only': 1}
        states = [m.get('scan_state') for m in members if m.get('scan_state')]
        if states:
            merged['scan_state'] = max(states, key=lambda s: _prio.get(s, 0))
        # Diagnostics-only: merge incomplete observations; never promote to edges
        incompletes: List[Dict[str, Any]] = []
        seen_inc: set = set()
        for m in members:
            for obs in (m.get('incomplete_observations') or []):
                if not isinstance(obs, dict):
                    continue
                key = (
                    str(obs.get('hostname') or ''),
                    str(obs.get('protocol') or ''),
                    str(obs.get('parse_source') or ''),
                    str(obs.get('parse_warning') or ''),
                    str(obs.get('local_port') or ''),
                    str(obs.get('remote_port') or ''),
                )
                if key in seen_inc:
                    continue
                seen_inc.add(key)
                incompletes.append(dict(obs))
        if incompletes:
            merged['incomplete_observations'] = incompletes
        elif 'incomplete_observations' in merged:
            merged.pop('incomplete_observations', None)
        final_nodes.append(merged)

        for m in members:
            for alias in (
                m.get('id', ''),
                _norm_host(m.get('id')),
                _valid_ip(m.get('ip')) or '',
            ):
                if alias:
                    alias_map[str(alias).lower()] = cid

    return final_nodes, alias_map


def rewire_edges(
    edges: List[Dict[str, Any]],
    alias_map: Dict[str, str],
) -> List[Dict[str, Any]]:
    """Remap edge endpoints to canonical ids; keep parallel links for Link Inventory."""

    def map_id(name: str) -> str:
        if not name:
            return name
        low = name.lower()
        if low in alias_map:
            return alias_map[low]
        short = _norm_host(name)
        if short in alias_map:
            return alias_map[short]
        return name

    out = []
    for e in edges:
        ne = dict(e)
        ne['from'] = map_id(e.get('from', ''))
        ne['to'] = map_id(e.get('to', ''))
        out.append(ne)
    return out


def validate_graph(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Pre-render validation report."""
    node_ids = {n.get('id') for n in nodes if n.get('id')}
    node_ids_lower = {str(i).lower() for i in node_ids}
    warnings: List[str] = []
    orphan_edges = 0
    for e in edges:
        f, t = e.get('from'), e.get('to')
        if str(f).lower() not in node_ids_lower or str(t).lower() not in node_ids_lower:
            orphan_edges += 1

    ip_counts: Dict[str, List[str]] = {}
    for n in nodes:
        ip = _valid_ip(n.get('ip'))
        if ip:
            ip_counts.setdefault(ip, []).append(n.get('id', ''))
    dup_ips = {ip: ids for ip, ids in ip_counts.items() if len(set(ids)) > 1}
    if dup_ips:
        warnings.append(f"duplicate IP keys: {len(dup_ips)}")

    host_counts: Dict[str, List[str]] = {}
    for n in nodes:
        h = _norm_host(n.get('id'))
        if h and not _valid_ip(h):
            host_counts.setdefault(h, []).append(str(n.get('id') or ''))
    dup_hosts = {h: ids for h, ids in host_counts.items() if len(set(ids)) > 1}
    if dup_hosts:
        warnings.append(f"duplicate hostnames: {len(dup_hosts)}")
        for n in nodes:
            hn = _norm_host(n.get('id'))
            if hn in dup_hosts:
                n['identity_conflict'] = True

    if any(n.get('identity_conflict') for n in nodes):
        warnings.append('identity_conflict')

    chassis_counts: Dict[str, List[str]] = {}
    for n in nodes:
        cid = str(n.get('chassis_id') or '').strip().lower()
        if cid and cid not in ('unknown', 'none', '-', 'n/a'):
            chassis_counts.setdefault(cid, []).append(str(n.get('id') or ''))
    dup_chassis = {c: ids for c, ids in chassis_counts.items() if len(set(ids)) > 1}
    if dup_chassis:
        warnings.append(f'duplicate chassis IDs: {len(dup_chassis)}')
        for n in nodes:
            cid = str(n.get('chassis_id') or '').strip().lower()
            if cid in dup_chassis:
                n['chassis_conflict'] = True
                n['identity_conflict'] = True
        warnings.append('chassis_conflict')

    failed = [
        n.get('id') for n in nodes
        if n.get('scan_state') in ('failed', 'auth_denied', 'timeout')
    ]
    partial = bool(failed) or orphan_edges > 0 or any(n.get('identity_conflict') for n in nodes)

    if orphan_edges:
        warnings.append(f"orphan edges: {orphan_edges}")

    return {
        'ok': orphan_edges == 0 and not dup_ips and not dup_hosts and not any(n.get('identity_conflict') for n in nodes),
        'node_count': len(nodes),
        'edge_count': len(edges),
        'orphan_edges': orphan_edges,
        'warnings': warnings,
        'partial': partial,
        'failed_hosts': failed,
        'duplicate_hostnames': list(dup_hosts.keys()),
        'duplicate_chassis': list(dup_chassis.keys()) if dup_chassis else [],
    }


def flag_remote_port_contradictions(edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Same pair + local port but disagreeing remote ports → Mismatch, do not pick a winner."""
    buckets: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {}
    for e in edges:
        f, t = e.get('from'), e.get('to')
        lp = str(e.get('f_port') or e.get('local_port') or '').strip().lower()
        if not f or not t or not lp:
            continue
        a, b = sorted([str(f).lower(), str(t).lower()])
        buckets.setdefault((a, b, lp), []).append(e)
    for members in buckets.values():
        remotes = {
            str(m.get('t_port') or m.get('remote_port') or '').strip().lower()
            for m in members
        }
        remotes.discard('')
        if len(remotes) < 2:
            continue
        note = 'contradictory remote ports: ' + ', '.join(sorted(remotes))
        for m in members:
            existing = m.get('contradictions') or []
            if note not in existing:
                existing.append(note)
            m['contradictions'] = existing
            m['confidence'] = 'Mismatch'
            m['trust_tier'] = 'mismatch'
            m['trust_score'] = min(int(m.get('trust_score') or 60), 40)
    return edges


def _normalize_edge_port(value: Optional[str]) -> str:
    """Normalize port labels. Never invent 'n/a'/'unknown' placeholders."""
    if not value:
        return ''
    s = str(value).strip()
    if s.lower() in ('unknown', 'null', 'none', 'n/a', 'n\\a', '-', ''):
        return ''
    from utils.cisco_iface import normalize_cisco_iface
    mapped = normalize_cisco_iface(s)
    return mapped if mapped else s


def _undirected_cable_key(edge: Dict[str, Any]) -> Tuple[str, str, str, str]:
    """Canonical identity for one physical/L2 cable (hosts + ports), ignoring protocol."""
    f = str(edge.get('from') or '').strip().lower()
    t = str(edge.get('to') or '').strip().lower()
    fp = _normalize_edge_port(edge.get('f_port') or edge.get('local_port'))
    tp = _normalize_edge_port(edge.get('t_port') or edge.get('remote_port'))
    left = (f, fp.lower())
    right = (t, tp.lower())
    if left <= right:
        return (f, fp.lower(), t, tp.lower())
    return (t, tp.lower(), f, fp.lower())


def make_observation_evidence(
    *,
    protocol: str = '',
    vendor: str = '',
    command: str = '',
    evidence_type: str = 'neighbor',
    collected_at: Optional[str] = None,
    local_port: str = '',
    remote_port: str = '',
    raw_fragment: str = '',
    port_role: str = '',
    not_physical: bool = False,
    parse_source: str = '',
    platform: str = '',
) -> Dict[str, Any]:
    """One supporting observation for a topology edge. Never invents timestamps."""
    proto = str(protocol or '').strip()
    cmd = command or (
        'show cdp neighbors detail' if proto.upper() == 'CDP'
        else 'show lldp neighbors' if proto.upper() == 'LLDP'
        else ''
    )
    item = {
        'protocol': proto,
        'vendor': vendor or '',
        'command': cmd,
        'evidence_type': evidence_type,
        'collected_at': collected_at or None,
        'local_port': local_port or '',
        'remote_port': remote_port or '',
        'parse_source': parse_source or '',
        'port_role': port_role or '',
        'not_physical': bool(not_physical),
        'platform': platform or '',
    }
    if raw_fragment:
        item['raw_fragment'] = str(raw_fragment)[:500]
    return item


def observation_from_edge(edge: Dict[str, Any]) -> Dict[str, Any]:
    """Build a synthetic evidence item from a legacy edge that lacks evidence[]."""
    proto = str(edge.get('protocol') or edge.get('discovery') or '').split('+')[0]
    return make_observation_evidence(
        protocol=proto,
        vendor=str(edge.get('vendor') or edge.get('platform') or ''),
        command=str(edge.get('command') or ''),
        evidence_type='neighbor',
        collected_at=edge.get('collected_at') or edge.get('observed_at'),
        local_port=str(edge.get('f_port') or edge.get('local_port') or ''),
        remote_port=str(edge.get('t_port') or edge.get('remote_port') or ''),
        raw_fragment=str(edge.get('raw_evidence') or edge.get('raw_fragment') or ''),
        port_role=str(edge.get('port_role') or ''),
        not_physical=bool(edge.get('not_physical')),
        parse_source=str(edge.get('parse_source') or ''),
        platform=str(edge.get('peer_platform') or edge.get('platform') or ''),
    )


def merge_protocol_duplicate_edges(edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge CDP+LLDP (or other protocol) views of the same cable; keep sources[] + evidence[].

    Distinct ports on the same pair remain parallel links.
    """
    groups: Dict[Tuple[str, str, str, str], List[Dict[str, Any]]] = {}
    order: List[Tuple[str, str, str, str]] = []
    for e in edges:
        key = _undirected_cable_key(e)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(e)

    out: List[Dict[str, Any]] = []
    for key in order:
        members = groups[key]
        winner = dict(members[0])
        sources: List[str] = []
        protos: List[str] = []
        evidence: List[Dict[str, Any]] = []
        for m in members:
            proto = str(m.get('protocol') or m.get('discovery') or '').strip()
            if proto:
                protos.append(proto)
            for src in m.get('sources') or ([proto.lower()] if proto else []):
                s = str(src).strip()
                if s and s.lower() not in {x.lower() for x in sources}:
                    sources.append(s.lower())
            if m.get('evidence') and isinstance(m.get('evidence'), list):
                for ev in m['evidence']:
                    if isinstance(ev, dict):
                        evidence.append(dict(ev))
            else:
                evidence.append(observation_from_edge(m))
        winner['sources'] = sources
        winner['evidence'] = evidence
        stamps = [str(ev.get('collected_at')).strip() for ev in evidence if ev.get('collected_at')]
        if stamps:
            winner['collected_at'] = min(stamps)
            winner['collected_at_latest'] = max(stamps)
            if min(stamps) != max(stamps):
                winner['mixed_source_timestamps'] = True
        uniq_proto = []
        for p in protos:
            up = p.upper() if p.lower() in ('cdp', 'lldp') else p
            if up not in uniq_proto:
                uniq_proto.append(up)
        if uniq_proto:
            winner['protocol'] = '+'.join(uniq_proto)
        winner['edge_type'] = 'lldp-neighbor' if 'lldp' in sources else (
            'cdp-neighbor' if 'cdp' in sources else winner.get('edge_type', 'inferred-path-edge')
        )
        if 'lldp' in sources and 'cdp' in sources:
            winner['edge_type'] = 'lldp-neighbor'
            winner['provenance_merged'] = True
        remotes = {
            str(m.get('t_port') or m.get('remote_port') or '').strip().lower()
            for m in members
        }
        remotes.discard('')
        remotes.discard('n/a')
        remotes.discard('unknown')
        if len(remotes) > 1:
            winner.setdefault('contradictions', []).append(
                'contradictory remote ports: ' + ', '.join(sorted(remotes))
            )
            winner['confidence'] = 'Mismatch'
            winner['trust_tier'] = 'mismatch'
            winner['trust_score'] = min(int(winner.get('trust_score') or 60), 40)
        directions = {(str(m.get('from')), str(m.get('to'))) for m in members}
        winner['bidirectional'] = any(m.get('bidirectional') for m in members) or len(directions) > 1
        winner['one_sided'] = not winner['bidirectional']
        scores = [int(m.get('trust_score') or 0) for m in members]
        if scores:
            if winner.get('trust_tier') == 'mismatch' or winner.get('contradictions'):
                winner['trust_score'] = min(min(scores), 40)
            else:
                winner['trust_score'] = max(scores)
        tiers = [m.get('trust_tier') for m in members if m.get('trust_tier')]
        if tiers:
            order_t = ['verified', 'high', 'medium', 'low', 'inferred', 'untrusted', 'mismatch']
            winner['trust_tier'] = min(tiers, key=lambda t: order_t.index(t) if t in order_t else 99)
        confs = [m.get('confidence') for m in members if m.get('confidence')]
        if winner.get('trust_tier') == 'mismatch' or winner.get('contradictions'):
            winner['confidence'] = 'Mismatch'
            winner['trust_tier'] = 'mismatch'
        elif confs:
            winner['confidence'] = confs[0] if winner['bidirectional'] else (
                'Medium' if 'Verified' not in confs else 'High'
            )
            if winner['bidirectional'] and any(c == 'Verified' for c in confs):
                winner['confidence'] = 'Verified'
            elif winner['bidirectional']:
                winner['confidence'] = max(confs, key=lambda c: {'Verified': 3, 'High': 2, 'Medium': 1, 'Low': 0, 'Mismatch': -1}.get(c, 0))
        # Evidence agreement summary (ports/protocols) — does not invent resolution
        winner['evidence_summary'] = {
            'count': len(evidence),
            'protocols': sorted({str(ev.get('protocol') or '').upper() for ev in evidence if ev.get('protocol')}),
            'timestamps_present': sum(1 for ev in evidence if ev.get('collected_at')),
            'timestamps_missing': sum(1 for ev in evidence if not ev.get('collected_at')),
            'logical_l3': any(ev.get('not_physical') for ev in evidence),
        }
        out.append(winner)
    return out


def normalize_discovery_edges(edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize port labels on edges for reports and link inventory."""
    out = []
    for e in edges:
        ne = dict(e)
        fp = _normalize_edge_port(ne.get('f_port'))
        tp = _normalize_edge_port(ne.get('t_port'))
        ne['f_port'] = fp
        ne['t_port'] = tp
        if not fp:
            # Incomplete local attachment — keep record but mark partial; do not invent ports
            ne['partial'] = True
            gaps = list(ne.get('evidence_gaps') or [])
            if 'local_port' not in gaps:
                gaps.append('local_port')
            ne['evidence_gaps'] = gaps
        if not tp:
            ne['partial'] = True
            gaps = list(ne.get('evidence_gaps') or [])
            if 'remote_port' not in gaps:
                gaps.append('remote_port')
            ne['evidence_gaps'] = gaps
        proto = ne.get('protocol') or ne.get('discovery') or 'LINK'
        rem_label = tp if tp else '(remote port unobserved)'
        loc_label = fp if fp else '(local port unobserved)'
        ne['label'] = f"{proto}\n{loc_label} ↔ {rem_label}"
        out.append(ne)
    return out


def annotate_lag_ae_edges(edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Classify Po/ae vs member from ifName. Does not claim LACP oper-state.

    T-L2-11: a degraded member must not delete a parallel bundle edge.
    IRB/L3 SVI ports are not LAG members — skip member/bundle heuristics for them.
    """
    from utils.juniper_iface import is_junos_irb_or_l3_svi

    for e in edges:
        fp = str(e.get('f_port') or e.get('local_port') or '')
        tp = str(e.get('t_port') or e.get('remote_port') or '')
        if is_junos_irb_or_l3_svi(fp) or is_junos_irb_or_l3_svi(tp) or e.get('not_physical'):
            e['bundle_kind'] = ''
            continue
        if _port_is_bundle(fp) or _port_is_bundle(tp):
            e['bundle_kind'] = 'bundle'
            e['lag_note'] = (
                'Bundle/AE ifName (naming heuristic). '
                'LACP member oper-state is not collected by CDP/LLDP crawl.'
            )
        elif fp or tp:
            e['bundle_kind'] = 'member'
        status = str(e.get('oper_status') or e.get('member_status') or '').lower()
        if status in ('down', 'notconnect', 'not connected', 'disabled', 'err-disabled'):
            e['degraded'] = True
            extra = 'Member reported down — keep any parallel bundle edge; do not treat as missing LAG.'
            e['lag_note'] = ((e.get('lag_note') or '') + ' ' + extra).strip()
    return edges


def annotate_logical_l3_edges(edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Mark Junos IRB / L3 SVI attachments as non-physical (T-L3-04).

    VLAN membership alone never creates edges here — only port-role honesty on
    existing neighbor-derived edges.
    """
    from utils.juniper_iface import classify_junos_port_role, is_junos_irb_or_l3_svi

    for e in edges:
        fp = str(e.get('f_port') or e.get('local_port') or '')
        tp = str(e.get('t_port') or e.get('remote_port') or '')
        roles = []
        if fp:
            roles.append(classify_junos_port_role(fp))
        if tp:
            roles.append(classify_junos_port_role(tp))
        if e.get('port_role'):
            roles.append(str(e.get('port_role')))
        logical = (
            e.get('not_physical')
            or is_junos_irb_or_l3_svi(fp)
            or is_junos_irb_or_l3_svi(tp)
            or any(r in ('irb_l3', 'vlan_l3') for r in roles)
        )
        if not logical:
            continue
        e['not_physical'] = True
        e['layer'] = e.get('layer') or 'l3-logical'
        e['edge_kind'] = e.get('edge_kind') or 'irb-adjacency'
        e['port_role'] = next((r for r in roles if r in ('irb_l3', 'vlan_l3')), 'irb_l3')
        e['bundle_kind'] = ''
        e['confidence'] = 'Low' if e.get('confidence') != 'Mismatch' else e['confidence']
        e['trust_tier'] = 'inferred' if e.get('trust_tier') != 'mismatch' else e['trust_tier']
        note = (
            'Junos IRB/L3 SVI evidence — routed interface, not a switch-switch cable. '
            'VLAN membership alone does not prove physical adjacency.'
        )
        existing = e.get('trust_note') or ''
        if note not in existing:
            e['trust_note'] = (existing + '; ' + note).strip('; ')
        e.setdefault('evidence_gaps', [])
        if 'physical_link' not in e['evidence_gaps']:
            e['evidence_gaps'].append('physical_link')
    return edges


def annotate_edge_freshness(
    edges: List[Dict[str, Any]],
    *,
    now=None,
    stale_hours: float = 24.0,
) -> List[Dict[str, Any]]:
    """Stamp freshness from per-evidence timestamps when present.

    Edge freshness: current | stale | mixed | unknown
    Never invents timestamps. Mixed freshness is visible but does not alone
    downgrade confidence (port contradictions still use mismatch rules).
    """
    from datetime import datetime, timezone

    def _parse_ts(raw):
        if not raw:
            return None
        s = str(raw).strip()
        for fmt in (
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
        ):
            try:
                if fmt.endswith('%z') and s.endswith('Z'):
                    s2 = s[:-1] + '+0000'
                    return datetime.strptime(s2, '%Y-%m-%dT%H:%M:%S%z')
                return datetime.strptime(s.replace('Z', ''), fmt.replace('%z', '').replace('Z', ''))
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(s.replace('Z', '+00:00'))
        except ValueError:
            return None

    def _freshness_for_ts(ts, ref):
        if ts is None:
            return 'unknown'
        age_h = (ref - ts.replace(tzinfo=None)).total_seconds() / 3600.0
        if age_h > stale_hours:
            return 'stale'
        return 'current'

    ref = now or datetime.now(timezone.utc).replace(tzinfo=None)
    graph_stamps = []
    for e in edges:
        evidence = e.get('evidence')
        if not evidence or not isinstance(evidence, list):
            # Backward compatible: single edge stamp
            if not e.get('evidence'):
                e['evidence'] = [observation_from_edge(e)]
            evidence = e['evidence']

        per = []
        for ev in evidence:
            if not isinstance(ev, dict):
                continue
            ts = _parse_ts(ev.get('collected_at'))
            fr = _freshness_for_ts(ts, ref)
            ev['freshness'] = fr
            if ts is not None:
                ev['observation_age_hours'] = round(
                    (ref - ts.replace(tzinfo=None)).total_seconds() / 3600.0, 2
                )
            per.append(fr)

        kinds = set(per) if per else {'unknown'}
        if not per or kinds == {'unknown'}:
            e['freshness'] = 'unknown'
            e['freshness_conflict'] = False
            e['freshness_note'] = 'no observation timestamp on evidence'
            # Fall back to edge-level stamp if present
            edge_fr = _freshness_for_ts(_parse_ts(e.get('collected_at') or e.get('observed_at')), ref)
            if edge_fr != 'unknown':
                e['freshness'] = edge_fr
                e['stale'] = edge_fr == 'stale'
                e['freshness_note'] = (
                    f'observation older than {stale_hours:g}h'
                    if edge_fr == 'stale' else 'within freshness window'
                )
        elif kinds == {'current'}:
            e['freshness'] = 'current'
            e['stale'] = False
            e['freshness_conflict'] = False
            e['freshness_note'] = 'all evidence within freshness window'
        elif kinds == {'stale'}:
            e['freshness'] = 'stale'
            e['stale'] = True
            e['freshness_conflict'] = False
            e['freshness_note'] = f'all evidence older than {stale_hours:g}h'
        else:
            # current+stale, current+unknown, stale+unknown → mixed
            e['freshness'] = 'mixed'
            e['stale'] = 'stale' in kinds
            e['freshness_conflict'] = True
            e['freshness_note'] = (
                'supporting observations differ in freshness — see evidence[]'
            )
            e.setdefault('contradictions', [])
            note = 'mixed-freshness evidence timestamps'
            if note not in e['contradictions']:
                e['contradictions'].append(note)

        # Aggregate stamps for map consumers (still not invented)
        stamps = [str(ev.get('collected_at')) for ev in evidence if isinstance(ev, dict) and ev.get('collected_at')]
        if stamps:
            e['collected_at'] = e.get('collected_at') or min(stamps)
            e['collected_at_latest'] = max(stamps)
        graph_stamps.append(e.get('freshness'))

    kinds_g = {s for s in graph_stamps if s}
    if 'current' in kinds_g and 'stale' in kinds_g or 'mixed' in kinds_g:
        for e in edges:
            if e.get('freshness') in ('current', 'stale', 'mixed'):
                e['freshness_graph'] = 'mixed'
    return edges


def _port_is_bundle(port: str) -> bool:
    s = (port or '').strip().lower().replace(' ', '')
    s = s.replace('port-channel', 'po')
    return bool(re.match(r'^(po|ae)\d', s))


def canonicalize_discovery_graph(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """Full pipeline: merge nodes, rewire edges, validate, trust-score adjacency."""
    merged, alias_map = merge_nodes(nodes)
    rewired = rewire_edges(edges, alias_map)
    # IRB/L3 before trust so Verified-cable scoring never applies to logical ports
    rewired = annotate_logical_l3_edges(rewired)
    trust_error = ''
    try:
        from utils.topology_trust import apply_discovery_edge_trust
        apply_discovery_edge_trust(rewired)
    except Exception as exc:
        trust_error = str(exc)
    flag_remote_port_contradictions(rewired)
    rewired = merge_protocol_duplicate_edges(rewired)
    rewired = annotate_logical_l3_edges(rewired)  # re-assert after protocol merge
    rewired = annotate_lag_ae_edges(rewired)
    rewired = normalize_discovery_edges(rewired)
    rewired = annotate_edge_freshness(rewired)
    report = validate_graph(merged, rewired)
    if trust_error:
        report.setdefault('warnings', []).append(f'trust scoring skipped: {trust_error}')
        report['ok'] = False
    return merged, rewired, report


def canonicalize_topology_edge_list(
    edges: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Light canonicalization for Swiss Tools topology_mapper edges:
    normalize endpoint hostnames via safe_node_name-style shortening.
    """
    from modules.network_base import safe_node_name

    out = []
    for e in edges:
        ne = dict(e)
        for side in ('from', 'to'):
            raw = e.get(side, '')
            cleaned = safe_node_name(raw) or _norm_host(raw) or raw
            ne[side] = cleaned
        out.append(ne)
    return out
