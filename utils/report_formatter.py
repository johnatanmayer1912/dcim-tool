import os
import csv
import json
import sys
import webbrowser
from datetime import datetime


def _report_error(func_name, filename, error):
    """Log report-writing errors to stderr so they're visible in logs."""
    msg = f"[REPORT ERROR] {func_name}('{filename}'): {error}"
    print(msg, file=sys.stderr)


def write_text_file(filename, lines):
    try:
        if lines is None:
            _report_error("write_text_file", filename, "content is None — skipping write")
            return
        with open(filename, 'w', encoding='utf-8') as f:
            if isinstance(lines, list):
                f.writelines('\n'.join(lines))
            else:
                f.write(lines)
    except Exception as e:
        _report_error("write_text_file", filename, e)

def append_text_file(filename, text):
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(text + "\n")
    except Exception as e:
        _report_error("append_text_file", filename, e)

def write_csv_file(filename, fieldnames, data_rows):
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            w.writeheader()
            w.writerows(data_rows)
    except Exception as e:
        _report_error("write_csv_file", filename, e)

def init_vlan_parsed_report(filename):
    try:
        from utils.output_chrome import text_report_header
        header = text_report_header(
            'VLAN Parsed Inventory',
            hints=[
                'Pipe-delimited table: Host | VLAN ID | Status | Name',
                'Append rows as each device is scanned',
            ],
        )
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(header)
            f.write("Host | VLAN ID | Status | Name/Description\n")
            f.write("-" * 80 + "\n")
    except Exception as e:
        _report_error("init_vlan_parsed_report", filename, e)

def append_vlan_parsed_report(filename, true_host, parsed_data):
    if not parsed_data:
        return
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            for item in parsed_data:
                if len(item) >= 3:
                    f.write(f"{true_host} | {item[0]} | {item[2]} | {item[1]}\n")
    except Exception as e:
        _report_error("append_vlan_parsed_report", filename, e)

def write_files_in_directory(dir_name, file_contents_map):
    try:
        os.makedirs(dir_name, exist_ok=True)
        for fname, content in file_contents_map.items():
            path = os.path.join(dir_name, fname)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content + "\n")
    except Exception as e:
        _report_error("write_files_in_directory", dir_name, e)


def generate_node_interface_html(html_file, true_host, nodes_json, edges_json, vis_js_content, stats=None):
    """
    Generate improved interface topology HTML.

    v6.2.0 improvements:
      - Summary stats bar (total/up/down/err/MAC counts)
      - Search/filter box (by port name, description, VLAN, MAC)
      - 5-state color legend
      - Physics layout with connected ports closer to center
    """
    from html import escape as html_escape
    true_host = html_escape(str(true_host or ''))
    stats = stats or {}
    total = stats.get('total', len(nodes_json) - 1)
    up = stats.get('up', 0)
    down = stats.get('down', 0)
    err = stats.get('err', 0)
    mac = stats.get('mac', 0)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <title>Interface Map: {true_host}</title>
    <style>
      :root {{
        --apple-blue: #007aff;
        --apple-grey: #8e8e93;
        --apple-bg: #f5f5f7;
        --glass-bg: rgba(255, 255, 255, 0.7);
        --glass-border: rgba(255, 255, 255, 0.3);
      }}
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      body {{ 
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Helvetica Neue", sans-serif; 
        background: var(--apple-bg); 
        color: #1d1d1f; 
        padding: 24px;
        -webkit-font-smoothing: antialiased;
      }}
      .header {{ margin-bottom:20px; }}
      .header h2 {{ font-weight:700; color:#1d1d1f; font-size:24px; letter-spacing: -0.5px; }}
      .header p {{ font-size:13px; color:var(--apple-grey); margin-top:4px; }}

      /* Stats bar */
      .stats-bar {{
        display:flex; gap:12px; flex-wrap:wrap; margin-bottom:20px;
      }}
      .stat-card {{
        flex:1; min-width:110px; padding:14px; border-radius:14px;
        text-align:center; color:white; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        transition: transform 0.2s ease;
      }}
      .stat-card:hover {{ transform: translateY(-2px); }}
      .stat-card .num {{ font-size:24px; font-weight:700; line-height:1; }}
      .stat-card .lbl {{ font-size:10px; margin-top:4px; opacity:0.9; font-weight:600; text-transform: uppercase; letter-spacing: 0.5px; }}

      /* Search toolbar */
      .toolbar {{
        display:flex; gap:12px; align-items:center; flex-wrap:wrap;
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius:14px; padding:12px 16px;
        margin-bottom:16px; box-shadow: 0 8px 32px rgba(0,0,0,0.05);
      }}
      .toolbar input {{
        border: 1px solid #d2d2d7; border-radius:10px; padding:8px 12px;
        font-size:14px; outline:none; min-width:240px; flex:1;
        background: rgba(255,255,255,0.8);
        transition: all 0.2s;
      }}
      .toolbar input:focus {{ border-color:var(--apple-blue); box-shadow: 0 0 0 4px rgba(0,122,255,0.1); }}
      .toolbar button {{
        background: var(--apple-blue); color:white; border:none; border-radius:10px;
        padding:8px 16px; font-size:13px; font-weight:600; cursor:pointer;
        transition: all 0.2s;
      }}
      .toolbar button:hover {{ background: #0071e3; }}
      .toolbar button.secondary {{
        background: #e8e8ed; color:#1d1d1f;
      }}
      .toolbar button.secondary:hover {{ background: #d2d2d7; }}
      
      .filter-btns {{ display:flex; gap:8px; flex-wrap:wrap; }}
      .filter-btn {{
        padding:6px 12px; border-radius:12px; font-size:12px; cursor:pointer;
        border:2px solid transparent; transition:all 0.2s;
        font-weight: 500;
      }}
      .filter-btn.active {{ transform: scale(1.05); box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
      .filter-btn:hover {{ opacity:0.9; }}

      /* Legend */
      .legend {{
        display:flex; gap:16px; flex-wrap:wrap; margin-bottom:16px;
        font-size:12px; color:#86868b;
        padding: 0 8px;
      }}
      .leg-item {{ display:flex; align-items:center; gap:6px; font-weight: 500; }}
      .box {{ width:10px; height:10px; border-radius:50%; }}

      /* Network canvas */
      #net {{
        width:100%; height:calc(100vh - 300px);
        background:white; border-radius:20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.06);
        border:1px solid #d2d2d7;
      }}
      div.vis-tooltip {{
        background: rgba(255,255,255,0.95) !important; 
        backdrop-filter: blur(10px);
        padding: 0 !important;
        border-radius: 14px !important;
        box-shadow: 0 12px 48px rgba(0,0,0,0.15) !important;
        border: 1px solid rgba(0,0,0,0.05) !important;
      }}
      #filterStatus {{
        font-size:12px; color:#86868b; padding:4px 10px;
        background:#e8e8ed; border-radius:8px;
        font-weight: 500;
      }}
    </style>
  <script type="text/javascript">{vis_js_content}</script>
</head>
<body>
  <div class="header">
    <h2>&#x1F5A5;&#xFE0F; Interface Map: {true_host}</h2>
    <p>Port-level topology &bull; {total} interfaces &bull; Click a port for details</p>
  </div>

  <!-- Stats bar -->
  <div class="stats-bar">
    <div class="stat-card" style="background:#27ae60;">
      <div class="num">{up}</div><div class="lbl">&#x2191; Up / Connected</div>
    </div>
    <div class="stat-card" style="background:#e74c3c;">
      <div class="num">{down}</div><div class="lbl">&#x2193; Down</div>
    </div>
    <div class="stat-card" style="background:#f39c12;">
      <div class="num">{err}</div><div class="lbl">&#x26A0; Err-Disabled</div>
    </div>
    <div class="stat-card" style="background:#1abc9c;">
      <div class="num">{mac}</div><div class="lbl">&#x1F3F4; MAC Learned</div>
    </div>
    <div class="stat-card" style="background:#95a5a6;">
      <div class="num">{total}</div><div class="lbl">Total Ports</div>
    </div>
  </div>

  <!-- Search & filter toolbar -->
  <div class="toolbar">
    <span style="font-size:12px; color:#7f8c8d; font-weight:600;">&#x1F50D;</span>
    <input type="text" id="searchInput" placeholder="Search port, description, VLAN, MAC..."
           oninput="filterPorts(this.value)" />
    <button class="secondary" onclick="clearFilter()">&#x2715; Clear</button>
    <span style="color:#dfe6e9;">|</span>
    <div class="filter-btns">
      <button class="filter-btn active" id="btn-all"
              style="background:#2c3e50; color:white; border-color:#2c3e50;"
              onclick="setGroupFilter('all')">All</button>
      <button class="filter-btn" id="btn-connected"
              style="background:#e8f8f0; color:#27ae60; border-color:#27ae60;"
              onclick="setGroupFilter('connected')">&#x2191; Up</button>
      <button class="filter-btn" id="btn-occupied"
              style="background:#e8f8f5; color:#1abc9c; border-color:#1abc9c;"
              onclick="setGroupFilter('occupied')">&#x1F3F4; MAC</button>
      <button class="filter-btn" id="btn-err"
              style="background:#fdf0f0; color:#c0392b; border-color:#c0392b;"
              onclick="setGroupFilter('err')">&#x26A0; Err</button>
      <button class="filter-btn" id="btn-down"
              style="background:#fef9f0; color:#e67e22; border-color:#e67e22;"
              onclick="setGroupFilter('configured_down')">&#x2193; Down</button>
    </div>
    <span id="filterStatus"></span>
  </div>

  <!-- Legend -->
  <div class="legend">
    <div class="leg-item"><div class="box" style="background:#2ecc71;"></div>Connected</div>
    <div class="leg-item"><div class="box" style="background:#1abc9c;"></div>Connected + MAC</div>
    <div class="leg-item"><div class="box" style="background:#e67e22;"></div>Configured / Down</div>
    <div class="leg-item"><div class="box" style="background:#c0392b;"></div>Err-Disabled</div>
    <div class="leg-item"><div class="box" style="background:#7f8c8d;"></div>Admin Down</div>
    <div class="leg-item"><div class="box" style="background:#ecf0f1; border:1px solid #ccc;"></div>Unused</div>
  </div>

  <div id="net"></div>

  <script>
    var nodesData = {json.dumps(nodes_json)};
    var edgesData = {json.dumps(edges_json)};

    // Convert HTML tooltips to DOM elements
    nodesData.forEach(function(n) {{
      if (n.title && typeof n.title === 'string' && n.title.indexOf('<') !== -1) {{
        var div = document.createElement('div');
        div.innerHTML = n.title;
        n.title = div;
      }}
    }});

    var allNodes = new vis.DataSet(nodesData);
    var allEdges = new vis.DataSet(edgesData);

    var net = new vis.Network(
      document.getElementById('net'),
      {{ nodes: allNodes, edges: allEdges }},
      {{
        physics: {{
          forceAtlas2Based: {{
            gravitationalConstant: -80,
            centralGravity: 0.005,
            springLength: 120,
            springConstant: 0.06,
            damping: 0.4
          }},
          solver: 'forceAtlas2Based',
          stabilization: {{ iterations: 200 }}
        }},
        interaction: {{
          hover: true, tooltipDelay: 80,
          navigationButtons: true, keyboard: true
        }}
      }}
    );

    // ── Search & Filter ───────────────────────────────────────────────────────
    var currentGroupFilter = 'all';
    var currentTextFilter = '';

    function normalizeMacHex(s) {{
      return (s || '').replace(/[.:\\-\\s_]/g, '').toLowerCase();
    }}
    function macQueryMatches(haystack, query) {{
      var q = normalizeMacHex(query);
      if (!q) return false;
      var h = normalizeMacHex(haystack);
      return h.indexOf(q) !== -1;
    }}
    function nodeMacMatch(node, q) {{
      if (!q) return true;
      if (node.macs_search && macQueryMatches(node.macs_search, q)) return true;
      if (node.macs && node.macs.some(function(m) {{ return macQueryMatches(m, q); }})) return true;
      return false;
    }}

    function applyFilters() {{
      var q = currentTextFilter.toLowerCase().trim();
      var updates = [];
      var visibleCount = 0;

      nodesData.forEach(function(n) {{
        if (n.id === 'switch') {{
          updates.push({{ id: n.id, hidden: false }});
          return;
        }}

        // Group filter
        var groupMatch = (currentGroupFilter === 'all') || (n.group === currentGroupFilter);

        // Text filter (port, desc, VLAN, speed, MAC — format-agnostic)
        var textMatch = !q ||
          n.id.toLowerCase().indexOf(q) !== -1 ||
          (n.desc && n.desc.toLowerCase().indexOf(q) !== -1) ||
          (n.vlan && n.vlan.toLowerCase().indexOf(q) !== -1) ||
          (n.speed && n.speed.toLowerCase().indexOf(q) !== -1) ||
          (n.label && n.label.toLowerCase().indexOf(q) !== -1) ||
          nodeMacMatch(n, q);

        var visible = groupMatch && textMatch;
        if (visible) visibleCount++;
        updates.push({{ id: n.id, hidden: !visible }});
      }});

      allNodes.update(updates);

      // Update edge visibility to match node visibility
      var hiddenNodes = new Set(
        updates.filter(function(u) {{ return u.hidden; }}).map(function(u) {{ return u.id; }})
      );
      var edgeUpdates = edgesData.map(function(e) {{
        return {{ id: e.id || undefined, from: e.from, to: e.to,
                  hidden: hiddenNodes.has(e.to) }};
      }});
      allEdges.update(edgeUpdates);

      var total_visible = nodesData.filter(function(n) {{ return n.id !== 'switch'; }}).length;
      document.getElementById('filterStatus').textContent =
        visibleCount + ' / ' + total_visible + ' ports';
    }}

    function filterPorts(q) {{
      currentTextFilter = q;
      applyFilters();
    }}

    function setGroupFilter(group) {{
      currentGroupFilter = group;
      // Update button styles
      ['all','connected','occupied','err','down'].forEach(function(g) {{
        var btn = document.getElementById('btn-' + (g === 'configured_down' ? 'down' : g));
        if (btn) btn.classList.remove('active');
      }});
      var activeId = group === 'configured_down' ? 'btn-down' : 'btn-' + group;
      var activeBtn = document.getElementById(activeId);
      if (activeBtn) activeBtn.classList.add('active');
      applyFilters();
    }}

    function clearFilter() {{
      document.getElementById('searchInput').value = '';
      currentTextFilter = '';
      currentGroupFilter = 'all';
      setGroupFilter('all');
    }}
  </script>
</body>
</html>"""
    try:
        with open(html_file, 'w', encoding='utf-8', errors='replace') as f:
            f.write(html_content)
        webbrowser.open('file://' + os.path.realpath(html_file))
    except Exception:
        pass

def generate_topology_html(html_file, num_nodes, num_edges, nodes_str, edges_str, vis_js_content,
                         extra_header="", map_mode="all", board_payload_json=None,
                         presentation_json=None, briefing_extra=None,
                         utilization_overlay=None):
    import json as _json
    from utils import vpc_board_formatter as vbf
    from utils.topo_map_shell import (
        embed_link_inventory_html,
        embed_link_inventory_js,
        link_rows_from_edges,
        read_version_label,
        script_safe_json,
        shell_css,
    )
    from utils import standard_map_shell as sms

    vpc_board_block = ""
    vpc_board_script = ""
    vpc_extra_style = shell_css('#8b5cf6')
    map_hidden_class = ""
    l2_toggle_btn = ""
    stats_hint = "Topology Map (default) — Link Inventory tab for table view"
    version_label = read_version_label()
    vpc_init_script = ""
    body_class = ""
    nst_standard_map_flag = "false"
    vpc_layout_hidden = ""
    link_rows_json = "[]"
    link_shell_html = ""
    link_shell_js = ""
    topo_map_hidden = ""
    standard_map_css = ""
    standard_map_style_bar = ""
    standard_map_pane = ""
    standard_top_chrome = ""
    legacy_header_block = ""
    briefing_json = "{}"
    use_standard_split = map_mode == 'all'
    # DEBUG: Log map mode and split decision
    try:
        _edges_list = _json.loads(edges_str) if edges_str else []
        _nodes_list = _json.loads(nodes_str) if nodes_str else []
        _link_rows = link_rows_from_edges(_edges_list, _nodes_list)
        link_rows_json = _json.dumps(_link_rows)
        if use_standard_split:
            _brief = sms.build_briefing_stats(_edges_list, _nodes_list, briefing_extra or {})
            briefing_json = _json.dumps(_brief)
            standard_map_css = sms.standard_map_shell_css()
            # DEBUG: Log CSS injection
            standard_map_style_bar = sms.embed_standard_map_style_bar()
            standard_map_pane = sms.embed_standard_map_pane_html()
            # Phase 6 Wave 3 — reuse authoritative Program Status builder
            from utils.discovery_program_status import (
                program_status_for_inventory_standard_l2,
            )
            _ps = program_status_for_inventory_standard_l2(
                num_devices=num_nodes, num_links=num_edges,
            )
            standard_top_chrome = sms.embed_standard_map_top_chrome(
                version_label, num_nodes, num_edges, extra_header,
                program_status=_ps,
            )
            legacy_header_block = ""
            _overlay_payload = {
                'ok': False,
                'available': False,
                'error': None,
                'mode': None,
                'evidence_class': None,
                'doc': None,
                'bindings': {},
                'l2_edge_count': 0,
                'painted_count': 0,
                'banner': (
                    'Utilization paints existing L2 links only. It is not topology. '
                    'Gray dashed = no sample — not down. Overlay never creates cables.'
                ),
                'replay_label': 'Replay snapshot — not a live poll.',
                'live_label': 'Live SSH counters — not SNMP.',
                'unmapped_title': 'Unmapped interfaces (not drawn)',
            }
            try:
                from utils.utilization_overlay import bind_overlay_to_standard_l2
                _bound = bind_overlay_to_standard_l2(
                    _nodes_list, _edges_list, utilization_overlay,
                )
                _overlay_payload = _bound.as_embed_payload()
            except Exception:
                _overlay_payload['error'] = 'utilization overlay unavailable'
            link_shell_js = (
                sms.embed_standard_map_js(link_rows_json, briefing_json)
                + sms.embed_utilization_overlay_js(script_safe_json(_overlay_payload))
            )
            stats_hint = "Standard Map — Tier default · map + connection index side-by-side"
            body_class = "nst-standard-map"
            nst_standard_map_flag = "true"
            # DEBUG: Log body class and standard map flag
        else:
            link_shell_html = embed_link_inventory_html(
                links_hidden=True,
                map_hidden=False,
                map_default=True,
            )
            link_shell_js = embed_link_inventory_js(link_rows_json, map_default=True)
            topo_map_hidden = ""
    except Exception:
        link_shell_html = ""
        link_shell_js = ""
        use_standard_split = False

    if use_standard_split:
        layout_container_class = "layout-container nst-standard-split"
        map_column_inner = f"""
      <div class="nst-map-col">
      {standard_map_style_bar}
      <div id="mynetwork" class="nst-map-main"{map_hidden_class}{topo_map_hidden}>
        <div id="network-fallback" style="padding:60px 40px;text-align:center;background:#0f172a;height:100%;display:flex;flex-direction:column;justify-content:center;align-items:center;">
          <div style="font-size:48px;margin-bottom:20px;">&#127760;</div>
          <h2 style="color:#f1f5f9;margin-bottom:16px;font-size:24px;">Standard L2 Map</h2>
          <p style="color:#94a3b8;margin-bottom:24px;max-width:400px;">Initializing tier topology…</p>
        </div>
      </div>
      </div>
      {standard_map_pane}
"""
    else:
        layout_container_class = "layout-container"
        map_column_inner = f"""
      <div class="map-column" style="flex:1;display:flex;flex-direction:column;min-width:0;height:100%;">
      {link_shell_html}
      <div id="mynetwork"{map_hidden_class}{topo_map_hidden}>
        <div id="network-fallback" style="padding:60px 40px;text-align:center;background:#0f172a;height:100%;display:flex;flex-direction:column;justify-content:center;align-items:center;">
          <div style="font-size:48px;margin-bottom:20px;">&#127760;</div>
          <h2 style="color:#f1f5f9;margin-bottom:16px;font-size:24px;">Network Topology Map</h2>
          <p style="color:#94a3b8;margin-bottom:24px;max-width:400px;">Initializing visualization...</p>
          <div style="background:#1e293b;border-radius:8px;padding:16px 24px;margin-top:16px;">
            <p style="color:#64748b;font-size:12px;margin:0;">If this message persists, check browser console (F12) for errors</p>
          </div>
        </div>
      </div>
      </div>
"""

    if map_mode == 'vpc':
        from utils import vpc_map_shell as vms
        layout_options = """
      layout: { improvedLayout: false },
      physics: { enabled: false },"""
        vpc_extra_style = vbf.vpc_board_css() + vms.vpc_light_css() + shell_css('#4f46e5')
        vpc_board_block = vms.vpc_board_host_shell() + vms.vpc_command_center_tabs_html()
        pres_json = presentation_json or board_payload_json or '{"domains":[]}'
        vpc_board_script = vbf.vpc_board_js_initializer(
            board_payload_json or '{"domains":[]}', command_center=True,
        )
        vpc_board_script += vms.vpc_shell_js(pres_json, board_payload_json or '{"domains":[]}')
        map_hidden_class = ""
        l2_toggle_btn = '<button type="button" onclick="toggleNonVpcEdges()">Show non-vPC links</button>'
        stats_hint = "VPC Command Center — Overview shows board + map; use tabs for links and raw data"
        body_class = "vpc-light vpc-command-center"
        vpc_layout_hidden = ' style="display:none !important;"'
        vpc_init_script = """
    window._showNonVpcEdges = false;
    function toggleNonVpcEdges() {
      window._showNonVpcEdges = !window._showNonVpcEdges;
      vpcApplyGraphVisibility();
      if (network) vpcFitTopology(40);
    }
    function vpcEdgeIsAdjacency(e) {
      return e.hidden === true || e.color === '#bdc3c7' || e.edge_hidden === true;
    }
    function vpcApplyGraphVisibility() {
      if (!edges) return;
      var updates = [];
      edges.forEach(function(e) {
        if (vpcEdgeIsAdjacency(e)) {
          updates.push({ id: e.id, hidden: !window._showNonVpcEdges });
        }
      });
      if (updates.length) edges.update(updates);
    }
    function vpcFitTopology(pad) {
      if (!network || !nodes) return;
      if (window._vpcFitTimer) clearTimeout(window._vpcFitTimer);
      window._vpcFitTimer = setTimeout(function() {
        window._vpcFitTimer = null;
        var visible = nodes.get({
          filter: function(n) { return !n.hidden; }
        });
        if (!visible.length) {
          try { network.fit({ animation: false }); } catch (e) {}
          return;
        }
        try {
          network.fit({
            nodes: visible.map(function(n) { return n.id; }),
            animation: false,
            padding: pad || 40
          });
        } catch (e) {
          try { network.fit({ animation: false }); } catch (e2) {}
        }
      }, 50);
    }
    function vpcHighlightDomain(domainId) {
      if (!network || !nodes || !domainId) return;
      var nodeId = 'VPC_Domain_' + domainId;
      var members = [];
      try {
        var dom = (window.__VPC_BOARD__ && window.__VPC_BOARD__.domains || []).find(function(d) {
          return String(d.domain_id) === String(domainId);
        });
        if (dom && dom.peers) dom.peers.forEach(function(p) { members.push(p.hostname); });
      } catch (e) {}
      var focus = [nodeId].concat(members).filter(Boolean);
      nodes.update(nodes.get().map(function(n) {
        var on = focus.indexOf(n.id) >= 0 || (n.vpc_domain_id && String(n.vpc_domain_id) === String(domainId));
        return {
          id: n.id,
          opacity: on ? 1 : 0.25,
          borderWidth: on ? 4 : 2
        };
      }));
      network.selectNodes(focus.filter(function(id) { return nodes.get(id); }));
      vpcFitTopology(60);
    }
"""
    else:
        layout_options = """
      layout: {
        hierarchical: {
          enabled: true,
          direction: 'UD',
          sortMethod: 'directed',
          levelSeparation: 180,
          nodeSpacing: 160,
          treeSpacing: 200,
          blockShifting: true,
          edgeMinimization: true,
          parentCentralization: true
        }
      },
      physics: { enabled: false },"""

    if not use_standard_split:
        legacy_header_block = f"""
  <div class="header">
    <h2>&#x1F5FA;&#xFE0F; {"vPC Domain Topology" if map_mode == "vpc" else "Network Topology Map"} <span style="font-size:14px; color:#a78bfa;">{version_label}</span></h2>
    <div class="stats">{num_nodes} Nodes &middot; {num_edges} Links &middot; <span style="color:#6366f1;">{stats_hint}</span></div>
  </div>
  {extra_header}
  {vpc_board_block}

  <div class="topo-toolbar">
    <span style="font-size:12px; color:#a0aec0; font-weight:600;">&#x1F50D; Search:</span>
    <input type="text" id="searchInput" placeholder="Device, role, IP, port, Po, vPC domain, MAC..." oninput="searchNodes(this.value); if(typeof topoShellSearch==='function') topoShellSearch(this.value);" />
    <button onclick="clearSearch()">&#x2715; Clear</button>
    <span style="color:rgba(255,255,255,0.2);">|</span>
    <button id="descToggleBtn" onclick="toggleDescriptions()">Show Descriptions</button>
    {l2_toggle_btn}
  </div>

  <div class="legend">
    <div class="legend-item"><div class="box" style="background:#0072B2"></div> Standard Link</div>
    <div class="legend-item"><div class="box" style="background:#009E73"></div> Port-Channel</div>
    <div class="legend-item"><div class="box" style="background:#E69F00"></div> vPC Member</div>
    <div class="legend-item"><div class="box" style="background:#CC79A7"></div> vPC Peer-Link</div>
    <div class="legend-item"><div class="box" style="background:#56B4E9"></div> vPC Shared</div>
    <div class="legend-item"><div class="box" style="background:#D55E00"></div> Orphan/Mismatch</div>
    <div class="legend-item"><div class="box" style="background:#F0E442"></div> Asymmetric</div>
  </div>
"""

    # DEBUG: Log before HTML generation
    if use_standard_split:
        legacy_aside_html = (
            '<!-- Standard L2 uses nst-conn-panel; legacy side panels omitted -->\n'
        )
    else:
        legacy_aside_html = r'''<!-- VIEW 1: Standard Node/Edge Details Panel -->
      <div id="side-panel" class="side-panel">
          <div id="panel-content">
              <h3>Select a Node or Link</h3>
              <p>Click on any element in the graph to view detailed troubleshooting data.</p>
          </div>
      </div>
      
       <!-- VIEW 2: VPC Detail Panel (shown when VPC domain clicked) -->
      <div id="vpc-detail-panel" class="side-panel">
          <div class="vpc-detail-header">
              <div class="panel-nav">
                  <button class="nav-btn" onclick="app.goBack()">&#x2715; Close</button>
              </div>
              <div style="display:flex; justify-content:space-between; align-items:center;">
                  <h2 id="vpc-detail-title">VPC Domain</h2>
                  <div id="vpc-health-badge" class="health-badge healthy">100%</div>
              </div>
              <div class="vpc-domain-badge">
                  <span id="vpc-detail-id">Domain ID: --</span>
              </div>
          </div>
          
          <div class="panel-section">
              <div class="panel-title">Intelligence & Correlation</div>
              <div id="vpc-correlation-content" style="margin-bottom: var(--space-sm);">
                  <!-- Dynamic Alerts -->
              </div>
          </div>
          
          <!-- Peer Link Visualization -->
          <div class="peer-link-section">
              <div class="peer-link-title">vPC Peer Link (Keepalive + CFS)</div>
              <div class="peer-link-visual" id="peer-link-visual">
                  <span id="peer-member-1">--</span>
                  <div class="peer-link-line"></div>
                  <span id="peer-member-2">--</span>
              </div>
              <div id="peer-link-port" class="peer-meta-line">Port: --</div>
              <div id="peer-keepalive-status" class="peer-meta-line">Keepalive: --</div>
              <div id="peer-link-status" class="peer-meta-line">Peer-Link: --</div>
          </div>
          
          <!-- Member Devices -->
          <div class="vpc-members-grid" id="vpc-members-grid">
              <!-- Populated by JavaScript -->
          </div>
          
          <!-- Member Interfaces -->
          <div class="vpc-interfaces-list">
              <div class="category-header">
                  <span>&#128203;</span> Member Interfaces & vPCs
              </div>
              <div id="vpc-interfaces-content">
                  <!-- Populated by JavaScript -->
              </div>
          </div>
          
          <div class="panel-section">
              <div class="panel-title">Per-vPC Consistency (show vpc table)</div>
              <div id="vpc-consistency-summary" style="font-size: 11px; background: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0; max-height: 150px; overflow-y: auto;">
                  Checking per-vPC rows...
              </div>
          </div>
          <div class="panel-section">
              <div class="panel-title">Global Consistency Parameters (CLI)</div>
              <pre id="vpc-global-consistency-panel" style="font-size: 10px; font-family: monospace; white-space: pre-wrap; background: #0f172a; color: #e2e8f0; padding: 10px; border-radius: 6px; max-height: 180px; overflow-y: auto;">—</pre>
          </div>
          
          <!-- Action Buttons -->
          <div class="panel-actions">
              <button class="action-btn primary" onclick="app.showConnectionIntelligence()">
                  &#128161; Connection Intelligence
              </button>
              <button class="action-btn secondary" onclick="app.highlightVPCDomain()">
                  &#128064; Highlight on Map
              </button>
          </div>
      </div>
      
      <!-- VIEW 3: Connection Intelligence Panel -->
      <div id="connection-intelligence-panel" class="side-panel">
          <div class="intel-header">
              <div>
                  <div class="panel-nav">
                      <button class="nav-btn" onclick="app.goBack()">&#x2190; Back</button>
                  </div>
                  <h2 id="intel-domain-title">Connection Intelligence</h2>
              </div>
          </div>
          
          <!-- Shared Connections -->
          <div class="connection-section">
              <div class="section-header shared">
                  <span>&#9989;</span> Shared Connections (Dual-Homed)
              </div>
              <div id="shared-connections-list">
                  <!-- Populated by JavaScript -->
              </div>
          </div>
          
          <!-- Non-Shared Connections -->
          <div class="connection-section">
              <div class="section-header orphan">
                  <span>&#9888;&#65039;</span> Non-Shared Connections (Single-Homed)
              </div>
              <div id="orphan-connections-list">
                  <!-- Populated by JavaScript -->
              </div>
          </div>
          
          <!-- Action Buttons -->
          <div class="panel-actions">
              <button class="action-btn" onclick="app.exportConnectionReport()">
                  &#128190; Export Report
              </button>
              <button class="action-btn secondary" onclick="app.goBack()">
                  Close
              </button>
          </div>
      </div>
'''

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{"Standard L2 Map" if use_standard_split else "Network Topology Map"}</title>
  <style>
    /* ============================================
       DESIGN SYSTEM v8.5 - NOC DASHBOARD STYLE
       ============================================ */
    :root {{{{
      --accent-primary: #007aff;
      --accent-secondary: #5856d6;
      --accent-gradient: linear-gradient(135deg, #007aff 0%, #5856d6 100%);
      
      /* NOC Dark Theme Palette */
      --bg-deep: #000000;
      --bg-surface: #1c1c1e;
      --bg-glass: rgba(28, 28, 30, 0.85);
      --border-glass: rgba(255, 255, 255, 0.12);
      
      --text-primary: #ffffff;
      --text-secondary: #8e8e93;
      --text-muted: #48484a;
      
      --radius-apple: 14px;
      --radius-pill: 20px;
      
      --shadow-premium: 0 20px 40px rgba(0,0,0,0.4);
      --glow-blue: 0 0 20px rgba(0, 122, 255, 0.3);
    }}

    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    
    body {{ 
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", system-ui, sans-serif; 
      background: var(--bg-deep); 
      color: var(--text-primary); 
      padding: 24px; 
      overflow: hidden;
      font-size: 13px;
      -webkit-font-smoothing: antialiased;
    }}

    body.vpc-command-center {{
      overflow-y: auto !important;
      overflow-x: hidden !important;
      min-height: 100vh;
    }}
    body.vpc-command-center #mynetwork.vpc-map-pane {{
      flex: 0 0 auto;
      height: clamp(420px, 50vh, 680px);
      max-height: 680px;
      min-height: 420px;
      overflow: hidden;
    }}
    
    /* Animations */
    @keyframes pulse-ring {{
      0% {{ transform: scale(0.33); }}
      80%, 100% {{ opacity: 0; }}
    }}
    
    @keyframes marching-ants {{
      from {{ stroke-dashoffset: 20; }}
      to {{ stroke-dashoffset: 0; }}
    }}

    .header {{ 
      display: flex; 
      justify-content: space-between; 
      align-items: center; 
      margin-bottom: 24px; 
      flex-wrap: wrap; 
      gap: 16px; 
    }}
    
    h2 {{ 
      color: var(--text-primary); 
      font-weight: 700; 
      font-size: 26px; 
      letter-spacing: -0.5px;
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    
    .stats-summary {{ 
      background: var(--bg-surface);
      backdrop-filter: blur(20px);
      border: 1px solid var(--border-glass);
      padding: 8px 16px; 
      border-radius: var(--radius-pill); 
      font-size: 13px; 
      color: var(--text-secondary);
      font-weight: 500;
      box-shadow: var(--shadow-premium);
    }}
    
    /* Layout Containers */
    #main-container {{
      display: flex;
      gap: 24px;
      height: calc(100vh - 100px);
      width: 100%;
    }}

    #mynetwork {{ 
      flex: 1;
      height: 100%;
      background: radial-gradient(circle at 50% 50%, #1c1c1e 0%, #000000 100%); 
      border-radius: 24px; 
      box-shadow: inset 0 0 100px rgba(0,122,255,0.05);
      border: 1px solid var(--border-glass);
      transition: flex 0.28s ease, margin 0.28s ease;
      position: relative;
    }}

    #mynetwork.panel-open {{
      margin-right: 400px;
    }}

    /* Floating Panels */
    .side-panel {{
      position: fixed;
      top: 100px;
      right: 24px;
      bottom: 24px;
      width: 380px;
      background: var(--bg-glass) !important;
      backdrop-filter: blur(30px) saturate(180%) !important;
      -webkit-backdrop-filter: blur(30px) saturate(180%) !important;
      border: 1px solid var(--border-glass) !important;
      border-radius: 24px !important;
      display: none;
      flex-direction: column;
      box-shadow: var(--shadow-premium);
      z-index: 1000;
      overflow: hidden;
      animation: slideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    
    .header {{ 
      display: flex; 
      justify-content: space-between; 
      align-items: center; 
      margin-bottom: var(--space-sm); 
      flex-wrap: wrap; 
      gap: var(--space-sm); 
    }}
    
    h2 {{ 
      color: var(--text-primary); 
      font-weight: 300; 
      font-size: 22px; 
    }}
    
    .stats {{ 
      background: var(--border-light); 
      padding: var(--space-sm) var(--space-md); 
      border-radius: var(--radius-md); 
      font-size: 13px; 
      color: var(--text-secondary); 
    }}
    
    .legend {{ 
      display: flex; 
      gap: var(--space-md); 
      margin-bottom: var(--space-sm); 
      font-size: 11px; 
      color: var(--text-secondary); 
      flex-wrap: wrap; 
    }}
    
    .legend-item {{ 
      display: flex; 
      align-items: center; 
      gap: var(--space-xs); 
    }}
    
    .box {{ 
      width: 12px; 
      height: 12px; 
      border-radius: var(--radius-xs); 
    }}
    
    /* Toolbar */
    .topo-toolbar {{
      display: flex; 
      gap: var(--space-sm); 
      align-items: center; 
      flex-wrap: wrap;
      background: var(--border-light); 
      border-radius: var(--radius-md);
      padding: var(--space-sm) var(--space-md); 
      margin-bottom: var(--space-sm);
    }}
    
    .topo-toolbar input {{
      background: rgba(255,255,255,0.1); 
      border: 1px solid var(--border-medium);
      color: var(--text-primary); 
      border-radius: var(--radius-sm); 
      padding: 6px 10px; 
      font-size: 13px; 
      outline: none; 
      min-width: 180px;
    }}
    
    .topo-toolbar button {{
      background: rgba(255,255,255,0.15); 
      border: 1px solid var(--border-medium);
      color: var(--text-primary); 
      border-radius: var(--radius-sm); 
      padding: 6px 12px; 
      font-size: 12px; 
      cursor: pointer; 
      transition: all var(--transition-fast);
    }}
    
    .topo-toolbar button:hover {{ 
      background: rgba(255,255,255,0.25); 
    }}
    
    .topo-toolbar button.active {{
      background: var(--vpc-primary);
      border-color: var(--vpc-primary);
    }}
    
    /* Layout Container */
    .layout-container {{
      display: flex; 
      gap: var(--space-md); 
      height: calc(100vh - 160px);
      position: relative;
    }}
    
    /* Network Graph */
    #mynetwork {{
      flex: 1; 
      height: 100%; 
      border: 1px solid var(--bg-tertiary); 
      border-radius: var(--radius-lg);
      background: var(--bg-primary); 
      background-image: radial-gradient(var(--bg-secondary) 1px, transparent 1px);
      background-size: 20px 20px;
      box-shadow: var(--shadow-lg);
      transition: flex var(--transition-base);
    }}
    
    #mynetwork.panel-open {{
      flex: 0 0 calc(100% - 480px);
    }}
    
    /* ============================================
       SIDE PANELS - 3 View System
       ============================================ */
    
    /* Base Panel Styles */
    .side-panel {{
      width: 460px; 
      background: var(--bg-panel); 
      color: var(--text-dark); 
      border-radius: var(--radius-lg);
      padding: var(--space-md); 
      overflow-y: auto; 
      box-shadow: var(--shadow-lg);
      display: none; 
      flex-direction: column; 
      font-size: 13px;
      position: relative;
      animation: slideIn var(--transition-base);
    }}
    
    @keyframes slideIn {{
      from {{ opacity: 0; transform: translateX(20px); }}
      to {{ opacity: 1; transform: translateX(0); }}
    }}
    
    /* VIEW 1: Standard Side Panel (Node/Edge details) */
    #side-panel {{
      composes: side-panel;
    }}
    
    #side-panel h3 {{ 
      color: var(--text-dark); 
      font-size: 16px; 
      margin-bottom: var(--space-sm); 
      border-bottom: 2px solid var(--vpc-primary); 
      padding-bottom: var(--space-xs); 
    }}
    
    /* VIEW 2: VPC Detail Panel */
    #vpc-detail-panel {{
      composes: side-panel;
    }}
    
    .vpc-detail-header {{
      background: var(--vpc-gradient);
      color: white;
      margin: calc(-1 * var(--space-md));
      margin-bottom: var(--space-md);
      padding: var(--space-lg);
      border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    }}
    
    .vpc-detail-header h2 {{
      color: white;
      font-size: 24px;
      font-weight: 700;
      margin: 0;
    }}
    
    .vpc-domain-badge {{
      display: inline-flex;
      align-items: center;
      gap: var(--space-xs);
      background: rgba(255,255,255,0.2);
      padding: var(--space-xs) var(--space-sm);
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      margin-top: var(--space-sm);
    }}
    
    /* Member Cards Grid */
    .vpc-members-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: var(--space-md);
      margin-bottom: var(--space-lg);
    }}
    
    .vpc-member-card {{
      background: var(--bg-secondary);
      border: 2px solid var(--border-light);
      border-radius: var(--radius-md);
      padding: var(--space-md);
      text-align: center;
      transition: all var(--transition-fast);
    }}
    
    .vpc-member-card:hover {{
      border-color: var(--vpc-primary);
      box-shadow: var(--shadow-md);
    }}
    
    .vpc-member-card.primary {{
      border-color: var(--vpc-primary);
      background: linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(139,92,246,0.1) 100%);
    }}
    
    .member-icon {{
      font-size: 32px;
      margin-bottom: var(--space-xs);
    }}
    
    .member-name {{
      font-weight: 700;
      font-size: 14px;
      color: var(--text-dark);
    }}
    
    .member-role {{
      font-size: 11px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    
    .member-ip {{
      font-family: monospace;
      font-size: 11px;
      color: var(--vpc-primary);
      margin-top: var(--space-xs);
    }}
    
    /* Peer Link Display */
    .peer-link-section {{
      background: linear-gradient(135deg, rgba(168,85,247,0.1) 0%, rgba(139,92,246,0.1) 100%);
      border: 2px solid var(--peer-link);
      border-radius: var(--radius-md);
      padding: var(--space-md);
      margin-bottom: var(--space-lg);
      text-align: center;
    }}
    
    .peer-link-title {{
      font-size: 11px;
      text-transform: uppercase;
      color: var(--peer-link);
      font-weight: 700;
      letter-spacing: 1px;
      margin-bottom: var(--space-sm);
    }}
    
    .peer-link-visual {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: var(--space-md);
      font-size: 14px;
    }}
    
    .peer-link-line {{
      flex: 1;
      height: 3px;
      background: linear-gradient(90deg, var(--peer-link) 0%, var(--vpc-accent) 100%);
      border-radius: 2px;
      position: relative;
    }}
    
    .peer-meta-line {{
      margin-top: 6px;
      font-size: 12px;
      color: #64748b;
      line-height: 1.5;
    }}
    .peer-meta-line .status-ok {{ color: #22c55e; font-weight: 600; }}
    .peer-meta-line .status-warn {{ color: #f59e0b; font-weight: 600; }}
    .peer-meta-line .status-bad {{ color: #ef4444; font-weight: 600; }}

    .peer-link-line::after {{
      content: '';
      position: absolute;
      left: 50%;
      top: 50%;
      transform: translate(-50%, -50%);
      width: 8px;
      height: 8px;
      background: white;
      border: 2px solid var(--peer-link);
      border-radius: 50%;
    }}
    
    /* Interface List */
    .vpc-interfaces-list {{
      background: var(--bg-secondary);
      border-radius: var(--radius-md);
      padding: var(--space-md);
    }}
    
    .interface-category {{
      margin-bottom: var(--space-md);
    }}
    
    .interface-category:last-child {{
      margin-bottom: 0;
    }}
    
    .category-header {{
      display: flex;
      align-items: center;
      gap: var(--space-xs);
      font-size: 12px;
      font-weight: 700;
      color: var(--text-dark);
      margin-bottom: var(--space-sm);
      padding-bottom: var(--space-xs);
      border-bottom: 1px solid var(--border-light);
    }}
    
    .interface-item {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--space-xs) var(--space-sm);
      background: white;
      border-radius: var(--radius-sm);
      margin-bottom: var(--space-xs);
      border: 1px solid var(--border-light);
    }}
    
    .interface-name {{
      font-family: monospace;
      font-size: 12px;
      color: var(--text-dark);
    }}
    
    .interface-vpc {{
      background: var(--vpc-primary);
      color: white;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 10px;
      font-weight: 600;
    }}
    
    /* VIEW 3: Connection Intelligence Panel */
    #connection-intelligence-panel {{
      composes: side-panel;
      width: 500px;
    }}
    
    .intel-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: var(--space-md);
      padding-bottom: var(--space-sm);
      border-bottom: 2px solid var(--border-light);
    }}
    
    .intel-header h2 {{
      color: var(--text-dark);
      font-size: 18px;
      font-weight: 700;
    }}
    
    .connection-section {{
      margin-bottom: var(--space-lg);
    }}
    
    .section-header {{
      display: flex;
      align-items: center;
      gap: var(--space-xs);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: var(--space-sm);
    }}
    
    .section-header.shared {{
      color: var(--shared-link);
    }}
    
    .section-header.orphan {{
      color: var(--orphan-link);
    }}
    
    .connection-card {{
      background: white;
      border: 1px solid var(--border-light);
      border-radius: var(--radius-md);
      padding: var(--space-md);
      margin-bottom: var(--space-sm);
      transition: all var(--transition-fast);
    }}
    
    .connection-card:hover {{
      border-color: var(--vpc-primary);
      box-shadow: var(--shadow-sm);
    }}
    
    .connection-card.shared {{
      border-left: 4px solid var(--shared-link);
    }}
    
    .connection-card.orphan {{
      border-left: 4px solid var(--orphan-link);
    }}
    
    .connection-title {{
      font-weight: 600;
      color: var(--text-dark);
      margin-bottom: var(--space-xs);
    }}
    
    .connection-meta {{
      font-size: 12px;
      color: var(--text-muted);
    }}
    
    .risk-badge {{
      display: inline-block;
      background: rgba(239, 68, 68, 0.1);
      color: var(--orphan-link);
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 10px;
      font-weight: 600;
      margin-top: var(--space-xs);
    }}
    
    /* Navigation Buttons */
    .panel-nav {{
      display: flex;
      gap: var(--space-xs);
      margin-bottom: var(--space-md);
    }}
    
    .nav-btn {{
      background: transparent;
      border: 1px solid var(--border-light);
      color: var(--text-muted);
      padding: var(--space-xs) var(--space-sm);
      border-radius: var(--radius-sm);
      font-size: 12px;
      cursor: pointer;
      transition: all var(--transition-fast);
    }}
    
    .nav-btn:hover {{
      background: var(--bg-secondary);
      color: var(--text-dark);
    }}
    
    .nav-btn.primary {{
      background: var(--vpc-primary);
      border-color: var(--vpc-primary);
      color: white;
    }}
    
    /* Action Buttons */
    .panel-actions {{
      display: flex;
      gap: var(--space-sm);
      margin-top: auto;
      padding-top: var(--space-md);
      border-top: 1px solid var(--border-light);
    }}
    
    .action-btn {{
      flex: 1;
      background: var(--bg-secondary);
      border: 1px solid var(--border-light);
      color: var(--text-dark);
      padding: var(--space-sm);
      border-radius: var(--radius-sm);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all var(--transition-fast);
      text-align: center;
    }}
    
    .action-btn:hover {{
      background: var(--vpc-primary);
      border-color: var(--vpc-primary);
      color: white;
    }}
    
    .action-btn.secondary {{
      background: transparent;
    }}
    
    /* Legacy Panel Styles (preserved for backward compatibility) */
    .panel-section {{ 
      margin-bottom: var(--space-md); 
      background: var(--bg-secondary); 
      padding: var(--space-md); 
      border-radius: var(--radius-md); 
      border: 1px solid var(--border-light); 
    }}
    
    .panel-title {{ 
      font-size: 11px; 
      text-transform: uppercase; 
      color: var(--text-muted); 
      font-weight: 700; 
      margin-bottom: var(--space-sm); 
      letter-spacing: 0.5px;
    }}
    
    table.data-table {{ 
      width: 100%; 
      border-collapse: collapse; 
      font-size: 12px;
    }}
    
    table.data-table th, table.data-table td {{ 
      padding: var(--space-xs) var(--space-sm); 
      text-align: left; 
      border-bottom: 1px solid var(--border-light); 
    }}
    
    table.data-table th {{ 
      background: var(--bg-secondary); 
      color: var(--text-dark); 
      font-weight: 600; 
      font-size: 11px;
      text-transform: uppercase;
    }}
    
    .status-badge {{ 
      padding: 3px 8px; 
      border-radius: 12px; 
      font-weight: 600; 
      font-size: 10px; 
      color: white; 
      display: inline-block; 
    }}
    
    .status-up {{ background: #27ae60; }}
    .status-down {{ background: #e74c3c; }}
    .status-warn {{ background: #f39c12; }}
    .mac-box {{ 
      background: var(--bg-secondary); 
      padding: 2px 6px; 
      border-radius: 4px; 
      font-family: monospace; 
      display: inline-block; 
      margin: 2px; 
      font-size: 11px;
      color: var(--text-dark);
    }}
    
    /* View State Management */
    .view-hidden {{ display: none !important; }}
    .view-active {{ display: flex !important; }}
    
    /* Responsive */
    @media (max-width: 1200px) {{
      .side-panel {{ width: 400px; }}
      #mynetwork.panel-open {{ flex: 0 0 calc(100% - 420px); }}
    }}
    {vpc_extra_style}
    
    /* Standard L2 Map CSS - injected after legacy styles to ensure precedence */
    {standard_map_css}
    
    @media (max-width: 900px) {{
      .layout-container {{ flex-direction: column; }}
      .side-panel {{ 
        width: 100%; 
        height: 50%;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 100;
        border-radius: var(--radius-lg) var(--radius-lg) 0 0;
      }}
      #mynetwork.panel-open {{ flex: 1; }}
    }}
    @media print {{
      @page {{ size: A4 landscape; margin: 10mm; }}
      body {{ background: white !important; color: #111 !important; }}
      .header, .legend, .topo-toolbar, .layout-container > aside {{ display: none !important; }}
      #mynetwork, .topo-link-inventory {{ page-break-inside: avoid; }}
      .topo-link-inventory {{ display: block !important; max-height: none !important; }}
      #mynetwork.topo-map-hidden {{ display: none !important; }}
      table.topo-inv-table th, table.topo-inv-table td {{ border: 1px solid #333; color: #111; }}
    }}
  </style>
  <script type="text/javascript">
{vis_js_content}
  </script>
</head>
<body class="{body_class}">
  {standard_top_chrome}
  {legacy_header_block}

  <main class="{layout_container_class}"{vpc_layout_hidden}>
      {map_column_inner}
      
            {legacy_aside_html}
    </main>

  <script>
    if (typeof vis === 'undefined') {{
        alert('CRITICAL: Vis.js library failed to load. The topology map cannot be rendered. Please check if vis-network.min.js is present in the modules/web directory.');
    }}
    var nodes_raw = {nodes_str};
    var edges_raw = {edges_str};

    var nodes = new vis.DataSet(nodes_raw);
    var edges = new vis.DataSet(edges_raw);
    {link_shell_js}
    
    var showDescriptions = false;
    function toggleDescriptions() {{
        showDescriptions = !showDescriptions;
        var btn = document.getElementById("descToggleBtn");
        btn.innerText = showDescriptions ? "Hide Descriptions" : "Show Descriptions";
        btn.style.background = showDescriptions ? "rgba(52, 152, 219, 0.4)" : "";
        btn.style.borderColor = showDescriptions ? "#3498db" : "";
        
        var updates = [];
        edges.get().forEach(function(e) {{
            var originalLabel = e.label || "";
            if (e.edge_data && e.edge_data.label) {{
                originalLabel = e.edge_data.label;
            }}
            var newLabel = originalLabel;
            
            if (showDescriptions && e.edge_data) {{
                var fDesc = e.edge_data.f_int_data ? e.edge_data.f_int_data.desc : (e.f_int_data ? e.f_int_data.desc : "");
                var tDesc = e.edge_data.t_int_data ? e.edge_data.t_int_data.desc : (e.t_int_data ? e.t_int_data.desc : "");
                var dLines = [];
                if (fDesc && fDesc !== "-") dLines.push(e.from + ": " + fDesc);
                if (tDesc && tDesc !== "-") dLines.push(e.to + ": " + tDesc);
                
                if (dLines.length > 0) {{
                    newLabel += "\\n[" + dLines.join(" | ") + "]";
                }}
            }}
            
            updates.push({{id: e.id, label: newLabel}});
        }});
        edges.update(updates);
    }}

    var _mapModeVpc = {'true' if map_mode == 'vpc' else 'false'};
    var _nstStandardMap = {nst_standard_map_flag};
    var container = document.getElementById('mynetwork');
    
    // Hide fallback only after Vis network is successfully created
    function nstHideFallback() {{
        var fallbackEl = document.getElementById('network-fallback');
        if (fallbackEl) fallbackEl.style.display = 'none';
    }}
    function nstShowFallback(msg) {{
        var fallbackEl = document.getElementById('network-fallback');
        if (!fallbackEl) return;
        fallbackEl.style.display = 'flex';
        if (msg) {{
            var p = fallbackEl.querySelector('p');
            if (p) p.textContent = msg;
        }}
    }}
    
    // vPC link styling — static by default (stable on older/offline PCs)
    var enableFlowAnimation = false;
    try {{
        if (window.matchMedia && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {{
            enableFlowAnimation = false;
        }}
    }} catch (motionErr) {{ enableFlowAnimation = false; }}

    var flowOffset = 0;
    var flowTimer = null;
    function startFlowAnimation() {{
        if (!enableFlowAnimation) return;
        flowOffset++;
        if (flowOffset > 20) flowOffset = 0;
        var updates = [];
        edges.get().forEach(function(e) {{
            var et = e.type || (e.edge_data && e.edge_data.type);
            if (et === 'vpc' || et === 'vpc_shared' || et === 'vpc-peer-link' || et === 'port-channel' || et === 'vpc-domain-placeholder') {{
                var state = e.link_state || 'active';
                var isPeer = et === 'vpc-peer-link';
                var isAnchor = et === 'vpc-domain-placeholder';
                var color = isAnchor ? '#94a3b8' : (isPeer ? '#a855f7' : (state === 'active' ? '#10b981' : (state === 'partial' ? '#f59e0b' : '#ef4444')));
                var dashPattern = isAnchor ? [5, 5] : ((state === 'active') ? [10, 5] : (state === 'partial' ? [15, 4, 4, 4] : [2, 10]));
                updates.push({{
                    id: e.id, dashes: dashPattern, dashOffset: -flowOffset,
                    width: isAnchor ? 2 : (isPeer ? 5 : (state === 'down' ? 2 : 4)),
                    color: {{ color: color, highlight: color, hover: color }},
                    arrows: {{ to: {{ enabled: !isPeer && !isAnchor && state !== 'down', scaleFactor: 0.5 }} }}
                }});
            }}
        }});
        if (updates.length > 0) edges.update(updates);
        flowTimer = setTimeout(startFlowAnimation, 250);
    }}
    function stopFlowAnimation() {{
        enableFlowAnimation = false;
        if (flowTimer) {{ clearTimeout(flowTimer); flowTimer = null; }}
    }}
    
    var network = null;
    function vpcMapPaneReady(container) {{
      if (!container) return false;
      container.style.width = '100%';
      container.style.flex = '0 0 auto';
      container.style.minHeight = '420px';
      container.style.height = '480px';
      container.style.maxHeight = '680px';
      container.style.overflow = 'hidden';
      return container.offsetHeight >= 32;
    }}

    function vpcPostMapInit() {{
      if (!network || !_mapModeVpc) return;
      try {{
        if (typeof vpcApplyGraphVisibility === 'function') vpcApplyGraphVisibility();
        if (typeof app !== 'undefined' && app.enhanceVPCNodes) app.enhanceVPCNodes();
        if (!window._vpcAutoFitDone) {{
          window._vpcAutoFitDone = true;
          if (typeof vpcFitTopology === 'function') vpcFitTopology(48);
        }}
      }} catch (e) {{ console.warn('[VPC_CC] post init:', e); }}
    }}

    function createTopologyNetwork() {{
      if (network) return network;
      var c = document.getElementById('mynetwork');
      if (!c) return null;
      if (typeof vis === 'undefined' || !vis.Network) {{
        nstShowFallback('Vis.js failed to load. Re-open from Swiss Tools or check offline bundle.');
        return null;
      }}
      if (_nstStandardMap && typeof nstEnsureMapSize === 'function') nstEnsureMapSize();
      if (_mapModeVpc && !vpcMapPaneReady(c)) return null;
      if (_nstStandardMap) {{
        c.style.minHeight = c.style.minHeight || '420px';
        c.style.height = c.style.height || '100%';
        c.style.background = '#0b0f19';
      }}
      var netOpts = {{
      {layout_options}
      interaction: {{
        hover: true, tooltipDelay: 200, zoomView: true, dragView: true,
        navigationButtons: true, keyboard: true, multiselect: true
      }},
      nodes: {{
        font: {{ size: 14, face: 'system-ui', color: '#ffffff', strokeWidth: 2, strokeColor: '#0f172a' }},
        borderWidth: 2,
        margin: 12,
        shadow: {{ enabled: true, color: 'rgba(15,23,42,0.25)', size: 8, x: 2, y: 2 }}
      }},
      edges: {{
        width: 2,
        font: {{
          size: 11, face: 'system-ui', color: '#1e293b', align: 'horizontal',
          background: 'rgba(255,255,255,0.92)', strokeWidth: 3, strokeColor: '#ffffff'
        }},
        smooth: {{ type: 'continuous', roundness: 0.15 }},
        selectionWidth: 4,
        hoverWidth: 1.5
      }},
      groups: {{
        vpc_primary: {{
          shape: 'box',
          color: {{
            background: '#059669',
            border: '#047857',
            highlight: {{ background: '#10b981', border: '#059669' }}
          }},
          font: {{ size: 14, color: '#ffffff', face: 'Inter', weight: 600 }},
          borderWidth: 3,
          shadow: {{ enabled: false }},
          margin: 12,
          shapeProperties: {{ borderRadius: 6 }}
        }},
        vpc_secondary: {{
          shape: 'box',
          color: {{
            background: '#7c3aed',
            border: '#6d28d9',
            highlight: {{ background: '#8b5cf6', border: '#7c3aed' }}
          }},
          font: {{ size: 14, color: '#ffffff', face: 'Inter', weight: 600 }},
          borderWidth: 3,
          shadow: {{ enabled: false, color: 'rgba(124, 58, 237, 0.5)', size: 15, x: 0, y: 0 }},
          margin: 12,
          shapeProperties: {{ borderRadius: 6 }}
        }},
        vpc_domain: {{
          shape: 'box',
          color: {{
            background: 'rgba(99, 102, 241, 0.2)',
            border: '#6366f1',
            highlight: {{ background: 'rgba(129, 140, 248, 0.4)', border: '#818cf8' }}
          }},
          font: {{ size: 20, color: '#f8fafc', face: 'Inter', weight: 800 }},
          borderWidth: 2,
          shadow: {{ enabled: false, color: 'rgba(99, 102, 241, 0.4)', size: 30, x: 0, y: 0 }},
          margin: 24,
          shapeProperties: {{ borderRadius: 12 }}
        }},
        server: {{
          shape: 'dot',
          size: 25,
          color: {{
            background: '#f59e0b',
            border: '#d97706',
            highlight: {{ background: '#fbbf24', border: '#f59e0b' }}
          }},
          font: {{ size: 12, color: '#f1f5f9', face: 'Inter' }},
          borderWidth: 2,
          shadow: {{ enabled: false, color: 'rgba(245, 158, 11, 0.4)', size: 10 }}
        }},
        vpc_peer: {{
          shape: 'box',
          font: {{ size: 16, strokeWidth: 2, strokeColor: '#000' }},
          shadow: {{ enabled: false, color: 'rgba(155, 89, 182, 0.4)', size: 15 }}
        }}
      }}
    }};
      if (_mapModeVpc) {{
        netOpts.layout = {{ improvedLayout: false }};
        netOpts.physics = {{ enabled: false }};
        netOpts.configure = {{ enabled: false }};
      }}
      network = new vis.Network(c, {{nodes: nodes, edges: edges}}, netOpts);
      window.network = network;
      if (_mapModeVpc) vpcPostMapInit();
      if (_nstStandardMap) {{
        nstHideFallback();
        try {{ network.fit({{ animation: false, padding: 48 }}); }} catch (fitE) {{}}
      }}
      return network;
    }}

    function wireNetworkHandlers() {{
      if (!network) return;
      if (window._topoHandlersWired) return;
      window._topoHandlersWired = true;
    // Standard L2 omits legacy side-panel DOM — connection index handles selection.
    if (_nstStandardMap) return;
    var sidePanel = document.getElementById('side-panel');
    var panelContent = document.getElementById('panel-content');
    if (!sidePanel || !panelContent) return;

    // Handle Clicks for Side Panel
    network.on("selectNode", function (params) {{
        if (params.nodes.length > 0) {{
            var nodeId = params.nodes[0];
            var nodeData = nodes.get(nodeId);
            renderNodePanel(nodeData);
        }}
    }});

    network.on("selectEdge", function (params) {{
        if (params.edges.length > 0 && params.nodes.length === 0) {{
            var edgeId = params.edges[0];
            var edgeData = edges.get(edgeId);
            renderEdgePanel(edgeData);
        }}
    }});

    network.on("deselectNode", function () {{ sidePanel.style.display = 'none'; }});
    network.on("deselectEdge", function () {{ sidePanel.style.display = 'none'; }});

    function renderNodePanel(node) {{
        sidePanel.style.display = 'flex';
        var html = '<h3>&#128187; ' + node.id.toUpperCase() + '</h3>';
        
        // Device Info
        if (node.device_info && Object.keys(node.device_info).length > 0) {{
            html += '<div class="panel-section">' +
                '<div class="panel-title">System Information (CDP/LLDP)</div>' +
                '<table class="data-table">' +
                    (node.device_info.platform ? '<tr><th>Platform</th><td>' + node.device_info.platform + '</td></tr>' : '') +
                    (node.device_info.version ? '<tr><th>Version</th><td>' + node.device_info.version + '</td></tr>' : '') +
                    (node.device_info.mgmt_ip ? '<tr><th>Mgmt IP</th><td><a href="ssh://' + node.device_info.mgmt_ip + '">' + node.device_info.mgmt_ip + '</a></td></tr>' : '') +
                '</table>' +
            '</div>';
        }}
        
        // Port Stats
        if (node.port_stats) {{
            html += '<div class="panel-section">' +
                '<div class="panel-title">Port Status Summary</div>' +
                '<span class="status-badge status-up">↑ ' + node.port_stats.up + ' Up</span>' +
                '<span class="status-badge status-down">↓ ' + node.port_stats.down + ' Down</span>' +
                '<span class="status-badge status-warn">&#9888; ' + node.port_stats.err + ' Err</span>' +
                '<span style="font-size:11px; margin-left:10px;">Total: ' + node.port_stats.total + '</span>' +
            '</div>';
        }}

        // vPC info - v6.5.8: Enhanced vPC domain display
        if (node.vpc_count > 0 || node.vpc_domain_id) {{
            html += '<div class="panel-section" style="background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%); border: 2px solid #f97316;">';
            html += '<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">';
            html += '<span style="font-size: 24px;">&#128310;</span>';
            html += '<div>';
            html += '<div style="font-size: 12px; text-transform: uppercase; color: #ea580c; font-weight: 700;">vPC Cluster Connectivity</div>';
            if (node.vpc_domain_id) {{
                html += '<div style="font-size: 16px; font-weight: 700; color: #7c2d12;">Domain ID: ' + node.vpc_domain_id + '</div>';
                html += '<div style="margin-top: 8px; display:flex; flex-direction:column; gap:8px;">';
                html += '<button onclick="app.showVPCDetail(`VPC_Domain_${{node.vpc_domain_id}}`); app.switchView(`vpc_detail`);" style="background:#ea580c; color:white; border:none; padding:8px 12px; border-radius:6px; font-size:11px; font-weight:700; cursor:pointer; box-shadow:0 2px 4px rgba(234,88,12,0.3); transition:all 0.2s; width:100%; text-align:center;">' +
                        '&#128202; VIEW CLUSTER DASHBOARD' +
                        '</button>';
                html += '</div>';
            }} else {{
                html += '<div style="font-size: 16px; font-weight: 700; color: #7c2d12;">' + node.vpc_count + ' Active vPC Domain(s)</div>';
            }}
            html += '</div></div>';
            
            // Show vPC details if available
            if (node.vpc_details && Object.keys(node.vpc_details).length > 0) {{
                html += '<div style="border-top: 1px dashed #fdba74; padding-top: 8px; margin-top: 8px;">';
                html += '<div style="font-size: 11px; color: #9a3412; font-weight: 600; margin-bottom: 6px;">vPC Configuration:</div>';
                for (var vpcPort in node.vpc_details) {{
                    var vpcInfo = node.vpc_details[vpcPort];
                    var vpcType = String(vpcInfo.type || 'member');
                    var vpcId = String(vpcInfo.vpc_id || 'N/A');
                    var status = String(vpcInfo.status || 'unknown');
                    var statusColor = status === 'up' ? '#16a34a' : '#dc2626';
                    var typeIcon = vpcType === 'peer-link' ? '&#128995;' : '&#128992;';
                    
                    html += '<div style="display: flex; justify-content: space-between; align-items: center; padding: 4px 8px; background: white; border-radius: 4px; margin-bottom: 4px; font-size: 12px;">';
                    html += '<div><span style="font-family: monospace; color: #7c2d12; font-weight: 600;">' + vpcPort + '</span> <span style="color: #9a3412;">' + typeIcon + ' ' + vpcType.replace("-", " ").toUpperCase() + '</span></div>';
                    html += '<div style="display: flex; gap: 8px; align-items: center;">';
                    html += '<span style="background: #fff7ed; color: #c2410c; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 600;">vPC ' + vpcId + '</span>';
                    html += '<span style="color: ' + statusColor + '; font-weight: 600; text-transform: uppercase; font-size: 10px;">' + status + '</span>';
                    html += '</div></div>';
                }}
                html += '</div>';
            }}
            html += '</div>';
        }}

        // v6.9.3: Logical Interface Manifest (Port-Channels & LAGs)
        // This resolves the "missing port-channel" data issue by providing a dedicated section
        // for logical aggregation health and physical member status.
        if (node.port_channels && Object.keys(node.port_channels).length > 0) {{
            html += '<div class="panel-section" style="background: #f0f9ff; border: 1px solid #bae6fd;">';
            html += '<div class="panel-title" style="color: #0369a1;">&#128311; Logical Port-Channels</div>';
            
            for (var poId in node.port_channels) {{
                var po = node.port_channels[poId];
                var protocol = String(po.protocol || 'LACP').toUpperCase();
                var members = po.members || [];
                var memberCount = members.length;
                
                html += '<div style="background: white; border: 1px solid #e0f2fe; border-radius: 6px; padding: 8px; margin-bottom: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">';
                html += '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">';
                html += '<span style="font-family: monospace; font-size: 14px; font-weight: 700; color: #0c4a6e;">' + poId + '</span>';
                html += '<span style="background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 12px; font-size: 9px; font-weight: 700;">' + protocol + '</span>';
                html += '</div>';
                
                // Member ports grid
                if (memberCount > 0) {{
                    html += '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px;">';
                    members.forEach(function(m) {{
                        var mName = String(m.intf || m);
                        var mFlag = String(m.flags || '');
                        var isBundled = mFlag.indexOf('P') !== -1 || mFlag.indexOf('bundled') !== -1;
                        var mCol = isBundled ? '#059669' : '#dc2626';
                        
                        html += '<div style="font-size: 10px; padding: 2px 6px; border-radius: 4px; background: #f8fafc; border: 1px solid #f1f5f9; display: flex; justify-content: space-between;">';
                        html += '<span style="font-family: monospace;">' + mName + '</span>';
                        html += '<span style="color: ' + mCol + '; font-weight: 700;">' + (mFlag || '---') + '</span>';
                        html += '</div>';
                    }});
                    html += '</div>';
                }} else {{
                    html += '<div style="font-size: 10px; color: #64748b; font-style: italic;">No members detected</div>';
                }}
                html += '</div>';
            }}
            html += '</div>';
        }}

        // ============================================================================
        // FULLY FUNCTIONAL FEATURE - Device Interface & MAC Display (v6.5.2)
        // 
        // CRITICAL FIX: Side panel now displays complete interface details including:
        // - Interface status, VLAN, speed, description
        // - MAC addresses learned on each interface (up to 50 per interface)
        // - Expandable/collapsible interface list
        // - Works on IOS, NXOS, JUNOS
        //
        // DO NOT MODIFY: This code is fully tested and functional
        // Any changes must go through regression testing
        // ============================================================================
        
        // Interface Details Section
        if (node.interfaces && Object.keys(node.interfaces).length > 0) {{
            var intfs = Object.keys(node.interfaces);
            var maxDisplay = 50; // Cap at 50 interfaces for performance
            
            html += '<div class="panel-section">' +
                '<div class="panel-title">Interfaces (' + intfs.length + ' total)</div>' +
                '<div style="max-height:400px; overflow-y:auto;" id="interface-list">';
            
            // Sort interfaces naturally (Gi0/1 before Gi0/10)
            intfs.sort(function(a, b) {{
                var aNum = a.match(/[0-9]+/);
                var bNum = b.match(/[0-9]+/);
                if (aNum && bNum) {{
                    var aPrefix = a.split(aNum[0])[0];
                    var bPrefix = b.split(bNum[0])[0];
                    if (aPrefix === bPrefix) return parseInt(aNum[0]) - parseInt(bNum[0]);
                }}
                return a.localeCompare(b);
            }});
            
            var displayCount = Math.min(intfs.length, maxDisplay);
            for (var i = 0; i < displayCount; i++) {{
                var intfName = intfs[i];
                var intfData = node.interfaces[intfName] || {{}};
                var status = intfData.status || 'unknown';
                var statusColor = status === 'up' ? '#27ae60' : (status === 'err-disabled' ? '#e67e22' : (status === 'down' ? '#c0392b' : '#7f8c8d'));
                var vlan  = (intfData.vlan  && intfData.vlan  !== '') ? intfData.vlan  : '-';
                var speed = (intfData.speed && intfData.speed !== '') ? intfData.speed : '-';
                var desc  = intfData.desc || '';
                var macs  = intfData.macs || [];
                
                html += '<div style="border:1px solid #e1e4e8; border-radius:6px; margin:4px 0; padding:8px; background:#f8f9fa;">' +
                    '<div style="font-weight:600; color:#2c3e50; margin-bottom:4px; display:flex; justify-content:space-between; align-items:center;">' +
                        '<span>' + intfName + '</span>' +
                        '<span style="color:' + statusColor + '; font-weight:bold; text-transform:uppercase; font-size:10px; background:' + statusColor + '22; padding:2px 6px; border-radius:8px;">' + status + '</span>' +
                    '</div>';
                
                if (desc && desc !== '-') {{
                    html += '<div style="margin-bottom:6px; padding:6px 8px; border-left:3px solid #667eea; background:#eef2ff; color:#334155; font-size:12px;"><strong>Desc:</strong> <em>' + desc + '</em></div>';
                }}
                
                // Speed and VLAN row — always show, even if '-'
                html += '<div style="display:flex; gap:12px; font-size:11px; margin-bottom:4px;">' +
                    '<span><span style="color:#888;">VLAN:</span> <b style="color:#8e44ad;">' + vlan + '</b></span>' +
                    '<span><span style="color:#888;">Speed:</span> <b style="color:#2980b9;">' + speed + '</b></span>' +
                '</div>';
                
                // MAC Addresses
                if (macs && macs.length > 0) {{
                    var maxMacs = 10;
                    var macDisplay = macs.slice(0, maxMacs).map(function(m) {{
                        return '<span style="display:inline-block; background:#e1e4e8; color:#24292e; padding:1px 5px; border-radius:3px; font-size:10px; font-family:monospace; margin:1px;">' + m + '</span>';
                    }}).join('');
                    if (macs.length > maxMacs) {{
                        macDisplay += '<span style="font-size:9px; color:#586069; margin-left:4px;">+' + (macs.length - maxMacs) + ' more</span>';
                    }}
                    html += '<div style="margin-top:4px; padding-top:4px; border-top:1px dashed #d1d5da;">' +
                        '<span style="font-size:10px; color:#586069;">MACs (' + macs.length + '):</span>' +
                        '<div style="margin-top:2px;">' + macDisplay + '</div>' +
                    '</div>';
                }}
                
                html += '</div>';
            }}
            
            if (intfs.length > maxDisplay) {{
                html += '<div style="text-align:center; padding:8px; color:#586069; font-size:11px; font-style:italic;">' +
                    '+' + (intfs.length - maxDisplay) + ' more interfaces not shown' +
                '</div>';
            }}
            
            html += '</div></div>';
        }} else if (!node.is_scanned) {{
            // Node was discovered via CDP/LLDP but not directly scanned
            html += '<div class="panel-section" style="background:#fff8e1; border-color:#f39c12;">' +
                '<div class="panel-title" style="color:#e67e22;">Interface Data Unavailable</div>' +
                '<p style="font-size:11px; color:#7f8c8d; margin:0;">' +
                    'This device was discovered via CDP/LLDP from a neighbor but was not ' +
                    'directly scanned. Run the topology map with this device in your inventory ' +
                    'to see its interface details.' +
                '</p>' +
            '</div>';
        }}

        panelContent.innerHTML = html;
    }}

    function renderEdgePanel(edge) {{
        sidePanel.style.display = 'flex';
        var data = edge.edge_data;
        if (!data) {{
            panelContent.innerHTML = '<h3>Link Detail</h3><p>No extended data available.</p>';
            return;
        }}

        // v6.5.8: Enhanced edge panel with vPC-specific information
        var confColor = data.confidence === 'High' ? '#27ae60' : (data.confidence === 'Mismatch' ? '#c0392b' : '#f39c12');
        
        // vPC-specific styling
        var linkType = String(data.type || 'standard');
        var domainId = String(data.vpc_domain_id || '');
        var isVpc = data.is_vpc_member || data.is_vpc_peer_link || linkType === 'vpc' || linkType === 'vpc-peer-link';
        var linkTypeColor = linkType === 'vpc-peer-link' ? '#9b59b6' :
                           linkType === 'vpc' ? '#e67e22' :
                           linkType === 'vpc-domain-peer' ? '#8e44ad' :
                           linkType === 'port-channel' ? '#27ae60' : '#607d8b';
        
        var html = '<h3>&#128279; ' + data.from + ' ↔ ' + data.to + '</h3>';
        
        // vPC Header with prominent styling
        if (isVpc) {{
            html += '<div style="background: linear-gradient(135deg, ' + linkTypeColor + '22 0%, ' + linkTypeColor + '44 100%); border-left: 4px solid ' + linkTypeColor + '; padding: 12px; border-radius: 8px; margin-bottom: 12px;">';
            html += '<div style="font-size: 12px; text-transform: uppercase; color: ' + linkTypeColor + '; font-weight: 600; margin-bottom: 4px;">';
            if (data.is_vpc_peer_link) html += '&#128995; vPC PEER LINK (Keepalive + CFS)';
            else if (data.is_vpc_member) html += '&#128992; vPC MEMBER PORT';
            else if (linkType === 'port-channel') html += '&#128994; Port-Channel';
            else if (linkType === 'vpc-domain-peer') html += '&#128997; vPC DOMAIN PEER RELATION';
            else html += '&#128279; ' + linkType.toUpperCase();
            html += '</div>';
            if (domainId) {{
                html += '<div style="font-size: 12px; margin-top: 6px;"><span style="background:' + linkTypeColor + '; color:#fff; padding:2px 8px; border-radius:10px;">Domain ID ' + domainId + '</span></div>';
            }}
            if (data.label) {{
                html += '<div style="font-size: 18px; font-weight: 700; color: #2d3748;">' + data.label + '</div>';
            }}
            html += '</div>';
        }}
        
        html += '<div style="margin-bottom:10px;">' +
            '<span class="status-badge" style="background:' + confColor + '">Confidence: ' + data.confidence + '</span> ' +
            '<span class="status-badge" style="background:' + linkTypeColor + '">Type: ' + linkType.toUpperCase() + '</span>' +
        '</div>';

        // Link Description Section (v6.5.8: prominent display)
        if ((data.f_int_data && data.f_int_data.desc) || (data.t_int_data && data.t_int_data.desc)) {{
            html += '<div class="panel-section" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">';
            html += '<div style="font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.9; margin-bottom: 6px;">&#128203; Link Descriptions</div>';
            if (data.f_int_data && data.f_int_data.desc) {{
                html += '<div style="font-size: 13px; margin-bottom: 4px;"><strong>' + data.from + ':</strong> <em>' + data.f_int_data.desc + '</em></div>';
            }}
            if (data.t_int_data && data.t_int_data.desc) {{
                html += '<div style="font-size: 13px;"><strong>' + data.to + ':</strong> <em>' + data.t_int_data.desc + '</em></div>';
            }}
            html += '</div>';
        }}

        // v6.9.0: Enhanced Port-Channel / vPC Details with Validation
        if (data.bundled_links && data.bundled_links.length > 0) {{
            if (linkType === 'vpc_shared' || linkType === 'vpc_orphan') {{
                html += '<div class="panel-section" style="background:#f0fdf4; border: 1px solid #bbf7d0;">' +
                    '<div class="panel-title" style="color:#16a34a; font-weight:700;">' +
                        '<span>&#128311; Physical-to-Logical Link Synchronization Map</span>' +
                    '</div>' +
                    '<div style="font-size:11px; margin-bottom:8px; color:#475569;">' +
                        'Verifying port correlation across the vPC peer pair connecting downstream to <b>' + data.to + '</b>.' +
                    '</div>' +
                    '<table class="data-table" style="font-size:11px;">' +
                    '<tr style="background:#dcfce7; color:#14532d;">' +
                        '<th>Active Switch</th>' +
                        '<th>Switch Port</th>' +
                        '<th>Downstream Port</th>' +
                        '<th>Port Status</th>' +
                        '<th>Speed / Duplex</th>' +
                    '</tr>';
                    
                data.bundled_links.forEach(function(l) {{
                    var st = l.f_int_data ? l.f_int_data.status : 'unknown';
                    var stCol = st === 'up' ? '#16a34a' : '#dc2626';
                    var spd = l.f_int_data ? (l.f_int_data.speed || '-') : '-';
                    var dpl = l.f_int_data ? (l.f_int_data.duplex || '-') : '-';
                    var switchName = l.from || 'Switch';
                    
                    html += '<tr style="border-bottom: 1px solid #e2e8f0;">' +
                        '<td style="font-weight:600; color:#1e293b;">' + switchName + '</td>' +
                        '<td style="font-family:monospace; font-weight:700; color:#0369a1;">' + l.f_port + '</td>' +
                        '<td style="font-family:monospace; font-weight:700; color:#4f46e5;">' + (l.t_port || '-') + '</td>' +
                        '<td style="color:' + stCol + '; font-weight:700; text-transform:uppercase;">' + st + '</td>' +
                        '<td style="color:#475569;">' + spd + ' / ' + dpl + '</td>' +
                    '</tr>';
                }});
                html += '</table></div>';
            }} else {{
                var pcTitle = data.is_vpc_member ? 'vPC Member Ports' : 'Port-Channel Members';
                html += '<div class="panel-section">' +
                    '<div class="panel-title" style="display:flex; justify-content:space-between;">' +
                        '<span>' + pcTitle + ' (' + data.bundled_links.length + ' physical links)</span>' +
                        (data.cdp_validated ? '<span style="color:#10b981; font-size:10px;">&#10004; CDP Validated</span>' : '') +
                    '</div>' +
                    '<table class="data-table" style="font-size:10px;">' +
                    '<tr><th>Local</th><th>Partner SysID</th><th>P. Port</th><th>State</th><th>Status</th></tr>';
                data.bundled_links.forEach(function(l) {{
                    var st = l.f_int_data ? l.f_int_data.status : 'unknown';
                    var stCol = st === 'up' ? '#27ae60' : (st === 'down' ? '#c0392b' : '#f39c12');
                    var partner_id = '-', partner_port = '-', lacp_state = '-';
                    
                    // Extract LACP data if available on the link or passed down
                    if (l.lacp_partner) {{
                        partner_id = l.lacp_partner.partner_id || '-';
                        partner_port = l.lacp_partner.partner_port || '-';
                        lacp_state = l.lacp_partner.partner_state || '-';
                    }}
                    
                    html += '<tr>' +
                        '<td style="font-family: monospace;">' + l.f_port + '</td>' +
                        '<td style="font-family: monospace; color:#475569;">' + partner_id + '</td>' +
                        '<td style="font-family: monospace; color:#475569;">' + partner_port + '</td>' +
                        '<td style="font-family: monospace;">' + lacp_state + '</td>' +
                        '<td style="color:' + stCol + '; font-weight:bold; text-transform: uppercase;">' + st + '</td>' +
                    '</tr>';
                }});
                html += '</table></div>';
            }}
        }}

        // Render Interface Details
        var f_int = data.f_int_data || {{}};
        html += renderInterfaceDetail(data.from, data.f_port, f_int);
        
        var t_int = data.t_int_data || {{}};
        html += renderInterfaceDetail(data.to, data.t_port, t_int);

        panelContent.innerHTML = html;
    }}

    function renderInterfaceDetail(host, port, intData) {{
        var status = intData.status || 'unknown';
        var statusColor = status === 'up' ? '#27ae60' : (status === 'err-disabled' ? '#e67e22' : (status === 'down' ? '#c0392b' : '#7f8c8d'));
        var desc = intData.desc || '';
        
        var html = '<div class="panel-section" style="border-left: 4px solid ' + statusColor + ';">' +
            '<div class="panel-title" style="display:flex; justify-content:space-between; align-items:center;">' +
                '<span>Interface: ' + host + ' / ' + port + '</span>' +
                '<span style="color:' + statusColor + '; font-weight:bold; text-transform:uppercase; font-size:11px; background:' + statusColor + '22; padding:2px 8px; border-radius:8px;">' + status + '</span>' +
            '</div>';
        
        // v6.5.8: Prominent description display (if available)
        if (desc && desc !== '-') {{
            html += '<div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; padding:12px; border-radius:8px; margin:8px 0; box-shadow:0 2px 8px rgba(102,126,234,0.3);">' +
                '<div style="font-size:10px; text-transform:uppercase; letter-spacing:0.5px; opacity:0.9; margin-bottom:4px;">&#128203; Interface Description</div>' +
                '<div style="font-size:14px; font-weight:600; font-style:italic;">' + desc + '</div>' +
            '</div>';
        }}
        
        html += '<table class="data-table">' +
                '<tr><th>Status</th><td style="color:' + statusColor + '; font-weight:bold; text-transform:uppercase;">' + status + '</td></tr>' +
                '<tr><th>Description</th><td style="font-style:italic; color:#4a5568;">' + (desc || '-') + '</td></tr>' +
                '<tr><th>VLAN</th><td><span style="background:#e9d5ff; color:#6b21a8; padding:2px 8px; border-radius:12px; font-weight:600;">' + (intData.vlan || '-') + '</span></td></tr>' +
                '<tr><th>Speed</th><td><span style="background:#dbeafe; color:#1e40af; padding:2px 8px; border-radius:12px; font-weight:600;">' + (intData.speed || '-') + '</span></td></tr>' +
            '</table>';
            
        // MAC Addresses
        if (intData.macs && intData.macs.length > 0) {{
            var maxMacs = 50;
            var macHtml = intData.macs.slice(0, maxMacs).map(function(m) {{ return '<span class="mac-box">' + m + '</span>'; }}).join('');
            if (intData.macs.length > maxMacs) {{
                macHtml += '<span style="font-size:10px; color:#7f8c8d;"> +' + (intData.macs.length - maxMacs) + ' more MACs...</span>';
            }}
            html += '<div style="margin-top:8px;"><b>Endpoint MACs learned:</b><br>' + macHtml + '</div>';
        }}
        html += '</div>';
        return html;
    }}

    // Search logic
    var originalColors = {{}};
    nodes_raw.forEach(function(n) {{ originalColors[n.id] = n.color; }});

    function normalizeMacHex(s) {{
      return (s || '').replace(/[.:\\-\\s_]/g, '').toLowerCase();
    }}
    function macQueryMatches(haystack, query) {{
      var q = normalizeMacHex(query);
      if (!q) return false;
      return normalizeMacHex(haystack).indexOf(q) !== -1;
    }}

    function searchNodes(query) {{
        if (typeof topoShellSearch === 'function') {{
            topoShellSearch(query);
            if (!query || !query.trim()) {{
                var updates = [];
                nodes_raw.forEach(function(n) {{
                    updates.push({{ id: n.id, color: originalColors[n.id], borderWidth: 2 }});
                }});
                nodes.update(updates);
            }}
            return;
        }}
        if (!query || query.trim() === '') {{
            clearSearch();
            return;
        }}
        var q = query.toLowerCase().trim();
        var updates = [];
        nodes_raw.forEach(function(n) {{
            var match = n.id.toLowerCase().indexOf(q) !== -1 ||
                        (n.ip && String(n.ip).toLowerCase().indexOf(q) !== -1) ||
                        (n.role && n.role.toLowerCase().indexOf(q) !== -1) ||
                        (n.label && n.label.toLowerCase().indexOf(q) !== -1) ||
                        (n.vpc_domain_id && String(n.vpc_domain_id).toLowerCase().indexOf(q) !== -1);
            
            // Search inside MAC addresses if interface data exists (colon/dash/dot agnostic)
            if (!match && n.interfaces) {{
                for (var intf in n.interfaces) {{
                    var idata = n.interfaces[intf];
                    if (idata.macs && idata.macs.some(function(m) {{ return macQueryMatches(m, q); }})) {{
                        match = true; break;
                    }}
                    if (idata.desc && idata.desc.toLowerCase().indexOf(q) !== -1) {{
                        match = true; break;
                    }}
                }}
            }}
            if (!match && n.macs_search && macQueryMatches(n.macs_search, q)) {{
                match = true;
            }}
            if (!match && n.macs && n.macs.some(function(m) {{ return macQueryMatches(m, q); }})) {{
                match = true;
            }}

            if (match) {{
                updates.push({{ id: n.id, color: {{ background: '#fff176', border: '#f39c12' }}, borderWidth: 4 }});
            }} else {{
                updates.push({{ id: n.id, color: {{ background: originalColors[n.id].background + '55', border: originalColors[n.id].border }}, borderWidth: 1 }});
            }}
        }});
        nodes.update(updates);
    }}

    function clearSearch() {{
        document.getElementById('searchInput').value = '';
        var updates = nodes_raw.map(function(n) {{ return {{ id: n.id, color: originalColors[n.id], borderWidth: 2 }}; }});
        nodes.update(updates);
    }}

    // ============================================
    // VPC VISUALIZATION SYSTEM v7.0
    // 3-View Architecture: Global → VPC Detail → Intelligence
    // ============================================
    
    var app = {{
        // View State Management
        currentView: 'global',  // 'global' | 'vpc_detail' | 'intelligence'
        viewHistory: [],
        selectedVPCDomain: null,
        vpcData: {{}},  // Extracted VPC domain structures
        
        // Initialize application
        init: function() {{
            // v6.7.2: Data validation and diagnostics
            console.log('[VPC v7.0] ============================================');
            console.log('[VPC v7.0] Raw nodes count:', nodes_raw ? nodes_raw.length : 'undefined');
            console.log('[VPC v7.0] Raw edges count:', edges_raw ? edges_raw.length : 'undefined');
            
            // Validate data before processing
            if (!nodes_raw || !Array.isArray(nodes_raw) || nodes_raw.length === 0) {{
                console.error('[VPC v7.0] ERROR: No nodes data available!');
                var mapEl = document.getElementById('mynetwork');
                var emptyEl = document.getElementById('vpc-map-empty');
                if (window.__VPC_COMMAND_CENTER__ && emptyEl) {{
                    emptyEl.style.display = 'block';
                    if (mapEl) mapEl.style.display = 'none';
                }} else if (mapEl) {{
                    mapEl.innerHTML =
                    '<div style="padding:40px;text-align:center;">' +
                    '<h3 style="color:#ef4444;">&#9888; No Topology Data</h3>' +
                    '<p style="color:#94a3b8;">The map was generated but contains no device data.</p>' +
                    '</div>';
                }}
                return;
            }}
            
            // Log VPC nodes found
            var vpcNodes = nodes_raw.filter(function(n) {{ return n.id && n.id.indexOf('VPC_Domain_') === 0; }});
            console.log('[VPC v7.0] VPC domain nodes found:', vpcNodes.length);
            vpcNodes.forEach(function(n) {{
                console.log('[VPC v7.0]   -', n.id, 'members:', n.vpc_members || 'NOT SET');
            }});
            
            this.extractVPCData();
            this.enhanceVPCNodes();
            console.log('[VPC v7.0] Initialized with', Object.keys(this.vpcData).length, 'VPC domains');
            console.log('[VPC v7.0] ============================================');
        }},
        
        // Extract VPC domain structures from raw data
        extractVPCData: function() {{
            var self = this;
            
            // Find all VPC domain nodes
            nodes_raw.forEach(function(node) {{
                if (node.id && node.id.indexOf('VPC_Domain_') === 0) {{
                    var domainId = node.id.replace('VPC_Domain_', '');
                    
                    // v6.7.2: Try multiple sources for member data
                    var members = node.vpc_members || [];
                    
                    // Fallback: extract from vpc_details keys if vpc_members not set
                    if (members.length === 0 && node.vpc_details) {{
                        var detailKeys = Object.keys(node.vpc_details);
                        var extractedMembers = {{}};
                        detailKeys.forEach(function(key) {{
                            var parts = key.split(':');
                            if (parts.length > 0) {{
                                var deviceName = parts[0].trim();
                                if (deviceName) extractedMembers[deviceName] = true;
                            }}
                        }});
                        members = Object.keys(extractedMembers);
                        console.log('[VPC v7.0] Extracted members:', members);
                    }}
                    
                    // Second fallback: check interfaces for device names
                    if (members.length === 0 && node.interfaces) {{
                        var interfaceKeys = Object.keys(node.interfaces);
                        var extractedMembers = {{}};
                        interfaceKeys.forEach(function(key) {{
                            var parts = key.split(':');
                            if (parts.length > 0) {{
                                var deviceName = parts[0].trim();
                                if (deviceName) extractedMembers[deviceName] = true;
                            }}
                        }});
                        members = Object.keys(extractedMembers);
                        if (members.length > 0) {{
                            console.log('[VPC v7.0] Fallback from interfaces:', members);
                        }}
                    }}
                    
                    self.vpcData[domainId] = {{
                        id: domainId,
                        nodeId: node.id,
                        members: members,
                        peerLink: null,
                        sharedConnections: [],
                        orphanConnections: [],
                        interfaces: {{}},
                        allEdges: []
                    }};
                    
                    // Extract interfaces from node metadata
                    if (node.interfaces) {{
                        self.vpcData[domainId].interfaces = node.interfaces;
                    }}
                }}
            }});
            
            function edgeTypeOf(edge) {{
                return edge.type || (edge.edge_data && edge.edge_data.type) || '';
            }}

            // Categorize edges by VPC domain
            edges_raw.forEach(function(edge) {{
                var et = edgeTypeOf(edge);
                if (!et) return;
                
                var domainId = self.findDomainForEdge(edge);
                if (!domainId) return;
                
                var domain = self.vpcData[domainId];
                if (!domain) return;
                
                domain.allEdges.push(edge);
                
                if (et === 'vpc-peer-link') {{
                    domain.peerLink = edge;
                }} else if (et === 'vpc_shared') {{
                    domain.sharedConnections.push(edge);
                }} else if (et === 'vpc_orphan') {{
                    domain.orphanConnections.push(edge);
                }}
            }});
        }},
        
        // Find which VPC domain an edge belongs to
        findDomainForEdge: function(edge) {{
            for (var domainId in this.vpcData) {{
                var domain = this.vpcData[domainId];
                var members = domain.members;
                
                // Check if edge connects to any member of this domain
                if (members.indexOf(edge.from) !== -1 || members.indexOf(edge.to) !== -1) {{
                    return domainId;
                }}
                // Check VPC domain node itself
                if (edge.from === domain.nodeId || edge.to === domain.nodeId) {{
                    return domainId;
                }}
            }}
            return null;
        }},
        
        // Enhance VPC domain nodes with visual styling
        enhanceVPCNodes: function() {{
            var updates = [];
            
            nodes_raw.forEach(function(node) {{
                if (node.id && node.id.indexOf('VPC_Domain_') === 0) {{
                    updates.push({{
                        id: node.id,
                        group: 'vpc_domain',
                        size: 60,
                        font: {{ size: 16, color: '#ffffff', face: 'Inter' }},
                        color: {{
                            background: '#6366f1',
                            border: '#4338ca',
                            highlight: {{ background: '#818cf8', border: '#6366f1' }}
                        }},
                        borderWidth: 3,
                        shadow: {{
                            enabled: true,
                            color: 'rgba(99, 102, 241, 0.5)',
                            size: 20,
                            x: 0,
                            y: 0
                        }},
                        shape: 'box',
                        margin: 16,
                        // Make VPC domains more prominent in physics
                        mass: 5
                    }});
                }}
            }});
            
            if (updates.length > 0) {{
                nodes.update(updates);
            }}
        }},
        
        // View Navigation
        goBack: function() {{
            if (this.viewHistory.length > 0) {{
                var previousView = this.viewHistory.pop();
                this.switchView(previousView, false);
            }} else {{
                this.switchView('global');
            }}
        }},
        
        switchView: function(viewName, addToHistory) {{
            if (addToHistory !== false && this.currentView !== viewName) {{
                this.viewHistory.push(this.currentView);
            }}
            
            // Hide all panels (null-safe: Standard L2 omits legacy panels)
            var _sp = document.getElementById('side-panel');
            var _vp = document.getElementById('vpc-detail-panel');
            var _ip = document.getElementById('connection-intelligence-panel');
            var _mn = document.getElementById('mynetwork');
            if (_sp) _sp.style.display = 'none';
            if (_vp) _vp.style.display = 'none';
            if (_ip) _ip.style.display = 'none';
            if (_mn) _mn.classList.remove('panel-open');
            
            this.currentView = viewName;
            
            switch(viewName) {{
                case 'global':
                    // Default state - no panels open
                    network.unselectAll();
                    break;
                    
                case 'vpc_detail':
                    document.getElementById('vpc-detail-panel').style.display = 'flex';
                    document.getElementById('mynetwork').classList.add('panel-open');
                    break;
                    
                case 'intelligence':
                    document.getElementById('connection-intelligence-panel').style.display = 'flex';
                    document.getElementById('mynetwork').classList.add('panel-open');
                    break;
            }}
            
            setTimeout(function() {{
                network.setSize('100%', '100%');
                network.fit({{ animation: false }});
            }}, 100);
        }},
        
        // Show VPC Detail View
        showVPCDetail: function(nodeId) {{
            var domainId = nodeId.replace('VPC_Domain_', '');
            var domain = this.vpcData[domainId];
            
            if (!domain) {{
                console.error('VPC domain not found:', domainId);
                return;
            }}
            
            this.selectedVPCDomain = domain;
            
            // vPC Health & Correlation Integration
            var nodeData = nodes.get(nodeId);
            var correlation = nodeData.correlation || {{}};
            var healthScore = correlation.health_score !== undefined ? correlation.health_score : 100;
            var healthBadge = document.getElementById('vpc-health-badge');
            
            healthBadge.textContent = healthScore + '%';
            healthBadge.className = 'health-badge ' + (correlation.health_label || 'healthy').toLowerCase();
            
            var correlationHtml = '';
            if (correlation.consistency_alerts && correlation.consistency_alerts.length > 0) {{
                correlation.consistency_alerts.forEach(function(msg) {{
                    correlationHtml += '<div class="alert-card"><span>&#9888;</span> ' + msg + '</div>';
                }});
            }}
            if (correlation.peer_mismatches && correlation.peer_mismatches.length > 0) {{
                correlation.peer_mismatches.forEach(function(msg) {{
                    correlationHtml += '<div class="alert-card"><span>&#10060;</span> ' + msg + '</div>';
                }});
            }}
            if (correlation.orphan_links && correlation.orphan_links.length > 0) {{
                correlation.orphan_links.forEach(function(msg) {{
                    correlationHtml += '<div class="alert-card warn"><span>&#9888;</span> Orphan Port: ' + msg + '</div>';
                }});
            }}
            if (!correlationHtml) {{
                correlationHtml = '<div style="color:#27ae60; font-size:12px; font-weight:600;">&#9989; Synchronization valid between peers.</div>';
            }}
            document.getElementById('vpc-correlation-content').innerHTML = correlationHtml;
            
            // v6.9.3: Structured VPC operational summary (Adaptive Key Mapping)
            var consistencyHtml = '<table class="dashboard-table" style="font-size:11px;">';
            consistencyHtml += '<tr><th>vPC</th><th>Po</th><th>Status</th><th>Consistency</th><th>Active VLANs</th></tr>';
            var hasData = false;
            
            if (nodeData.vpc_structured && nodeData.vpc_structured.length > 0) {{
                nodeData.vpc_structured.forEach(function(vs) {{
                    var peerName = vs.member;
                    var table = vs.vpc_structured.vpc_table || [];
                    if (table.length > 0) hasData = true;
                    
                    table.forEach(function(row) {{
                        // v6.9.3: Adaptive key lookup for heterogeneous NX-OS telemetry
                        var vpcId = row.vpc_id || row['vpc-id'] || 'N/A';
                        var po = row.po || row.port_channel || row['port-channel'] || '-';
                        var status = (row.status || row.state || 'unknown').toLowerCase();
                        var consistency = (row.consistency || row['consistency-status'] || 'unknown').toLowerCase();
                        var active_vlans = row.active_vlans || row['vlan-id'] || '-';
                        
                        var stCol = status === 'up' || status === 'success' ? '#16a34a' : '#dc2626';
                        var consCol = consistency === 'success' || consistency === 'consistent' ? '#16a34a' : '#ea580c';
                        
                        consistencyHtml += '<tr>' +
                            '<td>' + vpcId + ' <span style="color:#94a3b8;font-size:9px;">(' + peerName + ')</span></td>' +
                            '<td>' + po + '</td>' +
                            '<td style="color:' + stCol + '; font-weight:600;">' + status.toUpperCase() + '</td>' +
                            '<td style="color:' + consCol + ';">' + consistency + '</td>' +
                            '<td style="font-family:monospace; color:#6366f1;">' + active_vlans + '</td>' +
                        '</tr>';
                    }});
                }});
            }}
            
            consistencyHtml += '</table>';
            
            document.getElementById('vpc-consistency-summary').innerHTML = consistencyHtml;
            if (!hasData) {{
                document.getElementById('vpc-consistency-summary').innerHTML = '<div style="color:var(--text-muted); font-size:11px; padding:10px;">No structured vPC table data collected for this domain.</div>';
            }}

            var globalRaw = '';
            if (nodeData.vpc_details && nodeData.vpc_details['_consistency_global']) {{
                var gmeta = nodeData.vpc_details['_consistency_global'];
                globalRaw = (typeof gmeta === 'object') ? (gmeta.raw || gmeta.text || JSON.stringify(gmeta)) : String(gmeta);
            }}
            (nodeData.vpc_structured || []).forEach(function(vs) {{
                var peer = vs.member;
                var vd = (nodes_raw.find(function(n) {{ return n.id === peer; }}) || {{}}).vpc_details || {{}};
                if (vd['_consistency_global']) {{
                    var gm = vd['_consistency_global'];
                    globalRaw += '\\n=== ' + peer + ' ===\\n' + ((gm.raw || gm.text) || JSON.stringify(gm));
                }}
            }});
            document.getElementById('vpc-global-consistency-panel').textContent =
                globalRaw.trim() || 'No show vpc consistency-parameters global output collected.';

            // Update header
            document.getElementById('vpc-detail-title').textContent = 'VPC Domain ' + domainId;
            document.getElementById('vpc-detail-id').textContent = 'Domain ID: ' + domainId;
            
            function telemetryHealthy(val) {{
                var s = String(val || '').toLowerCase().trim();
                if (!s || s === 'unknown') return null;
                if (/down|dead|fail|unreach|lost|inactive/.test(s)) return false;
                if (/alive|peer is up|\\bup\\b|ok|success|active/.test(s)) return true;
                return null;
            }}
            function statusClass(val) {{
                var h = telemetryHealthy(val);
                if (h === true) return 'status-ok';
                if (h === false) return 'status-bad';
                return 'status-warn';
            }}
            function formatTelemetry(val) {{
                if (!val || val === 'unknown') return 'Unknown';
                return String(val);
            }}

            // Update peer link visualization + keepalive / peer-link telemetry
            var members = domain.members;
            document.getElementById('peer-member-1').textContent = members[0] || '--';
            document.getElementById('peer-member-2').textContent = members[1] || '--';
            var peerPo = '';
            if (nodeData.vpc_structured && nodeData.vpc_structured.length) {{
                nodeData.vpc_structured.forEach(function(vs) {{
                    var plpo = (vs.vpc_structured || {{}}).peer_link_po;
                    if (plpo) peerPo = plpo;
                }});
            }}
            if (domain.peerLink) {{
                var plLabel = peerPo || domain.peerLink.f_port || domain.peerLink.label || '--';
                document.getElementById('peer-link-port').innerHTML =
                    'Port: <span class="' + statusClass('up') + '">' + plLabel + '</span>';
            }} else if (peerPo) {{
                document.getElementById('peer-link-port').innerHTML =
                    'Port: <span class="status-ok">' + peerPo + '</span> (from show vpc)';
            }} else {{
                document.getElementById('peer-link-port').textContent = 'Port: Peer link not detected';
            }}

            var kaHtml = '', plHtml = '';
            if (nodeData.vpc_structured && nodeData.vpc_structured.length) {{
                var kaParts = [], plParts = [];
                nodeData.vpc_structured.forEach(function(vs) {{
                    var peer = vs.member || '?';
                    var st = vs.vpc_structured || {{}};
                    var ka = st.keepalive_status || 'unknown';
                    var pl = st.peer_status || 'unknown';
                    kaParts.push('<span class="' + statusClass(ka) + '">' + peer + ': ' + formatTelemetry(ka) + '</span>');
                    plParts.push('<span class="' + statusClass(pl) + '">' + peer + ': ' + formatTelemetry(pl) + '</span>');
                }});
                kaHtml = kaParts.join(' &nbsp;|&nbsp; ');
                plHtml = plParts.join(' &nbsp;|&nbsp; ');
            }} else {{
                kaHtml = '<span class="status-warn">No keepalive telemetry collected</span>';
                plHtml = '<span class="status-warn">No peer-link telemetry collected</span>';
            }}
            document.getElementById('peer-keepalive-status').innerHTML = 'Keepalive: ' + kaHtml;
            document.getElementById('peer-link-status').innerHTML = 'Peer-Link: ' + plHtml;
            
            // Update member cards (Role & Keepalive per peer)
            var membersHtml = '';
            domain.members.forEach(function(member, index) {{
                var role = 'Secondary', ka = 'Unknown', plSt = 'Unknown';
                if (nodeData.vpc_structured) {{
                    nodeData.vpc_structured.forEach(function(vs) {{
                        if (vs.member === member) {{
                            role = vs.vpc_structured.role || role;
                            ka = vs.vpc_structured.keepalive_status || ka;
                            plSt = vs.vpc_structured.peer_status || plSt;
                        }}
                    }});
                }}
                var isPrimary = role.toLowerCase() === 'primary';
                var kaHealthy = telemetryHealthy(ka);
                var kaCol = kaHealthy === true ? '#22c55e' : (kaHealthy === false ? '#ef4444' : '#f59e0b');
                var kaLabel = formatTelemetry(ka);
                
                membersHtml += 
                    '<div class="vpc-member-card ' + (isPrimary ? 'primary' : '') + '">' +
                        '<div class="member-icon">&#128187;</div>' +
                        '<div class="member-name">' + member + '</div>' +
                        '<div class="member-role" style="display:flex; justify-content:space-between;">' +
                            '<span>' + (isPrimary ? 'Primary' : 'Secondary') + '</span>' +
                            '<span style="color:' + kaCol + '; font-size:9px;" title="Peer-Link: ' + plSt + '">KA: ' + kaLabel + '</span>' +
                        '</div>' +
                    '</div>';
            }});
            document.getElementById('vpc-members-grid').innerHTML = membersHtml;
            
            // Update interfaces list
            this.renderVPCInterfaces(domain);
            
            // Switch to detail view
            this.switchView('vpc_detail');
        }},
        
        // Render VPC interfaces grouped by member — v7.1 Physical + structured fallback
        renderVPCInterfaces: function(domain) {{
            var html = '';
            var memberPortMap = {{}};
            domain.members.forEach(function(m) {{ memberPortMap[m] = []; }});

            function edgeBundled(edge) {{
                if (edge.bundled_links && edge.bundled_links.length) return edge.bundled_links;
                if (edge.edge_data && edge.edge_data.bundled_links) return edge.edge_data.bundled_links;
                return [];
            }}

            edges_raw.forEach(function(edge) {{
                var et = edge.type || (edge.edge_data && edge.edge_data.type);
                if (et === 'vpc_shared' || et === 'vpc_orphan') {{
                    var bundled = edgeBundled(edge);
                    bundled.forEach(function(link) {{
                        var sw = link.from || '';
                        if (memberPortMap.hasOwnProperty(sw)) {{
                            var vpcNum = edge.label ? edge.label.match(/vPC\\s*([0-9]+)/) : null;
                            var vpcLabel = vpcNum ? 'vPC ' + vpcNum[1] : (edge.type === 'vpc_orphan' ? 'Orphan' : 'vPC');
                            var downstream = link.to || '-';
                            var downPort = link.t_port || '-';
                            var st = link.f_int_data ? (link.f_int_data.status || 'unknown') : 'unknown';
                            var spd = link.f_int_data ? (link.f_int_data.speed || '-') : '-';
                            memberPortMap[sw].push({{
                                localPort: link.f_port || '-',
                                remoteDevice: downstream,
                                remotePort: downPort,
                                vpcLabel: vpcLabel,
                                status: st,
                                speed: spd
                            }});
                        }}
                    }});
                }} else if ((edge.from === '' || edge.to === '') && edge.is_vpc_member) {{
                    var sw2 = edge.from;
                    if (memberPortMap.hasOwnProperty(sw2)) {{
                        memberPortMap[sw2].push({{
                            localPort: edge.f_port || '-',
                            remoteDevice: edge.to,
                            remotePort: edge.t_port || '-',
                            vpcLabel: 'vPC',
                            status: (edge.f_int_data || {{}}).status || 'unknown',
                            speed: (edge.f_int_data || {{}}).speed || '-'
                        }});
                    }}
                }}
            }});

            // Fallback: vpc_member_interfaces / vpc_structured from domain node (show vpc + Po members)
            var domainNode = nodes.get(domain.nodeId);
            if (domainNode) {{
                var bySwitch = domainNode.vpc_member_interfaces || {{}};
                domain.members.forEach(function(member) {{
                    var block = bySwitch[member];
                    if (!block || !block.entries) return;
                    block.entries.forEach(function(ent) {{
                        if (ent.entry_type === 'peer-link') return;
                        var ifaces = ent.member_interfaces || [];
                        if (ifaces.length === 0 && ent.port_channel) {{
                            memberPortMap[member].push({{
                                localPort: ent.port_channel,
                                remoteDevice: '(vPC table)',
                                remotePort: '-',
                                vpcLabel: ent.vpc_id ? ('vPC ' + ent.vpc_id) : 'vPC',
                                status: ent.status || 'unknown',
                                speed: '-'
                            }});
                        }} else {{
                            ifaces.forEach(function(lp) {{
                                memberPortMap[member].push({{
                                    localPort: lp,
                                    remoteDevice: ent.port_channel || '(Po)',
                                    remotePort: '-',
                                    vpcLabel: ent.vpc_id ? ('vPC ' + ent.vpc_id) : 'vPC',
                                    status: ent.status || 'unknown',
                                    speed: '-'
                                }});
                            }});
                        }}
                    }});
                }});
            }}
            
            function dedupePorts(ports) {{
                var seen = {{}};
                var out = [];
                ports.forEach(function(p) {{
                    var k = (p.localPort || '') + '|' + (p.remoteDevice || '') + '|' + (p.vpcLabel || '');
                    if (seen[k]) return;
                    seen[k] = true;
                    out.push(p);
                }});
                return out;
            }}

            domain.members.forEach(function(member) {{
                html += '<div class="interface-category">';
                html += '<div class="category-header">&#128187; ' + member + '</div>';
                
                var ports = dedupePorts(memberPortMap[member] || []);
                
                if (ports.length > 0) {{
                    html += '<table style="width:100%; font-size:11px; border-collapse:collapse; margin-top:4px;">';
                    html += '<tr style="color:#94a3b8; font-size:10px; text-transform:uppercase;">' +
                        '<th style="padding:4px 6px; text-align:left;">Local Port</th>' +
                        '<th style="padding:4px 6px; text-align:left;">↔ Remote Device</th>' +
                        '<th style="padding:4px 6px; text-align:left;">Remote Port</th>' +
                        '<th style="padding:4px 6px; text-align:left;">vPC</th>' +
                        '<th style="padding:4px 6px; text-align:left;">Status</th>' +
                        '<th style="padding:4px 6px; text-align:left;">Speed</th>' +
                    '</tr>';
                    ports.forEach(function(p) {{
                        var stCol = p.status === 'up' ? '#22c55e' : '#ef4444';
                        html += '<tr style="border-top:1px solid rgba(255,255,255,0.05);">' +
                            '<td style="padding:5px 6px; font-family:monospace; font-weight:700; color:#38bdf8;">' + p.localPort + '</td>' +
                            '<td style="padding:5px 6px; color:#c4b5fd; font-weight:600;">' + p.remoteDevice + '</td>' +
                            '<td style="padding:5px 6px; font-family:monospace; color:#a78bfa;">' + p.remotePort + '</td>' +
                            '<td style="padding:5px 6px; color:#fb923c; font-weight:700;">' + p.vpcLabel + '</td>' +
                            '<td style="padding:5px 6px; color:' + stCol + '; font-weight:700; text-transform:uppercase;">' + p.status + '</td>' +
                            '<td style="padding:5px 6px; color:#94a3b8;">' + p.speed + '</td>' +
                        '</tr>';
                    }});
                    html += '</table>';
                }} else {{
                    html += '<div style="padding:8px; color:#64748b; font-size:12px;">No vPC member ports detected for this switch</div>';
                }}
                
                html += '</div>';
            }});
            
            document.getElementById('vpc-interfaces-content').innerHTML = html;
        }},
        
        // Show Connection Intelligence View
        showConnectionIntelligence: function() {{
            var domain = this.selectedVPCDomain;
            if (!domain) return;
            
            // Update header
            document.getElementById('intel-domain-title').textContent = 'VPC Domain ' + domain.id;
            
            // Render shared connections (v6.9.0 Validation overlay)
            var sharedHtml = '';
            if (domain.sharedConnections.length > 0) {{
                domain.sharedConnections.forEach(function(conn) {{
                    var targetNode = conn.from.indexOf('VPC_Domain_') === 0 ? conn.to : conn.from;
                    var linkCount = conn.bundled_links ? conn.bundled_links.length : 1;
                    var validationBadge = conn.cdp_validated ? 
                        '<span style="background:#059669; color:white; padding:2px 6px; border-radius:10px; font-size:10px; margin-left:8px;">&#10004; Validated</span>' : 
                        '<span style="background:#d97706; color:white; padding:2px 6px; border-radius:10px; font-size:10px; margin-left:8px;">&#9888; Inferred</span>';
                        
                    sharedHtml += 
                        '<div class="connection-card shared">' +
                            '<div class="connection-title">&#9989; ' + targetNode + validationBadge + '</div>' +
                            '<div class="connection-meta">' +
                                'Connected to both members via ' + (conn.label || 'vPC') + '<br>' +
                                linkCount + ' physical link' + (linkCount > 1 ? 's' : '') +
                            '</div>' +
                        '</div>';
                }});
            }} else {{
                sharedHtml = '<div style="padding:12px; color:#64748b; font-size:12px;">No shared connections detected</div>';
            }}
            document.getElementById('shared-connections-list').innerHTML = sharedHtml;
            
            // Render orphan connections
            var orphanHtml = '';
            if (domain.orphanConnections.length > 0) {{
                domain.orphanConnections.forEach(function(conn) {{
                    var targetNode = conn.from.indexOf('VPC_Domain_') === 0 ? conn.to : conn.from;
                    var member = conn.from.indexOf('VPC_Domain_') === 0 ? conn.to : conn.from;
                    orphanHtml += 
                        '<div class="connection-card orphan">' +
                            '<div class="connection-title">&#9888;&#65039; ' + targetNode + '</div>' +
                            '<div class="connection-meta">' +
                                'Connected only to: <strong>' + member + '</strong><br>' +
                                'Port: ' + (conn.f_port || '--') +
                            '</div>' +
                            '<div class="risk-badge">RISK: Not redundant</div>' +
                        '</div>';
                }});
            }} else {{
                orphanHtml = '<div style="padding:12px; color:#27ae60; font-size:12px;">&#9989; No single-homed connections detected - all connections are redundant!</div>';
            }}
            document.getElementById('orphan-connections-list').innerHTML = orphanHtml;
            
            // Switch to intelligence view
            this.switchView('intelligence');
        }},
        
        // Highlight VPC domain on map
        highlightVPCDomain: function() {{
            var domain = this.selectedVPCDomain;
            if (!domain) return;
            
            // Select the VPC domain node
            network.selectNodes([domain.nodeId]);
            
            // Focus camera on it
            network.focus(domain.nodeId, {{
                scale: 1.2,
                animation: {{
                    duration: 500,
                    easingFunction: 'easeInOutQuad'
                }}
            }});
        }},
        
        // Export connection report
        exportConnectionReport: function() {{
            var domain = this.selectedVPCDomain;
            if (!domain) return;
            
            var report = [
                'VPC DOMAIN ' + domain.id + ' - Connection Report',
                'Generated: ' + new Date().toLocaleString(),
                '',
                'MEMBER DEVICES:',
                domain.members.join(', '),
                '',
                'SHARED CONNECTIONS (Dual-Homed):',
            ];
            
            if (domain.sharedConnections.length > 0) {{
                domain.sharedConnections.forEach(function(conn) {{
                    var target = conn.from.indexOf('VPC_Domain_') === 0 ? conn.to : conn.from;
                    report.push('  - ' + target + ' via ' + (conn.label || 'vPC'));
                }});
            }} else {{
                report.push('  None detected');
            }}
            
            report.push('');
            report.push('NON-SHARED CONNECTIONS (Single-Homed - RISK):');
            
            if (domain.orphanConnections.length > 0) {{
                domain.orphanConnections.forEach(function(conn) {{
                    var target = conn.from.indexOf('VPC_Domain_') === 0 ? conn.to : conn.from;
                    report.push('  - ' + target + ' [RISK: Not redundant]');
                }});
            }} else {{
                report.push('  None detected - All connections are redundant');
            }}
            
            // Download as text file
            var blob = new Blob([report.join('\\n')], {{ type: 'text/plain' }});
            var url = URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.href = url;
            a.download = 'vpc-domain-' + domain.id + '-report.txt';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }}
    }};
    
    // ============================================
    // ENHANCED EVENT HANDLERS FOR 3-VIEW SYSTEM
    // ============================================
    
    // Override the selectNode handler to support VPC domains
    network.off('selectNode');
    network.on('selectNode', function(params) {{
        try {{
            if (params.nodes.length > 0) {{
                var nodeId = params.nodes[0];
                var nodeData = nodes.get(nodeId);
                if (!nodeData) return;
                
                // Check if this is a VPC domain node
                if (nodeId && String(nodeId).indexOf('VPC_Domain_') === 0) {{
                    if (typeof app !== 'undefined' && app.showVPCDetail) {{
                        app.showVPCDetail(nodeId);
                    }}
                }} else {{
                    // Standard node - show original panel
                    renderNodePanel(nodeData);
                    document.getElementById('side-panel').style.display = 'flex';
                    document.getElementById('mynetwork').classList.add('panel-open');
                    document.getElementById('vpc-detail-panel').style.display = 'none';
                    document.getElementById('connection-intelligence-panel').style.display = 'none';
                    
                    // Trigger resize
                    setTimeout(function() {{ network.fit({{ animation: false }}); }}, 100);
                }}
            }}
        }} catch (e) {{
            console.error('[VIS] Error in selectNode:', e);
        }}
    }});
    
    }}

    if (!_mapModeVpc) {{
      if (_nstStandardMap && typeof nstBootStandardMap === 'function') {{
        nstBootStandardMap();
      }} else {{
        createTopologyNetwork();
        wireNetworkHandlers();
        if (typeof topoViewTab === 'function') {{
          try {{ topoViewTab('map'); }} catch (e) {{ console.warn('[TOPO] tab:', e); }}
        }}
        setTimeout(function() {{
          if (!network && typeof createTopologyNetwork === 'function') createTopologyNetwork();
          if (network) {{
            try {{ network.fit({{ animation: false }}); }} catch (e) {{}}
          }}
        }}, 120);
      }}
    }}

    // Initialize app on load (VPC detail panels; map boot is vpcCommandCenterInit for CC)
    if (typeof app !== 'undefined' && app.init) {{ try {{ app.init(); }} catch (appInitErr) {{ console.warn('[VPC] app.init:', appInitErr); }} }}
    {vpc_init_script}
    {vpc_board_script}
    
    if (!_mapModeVpc) {{
        startFlowAnimation();
        if (network) network.once('stabilized', function() {{
            try {{
                network.setOptions({{ physics: {{ enabled: false }} }});
                stopFlowAnimation();
            }} catch (physErr) {{ console.warn('[VIS] physics disable:', physErr); }}
            network.fit({{ animation: false }});
        }});
        setTimeout(function() {{ if (network) network.fit({{ animation: false }}); }}, 800);
    }} else {{
        stopFlowAnimation();
    }}
  </script>
</body>
</html>'''

    try:
        write_text_file(html_file, html_content)
    except Exception as e:
        _report_error("generate_topology_html", html_file, e)
        pass


# =============================================================================
# PLUGIN REPORT FUNCTIONS (v6.0+)
# Required by all plugins in modules/plugins/
# =============================================================================

def save_plugin_report(plugin_id: str, host: str, data: dict, formatter_func) -> str:
    """
    Save a plugin report to disk using the provided formatter function.

    Args:
        plugin_id:      Plugin identifier string (e.g. 'serial_number')
        host:           Device hostname or IP
        data:           Result data dict from the plugin run() function
        formatter_func: Callable(data, host) -> str that produces the report text

    Returns:
        Path to the saved report file (str)
    """
    from utils.output_paths import CAT_PLUGINS, path_in_run, prepare_run_output, slugify, write_run_manifest
    from utils.output_chrome import (
        PLUGIN_HINTS,
        plugin_display_name,
        wrap_plugin_html_report,
        wrap_plugin_text_report,
        write_run_readme,
    )

    safe_host = str(host).replace(":", "_").replace("/", "_").replace(".", "_")
    paths = prepare_run_output(CAT_PLUGINS, slugify(f'{plugin_id}_{safe_host}'))
    filename = path_in_run(paths, 'report.txt')
    html_file = paths.get('html_path') or path_in_run(paths, 'report.html')
    try:
        raw_content = formatter_func(data, host)
        content = wrap_plugin_text_report(plugin_id, host, raw_content)
        write_text_file(filename, content)
        html_body = wrap_plugin_html_report(plugin_id, host, content)
        write_text_file(html_file, html_body)
        write_run_manifest(paths, {
            'plugin_id': plugin_id,
            'host': host,
            'report_path': filename,
            'html_path': html_file,
        })
        write_run_readme(
            paths,
            title=plugin_display_name(plugin_id),
            task_summary=f'Device: {host}',
            hints=PLUGIN_HINTS.get(plugin_id),
        )
    except Exception as e:
        _report_error("save_plugin_report", filename, e)
    return filename


def append_to_master_report(plugin_id: str, host: str, status: str,
                             summary: str, report_path: str) -> None:
    """
    Append a one-line entry to the master plugin run log.

    Args:
        plugin_id:   Plugin identifier
        host:        Device hostname or IP
        status:      'success' | 'fail'
        summary:     Short human-readable summary of the result
        report_path: Path to the individual report file (or 'N/A')
    """
    from utils.output_paths import get_master_log_path
    master_file = get_master_log_path('plugin_execution_summary.txt')
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_icon = "✅" if status == "success" else "❌"
    line = f"[{ts}] {status_icon} [{plugin_id}] {host} | {summary} | Report: {report_path}"
    append_text_file(master_file, line)


def generate_consolidated_plugin_report(plugin_id: str, results: list) -> str:
    """
    Generate a consolidated human-readable report from multi-device plugin results.

    Args:
        plugin_id: Plugin identifier
        results:   List of result dicts from run_generic_plugin()

    Returns:
        Path to the saved consolidated report file
    """
    from utils.output_paths import CAT_PLUGINS, path_in_run, prepare_run_output, slugify, write_run_manifest
    from utils.output_chrome import text_report_footer, text_report_header, write_run_readme

    paths = prepare_run_output(CAT_PLUGINS, slugify(f'{plugin_id}_consolidated'))
    filename = path_in_run(paths, 'consolidated_report.txt')

    body_lines = [
        f"Plugin Report: {plugin_id.replace('_', ' ').title()}",
        f"Devices:       {len(results)}",
        "",
    ]

    success_count = 0
    for res in results:
        host = res.get("device", res.get("host", "unknown"))
        status = res.get("status", "unknown")
        data = res.get("data", {})
        error = res.get("error", "")

        if status == "success":
            success_count += 1
            body_lines.append(f"[✅ SUCCESS] {host}")
            # Render key data fields
            for k, v in data.items():
                if k in ("true_host", "raw_output"):
                    continue
                if isinstance(v, list):
                    body_lines.append(f"  {k}: {len(v)} items")
                elif isinstance(v, dict):
                    body_lines.append(f"  {k}: {len(v)} entries")
                else:
                    body_lines.append(f"  {k}: {v}")
        else:
            body_lines.append(f"[❌ FAILED]  {host}: {error}")
        body_lines.append("")

    summary = f"Summary: {success_count}/{len(results)} devices successful"
    content = (
        text_report_header(
            f"Consolidated — {plugin_id.replace('_', ' ').title()}",
            subtitle=f"Multi-device run · {len(results)} target(s)",
            hints=[
                'Each device section shows SUCCESS or FAILED with key fields',
                'Open individual device folders under outputs/plugins/ for detail',
            ],
        )
        + "\n".join(body_lines)
        + text_report_footer(summary=summary)
    )
    write_text_file(filename, content)
    write_run_manifest(paths, {'plugin_id': plugin_id, 'report_path': filename, 'devices': len(results)})
    write_run_readme(
        paths,
        title=f'Consolidated {plugin_id.replace("_", " ").title()}',
        task_summary=summary,
        files={'consolidated_report.txt': 'Multi-device summary — plain text'},
    )
    return filename


# ── Per-plugin format functions ───────────────────────────────────────────────
# Each returns a formatted string report for a single device result.

def format_vlan_audit_report(data: dict, host: str) -> str:
    """Format VLAN audit plugin result for a single device."""
    lines = [
        f"VLAN Audit Report — {host}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 50,
        "",
    ]
    vlans = data.get("vlans", [])
    if vlans:
        lines.append(f"VLANs Found: {len(vlans)}")
        lines.append(f"{'ID':<8} {'Name':<30} {'Status'}")
        lines.append("-" * 50)
        for v in vlans:
            if isinstance(v, (list, tuple)) and len(v) >= 2:
                vid, vname = str(v[0]), str(v[1])
                vstatus = str(v[2]) if len(v) > 2 else "active"
            elif isinstance(v, dict):
                vid = str(v.get("id", "?"))
                vname = str(v.get("name", "Unknown"))
                vstatus = str(v.get("status", "active"))
            else:
                vid, vname, vstatus = str(v), "Unknown", "active"
            lines.append(f"{vid:<8} {vname:<30} {vstatus}")
    else:
        lines.append("No VLANs found or data unavailable.")
    return "\n".join(lines)


def format_vpc_domain_report(data: dict, host: str) -> str:
    """Format vPC domain plugin result for a single device."""
    lines = [
        f"vPC Domain Report — {host}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 50,
        "",
    ]
    if not data.get("present"):
        lines.append("vPC Domain: Not configured / not detected on this device.")
        if data.get("message"):
            lines.append(f"Note: {data['message']}")
        return "\n".join(lines)
    lines += [
        f"Hostname:           {data.get('true_host', host)}",
        f"vPC Domain ID:      {data.get('domain_id', 'N/A')}",
        f"Role:               {data.get('role', 'unknown')}",
        f"Peer-Link Status:   {data.get('peer_status', 'unknown')}",
        f"Keepalive Status:   {data.get('keepalive_status', 'unknown')}",
    ]
    return "\n".join(lines)


def format_serial_number_report(data: dict, host: str) -> str:
    """Format serial number plugin result for a single device."""
    lines = [
        f"Serial Number Report — {host}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 50,
        "",
    ]
    serial = data.get("serial_number", data.get("serial", "N/A"))
    model = data.get("model", "N/A")
    hostname = data.get("true_host", host)
    lines += [
        f"Hostname:      {hostname}",
        f"Model:         {model}",
        f"Serial Number: {serial}",
    ]
    # Handle stacked/module serials
    modules = data.get("modules", [])
    if modules:
        lines.append("")
        lines.append("Module Serials:")
        for m in modules:
            if isinstance(m, dict):
                lines.append(f"  Slot {m.get('slot','?')}: {m.get('serial','N/A')} ({m.get('description','N/A')})")
            else:
                lines.append(f"  {m}")
    return "\n".join(lines)


def format_device_time_report(data: dict, host: str) -> str:
    """Format device time/NTP plugin result for a single device."""
    lines = [
        f"Device Time Report — {host}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 50,
        "",
        f"Device Time:   {data.get('device_time', 'N/A')}",
        f"Timezone:      {data.get('timezone', 'N/A')}",
        f"NTP Status:    {data.get('ntp_status', 'N/A')}",
        f"NTP Server:    {data.get('ntp_server', 'N/A')}",
        f"NTP Synced:    {'Yes ✅' if data.get('ntp_synced') else 'No ❌'}",
    ]
    ntp_peers = data.get("ntp_peers", [])
    if ntp_peers:
        lines.append("")
        lines.append("NTP Peers:")
        for p in ntp_peers:
            if isinstance(p, dict):
                lines.append(f"  {p.get('address','?')} — {p.get('status','?')}")
            else:
                lines.append(f"  {p}")
    return "\n".join(lines)


def generate_consolidated_standards_report(policy_file: str, sev_filter: str, cat_filter: str, results: list) -> str:
    """
    v6.5.8: Generate a single consolidated report for Standards Validator bulk runs.
    
    Args:
        policy_file: Path to the policy file used
        sev_filter: Severity filter applied
        cat_filter: Category filter applied
        results: List of all device results
        
    Returns:
        Path to the saved consolidated report file
    """
    from utils.output_paths import CAT_COMPLIANCE, path_in_run, prepare_run_output, slugify, write_run_manifest

    paths = prepare_run_output(CAT_COMPLIANCE, slugify('consolidated'))
    filename = path_in_run(paths, 'standards_consolidated.txt')
    
    total_devices = len(results)
    compliant_count = sum(1 for r in results if r.get('data', {}).get('compliant', False))
    non_compliant_count = total_devices - compliant_count
    
    # Count total violations
    total_violations = 0
    critical_violations = 0
    high_violations = 0
    for r in results:
        violations = r.get('data', {}).get('violations', [])
        total_violations += len(violations)
        critical_violations += sum(1 for v in violations if v.get('severity') == 'critical')
        high_violations += sum(1 for v in violations if v.get('severity') == 'high')
    
    lines = [
        "=" * 80,
        "NETWORK SWISS TOOL PRO - STANDARDS VALIDATOR CONSOLIDATED REPORT",
        "=" * 80,
        "",
        f"Generated:        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Policy File:      {policy_file}",
        f"Severity Filter:  {sev_filter}",
        f"Category Filter:  {cat_filter if cat_filter else 'All'}",
        "",
        "-" * 80,
        "SUMMARY",
        "-" * 80,
        f"Total Devices:        {total_devices}",
        f"Compliant:            {compliant_count} ({compliant_count/total_devices*100:.1f}%)" if total_devices > 0 else "Compliant:            0",
        f"Non-Compliant:        {non_compliant_count} ({non_compliant_count/total_devices*100:.1f}%)" if total_devices > 0 else "Non-Compliant:        0",
        f"Total Violations:     {total_violations}",
        f"  Critical:           {critical_violations}",
        f"  High:               {high_violations}",
        "",
        "=" * 80,
        "DETAILED RESULTS BY DEVICE",
        "=" * 80,
        "",
    ]
    
    # Sort results: non-compliant first, then by hostname
    sorted_results = sorted(results, key=lambda r: (r.get('data', {}).get('compliant', True), r.get('device', '')))
    
    for res in sorted_results:
        host = res.get('device', 'unknown')
        data = res.get('data', {})
        status = res.get('status', 'unknown')
        error = res.get('error', '')
        
        if status == 'fail':
            lines.append(f"❌ {host} - ERROR: {error}")
            lines.append("")
            continue
            
        compliant = data.get('compliant', False)
        violations = data.get('violations', [])
        checked = data.get('policies_checked', 0)
        true_host = data.get('true_host', host)
        
        # Header with status
        status_icon = "✅" if compliant else "❌"
        lines.append(f"{status_icon} {host} ({true_host})")
        lines.append(f"   Status: {'COMPLIANT' if compliant else 'NON-COMPLIANT'} | Policies Checked: {checked}")
        
        if violations:
            lines.append(f"   Violations ({len(violations)}):")
            for v in violations:
                sev = v.get('severity', 'medium').upper()
                pid = v.get('policy_id', 'unknown')
                cat = v.get('category', 'General')
                desc = v.get('description', '')
                lines.append(f"      [{sev}] {pid} ({cat})")
                lines.append(f"         {desc}")
                if v.get('remediation'):
                    rem = v.get('remediation', '').replace('\n', '\n         ')
                    lines.append(f"         Fix: {rem}")
        lines.append("")
    
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)
    
    content = "\n".join(lines)
    write_text_file(filename, content)
    html_path = path_in_run(paths, 'standards_gap_analysis.html')
    try:
        from modules.plugins.standards_validator import _generate_html_standards_report
        html = _generate_html_standards_report(results, policy_file, datetime.now().isoformat())
        write_text_file(html_path, html)
    except Exception:
        html_path = ''
    write_run_manifest(paths, {
        'report_path': filename,
        'html_path': html_path or None,
        'policy_file': policy_file,
        'total_devices': total_devices,
    })
    return filename


def format_critical_logs_report(data: dict, host: str) -> str:
    """Format critical logs plugin result for a single device."""
    lines = [
        f"Critical Logs Report — {host}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 50,
        "",
    ]
    log_entries = data.get("logs", data.get("critical_logs", []))
    if log_entries:
        lines.append(f"Critical Log Entries Found: {len(log_entries)}")
        lines.append("")
        for entry in log_entries:
            if isinstance(entry, dict):
                lines.append(f"  [{entry.get('severity','?')}] {entry.get('timestamp','?')} — {entry.get('message','?')}")
            else:
                lines.append(f"  {entry}")
    else:
        lines.append("No critical log entries found. ✅")
    return "\n".join(lines)


def format_interface_errors_report(data: dict, host: str) -> str:
    """Format interface errors plugin result for a single device."""
    lines = [
        f"Interface Errors Report — {host}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 50,
        "",
    ]
    interfaces = data.get("interfaces", data.get("error_interfaces", []))
    if interfaces:
        lines.append(f"Interfaces with Errors: {len(interfaces)}")
        lines.append(f"{'Interface':<20} {'In Errors':<12} {'Out Errors':<12} {'CRC':<10} {'Resets'}")
        lines.append("-" * 70)
        for intf in interfaces:
            if isinstance(intf, dict):
                lines.append(
                    f"{intf.get('interface','?'):<20} "
                    f"{str(intf.get('input_errors', 0)):<12} "
                    f"{str(intf.get('output_errors', 0)):<12} "
                    f"{str(intf.get('crc', 0)):<10} "
                    f"{str(intf.get('resets', 0))}"
                )
            else:
                lines.append(f"  {intf}")
    else:
        lines.append("No interface errors found. ✅")
    return "\n".join(lines)


def format_asset_warranty_report(data: dict, host: str) -> str:
    """Format asset warranty plugin result for a single device."""
    lines = [
        f"Cisco Asset & Warranty Inventory — {host}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Summary: {data.get('collection_summary', '')}",
        "=" * 50,
        "",
    ]
    for idx, asset in enumerate(data.get('assets') or [], 1):
        lines.append(f"--- Asset {idx} ---")
        for key in (
            'hostname', 'collection_method', 'pid', 'vid', 'serial_number',
            'software_version', 'warranty_end', 'warranty_status',
            'contract_status', 'severity', 'error',
        ):
            val = asset.get(key)
            if val not in (None, ''):
                lines.append(f"  {key}: {val}")
        lines.append('')
    return "\n".join(lines)


def format_asset_warranty_csv(data: dict, host: str) -> str:
    """Format asset warranty plugin result as CSV matching demo format.
    
    Matches demo_cisco_eol_catalog.html format with clear EOL/EOS display.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[CSV_FORMATTER] === CSV FORMATTING START ===")
    logger.info(f"[CSV_FORMATTER] Host: {host}")
    logger.info(f"[CSV_FORMATTER] Data keys: {list(data.keys())}")
    
    assets = data.get('assets') or []
    logger.info(f"[CSV_FORMATTER] Asset count: {len(assets)}")
    
    if not assets:
        logger.warning("[CSV_FORMATTER] No assets to format")
        return ""
    
    if assets:
        logger.info(f"[CSV_FORMATTER] First asset keys: {list(assets[0].keys())}")
        logger.info(f"[CSV_FORMATTER] First asset EOL fields: end_of_life={assets[0].get('end_of_life', 'MISSING')}, end_of_support={assets[0].get('end_of_support', 'MISSING')}")
    
    # Match demo format columns
    fieldnames = [
        'Host',
        'Hostname',
        'Product ID (PID)',
        'Serial Number',
        'Software Version',
        'Warranty Status',
        'End of Life',
        'End of Support',
    ]
    
    logger.info(f"[CSV_FORMATTER] CSV fieldnames: {fieldnames}")
    
    rows = []
    for idx, asset in enumerate(assets):
        row = {
            'Host': asset.get('host', data.get('host', '')),
            'Hostname': asset.get('hostname', ''),
            'Product ID (PID)': asset.get('pid', ''),
            'Serial Number': asset.get('serial_number', ''),
            'Software Version': asset.get('software_version', ''),
            'Warranty Status': asset.get('warranty_status', ''),
            'End of Life': asset.get('end_of_life', ''),
            'End of Support': asset.get('end_of_support', ''),
        }
        rows.append(row)
        if idx == 0:
            logger.info(f"[CSV_FORMATTER] First row PID: {row.get('Product ID (PID)', 'MISSING')}")
            logger.info(f"[CSV_FORMATTER] First row End of Life: {row.get('End of Life', 'MISSING')}")
    
    logger.info(f"[CSV_FORMATTER] Total rows: {len(rows)}")
    logger.info(f"[CSV_FORMATTER] === CSV FORMATTING END ===")
    
    # Write CSV to string
    import io
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def format_asset_warranty_html(data: dict, host: str) -> str:
    """Format asset warranty plugin result as HTML with clickable PIDs and modal.
    
    Matches demo_cisco_eol_catalog.html format with clear EOL/EOS display.
    """
    import logging
    logger = logging.getLogger(__name__)
    from html import escape
    
    logger.info(f"[HTML_FORMATTER] === HTML FORMATTING START ===")
    logger.info(f"[HTML_FORMATTER] Host: {host}")
    logger.info(f"[HTML_FORMATTER] Data keys: {list(data.keys())}")
    
    assets = data.get('assets') or []
    logger.info(f"[HTML_FORMATTER] Asset count: {len(assets)}")
    
    if not assets:
        logger.warning("[HTML_FORMATTER] No assets to format")
        return '<p>No assets collected.</p>'
    
    if assets:
        logger.info(f"[HTML_FORMATTER] First asset keys: {list(assets[0].keys())}")
        logger.info(f"[HTML_FORMATTER] First asset EOL fields: end_of_life={assets[0].get('end_of_life', 'MISSING')}, end_of_support={assets[0].get('end_of_support', 'MISSING')}")
    
    # Build HTML table matching demo format
    rows_html = []
    for asset in assets:
        host_ip = asset.get('host', data.get('host', ''))
        hostname = asset.get('hostname', '')
        pid = asset.get('pid', '')
        serial = asset.get('serial_number', '')
        software = asset.get('software_version', '')
        
        # Get warranty status and calculate display
        warranty_status = asset.get('warranty_status', 'unknown')
        status_badge = _get_warranty_status_badge(warranty_status)
        
        # Get EOL/EOS dates - ensure they are displayed clearly
        eol = asset.get('end_of_life', '')
        eos = asset.get('end_of_support', '')
        
        # Log first row for debugging
        if not rows_html:
            logger.info(f"[HTML_FORMATTER] First row - Host: {host_ip}, PID: {pid}, EOL: {eol}, EOS: {eos}")
        
        # Create clickable PID
        pid_display = f'<a class="nst-clickable-pid" onclick="openCiscoEolCatalog(\'{escape(pid)}\')">{escape(pid)}</a>' if pid else ''
        
        rows_html.append(f'''
            <tr>
                <td>{escape(host_ip)}</td>
                <td>{escape(hostname)}</td>
                <td>{pid_display}</td>
                <td>{escape(serial)}</td>
                <td>{escape(software)}</td>
                <td>{status_badge}</td>
                <td>{escape(eol)}</td>
                <td>{escape(eos)}</td>
            </tr>
        ''')
    
    logger.info(f"[HTML_FORMATTER] Total rows: {len(rows_html)}")
    logger.info(f"[HTML_FORMATTER] === HTML FORMATTING END ===")
    
    table_html = f'''
        <table>
            <thead>
                <tr>
                    <th>Host</th>
                    <th>Hostname</th>
                    <th>Product ID (PID)</th>
                    <th>Serial Number</th>
                    <th>Software Version</th>
                    <th>Warranty Status</th>
                    <th>End of Life</th>
                    <th>End of Support</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows_html)}
            </tbody>
        </table>
    '''
    
    # Add modal and JavaScript
    modal_html = _get_cisco_eol_modal()
    js_html = _get_cisco_eol_javascript()
    
    return table_html + modal_html + js_html


def _get_warranty_status_badge(status: str) -> str:
    """Generate HTML badge for warranty status."""
    status_norm = (status or 'unknown').strip().lower()
    badges = {
        'active': '<span class="nst-status-badge nst-status-active">Active</span>',
        'expired': '<span class="nst-status-badge nst-status-expired">Expired</span>',
        'warning': '<span class="nst-status-badge nst-status-warning">Expiring Soon</span>',
        'unknown': '<span class="nst-status-badge nst-status-unknown">Unknown</span>',
        'not a cisco device': (
            '<span class="nst-status-badge nst-status-info" '
            'style="background:#e0f2fe;color:#075985;border:1px solid #7dd3fc;">'
            'not a cisco device</span>'
        ),
    }
    if status_norm in badges:
        return badges[status_norm]
    if 'not a cisco' in status_norm:
        return badges['not a cisco device']
    return badges['unknown']


def _get_cisco_eol_modal() -> str:
    """Generate HTML modal for Cisco EOL catalog."""
    return '''
    <div id="nst-cisco-eol-modal" class="nst-modal-overlay" style="display: none;">
        <div class="nst-modal-content">
            <div class="nst-modal-header">
                <div class="nst-modal-title">📚 Cisco EOL/EOS Model Catalog</div>
                <button class="nst-modal-close" onclick="closeCiscoEolCatalog()">×</button>
            </div>
            <div class="nst-modal-body">
                <div class="nst-toolbar">
                    <input type="text" id="nst-eol-search" placeholder="Search by PID, model name..." oninput="filterCiscoEolCatalog()">
                    <button onclick="clearCiscoEolSearch()">Clear</button>
                    <div class="nst-filter-btns">
                        <button class="nst-filter-btn active" id="nst-btn-all" onclick="setCiscoEolFilter('all')">All</button>
                        <button class="nst-filter-btn" id="nst-btn-active" onclick="setCiscoEolFilter('active')">Active</button>
                        <button class="nst-filter-btn" id="nst-btn-expired" onclick="setCiscoEolFilter('expired')">Expired</button>
                        <button class="nst-filter-btn" id="nst-btn-warning" onclick="setCiscoEolFilter('warning')">Expiring Soon</button>
                    </div>
                </div>
                <table id="nst-eol-table">
                    <thead>
                        <tr>
                            <th>PID</th>
                            <th>Model Name</th>
                            <th>End of Life</th>
                            <th>End of Support</th>
                            <th>End of Service</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="nst-eol-body">
                        <!-- Populated by JavaScript -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    '''


def _get_cisco_eol_javascript() -> str:
    """Generate JavaScript for Cisco EOL catalog modal with data from database."""
    try:
        from modules.cisco_eol_database import get_all_models, seed_demo_data
        import json
        
        # Try to load from database first
        models = get_all_models()
        
        if not models:
            # Fallback to demo data if database is unavailable
            models = seed_demo_data()
        
        # Convert models to JavaScript array format
        js_models = []
        for model in models:
            js_models.append({
                'pid': model.get('pid', ''),
                'name': model.get('model_name', ''),
                'eol': model.get('end_of_life', ''),
                'eos': model.get('end_of_support', ''),
                'eosvc': model.get('end_of_service', ''),
                'status': model.get('warranty_status', 'unknown')
            })
        
        # Generate JavaScript with dynamic data
        js_data = json.dumps(js_models)
        
        return f'''
    <script>
    // Data loaded from Cisco EOL/EOS database ({len(js_models)} models)
    const ciscoEolData = {js_data};
    
    let ciscoEolFilter = 'all';
    let ciscoEolHighlightedPid = null;
    
    function openCiscoEolCatalog(pid) {{
        ciscoEolHighlightedPid = pid;
        document.getElementById('nst-cisco-eol-modal').style.display = 'flex';
        renderCiscoEolCatalog();
        highlightCiscoEolRow(pid);
    }}
    
    function closeCiscoEolCatalog() {{
        document.getElementById('nst-cisco-eol-modal').style.display = 'none';
        ciscoEolHighlightedPid = null;
    }}
    
    function getCiscoEolStatusBadge(status) {{
        const badges = {{
            'active': '<span class="nst-status-badge nst-status-active">Active</span>',
            'expired': '<span class="nst-status-badge nst-status-expired">Expired</span>',
            'warning': '<span class="nst-status-badge nst-status-warning">Expiring Soon</span>',
            'unknown': '<span class="nst-status-badge nst-status-unknown">Unknown</span>'
        }};
        return badges[status] || badges['unknown'];
    }}
    
    function renderCiscoEolCatalog() {{
        const searchTerm = document.getElementById('nst-eol-search').value.toLowerCase();
        const tbody = document.getElementById('nst-eol-body');
        
        let filteredData = ciscoEolData.filter(item => {{
            const matchesSearch = item.pid.toLowerCase().includes(searchTerm) || 
                                 item.name.toLowerCase().includes(searchTerm);
            const matchesFilter = ciscoEolFilter === 'all' || item.status === ciscoEolFilter;
            return matchesSearch && matchesFilter;
        }});
        
        if (filteredData.length === 0) {{
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No models found matching your search.</td></tr>';
            return;
        }}
        
        tbody.innerHTML = filteredData.map(item => `
            <tr data-pid="${{item.pid}}" class="${{item.pid === ciscoEolHighlightedPid ? 'nst-highlighted-row' : ''}}">
                <td><strong>${{item.pid}}</strong></td>
                <td>${{item.name}}</td>
                <td>${{item.eol}}</td>
                <td>${{item.eos}}</td>
                <td>${{item.eosvc}}</td>
                <td>${{getCiscoEolStatusBadge(item.status)}}</td>
            </tr>
        `).join('');
        
        if (ciscoEolHighlightedPid) {{
            highlightCiscoEolRow(ciscoEolHighlightedPid);
        }}
    }}
    
    function highlightCiscoEolRow(pid) {{
        document.querySelectorAll('#nst-eol-body tr').forEach(row => {{
            row.classList.remove('nst-highlighted-row');
        }});
        
        const row = document.querySelector(`tr[data-pid="${{pid}}"]`);
        if (row) {{
            row.classList.add('nst-highlighted-row');
            row.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        }}
    }}
    
    function filterCiscoEolCatalog() {{
        renderCiscoEolCatalog();
    }}
    
    function clearCiscoEolSearch() {{
        document.getElementById('nst-eol-search').value = '';
        renderCiscoEolCatalog();
    }}
    
    function setCiscoEolFilter(filter) {{
        ciscoEolFilter = filter;
        
        document.querySelectorAll('.nst-filter-btn').forEach(btn => {{
            btn.classList.remove('active');
        }});
        document.getElementById(`nst-btn-${{filter}}`).classList.add('active');
        
        renderCiscoEolCatalog();
    }}
    
    // Close modal on escape key
    document.addEventListener('keydown', (e) => {{
        if (e.key === 'Escape') {{
            closeCiscoEolCatalog();
        }}
    }});
    
    // Close modal on overlay click
    document.getElementById('nst-cisco-eol-modal').addEventListener('click', (e) => {{
        if (e.target.id === 'nst-cisco-eol-modal') {{
            closeCiscoEolCatalog();
        }}
    }});
    
    // Initial render
    renderCiscoEolCatalog();
    </script>
    '''
    except Exception as e:
        # Fallback to hardcoded demo data if database loading fails
        import logging
        logging.warning(f"Failed to load Cisco EOL data from database: {e}, using fallback")
        return '''
    <script>
    // Fallback demo data (database unavailable)
    const ciscoEolData = [
        {pid: 'N9K-C93180YC-EX', name: 'Nexus 93180YC-EX 48p 10/25G & 6p 100G', eol: '2027-08-31', eos: '2027-08-31', eosvc: '2027-08-31', status: 'active'},
        {pid: 'N9K-C93180LC-EX', name: 'Nexus 93180LC-EX 48p 10G', eol: '2025-08-31', eos: '2025-08-31', eosvc: '2025-08-31', status: 'warning'},
        {pid: 'N9K-C93180YC-FX', name: 'Nexus 93180YC-FX 48p 1/10/25G & 6p 40/100G', eol: '2029-07-31', eos: '2029-07-31', eosvc: '2029-07-31', status: 'active'},
        {pid: 'C9300-48P', name: 'Catalyst 9300 48-port PoE+', eol: '2030-12-01', eos: '2033-12-01', eosvc: '2036-12-01', status: 'active'},
        {pid: 'C9500-48Y4C', name: 'Catalyst 9500 48-port', eol: '2032-06-01', eos: '2035-06-01', eosvc: '2038-06-01', status: 'active'},
        {pid: 'ISR4451-X/K9', name: 'ISR 4451-X Router', eol: '2026-03-01', eos: '2027-03-01', eosvc: '2028-03-01', status: 'warning'},
        {pid: 'WS-C3750X-48S', name: 'Catalyst 3750X 48-port', eol: '2019-11-30', eos: '2020-11-30', eosvc: '2021-11-30', status: 'expired'},
    ];
    
    let ciscoEolFilter = 'all';
    let ciscoEolHighlightedPid = null;
    
    function openCiscoEolCatalog(pid) {{
        ciscoEolHighlightedPid = pid;
        document.getElementById('nst-cisco-eol-modal').style.display = 'flex';
        renderCiscoEolCatalog();
        highlightCiscoEolRow(pid);
    }}
    
    function closeCiscoEolCatalog() {{
        document.getElementById('nst-cisco-eol-modal').style.display = 'none';
        ciscoEolHighlightedPid = null;
    }}
    
    function getCiscoEolStatusBadge(status) {{
        const badges = {{
            'active': '<span class="nst-status-badge nst-status-active">Active</span>',
            'expired': '<span class="nst-status-badge nst-status-expired">Expired</span>',
            'warning': '<span class="nst-status-badge nst-status-warning">Expiring Soon</span>',
            'unknown': '<span class="nst-status-badge nst-status-unknown">Unknown</span>'
        }};
        return badges[status] || badges['unknown'];
    }}
    
    function renderCiscoEolCatalog() {{
        const searchTerm = document.getElementById('nst-eol-search').value.toLowerCase();
        const tbody = document.getElementById('nst-eol-body');
        
        let filteredData = ciscoEolData.filter(item => {{
            const matchesSearch = item.pid.toLowerCase().includes(searchTerm) || 
                                 item.name.toLowerCase().includes(searchTerm);
            const matchesFilter = ciscoEolFilter === 'all' || item.status === ciscoEolFilter;
            return matchesSearch && matchesFilter;
        }});
        
        if (filteredData.length === 0) {{
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No models found matching your search.</td></tr>';
            return;
        }}
        
        tbody.innerHTML = filteredData.map(item => `
            <tr data-pid="${{item.pid}}" class="${{item.pid === ciscoEolHighlightedPid ? 'nst-highlighted-row' : ''}}">
                <td><strong>${{item.pid}}</strong></td>
                <td>${{item.name}}</td>
                <td>${{item.eol}}</td>
                <td>${{item.eos}}</td>
                <td>${{item.eosvc}}</td>
                <td>${{getCiscoEolStatusBadge(item.status)}}</td>
            </tr>
        `).join('');
        
        if (ciscoEolHighlightedPid) {{
            highlightCiscoEolRow(ciscoEolHighlightedPid);
        }}
    }}
    
    function highlightCiscoEolRow(pid) {{
        document.querySelectorAll('#nst-eol-body tr').forEach(row => {{
            row.classList.remove('nst-highlighted-row');
        }});
        
        const row = document.querySelector(`tr[data-pid="${{pid}}"]`);
        if (row) {{
            row.classList.add('nst-highlighted-row');
            row.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        }}
    }}
    
    function filterCiscoEolCatalog() {{
        renderCiscoEolCatalog();
    }}
    
    function clearCiscoEolSearch() {{
        document.getElementById('nst-eol-search').value = '';
        renderCiscoEolCatalog();
    }}
    
    function setCiscoEolFilter(filter) {{
        ciscoEolFilter = filter;
        
        document.querySelectorAll('.nst-filter-btn').forEach(btn => {{
            btn.classList.remove('active');
        }});
        document.getElementById(`nst-btn-${{filter}}`).classList.add('active');
        
        renderCiscoEolCatalog();
    }}
    
    // Close modal on escape key
    document.addEventListener('keydown', (e) => {{
        if (e.key === 'Escape') {{
            closeCiscoEolCatalog();
        }}
    }});
    
    // Close modal on overlay click
    document.getElementById('nst-cisco-eol-modal').addEventListener('click', (e) => {{
        if (e.target.id === 'nst-cisco-eol-modal') {{
            closeCiscoEolCatalog();
        }}
    }});
    
    // Initial render
    renderCiscoEolCatalog();
    </script>
    '''


def format_environment_status_report(data: dict, host: str) -> str:
    """Format environment status plugin result for a single device."""
    lines = [
        f"Environment Status Report — {host}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 50,
        "",
    ]
    # Power supplies
    power = data.get("power_supplies", [])
    if power:
        lines.append("Power Supplies:")
        for ps in power:
            if isinstance(ps, dict):
                status_icon = "✅" if "ok" in str(ps.get("status", "")).lower() else "❌"
                lines.append(f"  {status_icon} {ps.get('name','?')}: {ps.get('status','?')}")
            else:
                lines.append(f"  {ps}")
        lines.append("")

    # Fans
    fans = data.get("fans", [])
    if fans:
        lines.append("Fans:")
        for fan in fans:
            if isinstance(fan, dict):
                status_icon = "✅" if "ok" in str(fan.get("status", "")).lower() else "❌"
                lines.append(f"  {status_icon} {fan.get('name','?')}: {fan.get('status','?')}")
            else:
                lines.append(f"  {fan}")
        lines.append("")

    # Temperature
    temps = data.get("temperature", [])
    if temps:
        lines.append("Temperature Sensors:")
        for t in temps:
            if isinstance(t, dict):
                status_icon = "✅" if "ok" in str(t.get("status", "")).lower() else "⚠️"
                lines.append(f"  {status_icon} {t.get('sensor','?')}: {t.get('value','?')} (Threshold: {t.get('threshold','?')})")
            else:
                lines.append(f"  {t}")

    if not power and not fans and not temps:
        lines.append("No environment data available.")

    return "\n".join(lines)
