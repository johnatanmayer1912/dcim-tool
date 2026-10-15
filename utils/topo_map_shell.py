# ============================================================================
# AI_NAVIGATION_BREADCRUMBS - utils/topo_map_shell.py
# ============================================================================
# PURPOSE:
#   Unified Multi-Layer Offline Topology Map Shell (Vis.js, zero external CDN).
#   Provides multi-layer switching: Physical, Layer 2, Layer 3, Overlay, and STP.
#   Includes blast-radius neighborhood highlighting and link-evidence inspection.
#
# ARCHITECTURAL ROLE:
#   Shared visual template foundation for Discovery, L3 Routing, and STP plugins.
#
# KEY FUNCTIONS:
#   - layer_switch_html(default_layer): HTML markup for layer buttons (Physical/L2/L3/Overlay/STP)
#   - nstSetLayer(layer): Client-side layer toggle adjusting edge/node visibility
#   - script_safe_json(obj): XSS-safe JSON string serialization
#
# CONNECTIONS:
#   - Called by: utils/l3_map_shell.py, utils/discovery_map_shell.py, utils/report_formatter.py
#   - Supports: modules/plugins/stp_topology_visualizer.py, modules/plugins/network_discovery.py
# ============================================================================
import json
import os
import sys
from datetime import datetime

from utils.evidence_inspector import topology_relation_key

# Honesty constants — tests import these; do not drift from JS.
NST_STALE_HOURS = 24
NST_BLAST_SEMANTICS = 'neighborhood-not-path'
OFFLINE_VIS_MISSING_SCRIPT = (
    '<script type="text/javascript">'
    'window.NST_VIS_MISSING=true;'
    'document.addEventListener("DOMContentLoaded",function(){'
    'var p=document.createElement("p");'
    'p.setAttribute("role","alert");'
    'p.textContent="Offline map engine missing (vis-network.min.js). '
    'This build will not fetch it from the internet.";'
    'if(document.body){document.body.insertBefore(p,document.body.firstChild);}'
    '});'
    '</script>'
)


def script_safe_json(obj):
    """JSON for embedding in <script> — neutralize </script> breakout."""
    return (
        json.dumps(obj)
        .replace('<', '\\u003c')
        .replace('>', '\\u003e')
        .replace('&', '\\u0026')
    )


def read_version_label():
    try:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, 'VERSION'), encoding='utf-8') as vf:
            return f"v{vf.read().strip()}"
    except Exception:
        return 'v7.0.0'


def load_app_logo_data_uri() -> str:
    """Embed NST favicon for fully offline map HTML."""
    try:
        import base64
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        png = os.path.join(root, 'favicon_program.png')
        if os.path.exists(png):
            with open(png, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('ascii')
            return f"data:image/png;base64,{b64}"
    except Exception:
        pass
    return ''


def load_vis_script():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        vis_js_path = os.path.join(sys._MEIPASS, 'modules', 'web', 'vis-network.min.js')
    else:
        vis_js_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'modules', 'web', 'vis-network.min.js',
        )
    if os.path.exists(vis_js_path):
        try:
            with open(vis_js_path, 'r', encoding='utf-8') as f:
                return f'<script type="text/javascript">{f.read()}</script>'
        except Exception:
            pass
    # Offline-first: never fetch vis.js from the internet.
    return OFFLINE_VIS_MISSING_SCRIPT


def link_rows_from_edges(edges, nodes=None):
    """Build connection index rows (WHO/HOW/WHAT) from edge dicts or edge_data payloads."""
    node_meta = {}
    if nodes:
        for n in nodes:
            if isinstance(n, dict):
                node_meta[n.get('id', '')] = n
    rows = []
    for e in edges:
        if not isinstance(e, dict):
            continue
        ed = e.get('edge_data') if e.get('edge_data') else e
        f_port = e.get('local_port') or ed.get('f_port') or e.get('f_port') or ''
        t_port = e.get('remote_port') or ed.get('t_port') or e.get('t_port') or ''
        f_int = ed.get('f_int_data') or e.get('f_int_data') or {}
        t_int = ed.get('t_int_data') or e.get('t_int_data') or {}
        peer = ed.get('peer_info') or e.get('peer_info') or {}
        link_type = ed.get('type') or e.get('type') or ''
        protocol = e.get('protocol') or ''
        if not protocol:
            if link_type in ('vpc', 'vpc-peer-link', 'port-channel'):
                protocol = 'CDP/LLDP'
            elif link_type == 'asymmetric':
                protocol = 'CDP (unidir)'
            else:
                protocol = 'CDP/LLDP'
        vlan = (
            e.get('vlan') or e.get('native_vlan')
            or f_int.get('vlan') or t_int.get('vlan') or ''
        )
        if vlan and str(vlan).lower() in ('trunk', '1'):
            pass
        rows.append({
            'from': ed.get('from') or e.get('from', ''),
            'to': ed.get('to') or e.get('to', ''),
            'local_port': f_port,
            'remote_port': t_port,
            'protocol': protocol,
            'vlan': vlan,
            'speed': f_int.get('speed') or e.get('speed') or '',
            'status': f_int.get('status') or e.get('status') or '',
            'description': (f_int.get('desc') or '').strip() if f_int.get('desc') not in ('-', '') else '',
            'confidence': ed.get('confidence') or e.get('confidence') or '',
            'trust_tier': ed.get('trust_tier') or e.get('trust_tier') or '',
            'trust_score': ed.get('trust_score') if ed.get('trust_score') is not None else e.get('trust_score', ''),
            'bidirectional': ed.get('bidirectional') if 'bidirectional' in ed else e.get('bidirectional', False),
            'one_sided': ed.get('one_sided') if 'one_sided' in ed else e.get('one_sided', False),
            'spoof_risk': ed.get('spoof_risk') if 'spoof_risk' in ed else e.get('spoof_risk', False),
            'trust_note': ed.get('trust_note') or e.get('trust_note') or '',
            'contradictions': ed.get('contradictions') or e.get('contradictions') or [],
            'sources': ed.get('sources') or e.get('sources') or [],
            'edge_type': ed.get('edge_type') or e.get('edge_type') or '',
            'link_type': link_type,
            'remote_platform': peer.get('platform') or e.get('peer_platform') or '',
            'local_role': (node_meta.get(ed.get('from') or e.get('from', ''), {}).get('role') or ''),
            'remote_role': (node_meta.get(ed.get('to') or e.get('to', ''), {}).get('role') or ''),
            'hop': e.get('hop', ''),
            'vpc_domain': ed.get('vpc_domain_id') or e.get('vpc_domain_id', ''),
            'bundle_kind': ed.get('bundle_kind') or e.get('bundle_kind') or '',
            'lag_note': ed.get('lag_note') or e.get('lag_note') or '',
            'degraded': bool(ed.get('degraded') or e.get('degraded')),
            # Evidence inspector parity (same fields as map edges; never invented)
            'layer': ed.get('layer') or e.get('layer') or '',
            'edge_kind': ed.get('edge_kind') or e.get('edge_kind') or '',
            'not_physical': bool(ed.get('not_physical') or e.get('not_physical')),
            'evidence': (
                list(ed['evidence']) if isinstance(ed.get('evidence'), list)
                else (list(e['evidence']) if isinstance(e.get('evidence'), list) else [])
            ),
            'evidence_summary': (
                dict(ed['evidence_summary']) if isinstance(ed.get('evidence_summary'), dict)
                else (
                    dict(e['evidence_summary'])
                    if isinstance(e.get('evidence_summary'), dict) else {}
                )
            ),
            'collected_at': ed.get('collected_at') or e.get('collected_at') or '',
            'collected_at_latest': (
                ed.get('collected_at_latest') or e.get('collected_at_latest') or ''
            ),
            'freshness': ed.get('freshness') or e.get('freshness') or '',
            'freshness_conflict': bool(
                ed.get('freshness_conflict') or e.get('freshness_conflict')
            ),
            'freshness_note': ed.get('freshness_note') or e.get('freshness_note') or '',
            'lacp_collected': bool(ed.get('lacp_collected') or e.get('lacp_collected')),
            'lacp_oper': ed.get('lacp_oper') or e.get('lacp_oper') or '',
        })
        # Stable map↔table sync key (not array index)
        rk = topology_relation_key(rows[-1])
        if rk:
            rows[-1]['relation_key'] = rk
    return rows


def default_grid_positions(nodes, edges):
    """Simple grid layout by node index."""
    ids = [n['id'] if isinstance(n, dict) else n for n in nodes]
    positions = {}
    n = len(ids)
    for i, nid in enumerate(sorted(ids)):
        cols = max(1, int(n ** 0.5) + 1)
        row, col = divmod(i, cols)
        positions[nid] = {'x': (col - cols / 2) * 200, 'y': row * 140, 'fixed': True}
    return positions


def topo_search_helpers_js():
    """Shared Vis.js search: primary match + 1-hop neighbors highlighted; others dimmed."""
    return """
    function topoCollectFocus(q) {
        var primary = {}, hop = {};
        if (!q) return { primary: primary, hop: hop };
        nodes.forEach(function(n) {
            if (topoNodeHaystack(n).indexOf(q) >= 0) primary[n.id] = true;
        });
        edges.forEach(function(e) {
            if (topoEdgeHaystack(e).indexOf(q) >= 0) {
                primary[e.from] = true;
                primary[e.to] = true;
            }
        });
        Object.keys(primary).forEach(function(pid) {
            edges.forEach(function(e) {
                if (e.from === pid && !primary[e.to]) hop[e.to] = true;
                if (e.to === pid && !primary[e.from]) hop[e.from] = true;
            });
        });
        return { primary: primary, hop: hop };
    }
    function topoApplyNodeEdgeFocus(q, allN, allE) {
        var focus = topoCollectFocus(q);
        var nu = [], eu = [];
        allN.forEach(function(id) {
            if (!q) nu.push({ id: id, hidden: false, opacity: 1, borderWidth: 1 });
            else if (focus.primary[id]) nu.push({ id: id, hidden: false, opacity: 1, borderWidth: 4 });
            else if (focus.hop[id]) nu.push({ id: id, hidden: false, opacity: 0.75, borderWidth: 2 });
            else nu.push({ id: id, hidden: false, opacity: 0.15, borderWidth: 1 });
        });
        allE.forEach(function(eid) {
            var e = edges.get(eid);
            if (!e) return;
            if (!q) eu.push({ id: eid, hidden: false, opacity: 1 });
            else {
                var pf = focus.primary[e.from] || focus.primary[e.to];
                var nh = focus.hop[e.from] || focus.hop[e.to];
                eu.push({ id: eid, hidden: false, opacity: pf ? 1 : (nh ? 0.55 : 0.08) });
            }
        });
        nodes.update(nu);
        edges.update(eu);
        if (q) {
            var first = Object.keys(focus.primary)[0];
            var net = window.topoNetwork || window.network || window.discNetwork;
            if (net && first) {
                try { net.selectNodes([first]); net.focus(first, { scale: 1.15, animation: false }); } catch (ex) {}
            }
        }
        return focus;
    }
"""


def link_inventory_light_theme_css():
    """Readable link inventory inside light Command Center shells (VPC, Discovery)."""
    return """
    /* Light command centers: body color is dark — override dark inventory pane */
    body.vpc-command-center #topo-link-inventory,
    body.discovery-command-center #topo-link-inventory,
    body.vpc-command-center #vpc-panel-links,
    body.discovery-command-center #disc-link-inventory-host {
      background: #fff !important;
      color: #1e293b !important;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 12px 16px;
    }
    body.vpc-command-center #vpc-panel-links {
      margin: 0 0 16px 0;
      min-height: 360px;
    }
    body.vpc-command-center .topo-inv-table,
    body.discovery-command-center .topo-inv-table {
      background: #fff !important;
    }
    body.vpc-command-center .topo-inv-table th,
    body.discovery-command-center .topo-inv-table th {
      background: #1e293b !important;
      color: #f8fafc !important;
      position: sticky;
      top: 0;
      z-index: 2;
    }
    body.vpc-command-center .topo-inv-table td,
    body.discovery-command-center .topo-inv-table td {
      color: #1e293b !important;
      border-bottom: 1px solid #e2e8f0 !important;
      background: #fff;
    }
    body.vpc-command-center .topo-inv-table tr:nth-child(even) td,
    body.discovery-command-center .topo-inv-table tr:nth-child(even) td {
      background: #f8fafc;
    }
    body.vpc-command-center .topo-inv-table tr:hover td,
    body.discovery-command-center .topo-inv-table tr:hover td {
      background: #ede9fe !important;
    }
    .topo-inv-table tr.nst-link-row-selected td,
    body.discovery-command-center .topo-inv-table tr.nst-link-row-selected td,
    body.vpc-command-center .topo-inv-table tr.nst-link-row-selected td {
      background: #ddd6fe !important;
      box-shadow: inset 3px 0 0 #6d28d9;
    }
    .topo-inv-table tr.nst-link-row-selected td {
      background: #312e81;
    }
    body.discovery-command-center .topo-inv-table tr.nst-link-row-selected td,
    body.vpc-command-center .topo-inv-table tr.nst-link-row-selected td {
      background: #ddd6fe !important;
    }
    body.vpc-command-center .topo-view-tabs button,
    body.discovery-command-center .topo-view-tabs button {
      background: #fff !important;
      color: #334155 !important;
      border-color: #cbd5e1 !important;
    }
    body.vpc-command-center .topo-view-tabs button.active,
    body.discovery-command-center .topo-view-tabs button.active {
      background: #4f46e5 !important;
      color: #fff !important;
      border-color: #4338ca !important;
    }
    body.vpc-command-center .topo-search-bar,
    body.discovery-command-center .topo-search-bar {
      background: #f8fafc !important;
      border: 1px solid #e2e8f0 !important;
      border-radius: 8px;
      margin-bottom: 10px;
      padding: 8px 12px;
    }
    body.vpc-command-center .topo-search-bar input,
    body.discovery-command-center .topo-search-bar input {
      background: #fff !important;
      color: #0f172a !important;
      border-color: #cbd5e1 !important;
    }
    body.vpc-command-center .topo-search-bar span,
    body.discovery-command-center .topo-search-bar span {
      color: #475569 !important;
    }
    .topo-inv-hint {
      font-size: 12px;
      color: #475569;
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      border-radius: 8px;
      padding: 8px 12px;
      margin-bottom: 10px;
      line-height: 1.45;
    }
    .topo-port {
      font-family: Consolas, "Courier New", monospace;
      font-size: 11px;
      font-weight: 600;
      color: #0369a1;
      background: #e0f2fe;
      padding: 2px 6px;
      border-radius: 4px;
      white-space: nowrap;
    }
    .topo-trust-pill {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 10px;
      font-size: 10px;
      font-weight: 700;
      color: #fff;
      white-space: nowrap;
    }
    .topo-trust-verified { background: #059669; }
    .topo-trust-medium { background: #d97706; }
    .topo-trust-inferred { background: #64748b; }
    .topo-trust-mismatch { background: #dc2626; }
    .topo-link-type {
      font-size: 10px;
      font-weight: 600;
      color: #6366f1;
      text-transform: uppercase;
    }
    """


def shell_css(accent='#0a84ff'):
    from utils.map_shell_theme import enterprise_map_css
    return enterprise_map_css() + f"""
    .topo-view-tabs {{ display:flex; gap:8px; margin:12px 16px; flex-wrap:wrap; align-items:center; }}
    .topo-view-tabs button {{
      padding:10px 18px; border-radius:10px; border:1px solid #475569;
      background:#1e293b; color:#e2e8f0; cursor:pointer; font-weight:600; font-size:13px;
      font-family: var(--nst-map-font), -apple-system, system-ui, sans-serif;
    }}
    .topo-view-tabs button.active {{ background:{accent}; border-color:{accent}; color:#fff; }}
    #topo-link-inventory {{ flex:1; overflow:auto; padding:16px 20px; background:#0f172a; color:#e2e8f0; }}
    #topo-link-inventory.hidden {{ display:none !important; }}
    #mynetwork.topo-map-hidden {{ display:none !important; }}
    .topo-inv-table {{ width:100%; border-collapse:collapse; font-size:12px; background:#1e293b; }}
    .topo-inv-table th {{
      text-align:left; padding:10px; background:#334155; color:#f1f5f9;
      position:sticky; top:0; cursor:pointer;
    }}
    .topo-inv-table td {{ padding:8px 10px; border-bottom:1px solid #334155; color:#e2e8f0; }}
    .topo-inv-table tr:hover td {{ background:#1e3a5f; }}
    .topo-search-bar {{
      padding:8px 16px; background:#1e293b; border-bottom:1px solid #334155;
      display:flex; gap:10px; align-items:center; flex-wrap:wrap;
    }}
    .topo-search-bar input {{
      flex:1; min-width:200px; padding:8px 12px; border-radius:6px;
      border:1px solid #475569; background:#0f172a; color:#f1f5f9;
    }}
    .topo-adj-list {{ font-size:11px; margin-top:8px; max-height:180px; overflow:auto; }}
    .topo-adj-list div {{ padding:4px 0; border-bottom:1px solid #334155; }}
    .nst-layer-switch {{ display:flex; gap:6px; flex-wrap:wrap; align-items:center; margin:8px 16px; }}
    .nst-layer-switch button {{
      padding:6px 12px; border-radius:6px; border:1px solid #475569;
      background:#1e293b; color:#e2e8f0; cursor:pointer; font-size:12px; font-weight:600;
    }}
    .nst-layer-switch button.active {{ background:{accent}; border-color:{accent}; color:#fff; }}
    .nst-stale {{ color:#fbbf24; font-weight:700; font-size:12px; }}
    .nst-fresh {{ color:#cbd5e1; font-size:12px; }}
    #nst-overlay-note {{ color:#fbbf24; font-size:12px; }}
    .nst-why-link {{
      margin: 0 16px 8px 16px; padding:8px 12px; border-radius:8px;
      background:#1e293b; border:1px solid #334155; color:#cbd5e1; font-size:12px;
    }}
    .nst-why-link button.nst-ev-open {{
      margin-left:10px; padding:4px 10px; font-size:11px; font-weight:600;
      border-radius:6px; border:1px solid #64748b; background:#334155; color:#f8fafc; cursor:pointer;
    }}
    .nst-why-link button.nst-ev-open:focus {{ outline:2px solid #93c5fd; outline-offset:2px; }}
    .nst-ev-backdrop {{
      display:none; position:fixed; inset:0; background:rgba(15,23,42,0.55); z-index:9000;
    }}
    .nst-ev-backdrop.nst-ev-open {{ display:block; }}
    .nst-ev-dialog {{
      display:none; position:fixed; top:0; right:0; width:min(420px, 100vw); height:100vh;
      z-index:9001; background:#0f172a; color:#e2e8f0; border-left:1px solid #334155;
      box-shadow:-8px 0 24px rgba(0,0,0,0.35); flex-direction:column;
    }}
    .nst-ev-dialog.nst-ev-open {{ display:flex; }}
    .nst-ev-dialog:focus {{ outline:none; }}
    .nst-ev-head {{
      display:flex; align-items:flex-start; justify-content:space-between; gap:12px;
      padding:14px 16px; border-bottom:1px solid #334155;
    }}
    .nst-ev-head h2 {{ margin:0; font-size:15px; color:#f8fafc; }}
    .nst-ev-head .nst-ev-sub {{ margin:4px 0 0; font-size:11px; color:#94a3b8; }}
    .nst-ev-close {{
      flex-shrink:0; padding:6px 12px; border-radius:6px; border:1px solid #64748b;
      background:#1e293b; color:#f8fafc; cursor:pointer; font-size:12px; font-weight:600;
    }}
    .nst-ev-close:focus {{ outline:2px solid #93c5fd; outline-offset:2px; }}
    .nst-ev-body {{
      flex:1; overflow:auto; padding:12px 16px 24px; font-size:12px; line-height:1.45;
    }}
    .nst-ev-body section {{ margin-bottom:14px; }}
    .nst-ev-body h3 {{
      margin:0 0 6px; font-size:11px; text-transform:uppercase; letter-spacing:0.04em; color:#94a3b8;
    }}
    .nst-ev-kv {{ display:grid; grid-template-columns:118px 1fr; gap:4px 8px; margin:0; }}
    .nst-ev-kv dt {{ color:#94a3b8; }}
    .nst-ev-kv dd {{ margin:0; color:#f1f5f9; word-break:break-word; }}
    .nst-ev-badge {{
      display:inline-block; padding:2px 8px; border-radius:6px; font-size:10px; font-weight:700;
      border:1px solid #475569; background:#1e293b; color:#e2e8f0; margin-right:4px;
    }}
    .nst-ev-badge.warn {{ border-color:#f59e0b; color:#fde68a; }}
    .nst-ev-badge.danger {{ border-color:#f87171; color:#fecaca; }}
    .nst-ev-badge.info {{ border-color:#38bdf8; color:#bae6fd; }}
    .nst-ev-card {{
      border:1px solid #334155; border-radius:8px; padding:8px 10px; margin-bottom:8px; background:#1e293b;
    }}
    .nst-ev-card summary {{ cursor:pointer; font-weight:600; color:#f8fafc; }}
    .nst-ev-card summary:focus {{ outline:2px solid #93c5fd; outline-offset:2px; }}
    .nst-ev-empty {{ color:#94a3b8; font-style:italic; }}
    .nst-ev-ro {{ font-size:11px; color:#64748b; margin-top:8px; }}
    button.nst-ev-inspect-btn {{
      padding:4px 10px; font-size:11px; font-weight:600; border-radius:6px;
      border:1px solid #64748b; background:#334155; color:#f8fafc; cursor:pointer;
    }}
    button.nst-ev-inspect-btn:focus {{ outline:2px solid #93c5fd; outline-offset:2px; }}
    button.nst-ev-inspect-btn:disabled {{
      opacity:0.55; cursor:not-allowed;
    }}
    body.discovery-command-center button.nst-ev-inspect-btn {{
      background:#fff; color:#334155; border-color:#94a3b8;
    }}
    .nst-overlay-empty {{
      margin: 0 16px 8px 16px; padding:12px 14px; border-radius:8px;
      background:#1e293b; border:1px dashed #fbbf24; color:#fde68a; font-size:13px; line-height:1.45;
    }}
    .nst-scale-note {{ color:#94a3b8; font-size:11px; margin-left:8px; }}
    {link_inventory_light_theme_css()}
    """


def embed_link_inventory_render_js():
    """Shared row renderer — trust pills, monospace ports, readable cells."""
    return """
    window.NST_STALE_HOURS = """ + str(NST_STALE_HOURS) + """;
    window.NST_BLAST_SEMANTICS = '""" + NST_BLAST_SEMANTICS + """';
    function topoEsc(s) {
      return String(s == null ? '' : s)
        .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }
    function topoTrustPill(tier) {
      var t = (tier || 'inferred').toString().toLowerCase();
      var cls = 'topo-trust-inferred';
      var label = tier || 'Inferred';
      if (t.indexOf('verif') >= 0) { cls = 'topo-trust-verified'; label = 'Verified'; }
      else if (t.indexOf('high') >= 0) { cls = 'topo-trust-verified'; label = 'High'; }
      else if (t.indexOf('medium') >= 0 || t.indexOf('unidir') >= 0) { cls = 'topo-trust-medium'; label = 'Medium'; }
      else if (t.indexOf('low') >= 0) { cls = 'topo-trust-medium'; label = 'Low'; }
      else if (t.indexOf('mismatch') >= 0) { cls = 'topo-trust-mismatch'; label = 'Mismatch'; }
      else if (t.indexOf('untrust') >= 0) { cls = 'topo-trust-mismatch'; label = 'Untrusted'; }
      else if (t.indexOf('infer') >= 0) { cls = 'topo-trust-inferred'; label = 'Inferred'; }
      return '<span class="topo-trust-pill '+cls+'">'+label+'</span>';
    }
    function topoPortCell(p) {
      var v = (p === null || p === undefined || p === '') ? '—' : String(p);
      return '<code class="topo-port">'+v+'</code>';
    }
    function topoLinkTypeCell(r) {
      var lt = (r.link_type || r.protocol || '').toString();
      if (!lt) return '—';
      return '<span class="topo-link-type">'+lt.replace(/_/g, ' ')+'</span>';
    }
    function topoRenderLinkRow(r, idx) {
      var evid = (r.sources && r.sources.length) ? r.sources.join('+') : (r.one_sided ? 'one-sided' : '—');
      if (r.spoof_risk || r.one_sided) evid += ' · spoof-risk';
      if (r.contradictions && r.contradictions.length) evid += ' · CONFLICT';
      if (r.freshness_conflict || r.freshness === 'mixed') evid += ' · MIXED';
      if (r.not_physical) evid += ' · L3/IRB';
      if (r.bundle_kind === 'bundle') evid += ' · BUNDLE/AE';
      if (r.degraded) evid += ' · DEGRADED';
      var i = (typeof idx === 'number') ? idx : -1;
      var inspect = '<button type="button" class="nst-ev-inspect-btn"' +
        ' aria-label="Inspect link evidence for ' + topoEsc(r.from||'') + ' to ' + topoEsc(r.to||'') + '"' +
        (i >= 0 ? ' onclick="nstInspectLinkRowByIndex(' + i + ')"' : ' disabled title="Inspect unavailable"') +
        '>Inspect</button>';
      return '<td><strong>'+topoEsc(r.from||'—')+'</strong></td>'+
        '<td>'+topoPortCell(r.local_port)+'</td>'+
        '<td><strong>'+topoEsc(r.to||'—')+'</strong></td>'+
        '<td>'+topoPortCell(r.remote_port)+'</td>'+
        '<td>'+topoLinkTypeCell(r)+'</td>'+
        '<td>'+topoEsc(r.vlan || '—')+'</td>'+
        '<td>'+topoTrustPill(r.trust_tier)+'</td>'+
        '<td>'+topoEsc(evid)+'</td>'+
        '<td>'+inspect+'</td>';
    }
    function nstLinkRowToEdge(r) {
      r = r || {};
      var evidence = (r.evidence && r.evidence.length) ? r.evidence : [];
      var edge = {
        from: r.from || '',
        to: r.to || '',
        f_port: r.f_port || r.local_port || '',
        t_port: r.t_port || r.remote_port || '',
        local_port: r.local_port || r.f_port || '',
        remote_port: r.remote_port || r.t_port || '',
        protocol: r.protocol || '',
        layer: r.layer || '',
        edge_kind: r.edge_kind || '',
        not_physical: !!r.not_physical,
        confidence: r.confidence || '',
        trust_tier: r.trust_tier || '',
        trust_note: r.trust_note || '',
        one_sided: !!r.one_sided,
        spoof_risk: !!r.spoof_risk,
        sources: r.sources || [],
        contradictions: r.contradictions || [],
        evidence: evidence,
        evidence_summary: r.evidence_summary || {},
        collected_at: r.collected_at || '',
        collected_at_latest: r.collected_at_latest || '',
        freshness: r.freshness || '',
        freshness_conflict: !!r.freshness_conflict,
        freshness_note: r.freshness_note || '',
        bundle_kind: r.bundle_kind || '',
        lag_note: r.lag_note || '',
        lacp_collected: !!r.lacp_collected,
        lacp_oper: r.lacp_oper || '',
        degraded: !!r.degraded
      };
      edge.relation_key = r.relation_key || nstRelationKey(edge);
      return edge;
    }
    function nstRelationKey(obj) {
      obj = obj || {};
      if (obj.relation_key) return String(obj.relation_key);
      var aHost = String(obj.from || '').trim().toLowerCase();
      var bHost = String(obj.to || '').trim().toLowerCase();
      var aPort = String(obj.f_port || obj.local_port || '').trim().toLowerCase();
      var bPort = String(obj.t_port || obj.remote_port || '').trim().toLowerCase();
      if (!aHost && !bHost) return '';
      var left = [aHost, aPort];
      var right = [bHost, bPort];
      if (left[0] > right[0] || (left[0] === right[0] && left[1] > right[1])) {
        var tmp = left; left = right; right = tmp;
      }
      var kind = String(obj.edge_kind || '').trim().toLowerCase();
      if (!kind) {
        var layer = String(obj.layer || '').trim().toLowerCase();
        if (obj.not_physical || layer === 'l3' || layer === 'overlay') kind = layer || 'logical';
        else kind = 'l2';
      }
      return [left[0], left[1], right[0], right[1], kind].join('|');
    }
    function nstClearRelationSync() {
      document.querySelectorAll('#link-tbody tr.nst-link-row-selected').forEach(function(tr) {
        tr.classList.remove('nst-link-row-selected');
        tr.removeAttribute('aria-selected');
      });
      var prevEdge = window._nstSyncEdgeId;
      window._nstSyncRelationKey = '';
      window._nstSyncEdgeId = '';
      if (prevEdge && !window._nstSyncSelecting) {
        var net = (typeof nstMapHandle === 'function') ? nstMapHandle() : null;
        if (!net) net = window.discNetwork || window.topoNetwork || null;
        if (net && typeof net.selectEdges === 'function') {
          window._nstSyncSelecting = true;
          try { net.selectEdges([]); } catch (err) {}
          window._nstSyncSelecting = false;
        }
      }
    }
    function nstFindEdgeIdByRelationKey(key) {
      if (!key || typeof edges === 'undefined' || !edges || !edges.get) return null;
      var found = null;
      edges.forEach(function(e) {
        if (found) return;
        var rk = e.relation_key || nstRelationKey(e);
        if (rk && rk === key) found = e.id;
      });
      return found;
    }
    function nstSyncHighlightRelation(obj, opts) {
      opts = opts || {};
      var key = (obj && (obj.relation_key || nstRelationKey(obj))) || '';
      // Replace prior row highlight without clearing map selection mid-sync
      document.querySelectorAll('#link-tbody tr.nst-link-row-selected').forEach(function(tr) {
        tr.classList.remove('nst-link-row-selected');
        tr.removeAttribute('aria-selected');
      });
      window._nstSyncRelationKey = key;
      if (!key) return false;
      var matched = false;
      document.querySelectorAll('#link-tbody tr[data-relation-key]').forEach(function(tr) {
        if (tr.getAttribute('data-relation-key') === key) {
          tr.classList.add('nst-link-row-selected');
          tr.setAttribute('aria-selected', 'true');
          matched = true;
          if (opts.scrollRow !== false) {
            try { tr.scrollIntoView({ block: 'nearest', inline: 'nearest' }); } catch (err) {}
          }
        }
      });
      if (opts.selectMap) {
        var eid = nstFindEdgeIdByRelationKey(key);
        var net = (typeof nstMapHandle === 'function') ? nstMapHandle() : null;
        if (!net) net = window.discNetwork || window.topoNetwork || null;
        if (eid != null && net && typeof net.selectEdges === 'function') {
          window._nstSyncEdgeId = eid;
          window._nstSyncSelecting = true;
          try { net.selectEdges([eid]); } catch (err2) {}
          window._nstSyncSelecting = false;
        }
      } else if (obj && obj.id != null) {
        window._nstSyncEdgeId = obj.id;
      }
      // Map→table path: reveal Link Inventory only if hidden and a matching row exists
      if (matched && !opts.selectMap && opts.revealInventory !== false) {
        nstRevealLinkInventoryIfNeeded();
        if (opts.scrollRow !== false) {
          document.querySelectorAll('#link-tbody tr.nst-link-row-selected').forEach(function(tr) {
            try { tr.scrollIntoView({ block: 'nearest', inline: 'nearest' }); } catch (err3) {}
          });
        }
      }
      return matched;
    }
    function nstLinkInventoryIsHidden() {
      var discPanel = document.getElementById('disc-panel-links');
      if (discPanel) {
        return !discPanel.classList.contains('active');
      }
      var inv = document.getElementById('topo-link-inventory');
      if (!inv) return null;
      if (inv.classList.contains('hidden')) return true;
      try {
        var st = window.getComputedStyle ? window.getComputedStyle(inv) : null;
        if (st && (st.display === 'none' || st.visibility === 'hidden')) return true;
      } catch (err) {}
      return false;
    }
    function nstRevealLinkInventoryIfNeeded() {
      var hidden = nstLinkInventoryIsHidden();
      if (hidden !== true) return false;
      if (document.getElementById('disc-panel-links') && typeof discCcTab === 'function') {
        discCcTab('links');
        return true;
      }
      if (document.getElementById('topo-link-inventory') && typeof topoViewTab === 'function') {
        topoViewTab('links');
        return true;
      }
      return false;
    }
    function nstInspectLinkRowByIndex(idx) {
      var rows = window.__TOPO_LINKS__ || [];
      var r = rows[idx];
      if (!r) {
        nstClearRelationSync();
        if (typeof nstOpenEvidenceInspector === 'function') {
          nstOpenEvidenceInspector({
            from: 'unknown', to: 'unknown', f_port: 'unknown', t_port: 'unknown',
            protocol: '', evidence: [], freshness: 'unknown'
          });
        }
        return;
      }
      var edge = nstLinkRowToEdge(r);
      nstSyncHighlightRelation(edge, { selectMap: true, scrollRow: true });
      if (typeof nstWhyThisLink === 'function') nstWhyThisLink(edge);
      else if (typeof nstOpenEvidenceInspector === 'function') nstOpenEvidenceInspector(edge);
    }
    function nstMarkFreshness(iso) {
      var el = document.getElementById('nst-freshness');
      if (!el || !iso) return;
      window._nstFreshIso = iso;
      var t = Date.parse(String(iso).replace(' ', 'T'));
      if (isNaN(t)) { el.textContent = 'Collected ' + iso; return; }
      var ageH = (Date.now() - t) / 3600000;
      if (ageH > window.NST_STALE_HOURS) {
        el.textContent = 'STALE (>' + window.NST_STALE_HOURS + 'h) — collected ' + iso + ' — not current truth';
        el.className = 'nst-stale';
      } else {
        el.textContent = 'Collected ' + iso + ' — clock-checked vs this browser';
        el.className = 'nst-fresh';
      }
    }
    function nstStartFreshnessClock(iso) {
      nstMarkFreshness(iso);
      if (window._nstFreshTimer) clearInterval(window._nstFreshTimer);
      window._nstFreshTimer = setInterval(function() { nstMarkFreshness(window._nstFreshIso); }, 60000);
    }
    function nstPhysicalEligible(e) {
      if (!e) return false;
      if (e.not_physical || e.layer === 'l3') return false;
      if (e.one_sided || e.spoof_risk) return false;
      if (e.contradictions && e.contradictions.length) return false;
      return true;
    }
    function nstIsOverlayEdge(e) {
      if (!e) return false;
      var kind = String(e.edge_kind || '').toLowerCase();
      var proto = String(e.protocol || '').toLowerCase();
      return e.layer === 'overlay' || kind === 'nve-peer' || proto === 'evpn';
    }
    function nstSetLayer(layer) {
      var note = document.getElementById('nst-overlay-note');
      var empty = document.getElementById('nst-overlay-empty');
      var emptyAbsent = document.getElementById('nst-overlay-empty-absent');
      var emptyZero = document.getElementById('nst-overlay-empty-zero');
      var physNote = document.getElementById('nst-physical-note');
      if (physNote) physNote.hidden = layer !== 'physical';
      document.querySelectorAll('.nst-layer-switch [data-layer]').forEach(function(b) {
        b.classList.toggle('active', b.getAttribute('data-layer') === layer);
      });
      var ds = nstEdgeSet();
      var overlayEdges = ds ? ds.get().filter(nstIsOverlayEdge) : [];
      var collected = !!(window.NST_OVERLAY_COLLECTED) || overlayEdges.length > 0;
      if (note) {
        note.hidden = layer !== 'overlay';
        note.textContent = collected
          ? (overlayEdges.length ? ('Overlay: ' + overlayEdges.length + ' NVE/EVPN peer(s) from device CLI — not cables.')
            : 'EVPN/NVE CLI ran; no overlay peers in this crawl.')
          : 'EVPN/VXLAN overlay is not collected.';
      }
      if (empty) empty.hidden = !(layer === 'overlay' && overlayEdges.length === 0);
      if (emptyAbsent) emptyAbsent.hidden = collected;
      if (emptyZero) emptyZero.hidden = !collected;
      if (!ds) return;
      ds.get().forEach(function(e) {
        var notPhys = !!(e.not_physical || e.layer === 'l3');
        var kind = String(e.edge_kind || e.protocol || '').toLowerCase();
        var hidden = false;
        if (layer === 'overlay') hidden = !nstIsOverlayEdge(e);
        else if (layer === 'l3') hidden = !notPhys && !/bgp|ospf|isis|eigrp/.test(kind);
        else if (layer === 'stp') {
          var isStp = e.layer === 'stp' || e.edge_kind === 'stp' || !!e.stp_state || /stp|spanning/i.test(String(e.title || ''));
          hidden = !isStp && !nstPhysicalEligible(e);
          var state = String(e.stp_state || e.port_state || '').toLowerCase();
          var updateObj = {id: e.id, hidden: hidden};
          if (state.includes('block') || state.includes('alt') || state.includes('discard')) {
            updateObj.color = {color: '#ef4444', highlight: '#f87171'};
            updateObj.dashes = [4, 4];
          } else if (state.includes('fwd') || state.includes('forward')) {
            updateObj.color = {color: '#22c55e', highlight: '#4ade80'};
          }
          ds.update(updateObj);
          return;
        }
        else if (layer === 'physical') hidden = !nstPhysicalEligible(e) || nstIsOverlayEdge(e);
        else hidden = notPhys || nstIsOverlayEdge(e);
        ds.update({id: e.id, hidden: hidden});
      });
    }
    function nstApplyHashLayer() {
      var h = (location.hash || '').replace(/^#/, '');
      var m = /(?:nst-)?layer=([a-z0-9_]+)/i.exec(h);
      var layer = m ? m[1].toLowerCase() : '';
      if (layer === 'physical' || layer === 'l2' || layer === 'l3' || layer === 'overlay' || layer === 'stp') {
        nstSetLayer(layer);
      }
    }
    function nstEdgeSet() {
      if (typeof edges !== 'undefined' && edges && typeof edges.get === 'function') return edges;
      if (window.edges && typeof window.edges.get === 'function') return window.edges;
      return null;
    }
    function nstNodeSet() {
      if (typeof nodes !== 'undefined' && nodes && typeof nodes.get === 'function') return nodes;
      if (window.nodes && typeof window.nodes.get === 'function') return window.nodes;
      return null;
    }
    function nstMapHandle() {
      return window.discNetwork || window.topoNetwork || window.network || null;
    }
    function nstResetHighlight() {
      var nset = nstNodeSet();
      var eset = nstEdgeSet();
      if (typeof nstClearRelationSync === 'function') nstClearRelationSync();
      if (!nset || !eset) return;
      nset.get().forEach(function(n) { nset.update({id: n.id, opacity: 1}); });
      eset.get().forEach(function(e) { eset.update({id: e.id, opacity: 1}); });
    }
    function nstBlastRadius(hops) {
      var net = nstMapHandle();
      var nset = nstNodeSet();
      var eset = nstEdgeSet();
      hops = (parseInt(hops, 10) === 2) ? 2 : 1;
      var nid = (net && net.getSelectedNodes && net.getSelectedNodes()[0]) || null;
      var el = document.getElementById('nst-why-link');
      if (!nid || !nset || !eset) {
        if (el) el.textContent = 'Select a device, then Blast radius (1-hop neighborhood, not a traffic path).';
        return;
      }
      var hop = {}; hop[nid] = 0;
      var frontier = [nid];
      for (var h = 0; h < hops; h++) {
        var next = [];
        frontier.forEach(function(id) {
          eset.get().forEach(function(e) {
            var other = e.from === id ? e.to : (e.to === id ? e.from : null);
            if (other && hop[other] === undefined) {
              hop[other] = h + 1;
              next.push(other);
            }
          });
        });
        frontier = next;
      }
      nset.get().forEach(function(n) {
        nset.update({id: n.id, opacity: hop[n.id] !== undefined ? 1 : 0.18});
      });
      eset.get().forEach(function(e) {
        var keep = hop[e.from] !== undefined && hop[e.to] !== undefined;
        eset.update({id: e.id, opacity: keep ? 1 : 0.08});
      });
      if (el) el.textContent = 'Blast radius for ' + nid + ' — ' + hops +
        '-hop neighborhood (not a forwarding path). Esc resets.';
    }
    function nstEvUnknown(v) {
      var s = (v == null || v === '') ? '' : String(v).trim();
      return s || 'unknown';
    }
    function nstEvBucket(ev) {
      var role = String((ev && ev.port_role) || '').toLowerCase();
      var kind = String((ev && ev.evidence_type) || '').toLowerCase();
      if ((ev && ev.not_physical) || role.indexOf('irb') >= 0 || role.indexOf('l3') >= 0 ||
          kind === 'vlan_context' || kind === 'irb_context' || kind === 'l3_context') {
        return 'supporting_context';
      }
      if (kind === 'inferred' || kind === 'heuristic') return 'inferred';
      return 'observed';
    }
    function nstBuildEvidenceInspectorModel(e) {
      e = e || {};
      var raw = (e.evidence && e.evidence.length) ? e.evidence : [];
      var items = [];
      raw.forEach(function(ev) {
        if (!ev || typeof ev !== 'object') {
          items.push({
            bucket: 'unknown', protocol: 'unknown', vendor: 'unknown', command: 'unknown',
            parse_source: 'unknown', local_port: 'unknown', remote_port: 'unknown',
            port_role: 'unknown', not_physical: false, collected_at_display: 'unknown',
            timestamp_known: false, freshness: 'unknown', evidence_type: 'malformed', malformed: true
          });
          return;
        }
        var ts = ev.collected_at;
        var known = !!(ts != null && String(ts).trim());
        items.push({
          bucket: nstEvBucket(ev),
          protocol: nstEvUnknown(ev.protocol),
          vendor: nstEvUnknown(ev.vendor || ev.platform),
          command: nstEvUnknown(ev.command),
          parse_source: nstEvUnknown(ev.parse_source),
          local_port: nstEvUnknown(ev.local_port),
          remote_port: nstEvUnknown(ev.remote_port),
          port_role: nstEvUnknown(ev.port_role),
          not_physical: !!ev.not_physical,
          collected_at_display: known ? String(ts) : 'unknown',
          timestamp_known: known,
          freshness: nstEvUnknown(ev.freshness || (known ? '' : 'unknown')),
          evidence_type: nstEvUnknown(ev.evidence_type || 'neighbor'),
          malformed: false
        });
      });
      var contradictions = (e.contradictions || []).map(function(c) { return String(c); }).filter(Boolean);
      var freshness = nstEvUnknown(e.freshness);
      var conflict = !!(e.freshness_conflict || freshness === 'mixed');
      var supporting = items.filter(function(i) { return i.bucket === 'supporting_context'; });
      var observed = items.filter(function(i) { return i.bucket === 'observed'; });
      var inferred = [];
      if (e.one_sided || e.spoof_risk) inferred.push('ONE-SIDED / spoof-risk — not a verified cable');
      var conf = (e.confidence || e.trust_tier || '').toString().trim();
      if (conf) inferred.push('confidence/trust conclusion=' + conf);
      if (e.not_physical || String(e.edge_kind || '').toLowerCase().indexOf('irb') >= 0) {
        inferred.push('edge classified as non-cable / logical adjacency');
      }
      if (e.bundle_kind === 'bundle' && !e.lacp_collected) {
        inferred.push('BUNDLE/AE naming heuristic — not LACP proof');
      }
      var cableClaim = (e.not_physical || supporting.length)
        ? 'supporting L3/IRB context — not cable proof'
        : ((e.one_sided || e.spoof_risk)
          ? 'not a verified cable (one-sided)'
          : 'adjacency from neighbor protocol(s) — inspect evidence');
      return {
        read_only: true,
        endpoints: {
          from: nstEvUnknown(e.from), to: nstEvUnknown(e.to),
          f_port: nstEvUnknown(e.f_port || e.local_port),
          t_port: nstEvUnknown(e.t_port || e.remote_port)
        },
        classification: {
          protocol: nstEvUnknown(e.protocol),
          layer: nstEvUnknown(e.layer),
          edge_kind: nstEvUnknown(e.edge_kind),
          not_physical: !!e.not_physical,
          cable_claim: cableClaim
        },
        trust: {
          confidence: nstEvUnknown(e.confidence),
          trust_tier: nstEvUnknown(e.trust_tier),
          trust_note: (e.trust_note || '') || null
        },
        freshness: {
          state: freshness,
          conflict: conflict,
          note: (e.freshness_note || '') || null,
          collected_at_display: nstEvUnknown(e.collected_at),
          collected_at_latest_display: nstEvUnknown(e.collected_at_latest)
        },
        evidence_count: items.length,
        sections: {
          observed: observed,
          supporting_context: supporting,
          inferred_conclusions: inferred,
          conflicts: contradictions,
          unknowns: items.filter(function(i) {
            return i.bucket !== 'observed' && i.bucket !== 'supporting_context' && i.bucket !== 'inferred';
          })
        },
        evidence_items: items,
        has_evidence: items.length > 0,
        empty_message: items.length ? null : 'No supporting observations attached to this edge.'
      };
    }
    function nstEvKv(rows) {
      var html = '<dl class="nst-ev-kv">';
      rows.forEach(function(r) {
        html += '<dt>' + topoEsc(r[0]) + '</dt><dd>' + topoEsc(r[1]) + '</dd>';
      });
      return html + '</dl>';
    }
    function nstEvItemCard(it, idx) {
      var title = (it.protocol || 'unknown') + ' · ' + (it.local_port || 'unknown') +
        ' ↔ ' + (it.remote_port || 'unknown');
      var badges = '';
      if (it.not_physical || it.bucket === 'supporting_context') {
        badges += '<span class="nst-ev-badge info">L3/IRB context</span>';
      }
      if (it.freshness === 'stale') badges += '<span class="nst-ev-badge warn">stale</span>';
      if (it.freshness === 'mixed') badges += '<span class="nst-ev-badge warn">mixed</span>';
      if (it.freshness === 'current') badges += '<span class="nst-ev-badge">current</span>';
      if (!it.timestamp_known) badges += '<span class="nst-ev-badge warn">timestamp unknown</span>';
      if (it.malformed) badges += '<span class="nst-ev-badge danger">malformed</span>';
      var body = nstEvKv([
        ['Protocol', it.protocol],
        ['Vendor', it.vendor],
        ['Command', it.command],
        ['Parse source', it.parse_source],
        ['Local port', it.local_port],
        ['Remote port', it.remote_port],
        ['Port role', it.port_role],
        ['Not physical', it.not_physical ? 'yes' : 'no'],
        ['Collected at', it.collected_at_display],
        ['Freshness', it.freshness]
      ]);
      return '<details class="nst-ev-card"' + (idx === 0 ? ' open' : '') + '>' +
        '<summary>' + topoEsc(title) + ' ' + badges + '</summary>' + body + '</details>';
    }
    function nstRenderEvidenceInspectorHtml(model) {
      var m = model || {};
      var ep = m.endpoints || {};
      var cl = m.classification || {};
      var tr = m.trust || {};
      var fr = m.freshness || {};
      var sec = m.sections || {};
      var html = '';
      html += '<section aria-labelledby="nst-ev-sum-h"><h3 id="nst-ev-sum-h">Edge summary</h3>';
      html += nstEvKv([
        ['From', (ep.from || 'unknown') + ' / ' + (ep.f_port || 'unknown')],
        ['To', (ep.to || 'unknown') + ' / ' + (ep.t_port || 'unknown')],
        ['Protocol', cl.protocol || 'unknown'],
        ['Layer / kind', (cl.layer || 'unknown') + ' / ' + (cl.edge_kind || 'unknown')],
        ['Cable claim', cl.cable_claim || 'unknown'],
        ['Confidence', tr.confidence || 'unknown'],
        ['Trust tier', tr.trust_tier || 'unknown'],
        ['Freshness', fr.state || 'unknown'],
        ['Freshness conflict', fr.conflict ? 'yes' : 'no'],
        ['Collected (oldest)', fr.collected_at_display || 'unknown'],
        ['Collected (latest)', fr.collected_at_latest_display || 'unknown'],
        ['Evidence count', String(m.evidence_count != null ? m.evidence_count : 0)]
      ]);
      if (fr.note) html += '<p>' + topoEsc(fr.note) + '</p>';
      if (tr.trust_note) html += '<p>' + topoEsc(tr.trust_note) + '</p>';
      html += '</section>';

      html += '<section aria-labelledby="nst-ev-obs-h"><h3 id="nst-ev-obs-h">Observed evidence</h3>';
      if ((sec.observed || []).length) {
        (sec.observed || []).forEach(function(it, i) { html += nstEvItemCard(it, i); });
      } else {
        html += '<p class="nst-ev-empty">' + topoEsc(m.empty_message || 'No observed neighbor evidence.') + '</p>';
      }
      html += '</section>';

      html += '<section aria-labelledby="nst-ev-sup-h"><h3 id="nst-ev-sup-h">Supporting context (L3/IRB/VLAN)</h3>';
      if ((sec.supporting_context || []).length) {
        html += '<p class="nst-ev-empty">Not cable proof — logical / IRB / VLAN context only.</p>';
        (sec.supporting_context || []).forEach(function(it, i) { html += nstEvItemCard(it, i); });
      } else {
        html += '<p class="nst-ev-empty">None.</p>';
      }
      html += '</section>';

      html += '<section aria-labelledby="nst-ev-inf-h"><h3 id="nst-ev-inf-h">Inferred conclusions</h3>';
      if ((sec.inferred_conclusions || []).length) {
        html += '<ul>' + (sec.inferred_conclusions || []).map(function(x) {
          return '<li>' + topoEsc(x) + '</li>';
        }).join('') + '</ul>';
      } else {
        html += '<p class="nst-ev-empty">None beyond observations.</p>';
      }
      html += '</section>';

      html += '<section aria-labelledby="nst-ev-cf-h"><h3 id="nst-ev-cf-h">Conflicts</h3>';
      if (fr.conflict) {
        html += '<p><span class="nst-ev-badge warn">mixed freshness</span> Observations disagree in age.</p>';
      }
      if ((sec.conflicts || []).length) {
        html += '<ul>' + (sec.conflicts || []).map(function(x) {
          return '<li>' + topoEsc(x) + '</li>';
        }).join('') + '</ul>';
      } else if (!fr.conflict) {
        html += '<p class="nst-ev-empty">No contradiction notes.</p>';
      }
      html += '</section>';

      if ((sec.unknowns || []).length) {
        html += '<section aria-labelledby="nst-ev-un-h"><h3 id="nst-ev-un-h">Unknown / partial</h3>';
        (sec.unknowns || []).forEach(function(it, i) { html += nstEvItemCard(it, i); });
        html += '</section>';
      }
      html += '<p class="nst-ev-ro">Read-only inspector — cannot edit trust, delete evidence, or mutate topology.</p>';
      return html;
    }
    function nstCloseEvidenceInspector() {
      var dlg = document.getElementById('nst-evidence-inspector');
      var bd = document.getElementById('nst-evidence-backdrop');
      if (dlg) {
        dlg.classList.remove('nst-ev-open');
        dlg.setAttribute('aria-hidden', 'true');
        dlg.setAttribute('hidden', '');
      }
      if (bd) {
        bd.classList.remove('nst-ev-open');
        bd.setAttribute('aria-hidden', 'true');
        bd.setAttribute('hidden', '');
      }
      if (typeof nstClearRelationSync === 'function') nstClearRelationSync();
      var prev = window._nstEvPrevFocus;
      if (prev && typeof prev.focus === 'function') {
        try { prev.focus(); } catch (err) {}
      }
      window._nstEvPrevFocus = null;
    }
    function nstOpenEvidenceInspector(e) {
      var dlg = document.getElementById('nst-evidence-inspector');
      var body = document.getElementById('nst-evidence-body');
      var bd = document.getElementById('nst-evidence-backdrop');
      if (!dlg || !body || !e) return;
      window._nstEvPrevFocus = document.activeElement;
      var model = nstBuildEvidenceInspectorModel(e);
      body.innerHTML = nstRenderEvidenceInspectorHtml(model);
      if (bd) {
        bd.removeAttribute('hidden');
        bd.setAttribute('aria-hidden', 'false');
        bd.classList.add('nst-ev-open');
      }
      dlg.removeAttribute('hidden');
      dlg.setAttribute('aria-hidden', 'false');
      dlg.classList.add('nst-ev-open');
      var closeBtn = document.getElementById('nst-evidence-close');
      if (closeBtn) {
        try { closeBtn.focus(); } catch (err) {}
      } else {
        try { dlg.focus(); } catch (err2) {}
      }
    }
    function nstWhyThisLink(e) {
      var el = document.getElementById('nst-why-link');
      if (!el || !e) return;
      var bits = [];
      bits.push((e.protocol || 'link') + ': ' + (e.from || '') + ' ' + (e.f_port || e.local_port || '') +
        ' ↔ ' + (e.to || '') + ' ' + (e.t_port || e.remote_port || ''));
      if (e.one_sided || e.spoof_risk) bits.push('ONE-SIDED — spoofable, not a verified cable');
      if (e.confidence) bits.push('confidence=' + e.confidence);
      if (e.freshness) bits.push('freshness=' + e.freshness);
      if (e.freshness_conflict || e.freshness === 'mixed') bits.push('MIXED FRESHNESS');
      if (e.sources && e.sources.length) bits.push('evidence=' + e.sources.join('+'));
      if (e.evidence && e.evidence.length) bits.push('observations=' + e.evidence.length);
      if (e.contradictions && e.contradictions.length) bits.push('Mismatch/CONFLICT — contradictory remotes, no winner: ' + e.contradictions.join('; '));
      if (e.lacp_collected && e.lacp_oper) bits.push('LACP ' + e.lacp_oper + ' (device CLI)');
      else if (e.bundle_kind === 'bundle') bits.push('BUNDLE/AE ifName — naming heuristic, LACP member health not collected');
      else if (e.bundle_kind === 'member') bits.push('Member ifName (not the bundle interface; not LACP state)');
      if (e.degraded) bits.push('DEGRADED member — bundle edge must remain if present');
      if (e.lag_note) bits.push(e.lag_note);
      if (e.trust_note) bits.push(e.trust_note);
      if (e.not_physical) bits.push('logical adjacency — not a cable');
      var src = e.edge_data || e;
      if (src.desc_vs_neighbor && src.desc_vs_neighbor !== 'unknown') {
        bits.push('desc vs neighbor=' + src.desc_vs_neighbor);
      }
      if (src.speed_mismatch) bits.push('SPEED MISMATCH — CLI snapshot, not a cable cert');
      if (src.duplex_mismatch) bits.push('DUPLEX MISMATCH — CLI snapshot, not a cable cert');
      if (src.cable_issues && src.cable_issues.length) bits.push('witness issues: ' + src.cable_issues.join(', '));
      if (src.cable_witnesses && src.cable_witnesses.length) bits.push(src.cable_witnesses.slice(0, 3).join('; '));
      if (src.optics_collected && src.optics) bits.push('DOM snapshot collected (not a certified cable)');
      if (src.cable_note) bits.push(src.cable_note);
      if (typeof nstSyncHighlightRelation === 'function' && !window._nstSyncSelecting) {
        nstSyncHighlightRelation(e, { selectMap: false, scrollRow: true });
      }
      el.textContent = '';
      el.appendChild(document.createTextNode(bits.join(' · ') + ' '));
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'nst-ev-open';
      btn.setAttribute('aria-label', 'Open read-only link evidence inspector');
      btn.textContent = 'Inspect evidence';
      btn.addEventListener('click', function(ev) {
        ev.preventDefault();
        nstOpenEvidenceInspector(e);
      });
      el.appendChild(btn);
      nstOpenEvidenceInspector(e);
    }
    document.addEventListener('keydown', function(ev) {
      if (ev.key !== 'Escape') return;
      var dlg = document.getElementById('nst-evidence-inspector');
      if (dlg && dlg.classList.contains('nst-ev-open')) {
        ev.preventDefault();
        nstCloseEvidenceInspector();
        return;
      }
      nstResetHighlight();
    });
    document.addEventListener('DOMContentLoaded', nstApplyHashLayer);
    setTimeout(nstApplyHashLayer, 80);
    function nstMarkScale(count) {
      var el = document.getElementById('nst-scale-note');
      if (!el) return;
      el.hidden = !(count > 50);
    }
"""


def layer_switch_html(default_layer='l2'):
    return f"""
    <div class="nst-layer-switch" role="navigation" aria-label="Map layer">
      <button type="button" data-layer="physical" aria-label="Bidirectional CDP/LLDP only, not verified cables" {'class="active"' if default_layer=='physical' else ''} onclick="nstSetLayer('physical')">Physical</button>
      <button type="button" data-layer="l2" aria-label="Show all layer-2 adjacencies including one-sided" {'class="active"' if default_layer=='l2' else ''} onclick="nstSetLayer('l2')">L2</button>
      <button type="button" data-layer="l3" aria-label="Show layer-3 routing adjacencies" {'class="active"' if default_layer=='l3' else ''} onclick="nstSetLayer('l3')">L3</button>
      <button type="button" data-layer="overlay" aria-label="EVPN/VXLAN overlay from NVE CLI when collected" {'class="active"' if default_layer=='overlay' else ''} onclick="nstSetLayer('overlay')">Overlay</button>
      <button type="button" data-layer="stp" aria-label="Spanning-Tree Protocol root bridge, forwarding and blocking ports" {'class="active"' if default_layer=='stp' else ''} onclick="nstSetLayer('stp')">STP</button>
      <button type="button" aria-label="Highlight one-hop blast radius of selected device" onclick="nstBlastRadius(1)">Blast 1 hop</button>
      <button type="button" aria-label="Highlight two-hop neighborhood, not a traffic path" onclick="nstBlastRadius(2)">Blast 2 hop</button>
      <button type="button" aria-label="Reset map highlights" onclick="nstResetHighlight()">Reset highlight</button>
      <span id="nst-stp-note" hidden>STP View: Spanning-Tree topology (Forwarding green, Blocking red dashed).</span>
      <span id="nst-overlay-note" hidden>EVPN/VXLAN overlay is not collected.</span>
      <span id="nst-physical-note" hidden>Physical view = bidirectional CDP/LLDP only — not verified cables, not LACP.</span>
      <span id="nst-freshness"></span>
      <span id="nst-scale-note" class="nst-scale-note" hidden>Large graph — search/filter recommended. Physics off. Blast radius is a neighborhood, not a path.</span>
    </div>
    <div id="nst-overlay-empty" class="nst-overlay-empty" hidden role="status">
      <div id="nst-overlay-empty-absent">
      <strong>Overlay not collected.</strong>
      This product does not gather EVPN/VXLAN VTEP or overlay control-plane data
      until Discovery or inventory topology runs NVE/EVPN CLI.
      An empty overlay panel is not proof the fabric has no overlay.
      Use Physical, L2, or L3 for what was actually crawled.
      Hostnames that look like leaf, spine, or vtep are <em>not</em> overlay evidence.
      </div>
      <div id="nst-overlay-empty-zero" hidden>
      <strong>EVPN/NVE CLI ran; no overlay peers in this crawl.</strong>
      Empty overlay is not an empty fabric. Underlay stays on Physical/L2.
      </div>
    </div>
    <div id="nst-why-link" class="nst-why-link" aria-live="polite">Click a device or link for evidence. Blast radius is a neighborhood, not a forwarding path. Esc resets.</div>
    <div id="nst-evidence-backdrop" class="nst-ev-backdrop" hidden aria-hidden="true" onclick="nstCloseEvidenceInspector()"></div>
    <div id="nst-evidence-inspector" class="nst-ev-dialog" role="dialog" aria-modal="true"
      aria-labelledby="nst-evidence-title" aria-hidden="true" hidden tabindex="-1">
      <div class="nst-ev-head">
        <div>
          <h2 id="nst-evidence-title">Link evidence (read-only)</h2>
          <p class="nst-ev-sub">Why this edge exists — observations, conflicts, and unknowns. Esc closes.</p>
        </div>
        <button type="button" id="nst-evidence-close" class="nst-ev-close"
          aria-label="Close evidence inspector" onclick="nstCloseEvidenceInspector()">Close</button>
      </div>
      <div id="nst-evidence-body" class="nst-ev-body"></div>
    </div>
    """


def embed_link_inventory_block(links_default=True, map_default=False):
    """HTML fragment for Link Inventory tab (embed in report_formatter maps)."""
    if map_default:
        links_default = False
    links_hidden = '' if links_default else 'hidden'
    links_active = 'active' if links_default else ''
    map_active = 'active' if map_default or not links_default else ''
    return f"""
  <div class="topo-view-tabs" id="topo-view-tabs" style="margin:8px 16px 0;">
    <button type="button" id="tab-btn-links" class="{links_active}" onclick="topoViewTab('links')">Link Inventory</button>
    <button type="button" id="tab-btn-map" class="{map_active}" onclick="topoViewTab('map')">Topology Map</button>
    <span id="topo-search-count" style="font-size:11px;color:#94a3b8;margin-left:8px;"></span>
  </div>
  <div id="topo-link-inventory" class="{links_hidden}" style="flex:1;overflow:auto;min-height:200px;">
    <div class="topo-inv-hint">Sort columns by clicking headers. Filter with search — matching rows highlight on the map.</div>
    <div class="topo-search-bar">
      <span style="font-size:12px;font-weight:600;">Filter links &amp; map:</span>
      <input type="text" id="topo-search-input" placeholder="hostname, IP, port-channel, Po, protocol..."
        oninput="topoApplySearch(this.value)" />
    </div>
    <table class="topo-inv-table">
      <thead><tr>
        <th onclick="topoSortTable(0)">From</th>
        <th onclick="topoSortTable(1)">Local Port</th>
        <th onclick="topoSortTable(2)">To</th>
        <th onclick="topoSortTable(3)">Remote Port</th>
        <th onclick="topoSortTable(4)">Type</th>
        <th onclick="topoSortTable(5)">VLAN</th>
        <th onclick="topoSortTable(6)">Trust</th>
        <th onclick="topoSortTable(7)">Evidence</th>
        <th>Inspect</th>
      </tr></thead>
      <tbody id="link-tbody"></tbody>
    </table>
  </div>
"""


def embed_link_inventory_js(link_rows_json, map_default=False):
    """JavaScript for embedded link inventory (uses existing nodes/edges DataSets)."""
    boot_map = """
    function topoBootMapVisible() {
      if (window.__VPC_COMMAND_CENTER__) return;
      if (typeof topoViewTab === 'function') topoViewTab('map');
      else if (typeof createTopologyNetwork === 'function') {
        createTopologyNetwork();
        if (typeof wireNetworkHandlers === 'function') wireNetworkHandlers();
        if (typeof network !== 'undefined' && network) {
          try { network.fit({ animation: false }); } catch (e) {}
        }
      }
    }
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function() { setTimeout(topoBootMapVisible, 80); });
    } else {
      setTimeout(topoBootMapVisible, 80);
    }
""" if map_default else ""
    return f"""
    window.__TOPO_LINKS__ = {link_rows_json};
    var topoSortCol = 0, topoSortAsc = true;
    {embed_link_inventory_render_js()}
    function renderLinkTable() {{
        var tb = document.getElementById('link-tbody');
        if (!tb) return;
        tb.innerHTML = '';
        (window.__TOPO_LINKS__ || []).forEach(function(r, idx) {{
            var tr = document.createElement('tr');
            tr.dataset.search = [r.from,r.local_port,r.to,r.remote_port,r.protocol,r.vlan||'',r.vpc_domain||'',r.trust_tier||'',r.link_type||''].join(' ').toLowerCase();
            if (r.relation_key) tr.setAttribute('data-relation-key', r.relation_key);
            tr.innerHTML = topoRenderLinkRow(r, idx);
            tb.appendChild(tr);
        }});
    }}
    function topoSortTable(col) {{
        if (topoSortCol === col) topoSortAsc = !topoSortAsc;
        else {{ topoSortCol = col; topoSortAsc = true; }}
        var keys = ['from','local_port','to','remote_port','protocol','vlan','trust_tier'];
        var k = keys[col];
        window.__TOPO_LINKS__.sort(function(a,b) {{
            var va=(a[k]||'').toString(), vb=(b[k]||'').toString();
            if (va<vb) return topoSortAsc?-1:1;
            if (va>vb) return topoSortAsc?1:-1;
            return 0;
        }});
        renderLinkTable();
        var si = document.getElementById('topo-search-input');
        if (si) topoApplySearch(si.value);
    }}
    function topoShellShowLinks() {{
        var inv = document.getElementById('topo-link-inventory');
        if (inv) inv.classList.remove('hidden');
        renderLinkTable();
    }}
    function topoViewTab(which) {{
        var inv = document.getElementById('topo-link-inventory');
        var net = document.getElementById('mynetwork');
        var bl = document.getElementById('tab-btn-links');
        var bm = document.getElementById('tab-btn-map');
        if (!inv || !net) return;
        if (which === 'links') {{
            inv.classList.remove('hidden');
            net.classList.add('topo-map-hidden');
            if (bl) bl.classList.add('active');
            if (bm) bm.classList.remove('active');
        }} else {{
            inv.classList.add('hidden');
            net.classList.remove('topo-map-hidden');
            if (bm) bm.classList.add('active');
            if (bl) bl.classList.remove('active');
            if (typeof createTopologyNetwork === 'function') createTopologyNetwork();
            if (window.network) {{
                try {{ window.network.fit({{ animation: false }}); }} catch (e) {{}}
            }}
        }}
    }}
    function topoNodeHaystack(n) {{
        return [n.id,n.label,n.role,n.ip,n.platform,n.vpc_domain_id,n.title].join(' ').toLowerCase();
    }}
    function topoEdgeHaystack(e) {{
        return [e.label,e.from,e.to,e.f_port,e.t_port,e.protocol,e.title,e.type].join(' ').toLowerCase();
    }}
    {topo_search_helpers_js()}
    function topoApplySearch(q) {{
        q = (q||'').trim().toLowerCase();
        var si = document.getElementById('topo-search-input');
        var mainInp = document.getElementById('searchInput');
        if (si && mainInp && document.activeElement === mainInp) si.value = mainInp.value;
        if (mainInp && si && document.activeElement === si) mainInp.value = si.value;
        q = (si && si.value) ? si.value.trim().toLowerCase() : q;
        if (typeof nodes === 'undefined' || typeof edges === 'undefined') return;
        var allN = nodes.getIds().slice();
        var allE = edges.getIds().slice();
        topoApplyNodeEdgeFocus(q, allN, allE);
        var trs = document.querySelectorAll('#link-tbody tr');
        var vis=0;
        trs.forEach(function(tr) {{
            var ok = !q || (tr.dataset.search||'').indexOf(q)>=0;
            tr.style.display = ok ? '' : 'none';
            if (ok) vis++;
        }});
        var cnt = document.getElementById('topo-search-count');
        if (cnt) cnt.textContent = q ? (vis+' links match') : '';
    }}
    function topoShellSearch(q) {{ topoApplySearch(q); }}
    renderLinkTable();
    (function() {{
        var mi = document.getElementById('searchInput');
        if (mi) mi.addEventListener('input', function() {{ topoApplySearch(mi.value); }});
    }})();
{boot_map}
"""


def render_topology_page(
    filepath,
    title,
    nodes_json,
    edges_json,
    link_rows,
    *,
    subtitle='',
    accent='#0a84ff',
    extra_head='',
    extra_body_before='',
    map_visible_class='topo-map-hidden',
    links_default=True,
):
    """Write standalone HTML with unified map shell."""
    version_label = read_version_label()
    vis_script = load_vis_script()
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sub = subtitle or f'{len(nodes_json)} devices · {len(edges_json)} links · {ts}'
    map_hidden = map_visible_class if links_default else ''
    links_hidden = 'hidden' if not links_default else ''

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    {vis_script}
    <style>
        body {{ margin:0; padding:0; background:#060d1a; color:#f1f5f9;
            font-family:system-ui,'Segoe UI',sans-serif; height:100vh;
            display:flex; flex-direction:column; overflow:hidden; }}
        .nst-top-chrome {{ flex-shrink:0; }}
        #main-wrap {{ display:flex; flex-direction:column; flex:1 1 0%; overflow:hidden; min-height:0; }}
        #container {{ display:flex; flex:1 1 0%; overflow:hidden; min-height:0; }}
        #mynetwork {{ flex:1; background:#060d1a; min-height:300px; }}
        #topo-sidebar {{ width:300px; background:#1e293b; border-left:1px solid #334155;
            padding:14px; overflow-y:auto; flex-shrink:0; }}
        .card {{ background:#0f172a; border:1px solid #334155; border-radius:8px;
            padding:10px 12px; margin-bottom:10px; }}
        .card-title {{ font-size:11px; font-weight:700; text-transform:uppercase;
            color:#64748b; letter-spacing:.05em; margin-bottom:6px; }}
        .table-prop {{ width:100%; border-collapse:collapse; font-size:12px; }}
        .table-prop td {{ padding:4px 0; color:#94a3b8; }}
        .table-prop td:first-child {{ color:#93c5fd; width:42%; }}
        {shell_css(accent)}
        {extra_head}
    </style>
</head>
<body>
    <div class="nst-top-chrome" id="nst-top-chrome" role="banner">
      <div class="nst-top-row">
        <div class="nst-brand-icon" aria-hidden="true">🗺</div>
        <div>
          <h1 style="font-size:15px;font-weight:700;color:#f1f5f9;margin:0">{title}<span class="nst-ver">{version_label}</span></h1>
          <div style="font-size:10px;color:#475569;margin-top:1px;">{sub}</div>
        </div>
        <div class="nst-top-stats">
          <div class="nst-hstat"><div class="nst-hstat-val">{len(nodes_json)}</div><div class="nst-hstat-lbl">Devices</div></div>
          <div class="nst-vsep"></div>
          <div class="nst-hstat"><div class="nst-hstat-val">{len(edges_json)}</div><div class="nst-hstat-lbl">Links</div></div>
        </div>
      </div>
      <div class="nst-toolbar-row">
        <input type="text" class="nst-search-input" id="topo-search-input"
          placeholder="hostname, IP, port, protocol…"
          oninput="topoApplySearch(this.value)" aria-label="Search topology">
        <span id="topo-search-count" style="font-size:11px;color:#64748b;margin-left:4px"></span>
      </div>
      <div class="nst-legend-row" aria-label="Link legend">
        <span class="nst-legend-pill"><span class="nst-legend-swatch" style="background:#607d8b"></span>Standard</span>
        <span class="nst-legend-pill"><span class="nst-legend-swatch" style="background:#10b981"></span>Port-Channel</span>
        <span class="nst-legend-pill"><span class="nst-legend-swatch" style="background:#f59e0b"></span>vPC Member</span>
        <span class="nst-legend-pill"><span class="nst-legend-swatch" style="background:#8b5cf6"></span>Peer-Link</span>
        <span class="nst-legend-pill"><span class="nst-legend-swatch" style="background:#059669"></span>Verified</span>
        <span class="nst-legend-pill"><span class="nst-legend-swatch" style="background:#ef4444"></span>Mismatch</span>
      </div>
    </div>
    {layer_switch_html('l2')}
    {extra_body_before}
    <main id="main-wrap">
        <div class="topo-view-tabs">
            <button type="button" id="tab-btn-links" class="{'active' if links_default else ''}"
                onclick="topoViewTab('links')">Link Inventory</button>
            <button type="button" id="tab-btn-map" class="{'' if links_default else 'active'}"
                onclick="topoViewTab('map')">Topology Map</button>
            <button type="button" onclick="window.print()">Print</button>
        </div>
        <div id="container">
            <div id="topo-link-inventory" class="{links_hidden}">
                <table class="topo-inv-table" id="link-table">
                    <thead><tr>
                        <th onclick="topoSortTable(0)">From</th>
                        <th onclick="topoSortTable(1)">Local</th>
                        <th onclick="topoSortTable(2)">To</th>
                        <th onclick="topoSortTable(3)">Remote</th>
                        <th onclick="topoSortTable(4)">Type</th>
                        <th onclick="topoSortTable(5)">VLAN</th>
                        <th onclick="topoSortTable(6)">Trust</th>
                        <th onclick="topoSortTable(7)">Evidence</th>
                        <th>Inspect</th>
                    </tr></thead>
                    <tbody id="link-tbody"></tbody>
                </table>
            </div>
            <div id="mynetwork" class="{map_hidden}"></div>
            <div id="topo-sidebar">
                <div class="card">
                    <div class="card-title">Overview</div>
                    <table class="table-prop">
                        <tr><td>Nodes</td><td id="topo-node-count">{len(nodes_json)}</td></tr>
                        <tr><td>Links</td><td id="topo-edge-count">{len(edges_json)}</td></tr>
                    </table>
                </div>
                <div class="card" id="topo-detail-card" style="display:none;">
                    <div class="card-title">Selected</div>
                    <table class="table-prop">
                        <tr><td>Name</td><td id="node-name">-</td></tr>
                        <tr><td>IP</td><td id="node-ip">-</td></tr>
                        <tr><td>Info</td><td id="node-extra">-</td></tr>
                    </table>
                    <div class="card-title" style="margin-top:10px;">Adjacencies</div>
                    <div class="topo-adj-list" id="node-adj"></div>
                </div>
            </div>
        </div>
    </main>
    <script type="text/javascript">
        window.__TOPO_LINKS__ = {script_safe_json(link_rows)};
        var nodes = new vis.DataSet({script_safe_json(nodes_json)});
        var edges = new vis.DataSet({script_safe_json(edges_json)});
        window.nodes = nodes;
        window.edges = edges;
        var topoAllNodeIds = nodes.getIds().slice();
        var topoAllEdgeIds = edges.getIds().slice();

        function topoViewTab(which) {{
            var inv = document.getElementById('topo-link-inventory');
            var net = document.getElementById('mynetwork');
            var bl = document.getElementById('tab-btn-links');
            var bm = document.getElementById('tab-btn-map');
            if (which === 'links') {{
                inv.classList.remove('hidden'); net.classList.add('topo-map-hidden');
                bl.classList.add('active'); bm.classList.remove('active');
            }} else {{
                inv.classList.add('hidden'); net.classList.remove('topo-map-hidden');
                bm.classList.add('active'); bl.classList.remove('active');
                if (window.topoNetwork) window.topoNetwork.fit({{ animation: false }});
            }}
        }}

        {embed_link_inventory_render_js()}
        if (typeof nstMarkScale === 'function') nstMarkScale(nodes.length);
        function renderLinkTable() {{
            var tb = document.getElementById('link-tbody');
            tb.innerHTML = '';
            (window.__TOPO_LINKS__ || []).forEach(function(r, idx) {{
                var tr = document.createElement('tr');
                tr.dataset.search = [r.from,r.local_port,r.to,r.remote_port,r.protocol,r.trust_tier||'',(r.sources||[]).join(' ')].join(' ').toLowerCase();
                if (r.relation_key) tr.setAttribute('data-relation-key', r.relation_key);
                tr.innerHTML = topoRenderLinkRow(r, idx);
                tb.appendChild(tr);
            }});
        }}
        var topoSortCol = 0, topoSortAsc = true;
        function topoSortTable(col) {{
            if (topoSortCol === col) topoSortAsc = !topoSortAsc;
            else {{ topoSortCol = col; topoSortAsc = true; }}
            var keys = ['from','local_port','to','remote_port','protocol','vlan','trust_tier','sources'];
            var k = keys[col];
            window.__TOPO_LINKS__.sort(function(a,b) {{
                var va=(a[k]||'').toString(), vb=(b[k]||'').toString();
                if (va<vb) return topoSortAsc?-1:1;
                if (va>vb) return topoSortAsc?1:-1;
                return 0;
            }});
            renderLinkTable(); topoApplySearch(document.getElementById('topo-search-input').value);
        }}
        renderLinkTable();

        function topoNodeHaystack(n) {{
            return [n.id,n.label,n.ip,n.platform,n.vpc_domain_id,n.title].join(' ').toLowerCase();
        }}
        function topoEdgeHaystack(e) {{
            return [e.label,e.from,e.to,e.f_port,e.t_port,e.protocol,e.title,e.type].join(' ').toLowerCase();
        }}
        {topo_search_helpers_js()}
        function topoApplySearch(q) {{
            q = (q||'').trim().toLowerCase();
            topoApplyNodeEdgeFocus(q, topoAllNodeIds, topoAllEdgeIds);
            var trs = document.querySelectorAll('#link-tbody tr');
            var vis=0;
            trs.forEach(function(tr) {{
                var ok = !q || (tr.dataset.search||'').indexOf(q)>=0;
                tr.style.display = ok ? '' : 'none';
                if (ok) vis++;
            }});
            document.getElementById('topo-search-count').textContent =
                q ? (vis+' links, filter: '+q) : '';
        }}

        var container = document.getElementById('mynetwork');
        window.topoNetwork = new vis.Network(container, {{ nodes: nodes, edges: edges }}, {{
            physics: {{ enabled: false }},
            nodes: {{ font: {{ size: 12, face: 'system-ui' }} }},
            edges: {{ font: {{ size: 9, face: 'system-ui', align: 'middle' }} }},
            interaction: {{ hover: true }}
        }});

        function showAdj(nodeId) {{
            var html = '';
            edges.forEach(function(e) {{
                if (e.from === nodeId) html += '<div><b>→ '+e.to+'</b> '+(e.f_port||'')+' ('+(e.protocol||e.type||'')+')</div>';
                if (e.to === nodeId) html += '<div><b>← '+e.from+'</b> '+(e.t_port||'')+' ('+(e.protocol||e.type||'')+')</div>';
            }});
            document.getElementById('node-adj').innerHTML = html || '<div>No links</div>';
        }}
        window.topoNetwork.on('selectNode', function(params) {{
            var nd = nodes.get(params.nodes[0]);
            if (!nd) return;
            document.getElementById('node-name').textContent = nd.id;
            document.getElementById('node-ip').textContent = nd.ip || '—';
            var extra = (nd.os_family || '') + (nd.device_type ? ' (' + nd.device_type + ')' : '');
            if (!extra.trim()) extra = nd.platform || nd.title || '—';
            document.getElementById('node-extra').textContent = extra;
            document.getElementById('topo-detail-card').style.display = 'block';
            showAdj(nd.id);
            var why = document.getElementById('nst-why-link');
            if (why) why.textContent = 'Selected ' + nd.id + ' — Blast radius for 1-hop impact.';
        }});
        window.topoNetwork.on('selectEdge', function(params) {{
            if (window._nstSyncSelecting) return;
            if (!params.edges.length) return;
            nstWhyThisLink(edges.get(params.edges[0]));
        }});
        window.topoNetwork.on('deselectNode', function() {{
            document.getElementById('topo-detail-card').style.display = 'none';
        }});
        nstStartFreshnessClock({script_safe_json(ts)});
    </script>
</body>
</html>"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)


def embed_link_inventory_html(links_hidden=False, map_hidden=False, map_default=False):
    """HTML fragment for unified Link Inventory + Map tabs (report_formatter / vPC)."""
    if map_default:
        links_hidden = True
        map_hidden = False
    inv_cls = 'hidden' if links_hidden else ''
    net_cls = 'topo-map-hidden' if map_hidden else ''
    links_active = '' if links_hidden else 'active'
    map_active = 'active' if map_default or links_hidden else ''
    return f"""
  <div class="topo-view-tabs" id="topo-shell-tabs">
    <button type="button" id="tab-btn-links" class="{links_active}" onclick="topoViewTab('links')">Link Inventory</button>
    <button type="button" id="tab-btn-map" class="{map_active}" onclick="topoViewTab('map')">Topology Map</button>
    <span id="topo-search-count" style="font-size:11px;color:#94a3b8;margin-left:12px;"></span>
  </div>
  <div id="topo-link-inventory" class="{inv_cls}" style="flex:1;overflow:auto;min-height:200px;">
    <div class="topo-inv-hint">Every L2 adjacency in this run — click column headers to sort. Trust badges show CDP/vPC validation level.</div>
    <div class="topo-search-bar">
      <span style="font-size:12px;font-weight:600;">Filter:</span>
      <input type="text" id="topo-search-input" placeholder="device, port, VLAN, trust tier…"
        oninput="topoApplySearch(this.value)" />
    </div>
    <table class="topo-inv-table" style="width:100%;">
      <thead><tr>
        <th onclick="topoSortTable(0)">From</th>
        <th onclick="topoSortTable(1)">Local Port</th>
        <th onclick="topoSortTable(2)">To</th>
        <th onclick="topoSortTable(3)">Remote Port</th>
        <th onclick="topoSortTable(4)">Type</th>
        <th onclick="topoSortTable(5)">VLAN</th>
        <th onclick="topoSortTable(6)">Trust</th>
        <th onclick="topoSortTable(7)">Evidence</th>
        <th>Inspect</th>
      </tr></thead>
      <tbody id="link-tbody"></tbody>
    </table>
  </div>
"""
