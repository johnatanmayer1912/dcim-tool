# ============================================================================
# AI_NAVIGATION_BREADCRUMBS - utils/l3_map_shell.py
# ============================================================================
# PURPOSE:
#   Offline L3 / Flow Routing Map HTML Shell (Vis.js, zero external CDN dependencies).
#   Renders Layer 3 topology graphs, subnet boundaries, gateway detectors,
#   and includes an interactive client-side and API-backed End-to-End Path Tracer.
#
# ARCHITECTURAL ROLE:
#   Primary visualization presentation tier for L3 routing analysis.
#   Generates standalone HTML files stored in outputs/plugins/.../l3_topology_map.html.
#
# KEY FUNCTIONS:
#   - render_l3_map_html(vis_payload, title, subtitle, map_kind): HTML generator
#   - _l3_js(...): JavaScript driver with physics stabilization and Path Tracer
#   - l3_map_css(): Scoped dark-theme styling with high-contrast accessibility
#
# CONNECTIONS:
#   - Called by: modules/l3_topology_runner.py, vlan_checker_web.py
#   - Consumes: utils/topo_map_shell.py, modules/routing_analyzer/path_tracer.py
#   - Visualizes: Normalized routing bundles from collector/parser/normalizer
#
# INVARIANTS:
#   - 100% Offline: Zero external CDN script tags; Vis.js is inlined/bundled.
#   - Honest Metadata: Clearly states overlay vs underlay status in header.
# ============================================================================
from __future__ import annotations

import html
import json
from typing import Any, Dict


from utils.topo_map_shell import (
    load_vis_script, read_version_label, shell_css, topo_search_helpers_js,
    load_app_logo_data_uri, layer_switch_html, script_safe_json,
    embed_link_inventory_render_js,
)


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

def l3_map_css() -> str:
    from utils.map_shell_theme import enterprise_map_css
    return enterprise_map_css() + """
body.l3-routing-map {
  background: #0f172a !important;
  color: #e2e8f0 !important;
  height: 100vh; margin: 0;
  display: flex; flex-direction: column; overflow: hidden;
  font-family: var(--nst-map-font), system-ui, sans-serif;
}
body.l3-routing-map header {
  background: #1e293b;
  border-bottom: 1px solid #334155;
  padding: 12px 20px; display: flex; align-items: center; gap: 16px;
}
body.l3-routing-map header .l3-brand-logo {
  width: 36px; height: 36px; border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.35);
}
body.l3-routing-map header h1 { margin: 0; font-size: 18px; color: #f1f5f9; flex: 1; }
body.l3-routing-map header p  { margin: 0; font-size: 11px; color: #94a3b8; }
.l3-vendor-badge {
  display: inline-block; padding: 2px 7px; border-radius: 4px;
  font-size: 10px; font-weight: 700; letter-spacing: .03em; margin-right: 4px;
}
/* Secure Cartography vendor colors */
.l3-vendor-cisco   { background: #00bceb; color: #ffffff; }
.l3-vendor-juniper { background: #f97316; color: #ffffff; }
.l3-vendor-arista  { background: #22c55e; color: #ffffff; }
.l3-vendor-ios    { background: #1d4ed8; color: #bfdbfe; }
.l3-vendor-iosxe  { background: #2563eb; color: #dbeafe; }
.l3-vendor-nxos   { background: #0891b2; color: #cffafe; }
.l3-vendor-other  { background: #475569; color: #e2e8f0; }
.l3-device-card {
  background: #0f172a; border: 1px solid #334155; border-radius: 8px;
  padding: 8px 10px; margin-bottom: 8px;
}
.l3-device-card b { color: #e2e8f0; font-size: 12px; }
.l3-device-card .l3-device-meta { font-size: 10px; color: #94a3b8; margin-top: 4px; line-height: 1.5; }
.l3-toolbar {
  display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
  padding: 8px 16px; background: #1e293b; border-bottom: 1px solid #334155;
}
.l3-toolbar input[type=text] {
  background: #0f172a; border: 1px solid #475569; color: #e2e8f0;
  padding: 5px 10px; border-radius: 6px; font-size: 12px; width: 180px;
}
.l3-toolbar input[type=text]:focus { outline: none; border-color: #818cf8; }
.l3-toolbar button {
  background: #334155; border: 1px solid #475569; color: #cbd5e1;
  padding: 5px 12px; border-radius: 6px; font-size: 12px; cursor: pointer;
  transition: all 0.2s;
}
.l3-toolbar button:hover { background: #475569; color: #f1f5f9; }
.l3-toolbar button.active { background: #4f46e5; border-color: #6366f1; color: #fff; }
.l3-toolbar button.flow-active { background: #10b981; border-color: #059669; color: #fff; }
.l3-trace-bar {
  display: flex; align-items: center; gap: 8px; margin-left: auto;
  background: #0f172a; padding: 4px 10px; border-radius: 8px; border: 1px solid #334155;
}
.l3-trace-bar input[type=text] {
  width: 140px; padding: 4px 8px; font-size: 11px; background: #1e293b;
}
.l3-trace-bar button.flow-btn {
  background: #0ea5e9; border-color: #0284c7; color: #fff; font-weight: 700;
}
.l3-trace-bar button.flow-btn:hover { background: #38bdf8; }
.l3-hop-card {
  background: #0f172a; border: 1px solid #334155; border-left: 3px solid #38bdf8;
  border-radius: 6px; padding: 8px 10px; margin-bottom: 6px; font-size: 11px;
}
.l3-hop-card.ingress { border-left-color: #10b981; }
.l3-hop-card.delivered { border-left-color: #22c55e; }
.l3-hop-card.loop { border-left-color: #ef4444; }
.l3-hop-head { font-weight: 700; color: #f1f5f9; display: flex; justify-content: space-between; }
.l3-hop-sub { color: #94a3b8; font-size: 10px; margin-top: 3px; font-family: monospace; }
.l3-stats {
  display: flex; flex-wrap: wrap; gap: 8px; padding: 8px 16px;
  background: #0f172a; border-bottom: 1px solid #1e293b;
}
.l3-stat {
  background: #1e293b; border: 1px solid #334155;
  border-radius: 8px; padding: 6px 14px; font-size: 12px; min-width: 80px;
}
.l3-stat b { color: #38bdf8; font-size: 18px; display: block; line-height: 1.2; }
.l3-legend {
  display: flex; flex-wrap: wrap; gap: 6px; padding: 6px 16px;
  background: #1e293b; border-bottom: 1px solid #334155; font-size: 11px;
}
.l3-legend-item {
  display: flex; align-items: center; gap: 5px;
  padding: 3px 8px; border-radius: 5px; background: #0f172a; cursor: pointer;
  border: 1px solid transparent; user-select: none;
}
.l3-legend-item:hover { border-color: #475569; }
.l3-legend-dot { width: 10px; height: 10px; border-radius: 50%; }
/* Secure Cartography legend colors */
.l3-legend-cisco   .l3-legend-dot { background: #00bceb; }
.l3-legend-juniper .l3-legend-dot { background: #f97316; }
.l3-legend-arista  .l3-legend-dot { background: #22c55e; }
.l3-legend-gateway .l3-legend-dot { background: #f59e0b; }
.l3-legend-default-gw .l3-legend-dot { background: #ef4444; }
.l3-legend-subnet .l3-legend-dot { background: #8b5cf6; }
/* ─── Protocol filter bar ──────────────────────────────────── */
.l3-proto-filter {
  display: flex; flex-wrap: wrap; gap: 5px; align-items: center;
  padding: 6px 14px; background: #0f172a; border-bottom: 1px solid #1e293b;
}
.l3-proto-filter label { font-size: 10px; color: #475569; font-weight: 700;
  text-transform: uppercase; letter-spacing: .06em; margin-right: 2px; }
.l3-proto-btn {
  padding: 3px 9px; border-radius: 4px; border: 1px solid #334155;
  background: #1e293b; color: #64748b; font-size: 11px; font-weight: 600;
  cursor: pointer; display: inline-flex; align-items: center; gap: 4px;
  transition: all .12s;
}
.l3-proto-btn:hover { border-color: #475569; color: #94a3b8; }
.l3-proto-btn.on { color: #f1f5f9; }
.l3-proto-btn.on.ospf   { border-color: #3b82f6; background: rgba(59,130,246,.15); color: #93c5fd; }
.l3-proto-btn.on.bgp    { border-color: #ef4444; background: rgba(239,68,68,.12);  color: #fca5a5; }
.l3-proto-btn.on.eigrp  { border-color: #8b5cf6; background: rgba(139,92,246,.12); color: #c4b5fd; }
.l3-proto-btn.on.static { border-color: #f59e0b; background: rgba(245,158,11,.12); color: #fde68a; }
.l3-proto-btn.on.conn   { border-color: #10b981; background: rgba(16,185,129,.12); color: #86efac; }
.l3-proto-btn.on.isis   { border-color: #06b6d4; background: rgba(6,182,212,.12);  color: #67e8f9; }
.l3-proto-dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
.l3-proto-dot.ospf   { background: #3b82f6; }
.l3-proto-dot.bgp    { background: #ef4444; }
.l3-proto-dot.eigrp  { background: #8b5cf6; }
.l3-proto-dot.static { background: #f59e0b; }
.l3-proto-dot.conn   { background: #10b981; }
.l3-proto-dot.isis   { background: #06b6d4; }
/* ─── CRITICAL: main must grow to fill remaining viewport height ──── */
main.l3-map-main {
  display: flex; flex-direction: column; flex: 1 1 0%; overflow: hidden;
  min-height: 0;
}
.l3-layout { display: flex; flex: 1 1 0%; min-height: 0; }
#l3-network { flex: 1; background: #060d1a; min-height: 300px; position: relative; }
.l3-side {
  width: 320px; min-width: 220px; max-width: 420px;
  overflow-y: auto; padding: 0;
  background: #111827; border-left: 1px solid #1f2937;
  display: flex; flex-direction: column;
}
.l3-side-header {
  padding: 10px 14px; background: #1e293b;
  border-bottom: 1px solid #334155; font-size: 13px; color: #a5b4fc;
  font-weight: 600; position: sticky; top: 0; z-index: 2;
}
.l3-side-section { padding: 10px 14px; border-bottom: 1px solid #1f2937; }
.l3-side-section h4 { margin: 0 0 6px; font-size: 11px; color: #64748b;
  text-transform: uppercase; letter-spacing: .05em; }
.l3-detail-panel {
  padding: 12px 14px; display: none; border-bottom: 2px solid #4f46e5;
  background: #0d1526;
}
.l3-detail-panel.visible { display: block; }
.l3-detail-panel h3 { margin: 0 0 8px; font-size: 13px; color: #c4b5fd; }
.l3-detail-table { width: 100%; border-collapse: collapse; font-size: 11px; }
.l3-detail-table td { padding: 3px 6px; border-bottom: 1px solid #1e293b; color: #cbd5e1; }
.l3-detail-table td:first-child { color: #64748b; white-space: nowrap; }
.l3-badge {
  display: inline-block; padding: 2px 6px; border-radius: 4px;
  font-size: 10px; font-weight: 600; margin: 1px;
}
.proto-ospf    { background: #1d4ed8; color: #bfdbfe; }
.proto-bgp     { background: #065f46; color: #a7f3d0; }
.proto-eigrp   { background: #7c3aed; color: #ddd6fe; }
.proto-static  { background: #92400e; color: #fde68a; }
.proto-connect { background: #166534; color: #bbf7d0; }
.proto-isis    { background: #9f1239; color: #fecdd3; }
.proto-rip     { background: #44403c; color: #d6d3d1; }
.proto-other   { background: #334155; color: #cbd5e1; }
.l3-failed { color: #f87171; font-size: 11px; padding: 4px 0; }
.l3-route-row {
  padding: 3px 0; border-bottom: 1px solid #1e293b;
  font-size: 11px; color: #94a3b8; font-family: monospace;
}
.l3-route-row b { color: #e2e8f0; }
"""


# ---------------------------------------------------------------------------
# JavaScript helpers
# ---------------------------------------------------------------------------

def _l3_js(nodes_json: str, edges_json: str, devices_json: str,
            gateways_json: str, subnets_json: str, all_routes_json: str, map_kind: str = 'l3') -> str:
    return f"""
const RAW_NODES    = {nodes_json};
const RAW_EDGES    = {edges_json};
const DEVICES_META = {devices_json};
const GW_META      = {gateways_json};
const SN_META      = {subnets_json};
const ALL_ROUTES   = {all_routes_json};

const PROTO_CLASS = {{
  'OSPF':'proto-ospf','OSPF-InterArea':'proto-ospf','OSPF-Ext1':'proto-ospf','OSPF-Ext2':'proto-ospf',
  'BGP':'proto-bgp','EIGRP':'proto-eigrp','EIGRP-External':'proto-eigrp',
  'Static':'proto-static','Connected':'proto-connect','Local':'proto-connect',
  'ISIS':'proto-isis','RIP':'proto-rip',
}};
function protoBadge(p) {{
  const cls = PROTO_CLASS[p] || 'proto-other';
  return `<span class="l3-badge ${{cls}}">${{p}}</span>`;
}}
function vendorBadge(platform) {{
  const p = (platform || '').toLowerCase();
  if (p.includes('junos') || p.includes('juniper'))
    return `<span class="l3-vendor-badge l3-vendor-juniper">Juniper</span>`;
  if (p.includes('arista'))
    return `<span class="l3-vendor-badge l3-vendor-arista">Arista</span>`;
  if (p.includes('nxos') || p.includes('nexus'))
    return `<span class="l3-vendor-badge l3-vendor-nxos">NX-OS</span>`;
  if (p.includes('xe'))
    return `<span class="l3-vendor-badge l3-vendor-iosxe">IOS-XE</span>`;
  if (p.includes('ios') || p.includes('cisco'))
    return `<span class="l3-vendor-badge l3-vendor-cisco">Cisco</span>`;
  return `<span class="l3-vendor-badge l3-vendor-other">${{platform || 'Device'}}</span>`;
}}
function ifaceListHtml(interfaces) {{
  const entries = Object.entries(interfaces || {{}});
  if (!entries.length) return '';
  let html = `<h4 style="color:#64748b;font-size:11px;margin:8px 0 4px;text-transform:uppercase">Interfaces</h4>`;
  entries.slice(0, 20).forEach(([iface, subnet]) => {{
    html += `<div class="l3-route-row"><b>${{iface}}</b> → ${{subnet}}</div>`;
  }});
  return html;
}}

/* ---- Vis.js setup ---- */
console.log('L3 Map: Starting initialization...');
console.log('RAW_NODES:', RAW_NODES);
console.log('RAW_EDGES:', RAW_EDGES);
console.log('vis available:', typeof vis !== 'undefined');

// Secure Cartography-inspired vendor colors
function getVendorColor(platform) {{
  const p = (platform || '').toLowerCase();
  if (p.includes('cisco')) return {{ background:'#00bceb', border:'#0085a3', highlight:{{ground:'#33d6ff',border:'#00bceb'}} }};
  if (p.includes('juniper')) return {{ background:'#f97316', border:'#c2410c', highlight:{{ground:'#fb923c',border:'#f97316'}} }};
  if (p.includes('arista')) return {{ background:'#22c55e', border:'#15803d', highlight:{{ground:'#4ade80',border:'#22c55e'}} }};
  return {{ background:'#64748b', border:'#475569', highlight:{{ground:'#94a3b8',border:'#64748b'}} }};
}}

const NODE_COLORS = {{
  device:          {{ background:'#00bceb', border:'#0085a3', highlight:{{background:'#33d6ff',border:'#00bceb'}} }},
  gateway:         {{ background:'#f59e0b', border:'#b45309', highlight:{{background:'#fbbf24',border:'#d97706'}} }},
  default_gateway: {{ background:'#ef4444', border:'#b91c1c', highlight:{{background:'#f87171',border:'#dc2626'}} }},
  subnet:          {{ background:'#8b5cf6', border:'#6d28d9', highlight:{{background:'#a78bfa',border:'#8b5cf6'}} }},
}};

function makeVisNode(n) {{
  let col;
  if (n.group === 'device') {{
    col = getVendorColor(n.platform);
  }} else {{
    col = NODE_COLORS[n.group] || NODE_COLORS.device;
  }}
  const vis_node = Object.assign({{}}, n, {{
    color: col,
    font: {{ size:12, color:'#e2e8f0', face:'Segoe UI' }},
    borderWidth: 2, shadow: true,
    title: n.title || n.label,
  }});
  // Node shapes encode device role (Finding #9)
  if (n.group === 'device' && n.role) {{
    const role = (n.role || '').toLowerCase();
    if (role === 'core') {{
      vis_node.shape = 'hexagon';
    }} else if (role === 'distribution' || role === 'dist') {{
      vis_node.shape = 'diamond';
    }} else if (role === 'access') {{
      vis_node.shape = 'box';
    }} else if (role === 'edge') {{
      vis_node.shape = 'triangle';
    }}
  }}
  // Preserve ghost-node visual treatment (borderDashes and opacity set by graph_builder)
  if (n._ghost) {{
    vis_node.borderWidth = 1;
    vis_node.shapeProperties = {{ borderDashes: [5, 5] }};
    if (n.opacity !== undefined) vis_node.opacity = n.opacity;
  }}
  if (n.borderDashes) {{
    vis_node.shapeProperties = {{ borderDashes: n.borderDashes }};
  }}
  return vis_node;
}}

const nodes = new vis.DataSet(RAW_NODES.map(makeVisNode));
const edges = new vis.DataSet(RAW_EDGES.map(e => ({{
  ...e,
  font: {{ size:10, align:'middle', color:'#64748b' }},
  color: {{ color:'#475569', highlight:'#818cf8' }},
  smooth: {{ type:'curvedCW', roundness:0.12 }},
}})));

const container = document.getElementById('l3-network');
console.log('Container dimensions:', container ? container.offsetWidth + 'x' + container.offsetHeight : 'not found');

if (!container) {{
  console.error('ERROR: l3-network container not found!');
  document.body.innerHTML = '<p role="alert" style="color:#f87171;padding:20px;font-family:monospace">Rendering Error: Network container not found. This is a layout bug — report it.</p>';
}}

/* Safety net: if the flex height chain collapsed to 0, force a minimum height.
   This ensures vis.js always gets a visible canvas even in edge-case browser modes. */
if (container && container.offsetHeight < 10) {{
  container.style.minHeight = '600px';
  console.warn('L3 map: container had 0 height — applied 600px fallback (CSS flex chain issue)');
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
  interaction: {{ hover:true, tooltipDelay:150, navigationButtons:true, keyboard:true, hoverTooltips:false }},
  nodes: {{ 
    borderWidth: 3, 
    shadow: true,
    size: 35,
  }},
  edges: {{ width:2, selectionWidth:4 }},
}});
window.network = network;
window.nodes = nodes;
window.edges = edges;
network.on('selectEdge', function(params) {{
  if (!params.edges.length) return;
  nstWhyThisLink(edges.get(params.edges[0]));
}});

// Fit the network to view all nodes after initialization
network.once('stabilizationIterationsDone', function() {{
  console.log('Stabilization done, fitting network...');
  /* Force redraw in case the container was initially 0px and then resized */
  network.redraw();
  network.fit({{ animation: true }});
}});

// Add error handler
network.on('error', function(error) {{
  console.error('Network error:', error);
}});

/* ---- Detail panel ---- */
const detailPanel = document.getElementById('detail-panel');
const detailContent = document.getElementById('detail-content');

// Finding #11: Custom hover tooltip
const customTooltip = document.createElement('div');
customTooltip.className = 'l3-custom-tooltip';
customTooltip.style.cssText = 'position:absolute;background:#1e293b;border:1px solid #334155;border-radius:6px;padding:8px 12px;color:#f1f5f9;font-size:11px;pointer-events:none;z-index:1000;display:none;box-shadow:0 4px 12px rgba(0,0,0,0.4);max-width:280px;';
document.body.appendChild(customTooltip);

network.on('hoverNode', function(params) {{
  if (!params.node) {{
    customTooltip.style.display = 'none';
    return;
  }}
  const node = params.node;
  let tooltipHtml = `<strong style="color:#93c5fd;font-size:12px">${{topoEsc(node.label || node.id)}}</strong>`;
  if (node.group === 'device') {{
    const m = DEVICES_META[node.id] || {{}};
    if (m.platform) tooltipHtml += `<br><span style="color:#94a3b8">Platform:</span> ${{topoEsc(m.platform)}}`;
    if (m.management_ip) tooltipHtml += `<br><span style="color:#94a3b8">Mgmt IP:</span> ${{topoEsc(m.management_ip)}}`;
    if (m.role) tooltipHtml += `<br><span style="color:#94a3b8">Role:</span> ${{topoEsc(m.role)}}`;
  }} else if (node.group === 'subnet') {{
    const m = SN_META[node.id] || {{}};
    if (m.prefix_len) tooltipHtml += `<br><span style="color:#94a3b8">Prefix:</span> /${{topoEsc(String(m.prefix_len))}}`;
    if (m.is_private !== undefined) tooltipHtml += `<br><span style="color:#94a3b8">Private:</span> ${{m.is_private ? 'Yes' : 'No'}}`;
  }}
  customTooltip.innerHTML = tooltipHtml;
  customTooltip.style.display = 'block';
}});

network.on('blurNode', function() {{
  customTooltip.style.display = 'none';
}});

network.on('hoverEdge', function(params) {{
  if (!params.edge) {{
    customTooltip.style.display = 'none';
    return;
  }}
  const edge = params.edge;
  let tooltipHtml = `<strong style="color:#93c5fd;font-size:12px">Link</strong>`;
  if (edge.protocol) tooltipHtml += `<br><span style="color:#94a3b8">Protocol:</span> ${{topoEsc(edge.protocol)}}`;
  if (edge.from && edge.to) {{
    tooltipHtml += `<br><span style="color:#94a3b8">${{topoEsc(edge.from)}}</span> ↔ <span style="color:#94a3b8">${{topoEsc(edge.to)}}</span>`;
  }}
  customTooltip.innerHTML = tooltipHtml;
  customTooltip.style.display = 'block';
}});

network.on('blurEdge', function() {{
  customTooltip.style.display = 'none';
}});

network.on('mousemove', function(params) {{
  if (customTooltip.style.display === 'none') return;
  customTooltip.style.left = (params.pointer.canvas.x + 15) + 'px';
  customTooltip.style.top = (params.pointer.canvas.y + 15) + 'px';
}});

network.on('click', function(params) {{
  if (!params.nodes.length) {{ detailPanel.classList.remove('visible'); return; }}
  const nid = params.nodes[0];
  const node = RAW_NODES.find(n => n.id === nid);
  if (!node) return;
  showDetail(nid, node.group || node.type);
}});

function showDetail(nid, group) {{
  let html = `<h3>${{topoEsc(nid)}}</h3><table class="l3-detail-table">`;
  if (group === 'device') {{
    const m = DEVICES_META[nid] || {{}};
    const protos = (m.protocols || []).map(protoBadge).join(' ');
    html += `<tr><td>Vendor</td><td>${{vendorBadge(m.platform)}}</td></tr>`;
    html += `<tr><td>Platform</td><td>${{topoEsc(m.platform || '—')}}</td></tr>`;
    html += `<tr><td>Mgmt IP</td><td>${{topoEsc(m.management_ip || nid)}}</td></tr>`;
    html += `<tr><td>SSH port</td><td>${{topoEsc(String(m.ssh_port || 22))}}</td></tr>`;
    html += `<tr><td>Default GW</td><td>${{topoEsc(m.default_gateway || '—')}}</td></tr>`;
    html += `<tr><td>Routes</td><td>${{topoEsc(String(m.route_count || 0))}}</td></tr>`;
    html += `<tr><td>VRFs</td><td>${{topoEsc(String(m.vrf_count || 0))}}</td></tr>`;
    html += `<tr><td>Protocols</td><td>${{protos || '—'}}</td></tr>`;
    if ((m.local_ips || []).length) {{
      html += `<tr><td>Local IPs</td><td>${{topoEsc(m.local_ips.join(', '))}}</td></tr>`;
    }}
    if ((m.vrf_names || []).length) {{
      html += `<tr><td>VRF Names</td><td>${{topoEsc(m.vrf_names.join(', '))}}</td></tr>`;
    }}
    if (m.route_count_by_protocol) {{
      const protoCounts = Object.entries(m.route_count_by_protocol)
        .map(([p, c]) => `${{protoBadge(p)}}: ${{topoEsc(String(c))}}`)
        .join(', ');
      html += `<tr><td>Route Count</td><td>${{protoCounts || '—'}}</td></tr>`;
    }}
    html += `</table>`;
    html += ifaceListHtml(m.interfaces);
    const myRoutes = ALL_ROUTES.filter(r => r.device_id === nid).slice(0, 30);
    if (myRoutes.length) {{
      html += `<h4 style="color:#64748b;font-size:11px;margin:8px 0 4px;text-transform:uppercase">Routes (first 30)</h4>`;
      myRoutes.forEach(r => {{
        html += `<div class="l3-route-row"><b>${{topoEsc(r.destination)}}</b> via ${{topoEsc(r.next_hop||'direct')}}
          ${{protoBadge(r.protocol)}} ${{r.interface ? '· '+topoEsc(r.interface) : ''}}</div>`;
      }});
    }}
  }} else if (group === 'gateway' || group === 'default_gateway') {{
    const m = GW_META[nid] || {{}};
    const protos = (m.protocols || []).map(protoBadge).join(' ');
    html += `<tr><td>Type</td><td>${{group === 'default_gateway' ? '<span style=color:#ef4444>Default GW</span>' : 'Gateway'}}</td></tr>`;
    html += `<tr><td>Subnets</td><td>${{topoEsc(String(m.subnet_count || 0))}}</td></tr>`;
    html += `<tr><td>Seen from</td><td>${{topoEsc(String((m.routing_devices||[]).length))}} device(s)</td></tr>`;
    html += `<tr><td>Protocols</td><td>${{protos||'—'}}</td></tr>`;
    html += `</table>`;
    const snList = (m.subnets || []).slice(0, 20);
    if (snList.length) {{
      html += `<h4 style="color:#64748b;font-size:11px;margin:8px 0 4px;text-transform:uppercase">Subnets served</h4>`;
      snList.forEach(s => {{ html += `<div class="l3-route-row">${{topoEsc(s)}}</div>`; }});
    }}
  }} else if (group === 'subnet') {{
    const m = SN_META[nid] || {{}};
    html += `<tr><td>Prefix len</td><td>/${{topoEsc(String(m.prefix_len || '?'))}}</td></tr>`;
    html += `<tr><td>Hosts</td><td>${{topoEsc(String(m.subnet_size || '?'))}}</td></tr>`;
    html += `<tr><td>Private</td><td>${{m.is_private ? 'Yes' : 'No'}}</td></tr>`;
    html += `<tr><td>Gateways</td><td>${{topoEsc((m.gateway_ips||[]).join(', ')||'—')}}</td></tr>`;
    html += `<tr><td>Seen from</td><td>${{topoEsc(String((m.advertising_devices||[]).length))}} device(s)</td></tr>`;
    // Finding #12: Enhanced subnet metadata
    if (m.gateway_ips && m.gateway_ips.length) {{
      html += `<tr><td>Gateway IPs</td><td>${{topoEsc(m.gateway_ips.join(', '))}}</td></tr>`;
    }}
    if (m.subnet_size !== undefined) {{
      html += `<tr><td>Total hosts</td><td>${{topoEsc(String(m.subnet_size))}}</td></tr>`;
    }}
    if (m.is_private !== undefined) {{
      html += `<tr><td>Private subnet</td><td>${{m.is_private ? 'Yes' : 'No'}}</td></tr>`;
    }}
    html += `</table>`;
  }} else {{
    html += `<tr><td>ID</td><td>${{topoEsc(nid)}}</td></tr></table>`;
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
  network.fit({{animation:true}});
}});

/* ---- Flow Animation (LPM / protocol-evidenced — never random) ---- */
let flowAnimationEnabled = false;
let flowInterval = null;
let lastPathEdgeIds = [];
window._nstLastPathEdgePairs = window._nstLastPathEdgePairs || [];

function _collectProtocolEvidencedEdgeIds() {{
  const ids = [];
  const all = edges.get();
  all.forEach(function(e) {{
    const proto = String((e.protocol || e.title || e.label || '')).toLowerCase();
    const hasProto = /ospf|bgp|eigrp|isis|static|connected|rip/.test(proto);
    const hasRouteMeta = !!(e.metric || e.admin_distance || e.bandwidth);
    if (hasProto || hasRouteMeta) ids.push(e.id);
  }});
  return ids;
}}

function _edgeIdsForPathPairs(pairs) {{
  const ids = [];
  const all = edges.get();
  (pairs || []).forEach(function(pair) {{
    all.forEach(function(e) {{
      if ((e.from === pair.from && e.to === pair.to) || (e.from === pair.to && e.to === pair.from)) {{
        ids.push(e.id);
      }}
    }});
  }});
  return ids;
}}

function _stopFlowAnimation() {{
  flowAnimationEnabled = false;
  if (flowInterval) {{ clearInterval(flowInterval); flowInterval = null; }}
  const btn = document.getElementById('btn-flow');
  if (btn) {{ btn.textContent = 'Animate LPM flow'; btn.classList.remove('on'); }}
  (lastPathEdgeIds || []).forEach(function(id) {{
    try {{ edges.update({{id: id, dashes: false, width: undefined}}); }} catch (e) {{}}
  }});
}}

document.getElementById('btn-flow').addEventListener('click', function() {{
  if (flowAnimationEnabled) {{
    _stopFlowAnimation();
    return;
  }}
  let pairs = window._nstLastPathEdgePairs || [];
  const srcEl = document.getElementById('trace-src-ip');
  const dstEl = document.getElementById('trace-dst-ip');
  const src = (srcEl && srcEl.value || '').trim();
  const dst = (dstEl && dstEl.value || '').trim();
  if ((!pairs || !pairs.length) && src && dst) {{
    try {{ l3TracePath(); }} catch (e) {{}}
    pairs = window._nstLastPathEdgePairs || [];
  }}
  let ids = _edgeIdsForPathPairs(pairs);
  if (!ids.length) {{
    ids = _collectProtocolEvidencedEdgeIds();
  }}
  if (!ids.length) {{
    alert('No LPM path or protocol-evidenced edges yet. Enter Source/Dest IP, click Trace Flow, then Animate — or build a map with route metadata on edges.');
    return;
  }}
  lastPathEdgeIds = ids;
  flowAnimationEnabled = true;
  const btn = document.getElementById('btn-flow');
  if (btn) {{ btn.textContent = 'Stop animation'; btn.classList.add('on'); }}
  let phase = 0;
  flowInterval = setInterval(function() {{
    phase = (phase + 1) % 12;
    ids.forEach(function(id, i) {{
      const on = ((i + phase) % 3) === 0;
      try {{
        edges.update({{
          id: id,
          dashes: on ? [8, 6] : [2, 10],
          width: on ? 5 : 2,
          color: {{ color: on ? '#10b981' : '#38bdf8', highlight: '#34d399' }}
        }});
      }} catch (e) {{}}
    }});
  }}, 220);
}});

/* ---- Focus Mode ---- */
let selectedNodeId = null;
document.getElementById('btn-focus').addEventListener('click', function() {{
  if (!selectedNodeId) {{
    alert('Click a node first to focus on it');
    return;
  }}
  const connectedNodes = network.getConnectedNodes(selectedNodeId);
  const allNodeIds = nodes.getIds();
  
  allNodeIds.forEach(id => {{
    if (id === selectedNodeId || connectedNodes.includes(id)) {{
      nodes.update({{id: id, hidden: false}});
    }} else {{
      nodes.update({{id: id, hidden: true}});
    }}
  }});
  network.fit({{animation: true}});
}});

/* ---- PNG Export ---- */
document.getElementById('btn-export').addEventListener('click', function() {{
  network.on('afterDrawing', function(ctx) {{
    const dataURL = ctx.canvas.toDataURL('image/png');
    const link = document.createElement('a');
    link.download = '{map_kind}_routing_map.png';
    link.href = dataURL;
    link.click();
    network.off('afterDrawing');
  }});
  network.redraw();
}});

/* ---- Track selected node for focus mode ---- */
network.on('click', function(params) {{
  if (params.nodes.length > 0) {{
    selectedNodeId = params.nodes[0];
  }}
}});

/* ---- Path Tracer (LPM Flow Simulation) ---- */
function ipToLong(ip) {{
  var parts = String(ip || '').trim().split('.');
  if (parts.length !== 4) return 0;
  return (((+parts[0]<<24)>>>0) + ((+parts[1]<<16)>>>0) + ((+parts[2]<<8)>>>0) + (+parts[3]>>>0))>>>0;
}}

function parseCidr(cidr) {{
  if (!cidr || !cidr.includes('/')) return null;
  var parts = cidr.split('/');
  var ipL = ipToLong(parts[0]);
  var mask = (+parts[1] === 0) ? 0 : (~((1 << (32 - +parts[1])) - 1)) >>> 0;
  return {{ net: (ipL & mask) >>> 0, mask: mask, prefixlen: +parts[1] }};
}}

function l3TracePath() {{
  var srcIp = (document.getElementById('trace-src-ip') || {{}}).value || '';
  var dstIp = (document.getElementById('trace-dst-ip') || {{}}).value || '';
  srcIp = srcIp.trim();
  dstIp = dstIp.trim();
  if (!srcIp || !dstIp) {{
    alert('Please enter both Source IP and Destination IP to trace flow.');
    return;
  }}
  var srcLong = ipToLong(srcIp);
  var dstLong = ipToLong(dstIp);
  if (!srcLong || !dstLong) {{
    alert('Invalid IPv4 address format. Example: 10.1.1.5');
    return;
  }}

  var ingressDev = null;
  var ingressIface = 'connected';
  var bestIngressMask = -1;

  for (var devId in DEVICES_META) {{
    var meta = DEVICES_META[devId] || {{}};
    var subs = meta.connected_subnets || [];
    for (var i = 0; i < subs.length; i++) {{
      var parsed = parseCidr(subs[i]);
      if (parsed && (srcLong & parsed.mask) === parsed.net) {{
        if (parsed.prefixlen > bestIngressMask) {{
          bestIngressMask = parsed.prefixlen;
          ingressDev = devId;
        }}
      }}
    }}
  }}

  if (!ingressDev) {{
    for (var i = 0; i < ALL_ROUTES.length; i++) {{
      var r = ALL_ROUTES[i];
      var p = parseCidr(r.network || r.prefix);
      if (p && (srcLong & p.mask) === p.net && (r.protocol === 'Connected' || r.protocol === 'Local')) {{
        if (p.prefixlen > bestIngressMask) {{
          bestIngressMask = p.prefixlen;
          ingressDev = r.device_id || r.device;
          ingressIface = r.interface || 'connected';
        }}
      }}
    }}
  }}

  if (!ingressDev) {{
    var keys = Object.keys(DEVICES_META);
    if (keys.length > 0) ingressDev = keys[0];
  }}

  if (!ingressDev) {{
    alert('No topology devices found to initiate trace.');
    return;
  }}

  var currentDev = ingressDev;
  var hops = [];
  var pathNodes = [currentDev];
  var pathEdgePairs = [];
  var visited = {{}};
  visited[currentDev] = true;
  var maxHops = 25;
  var complete = false;

  hops.push({{
    hop: 1,
    device: currentDev,
    action: 'ingress',
    desc: 'Source ' + srcIp + ' enters network at ' + currentDev,
    proto: 'Ingress'
  }});

  for (var h = 2; h <= maxHops; h++) {{
    var bestRoute = null;
    var bestPfx = -1;
    for (var i = 0; i < ALL_ROUTES.length; i++) {{
      var r = ALL_ROUTES[i];
      var rDev = r.device_id || r.device;
      if (rDev !== currentDev) continue;
      var p = parseCidr(r.network || r.prefix);
      if (p && (dstLong & p.mask) === p.net) {{
        if (p.prefixlen > bestPfx) {{
          bestPfx = p.prefixlen;
          bestRoute = r;
        }}
      }}
    }}

    if (!bestRoute) {{
      hops.push({{
        hop: h,
        device: currentDev,
        action: 'dropped',
        desc: 'No route to ' + dstIp + ' on ' + currentDev + ' (drop)',
        proto: 'Drop'
      }});
      break;
    }}

    var proto = bestRoute.protocol || 'Static';
    var nextHop = bestRoute.next_hop || bestRoute.nexthop || '';
    var iface = bestRoute.interface || '';

    if (proto.toLowerCase() === 'connected' || proto.toLowerCase() === 'local' || bestPfx === 32) {{
      hops.push({{
        hop: h,
        device: currentDev,
        action: 'delivered',
        desc: 'Delivered to ' + dstIp + ' via ' + (iface || 'local connected subnet'),
        proto: proto
      }});
      complete = true;
      break;
    }}

    var nextDev = null;
    var nhLong = ipToLong(nextHop);
    if (nhLong) {{
      for (var d in DEVICES_META) {{
        if (d === currentDev) continue;
        var meta = DEVICES_META[d] || {{}};
        var subs = meta.connected_subnets || [];
        for (var si = 0; si < subs.length; si++) {{
          var sp = parseCidr(subs[si]);
          if (sp && (nhLong & sp.mask) === sp.net) {{
            nextDev = d;
            break;
          }}
        }}
        if (nextDev) break;
      }}
    }}

    if (!nextDev || nextDev === currentDev) {{
      hops.push({{
        hop: h,
        device: currentDev,
        action: 'forward_gw',
        desc: 'Routed via ' + proto + ' to external gateway ' + nextHop + ' (' + iface + ')',
        proto: proto
      }});
      complete = true;
      break;
    }}

    if (visited[nextDev]) {{
      hops.push({{
        hop: h,
        device: currentDev,
        action: 'loop',
        desc: 'Routing loop detected: ' + currentDev + ' -> ' + nextDev,
        proto: 'Loop'
      }});
      break;
    }}

    hops.push({{
      hop: h,
      device: currentDev,
      action: 'forward',
      desc: 'Forward via ' + proto + ' (' + (bestRoute.network || '') + ') -> ' + nextHop + ' on ' + nextDev,
      proto: proto
    }});

    pathNodes.push(nextDev);
    pathEdgePairs.push({{from: currentDev, to: nextDev}});
    visited[nextDev] = true;
    currentDev = nextDev;
  }}

  var allEdges = edges.get();
  window._nstLastPathEdgePairs = pathEdgePairs.slice();
  allEdges.forEach(function(e) {{
    var isPath = false;
    for (var pi = 0; pi < pathEdgePairs.length; pi++) {{
      var pair = pathEdgePairs[pi];
      if ((e.from === pair.from && e.to === pair.to) || (e.from === pair.to && e.to === pair.from)) {{
        isPath = true;
        break;
      }}
    }}
    if (isPath) {{
      edges.update({{id: e.id, color: {{color: '#10b981', highlight: '#34d399'}}, width: 6, shadow: true}});
    }} else {{
      edges.update({{id: e.id, color: {{color: '#334155', opacity: 0.15}}, width: 1}});
    }}
  }});

  var allNodeIds = nodes.getIds();
  allNodeIds.forEach(function(nid) {{
    if (pathNodes.includes(nid)) {{
      nodes.update({{id: nid, borderWidth: 4, color: {{border: '#10b981'}} }});
    }} else {{
      nodes.update({{id: nid, borderWidth: 1, opacity: 0.35 }});
    }}
  }});

  var sideSec = document.getElementById('trace-section');
  var resDiv = document.getElementById('trace-results');
  if (sideSec && resDiv) {{
    sideSec.style.display = 'block';
    var html = '<div style="margin-bottom:8px;font-size:11px;color:#a5b4fc"><b>' + srcIp + '</b> → <b>' + dstIp + '</b> (' + (complete ? '<span style=color:#22c55e>Delivered</span>' : '<span style=color:#f59e0b>Incomplete</span>') + ')</div>';
    hops.forEach(function(hp) {{
      var cls = hp.action === 'delivered' ? 'delivered' : (hp.action === 'ingress' ? 'ingress' : (hp.action === 'loop' ? 'loop' : ''));
      html += '<div class="l3-hop-card ' + cls + '">';
      html += '<div class="l3-hop-head"><span>Hop ' + hp.hop + ': ' + hp.device + '</span><span class="l3-badge proto-ospf">' + hp.proto + '</span></div>';
      html += '<div class="l3-hop-sub">' + hp.desc + '</div>';
      html += '</div>';
    }});
    resDiv.innerHTML = html;
  }}
}}

function l3ClearTrace() {{
  var sideSec = document.getElementById('trace-section');
  if (sideSec) sideSec.style.display = 'none';
  nodes.getIds().forEach(function(nid) {{
    var raw = RAW_NODES.find(function(rn) {{ return rn.id === nid; }});
    if (raw) nodes.update(makeVisNode(raw));
  }});
  edges.getIds().forEach(function(eid) {{
    var raw = RAW_EDGES.find(function(re) {{ return re.id === eid; }});
    if (raw) edges.update({{
      ...raw,
      font: {{ size: 10, align: 'middle', color: '#64748b' }},
      color: {{ color: '#475569', highlight: '#818cf8' }},
      width: 2,
    }});
  }});
}}
"""


# ---------------------------------------------------------------------------
# render_l3_map_html
# ---------------------------------------------------------------------------

def _vendor_badge_html(platform: str) -> str:
    p = (platform or '').lower()
    if 'junos' in p or 'juniper' in p:
        return '<span class="l3-vendor-badge l3-vendor-juniper">Juniper</span>'
    if 'nxos' in p or 'nexus' in p:
        return '<span class="l3-vendor-badge l3-vendor-nxos">NX-OS</span>'
    if 'xe' in p:
        return '<span class="l3-vendor-badge l3-vendor-iosxe">IOS-XE</span>'
    if 'ios' in p or 'cisco' in p:
        return '<span class="l3-vendor-badge l3-vendor-ios">IOS</span>'
    label = html.escape(str(platform or 'Device'), quote=True)
    return f'<span class="l3-vendor-badge l3-vendor-other">{label}</span>'


def _device_sidebar_cards(devices: Dict[str, Any], limit: int = 25) -> str:
    if not devices:
        return '<div class="l3-route-row" style="color:#64748b">No devices</div>'
    rows = []
    for did, info in list(devices.items())[:limit]:
        did_e = html.escape(str(did), quote=True)
        mgmt = html.escape(str(info.get('management_ip') or did), quote=True)
        port = info.get('ssh_port') or 22
        port_txt = f':{port}' if port != 22 else ''
        gw = html.escape(str(info.get('default_gateway') or '—'), quote=True)
        ifaces = info.get('interfaces') or {}
        iface_preview = ', '.join(html.escape(str(k), quote=True) for k in list(ifaces.keys())[:3])
        if len(ifaces) > 3:
            iface_preview += '…'
        rows.append(
            f"<div class='l3-device-card'>"
            f"<div>{_vendor_badge_html(info.get('platform', ''))}<b>{did_e}</b></div>"
            f"<div class='l3-device-meta'>"
            f"Mgmt: {mgmt}{port_txt}<br>"
            f"Routes: {info.get('route_count', 0)} · Default GW: {gw}<br>"
            f"{'Ports: ' + iface_preview if iface_preview else ''}"
            f"</div></div>"
        )
    return ''.join(rows)


def render_l3_map_html(
    vis_payload: Dict[str, Any],
    title: str = 'L3 Routing Map',
    subtitle: str = '',
    map_kind: str = 'l3',
) -> str:
    """Render complete offline HTML for L3 or flow routing map."""
    nodes_json    = script_safe_json(vis_payload.get('nodes') or [])
    edges_json    = script_safe_json(vis_payload.get('edges') or [])
    analysis      = vis_payload.get('analysis') or {}
    gateways      = vis_payload.get('gateway_analysis') or {}
    subnets       = vis_payload.get('subnet_analysis') or {}
    devices       = vis_payload.get('devices') or {}
    failed        = vis_payload.get('failed_hosts') or []
    all_routes    = vis_payload.get('all_routes') or []
    version       = read_version_label()

    devices_json  = script_safe_json(devices)
    gw_json       = script_safe_json(gateways)
    sn_json       = script_safe_json(subnets)
    routes_json   = script_safe_json(all_routes[:2000])   # cap for JS

    # Escape title/subtitle for safe HTML embedding (prevent XSS via <title> and header)
    title_esc    = html.escape(str(title or 'L3 Routing Map'), quote=True)
    subtitle_esc = html.escape(str(subtitle or ''), quote=True)
    kind_label   = html.escape('Network Flow Map' if map_kind == 'flow' else 'L3 Routing Map')

    n_devices  = analysis.get('total_devices', len(devices))
    n_gateways = analysis.get('total_gateways', len(gateways))
    n_subnets  = analysis.get('total_subnets', len(subnets))
    n_routes   = vis_payload.get('route_count', analysis.get('total_routes', len(all_routes)))
    n_nodes    = len(vis_payload.get('nodes') or [])
    n_edges    = len(vis_payload.get('edges') or [])
    logo_uri = load_app_logo_data_uri()
    logo_html = (
        f"<img class='l3-brand-logo' src='{logo_uri}' alt='Network Swiss Tool Pro'>"
        if logo_uri else ''
    )
    fail_html  = (
        f"<div class='l3-side-section'><h4>Failed hosts ({len(failed)})</h4>"
        f"<div class='l3-failed'>⚠ SSH/routing collection failed for: "
        f"{html.escape(', '.join(str(x) for x in failed[:15]), quote=True)}"
        f"{'…' if len(failed) > 15 else ''}"
        f"<br><small style='color:#94a3b8'>Check credentials, SSH port, ACLs, and enable access.</small></div></div>"
        if failed else ''
    )

    # Protocol distribution for legend
    proto_dist = analysis.get('protocol_distribution') or {}
    # Secure Cartography-inspired legend colors
    LEGEND_COLORS = {
        'cisco':          '#00bceb',
        'juniper':        '#f97316',
        'arista':         '#22c55e',
        'gateway':         '#f59e0b',
        'default_gateway': '#ef4444',
        'subnet':          '#8b5cf6',
    }
    legend_html = ''.join(
        f"<div class='l3-legend-item l3-legend-{cls}'>"
        f"<div class='l3-legend-dot'></div>{lbl}</div>"
        for lbl, cls in [
            ('Cisco', 'cisco'),
            ('Juniper', 'juniper'),
            ('Arista', 'arista'),
            ('Gateway', 'gateway'),
            ('Default GW', 'default-gw'),
            ('Subnet', 'subnet'),
        ]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{title_esc} — Network Swiss Tool Pro {version}</title>
  {load_vis_script()}
  <style>{shell_css()}{l3_map_css()}</style>
</head>
<body class="l3-routing-map">
  <header>
    {logo_html}
    <div>
      <h1>{title_esc}</h1>
      <p>{kind_label} · {subtitle_esc} · Offline · {version}</p>
      <p class="overlay-honesty">L2/L3 only — EVPN/VXLAN overlay not collected.</p>
    </div>
  </header>
  {layer_switch_html('l3')}

  <main class="l3-map-main">

  <div class="l3-toolbar">
    <input type="text" id="search-input" placeholder="Search node…" autocomplete="off">
    <button id="btn-fit">Fit all</button>
    <button id="btn-reset">Reset</button>
    <button id="btn-focus">Focus Mode</button>
    <button id="btn-flow" title="Animate last LPM path (or protocol-evidenced edges)">Animate LPM flow</button>
    <button id="btn-export">Export PNG</button>
    <div class="l3-trace-bar">
      <span style="font-weight:700;color:#38bdf8;font-size:11px">⚡ PATH TRACER:</span>
      <input type="text" id="trace-src-ip" placeholder="Source IP" autocomplete="off">
      <span style="color:#64748b">→</span>
      <input type="text" id="trace-dst-ip" placeholder="Dest IP" autocomplete="off">
      <button id="btn-trace-flow" class="flow-btn" onclick="l3TracePath()">Trace Flow</button>
      <button id="btn-clear-trace" onclick="l3ClearTrace()">Clear</button>
    </div>
  </div>

  <div class="l3-proto-filter" id="l3-proto-filter" aria-label="Protocol filter">
    <label>Protocols:</label>
    <button class="l3-proto-btn on ospf" data-proto="ospf" onclick="l3ToggleProto(this,'ospf')"><span class="l3-proto-dot ospf"></span>OSPF</button>
    <button class="l3-proto-btn on bgp" data-proto="bgp" onclick="l3ToggleProto(this,'bgp')"><span class="l3-proto-dot bgp"></span>BGP</button>
    <button class="l3-proto-btn on eigrp" data-proto="eigrp" onclick="l3ToggleProto(this,'eigrp')"><span class="l3-proto-dot eigrp"></span>EIGRP</button>
    <button class="l3-proto-btn on static" data-proto="static" onclick="l3ToggleProto(this,'static')"><span class="l3-proto-dot static"></span>Static</button>
    <button class="l3-proto-btn on conn" data-proto="conn" onclick="l3ToggleProto(this,'conn')"><span class="l3-proto-dot conn"></span>Connected</button>
    <button class="l3-proto-btn on isis" data-proto="isis" onclick="l3ToggleProto(this,'isis')"><span class="l3-proto-dot isis"></span>IS-IS</button>
    <button class="l3-proto-btn" style="margin-left:auto;font-size:10px" onclick="l3ProtoAll(true)">All</button>
    <button class="l3-proto-btn" style="font-size:10px" onclick="l3ProtoAll(false)">None</button>
  </div>

  <div class="l3-stats">
    <div class="l3-stat"><b>{n_devices}</b>Devices</div>
    <div class="l3-stat"><b>{n_gateways}</b>Gateways</div>
    <div class="l3-stat"><b>{n_subnets}</b>Subnets</div>
    <div class="l3-stat"><b>{n_routes}</b>Routes</div>
    <div class="l3-stat"><b>{n_nodes}</b>Nodes</div>
    <div class="l3-stat"><b>{n_edges}</b>Edges</div>
  </div>

  <div class="l3-legend">{legend_html}</div>

  <div class="l3-layout">
    <div id="l3-network"></div>
    <div class="l3-side">
      <div class="l3-detail-panel" id="detail-panel">
        <div id="detail-content"></div>
      </div>
      <div class="l3-side-section" id="trace-section" style="display:none;background:#0d1526;border-bottom:2px solid #0ea5e9;">
        <h4 style="color:#38bdf8">⚡ Flow Simulation Hops</h4>
        <div id="trace-results"></div>
      </div>
      <div class="l3-side-header">Summary</div>
      <div class="l3-side-section">
        <h4>Devices ({n_devices})</h4>
        {_device_sidebar_cards(devices)}
      </div>
      <div class="l3-side-section">
        <h4>Default Gateways</h4>
        {''.join(
            f"<div class='l3-route-row'><b>{gw}</b>"
            f"{'<span style=color:#ef4444> default</span>' if info.get('is_default_gateway') else ''}"
            f" — {info.get('subnet_count',0)} subnets</div>"
            for gw, info in list(gateways.items())[:20]
            if info.get('is_default_gateway')
        ) or '<div class="l3-route-row" style="color:#64748b">None detected</div>'}
      </div>
      {fail_html}
    </div>
  </div>
  </main>

  <script>
  {embed_link_inventory_render_js()}
  document.addEventListener('DOMContentLoaded', function() {{
    {_l3_js(nodes_json, edges_json, devices_json, gw_json, sn_json, routes_json, map_kind)}
    nstSetLayer('l3');
  }});
  </script>
</body>
</html>"""
