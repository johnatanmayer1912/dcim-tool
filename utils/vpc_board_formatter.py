"""
vPC Engineering Board — offline-first tabular view (v6.9.27).
Rendered inside topology HTML when map_mode == 'vpc'.
"""
import html
import json


def vpc_board_css():
    return """
    .vpc-view-tabs { display:flex; gap:8px; margin:12px 0 16px 0; flex-wrap:wrap; }
    .vpc-view-tabs button {
      padding:10px 18px; border-radius:8px; border:1px solid #cbd5e1;
      background:#f8fafc; cursor:pointer; font-weight:600; font-size:13px;
    }
    .vpc-view-tabs button.active { background:#4f46e5; color:#fff; border-color:#4338ca; }
    #vpc-engineering-board {
      display:block; max-width:100%; overflow:auto;
      font-family: system-ui, Segoe UI, sans-serif;
      background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px;
      padding:16px; margin-bottom:12px;
    }
    #vpc-engineering-board.hidden { display:none !important; }
    body:not(.vpc-command-center) #mynetwork.map-tab-hidden { display:none !important; }
    body.vpc-command-center #vpc-engineering-board.hidden { display:block !important; }
    body.vpc-command-center .vpc-view-tabs { display:none !important; }
    .board-toolbar { display:flex; flex-wrap:wrap; gap:12px; align-items:center; margin-bottom:16px; }
    .board-toolbar label { font-size:12px; font-weight:600; color:#475569; }
    .board-toolbar select { padding:8px 12px; border-radius:6px; border:1px solid #cbd5e1; }
    .peer-strip { display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:12px; margin-bottom:16px; }
    .peer-card {
      background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:12px;
      box-shadow:0 1px 3px rgba(0,0,0,0.06);
    }
    .peer-card h4 { margin:0 0 8px 0; font-size:14px; color:#1e293b; }
    .peer-meta { font-size:12px; color:#64748b; line-height:1.5; }
    .peer-meta b { color:#334155; }
    .board-table-wrap { overflow-x:auto; margin-bottom:16px; }
    .board-table {
      width:100%; border-collapse:collapse; font-size:12px; background:#fff;
    }
    .board-table th {
      text-align:left; padding:8px 10px; background:#1e293b; color:#f1f5f9;
      font-weight:600; white-space:nowrap;
    }
    .board-table td { padding:8px 10px; border-bottom:1px solid #e2e8f0; vertical-align:top; }
    .board-table tr:nth-child(even) td { background:#f8fafc; }
    .st-up { color:#16a34a; font-weight:700; }
    .st-down { color:#dc2626; font-weight:700; }
    .board-section-title {
      font-size:13px; font-weight:700; color:#334155; margin:16px 0 8px 0;
      text-transform:uppercase; letter-spacing:0.04em;
    }
    .board-pre {
      font-size:11px; font-family: Consolas, monospace; white-space:pre-wrap;
      background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px;
      max-height:200px; overflow:auto;
    }
    .health-pill {
      display:inline-block; padding:4px 10px; border-radius:999px;
      font-size:11px; font-weight:700;
    }
    .health-HEALTHY { background:#dcfce7; color:#166534; }
    .health-WARNING { background:#fef3c7; color:#92400e; }
    .health-CRITICAL { background:#fee2e2; color:#991b1b; }
    .trust-pill {
      display:inline-block; padding:2px 8px; border-radius:999px;
      font-size:10px; font-weight:700; text-transform:uppercase;
    }
    .trust-verified { background:#d1fae5; color:#065f46; }
    .trust-high { background:#dbeafe; color:#1e40af; }
    .trust-medium { background:#fef3c7; color:#92400e; }
    .trust-low { background:#ffedd5; color:#9a3412; }
    .trust-inferred { background:#f1f5f9; color:#475569; }
    .trust-untrusted { background:#fee2e2; color:#991b1b; }
    .peer-unscanned-banner {
      background:#fffbeb; border:1px solid #f59e0b; border-radius:8px;
      padding:8px 10px; margin-bottom:8px; font-size:11px; color:#92400e;
    }
    @media print {
      .vpc-view-tabs, .topo-toolbar, .legend { display:none !important; }
      #vpc-engineering-board { border:none; }
      #mynetwork { display:none !important; }
    }
    """


def vpc_board_inner_html():
    """Board panel only (no legacy board/map tabs) — for VPC Command Center."""
    return """
  <div id="vpc-engineering-board">
    <h2 class="board-main-title" style="font-size:15px;font-weight:700;margin:0 0 10px 0;color:#1e293b;">Engineering Board</h2>
    <div class="board-toolbar">
      <label for="board-domain-select">vPC Domain</label>
      <select id="board-domain-select" onchange="boardRenderDomain(this.value)"></select>
      <span id="board-health-pill" class="health-pill health-HEALTHY">—</span>
    </div>
    <div id="board-peer-strip" class="peer-strip"></div>
    <div class="board-section-title">vPC Port-Channels</div>
    <div class="board-table-wrap"><table class="board-table" id="board-vpc-table">
      <thead><tr><th>Switch</th><th>vPC ID</th><th>Po</th><th>Status</th><th>Consistency</th><th>VLANs</th><th>Members</th></tr></thead>
      <tbody></tbody>
    </table></div>
    <div class="board-section-title">Downstream / Shared Links</div>
    <div class="board-table-wrap"><table class="board-table" id="board-downstream-table">
      <thead><tr><th>Switch</th><th>Local</th><th>Remote</th><th>Remote Port</th><th>Type</th><th>Trust</th></tr></thead>
      <tbody></tbody>
    </table></div>
    <div class="board-section-title">Interface Trust Chains</div>
    <div class="board-table-wrap"><table class="board-table" id="board-trust-chains-table">
      <thead><tr><th>Switch</th><th>Chain</th><th>Score</th><th>Tier</th><th>CDP</th><th>LACP</th></tr></thead>
      <tbody></tbody>
    </table></div>
    <div class="board-section-title">Global Consistency Parameters</div>
    <pre class="board-pre" id="board-global-consistency">—</pre>
    <div class="board-section-title">Alerts</div>
    <div id="board-alerts" style="font-size:12px;"></div>
  </div>
"""


def vpc_board_html_shell():
    return """
  <div class="vpc-view-tabs" id="vpc-view-tabs">
    <button type="button" id="tab-btn-board" class="active" onclick="vpcViewTab('board')">Engineering Board</button>
    <button type="button" id="tab-btn-map" onclick="vpcViewTab('map')">Simplified Map</button>
    <button type="button" onclick="window.print()">Print Board</button>
  </div>
""" + vpc_board_inner_html()


def vpc_board_js_initializer(board_payload_json, command_center=False):
    """Vanilla JS to render board from window.__VPC_BOARD__."""
    safe_json = board_payload_json or '{"domains":[]}'
    cc = "true" if command_center else "false"
    board_assign = "" if command_center else f"window.__VPC_BOARD__ = {safe_json};"
    auto_boot = "" if command_center else """
    document.addEventListener('DOMContentLoaded', function() {
      boardInit();
      vpcViewTab('board');
    });
    """
    return f"""
    {board_assign}
    window.__VPC_COMMAND_CENTER__ = {cc};
    function esc(s) {{
      if (s === null || s === undefined) return '';
      return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }}
    function vpcViewTab(which) {{
      if (window.__VPC_COMMAND_CENTER__) {{
        if (which === 'map' && typeof vpcCcTab === 'function') vpcCcTab('overview');
        return;
      }}
      var board = document.getElementById('vpc-engineering-board');
      var net = document.getElementById('mynetwork');
      var bb = document.getElementById('tab-btn-board');
      var bm = document.getElementById('tab-btn-map');
      if (!board || !net) return;
      if (which === 'board') {{
        board.classList.remove('hidden');
        net.classList.add('map-tab-hidden');
        bb.classList.add('active'); bm.classList.remove('active');
      }} else {{
        board.classList.add('hidden');
        net.classList.remove('map-tab-hidden');
        bm.classList.add('active'); bb.classList.remove('active');
        if (typeof network !== 'undefined' && network) {{
          try {{ network.fit({{ animation: false }}); }} catch(e) {{}}
        }}
      }}
    }}
    function trustPill(tier, score) {{
      var t = (tier || 'unknown').toLowerCase();
      var cls = 'trust-' + (t === 'verified' ? 'verified' : t);
      var label = (score !== undefined && score !== '' ? score + ' ' : '') + (tier || '?');
      return '<span class="trust-pill ' + cls + '">' + esc(label) + '</span>';
    }}
    function boardRenderDomain(domainId) {{
      var data = window.__VPC_BOARD__ || {{}};
      var dom = (data.domains || []).find(function(d) {{ return String(d.domain_id) === String(domainId); }});
      if (!dom) return;
      var pill = document.getElementById('board-health-pill');
      var h = dom.health || {{}};
      var lbl = (h.health_label || 'UNKNOWN').toUpperCase();
      pill.textContent = (h.health_score !== undefined ? h.health_score + '% ' : '') + lbl;
      pill.className = 'health-pill health-' + (lbl.indexOf('CRIT') >= 0 ? 'CRITICAL' : lbl.indexOf('WARN') >= 0 ? 'WARNING' : 'HEALTHY');
      var peersHtml = '';
      (dom.peers || []).forEach(function(p) {{
        if (p.is_scanned === false) {{
          peersHtml += '<div class="peer-unscanned-banner">⚠ Not fully scanned — vPC trust incomplete</div>';
        }}
        peersHtml += '<div class="peer-card"><h4>' + esc(p.hostname) +
          ' <span style="font-size:11px;color:#6366f1;">(' + esc(p.role) + ')</span></h4>' +
          '<div class="peer-meta"><b>Peer-Link Po:</b> ' + esc(p.peer_link_po || '—') + '<br>' +
          '<b>Peer status:</b> ' + esc(p.peer_status) + '<br>' +
          '<b>Keepalive:</b> ' + esc(p.keepalive_status) + '<br>' +
          (p.nxos_version ? '<b>NX-OS:</b> ' + esc(p.nxos_version) + '<br>' : '') +
          '<b>MGMT:</b> ' + esc(p.mgmt_ip || '—') + '</div></div>';
      }});
      document.getElementById('board-peer-strip').innerHTML = peersHtml;
      var vtbody = document.querySelector('#board-vpc-table tbody');
      vtbody.innerHTML = '';
      (dom.peers || []).forEach(function(p) {{
        (p.vpc_table || []).forEach(function(row) {{
          var members = [];
          var po = row.po || row.port_channel || '';
          var pcd = p.port_channels || {{}};
          if (pcd[po] && pcd[po].members) {{
            pcd[po].members.forEach(function(m) {{ members.push(m.intf || m); }});
          }}
          var ent = (p.member_interfaces || {{}}).entries || [];
          ent.forEach(function(e) {{
            if ((e.port_channel || '') === po && e.member_interfaces) {{
              members = members.concat(e.member_interfaces);
            }}
          }});
          var st = (row.status || '').toLowerCase();
          var tr = document.createElement('tr');
          tr.innerHTML = '<td>' + esc(p.hostname) + '</td><td>' + esc(row.vpc_id) + '</td><td>' + esc(po) +
            '</td><td class="' + (st === 'up' ? 'st-up' : 'st-down') + '">' + esc(row.status) +
            '</td><td>' + esc(row.consistency) + '</td><td>' + esc(row.active_vlans) +
            '</td><td style="font-family:monospace;font-size:11px;">' + esc(members.join(', ') || '—') + '</td>';
          vtbody.appendChild(tr);
        }});
      }});
      var dtbody = document.querySelector('#board-downstream-table tbody');
      dtbody.innerHTML = '';
      (dom.downstream_links || []).forEach(function(l) {{
        var tr = document.createElement('tr');
        tr.innerHTML = '<td>' + esc(l.switch) + '</td><td>' + esc(l.local_port) + '</td><td>' +
          esc(l.remote_host) + '</td><td>' + esc(l.remote_port) + '</td><td>' + esc(l.edge_type) + '</td><td>' +
          trustPill(l.trust_tier || l.confidence, l.trust_score) + '</td>';
        dtbody.appendChild(tr);
      }});
      var ctbody = document.querySelector('#board-trust-chains-table tbody');
      if (ctbody) {{
        ctbody.innerHTML = '';
        var chains = (dom.interface_trust_chains || []).slice();
        (dom.peers || []).forEach(function(p) {{
          (p.interface_trust_chains || []).forEach(function(c) {{
            var row = Object.assign({{}}, c);
            row.switch = p.hostname;
            chains.push(row);
          }});
        }});
        chains.forEach(function(c) {{
          var tr = document.createElement('tr');
          tr.innerHTML = '<td>' + esc(c.switch || c.hostname || '—') + '</td><td style="font-family:monospace;font-size:11px;">' +
            esc(c.chain || '—') + '</td><td>' + esc(c.trust_score) + '</td><td>' +
            trustPill(c.trust_tier, c.trust_score) + '</td><td>' +
            (c.bidirectional ? '✓ bidi' : (c.cdp_peer ? '→ ' + esc(c.cdp_peer) : '—')) + '</td><td>' +
            (c.lacp_witness ? '✓' : '—') + '</td>';
          ctbody.appendChild(tr);
        }});
        if (!chains.length) {{
          ctbody.innerHTML = '<tr><td colspan="6" style="color:#64748b;">No interface trust chains (scan NX-OS peers with vPC).</td></tr>';
        }}
      }}
      var gc = '';
      (dom.peers || []).forEach(function(p) {{
        if (p.global_consistency) {{
          gc += '=== ' + p.hostname + ' ===\\n' + p.global_consistency + '\\n\\n';
        }}
      }});
      document.getElementById('board-global-consistency').textContent = gc.trim() || 'No global consistency CLI captured.';
      var alerts = '';
      (h.consistency_alerts || []).forEach(function(a) {{ alerts += '<div style="color:#b45309;margin:4px 0;">⚠ ' + esc(a) + '</div>'; }});
      (h.peer_mismatches || []).forEach(function(a) {{ alerts += '<div style="color:#dc2626;margin:4px 0;">✗ ' + esc(a) + '</div>'; }});
      (dom.trust_alerts || []).forEach(function(a) {{ alerts += '<div style="color:#7c3aed;margin:4px 0;">◎ ' + esc(a) + '</div>'; }});
      var dc = dom.domain_completeness || {{}};
      if (dc.unscanned_members && dc.unscanned_members.length) {{
        alerts += '<div class="peer-unscanned-banner">Scan both vPC peers for verified trust: ' +
          esc(dc.unscanned_members.join(', ')) + '</div>';
      }}
      document.getElementById('board-alerts').innerHTML = alerts || '<span style="color:#16a34a;">No correlation alerts.</span>';
    }}
    function boardInit() {{
      var data = window.__VPC_BOARD__ || {{ domains: [] }};
      var sel = document.getElementById('board-domain-select');
      if (!sel) return;
      sel.innerHTML = '';
      (data.domains || []).forEach(function(d) {{
        var opt = document.createElement('option');
        opt.value = d.domain_id;
        opt.textContent = 'Domain ' + d.domain_id + ' (' + (d.members || []).join(' + ') + ')';
        sel.appendChild(opt);
      }});
      var def = data.default_domain || (data.domains[0] && data.domains[0].domain_id);
      if (def) {{ sel.value = def; boardRenderDomain(def); }}
      else if (!(data.domains || []).length) {{
        document.getElementById('board-alerts').innerHTML =
          '<div class="vpc-empty-state">No vPC domains in collected data. Run on NX-OS peers with <code>show vpc</code> success.</div>';
      }}
    }}
    {auto_boot}
    """


def build_board_payload_from_presentation(presentation):
    """Return board_sections dict for embedding."""
    return presentation.get('board_sections') if presentation else {'domains': []}
