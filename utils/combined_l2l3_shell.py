"""
utils/combined_l2l3_shell.py
------------------------------
Combined L2+L3 topology HTML shell (Vis.js, no CDN).
Overlays routing (L3) on physical topology (L2) with correlation visualization.

Features:
  - Physical links (CDP/LLDP) shown as solid lines
  - Logical routing paths shown as dashed/colored lines
  - Correlation indicators showing which L3 paths traverse which L2 links
  - Layer toggle buttons to show/hide L2 or L3
  - Protocol-aware edge styling
  - Gateway device highlighting
  - Interactive node click: shows per-node detail panel (L2 neighbors + L3 routes)
"""
from __future__ import annotations

import json
from typing import Any, Dict

from utils.topo_map_shell import load_vis_script, read_version_label, shell_css, load_app_logo_data_uri, script_safe_json


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

def combined_l2l3_css() -> str:
    return """
body.combined-l2l3-map {
  background: #0f172a !important;
  color: #e2e8f0 !important;
  height: 100vh; margin: 0;
  display: flex; flex-direction: column; overflow: hidden;
  font-family: system-ui, 'Segoe UI', sans-serif;
}
body.combined-l2l3-map header {
  background: #1e293b;
  border-bottom: 1px solid #334155;
  padding: 12px 20px; display: flex; align-items: center; gap: 16px;
}
body.combined-l2l3-map header .combined-brand-logo {
  width: 36px; height: 36px; border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.35);
}
body.combined-l2l3-map header h1 { margin: 0; font-size: 18px; color: #f1f5f9; flex: 1; }
body.combined-l2l3-map header p  { margin: 0; font-size: 11px; color: #94a3b8; }
.layer-badge {
  display: inline-block; padding: 2px 7px; border-radius: 4px;
  font-size: 10px; font-weight: 700; letter-spacing: .03em; margin-right: 4px;
}
.layer-l2 { background: #10b981; color: #ffffff; }
.layer-l3 { background: #3b82f6; color: #ffffff; }
.layer-both { background: #8b5cf6; color: #ffffff; }
.combined-device-card {
  background: #0f172a; border: 1px solid #334155; border-radius: 8px;
  padding: 8px 10px; margin-bottom: 8px;
}
.combined-device-card b { color: #e2e8f0; font-size: 12px; }
.combined-device-card .combined-device-meta { font-size: 10px; color: #94a3b8; margin-top: 4px; line-height: 1.5; }
.combined-toolbar {
  display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
  padding: 8px 16px; background: #1e293b; border-bottom: 1px solid #334155;
}
.combined-toolbar input[type=text] {
  background: #0f172a; border: 1px solid #475569; color: #e2e8f0;
  padding: 5px 10px; border-radius: 6px; font-size: 12px; width: 180px;
}
.combined-toolbar input[type=text]:focus { outline: none; border-color: #818cf8; }
.combined-toolbar button {
  background: #334155; border: 1px solid #475569; color: #cbd5e1;
  padding: 5px 12px; border-radius: 6px; font-size: 12px; cursor: pointer;
  transition: all 0.2s;
}
.combined-toolbar button:hover { background: #475569; color: #f1f5f9; }
.combined-toolbar button.active { background: #4f46e5; border-color: #6366f1; color: #fff; }
.combined-toolbar button.layer-l2-btn.active { background: #10b981; border-color: #059669; }
.combined-toolbar button.layer-l3-btn.active { background: #3b82f6; border-color: #2563eb; }
.combined-stats {
  display: flex; flex-wrap: wrap; gap: 8px; padding: 8px 16px;
  background: #0f172a; border-bottom: 1px solid #1e293b;
}
.combined-stat {
  background: #1e293b; border: 1px solid #334155;
  border-radius: 8px; padding: 6px 14px; font-size: 12px; min-width: 80px;
}
.combined-stat b { color: #38bdf8; font-size: 18px; display: block; line-height: 1.2; }
.combined-legend {
  display: flex; flex-wrap: wrap; gap: 6px; padding: 6px 16px;
  background: #1e293b; border-bottom: 1px solid #334155; font-size: 11px;
}
.combined-legend-item {
  display: flex; align-items: center; gap: 5px;
  padding: 3px 8px; border-radius: 5px; background: #0f172a; cursor: pointer;
  border: 1px solid transparent; user-select: none;
}
.combined-legend-item:hover { border-color: #475569; }
.combined-legend-dot { width: 10px; height: 10px; border-radius: 50%; }
.combined-legend-physical .combined-legend-dot { background: #10b981; }
.combined-legend-logical .combined-legend-dot { background: #3b82f6; }
.combined-legend-correlated .combined-legend-dot { background: #8b5cf6; }
/* ─── CRITICAL: main must grow to fill remaining viewport height ──── */
main.combined-map-main {
  display: flex; flex-direction: column; flex: 1 1 0%; overflow: hidden;
  min-height: 0;
}
.combined-layout { display: flex; flex: 1 1 0%; min-height: 0; }
#combined-network { flex: 1; background: #060d1a; min-height: 300px; position: relative; }
.combined-side {
  width: 340px; min-width: 240px; max-width: 440px;
  overflow-y: auto; padding: 0;
  background: #111827; border-left: 1px solid #1f2937;
  display: flex; flex-direction: column;
}
.combined-side-header {
  padding: 10px 14px; background: #1e293b;
  border-bottom: 1px solid #334155; font-size: 13px; color: #a5b4fc;
  font-weight: 600; position: sticky; top: 0; z-index: 2;
}
.combined-side-section { padding: 10px 14px; border-bottom: 1px solid #1f2937; }
.combined-side-section h4 { margin: 0 0 6px; font-size: 11px; color: #64748b;
  text-transform: uppercase; letter-spacing: .05em; }
.combined-detail-panel {
  padding: 12px 14px; display: none; border-bottom: 2px solid #8b5cf6;
  background: #0d1526;
}
.combined-detail-panel.visible { display: block; }
.combined-detail-panel h3 { margin: 0 0 8px; font-size: 13px; color: #c4b5fd; }
.combined-detail-table { width: 100%; border-collapse: collapse; font-size: 11px; }
.combined-detail-table td { padding: 3px 6px; border-bottom: 1px solid #1e293b; color: #cbd5e1; }
.combined-detail-table td:first-child { color: #64748b; white-space: nowrap; }
.correlation-indicator {
  display: inline-block; padding: 2px 6px; border-radius: 4px;
  font-size: 10px; font-weight: 600; margin: 1px;
}
.correlation-yes { background: #8b5cf6; color: #ffffff; }
.correlation-no { background: #475569; color: #cbd5e1; }
.l2-neighbor-row {
  padding: 2px 0; border-bottom: 1px solid #1e293b;
  font-size: 11px; color: #94a3b8;
}
.l2-neighbor-row b { color: #10b981; }
.l3-route-row {
  padding: 2px 0; border-bottom: 1px solid #1e293b;
  font-size: 11px; color: #94a3b8; font-family: monospace;
}
.l3-route-row b { color: #3b82f6; }
"""


# ---------------------------------------------------------------------------
# JavaScript helpers
# ---------------------------------------------------------------------------

def _combined_l2l3_js(nodes_json: str, edges_json: str, correlation_json: str, map_kind: str = 'combined') -> str:
    return f"""
const RAW_NODES = {nodes_json};
const RAW_EDGES = {edges_json};
const CORRELATION = {correlation_json};

const LAYER_CLASS = {{
  'l2': 'layer-l2',
  'l3': 'layer-l3',
  'l2+l3': 'layer-both'
}};

function layerBadge(layer) {{
  const cls = LAYER_CLASS[layer] || 'layer-l2';
  return `<span class="layer-badge ${{cls}}">${{layer}}</span>`;
}}

/* ---- Vis.js setup ---- */
console.log('Combined L2+L3 Map: Starting initialization...');
console.log('RAW_NODES:', RAW_NODES);
console.log('RAW_EDGES:', RAW_EDGES);
console.log('CORRELATION:', CORRELATION);

const NODE_COLORS = {{
  switch:          {{ background:'#10b981', border:'#059669', highlight:{{ground:'#34d399',border:'#10b981'}} }},
  device:          {{ background:'#10b981', border:'#059669', highlight:{{ground:'#34d399',border:'#10b981'}} }},
  gateway:         {{ background:'#f59e0b', border:'#b45309', highlight:{{ground:'#fbbf24',border:'#d97706'}} }},
  default_gateway: {{ background:'#ef4444', border:'#b91c1c', highlight:{{ground:'#f87171',border:'#dc2626'}} }},
  subnet:          {{ background:'#8b5cf6', border:'#6d28d9', highlight:{{ground:'#a78bfa',border:'#8b5cf6'}} }},
}};

function makeVisNode(n) {{
  let col = NODE_COLORS[n.group] || NODE_COLORS.switch;
  return Object.assign({{}}, n, {{
    color: col,
    font: {{ size:12, color:'#e2e8f0', face:'Segoe UI' }},
    borderWidth: 2, shadow: true,
    title: n.title || n.label,
  }});
}}

const nodes = new vis.DataSet(RAW_NODES.map(makeVisNode));
const edges = new vis.DataSet(RAW_EDGES.map(e => ({{
  ...e,
  font: {{ size:10, align:'middle', color:'#64748b' }},
  color: {{ color:'#475569', highlight:'#818cf8' }},
  smooth: {{ type:'curvedCW', roundness:0.12 }},
}})));

const container = document.getElementById('combined-network');

if (!container) {{
  console.error('ERROR: combined-network container not found!');
  document.body.innerHTML = '<p role="alert" style="color:#f87171;padding:20px;font-family:monospace">Rendering Error: Network container not found.</p>';
}}

/* Safety net: if the flex height chain collapsed to 0, force a minimum height. */
if (container && container.offsetHeight < 10) {{
  container.style.minHeight = '600px';
  console.warn('Combined map: container had 0 height — applied 600px fallback');
}}

const network = new vis.Network(container, {{ nodes, edges }}, {{
  layout: {{
    randomSeed: 42,
    improvedLayout: true,
  }},
  physics: {{
    enabled: true,
    stabilization: {{
      iterations: 1000,
      updateInterval: 25,
    }},
    barnesHut: {{
      gravitationalConstant: -3000,
      centralGravity: 0.5,
      springLength: 150,
      springConstant: 0.08,
      damping: 0.15,
      avoidOverlap: 0.8
    }}
  }},
  interaction: {{ hover:true, tooltipDelay:150, navigationButtons:true, keyboard:true }},
  nodes: {{ 
    borderWidth: 3, 
    shadow: true,
    size: 35,
  }},
  edges: {{ width:2, selectionWidth:4 }},
}});

network.once('stabilizationIterationsDone', function() {{
  network.redraw();
  network.fit({{ animation: true }});
}});

network.on('error', function(error) {{
  console.error('Network error:', error);
}});

/* ---- Layer toggle ---- */
let showL2 = true;
let showL3 = true;

document.getElementById('btn-layer-l2').addEventListener('click', function() {{
  showL2 = !showL2;
  this.classList.toggle('active', showL2);
  updateLayerVisibility();
}});

document.getElementById('btn-layer-l3').addEventListener('click', function() {{
  showL3 = !showL3;
  this.classList.toggle('active', showL3);
  updateLayerVisibility();
}});

function updateLayerVisibility() {{
  RAW_EDGES.forEach(e => {{
    const layer = e.layer || 'l2';
    const shouldShow = (layer === 'l2' && showL2) || (layer === 'l3' && showL3);
    edges.update({{id: e.id, hidden: !shouldShow}});
  }});
}}

/* ---- Detail panel ---- */
const detailPanel = document.getElementById('detail-panel');
const detailContent = document.getElementById('detail-content');

network.on('click', function(params) {{
  if (!params.nodes.length) {{ detailPanel.classList.remove('visible'); return; }}
  const nid = params.nodes[0];
  const node = RAW_NODES.find(n => n.id === nid);
  if (!node) return;
  showDetail(nid, node);
}});

function showDetail(nid, node) {{
  let html = `<h3>${{nid}}</h3><table class="combined-detail-table">`;
  html += `<tr><td>Layer</td><td>${{layerBadge(node.layer || 'unknown')}}</td></tr>`;
  html += `<tr><td>Type</td><td>${{node.group || 'unknown'}}</td></tr>`;
  
  if (node.protocols && node.protocols.length) {{
    html += `<tr><td>Protocols</td><td>${{node.protocols.join(', ')}}</td></tr>`;
  }}
  
  html += `</table>`;
  
  // Show L2 neighbors if available
  const l2Neighbors = RAW_EDGES.filter(e => 
    (e.from === nid || e.to === nid) && e.layer === 'l2'
  );
  if (l2Neighbors.length) {{
    html += `<h4 style="color:#64748b;font-size:11px;margin:8px 0 4px;text-transform:uppercase">L2 Neighbors (Physical)</h4>`;
    l2Neighbors.forEach(e => {{
      const peer = e.from === nid ? e.to : e.from;
      html += `<div class="l2-neighbor-row"><b>${{peer}}</b> via ${{e.label}}</div>`;
    }});
  }}
  
  // Show L3 correlations if available
  const l3Edges = RAW_EDGES.filter(e => 
    (e.from === nid || e.to === nid) && e.layer === 'l3'
  );
  if (l3Edges.length) {{
    html += `<h4 style="color:#64748b;font-size:11px;margin:8px 0 4px;text-transform:uppercase">L3 Routes (Logical)</h4>`;
    l3Edges.forEach(e => {{
      const peer = e.from === nid ? e.to : e.from;
      const physLink = e.physical_link ? `<span class="correlation-indicator correlation-yes">via ${{e.physical_link}}</span>` : '';
      html += `<div class="l3-route-row"><b>${{peer}}</b> ${{e.label}} ${{physLink}}</div>`;
    }});
  }}
  
  detailContent.innerHTML = html;
  detailPanel.classList.add('visible');
}}

/* ---- Search ---- */
document.getElementById('search-input').addEventListener('input', function() {{
  const q = this.value.trim().toLowerCase();
  if (!q) {{ nodes.forEach(n => nodes.update({{id:n.id,opacity:1}})); return; }}
  RAW_NODES.forEach(n => {{
    const match = (n.label||'').toLowerCase().includes(q) || (n.id+'').toLowerCase().includes(q);
    nodes.update({{id:n.id, opacity: match?1:0.15}});
  }});
}});

document.getElementById('btn-fit').addEventListener('click', () => network.fit({{animation:true}}));
document.getElementById('btn-reset').addEventListener('click', () => {{
  nodes.forEach(n => nodes.update({{id:n.id,opacity:1}}));
  document.getElementById('search-input').value='';
  detailPanel.classList.remove('visible');
  showL2 = true; showL3 = true;
  document.getElementById('btn-layer-l2').classList.add('active');
  document.getElementById('btn-layer-l3').classList.add('active');
  updateLayerVisibility();
  network.fit({{animation:true}});
}});
"""


# ---------------------------------------------------------------------------
# Render combined L2+L3 HTML
# ---------------------------------------------------------------------------

def render_combined_l2l3_html(
    combined_bundle: Dict[str, Any],
    title: str = 'Combined L2+L3 Topology',
    subtitle: str = '',
    map_kind: str = 'combined',
) -> str:
    """Render complete offline HTML for combined L2+L3 topology map."""
    nodes_json = script_safe_json(combined_bundle.get('nodes') or [])
    edges_json = script_safe_json(combined_bundle.get('edges') or [])
    correlation_json = script_safe_json(combined_bundle.get('correlation') or {})
    analysis = combined_bundle.get('analysis') or {}
    
    version = read_version_label()
    logo_uri = load_app_logo_data_uri()
    logo_html = (
        f"<img class='combined-brand-logo' src='{logo_uri}' alt='Network Swiss Tool Pro'>"
        if logo_uri else ''
    )
    
    n_nodes = analysis.get('total_nodes', 0)
    n_edges = analysis.get('total_edges', 0)
    n_l2_edges = analysis.get('l2_edge_count', 0)
    n_l3_edges = analysis.get('l3_edge_count', 0)
    n_correlated = analysis.get('correlated_edges', 0)
    n_gateways = analysis.get('gateway_count', 0)
    
    legend_html = ''.join(
        f"<div class='combined-legend-item combined-legend-{cls}'>"
        f"<div class='combined-legend-dot'></div>{lbl}</div>"
        for lbl, cls in [
            ('Physical (L2)', 'physical'),
            ('Logical (L3)', 'logical'),
            ('Correlated', 'correlated'),
        ]
    )
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{title} — Network Swiss Tool Pro {version}</title>
  {load_vis_script()}
  <style>{shell_css()}{combined_l2l3_css()}</style>
</head>
<body class="combined-l2l3-map">
  <header>
    {logo_html}
    <div>
      <h1>{title}</h1>
      <p>Combined Physical + Logical Topology · {subtitle} · Offline · {version}</p>
    </div>
  </header>

  <main class="combined-map-main">

  <div class="combined-toolbar">
    <input type="text" id="search-input" placeholder="Search node…" autocomplete="off">
    <button id="btn-layer-l2" class="layer-l2-btn active">L2 (Physical)</button>
    <button id="btn-layer-l3" class="layer-l3-btn active">L3 (Logical)</button>
    <button id="btn-fit">Fit all</button>
    <button id="btn-reset">Reset</button>
    <span style="color:#475569;font-size:11px;margin-left:8px">Click a node for details →</span>
  </div>

  <div class="combined-stats">
    <div class="combined-stat"><b>{n_nodes}</b>Nodes</div>
    <div class="combined-stat"><b>{n_edges}</b>Total Edges</div>
    <div class="combined-stat"><b>{n_l2_edges}</b>L2 Links</div>
    <div class="combined-stat"><b>{n_l3_edges}</b>L3 Routes</div>
    <div class="combined-stat"><b>{n_correlated}</b>Correlated</div>
    <div class="combined-stat"><b>{n_gateways}</b>Gateways</div>
  </div>

  <div class="combined-legend">{legend_html}</div>

  <div class="combined-layout">
    <div id="combined-network"></div>
    <div class="combined-side">
      <div class="combined-detail-panel" id="detail-panel">
        <div id="detail-content"></div>
      </div>
      <div class="combined-side-header">Topology Summary</div>
      <div class="combined-side-section">
        <h4>Physical Layer (L2)</h4>
        <div style="font-size:11px;color:#94a3b8">
          CDP/LLDP neighbor discovery<br>
          {n_l2_edges} physical links detected
        </div>
      </div>
      <div class="combined-side-section">
        <h4>Logical Layer (L3)</h4>
        <div style="font-size:11px;color:#94a3b8">
          Routing table analysis<br>
          {n_l3_edges} logical paths<br>
          {n_correlated} correlated with physical links
        </div>
      </div>
      <div class="combined-side-section">
        <h4>Gateways</h4>
        <div style="font-size:11px;color:#94a3b8">
          {n_gateways} gateway devices detected
        </div>
      </div>
    </div>
  </div>
  </main>

  <script>
  document.addEventListener('DOMContentLoaded', function() {{
    {_combined_l2l3_js(nodes_json, edges_json, correlation_json, map_kind)}
  }});
  </script>
</body>
</html>"""
