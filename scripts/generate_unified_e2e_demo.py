#!/usr/bin/env python3
"""Generate offline 8-vendor demo artifacts (fixture-only, not live)."""
from __future__ import annotations

import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

LAB = os.path.join(ROOT, 'tests', 'fixtures', 'demo_lab', 'unified_e2e_lab.json')
DEFAULT_OUT = os.path.join(
    ROOT, 'docs', 'review_folder', '2026.08.23', 'QA',
    'enterprise_validation_rendering_and_ship_readiness',
)


def load_lab():
    return json.load(open(LAB, encoding='utf-8'))


def _std_nodes(lab):
    nodes = []
    for i, n in enumerate(lab['nodes']):
        role = n.get('role') or 'access'
        color = {
            'core': '#c0392b',
            'distribution': '#e67e22',
            'access': '#2980b9',
        }.get(role, '#607d8b')
        nodes.append({
            'id': n['id'],
            'label': n['id'],
            'role': role,
            'level': int(n.get('depth') or 0),
            'shape': 'box',
            'device_type': n.get('device_type'),
            'ip': n.get('ip'),
            'platform': n.get('platform'),
            'color': {'background': color, 'border': '#333'},
            'font': {'color': '#fff'},
        })
    return nodes


def _std_edges(lab, include_non_cable=False):
    edges = []
    src = list(lab['l2_edges'])
    if include_non_cable:
        src += list(lab.get('non_cable_edges') or [])
    for i, e in enumerate(src):
        ed = {
            'from': e['from'], 'to': e['to'],
            'f_port': e.get('f_port'), 't_port': e.get('t_port'),
            'type': e.get('type') or 'standard',
            'trust_tier': e.get('trust_tier') or '',
            'confidence': e.get('confidence') or '',
            'protocol': e.get('protocol') or '',
            'one_sided': bool(e.get('one_sided')),
            'spoof_risk': bool(e.get('spoof_risk')),
            'layer': e.get('layer') or 'l2',
            'not_physical': bool(e.get('not_physical')),
        }
        edges.append({
            'id': f'e{i}',
            'from': e['from'], 'to': e['to'],
            'f_port': e.get('f_port'), 't_port': e.get('t_port'),
            'label': '',
            'map_label': f"{e.get('f_port')} ↔ {e.get('t_port')}",
            'type': e.get('type') or 'standard',
            'trust_tier': e.get('trust_tier') or '',
            'confidence': e.get('confidence') or '',
            'protocol': e.get('protocol') or '',
            'one_sided': bool(e.get('one_sided')),
            'spoof_risk': bool(e.get('spoof_risk')),
            'layer': e.get('layer') or 'l2',
            'not_physical': bool(e.get('not_physical')),
            'edge_kind': e.get('edge_kind') or '',
            'link_type': e.get('link_type') or '',
            'edge_data': ed,
            'color': '#a855f7' if e.get('not_physical') else '#607d8b',
            'width': 2,
        })
    return edges


def _overlay_doc(lab):
    return {
        'schema': 'nst.utilization_overlay.v1',
        'mode': 'replay',
        'evidence_class': 'fixture',
        'topology_job_id': lab['id'],
        'generated_at': '2026-08-22T21:00:00+00:00',
        'stale_after_seconds': None,
        'degraded': False,
        'collector': {'kind': 'none'},
        'paints': [{
            'cable_key': 'nx-core-01|eth1/1|nx-core-02|eth1/1|l2',
            'paint_state': 'hot',
            'in_bps': 9400000000,
            'out_bps': 8100000000,
            'in_pct': 94,
            'out_pct': 81,
            'pct': 94,
            'if_speed_bps': 10000000000,
            'join': {'status': 'mapped', 'sides': ['a', 'b']},
            'provenance': {
                'mode': 'replay',
                'evidence_class': 'fixture',
                'job_id': lab['id'],
                'commands': [],
            },
            'freshness': {
                'sampled_at': '2026-08-22T20:52:00+00:00',
                'age_seconds': 480,
                'stale': False,
            },
        }],
        'unmapped': [
            {
                'device_id': 'NX-CORE-01',
                'if_name_raw': 'mgmt0',
                'if_name_normalized': 'mgmt0',
                'reason': 'mgmt_or_l3_svi',
                'command': None,
            },
            {
                'device_id': 'NX-CORE-01',
                'if_name_raw': 'Eth1/99',
                'if_name_normalized': 'Eth1/99',
                'reason': 'no_matching_edge',
                'command': None,
            },
            {
                'device_id': 'NX-CORE-01',
                'if_name_raw': 'Eth1/10',
                'if_name_normalized': 'Eth1/10',
                'reason': 'bundle_member_not_on_graph',
                'command': None,
            },
        ],
        'summary': {
            'l2_edge_count': lab['expected']['l2_cable_count'],
            'painted_count': 1,
            'unmapped_count': 3,
            'partial_count': 0,
            'stale_count': 0,
        },
    }


def generate(out_root=None):
    from utils.report_formatter import generate_topology_html
    from utils.discovery_map_formatter import generate_discovery_html, build_vis_payload
    from utils.link_issues import build_link_issues
    from utils.utilization_overlay.join import (
        bind_overlay_to_standard_l2,
        is_paint_eligible_l2_edge,
        topology_fingerprint,
    )
    from utils.utilization_overlay.discovery_host import bind_overlay_to_discovery

    out_root = out_root or DEFAULT_OUT
    lab = load_lab()
    vis_path = os.path.join(ROOT, 'modules', 'web', 'vis-network.min.js')
    vis_js = open(vis_path, encoding='utf-8').read() if os.path.isfile(vis_path) else '/* vis stub */'

    demo = os.path.join(out_root, 'demo_lab')
    gen = os.path.join(out_root, 'generated_outputs')
    os.makedirs(os.path.join(demo, 'inventory'), exist_ok=True)
    os.makedirs(os.path.join(demo, 'fixtures'), exist_ok=True)
    os.makedirs(os.path.join(demo, 'expected_outputs'), exist_ok=True)
    for sub in ('maps', 'topology', 'enrichment', 'overlays', 'diagnostics', 'exports'):
        os.makedirs(os.path.join(gen, sub), exist_ok=True)

    shutil.copy(LAB, os.path.join(demo, 'fixtures', 'unified_e2e_lab.json'))
    inv_lines = ['# Offline demo inventory — not a live lab', '# Format: IP,device_type,group', '']
    for n in lab['nodes']:
        inv_lines.append(f"{n['ip']},{n['device_type']},{n['role']}")
    open(os.path.join(demo, 'inventory', 'demo_inventory.txt'), 'w', encoding='utf-8').write(
        '\n'.join(inv_lines) + '\n'
    )
    topo_md = [
        '# Offline 8-vendor demo topology',
        '',
        lab['honesty'],
        '',
        '## Devices (8)',
        '- 3× Cisco Nexus (`NX-CORE-01`, `NX-CORE-02`, `NX-AGG-01`)',
        '- 2× Cisco IOS (`IOS-DIST-01`, `IOS-ACC-01`)',
        '- 1× Cisco IOS-XE (`IOS-XE-DIST-02`)',
        '- 2× Juniper Junos (`JN-ACC-01`, `JN-ACC-02`)',
        '',
        '## L2 cables (7) — CDP/LLDP only',
    ]
    for e in lab['l2_edges']:
        extra = ' ONE-SIDED' if e.get('one_sided') else ''
        topo_md.append(
            f"- {e['from']} {e['f_port']} ↔ {e['to']} {e['t_port']} ({e['protocol']}){extra}"
        )
    topo_md += [
        '',
        '## Not cables',
        '- EVPN NVE peer NX-CORE-01 nve1 ↔ NX-CORE-02 nve1',
        '- STP-blocked IOS-DIST-01 Gi1/0/2 ↔ IOS-ACC-01 Gi1/0/2',
        '- Incomplete CDP on IOS-ACC-01 Gi1/0/24 (diagnostics only)',
        '',
        'Do not treat this as live-vendor proof.',
    ]
    open(os.path.join(demo, 'topology_description.md'), 'w', encoding='utf-8').write(
        '\n'.join(topo_md) + '\n'
    )

    for name in (
        'cisco_ios_show_interfaces.txt',
        'cisco_nxos_show_interface.txt',
        'juniper_show_interfaces_statistics.txt',
    ):
        src = os.path.join(ROOT, 'tests', 'fixtures', 'utilization', 'cli', name)
        if os.path.isfile(src):
            shutil.copy(src, os.path.join(gen, 'enrichment', name))

    nodes = _std_nodes(lab)
    l2_edges = _std_edges(lab, include_non_cable=False)
    mixed_edges = _std_edges(lab, include_non_cable=True)
    overlay = _overlay_doc(lab)

    overlay_path = os.path.join(gen, 'overlays', 'utilization_overlay_replay.json')
    json.dump(overlay, open(overlay_path, 'w', encoding='utf-8'), indent=2)

    std_path = os.path.join(gen, 'maps', 'standard_l2_overlay_replay.html')
    generate_topology_html(
        std_path, len(nodes), len(l2_edges),
        json.dumps(nodes), json.dumps(l2_edges), vis_js,
        map_mode='all',
        utilization_overlay=overlay,
    )
    std_off = os.path.join(gen, 'maps', 'standard_l2_overlay_off.html')
    generate_topology_html(
        std_off, len(nodes), len(l2_edges),
        json.dumps(nodes), json.dumps(l2_edges), vis_js,
        map_mode='all',
        utilization_overlay=None,
    )

    disc_nodes = []
    for n in lab['nodes']:
        row = dict(n)
        disc_nodes.append(row)
    disc_edges = list(lab['l2_edges']) + list(lab.get('non_cable_edges') or [])
    disc_path = os.path.join(gen, 'maps', 'discovery_command_center.html')
    generate_discovery_html(
        disc_path, disc_nodes, disc_edges,
        extra_meta={'utilization_overlay': overlay, 'scan_profile': 'offline_demo'},
    )

    issues = build_link_issues(disc_edges)
    json.dump(issues, open(os.path.join(gen, 'diagnostics', 'link_issues.json'), 'w', encoding='utf-8'), indent=2)

    bound = bind_overlay_to_standard_l2(nodes, l2_edges, overlay)
    vis_n, vis_e, _ = build_vis_payload(disc_nodes, disc_edges)
    disc_bound = bind_overlay_to_discovery(vis_n, vis_e, overlay)
    eligible = [e for e in mixed_edges if is_paint_eligible_l2_edge(e)]
    actual = {
        'device_count': len(lab['nodes']),
        'l2_edge_count': len(lab['l2_edges']),
        'non_cable_count': len(lab.get('non_cable_edges') or []),
        'standard_l2_vis_edges': len(l2_edges),
        'discovery_vis_edges': len(vis_e),
        'paint_eligible_mixed': len(eligible),
        'overlay_ok': bound.ok,
        'overlay_painted': bound.painted_count,
        'overlay_bindings': sorted(bound.bindings.keys()),
        'discovery_host': disc_bound.ok,
        'discovery_bindings': sorted(disc_bound.bindings.keys()),
        'discovery_evpn_unpainted': 'e7' not in disc_bound.bindings,
        'fingerprint_unchanged': topology_fingerprint(l2_edges) == topology_fingerprint(list(l2_edges)),
        'trust_tiers': [e.get('trust_tier') for e in l2_edges],
        'link_issue_count': len(issues),
        'honesty': lab['honesty'],
    }
    json.dump(lab['expected'], open(os.path.join(demo, 'expected_outputs', 'expected.json'), 'w', encoding='utf-8'), indent=2)
    json.dump(actual, open(os.path.join(gen, 'exports', 'actual_counts.json'), 'w', encoding='utf-8'), indent=2)

    topo_export = {
        'nodes': [{'id': n['id'], 'device_type': n['device_type'], 'ip': n['ip']} for n in lab['nodes']],
        'l2_edges': lab['l2_edges'],
        'non_cable_edges': lab.get('non_cable_edges'),
    }
    json.dump(topo_export, open(os.path.join(gen, 'topology', 'graph.json'), 'w', encoding='utf-8'), indent=2)

    return {
        'standard_l2': std_path,
        'discovery': disc_path,
        'overlay': overlay_path,
        'actual': actual,
        'bound_ok': bound.ok,
        'disc_ok': disc_bound.ok,
    }


if __name__ == '__main__':
    dest = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT
    info = generate(dest)
    print(json.dumps({k: info[k] for k in ('standard_l2', 'discovery', 'overlay', 'bound_ok', 'disc_ok', 'actual')}, indent=2))
