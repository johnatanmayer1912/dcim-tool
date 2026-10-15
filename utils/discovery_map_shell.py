"""
Discovery Command Center shell (v7.0.4) — offline light theme, split device table + map.
"""
import json

from utils.standard_map_shell import embed_utilization_overlay_js
from utils.topo_map_shell import (
    load_vis_script, read_version_label, shell_css, topo_search_helpers_js,
    embed_link_inventory_render_js, layer_switch_html, script_safe_json,
)


def discovery_light_css():
    from utils.map_shell_theme import enterprise_map_css
    return enterprise_map_css() + """
    body.discovery-command-center {
      background: #f1f5f9 !important;
      color: #0f172a !important;
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      font-family: var(--nst-map-font), -apple-system, system-ui, sans-serif;
    }
    body.discovery-command-center header {
      background: #fff;
      border-bottom: 1px solid #e2e8f0;
      padding: 12px 20px;
    }
    body.discovery-command-center header h1 {
      margin: 0;
      font-size: 17px;
      color: #0f172a;
    }
    /* Light CC inherits dark topo chrome tokens — override for WCAG AA on #f1f5f9 */
    body.discovery-command-center .nst-fresh { color: #334155; }
    body.discovery-command-center .nst-stale { color: #b45309; }
    body.discovery-command-center #nst-overlay-note { color: #92400e; }
    body.discovery-command-center .nst-layer-switch button {
      background: #fff;
      color: #1e293b;
      border-color: #cbd5e1;
    }
    body.discovery-command-center .nst-layer-switch button.active {
      background: #5b21b6;
      border-color: #5b21b6;
      color: #fff;
    }
    body.discovery-command-center .nst-util-chip { color: #334155; }
  .disc-cc-tabs { display:flex; gap:8px; flex-wrap:wrap; margin:12px 16px; }
  .disc-cc-tabs button {
    padding:10px 16px; border-radius:8px; border:1px solid #cbd5e1;
    background:#fff; cursor:pointer; font-weight:600; font-size:13px; color:#334155;
  }
  .disc-cc-tabs button.active { background:#7c3aed; color:#fff; border-color:#6d28d9; }
  .disc-cc-panel { display:none; flex:1; flex-direction:column; min-height:0; }
  .disc-cc-panel.active { display:flex; }
  .disc-split-overview {
    display:grid;
    grid-template-columns: 42% 58%;
    gap:12px;
    flex:1;
    min-height:400px;
    padding:0 16px 16px 16px;
  }
  .disc-split-table {
    overflow:auto;
    max-height: calc(100vh - 200px);
    border:1px solid #e2e8f0;
    border-radius:12px;
    background:#fff;
  }
  .disc-device-table { width:100%; border-collapse:collapse; font-size:12px; }
  .disc-device-table th {
    position:sticky; top:0; background:#1e293b; color:#f8fafc;
    padding:8px; text-align:left;
  }
  .disc-device-table td { padding:7px 8px; border-bottom:1px solid #e2e8f0; cursor:pointer; }
  .disc-device-table tr:hover td { background:#f1f5f9; }
  .disc-device-table tr.disc-row-active td { background:#ede9fe; }
  .disc-split-map {
    display:flex;
    flex-direction:column;
    min-height:400px;
  }
  .disc-map-search-bar {
    display:flex; gap:8px; align-items:center; margin-bottom:6px; flex-wrap:wrap;
  }
  .disc-map-search-bar input {
    flex:1; min-width:160px; padding:8px 10px; border-radius:8px;
    border:1px solid #cbd5e1; font-size:12px;
  }
  #disc-map-search-count { font-size:11px; color:#475569; }
  #mynetwork.disc-map-pane {
    flex:1;
    min-height:380px;
    background:#e2e8f0 !important;
    border:2px solid #94a3b8;
    border-radius:12px;
  }
  .disc-legend {
    display:flex; flex-wrap:wrap; gap:10px; font-size:11px;
    padding:8px 16px; color:#475569;
  }
  .disc-legend span { padding:4px 10px; border-radius:6px; border:1px solid #e2e8f0; background:#fff; }
  #disc-summary-panel {
    padding:16px 20px;
    overflow:auto;
    max-height: calc(100vh - 160px);
  }
  .disc-incomplete-banner {
    display:none;
    margin:0 16px 8px 16px;
    padding:10px 12px;
    border:1px solid #fcd34d;
    background:#fffbeb;
    border-radius:8px;
    font-size:12px;
    color:#92400e;
  }
  .disc-incomplete-banner.visible { display:block; }
  .disc-incomplete-banner ul { margin:6px 0 0 0; padding-left:18px; }
  .disc-program-status-banner {
    margin:0 16px 8px 16px;
    padding:10px 12px;
    border:1px solid #fecaca;
    background:#fef2f2;
    border-radius:8px;
    font-size:12px;
    color:#7f1d1d;
  }
  .disc-program-status-banner.gate-pass {
    border-color:#86efac;
    background:#f0fdf4;
    color:#14532d;
  }
  .disc-program-status-banner .disc-ps-gate {
    font-weight:800;
    margin:4px 0 6px 0;
  }
  .disc-program-status-banner ul {
    margin:6px 0 0 0;
    padding-left:18px;
    color:#334155;
  }
  .disc-program-status-banner .disc-ps-note {
    margin-top:6px;
    font-size:11px;
    color:#334155;
  }
  #disc-link-inventory-host {
    flex:1;
    overflow:auto;
    margin:0 16px 16px 16px;
    background:#fff;
    border:1px solid #e2e8f0;
    border-radius:12px;
  }
  .badge-scanned { background:#dcfce7; color:#166534; padding:2px 8px; border-radius:8px; font-size:10px; font-weight:700; }
  .badge-neighbor { background:#f1f5f9; color:#475569; padding:2px 8px; border-radius:8px; font-size:10px; }
  .badge-failed { background:#fee2e2; color:#991b1b; padding:2px 8px; border-radius:8px; font-size:10px; }
  .badge-seed { background:#ede9fe; color:#5b21b6; padding:2px 8px; border-radius:8px; font-size:10px; }
  .nst-util-toggle {
    display: inline-flex; align-items: center; gap: 6px;
    color: #334155; font-size: 11px; font-weight: 600;
  }
  .nst-util-chip {
    font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 999px;
    border: 1px solid #cbd5e1; background: #fff; color: #64748b;
  }
  .nst-util-chip.replay { border-color: #1d4ed8; color: #1e40af; background: #eff6ff; }
  .nst-util-chip.live { border-color: #047857; color: #065f46; background: #ecfdf5; }
  .nst-util-chip.degraded { border-color: #b45309; color: #92400e; }
  .nst-util-chip.err { border-color: #b91c1c; color: #991b1b; background: #fef2f2; }
  .nst-util-banner {
    margin: 0 16px 8px 16px; padding: 8px 10px; border-radius: 8px;
    border: 1px solid #93c5fd; background: #eff6ff; color: #1e3a8a;
    font-size: 11px; line-height: 1.4;
  }
  .nst-util-banner[hidden], .nst-util-legend[hidden], .nst-util-unmapped[hidden] { display: none !important; }
  .nst-util-legend {
    display: flex; flex-wrap: wrap; gap: 8px; padding: 6px 16px 10px;
    font-size: 11px; color: #334155;
  }
  .nst-util-swatch {
    display: inline-block; width: 18px; height: 0; border-top-width: 3px;
    border-top-style: solid; vertical-align: middle; margin-right: 6px;
  }
  .nst-util-swatch.gray { border-top-color: #64748b; border-top-style: dashed; width: 22px; }
  .nst-util-swatch.ok { border-top-color: #22c55e; }
  .nst-util-swatch.warn { border-top-color: #eab308; }
  .nst-util-swatch.hot { border-top-color: #ef4444; border-top-width: 4px; }
  .nst-util-unmapped {
    margin: 0 16px 8px 16px; padding: 8px 12px; border: 1px solid #e2e8f0;
    border-radius: 8px; background: #fff; font-size: 11px; color: #475569;
    max-height: 140px; overflow: auto;
  }
  .nst-util-unmapped table { width: 100%; border-collapse: collapse; }
  .nst-util-unmapped td, .nst-util-unmapped th {
    padding: 3px 6px; text-align: left; border-bottom: 1px solid #e2e8f0; color: #0f172a;
  }
  .nst-util-chrome {
    display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
    margin: 0 16px 8px 16px;
  }
  """


def discovery_utilization_chrome_html():
    """Viewer chrome for the existing utilization overlay. No live SSH start."""
    return """
  <div class="nst-util-chrome" id="nst-util-chrome" role="region" aria-label="Utilization overlay controls">
    <label class="nst-util-toggle" id="nst-util-toggle-wrap">
      <input type="checkbox" id="nst-util-overlay-on" disabled
        onchange="if(typeof nstSetUtilOverlay==='function') nstSetUtilOverlay(this.checked);" />
      Utilization overlay
    </label>
    <span class="nst-util-chip" id="nst-util-mode-chip">Overlay: none</span>
    <span style="font-size:11px;color:#334155;">Viewer only — Live SSH is Standard L2. Not SNMP. Paint is not topology.</span>
  </div>
  <div class="nst-util-banner" id="nst-util-banner" hidden></div>
  <div class="nst-util-legend" id="nst-util-legend" hidden aria-label="Utilization legend">
    <span><span class="nst-util-swatch gray"></span>unsampled (gray dashed — not down)</span>
    <span><span class="nst-util-swatch ok"></span>&lt;70%</span>
    <span><span class="nst-util-swatch warn"></span>70–90%</span>
    <span><span class="nst-util-swatch hot"></span>&gt;=90%</span>
  </div>
"""


def discovery_utilization_unmapped_html():
    return """
  <div class="nst-util-unmapped" id="nst-util-unmapped" hidden>
    <div style="font-weight:700;margin-bottom:4px;">Unmapped interfaces (not drawn)</div>
    <table>
      <thead><tr><th>Host</th><th>ifName</th><th>Normalized</th><th>Reason</th></tr></thead>
      <tbody id="nst-util-unmapped-body"></tbody>
    </table>
  </div>
"""


def discovery_command_center_body(link_inventory_html_fragment):
    return f"""
  <div class="disc-legend" role="region" aria-label="Discovery map legend">
    <span><b style="color:#3b82f6;">■</b> Scanned</span>
    <span><b style="color:#94a3b8;">■</b> Neighbor only</span>
    <span>CDP edges indigo · LLDP teal</span>
    <span>Hops increase downward on map</span>
    <span>Overlay layer = NVE/EVPN CLI peers only (not cables).</span>
    <span>Incomplete observations = diagnostics only (not map links).</span>
    <span>Program Status / release gate is not topology.</span>
  </div>
  {discovery_utilization_chrome_html()}
  <div id="disc-program-status-banner" class="disc-program-status-banner" role="region" aria-label="Discovery program status"></div>
  <div id="disc-incomplete-banner" class="disc-incomplete-banner" aria-live="polite"></div>
  {discovery_utilization_unmapped_html()}
  {layer_switch_html('l2')}
  <div class="disc-cc-tabs" id="disc-cc-tabs">
    <button type="button" class="active" id="disc-tab-overview" onclick="discCcTab('overview')">1 Overview</button>
    <button type="button" id="disc-tab-links" onclick="discCcTab('links')">2 Link Inventory</button>
    <button type="button" id="disc-tab-summary" onclick="discCcTab('summary')">3 Summary</button>
    <button type="button" onclick="window.print()">Print</button>
  </div>
  <div id="disc-panel-overview" class="disc-cc-panel active" role="region" aria-label="Discovery overview">
    <div class="disc-split-overview">
      <div class="disc-split-table">
        <table class="disc-device-table" id="disc-device-table">
          <thead><tr><th>Device</th><th>IP</th><th>Hop</th><th>State</th></tr></thead>
          <tbody id="disc-device-tbody"></tbody>
        </table>
      </div>
      <div class="disc-split-map">
        <div class="disc-map-search-bar">
          <label for="disc-map-search-input" style="font-size:12px;font-weight:600;color:#475569;">Search map</label>
          <input type="text" id="disc-map-search-input" placeholder="hostname, IP, platform…"
            oninput="discApplyMapSearch(this.value)" />
          <span id="disc-map-search-count"></span>
        </div>
        <div id="mynetwork" class="disc-map-pane"></div>
      </div>
    </div>
  </div>
  <div id="disc-panel-links" class="disc-cc-panel">
    <div id="disc-link-inventory-host">{link_inventory_html_fragment}</div>
  </div>
  <div id="disc-panel-summary" class="disc-cc-panel">
    <div id="disc-summary-panel"><p>Loading summary…</p></div>
  </div>
"""


def discovery_shell_js(discovery_json: str, link_rows_json: str):
    return f"""
    {embed_link_inventory_render_js()}
    if (typeof nstMarkScale === 'function') nstMarkScale(nodes.length);
    window.__DISCOVERY__ = {discovery_json};
    window.__TOPO_LINKS__ = {link_rows_json};
    window.NST_OVERLAY_COLLECTED = !!(window.__DISCOVERY__ && window.__DISCOVERY__.overlay_collected);

    function discCcTab(which) {{
      ['overview','links','summary'].forEach(function(t) {{
        var p = document.getElementById('disc-panel-' + t);
        var b = document.getElementById('disc-tab-' + t);
        if (p) p.classList.toggle('active', t === which);
        if (b) b.classList.toggle('active', t === which);
      }});
      if (which === 'overview') setTimeout(discBootMap, 40);
      if (which === 'links' && typeof renderLinkTable === 'function') renderLinkTable();
      if (which === 'summary') discRenderSummary();
    }}

    function discStateBadge(st) {{
      st = (st || 'neighbor_only').toLowerCase();
      if (st === 'scanned') return '<span class="badge-scanned">Scanned</span>';
      if (st === 'seed') return '<span class="badge-seed">Seed</span>';
      if (st === 'failed') return '<span class="badge-failed">Failed</span>';
      return '<span class="badge-neighbor">Neighbor</span>';
    }}

    function discPortLabel(raw, display) {{
      var d = (display || '').trim();
      if (d) return d;
      var r = (raw || '').trim();
      return r || '(unobserved)';
    }}

    function discRenderProgramStatus() {{
      var el = document.getElementById('disc-program-status-banner');
      if (!el) return;
      var ps = (window.__DISCOVERY__ || {{}}).program_status;
      if (!ps || typeof ps !== 'object') {{
        el.innerHTML = '<div class="disc-ps-gate">Release gate: unknown — do not claim enterprise ready.</div>';
        return;
      }}
      var ready = ps.readiness || {{}};
      var gate = String(ready.release_gate || 'BLOCKED');
      var hard = ready.hard_stop === true;
      if (gate === 'PASS' && !hard) {{
        el.className = 'disc-program-status-banner gate-pass';
      }} else {{
        el.className = 'disc-program-status-banner';
      }}
      var gateLine = (gate === 'BLOCKED' || hard)
        ? 'Release gate: BLOCKED (HARD STOP — not advisory). Enterprise ready: NO. Live truncated CDP/LLDP: NOT VALIDATED.'
        : (gate === 'PASS'
          ? 'Release gate: PASS (only after retained live evidence).'
          : ('Release gate: ' + gate + ' (treat as hard stop).'));
      var cats = ps.categories || [];
      var list = cats.map(function(c) {{
        return '<li><strong>' + topoEsc(c.label || c.id) + ':</strong> ' +
          topoEsc(c.summary || '') + '</li>';
      }}).join('');
      var note = (ps.honesty && ps.honesty.note) ? ps.honesty.note : '';
      var surfaces = ps.surfaces || [];
      var surfHtml = surfaces.length
        ? ('<div class="disc-ps-surfaces" style="margin-top:6px;font-size:11px;color:#475569;">'
          + '<strong>Surfaces sharing this Program Status:</strong> '
          + surfaces.map(function(s) {{
              return topoEsc(s.label || s.id);
            }}).join(' · ')
          + '</div>')
        : '';
      var cross = ps.cross_surface_note
        ? ('<div class="disc-ps-note">' + topoEsc(ps.cross_surface_note) + '</div>')
        : '';
      var jumps = ps.related_surface_jumps || [];
      var jumpHtml = jumps.length
        ? ('<div class="disc-ps-jumps" style="margin-top:8px;font-size:11px;">'
          + '<strong>Related surfaces (operator console):</strong> '
          + jumps.map(function(j) {{
              var h = (j.hash || 'nst-discovery');
              return '<a href="/#' + topoEsc(h) + '" target="_blank" rel="noopener">'
                + topoEsc(j.label || j.id) + '</a>';
            }}).join(' · ')
          + ' <span style="color:#334155;">(same Program Status; not the same topology)</span></div>')
        : '';
      el.innerHTML =
        '<div style="font-weight:700;">Discovery Program Status</div>' +
        '<div style="margin-top:4px;color:#334155;">' + topoEsc(ready.operator_summary || '') + '</div>' +
        '<div class="disc-ps-gate">' + topoEsc(gateLine) + '</div>' +
        (list ? '<ul>' + list + '</ul>' : '') +
        surfHtml +
        cross +
        jumpHtml +
        '<div class="disc-ps-note">' + topoEsc(note) +
        ' Program Status is not a topology layer and does not invent links. '
        + 'This shell is the Discovery Command Center — not the inventory Standard L2 map.</div>';
    }}

    function discCollectIncompleteRows() {{
      var d = window.__DISCOVERY__ || {{}};
      var rows = [];
      (d.devices || []).forEach(function(dev) {{
        var scanned = topoEsc(dev.id || dev.hostname || '—');
        (dev.incomplete_observations || []).forEach(function(o) {{
          rows.push({{ scanned: scanned, obs: o || {{}} }});
        }});
      }});
      return rows;
    }}

    function discRenderIncompleteBanner() {{
      var banner = document.getElementById('disc-incomplete-banner');
      if (!banner) return;
      var rows = discCollectIncompleteRows();
      var total = Number((window.__DISCOVERY__ || {{}}).incomplete_observation_count || 0) || rows.length;
      if (!total) {{
        banner.className = 'disc-incomplete-banner';
        banner.innerHTML = '';
        return;
      }}
      banner.className = 'disc-incomplete-banner visible';
      var items = rows.slice(0, 8).map(function(row) {{
        var o = row.obs;
        var peer = topoEsc(o.hostname || '(unobserved peer)');
        var proto = topoEsc(o.protocol || '—');
        var lp = topoEsc(discPortLabel(o.local_port, o.local_port_display));
        var rp = topoEsc(discPortLabel(o.remote_port, o.remote_port_display));
        return '<li><strong>' + row.scanned + '</strong> → ' + peer +
          ' · ' + proto + ' · local ' + lp + ' · remote ' + rp + '</li>';
      }}).join('');
      banner.innerHTML =
        '<div style="font-weight:700;margin-bottom:4px;">Incomplete observations (not map links)</div>' +
        '<div>' + total + ' incomplete observation(s) retained for diagnostics. ' +
        'These are not CDP/LLDP edges and are not drawn on the map.</div>' +
        (items ? '<ul>' + items + (rows.length > 8 ? '<li>…</li>' : '') + '</ul>' : '');
    }}

    function discRenderDeviceTable() {{
      var tb = document.getElementById('disc-device-tbody');
      if (!tb) return;
      var devices = window.__DISCOVERY__.devices || [];
      tb.innerHTML = devices.map(function(d) {{
        var nInc = Number(d.incomplete_observation_count || 0);
        var note = nInc > 0
          ? (' <span class="badge-failed" title="Incomplete observations — not links">' +
             nInc + ' incomplete</span>')
          : '';
        return '<tr data-node-id="'+ topoEsc(d.id||d.hostname||'') +'">' +
          '<td><b>'+ topoEsc(d.id||d.hostname||'') +'</b>' + note + '</td>' +
          '<td style="font-family:monospace;font-size:11px;">'+ topoEsc(d.ip||d.host||'—') +'</td>' +
          '<td>H'+ (d.depth !== undefined ? d.depth : '—') +'</td>' +
          '<td>'+ discStateBadge(d.scan_state) +'</td></tr>';
      }}).join('');
      tb.querySelectorAll('tr').forEach(function(tr) {{
        tr.addEventListener('click', function() {{
          tb.querySelectorAll('tr').forEach(function(r) {{ r.classList.remove('disc-row-active'); }});
          tr.classList.add('disc-row-active');
          var nid = tr.getAttribute('data-node-id');
          var si = document.getElementById('disc-map-search-input');
          if (si && nid) {{ si.value = nid; discApplyMapSearch(nid); }}
          else if (window.discNetwork && nid) {{
            try {{ window.discNetwork.selectNodes([nid]); window.discNetwork.focus(nid, {{scale:1.2, animation:false}}); }} catch(e) {{}}
          }}
        }});
      }});
    }}

    function topoNodeHaystack(n) {{
      return [n.id,n.label,n.ip,n.platform,n.title,(n.scan_state||'')].join(' ').toLowerCase();
    }}
    function topoEdgeHaystack(e) {{
      return [e.label,e.from,e.to,e.f_port,e.t_port,e.protocol,e.title,e.type].join(' ').toLowerCase();
    }}
    {topo_search_helpers_js()}
    function discApplyMapSearch(q) {{
      q = (q||'').trim().toLowerCase();
      if (typeof nodes === 'undefined' || typeof edges === 'undefined') return;
      var allN = nodes.getIds().slice();
      var allE = edges.getIds().slice();
      var focus = topoApplyNodeEdgeFocus(q, allN, allE);
      var tb = document.getElementById('disc-device-tbody');
      var matchCount = 0;
      if (tb) {{
        tb.querySelectorAll('tr').forEach(function(tr) {{
          var nid = (tr.getAttribute('data-node-id')||'').toLowerCase();
          var ok = !q || nid.indexOf(q) >= 0 || (focus.primary[nid] || focus.hop[nid]);
          tr.style.opacity = ok ? '1' : '0.35';
          if (focus.primary[nid]) tr.classList.add('disc-row-active');
          else tr.classList.remove('disc-row-active');
          if (ok && q) matchCount++;
        }});
      }}
      var cnt = document.getElementById('disc-map-search-count');
      if (cnt) cnt.textContent = q ? (matchCount + ' device(s)') : '';
    }}

    function discRenderSummary() {{
      var el = document.getElementById('disc-summary-panel');
      if (!el) return;
      var d = window.__DISCOVERY__;
      var devs = d.devices || [];
      var scanned = devs.filter(function(x) {{ return x.scan_state === 'scanned'; }}).length;
      var neigh = devs.filter(function(x) {{ return x.scan_state === 'neighbor_only'; }}).length;
      var links = d.links || [];
      var rows = discCollectIncompleteRows();
      var inc = Number(d.incomplete_observation_count || 0) || rows.length;
      var html = '<h3 style="margin-top:0;">Run summary</h3>' +
        '<p><b>'+ devs.length +'</b> devices · <b>'+ links.length +'</b> links · ' +
        '<b>'+ scanned +'</b> scanned · <b>'+ neigh +'</b> neighbor-only</p>';
      var ps = d.program_status;
      if (ps && ps.readiness) {{
        var rg = String(ps.readiness.release_gate || 'BLOCKED');
        var gateTxt = (rg === 'BLOCKED' || ps.readiness.hard_stop)
          ? 'BLOCKED (HARD STOP — not advisory)'
          : rg;
        html += '<div class="disc-program-status-banner" style="margin:12px 0;">' +
          '<div style="font-weight:700;">Discovery Program Status</div>' +
          '<div class="disc-ps-gate">Release gate: ' + topoEsc(gateTxt) +
          '. Enterprise ready: NO unless release_gate is PASS.</div>' +
          '<ul>' + (ps.categories || []).map(function(c) {{
            return '<li><strong>' + topoEsc(c.label || c.id) + ':</strong> ' +
              topoEsc(c.summary || '') + '</li>';
          }}).join('') + '</ul>' +
          '<div class="disc-ps-note">' +
          topoEsc((ps.honesty && ps.honesty.note) || '') +
          ' Not a topology layer.</div></div>';
      }}
      if (inc > 0) {{
        html += '<div class="disc-incomplete-banner visible" style="margin:12px 0;">' +
          '<div style="font-weight:700;">Incomplete observations (not map links)</div>' +
          '<p style="margin:6px 0 0 0;"><b>'+ inc +'</b> incomplete observation(s) — diagnostics only; ' +
          'not drawn as edges and not topology truth.</p><ul>' +
          rows.map(function(row) {{
            var o = row.obs;
            return '<li><strong>' + row.scanned + '</strong> → ' +
              topoEsc(o.hostname || '(unobserved peer)') + ' · ' +
              topoEsc(o.protocol || '—') + ' · local ' +
              topoEsc(discPortLabel(o.local_port, o.local_port_display)) +
              ' · remote ' +
              topoEsc(discPortLabel(o.remote_port, o.remote_port_display)) +
              (o.parse_warning ? (' · <em>' + topoEsc(o.parse_warning) + '</em>') : '') +
              '</li>';
          }}).join('') + '</ul></div>';
      }}
      html += '<p style="font-size:12px;color:#64748b;">Use Overview for map + table; Link inventory for sortable L2 rows. ' +
        'Incomplete observations never appear in Link Inventory as cables. ' +
        'Program Status / release gate is not topology truth.</p>';
      el.innerHTML = html;
    }}

    function discBootMap(attempt) {{
      attempt = attempt || 0;
      var c = document.getElementById('mynetwork');
      if (!c || typeof vis === 'undefined') return;
      if (window.discNetwork) {{
        try {{ window.discNetwork.redraw(); window.discNetwork.fit({{animation:false}}); }} catch(e) {{}}
        return;
      }}
      if (c.offsetHeight < 40 && attempt < 20) {{
        setTimeout(function() {{ discBootMap(attempt + 1); }}, 80);
        return;
      }}
      window.discNetwork = new vis.Network(c, {{nodes: nodes, edges: edges}}, {{
        physics: {{ enabled: false }},
        interaction: {{ hideEdgesOnDrag: true, zoomView: true, dragView: true, selectable: true }},
        nodes: {{ font: {{ size: 12, face: 'system-ui' }} }},
        edges: {{ font: {{ size: 9, align: 'middle' }} }}
      }});
      try {{ window.discNetwork.fit({{ animation: false }}); }} catch(e) {{}}
      window.discNetwork.on('selectEdge', function(params) {{
        if (window._nstSyncSelecting) return;
        if (!params.edges.length) return;
        nstWhyThisLink(edges.get(params.edges[0]));
      }});
      window.discNetwork.on('selectNode', function(params) {{
        var el = document.getElementById('nst-why-link');
        if (el && params.nodes.length) el.textContent = 'Selected ' + params.nodes[0] + ' — Blast radius for 1-hop impact.';
      }});
    }}

  function renderLinkTable() {{
    var tb = document.getElementById('link-tbody');
    if (!tb) return;
    tb.innerHTML = '';
    (window.__TOPO_LINKS__ || []).forEach(function(r, idx) {{
      var tr = document.createElement('tr');
      tr.dataset.search = [r.from,r.local_port,r.to,r.remote_port,r.protocol].join(' ').toLowerCase();
      if (r.relation_key) tr.setAttribute('data-relation-key', r.relation_key);
      tr.innerHTML = (typeof topoRenderLinkRow === 'function') ? topoRenderLinkRow(r, idx) :
        '<td>'+topoEsc(r.from)+'</td><td>'+topoEsc(r.local_port)+'</td><td>'+topoEsc(r.to)+
        '</td><td>'+topoEsc(r.remote_port)+'</td><td>'+topoEsc(r.protocol||'')+'</td>'+
        '<td>—</td><td>—</td><td>—</td><td><button type="button" class="nst-ev-inspect-btn" aria-label="Inspect unavailable" disabled>Inspect</button></td>';
      tb.appendChild(tr);
    }});
    var si = document.getElementById('topo-search-input');
    if (si && si.value) topoApplySearch(si.value);
  }}
  function topoApplySearch(q) {{
    q = (q||'').trim().toLowerCase();
    var trs = document.querySelectorAll('#link-tbody tr');
    var vis = 0;
    trs.forEach(function(tr) {{
      var ok = !q || (tr.dataset.search||'').indexOf(q)>=0;
      tr.style.display = ok ? '' : 'none';
      if (ok) vis++;
    }});
    var cnt = document.getElementById('topo-search-count');
    if (cnt) cnt.textContent = q ? (vis + ' links') : '';
  }}
  renderLinkTable();

    function discCommandCenterInit() {{
      discRenderProgramStatus();
      discRenderDeviceTable();
      discRenderIncompleteBanner();
      discRenderSummary();
      discBootMap(0);
      if (typeof nstSyncUtilChrome === 'function') nstSyncUtilChrome();
      if (typeof nstRenderUtilUnmapped === 'function') nstRenderUtilUnmapped();
      var discTs = (window.__DISCOVERY__ && (window.__DISCOVERY__.collected_at || window.__DISCOVERY__.generated_at)) || '';
      var discBasis = (window.__DISCOVERY__ && window.__DISCOVERY__.freshness_basis) || '';
      if (discTs) {{
        nstStartFreshnessClock(discTs);
        if (discBasis === 'unknown' || !window.__DISCOVERY__.collected_at) {{
          var el = document.getElementById('nst-freshness');
          if (el && discBasis === 'unknown') {{
            el.textContent = 'Freshness: UNKNOWN — no edge observation timestamp (render time is not crawl truth)';
            el.className = 'nst-stale';
          }}
        }}
      }}
    }}
    if (document.readyState === 'loading') {{
      document.addEventListener('DOMContentLoaded', discCommandCenterInit);
    }} else {{
      discCommandCenterInit();
    }}
    """


def render_discovery_command_center_page(
    filepath,
    title,
    nodes_json,
    edges_json,
    link_rows,
    discovery_meta,
    accent='#7c3aed',
    utilization_payload=None,
):
    """Write standalone Discovery Command Center HTML."""
    version_label = read_version_label()
    vis_script = load_vis_script()
    ts = discovery_meta.get('collected_at') or discovery_meta.get('generated_at', '')
    subtitle = discovery_meta.get('subtitle', f'{len(nodes_json)} devices · {len(edges_json)} links')
    discovery_json = script_safe_json(discovery_meta)
    link_rows_json = script_safe_json(link_rows)
    if utilization_payload is None:
        utilization_payload = {
            'ok': False,
            'available': False,
            'error': 'No utilization document loaded',
            'host': 'discovery',
            'live_controls': False,
            'bindings': {},
            'banner': (
                'Utilization paints existing L2 links only. It is not topology. '
                'Gray dashed = no sample — not down. Overlay never creates cables. '
                'Discovery is a viewer. EVPN, overlay, and incomplete observations '
                'are not cables and are never painted as utilization. '
                'Paint is not topology. Release gate is unchanged.'
            ),
        }
    util_js = embed_utilization_overlay_js(script_safe_json(utilization_payload))
    link_frag = """
    <div class="topo-search-bar" style="background:#f8fafc;border-bottom:1px solid #e2e8f0;">
      <label for="topo-search-input" style="font-size:12px;font-weight:600;color:#475569;">Filter links</label>
      <input type="text" id="topo-search-input" placeholder="hostname, IP, port, protocol…"
        oninput="typeof topoApplySearch==='function'&&topoApplySearch(this.value)" />
      <span id="topo-search-count" style="font-size:11px;color:#475569;"></span>
    </div>
    <table class="topo-inv-table" style="width:100%;font-size:12px;">
      <thead><tr>
        <th onclick="topoSortTable&&topoSortTable(0)">From</th>
        <th onclick="topoSortTable&&topoSortTable(1)">Local</th>
        <th onclick="topoSortTable&&topoSortTable(2)">To</th>
        <th onclick="topoSortTable&&topoSortTable(3)">Remote</th>
        <th onclick="topoSortTable&&topoSortTable(4)">Type</th>
        <th onclick="topoSortTable&&topoSortTable(5)">VLAN</th>
        <th onclick="topoSortTable&&topoSortTable(6)">Trust</th>
        <th onclick="topoSortTable&&topoSortTable(7)">Evidence</th>
        <th>Inspect</th>
      </tr></thead>
      <tbody id="link-tbody"></tbody>
    </table>
    """
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  {vis_script}
  <style>
    {shell_css(accent)}
    {discovery_light_css()}
  </style>
</head>
<body class="discovery-command-center">
  <header>
    <h1>{title} <span style="font-size:12px;color:#475569;">{version_label}</span></h1>
    <div style="font-size:12px;color:#475569;margin-top:4px;">{subtitle} · {ts}</div>
  </header>
  <main class="disc-cc-main">
  {discovery_command_center_body(link_frag)}
  </main>
  <script type="text/javascript">
    var nodes = new vis.DataSet({script_safe_json(nodes_json)});
    var edges = new vis.DataSet({script_safe_json(edges_json)});
    window.nodes = nodes;
    window.edges = edges;
    {discovery_shell_js(discovery_json, link_rows_json)}
    {util_js}
  </script>
</body>
</html>"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
