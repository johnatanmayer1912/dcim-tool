"""
VPC Command Center shell (v7.0.3) — offline-first, light theme, split board + map.
"""
import json


def vpc_light_css():
    from utils.map_shell_theme import enterprise_map_css
    return enterprise_map_css() + """
    body.vpc-light.vpc-command-center {
      background: #f1f5f9 !important;
      color: #0f172a !important;
      overflow-y: auto !important;
      overflow-x: hidden !important;
      min-height: 100vh;
      font-family: var(--nst-map-font), -apple-system, system-ui, sans-serif !important;
    }
    body.vpc-command-center .header h2 { color: #0f172a !important; }
    body.vpc-command-center .stats { color: #475569 !important; }
    body.vpc-command-center .stats-summary {
      background: #fff !important;
      color: #475569 !important;
      border: 1px solid #cbd5e1 !important;
    }
    body.vpc-command-center .topo-toolbar {
      background: #fff !important;
      border: 1px solid #e2e8f0 !important;
    }
    body.vpc-command-center .topo-toolbar input {
      background: #fff !important;
      color: #0f172a !important;
      border-color: #cbd5e1 !important;
    }
    body.vpc-command-center .topo-toolbar button {
      background: #f8fafc !important;
      color: #334155 !important;
      border-color: #cbd5e1 !important;
    }
    body.vpc-command-center .legend { color: #475569 !important; }
    body.vpc-command-center #mynetwork.vpc-map-pane {
      flex: 0 0 auto;
      min-height: 420px;
      height: clamp(420px, 50vh, 680px);
      max-height: 680px;
      width: 100%;
      overflow: hidden;
      background: #e2e8f0 !important;
      border: 2px solid #94a3b8 !important;
      border-radius: 12px;
      box-shadow: inset 0 0 0 1px #fff;
      display: block !important;
    }
    body.vpc-command-center #mynetwork.map-tab-hidden {
      display: block !important;
    }
    body.vpc-command-center #vpc-engineering-board {
      display: block !important;
      max-width: 100%;
    }
    body.vpc-command-center #vpc-engineering-board.hidden {
      display: block !important;
    }
    .vpc-cc-tabs { display:flex; gap:8px; flex-wrap:wrap; margin:12px 0; }
    .vpc-cc-tabs button {
      padding:10px 16px; border-radius:8px; border:1px solid #cbd5e1;
      background:#fff; cursor:pointer; font-weight:600; font-size:13px; color:#334155;
    }
    .vpc-cc-tabs button.active { background:#4f46e5; color:#fff; border-color:#4338ca; }
    .vpc-cc-panel { display:none; }
    .vpc-cc-panel.active { display:block; }
    .vpc-split-overview {
      display:grid;
      grid-template-columns: minmax(380px, 1.1fr) minmax(320px, 0.9fr);
      gap:12px;
      min-height:520px;
      align-items:start;
    }
    @media (max-width: 1000px) {
      .vpc-split-overview { grid-template-columns: 1fr; height:auto; }
    }
    .vpc-map-toolbar {
      display:flex; flex-wrap:wrap; gap:6px; align-items:center;
      margin-bottom:8px; padding:6px 8px; background:#fff;
      border:1px solid #e2e8f0; border-radius:8px;
    }
    .vpc-map-toolbar button {
      padding:6px 10px; font-size:11px; font-weight:600; border-radius:6px;
      border:1px solid #cbd5e1; background:#f8fafc; color:#334155; cursor:pointer;
    }
    .vpc-map-toolbar button:hover { background:#e8f1ff; border-color:#0a84ff; }
    .vpc-map-legend {
      display:flex; flex-wrap:wrap; gap:10px; font-size:11px; color:#475569;
      margin-bottom:6px;
      padding:8px 10px;
      background:#fff;
      border:1px solid #e2e8f0;
      border-radius:8px;
    }
    .vpc-map-legend span {
      display:inline-flex; align-items:center; gap:4px;
      padding:3px 8px; border-radius:6px; background:#f8fafc;
      border:1px solid #e2e8f0; font-weight:600;
    }
    .vpc-map-legend span::before {
      content:''; display:inline-block; width:12px; height:12px;
      border-radius:3px; margin-right:2px; vertical-align:middle;
      flex-shrink:0;
    }
    .vpc-map-hint {
      font-size:12px; color:#475569; background:#eff6ff;
      border:1px solid #bfdbfe; border-radius:8px;
      padding:8px 12px; margin-bottom:8px; line-height:1.45;
    }
    .vpc-map-hint b { color:#1d4ed8; }
    .vpc-leg-peer::before { background:#a855f7; }
    .vpc-leg-vpc::before { background:#f97316; }
    .vpc-leg-shared::before { background:#0984e3; }
    .vpc-leg-domain::before { background:#6366f1; }
    .vpc-leg-verified::before { background:#059669; }
    .vpc-leg-inferred::before { background:#94a3b8; }
    .vpc-split-board {
      overflow:auto;
      max-height: calc(100vh - 220px);
      border:1px solid #e2e8f0;
      border-radius:12px;
      background:#fff;
      padding:8px;
    }
    .vpc-split-map {
      display:flex;
      flex-direction:column;
      min-height:420px;
      overflow:hidden;
    }
    #vpc-collected-data {
      background:#fff;
      border:1px solid #e2e8f0;
      border-radius:12px;
      padding:16px;
      max-height: calc(100vh - 200px);
      overflow:auto;
      font-size:12px;
    }
    #vpc-collected-data h3 { font-size:14px; margin:12px 0 6px 0; color:#1e293b; }
    #vpc-collected-data table {
      width:100%; border-collapse:collapse; margin-bottom:16px;
    }
    #vpc-collected-data th {
      text-align:left; padding:6px 8px; background:#1e293b; color:#f8fafc;
    }
    #vpc-collected-data td {
      padding:6px 8px; border-bottom:1px solid #e2e8f0;
    }
    .vpc-empty-state {
      padding:24px; text-align:center; color:#64748b;
      background:#fffbeb; border:1px dashed #f59e0b; border-radius:10px;
    }
    .theme-toggle-btn { margin-left:auto; }
    """


def vpc_command_center_tabs_html():
    return """
  <div class="vpc-cc-tabs" id="vpc-cc-tabs">
    <button type="button" class="active" id="vpc-tab-overview" onclick="vpcCcTab('overview')">1 Overview</button>
    <button type="button" id="vpc-tab-links" onclick="vpcCcTab('links')">2 Link inventory</button>
    <button type="button" id="vpc-tab-data" onclick="vpcCcTab('data')">3 Collected data</button>
    <button type="button" onclick="window.print()">Print board</button>
    <button type="button" class="theme-toggle-btn" onclick="vpcToggleTheme()">Light / Dark</button>
  </div>
  <div id="vpc-panel-overview" class="vpc-cc-panel active">
    <div class="vpc-split-overview" id="vpc-split-overview">
      <div class="vpc-split-map">
        <div style="font-size:13px;font-weight:700;color:#1e293b;margin-bottom:4px;">Simplified Map — vPC topology</div>
        <div class="vpc-map-hint"><b>How to read this map:</b> Purple = peer-link · Orange = vPC member · Blue = dual-homed downstream · Green edges = verified CDP. Use <b>Fit view</b> if nodes overlap. Click a switch to highlight its links.</div>
        <div class="vpc-map-legend">
          <span class="vpc-leg-domain">Domain</span>
          <span class="vpc-leg-peer">Peer-link</span>
          <span class="vpc-leg-vpc">vPC member</span>
          <span class="vpc-leg-shared">Dual-homed</span>
          <span class="vpc-leg-verified">Verified CDP</span>
          <span class="vpc-leg-inferred">Inferred</span>
        </div>
        <div class="vpc-map-toolbar">
          <button type="button" onclick="vpcFitTopology(48)">Fit view</button>
          <button type="button" onclick="vpcFocusAllPeers()">All peers</button>
          <button type="button" onclick="toggleNonVpcEdges()">L2 adjacency</button>
          <button type="button" onclick="vpcResetHighlight()">Reset highlight</button>
        </div>
        <div id="vpc-map-empty" class="vpc-empty-state" style="display:none;margin-bottom:8px;">No topology nodes to display. Run vPC map on NX-OS peers with <code>show vpc</code> success, or check diagnostics 06/07.</div>
        <div id="mynetwork" class="vpc-map-pane"></div>
      </div>
      <div class="vpc-split-board" id="vpc-split-board-host"></div>
    </div>
  </div>
  <div id="vpc-panel-links" class="vpc-cc-panel">
    <div class="topo-inv-hint" style="margin:0 0 8px 0;">All L2 links collected in this vPC run — sortable table with trust validation badges.</div>
  </div>
  <div id="vpc-panel-data" class="vpc-cc-panel">
    <div id="vpc-collected-data"><p>Loading collected data…</p></div>
  </div>
"""


def vpc_shell_js(presentation_json: str, board_payload_json: str):
    pres = presentation_json or '{}'
    board = board_payload_json or '{"domains":[]}'
    return f"""
    window.__VPC_PRESENTATION__ = {pres};
    window.__VPC_BOARD__ = {board};
    window.__VPC_COMMAND_CENTER__ = true;

    function vpcCcTab(which) {{
      ['overview','links','data'].forEach(function(t) {{
        var p = document.getElementById('vpc-panel-' + t);
        var b = document.getElementById('vpc-tab-' + t);
        if (p) p.classList.toggle('active', t === which);
        if (b) b.classList.toggle('active', t === which);
      }});
      if (which === 'overview') {{
        setTimeout(vpcBootMap, 30);
      }}
      if (which === 'links') {{
        var linksPanel = document.getElementById('vpc-panel-links');
        var linkInv = document.getElementById('topo-link-inventory');
        if (linksPanel && linkInv && linkInv.parentNode !== linksPanel) {{
          linksPanel.appendChild(linkInv);
        }}
        if (typeof topoShellShowLinks === 'function') topoShellShowLinks();
      }}
      if (which === 'data') vpcRenderCollectedData();
    }}

    function vpcToggleTheme() {{
      document.body.classList.toggle('vpc-light');
      try {{
        localStorage.setItem('nst_vpc_theme', document.body.classList.contains('vpc-light') ? 'light' : 'dark');
      }} catch(e) {{}}
      vpcBootMap();
    }}

    function vpcFocusAllPeers() {{
      if (!nodes) return;
      var peerIds = nodes.get({{
        filter: function(n) {{
          return n.group === 'vpc_primary' || n.group === 'vpc_secondary' ||
            (n.id && String(n.id).indexOf('VPC_Domain_') === 0);
        }}
      }}).map(function(n) {{ return n.id; }});
      if (network && peerIds.length) {{
        network.selectNodes(peerIds);
        vpcFitTopology(56);
      }}
    }}

    function vpcResetHighlight() {{
      if (!nodes) return;
      var upd = nodes.get().map(function(n) {{
        return {{ id: n.id, opacity: 1, borderWidth: n.group === 'vpc_domain' ? 3 : 2 }};
      }});
      nodes.update(upd);
      if (network) network.unselectAll();
      vpcFitTopology(48);
    }}

    function vpcBootMap(attempt) {{
      attempt = attempt || 0;
      var c = document.getElementById('mynetwork');
      if (!c) return;
      c.classList.remove('map-tab-hidden', 'topo-map-hidden');
      c.style.display = 'block';
      if (typeof createTopologyNetwork === 'function') {{
        createTopologyNetwork();
      }}
      if (typeof network === 'undefined' || !network) {{
        if (attempt < 50) setTimeout(function() {{ vpcBootMap(attempt + 1); }}, 100);
        return;
      }}
      if (typeof wireNetworkHandlers === 'function' && !window._topoHandlersWired) {{
        wireNetworkHandlers();
      }}
      if (typeof vpcPostMapInit === 'function') vpcPostMapInit();
      try {{
        var emptyEl = document.getElementById('vpc-map-empty');
        var visNodes = nodes.get({{ filter: function(n) {{ return !n.hidden; }} }});
        if (!visNodes.length) {{
          if (emptyEl) emptyEl.style.display = 'block';
          if (c) c.style.minHeight = '200px';
        }} else {{
          if (emptyEl) emptyEl.style.display = 'none';
          if (attempt === 0 && !window._vpcAutoFitDone) {{
            window._vpcAutoFitDone = true;
            vpcFitTopology(48);
          }}
        }}
        var pos = network.getPositions();
        var ids = Object.keys(pos || {{}});
        if (ids.length && ids.every(function(id) {{ return pos[id].x === 0 && pos[id].y === 0; }})) {{
          console.warn('[VPC_CC] All nodes at origin — check 04_final_map_data.json / _ensure_vpc_nodes_positioned');
        }}
      }} catch(e) {{
        console.warn('[VPC_CC] map fit:', e);
      }}
    }}

    function vpcRenderCollectedData() {{
      var el = document.getElementById('vpc-collected-data');
      if (!el) return;
      var p = window.__VPC_PRESENTATION__ || {{}};
      var html = '';
      var domains = p.vpc_domains || [];
      if (!domains.length) {{
        html = '<div class="vpc-empty-state"><b>No vPC domains in this run.</b><br>Check NX-OS <code>show vpc</code> output in the diagnostic folder (06_pre_render_presentation.json).</div>';
      }} else {{
        html += '<h3>vPC Domains (' + domains.length + ')</h3><table><tr><th>Domain</th><th>Members</th></tr>';
        domains.forEach(function(d) {{
          html += '<tr><td>' + (d.domain_id || '') + '</td><td>' + (d.members || []).join(', ') + '</td></tr>';
        }});
        html += '</table>';
      }}
      var mi = p.member_interfaces_by_switch || {{}};
      var sw = Object.keys(mi);
      if (sw.length) {{
        html += '<h3>Member interfaces by switch</h3>';
        sw.forEach(function(h) {{
          var block = mi[h];
          html += '<p><b>' + h + '</b></p><table><tr><th>vPC</th><th>Po</th><th>Members</th></tr>';
          (block.entries || []).forEach(function(e) {{
            html += '<tr><td>' + (e.vpc_id||'') + '</td><td>' + (e.port_channel||'') + '</td><td>' +
              (e.member_interfaces||[]).join(', ') + '</td></tr>';
          }});
          html += '</table>';
        }});
      }}
      var ge = p.graph_edges || [];
      if (ge.length) {{
        html += '<h3>Graph edges (sample ' + Math.min(40, ge.length) + ')</h3><table><tr><th>From</th><th>To</th><th>Type</th></tr>';
        ge.slice(0, 40).forEach(function(e) {{
          html += '<tr><td>' + (e.from||'') + '</td><td>' + (e.to||'') + '</td><td>' + (e.type||'') + '</td></tr>';
        }});
        html += '</table>';
      }}
      el.innerHTML = html;
    }}

    function vpcMountBoard() {{
      var host = document.getElementById('vpc-split-board-host');
      var board = document.getElementById('vpc-engineering-board');
      if (!host || !board) return;
      if (board.parentNode !== host) host.appendChild(board);
      board.classList.remove('hidden');
      if (typeof boardInit === 'function') boardInit();
    }}

    function vpcCommandCenterInit() {{
      try {{
        if (localStorage.getItem('nst_vpc_theme') === 'dark') document.body.classList.remove('vpc-light');
      }} catch(e) {{}}
      vpcMountBoard();
      vpcRenderCollectedData();
      var linksPanel = document.getElementById('vpc-panel-links');
      var linkInv = document.getElementById('topo-link-inventory');
      if (linksPanel && linkInv) linksPanel.appendChild(linkInv);
      if (typeof boardRenderDomain === 'function' && !window._vpcBoardMapLinked) {{
        window._vpcBoardMapLinked = true;
        var _origBoardDom = boardRenderDomain;
        window.boardRenderDomain = function(domainId) {{
          _origBoardDom(domainId);
          if (typeof vpcHighlightDomain === 'function') vpcHighlightDomain(domainId);
        }};
      }}
      if (typeof app !== 'undefined' && app.init) {{
        try {{ app.init(); }} catch(e) {{ console.warn('[VPC_CC] app.init', e); }}
      }}
      vpcBootMap(0);
      setTimeout(function() {{ if (!window._vpcAutoFitDone) vpcBootMap(0); }}, 300);
    }}

    if (document.readyState === 'loading') {{
      document.addEventListener('DOMContentLoaded', vpcCommandCenterInit);
    }} else {{
      vpcCommandCenterInit();
    }}
    var _vpcResizeTimer = null;
    window.addEventListener('resize', function() {{
      if (_vpcResizeTimer) clearTimeout(_vpcResizeTimer);
      _vpcResizeTimer = setTimeout(function() {{
        if (typeof network !== 'undefined' && network) {{
          try {{ network.redraw(); }} catch(e) {{}}
        }}
      }}, 150);
    }});
    """


def vpc_board_host_shell():
    """Engineering board markup (mounted into split pane, no legacy tabs)."""
    from utils import vpc_board_formatter as vbf
    return (
        '<div id="vpc-engineering-board" '
        'style="display:block;border:none;background:transparent;padding:0;">'
        + vbf.vpc_board_inner_html().replace(
            '<div id="vpc-engineering-board">', '', 1
        )
    )
