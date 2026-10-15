"""
Discovery topology HTML — Discovery Command Center (v7.0.4).
"""
from datetime import datetime

from utils.discovery_graph import node_map_label, os_family_display
from utils.discovery_map_shell import render_discovery_command_center_page
from utils.evidence_inspector import topology_relation_key
from utils.topo_map_shell import link_rows_from_edges


def assign_discovery_positions(nodes, edges):
    by_depth = {}
    for n in nodes:
        d = int(n.get('depth', 0))
        by_depth.setdefault(d, []).append(n['id'])
    positions = {}
    for depth, ids in by_depth.items():
        n = len(ids)
        y = depth * 180
        for i, nid in enumerate(sorted(ids)):
            x = (i - (n - 1) / 2.0) * 220 if n > 1 else 0
            positions[nid] = {'x': x, 'y': y, 'fixed': True}
    return positions


def _scan_state_for_node(n):
    if n.get('scan_state'):
        return n['scan_state']
    if n.get('discovered_via') == 'Seed':
        return 'seed'
    if n.get('is_scanned'):
        return 'scanned'
    return 'neighbor_only'


def build_vis_payload(nodes, edges):
    positions = assign_discovery_positions(nodes, edges)
    scanned_ids = {n['id'] for n in nodes if _scan_state_for_node(n) == 'scanned'}
    nodes_json = []
    for n in nodes:
        nid = n['id']
        st = _scan_state_for_node(n)
        scanned = st in ('scanned', 'seed')
        if st == 'failed':
            bg, border, dash = '#fef3c7', '#d97706', [8, 4]
        elif scanned:
            bg, border, dash = '#3b82f6', '#1e3a8a', False
        else:
            bg, border, dash = '#94a3b8', '#64748b', [6, 4]
        pos = positions.get(nid, {'x': 0, 'y': 0, 'fixed': True})
        family = os_family_display(n.get('device_type'))
        depth = int(n.get('depth', 0))
        nodes_json.append({
            'id': nid,
            'label': f"H{depth}: {node_map_label(n)}",
            'ip': n.get('ip', ''),
            'platform': n.get('platform', ''),
            'device_type': n.get('device_type', ''),
            'os_family': family,
            'os_source': n.get('os_source', ''),
            'depth': depth,
            'scan_state': st,
            'identity_conflict': bool(n.get('identity_conflict')),
            'x': pos['x'], 'y': pos['y'], 'fixed': True,
            'color': {
                'background': bg,
                'border': border,
                'highlight': {'background': '#60a5fa', 'border': '#2563eb'},
            },
            'borderWidth': 3 if scanned else 2,
            'shape': 'box',
            'font': {'color': '#ffffff' if scanned else '#1e293b', 'size': 12},
        })
        if dash:
            nodes_json[-1]['shapeProperties'] = {'borderDashes': dash}
    edges_json = []
    for i, e in enumerate(edges):
        proto = (e.get('protocol') or '').upper()
        if 'STP' in proto or e.get('link_type') == 'stp-blocked':
            edge_color = '#f97316'
            dashed = True
        else:
            edge_color = '#6366f1' if 'CDP' in proto else '#14b8a6' if 'LLDP' in proto else '#64748b'
            f_scanned = e['from'] in scanned_ids
            t_scanned = e['to'] in scanned_ids
            dashed = not (f_scanned and t_scanned)
        title_bits = [f"{proto}: {e.get('f_port')} → {e.get('t_port')}"]
        if e.get('one_sided') or e.get('spoof_risk'):
            title_bits.append('ONE-SIDED — spoofable, not a verified cable')
        if e.get('confidence'):
            title_bits.append(f"confidence={e.get('confidence')}")
        if e.get('freshness'):
            title_bits.append(f"freshness={e.get('freshness')}")
        if e.get('freshness_conflict') or e.get('freshness') == 'mixed':
            title_bits.append('MIXED FRESHNESS — see evidence[]')
        if e.get('contradictions'):
            title_bits.append('CONFLICT')
        if e.get('not_physical') or e.get('edge_kind') == 'irb-adjacency':
            title_bits.append('L3/IRB context — not a cable')
        if e.get('lacp_collected') and e.get('lacp_oper'):
            title_bits.append(f"LACP {e.get('lacp_oper')} (device CLI)")
        elif e.get('bundle_kind') == 'bundle':
            title_bits.append('BUNDLE/AE naming heuristic')
        if e.get('degraded'):
            title_bits.append('DEGRADED member')
        if e.get('layer') == 'overlay' or proto == 'EVPN':
            edge_color = '#a855f7'
            dashed = True
            title_bits.append('OVERLAY NVE/EVPN — not a cable')
        evidence = e.get('evidence') if isinstance(e.get('evidence'), list) else []
        edges_json.append({
            'id': f'e{i}',
            'from': e['from'], 'to': e['to'],
            'label': f"{e.get('f_port', '?')} ↔ {e.get('t_port', '?')}",
            'title': ' · '.join(title_bits),
            'f_port': e.get('f_port', ''), 't_port': e.get('t_port', ''),
            'protocol': proto,
            'one_sided': bool(e.get('one_sided')),
            'spoof_risk': bool(e.get('spoof_risk') or e.get('one_sided')),
            'confidence': e.get('confidence', ''),
            'trust_tier': e.get('trust_tier') or '',
            'trust_note': e.get('trust_note') or '',
            'not_physical': bool(e.get('not_physical') or proto == 'EVPN'),
            'layer': e.get('layer') or ('overlay' if proto == 'EVPN' else 'l2'),
            'edge_kind': e.get('edge_kind') or '',
            'sources': e.get('sources') or [],
            'contradictions': e.get('contradictions') or [],
            'evidence': evidence,
            'evidence_summary': e.get('evidence_summary') or {},
            'collected_at': e.get('collected_at') or '',
            'collected_at_latest': e.get('collected_at_latest') or '',
            'freshness': e.get('freshness') or 'unknown',
            'freshness_conflict': bool(e.get('freshness_conflict')),
            'freshness_note': e.get('freshness_note') or '',

            'bundle_kind': e.get('bundle_kind') or '',
            'lag_note': e.get('lag_note') or '',
            'lacp_collected': bool(e.get('lacp_collected')),
            'lacp_oper': e.get('lacp_oper') or '',
            'degraded': bool(e.get('degraded')),
            'relation_key': topology_relation_key({
                'from': e.get('from'), 'to': e.get('to'),
                'f_port': e.get('f_port'), 't_port': e.get('t_port'),
                'edge_kind': e.get('edge_kind'), 'layer': e.get('layer'),
                'not_physical': e.get('not_physical') or proto == 'EVPN',
            }),
            'color': {'color': edge_color, 'highlight': edge_color},
            'width': 2 if not dashed else 1,
            'dashes': [6, 4] if dashed else False,
            'font': {'size': 9, 'align': 'middle'},
            'smooth': {'type': 'cubicBezier', 'roundness': 0.2},
        })
    link_rows = link_rows_from_edges(edges, nodes)
    node_depth = {n['id']: n.get('depth', 0) for n in nodes}
    for r in link_rows:
        r['hop'] = max(node_depth.get(r['from'], 0), node_depth.get(r['to'], 0))
    return nodes_json, edges_json, link_rows


def generate_discovery_html(filepath, nodes, edges, extra_meta=None):
    nodes_json, edges_json, link_rows = build_vis_payload(nodes, edges)
    from modules.plugins.network_discovery import _operator_incomplete_observation

    devices_out = []
    incomplete_total = 0
    for n in nodes:
        incompletes = [
            _operator_incomplete_observation(obs)
            for obs in (n.get('incomplete_observations') or [])
            if isinstance(obs, dict)
        ]
        incomplete_total += len(incompletes)
        devices_out.append({
            'id': n.get('id'),
            'hostname': n.get('id'),
            'ip': n.get('ip', ''),
            'depth': n.get('depth', 0),
            'scan_state': _scan_state_for_node(n),
            'device_type': n.get('device_type', ''),
            'platform': n.get('platform', ''),
            'neighbor_evidence': n.get('neighbor_evidence', ''),
            'identity_conflict': bool(n.get('identity_conflict')),
            'incomplete_observation_count': len(incompletes),
            'incomplete_observations': incompletes,
        })
    extra = extra_meta or {}
    status = extra.get('collection_status') or (
        'partial' if extra.get('partial') or extra.get('cancelled') else 'complete'
    )
    subtitle = f'{len(nodes)} devices · {len(edges)} links'
    if status != 'complete':
        subtitle += f' · {str(status).upper()} collection — not complete truth'
    empty_ev = {
        n.get('neighbor_evidence') for n in nodes
        if n.get('neighbor_evidence') in ('none_collected', 'protocol_disabled')
    }
    if empty_ev:
        subtitle += ' · empty CDP/LLDP is lack of evidence, not isolation'
    if incomplete_total:
        subtitle += (
            f' · {incomplete_total} incomplete observation(s) — not map links'
        )
    generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    edge_times = [
        str(e.get('collected_at')).strip()
        for e in edges
        if e.get('collected_at')
    ]
    if extra.get('collected_at'):
        collected_at = str(extra.get('collected_at')).strip()
        freshness_basis = 'crawl_observation'
    elif edge_times:
        collected_at = min(edge_times)
        freshness_basis = 'edge_observation'
    else:
        collected_at = None
        freshness_basis = 'unknown'
    freshness_states = {str(e.get('freshness') or 'unknown') for e in edges} if edges else {'unknown'}
    if not edges:
        map_freshness = 'unknown'
    elif freshness_states == {'current'}:
        map_freshness = 'current'
    elif freshness_states == {'stale'}:
        map_freshness = 'stale'
    elif 'current' in freshness_states and 'stale' in freshness_states:
        map_freshness = 'mixed'
    elif freshness_states == {'unknown'} or not edge_times:
        map_freshness = 'unknown'
    else:
        map_freshness = 'mixed'
    meta = {
        'devices': devices_out,
        'links': edges,
        'generated_at': generated_at,
        'collected_at': collected_at,
        'freshness_basis': freshness_basis,
        'freshness': map_freshness,
        'subtitle': subtitle,
        'partial': bool(extra.get('partial') or extra.get('cancelled')),
        'cancelled': bool(extra.get('cancelled')),
        'collection_status': status,
        'failed_hosts': extra.get('failed_hosts') or [],
        'overlay_collected': bool(extra.get('overlay_collected')),
        'overlay_note': extra.get('overlay_note') or '',
        'incomplete_observation_count': incomplete_total,
        'job_id': extra.get('job_id'),
        'scan_profile': extra.get('scan_profile'),
        'max_depth': extra.get('max_depth'),
    }
    # Phase 6 Wave 2 — embed authoritative Program Status (same builder as Wave 1 API)
    from utils.discovery_program_status import program_status_from_map_meta
    meta['program_status'] = program_status_from_map_meta(meta)
    overlay_src = extra.get('utilization_overlay')
    if overlay_src is None:
        from utils.utilization_overlay.model import resolve_replay_overlay_source
        overlay_src = resolve_replay_overlay_source(html_file=filepath)
    try:
        from utils.utilization_overlay.discovery_host import (
            bind_overlay_to_discovery,
            discovery_embed_payload,
        )
        bound = bind_overlay_to_discovery(nodes_json, edges_json, overlay_src)
        util_payload = discovery_embed_payload(bound)
    except Exception:
        util_payload = {
            'ok': False,
            'available': False,
            'error': 'utilization overlay unavailable',
            'host': 'discovery',
            'live_controls': False,
            'bindings': {},
            'banner': (
                'Utilization paints existing L2 links only. It is not topology. '
                'Gray dashed = no sample — not down. Overlay never creates cables. '
                'Discovery is a viewer. EVPN, overlay, and incomplete observations '
                'are not cables. Release gate is unchanged.'
            ),
        }
    render_discovery_command_center_page(
        filepath,
        'Discovery Command Center',
        nodes_json,
        edges_json,
        link_rows,
        meta,
        accent='#7c3aed',
        utilization_payload=util_payload,
    )
