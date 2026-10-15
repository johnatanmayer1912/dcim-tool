"""
Topology trust validation — bidirectional CDP/LLDP, vPC member cross-check, LACP witness.

AI_CONTEXT: Scores discovery edges after collection. Labels are honesty, not crypto proof.
AI_FLOW: apply_discovery_edge_trust(edges) → confidence/trust_tier/spoof_risk
AI_DEPENDS_ON: caller canonicalize_discovery_graph
AI_IMPACTS: map Evidence column, trust pills, one-sided spoof-risk
AI_MAP_NOTE: Bidirectional High is still protocol-spoofable. Never upgrade overlay here.
AI_CRAWL_NOTE: Incomplete neighbors → Low. One-sided → Medium + spoof_risk.
AI_SECURITY_NOTE: Telemetry is untrusted. Do not execute device output.
AI_BREADCRUMB: next — utils/discovery_graph.py, utils/topo_map_shell.py
AI_TODO_NEXT: Do not treat High as verified physical unless LACP/vPC witness exists.

Used after multi-device collection to score physical vs logical link confidence.
Aligned with NX-OS vPC best-practice: verify adjacency, port-channel membership, and
domain consistency before presenting maps to network engineers.
"""
from __future__ import annotations

import re
from typing import Callable

TRUST_TIERS = (
    ('verified', 95),
    ('high', 80),
    ('medium', 60),
    ('low', 40),
    ('inferred', 25),
    ('untrusted', 10),
)

_TIER_ORDER = {name: score for name, score in TRUST_TIERS}


def trust_tier_from_score(score: int) -> str:
    for name, threshold in TRUST_TIERS:
        if score >= threshold:
            return name
    return 'untrusted'


def _norm_po(name: str) -> str:
    n = (name or '').strip()
    n = re.sub(r'(?i)port-channel', 'Po', n)
    m = re.match(r'(?i)^(po)(\d+.*)$', n)
    if m:
        return 'Po' + m.group(2)
    return n


def directed_key(
    from_host: str,
    from_port: str,
    to_host: str,
    to_port: str,
    norm_fn: Callable[[str], str],
) -> tuple:
    return (from_host, norm_fn(from_port or ''), to_host, norm_fn(to_port or ''))


def build_directed_link_index(
    edges: list,
    safe_name_fn: Callable[[str], str],
    norm_fn: Callable[[str], str],
) -> set[tuple]:
    idx: set[tuple] = set()
    for e in edges:
        f = safe_name_fn(e.get('from', ''))
        t = safe_name_fn(e.get('to', ''))
        if not f or not t:
            continue
        idx.add(directed_key(f, e.get('f_port', ''), t, e.get('t_port', ''), norm_fn))
    return idx


def is_bidirectional(
    from_host: str,
    from_port: str,
    to_host: str,
    to_port: str,
    directed_index: set[tuple],
    norm_fn: Callable[[str], str],
) -> bool:
    forward = directed_key(from_host, from_port, to_host, to_port, norm_fn)
    reverse = directed_key(to_host, to_port, from_host, from_port, norm_fn)
    return forward in directed_index and reverse in directed_index


def build_enhanced_cdp_validation_map(
    host: str,
    edges: list,
    directed_index: set[tuple],
    norm_fn: Callable[[str], str],
    safe_name_fn: Callable[[str], str],
) -> dict:
    """Local port → neighbor with bidirectional witness flag."""
    out: dict = {}
    host_safe = safe_name_fn(host)
    for e in edges:
        if safe_name_fn(e.get('from', '')) != host_safe:
            continue
        local = norm_fn(e.get('f_port', ''))
        if not local:
            continue
        remote = safe_name_fn(e.get('to', ''))
        remote_port = norm_fn(e.get('t_port', ''))
        bidi = is_bidirectional(
            host_safe, e.get('f_port', ''), remote, e.get('t_port', ''),
            directed_index, norm_fn,
        )
        existing = out.get(local)
        entry = {
            'peer': remote,
            'peer_port': remote_port,
            'validated': bidi,
            'bidirectional': bidi,
            'discovery': e.get('discovery', 'cdp'),
            'trust_score': 90 if bidi else 55,
            'trust_tier': 'high' if bidi else 'medium',
        }
        if not existing or (bidi and not existing.get('bidirectional')):
            out[local] = entry
    return out


def _lacp_witness(meta: dict, po_name: str, norm_fn: Callable[[str], str]) -> bool:
    po = _norm_po(po_name)
    lacp = meta.get('lacp_neighbors') or {}
    for key, entries in lacp.items():
        if _norm_po(str(key)) != po:
            continue
        if entries:
            return True
    pc = meta.get('port_channel_detail') or {}
    pd = pc.get(po) or pc.get(po_name) or {}
    members = pd.get('members') or []
    return len(members) >= 1 and (pd.get('protocol', '').upper() == 'LACP' or bool(members))


def cross_check_vpc_members(
    host: str,
    meta: dict,
    cdp_map: dict,
    domain_members: set[str],
    norm_fn: Callable[[str], str],
) -> tuple[list[dict], list[str]]:
    """
    Validate each vPC/port-channel member against CDP and LACP witnesses.
    Returns interface trust chains and alert strings.
    """
    chains: list[dict] = []
    alerts: list[str] = []
    vs = meta.get('vpc_structured') or {}
    if not isinstance(vs, dict):
        return chains, alerts

    bundles = meta.get('bundles') or {}
    peer_link_po = _norm_po(vs.get('peer_link_po', ''))
    peer_domain_id = str(meta.get('vpc_domain_id') or vs.get('domain_id') or '').strip()

    def _chain_for_intf(intf: str, po: str, vpc_id: str, entry_type: str) -> dict:
        intf_n = norm_fn(intf)
        po_n = _norm_po(po)
        cdp = cdp_map.get(intf_n) or cdp_map.get(intf) or {}
        peer = cdp.get('peer', '')
        bidi = bool(cdp.get('bidirectional'))
        lacp_ok = _lacp_witness(meta, po_n, norm_fn)
        score = 25
        if bidi:
            score += 45
        elif cdp.get('peer'):
            score += 25
        if lacp_ok:
            score += 15
        if entry_type == 'peer-link' and peer in domain_members:
            score += 10
        if entry_type == 'vpc' and po_n:
            score += 5
        score = min(score, 100)
        tier = trust_tier_from_score(score)
        if entry_type == 'peer-link' and peer and peer not in domain_members and domain_members:
            alerts.append(f"{host} {intf_n}: peer-link CDP neighbor {peer} not in vPC domain members")
        if not cdp and not lacp_ok:
            alerts.append(f"{host} {intf_n}: no CDP/LACP witness for {entry_type} member")
        elif not bidi and cdp.get('peer'):
            alerts.append(f"{host} {intf_n}: unidirectional CDP to {peer} (no reverse entry)")
        return {
            'interface': intf_n,
            'port_channel': po_n,
            'vpc_id': vpc_id,
            'entry_type': entry_type,
            'cdp_peer': peer,
            'cdp_peer_port': cdp.get('peer_port', ''),
            'bidirectional': bidi,
            'lacp_witness': lacp_ok,
            'trust_score': score,
            'trust_tier': tier,
            'chain': ' → '.join(filter(None, [
                intf_n,
                po_n if po_n else None,
                f"vPC {vpc_id}" if vpc_id and vpc_id != 'peer-link' else None,
                f"CDP→{peer}" if peer else None,
            ])),
        }

    if peer_link_po:
        pc_detail = meta.get('port_channel_detail') or {}
        pl_data = pc_detail.get(peer_link_po) or {}
        for mem in pl_data.get('members', []):
            intf = mem.get('intf', mem) if isinstance(mem, dict) else mem
            chains.append(_chain_for_intf(str(intf), peer_link_po, 'peer-link', 'peer-link'))

    for row in vs.get('vpc_table', []):
        if not isinstance(row, dict):
            continue
        po = row.get('po', '')
        vpc_id = str(row.get('vpc_id', ''))
        pc_detail = meta.get('port_channel_detail') or {}
        pd = pc_detail.get(po) or {}
        for mem in pd.get('members', []):
            intf = mem.get('intf', mem) if isinstance(mem, dict) else mem
            chains.append(_chain_for_intf(str(intf), po, vpc_id, 'vpc'))

    for intf, po in bundles.items():
        if any(c.get('interface') == norm_fn(intf) for c in chains):
            continue
        vd = (meta.get('vpc_details') or {}).get(_norm_po(str(po))) or {}
        if vd.get('type') == 'vpc':
            chains.append(_chain_for_intf(str(intf), str(po), str(vd.get('vpc_id', '')), 'vpc'))

    return chains, alerts


def score_edge_trust(
    edge: dict,
    directed_index: set[tuple],
    node_metadata: dict,
    norm_fn: Callable[[str], str],
    safe_name_fn: Callable[[str], str],
) -> dict:
    """Compute trust_score, trust_tier, confidence label for one adjacency edge."""
    f = safe_name_fn(edge.get('from', ''))
    t = safe_name_fn(edge.get('to', ''))
    f_port = edge.get('f_port', '')
    t_port = edge.get('t_port', '')

    f_meta = node_metadata.get(f, {})
    t_meta = node_metadata.get(t, {})
    f_scanned = bool(f_meta)
    t_scanned = bool(t_meta)

    bidi = is_bidirectional(f, f_port, t, t_port, directed_index, norm_fn)
    f_int = f_meta.get('interfaces', {}).get(norm_fn(f_port), f_meta.get('interfaces', {}).get(f_port, {}))
    t_int = t_meta.get('interfaces', {}).get(norm_fn(t_port), t_meta.get('interfaces', {}).get(t_port, {}))
    f_stat = (f_int or {}).get('status', 'unknown')
    t_stat = (t_int or {}).get('status', 'unknown')

    score = 30
    if bidi:
        score += 40
    elif f_scanned or t_scanned:
        score += 15
    if f_scanned and t_scanned:
        score += 10
    if f_stat == 'up' and t_stat == 'up':
        score += 10
    elif f_stat == 'up' and t_stat in ('down', 'err-disabled'):
        score -= 25
    elif t_stat == 'up' and f_stat in ('down', 'err-disabled'):
        score -= 25

    f_bundle = (f_meta.get('bundles') or {}).get(norm_fn(f_port)) or (f_meta.get('bundles') or {}).get(f_port)
    if f_bundle and _lacp_witness(f_meta, f_bundle, norm_fn):
        score += 10

    did_f = str(f_meta.get('vpc_domain_id', '')).strip()
    did_t = str(t_meta.get('vpc_domain_id', '')).strip()
    if did_f and did_t and did_f == did_t:
        score += 5

    score = max(5, min(score, 100))
    tier = trust_tier_from_score(score)

    if score >= 90 and bidi and f_scanned and t_scanned and f_stat == 'up' and t_stat == 'up':
        confidence = 'Verified'
    elif bidi and f_stat == 'up' and t_stat == 'up':
        confidence = 'High'
    elif bidi:
        confidence = 'High' if score >= 75 else 'Medium'
    elif f_scanned and t_scanned:
        confidence = 'Medium'
    elif edge.get('type') in ('vpc-peer-link',) and edge.get('confidence') == 'Inferred':
        confidence = 'Inferred'
        score = min(score, 35)
        tier = 'inferred'
    else:
        confidence = 'Low'

    if f_stat == 'up' and t_stat in ('down', 'err-disabled'):
        confidence = 'Mismatch'
        score = min(score, 40)
        tier = 'low'
    elif t_stat == 'up' and f_stat in ('down', 'err-disabled'):
        confidence = 'Mismatch'
        score = min(score, 40)
        tier = 'low'

    return {
        'trust_score': score,
        'trust_tier': tier,
        'confidence': confidence,
        'bidirectional': bidi,
        'f_scanned': f_scanned,
        't_scanned': t_scanned,
    }


def validate_vpc_domain_completeness(
    vpc_domains: dict,
    node_metadata: dict,
) -> dict[str, dict]:
    """Flag domains with unscanned or inferred peers."""
    out: dict[str, dict] = {}
    for did, members in vpc_domains.items():
        scanned = [m for m in members if m in node_metadata and _node_has_vpc_data(node_metadata[m])]
        unscanned = [m for m in members if m not in node_metadata or not _node_has_vpc_data(node_metadata.get(m, {}))]
        out[did] = {
            'members': members,
            'scanned_members': scanned,
            'unscanned_members': unscanned,
            'fully_scanned': len(unscanned) == 0 and len(scanned) >= 2,
            'single_peer_only': len(scanned) == 1,
            'trust_score': 100 if len(unscanned) == 0 and len(scanned) >= 2 else (
                70 if len(scanned) >= 1 else 30
            ),
        }
    return out


def _node_has_vpc_data(meta: dict) -> bool:
    if not meta:
        return False
    vs = meta.get('vpc_structured') or {}
    if isinstance(vs, dict) and (vs.get('domain_id') or vs.get('vpc_table')):
        return True
    vd = meta.get('vpc_details') or {}
    for key, det in vd.items():
        if str(key).startswith('_'):
            continue
        if isinstance(det, dict) and det.get('type') in ('vpc', 'peer-link'):
            return True
    return bool(meta.get('vpcs'))


def infer_dual_homed_by_mac(node_metadata: dict, norm_fn: Callable[[str], str]) -> list[dict]:
    """Find downstream hosts reachable on same MAC from two vPC peers (weak witness)."""
    hints: list[dict] = []
    mac_to_links: dict[str, list] = {}
    for host, meta in node_metadata.items():
        did = str(meta.get('vpc_domain_id', '')).strip()
        if not did:
            continue
        for intf, data in (meta.get('interface_macs') or {}).items():
            macs = data if isinstance(data, list) else (data.get('macs', []) if isinstance(data, dict) else [])
            for mac in macs:
                mac_l = str(mac).lower().replace('.', '').replace(':', '')
                if len(mac_l) < 12:
                    continue
                mac_to_links.setdefault(mac_l, []).append({
                    'host': host, 'interface': norm_fn(intf), 'domain_id': did,
                })
    for mac, links in mac_to_links.items():
        hosts = {l['host'] for l in links}
        domains = {l['domain_id'] for l in links}
        if len(hosts) >= 2 and len(domains) == 1:
            hints.append({
                'mac': mac,
                'domain_id': next(iter(domains)),
                'links': links,
                'trust_tier': 'inferred',
                'trust_score': 35,
                'note': 'Same MAC seen on multiple vPC peer interfaces — possible dual-homed host',
            })
    return hints


def apply_topology_trust(
    edges: list,
    node_metadata: dict,
    norm_fn: Callable[[str], str],
    safe_name_fn: Callable[[str], str],
    log=None,
) -> dict:
    """
    Post-collection trust pass: bidirectional CDP, vPC cross-check, edge scoring.
    Mutates node_metadata (cdp_validation_map, interface_trust_chains, trust_alerts).
    """
    def _log(msg):
        if log:
            log(msg)

    directed_index = build_directed_link_index(edges, safe_name_fn, norm_fn)
    all_alerts: list[str] = []
    domain_members_by_host: dict[str, set[str]] = {}

    for host, meta in node_metadata.items():
        did = str(meta.get('vpc_domain_id', '')).strip()
        if did:
            peers = {h for h, m in node_metadata.items()
                     if str(m.get('vpc_domain_id', '')).strip() == did}
            domain_members_by_host[host] = peers

    for host, meta in node_metadata.items():
        cdp_map = build_enhanced_cdp_validation_map(
            host, edges, directed_index, norm_fn, safe_name_fn,
        )
        meta['cdp_validation_map'] = cdp_map
        members = domain_members_by_host.get(host, set())
        chains, alerts = cross_check_vpc_members(host, meta, cdp_map, members, norm_fn)
        meta['interface_trust_chains'] = chains
        meta['trust_alerts'] = alerts
        all_alerts.extend(alerts)

    for e in edges:
        if e.get('not_physical') or str(e.get('layer') or '').lower() == 'overlay':
            e.setdefault('discovery', 'nve')
            e.setdefault('confidence', 'Overlay')
            e.setdefault('trust_tier', 'overlay')
            e.setdefault('trust_note', 'NVE/EVPN peer from device CLI — not a cable')
            continue
        trust = score_edge_trust(e, directed_index, node_metadata, norm_fn, safe_name_fn)
        e.update(trust)
        # Do not invent CDP when protocol/discovery is absent
        if not e.get('discovery') and not e.get('protocol'):
            e['discovery'] = 'unattributed'
            e['partial'] = True
            e.setdefault('evidence_gaps', [])
            if 'protocol' not in e['evidence_gaps']:
                e['evidence_gaps'].append('protocol')
        else:
            e['discovery'] = e.get('discovery') or str(e.get('protocol') or '').lower()

    mac_hints = infer_dual_homed_by_mac(node_metadata, norm_fn)
    bidi_count = sum(1 for e in edges if e.get('bidirectional'))
    verified_count = sum(1 for e in edges if e.get('confidence') == 'Verified')

    summary = {
        'edge_count': len(edges),
        'bidirectional_edges': bidi_count,
        'verified_edges': verified_count,
        'trust_alerts': all_alerts[:50],
        'mac_dual_homed_hints': mac_hints[:20],
    }
    _log(f"[TRUST] {bidi_count}/{len(edges)} bidirectional adjacencies; {verified_count} verified")
    if all_alerts:
        _log(f"[TRUST] {len(all_alerts)} vPC/CDP cross-check alert(s)")
    return summary


def apply_discovery_edge_trust(
    edges: list,
    norm_fn: Callable[[str], str] | None = None,
    safe_name_fn: Callable[[str], str] | None = None,
    log=None,
) -> dict:
    """
    Lightweight trust pass for Discovery BFS edges (no SSH node_metadata).
    Marks bidirectional CDP/LLDP and assigns confidence/trust_tier on each edge.
    """
    norm_fn = norm_fn or (lambda x: x)
    safe_name_fn = safe_name_fn or (lambda x: (x or '').strip())

    for e in edges:
        if not e.get('f_port') and e.get('local_port'):
            e['f_port'] = e['local_port']
        if not e.get('t_port') and e.get('remote_port'):
            e['t_port'] = e['remote_port']

    directed_index = build_directed_link_index(edges, safe_name_fn, norm_fn)
    verified = 0
    bidi_count = 0
    for e in edges:
        if e.get('not_physical') or str(e.get('layer') or '').lower() in (
            'overlay', 'l3-logical', 'logical',
        ):
            layer = str(e.get('layer') or '').lower()
            if layer in ('l3-logical', 'logical') or e.get('edge_kind') == 'irb-adjacency':
                e.setdefault('discovery', e.get('discovery') or str(e.get('protocol') or 'lldp').lower())
                e['confidence'] = 'Low'
                e['trust_tier'] = 'inferred'
                e['one_sided'] = False
                e['spoof_risk'] = False
                e['bidirectional'] = False
                e['not_physical'] = True
                e['trust_note'] = (
                    e.get('trust_note')
                    or 'Junos IRB/L3 SVI — not a physical cable (T-L3-04)'
                )
            else:
                e.setdefault('discovery', 'nve')
                e.setdefault('confidence', 'Overlay')
                e.setdefault('trust_tier', 'overlay')
                e['one_sided'] = False
                e['spoof_risk'] = False
                e['bidirectional'] = False
                e['trust_note'] = 'NVE/EVPN peer from device CLI — not a cable'
            continue
        f = safe_name_fn(e.get('from', ''))
        t = safe_name_fn(e.get('to', ''))
        bidi = is_bidirectional(
            f, e.get('f_port') or e.get('local_port', ''),
            t, e.get('t_port') or e.get('remote_port', ''),
            directed_index, norm_fn,
        )
        # Align score with TRUST_TIERS so confidence labels are not higher than the tier.
        # Bidirectional CDP/LLDP (no SSH interface/LACP witness) is High, not Verified.
        if not e.get('from') or not e.get('to'):
            score, conf = 25, 'Low'
        elif bidi:
            score, conf = 80, 'High'
        else:
            score, conf = 60, 'Medium'
        tier = trust_tier_from_score(score)
        proto = (e.get('protocol') or e.get('discovery') or '').strip()
        if not proto:
            proto = 'unattributed'
            gaps = list(e.get('evidence_gaps') or [])
            if 'protocol' not in gaps:
                gaps.append('protocol')
            e['evidence_gaps'] = gaps
            # Protocol gap is explainable, not a fake CDP attribution
            e.setdefault('trust_note', 'protocol unattributed — not assumed CDP')
        proto_l = str(proto).lower()
        sources = list(e.get('sources') or [])
        if proto_l and proto_l not in ('unattributed',) and proto_l not in {str(s).lower() for s in sources}:
            sources.append(proto_l)
        e['bidirectional'] = bidi
        e['one_sided'] = not bidi
        e['spoof_risk'] = not bidi
        e['trust_score'] = score
        e['trust_tier'] = tier
        e['confidence'] = conf
        e['sources'] = sources
        e['discovery'] = proto_l
        port_missing = not (e.get('f_port') or e.get('local_port')) or not (
            e.get('t_port') or e.get('remote_port')
        )
        if e.get('partial') or port_missing:
            e['partial'] = True
            e['confidence'] = 'Low' if e.get('confidence') != 'Mismatch' else e['confidence']
            e['trust_score'] = min(int(e.get('trust_score') or 60), 40)
            e['trust_tier'] = 'low' if e.get('trust_tier') != 'mismatch' else e['trust_tier']
        if bidi:
            bidi_count += 1
        if not bidi:
            e['trust_note'] = 'one-sided CDP/LLDP — spoofable, not a verified cable'
        elif not e.get('trust_note'):
            e['trust_note'] = 'bidirectional CDP/LLDP (protocol still spoofable)'
        if e.get('partial'):
            e['trust_note'] = ((e.get('trust_note') or '') + '; partial port evidence').strip('; ')
        if conf == 'High' and bidi and not e.get('partial'):
            verified += 1
    if log:
        log(f"[TRUST] Discovery: {bidi_count}/{len(edges)} bidirectional; {verified} high-confidence")
    return {
        'edge_count': len(edges),
        'bidirectional_edges': bidi_count,
        'high_confidence_edges': verified,
    }
