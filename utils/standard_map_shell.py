"""
Standard L2 Map — NOC/NetEng split-pane shell (v7.3.2).

Map always visible alongside connection index. Map styles: Tier (default),
Radial, Focus (1–2 hop), Schematic. No matrix view.
Redesigned v7.3.2: modern dark enterprise theme matching L3 map aesthetic.
"""
import json


def standard_map_shell_css():
    from utils.map_shell_theme import enterprise_map_css
    return enterprise_map_css() + """
    /* ── Standard L2 Map — v7.4.22 enterprise redesign ─────────────── */
    :root {
      --bg0: #060d1a;
      --bg1: #0f172a;
      --bg2: #1e293b;
      --bg3: #334155;
      --bg4: #475569;
      --tx1: #f1f5f9;
      --tx2: #94a3b8;
      --tx3: #64748b;
      --bdr: #1e293b;
      --acc: #00c2d7;
      --acc2: #14b8a6;
      --grn: #10b981;
      --ora: #f59e0b;
      --red: #ef4444;
      --pur: #6366f1;
      --shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body.nst-standard-map {
      display: flex !important;
      flex-direction: column !important;
      height: 100vh !important;
      overflow: hidden !important;
      background: var(--bg0) !important;
      color: var(--tx1) !important;
      font-family: var(--nst-map-font), -apple-system, system-ui, sans-serif !important;
      padding: 0 !important;
    }

    /* ── Top chrome ─────────────────────────────────────────────────── */
    .nst-top-chrome {
      flex-shrink: 0;
      background: var(--bg1);
      border-bottom: 1px solid var(--bdr);
    }
    .nst-top-row {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 16px;
      border-bottom: 1px solid var(--bdr);
    }
    .nst-top-row .nst-brand-icon {
      width: 32px; height: 32px;
      background: linear-gradient(145deg, #00c2d7 0%, #14b8a6 100%);
      border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
      font-size: 11px; font-weight: 700; color: #fff; letter-spacing: 0.04em; flex-shrink: 0;
    }
    .nst-top-row h1 {
      font-size: 15px; font-weight: 700; color: var(--tx1);
      letter-spacing: -0.01em; margin: 0;
    }
    .nst-ver {
      font-size: 11px; color: var(--tx3); font-weight: 400; margin-left: 6px;
    }
    .nst-top-stats {
      margin-left: auto;
      display: flex; gap: 14px; align-items: center;
    }
    .nst-hstat { text-align: center; }
    .nst-hstat-val { font-size: 16px; font-weight: 700; color: #06b6d4; line-height: 1; }
    .nst-hstat-lbl { font-size: 10px; color: var(--tx3); margin-top: 1px; }
    .nst-vsep { width: 1px; height: 28px; background: var(--bdr); }

    /* ── Toolbar ──────────────────────────────────────────────────────── */
    .nst-toolbar-row {
      display: flex; flex-wrap: wrap; gap: 6px; align-items: center;
      padding: 7px 14px;
      background: var(--bg1);
      border-bottom: 1px solid var(--bdr);
    }
    .nst-search-input {
      background: var(--bg2); border: 1px solid var(--bg3); color: var(--tx1);
      padding: 5px 10px; border-radius: 6px; font-size: 12px;
      min-width: 180px; max-width: 340px; flex: 1;
    }
    .nst-search-input:focus { outline: none; border-color: var(--acc); }
    .nst-search-input::placeholder { color: var(--tx3); }
    .nst-btn {
      background: var(--bg2); border: 1px solid var(--bg3); color: var(--tx2);
      padding: 5px 11px; border-radius: 6px; font-size: 11px; font-weight: 600;
      cursor: pointer; transition: all 0.15s; white-space: nowrap;
    }
    .nst-btn:hover { border-color: var(--acc); color: var(--tx1); }
    .nst-btn.active { background: rgba(59,130,246,0.15); border-color: var(--acc); color: var(--acc); }
    .nst-btn[disabled] { opacity: 0.4; cursor: not-allowed; }
    .nst-util-toggle {
      display: inline-flex; align-items: center; gap: 6px;
      color: var(--tx2); font-size: 11px; font-weight: 600; cursor: pointer;
    }
    .nst-util-chip {
      font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 4px;
      border: 1px solid var(--bg3); background: var(--bg2); color: var(--tx3);
    }
    .nst-util-chip.replay { border-color: #1d4ed8; color: #93c5fd; background: #0b1f3a; }
    .nst-util-chip.live { border-color: #047857; color: #6ee7b7; background: #052e16; }
    .nst-util-chip.degraded { border-color: #b45309; color: #fde68a; }
    .nst-util-chip.err { border-color: #b91c1c; color: #fecaca; }

    /* ── Legend row ───────────────────────────────────────────────────── */
    .nst-legend-row {
      display: flex; flex-wrap: wrap; gap: 5px; align-items: center;
      padding: 6px 14px; background: var(--bg0);
      border-bottom: 1px solid var(--bdr);
    }
    .nst-legend-pill {
      display: inline-flex; align-items: center; gap: 5px;
      padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: 500;
      color: var(--tx2); background: var(--bg2); border: 1px solid var(--bdr);
    }
    .nst-legend-swatch { width: 8px; height: 8px; border-radius: 2px; flex-shrink: 0; }

    /* ── Map style bar ────────────────────────────────────────────────── */
    .nst-map-style-bar {
      display: flex; flex-wrap: wrap; gap: 4px; align-items: center;
      padding: 6px 10px;
      background: var(--bg1); border-bottom: 1px solid var(--bdr);
      flex-shrink: 0;
    }
    .nst-map-style-bar label { color: var(--tx3); font-size: 10px; font-weight: 600; margin-right: 2px; text-transform: uppercase; letter-spacing: 0.06em; }
    .nst-map-style-btn {
      padding: 4px 10px; border-radius: 5px; border: 1px solid var(--bg3);
      background: var(--bg2); color: var(--tx3); cursor: pointer;
      font-size: 11px; font-weight: 600; transition: all 0.15s;
    }
    .nst-map-style-btn.active { border-color: var(--acc); color: var(--acc); background: rgba(59,130,246,0.12); }
    .nst-map-style-btn:hover { border-color: var(--acc); color: var(--tx1); }
    .nst-focus-controls { display: flex; gap: 5px; align-items: center; margin-left: auto; flex-wrap: wrap; }
    .nst-focus-controls select {
      background: var(--bg2); border: 1px solid var(--bg3); color: var(--tx1);
      padding: 3px 7px; border-radius: 5px; font-size: 11px; max-width: 160px;
    }
    .nst-focus-controls button {
      padding: 3px 7px; border-radius: 5px; border: 1px solid var(--bg3);
      background: var(--bg2); color: var(--tx3); cursor: pointer; font-size: 10px;
    }
    .nst-focus-controls button.on { border-color: var(--ora); color: var(--ora); }

    /* ── Main layout ──────────────────────────────────────────────────── */
    .nst-standard-split {
      display: flex; flex: 1 1 0%; min-height: 0; overflow: hidden;
    }
    .nst-map-col {
      flex: 1 1 0%; display: flex; flex-direction: column; min-height: 0; overflow: hidden;
    }
    body.nst-standard-map #mynetwork,
    body.nst-standard-map #mynetwork.nst-map-main {
      flex: 1 1 auto; width: 100% !important; min-height: 0;
      height: 100% !important; background: var(--bg0) !important;
      border: none !important; border-radius: 0 !important; position: relative !important;
    }
    #network-fallback {
      flex: 1; display: flex; flex-direction: column;
      justify-content: center; align-items: center;
      background: var(--bg0); color: var(--tx3);
      font-size: 14px; gap: 8px;
    }

    /* ── Connection panel ─────────────────────────────────────────────── */
    .nst-conn-panel {
      width: 320px; min-width: 240px; max-width: 400px;
      flex-shrink: 0; display: flex; flex-direction: column;
      background: var(--bg1); border-left: 1px solid var(--bdr);
      overflow: hidden;
    }
    .nst-briefing {
      padding: 8px 12px; border-bottom: 1px solid var(--bdr);
      background: var(--bg2); flex-shrink: 0;
    }
    .nst-briefing-title {
      font-size: 11px; font-weight: 700; color: var(--tx2);
      text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px;
    }
    .nst-kpis { display: flex; flex-wrap: wrap; gap: 4px; }
    .nst-kpi {
      background: var(--bg1); border: 1px solid var(--bdr);
      border-radius: 4px; padding: 3px 7px;
      font-size: 10px; color: var(--tx3);
    }
    .nst-kpi b { color: var(--acc); font-size: 12px; }
    .nst-kpi.warn b { color: var(--ora); }
    .nst-kpi.bad b { color: var(--red); }
    .nst-conn-search {
      padding: 7px 10px; border-bottom: 1px solid var(--bdr); flex-shrink: 0;
    }
    .nst-conn-search input {
      width: 100%; padding: 5px 9px; border-radius: 5px;
      border: 1px solid var(--bg3); background: var(--bg0); color: var(--tx1);
      font-size: 11px;
    }
    .nst-conn-search input:focus { outline: none; border-color: var(--acc); }
    .nst-conn-table-wrap {
      flex: 1 1 auto; overflow: auto; min-height: 100px;
    }
    .nst-conn-table {
      width: 100%; border-collapse: collapse; font-size: 10px;
    }
    .nst-conn-table th {
      text-align: left; padding: 5px 7px;
      background: var(--bg2); color: var(--tx3);
      font-size: 9px; text-transform: uppercase; letter-spacing: 0.04em;
      position: sticky; top: 0; cursor: pointer; z-index: 1;
      border-bottom: 1px solid var(--bdr);
    }
    .nst-conn-table th:hover { color: var(--tx1); }
    .nst-conn-table td {
      padding: 4px 7px; border-bottom: 1px solid rgba(30,41,59,0.6);
      color: var(--tx2);
    }
    .nst-conn-table tr { cursor: pointer; }
    .nst-conn-table tr:hover td { background: rgba(59,130,246,0.07); }
    .nst-conn-table tr.nst-row-sel td { background: rgba(59,130,246,0.15); }
    .nst-conn-table tr.nst-peer-row td { border-left: 2px solid var(--pur); }
    .nst-conn-table .port { font-family: Consolas, monospace; color: #79c0ff; font-size: 9px; }
    .nst-link-detail {
      padding: 9px 11px; border-top: 1px solid var(--bdr);
      background: var(--bg2); font-size: 10px; color: var(--tx2);
      max-height: 120px; overflow: auto; flex-shrink: 0; line-height: 1.5;
    }
    .nst-link-detail strong { color: var(--tx1); display: block; margin-bottom: 3px; font-size: 11px; }

    /* ── Link type badges ─────────────────────────────────────────────── */
    .nst-type-badge {
      display: inline-block; font-size: 8px; padding: 1px 5px;
      border-radius: 3px; font-weight: 700; text-transform: uppercase;
    }
    .nst-type-vpc-peer { background: #7c3aed; color: #fff; }
    .nst-type-po { background: #059669; color: #fff; }
    .nst-type-vpc { background: #b45309; color: #fff; }
    .nst-type-std { background: #1d4ed8; color: #fff; }
    .nst-type-warn { background: #b91c1c; color: #fff; }

    /* ── Util overlay chrome ──────────────────────────────────────────── */
    .nst-util-banner {
      margin: 0; padding: 7px 14px;
      border-bottom: 1px solid #1d4ed8; background: #0b1f3a; color: #bfdbfe;
      font-size: 11px; line-height: 1.4;
    }
    .nst-util-banner[hidden], .nst-util-legend[hidden], .nst-util-unmapped[hidden] { display: none !important; }
    .nst-util-legend {
      display: flex; flex-wrap: wrap; gap: 8px; padding: 5px 14px;
      background: var(--bg0); font-size: 11px; color: var(--tx2);
      border-bottom: 1px solid var(--bdr);
    }
    .nst-util-swatch {
      display: inline-block; width: 18px; height: 0; border-top-width: 3px;
      border-top-style: solid; vertical-align: middle; margin-right: 5px;
    }
    .nst-util-swatch.gray { border-top-color: #475569; border-top-style: dashed; width: 22px; }
    .nst-util-swatch.ok { border-top-color: #10b981; }
    .nst-util-swatch.warn { border-top-color: #f59e0b; }
    .nst-util-swatch.hot { border-top-color: #ef4444; border-top-width: 4px; }
    .nst-util-unmapped {
      padding: 7px 11px; border-top: 1px solid var(--bdr); background: var(--bg1);
      font-size: 10px; color: var(--tx3); max-height: 130px; overflow: auto; flex-shrink: 0;
    }
    .nst-util-unmapped table { width: 100%; border-collapse: collapse; }
    .nst-util-unmapped td, .nst-util-unmapped th {
      padding: 3px 5px; text-align: left; border-bottom: 1px solid var(--bdr); color: var(--tx2);
    }

    /* ── Program status banner ────────────────────────────────────────── */
    .nst-program-status-banner {
      margin: 0; padding: 0 14px 8px;
      border-bottom: 1px solid var(--bdr); background: var(--bg1);
      font-size: 11px; color: var(--tx2); line-height: 1.45;
    }
    .nst-program-status-banner > summary {
      cursor: pointer; list-style: none; padding: 7px 0 2px;
      font-weight: 650; color: var(--tx3); font-size: 11px;
    }
    .nst-program-status-banner > summary::-webkit-details-marker { display: none; }
    .nst-program-status-banner[open] > summary { color: var(--acc); }
    .nst-program-status-banner .nst-ps-identity { color: #93c5fd; font-size: 10px; margin: 4px 0; }
    .nst-program-status-banner .nst-ps-gate { font-weight: 650; color: #fde68a; margin: 3px 0; }
    .nst-program-status-banner ul { margin: 4px 0 0 0; padding-left: 16px; color: var(--tx2); font-size: 10px; }
    .nst-program-status-banner .nst-ps-note { margin-top: 4px; font-size: 10px; color: var(--tx3); }

    /* ── Legacy compat: hide old header fragments ─────────────────────── */
    body.nst-standard-map > .header,
    body.nst-standard-map > .topo-toolbar,
    body.nst-standard-map > .legend,
    body.nst-standard-map #side-panel,
    body.nst-standard-map #vpc-detail-panel,
    body.nst-standard-map #connection-intelligence-panel { display: none !important; }

    /* ── Responsive ──────────────────────────────────────────────────── */
    @media (max-width: 860px) {
      .nst-standard-split { flex-direction: column; }
      .nst-conn-panel { width: 100%; max-width: none; max-height: 36vh; border-left: none; border-top: 1px solid var(--bdr); }
    }
    @media print {
      body.nst-standard-map { height: auto; overflow: visible; }
      .nst-conn-panel { width: 45%; }
      .nst-map-style-bar, .nst-toolbar-row, .nst-legend-row { display: none !important; }
    }

    /* ── Scrollbar ───────────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: var(--bg1); }
    ::-webkit-scrollbar-thumb { background: var(--bg3); border-radius: 3px; }
    """


def _html_esc(s: object) -> str:
    return (
        str(s if s is not None else '')
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
    )


def embed_inventory_program_status_banner(program_status):
    """Compact honesty strip for inventory Standard L2 (collapsed by default).

    Full Discovery Program Status (HARD STOP / live evidence) belongs on the
    Discovery crawl surface — not as a red wall above the inventory L2 map.
    """
    if not isinstance(program_status, dict):
        summary = 'Inventory Standard L2 — Program Status unknown'
        body = (
            '<div class="nst-ps-gate">Do not claim enterprise Discovery readiness '
            'from this map alone.</div>'
        )
    else:
        ready = program_status.get('readiness') or {}
        identity = program_status.get('map_identity') or {}
        gate = str(ready.get('release_gate') or 'BLOCKED')
        hard = ready.get('hard_stop') is True
        if gate == 'BLOCKED' or hard:
            gate_line = (
                'Discovery crawl release gate: BLOCKED until retained live_ssh evidence '
                '(HARD STOP). This inventory L2 map is a separate surface.'
            )
        elif gate == 'PASS':
            gate_line = 'Discovery crawl release gate: PASS (retained live evidence).'
        else:
            gate_line = f'Discovery crawl release gate: {gate}.'
        cats = program_status.get('categories') or []
        items = ''.join(
            '<li><strong>' + _html_esc(c.get('label') or c.get('id')) + ':</strong> '
            + _html_esc(c.get('summary') or '') + '</li>'
            for c in cats if isinstance(c, dict)
        )
        note = ((program_status.get('honesty') or {}).get('note') or '')
        summary = _html_esc(
            identity.get('label')
            or 'Inventory Standard L2 — sidebar SSH scope (not Discovery crawl)'
        )
        body = f"""
      <div class="nst-ps-identity">{summary}</div>
      <div>{_html_esc(ready.get('operator_summary') or '')}</div>
      <div class="nst-ps-gate">{_html_esc(gate_line)}</div>
      <ul>{items}</ul>
      <div class="nst-ps-note">{_html_esc(note)} Program Status is not inventory topology.</div>
"""
    return f"""
    <details class="nst-program-status-banner" id="nst-program-status-banner">
      <summary>Map honesty · inventory Standard L2 (not Discovery crawl)</summary>
      {body}
    </details>
    """

def embed_standard_map_top_chrome(version_label, num_nodes, num_edges, extra_header='', program_status=None):
    """Modern enterprise header — compact, informative, offline-safe."""
    ps_html = embed_inventory_program_status_banner(program_status)
    return f"""
  <div class="nst-top-chrome" id="nst-top-chrome" role="banner">
    <div class="nst-top-row">
      <div class="nst-brand-icon" aria-hidden="true">NST</div>
      <div>
        <h1>Standard L2 Map<span class="nst-ver">{version_label}</span></h1>
        <div style="font-size:10px;color:#475569;margin-top:1px;">Physical topology · inventory scope · not Discovery crawl Command Center</div>
      </div>
      <div class="nst-top-stats">
        <div class="nst-hstat"><div class="nst-hstat-val">{num_nodes}</div><div class="nst-hstat-lbl">Devices</div></div>
        <div class="nst-vsep"></div>
        <div class="nst-hstat"><div class="nst-hstat-val">{num_edges}</div><div class="nst-hstat-lbl">Links</div></div>
        <div class="nst-vsep"></div>
        <div class="nst-kpis" id="nst-kpi-row" style="gap:4px;align-items:center;"></div>
      </div>
    </div>
    {ps_html}
    {extra_header}
    <div class="nst-toolbar-row">
      <input type="text" class="nst-search-input" id="searchInput"
        placeholder="Search: device, port, VLAN, Po, peer-link…"
        oninput="if(typeof nstFilterConnections==='function') nstFilterConnections(this.value);"
        aria-label="Search topology" />
      <button type="button" class="nst-btn" onclick="nstClearSearch()" aria-label="Clear search">Clear</button>
      <button type="button" class="nst-btn" id="descToggleBtn" onclick="nstTogglePortLabels()">Port labels</button>
      <label class="nst-util-toggle" id="nst-util-toggle-wrap">
        <input type="checkbox" id="nst-util-overlay-on" disabled
          onchange="if(typeof nstSetUtilOverlay==='function') nstSetUtilOverlay(this.checked);" />
        Utilization overlay
      </label>
      <span class="nst-util-chip" id="nst-util-mode-chip">Overlay unavailable</span>
      <button type="button" class="nst-btn" id="nst-util-live-btn" disabled
        title="Live SSH requires the operator console and vault credential.">Live SSH</button>
    </div>
    <div class="nst-util-banner" id="nst-util-banner" hidden></div>
    <div class="nst-util-legend" id="nst-util-legend" hidden aria-label="Utilization legend">
      <span><span class="nst-util-swatch gray"></span>unsampled (gray dashed — not down)</span>
      <span><span class="nst-util-swatch ok"></span>&lt;70%</span>
      <span><span class="nst-util-swatch warn"></span>70–90%</span>
      <span><span class="nst-util-swatch hot"></span>≥90%</span>
    </div>
    <div class="nst-legend-row" aria-label="Link type legend">
      <span class="nst-legend-pill"><span class="nst-legend-swatch" style="background:#607d8b"></span>Standard</span>
      <span class="nst-legend-pill"><span class="nst-legend-swatch" style="background:#10b981"></span>Port-Channel</span>
      <span class="nst-legend-pill"><span class="nst-legend-swatch" style="background:#f59e0b"></span>vPC Member</span>
      <span class="nst-legend-pill"><span class="nst-legend-swatch" style="background:#8b5cf6"></span>Peer-Link</span>
      <span class="nst-legend-pill"><span class="nst-legend-swatch" style="background:#10b981;border:1px solid #34d399"></span>Verified</span>
      <span class="nst-legend-pill"><span class="nst-legend-swatch" style="background:#f59e0b"></span>Asymmetric</span>
      <span class="nst-legend-pill"><span class="nst-legend-swatch" style="background:#ef4444"></span>Mismatch</span>
    </div>
  </div>
"""


def embed_standard_map_pane_html():
    """Right-side connection panel — always visible next to map."""
    return """
      <div class="nst-conn-panel" id="nst-conn-panel" role="complementary" aria-label="Connection index">
        <div class="nst-briefing" id="nst-briefing">
          <div class="nst-briefing-title">Connection Index</div>
          <div class="nst-kpis" id="nst-kpi-row"></div>
        </div>
        <div class="nst-conn-search">
          <input type="text" id="nst-conn-filter" placeholder="Filter: device, port, VLAN, Po, CDP…"
            oninput="nstFilterConnections(this.value)" />
        </div>
        <div class="nst-conn-table-wrap" tabindex="0" role="region" aria-label="Connection index table">
          <table class="nst-conn-table">
            <thead><tr>
              <th onclick="nstSortConn(0)">Local</th>
              <th onclick="nstSortConn(1)">Port</th>
              <th onclick="nstSortConn(2)">Remote</th>
              <th onclick="nstSortConn(3)">Port</th>
              <th onclick="nstSortConn(4)">Type</th>
              <th onclick="nstSortConn(5)">VLAN</th>
              <th onclick="nstSortConn(6)">Speed</th>
            </tr></thead>
            <tbody id="nst-conn-tbody"></tbody>
          </table>
        </div>
        <div class="nst-util-unmapped" id="nst-util-unmapped" hidden>
          <div class="nst-briefing-title">Unmapped interfaces (not drawn)</div>
          <table>
            <thead><tr><th>Host</th><th>ifName</th><th>Normalized</th><th>Reason</th></tr></thead>
            <tbody id="nst-util-unmapped-body"></tbody>
          </table>
        </div>
        <div class="nst-link-detail" id="nst-link-detail">
          <strong>Selected link</strong>
          Click a row or map edge to inspect WHO / HOW / WHAT.
        </div>
      </div>
    """


def embed_standard_map_style_bar():
    return """
        <div class="nst-map-style-bar" id="nst-map-style-bar">
          <label>Map view</label>
          <button type="button" class="nst-map-style-btn active" data-style="tier" onclick="nstSetMapStyle('tier')">Tier</button>
          <button type="button" class="nst-map-style-btn" data-style="radial" onclick="nstSetMapStyle('radial')">Radial</button>
          <button type="button" class="nst-map-style-btn" data-style="focus" onclick="nstSetMapStyle('focus')">Focus</button>
          <button type="button" class="nst-map-style-btn" data-style="schematic" onclick="nstSetMapStyle('schematic')">Schematic</button>
          <div class="nst-focus-controls" id="nst-focus-controls" style="display:none;">
            <select id="nst-focus-device" onchange="nstApplyFocusView()"></select>
            <button type="button" id="nst-hop-1" class="on" onclick="nstSetFocusHops(1)">1 hop</button>
            <button type="button" id="nst-hop-2" onclick="nstSetFocusHops(2)">2 hops</button>
          </div>
        </div>
    """


def build_briefing_stats(edges_list, nodes_list, extra=None):
    """Compute KPI dict for briefing strip."""
    extra = extra or {}
    po = sum(1 for e in edges_list if (e.get('type') or (e.get('edge_data') or {}).get('type')) in (
        'port-channel', 'vpc', 'vpc-peer-link'))
    asym = sum(1 for e in edges_list if (e.get('type') or (e.get('edge_data') or {}).get('type')) == 'asymmetric'
               or (e.get('edge_data') or {}).get('confidence') == 'Medium')
    mismatch = sum(1 for e in edges_list if (e.get('edge_data') or {}).get('confidence') == 'Mismatch'
                  or e.get('confidence') == 'Mismatch')
    verified = sum(1 for e in edges_list if (e.get('edge_data') or e).get('confidence') == 'Verified'
                  or (e.get('edge_data') or e).get('trust_tier') == 'verified')
    roles = {}
    for n in nodes_list or []:
        r = n.get('role', 'unknown')
        roles[r] = roles.get(r, 0) + 1
    return {
        'nodes': len(nodes_list or []),
        'links': len(edges_list or []),
        'po_vpc': po,
        'asymmetric': asym,
        'mismatch': mismatch,
        'verified': verified,
        'core': roles.get('core', 0),
        'distribution': roles.get('distribution', 0),
        'access': roles.get('access', 0),
        'failed_hosts': extra.get('failed_hosts', 0),
        'truncated': extra.get('truncated', False),
    }


def embed_standard_map_js(link_rows_json, briefing_json='{}'):
    """Client-side map styles, connection table sync, focus mode."""
    return f"""
    window.__NST_LINKS__ = {link_rows_json};
    window.__NST_BRIEF__ = {briefing_json};
    window.__NST_MAP_STYLE__ = 'tier';
    window.__NST_FOCUS_HOPS__ = 1;
    window.__NST_SAVED_POS__ = {{}};
    window.__NST_SHOW_PORT_LABELS__ = false;
    var nstSortCol = 0, nstSortAsc = true;

    function nstLinkTypeBadge(lt) {{
      lt = (lt || 'standard').toLowerCase();
      if (lt.indexOf('peer') >= 0) return '<span class="nst-type-badge nst-type-vpc-peer">Peer</span>';
      if (lt === 'port-channel') return '<span class="nst-type-badge nst-type-po">Po</span>';
      if (lt === 'vpc') return '<span class="nst-type-badge nst-type-vpc">vPC</span>';
      if (lt === 'asymmetric') return '<span class="nst-type-badge nst-type-warn">Uni</span>';
      return '<span class="nst-type-badge nst-type-std">L2</span>';
    }}

    function nstClearSearch() {{
      var si = document.getElementById('searchInput');
      var cf = document.getElementById('nst-conn-filter');
      if (si) si.value = '';
      if (cf) cf.value = '';
      nstFilterConnections('');
    }}

    function nstTogglePortLabels() {{
      window.__NST_SHOW_PORT_LABELS__ = !window.__NST_SHOW_PORT_LABELS__;
      var btn = document.getElementById('descToggleBtn');
      if (btn) {{
        btn.textContent = window.__NST_SHOW_PORT_LABELS__ ? 'Hide port labels' : 'Show port labels';
        btn.classList.toggle('active', window.__NST_SHOW_PORT_LABELS__);
      }}
      nstApplyPortLabels();
    }}

    function nstApplyPortLabels() {{
      if (!edges) return;
      var show = window.__NST_SHOW_PORT_LABELS__;
      var upd = [];
      edges.forEach(function(e) {{
        var lbl = show ? (e.map_label || e.label || '') : '';
        if (show && lbl && lbl.length > 28) lbl = lbl.substring(0, 25) + '…';
        upd.push({{ id: e.id, label: lbl }});
      }});
      if (upd.length) edges.update(upd);
    }}

    function toggleDescriptions() {{ nstTogglePortLabels(); }}

    function nstRenderKpis() {{
      var b = window.__NST_BRIEF__ || {{}};
      var el = document.getElementById('nst-kpi-row');
      if (!el) return;
      var html = '';
      if (b.po_vpc) html += '<span class="nst-kpi"><b>' + b.po_vpc + '</b> Po/vPC</span>';
      if (b.asymmetric) html += '<span class="nst-kpi warn"><b>' + b.asymmetric + '</b> unidir</span>';
      if (b.mismatch) html += '<span class="nst-kpi bad"><b>' + b.mismatch + '</b> mismatch</span>';
      if (b.verified) html += '<span class="nst-kpi" style="border-color:#10b981;color:#10b981"><b>' + b.verified + '</b> verified</span>';
      if (b.failed_hosts) html += '<span class="nst-kpi bad"><b>' + b.failed_hosts + '</b> failed</span>';
      if (b.truncated) html += '<span class="nst-kpi warn"><b>cap</b></span>';
      el.innerHTML = html;
    }}

    function nstRowId(r) {{
      return [r.from, r.local_port, r.to, r.remote_port].join('|');
    }}

    function nstRenderConnTable() {{
      var tb = document.getElementById('nst-conn-tbody');
      if (!tb) return;
      tb.innerHTML = '';
      (window.__NST_LINKS__ || []).forEach(function(r, idx) {{
        var tr = document.createElement('tr');
        tr.dataset.rowId = nstRowId(r);
        tr.dataset.edgeIdx = idx;
        tr.dataset.search = [
          r.from, r.local_port, r.to, r.remote_port,
          r.vlan||'', r.speed||'', r.protocol||'', r.link_type||'',
          r.description||'', r.confidence||'', r.trust_tier||''
        ].join(' ').toLowerCase();
        if ((r.link_type||'').indexOf('peer') >= 0) tr.classList.add('nst-peer-row');
        tr.innerHTML =
          '<td><b>' + (r.from||'') + '</b></td>' +
          '<td class="port">' + (r.local_port||'') + '</td>' +
          '<td><b>' + (r.to||'') + '</td>' +
          '<td class="port">' + (r.remote_port||'') + '</td>' +
          '<td>' + nstLinkTypeBadge(r.link_type) + '</td>' +
          '<td>' + (r.vlan||'—') + '</td>' +
          '<td>' + (r.speed||'—') + '</td>';
        tr.onclick = function() {{ nstSelectLinkRow(tr, r); }};
        tb.appendChild(tr);
      }});
    }}

    function nstSelectLinkRow(tr, r) {{
      document.querySelectorAll('#nst-conn-tbody tr').forEach(function(x) {{
        x.classList.remove('nst-row-sel');
      }});
      if (tr) tr.classList.add('nst-row-sel');
      nstShowLinkDetail(r);
      nstHighlightEdgeOnMap(r);
    }}

    function nstShowLinkDetail(r) {{
      var el = document.getElementById('nst-link-detail');
      if (!el || !r) return;
      var lines = [
        '<strong>' + r.from + ' ' + r.local_port + ' → ' + r.to + ' ' + r.remote_port + '</strong>',
        'Type: ' + (r.link_type || r.protocol || 'standard') +
          (r.confidence ? ' · Confidence: ' + r.confidence : '') +
          (r.trust_tier ? ' · Trust: ' + r.trust_tier + (r.trust_score ? ' (' + r.trust_score + ')' : '') : '') +
          (r.bidirectional ? ' · Bidirectional CDP' : ''),
        'VLAN: ' + (r.vlan || '—') + ' · Speed: ' + (r.speed || '—') +
          ' · Status: ' + (r.status || '—'),
      ];
      if (r.description) lines.push('Desc: ' + r.description);
      if (r.remote_platform) lines.push('Remote platform: ' + r.remote_platform);
      el.innerHTML = lines.join('<br>');
    }}

    function nstHighlightEdgeOnMap(r) {{
      if (!edges || !network) return;
      var match = null;
      edges.forEach(function(e) {{
        if (e.from === r.from && e.to === r.to &&
            (e.f_port === r.local_port || (e.edge_data && e.edge_data.f_port === r.local_port))) {{
          match = e.id;
        }}
      }});
      if (match) {{
        try {{
          network.selectEdges([match]);
          network.focus(match, {{ scale: 1.1, animation: {{ duration: 300 }} }});
        }} catch (ex) {{}}
      }}
    }}

    function nstSortConn(col) {{
      if (nstSortCol === col) nstSortAsc = !nstSortAsc;
      else {{ nstSortCol = col; nstSortAsc = true; }}
      var keys = ['from','local_port','to','remote_port','link_type','vlan','speed'];
      var k = keys[col];
      window.__NST_LINKS__.sort(function(a,b) {{
        var va = (a[k]||'').toString(), vb = (b[k]||'').toString();
        if (va < vb) return nstSortAsc ? -1 : 1;
        if (va > vb) return nstSortAsc ? 1 : -1;
        return 0;
      }});
      nstRenderConnTable();
      nstFilterConnections(document.getElementById('nst-conn-filter').value);
    }}

    function nstFilterConnections(q) {{
      q = (q||'').trim().toLowerCase();
      var si = document.getElementById('searchInput');
      var cf = document.getElementById('nst-conn-filter');
      if (si && document.activeElement !== si && si.value.toLowerCase() !== q) si.value = q;
      if (cf && document.activeElement !== cf && cf.value.toLowerCase() !== q) cf.value = q;
      var vis = 0;
      document.querySelectorAll('#nst-conn-tbody tr').forEach(function(tr) {{
        var ok = !q || (tr.dataset.search||'').indexOf(q) >= 0;
        tr.style.display = ok ? '' : 'none';
        if (ok) vis++;
      }});
      if (typeof searchNodes === 'function') searchNodes(q);
      else if (typeof topoApplySearch === 'function') topoApplySearch(q);
      else if (typeof topoShellSearch === 'function') topoShellSearch(q);
    }}

    function nstPopulateFocusDevices() {{
      var sel = document.getElementById('nst-focus-device');
      if (!sel || !nodes) return;
      sel.innerHTML = '';
      nodes.get().slice().sort(function(a,b) {{
        return (a.id||'').localeCompare(b.id||'');
      }}).forEach(function(n) {{
        var o = document.createElement('option');
        o.value = n.id;
        o.textContent = n.id + (n.role ? ' (' + n.role + ')' : '');
        sel.appendChild(o);
      }});
    }}

    function nstSetFocusHops(n) {{
      window.__NST_FOCUS_HOPS__ = n;
      document.getElementById('nst-hop-1').classList.toggle('on', n === 1);
      document.getElementById('nst-hop-2').classList.toggle('on', n === 2);
      if (window.__NST_MAP_STYLE__ === 'focus') nstApplyFocusView();
    }}

    function nstCollectFocusNodes(centerId, hops) {{
      var primary = {{}}, hop1 = {{}}, hop2 = {{}};
      primary[centerId] = true;
      edges.forEach(function(e) {{
        if (e.from === centerId) hop1[e.to] = true;
        if (e.to === centerId) hop1[e.from] = true;
      }});
      if (hops >= 2) {{
        Object.keys(hop1).forEach(function(nid) {{
          edges.forEach(function(e) {{
            if (e.from === nid) hop2[e.to] = true;
            if (e.to === nid) hop2[e.from] = true;
          }});
        }});
      }}
      var visible = {{}};
      Object.assign(visible, primary, hop1, hop2);
      return {{ primary: primary, hop1: hop1, hop2: hop2, visible: visible }};
    }}

    function nstApplyFocusView() {{
      if (!nodes || !edges || !network) return;
      var center = document.getElementById('nst-focus-device').value;
      var hops = window.__NST_FOCUS_HOPS__ || 1;
      var f = nstCollectFocusNodes(center, hops);
      var nu = [], eu = [];
      nodes.forEach(function(n) {{
        var on = f.visible[n.id];
        nu.push({{
          id: n.id,
          hidden: !on,
          opacity: f.primary[n.id] ? 1 : (f.hop1[n.id] ? 0.9 : 0.75),
          borderWidth: f.primary[n.id] ? 4 : 2
        }});
      }});
      edges.forEach(function(e) {{
        var on = f.visible[e.from] && f.visible[e.to];
        eu.push({{ id: e.id, hidden: !on, opacity: on ? 1 : 0.05 }});
      }});
      nodes.update(nu);
      edges.update(eu);
      try {{ network.focus(center, {{ scale: 1.2, animation: false }}); }} catch (ex) {{}}
      nstFilterConnTableByDevice(center);
    }}

    function nstFilterConnTableByDevice(dev) {{
      document.querySelectorAll('#nst-conn-tbody tr').forEach(function(tr) {{
        var r = window.__NST_LINKS__[parseInt(tr.dataset.edgeIdx, 10)];
        if (!r) return;
        var ok = r.from === dev || r.to === dev;
        tr.style.display = ok ? '' : 'none';
      }});
    }}

    function nstSavePositions() {{
      if (!nodes) return;
      window.__NST_SAVED_POS__ = {{}};
      nodes.forEach(function(n) {{
        if (n.x != null) window.__NST_SAVED_POS__[n.id] = {{ x: n.x, y: n.y }};
      }});
    }}

    function nstRestorePositions() {{
      var upd = [];
      nodes.forEach(function(n) {{
        var p = window.__NST_SAVED_POS__[n.id];
        if (p) upd.push({{ id: n.id, x: p.x, y: p.y, fixed: false }});
        else upd.push({{ id: n.id, fixed: false }});
      }});
      if (upd.length) nodes.update(upd);
    }}

    function nstFitMap() {{
      if (!network) return;
      try {{
        network.redraw();
        network.fit({{ animation: false, padding: 50 }});
      }} catch (e) {{}}
    }}

    function nstEnsureMapSize() {{
      var col = document.querySelector('.nst-map-col');
      var c = document.getElementById('mynetwork');
      var split = document.querySelector('.nst-standard-split');
      if (split) {{
        split.style.minHeight = '420px';
        split.style.flex = '1 1 auto';
      }}
      if (col) {{
        col.style.minHeight = '420px';
        col.style.flex = '1 1 60%';
      }}
      if (c) {{
        c.style.minHeight = '360px';
        c.style.height = '100%';
        c.style.background = '#0b0f19';
      }}
    }}

    function nstApplyTierLayout() {{
      if (!network) return;
      nstRestorePositions();
      nodes.forEach(function(n) {{
        nodes.update({{ id: n.id, fixed: false, x: undefined, y: undefined }});
      }});
      network.setOptions({{
        layout: {{
          hierarchical: {{
            enabled: true,
            direction: 'UD',
            sortMethod: 'directed',
            levelSeparation: 150,
            nodeSpacing: 130,
            treeSpacing: 160
          }}
        }},
        physics: {{ enabled: false }},
        edges: {{ smooth: {{ type: 'cubicBezier', roundness: 0.35 }} }}
      }});
      setTimeout(nstFitMap, 80);
    }}

    function nstApplyRadialLayout() {{
      if (!nodes || !network) return;
      nstSavePositions();
      var byRole = {{ core: [], distribution: [], access: [], unknown: [] }};
      nodes.forEach(function(n) {{
        if (n.hidden) return;
        var r = n.role || 'unknown';
        if (!byRole[r]) byRole[r] = [];
        byRole[r].push(n.id);
      }});
      var rings = [
        ['core', 80],
        ['distribution', 200],
        ['access', 320],
        ['unknown', 400]
      ];
      var upd = [];
      rings.forEach(function(pair) {{
        var role = pair[0], radius = pair[1];
        var ids = byRole[role] || [];
        ids.forEach(function(id, i) {{
          var angle = (2 * Math.PI * i) / Math.max(ids.length, 1) - Math.PI / 2;
          upd.push({{
            id: id,
            x: radius * Math.cos(angle),
            y: radius * Math.sin(angle),
            fixed: true
          }});
        }});
      }});
      nodes.update(upd);
      network.setOptions({{
        layout: {{ hierarchical: {{ enabled: false }} }},
        physics: {{ enabled: false }},
        edges: {{ smooth: {{ type: 'curvedCW', roundness: 0.2 }} }}
      }});
      setTimeout(nstFitMap, 80);
    }}

    function nstApplySchematicLayout() {{
      if (!nodes || !network) return;
      nstSavePositions();
      var tiers = {{ core: 0, distribution: 1, access: 2, unknown: 1 }};
      var byTier = {{ 0: [], 1: [], 2: [] }};
      nodes.forEach(function(n) {{
        if (n.hidden) return;
        var t = tiers[n.role] != null ? tiers[n.role] : 1;
        byTier[t].push(n.id);
      }});
      var yStep = 200, xStep = 180, upd = [];
      [0, 1, 2].forEach(function(tier) {{
        var ids = byTier[tier] || [];
        var y = tier * yStep;
        ids.forEach(function(id, i) {{
          var x = (i - (ids.length - 1) / 2) * xStep;
          upd.push({{ id: id, x: x, y: y, fixed: true }});
        }});
      }});
      nodes.update(upd);
      network.setOptions({{
        layout: {{ hierarchical: {{ enabled: false }} }},
        physics: {{ enabled: false }},
        edges: {{ smooth: false }}
      }});
      setTimeout(nstFitMap, 80);
    }}

    function nstSetMapStyle(style) {{
      window.__NST_MAP_STYLE__ = style;
      document.querySelectorAll('.nst-map-style-btn').forEach(function(btn) {{
        btn.classList.toggle('active', btn.dataset.style === style);
      }});
      var fc = document.getElementById('nst-focus-controls');
      if (fc) fc.style.display = style === 'focus' ? 'flex' : 'none';
      if (!network) return;
      nodes.get().forEach(function(n) {{
        nodes.update({{ id: n.id, hidden: false, opacity: 1, borderWidth: 2 }});
      }});
      edges.get().forEach(function(e) {{
        edges.update({{ id: e.id, hidden: e.edge_data && e.hidden, opacity: 1 }});
      }});
      if (style === 'tier') nstApplyTierLayout();
      else if (style === 'radial') nstApplyRadialLayout();
      else if (style === 'schematic') nstApplySchematicLayout();
      else if (style === 'focus') {{
        network.setOptions({{
          layout: {{ hierarchical: {{ enabled: false }} }},
          physics: {{ enabled: false }},
          edges: {{ smooth: {{ type: 'cubicBezier', roundness: 0.3 }} }}
        }});
        nstApplyFocusView();
      }}
    }}

    function nstInitStandardMapShell() {{
      nstRenderKpis();
      nstRenderConnTable();
      nstPopulateFocusDevices();
      var cf = document.getElementById('nst-conn-filter');
      var si = document.getElementById('searchInput');
      if (cf && si) {{
        cf.addEventListener('input', function() {{ si.value = cf.value; }});
        si.addEventListener('input', function() {{ cf.value = si.value; nstFilterConnections(si.value); }});
      }}
      if (network) {{
        network.on('selectEdge', function(params) {{
          if (!params.edges.length) return;
          var e = edges.get(params.edges[0]);
          if (!e) return;
          var r = null;
          var links = window.__NST_LINKS__ || [];
          for (var li = 0; li < links.length; li++) {{
            var x = links[li];
            if (x.from === e.from && x.to === e.to) {{ r = x; break; }}
          }}
          if (r) {{
            var tr = document.querySelector('#nst-conn-tbody tr[data-row-id="' + nstRowId(r) + '"]');
            nstSelectLinkRow(tr, r);
          }}
        }});
        network.on('selectNode', function(params) {{
          if (!params.nodes.length) return;
          var nd = nodes.get(params.nodes[0]);
          if (!nd) return;
          var el = document.getElementById('nst-link-detail');
          if (el) {{
            el.innerHTML = '<strong>' + nstUtilEsc(nd.id) + '</strong>' +
              (nd.role ? ' · ' + nstUtilEsc(nd.role) : '') +
              '<br>Click a link row or edge for port-level detail.';
          }}
        }});
        network.on('doubleClick', function(params) {{
          if (params.nodes.length && window.__NST_MAP_STYLE__ === 'focus') {{
            document.getElementById('nst-focus-device').value = params.nodes[0];
            nstApplyFocusView();
          }}
        }});
      }}
    }}

    function nstBootStandardMap(retry) {{
      retry = retry || 0;
      nstEnsureMapSize();
      if (typeof createTopologyNetwork === 'function' && !network) {{
        createTopologyNetwork();
      }}
      if (!network && retry < 8) {{
        setTimeout(function() {{ nstBootStandardMap(retry + 1); }}, 150 + retry * 80);
        return;
      }}
      if (!network) {{
        if (typeof nstShowFallback === 'function') {{
          nstShowFallback('Map could not initialize. Try refresh or a newer Chrome build.');
        }}
        return;
      }}
      if (typeof wireNetworkHandlers === 'function') wireNetworkHandlers();
      nstInitStandardMapShell();
      nstApplyPortLabels();
      nstFitMap();
      setTimeout(nstFitMap, 200);
      setTimeout(nstFitMap, 600);
    }}

    function topoShellSearch(q) {{ nstFilterConnections(q); }}

    if (window.addEventListener) {{
      var _nstResizeTimer = null;
      window.addEventListener('resize', function() {{
        if (_nstResizeTimer) clearTimeout(_nstResizeTimer);
        _nstResizeTimer = setTimeout(function() {{
          nstEnsureMapSize();
          if (network) {{
            try {{ network.redraw(); }} catch (e) {{}}
          }}
        }}, 150);
      }});
      window.addEventListener('load', function() {{
        if (typeof nstBootStandardMap === 'function') nstBootStandardMap(0);
      }});
    }}
    """


def enrich_link_rows_from_vis_edges(edges_list, nodes_list=None):
    """Build NOC connection index rows from Vis.js edge payloads."""
    from utils.topo_map_shell import link_rows_from_edges
    flat = []
    for e in edges_list:
        if not isinstance(e, dict):
            continue
        ed = e.get('edge_data') or e
        merged = dict(ed)
        merged.setdefault('from', e.get('from', ''))
        merged.setdefault('to', e.get('to', ''))
        merged.setdefault('f_port', e.get('f_port', ed.get('f_port', '')))
        merged.setdefault('t_port', e.get('t_port', ed.get('t_port', '')))
        merged.setdefault('type', e.get('type', ed.get('type', '')))
        flat.append(merged)
    rows = link_rows_from_edges(flat, nodes_list)
    for i, e in enumerate(edges_list):
        if i < len(rows):
            rows[i]['edge_id'] = e.get('id', i)
    return rows


def embed_utilization_overlay_js(payload_json):
    """Client paint overlay. payload_json must already be script-safe JSON."""
    return (
        "\n    window.__NST_UTIL_PAYLOAD__ = "
        + payload_json
        + ";\n"
        + r"""
    window.__NST_UTIL_ON__ = false;
    window.__NST_UTIL_ORIG__ = {};

    function nstUtilEsc(s) {
      if (s === null || s === undefined) return '';
      return String(s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function nstUtilPayload() {
      return window.__NST_UTIL_PAYLOAD__ || { available: false, ok: false };
    }

    function nstUtilFmtBps(v) {
      if (v === null || v === undefined || v === '') return '—';
      var n = Number(v);
      if (!isFinite(n)) return nstUtilEsc(v);
      if (n >= 1e9) return (n / 1e9).toFixed(2) + ' Gbps';
      if (n >= 1e6) return (n / 1e6).toFixed(2) + ' Mbps';
      if (n >= 1e3) return (n / 1e3).toFixed(2) + ' kbps';
      return n + ' bps';
    }

    function nstUtilEdgeIsNonCable(e) {
      if (!e) return true;
      if (e.not_physical) return true;
      var layer = String(e.layer || '').toLowerCase();
      if (layer === 'overlay' || layer === 'l3' || layer === 'evpn') return true;
      var proto = String(e.protocol || '').toUpperCase();
      if (proto === 'EVPN' || proto === 'OSPF' || proto === 'BGP' || proto === 'ISIS') return true;
      var et = String(e.type || '').toLowerCase();
      if (et === 'overlay' || et.indexOf('evpn') >= 0) return true;
      if (et === 'stp-blocked' || et.indexOf('stp-blocked') >= 0) return true;
      var lt = String(e.link_type || '').toLowerCase();
      if (lt === 'stp-blocked' || lt === 'stp_blocked') return true;
      if (proto === 'STP') return true;
      return false;
    }

    function nstFindVisEdgeForRow(r) {
      if (!edges || !r) return null;
      var match = null;
      edges.forEach(function(e) {
        if (e.from === r.from && e.to === r.to &&
            (e.f_port === r.local_port || (e.edge_data && e.edge_data.f_port === r.local_port))) {
          match = e;
        }
      });
      return match;
    }

    function nstUtilBindingForRow(r) {
      var p = nstUtilPayload();
      var e = nstFindVisEdgeForRow(r);
      if (!e || !p.bindings) return null;
      return p.bindings[String(e.id)] || null;
    }

    function nstRenderUtilUnmapped() {
      var wrap = document.getElementById('nst-util-unmapped');
      var tb = document.getElementById('nst-util-unmapped-body');
      var p = nstUtilPayload();
      if (!wrap || !tb) return;
      tb.innerHTML = '';
      var rows = (p.doc && p.doc.unmapped) ? p.doc.unmapped : [];
      if (!window.__NST_UTIL_ON__ || !rows.length) {
        wrap.hidden = true;
        return;
      }
      wrap.hidden = false;
      rows.forEach(function(u) {
        var tr = document.createElement('tr');
        tr.innerHTML = '<td>' + nstUtilEsc(u.device_id) + '</td>' +
          '<td>' + nstUtilEsc(u.if_name_raw) + '</td>' +
          '<td>' + nstUtilEsc(u.if_name_normalized || '') + '</td>' +
          '<td>' + nstUtilEsc(u.reason) + '</td>';
        tb.appendChild(tr);
      });
    }

    function nstApplyUtilStrokes() {
      if (!edges) return;
      var p = nstUtilPayload();
      var discoveryHost = p.host === 'discovery';
      var updates = [];
      edges.forEach(function(e) {
        if (!window.__NST_UTIL_ORIG__[e.id]) {
          window.__NST_UTIL_ORIG__[e.id] = {
            color: e.color, width: e.width, dashes: e.dashes
          };
        }
        var view = (p.bindings && p.bindings[String(e.id)]) || null;
        if (discoveryHost && !view && nstUtilEdgeIsNonCable(e)) {
          return;
        }
        var st = view && view.stroke ? view.stroke : {
          color: '#64748b', width: 2, dashes: [5, 4]
        };
        updates.push({
          id: e.id,
          color: st.color,
          width: st.width,
          dashes: st.dashes
        });
      });
      if (updates.length) edges.update(updates);
    }

    function nstRestoreUtilStrokes() {
      if (!edges) return;
      var updates = [];
      edges.forEach(function(e) {
        var orig = window.__NST_UTIL_ORIG__[e.id];
        if (!orig) return;
        updates.push({
          id: e.id,
          color: orig.color,
          width: orig.width,
          dashes: orig.dashes
        });
      });
      if (updates.length) edges.update(updates);
    }

    function nstSetUtilOverlay(on) {
      var p = nstUtilPayload();
      var cb = document.getElementById('nst-util-overlay-on');
      if (!p.ok || !p.available) {
        window.__NST_UTIL_ON__ = false;
        if (cb) cb.checked = false;
        nstRestoreUtilStrokes();
        nstRenderUtilUnmapped();
        nstSyncUtilChrome();
        return;
      }
      window.__NST_UTIL_ON__ = !!on;
      if (cb) cb.checked = !!on;
      if (on) nstApplyUtilStrokes();
      else nstRestoreUtilStrokes();
      nstRenderUtilUnmapped();
      nstSyncUtilChrome();
    }

    function nstSyncUtilChrome() {
      var p = nstUtilPayload();
      var chip = document.getElementById('nst-util-mode-chip');
      var banner = document.getElementById('nst-util-banner');
      var legend = document.getElementById('nst-util-legend');
      var cb = document.getElementById('nst-util-overlay-on');
      if (cb) cb.disabled = !(p.ok && p.available);
      if (!p.ok || !p.available) {
        if (chip) {
          chip.textContent = p.error
            ? ('Overlay unavailable: ' + p.error)
            : 'Overlay: none — replay not loaded';
          chip.className = 'nst-util-chip' + (p.error ? ' err' : '');
        }
        if (banner) {
          banner.hidden = !p.error;
          if (p.error) banner.textContent = p.error + ' Map topology is unchanged.';
        }
        if (legend) legend.hidden = true;
        return;
      }
      if (chip) {
        var mode = p.mode || (p.doc && p.doc.mode) || 'replay';
        var degraded = !!(p.degraded || (p.doc && p.doc.degraded));
        if (mode === 'live') {
          chip.className = 'nst-util-chip live' + (degraded ? ' degraded' : '');
          chip.textContent = window.__NST_UTIL_ON__
            ? ('Live SSH/' + (p.evidence_class || 'live_ssh') + ' — not SNMP')
            : 'Live SSH available — overlay off';
        } else {
          chip.className = 'nst-util-chip replay';
          chip.textContent = window.__NST_UTIL_ON__
            ? ('Replay/' + (p.evidence_class || 'fixture') + ' — not a live poll')
            : 'Replay available — overlay off';
        }
      }
      if (legend) legend.hidden = !window.__NST_UTIL_ON__;
      if (banner) {
        banner.hidden = false;
        var extra = '';
        var modeB = p.mode || (p.doc && p.doc.mode) || '';
        if (p.degraded || (p.doc && p.doc.degraded)) {
          extra += ' Degraded — some devices failed or cancelled. Graph topology is unchanged.';
        }
        if (window.__NST_UTIL_ON__) {
          extra += ' Overlay on: ' + (p.painted_count || 0) + '/' + (p.l2_edge_count || 0) +
            ' L2 edges sampled. Unsampled stay gray dashed — not down.';
          var staleN = p.doc && p.doc.summary ? p.doc.summary.stale_count : 0;
          if (staleN) extra += ' STALE — last sample older than policy. Colors kept; do not treat as current load.';
          var gen = p.doc && p.doc.generated_at ? p.doc.generated_at : '';
          if (gen) extra += ' Sample: ' + gen + '.';
        } else {
          extra += ' Overlay off: L2 coloring unchanged.';
        }
        var modeLabel = (modeB === 'live')
          ? (p.live_label || 'Live SSH counters — not SNMP.')
          : (p.replay_label || 'Replay snapshot — not a live poll.');
        banner.textContent = (p.banner || '') + ' ' + modeLabel + extra;
      }
    }

    function nstAppendUtilDetail(r) {
      var el = document.getElementById('nst-link-detail');
      if (!el || !r) return;
      el.classList.toggle('nst-util-open', !!window.__NST_UTIL_ON__);
      if (!window.__NST_UTIL_ON__) return;
      var view = nstUtilBindingForRow(r);
      var bits = ['<div class="nst-util-inspect">'];
      bits.push('<strong>Utilization (paint, not topology)</strong>');
      if (!view) {
        bits.push('No utilization sample for this link.');
        bits.push('Gray dashed = no sample — not down.');
        bits.push('Paint is not topology. Overlay never creates cables.');
      } else {
        bits.push('Mode: ' + nstUtilEsc(view.mode) +
          ' · evidence: ' + nstUtilEsc(view.evidence_class) +
          ' · join: ' + nstUtilEsc(view.join_status || '—'));
        if (view.mode === 'live') {
          bits.push('Live SSH counters — not SNMP.');
        } else {
          bits.push('Replay snapshot — not a live poll.');
        }
        bits.push('in: ' + nstUtilFmtBps(view.in_bps) +
          (view.in_pct != null ? ' (' + nstUtilEsc(view.in_pct) + '%)' : '') +
          ' · out: ' + nstUtilFmtBps(view.out_bps) +
          (view.out_pct != null ? ' (' + nstUtilEsc(view.out_pct) + '%)' : ''));
        bits.push('ifSpeed: ' + nstUtilFmtBps(view.if_speed_bps) +
          (view.pct != null ? ' · pct max: ' + nstUtilEsc(view.pct) + '%' : ''));
        bits.push('job/snapshot: ' + nstUtilEsc(view.job_id || '—') +
          ' · sampled_at: ' + nstUtilEsc(view.sampled_at || '—') +
          (view.age_seconds != null ? ' · age: ' + nstUtilEsc(view.age_seconds) + 's' : ''));
        if (view.stale) {
          bits.push('STALE — last sample older than policy. Colors kept; do not treat as current load.');
        }
        if (view.paint_state === 'partial' || view.join_status === 'partial') {
          bits.push('One side sampled — not a full duplex measurement.');
        }
        bits.push(nstUtilEsc(view.truth ||
          'Paint is not topology. Gray dashed = no sample — not down.'));
      }
      bits.push('</div>');
      el.innerHTML = el.innerHTML + '<br>' + bits.join('<br>');
    }

    function nstAppendUtilWhy(e) {
      var el = document.getElementById('nst-why-link');
      if (!el || !e || !window.__NST_UTIL_ON__) return;
      var p = nstUtilPayload();
      if (!p.ok || !p.available) return;
      var note = document.createElement('div');
      note.className = 'nst-util-why';
      note.style.marginTop = '6px';
      note.style.fontSize = '11px';
      if (nstUtilEdgeIsNonCable(e)) {
        note.textContent = 'Utilization: not a cable (EVPN/overlay/incomplete). Not painted. Incomplete observations stay in diagnostics — not map links.';
        el.appendChild(note);
        return;
      }
      var view = (p.bindings && p.bindings[String(e.id)]) || null;
      var bits = ['Utilization (paint, not topology).'];
      if (!view) {
        bits.push('No utilization sample for this link. Gray dashed = no sample — not down.');
      } else if (view.mode === 'live') {
        bits.push('Live SSH counters — not SNMP.');
        if (view.stale) bits.push('STALE — last sample older than policy. Colors kept; do not treat as current load.');
        if (view.paint_state === 'partial' || view.join_status === 'partial') {
          bits.push('One side sampled — not a full duplex measurement.');
        }
      } else {
        bits.push('Replay snapshot — not a live poll.');
        if (view.stale) bits.push('STALE — last sample older than policy. Colors kept; do not treat as current load.');
        if (view.paint_state === 'partial' || view.join_status === 'partial') {
          bits.push('One side sampled — not a full duplex measurement.');
        }
      }
      note.textContent = bits.join(' ');
      el.appendChild(note);
    }

    (function nstHookUtilOverlay() {
      if (typeof nstShowLinkDetail === 'function' && !nstShowLinkDetail._nstUtilHooked) {
        var _base = nstShowLinkDetail;
        var wrapped = function(r) {
          _base(r);
          nstAppendUtilDetail(r);
        };
        wrapped._nstUtilHooked = true;
        nstShowLinkDetail = wrapped;
      }
      if (typeof nstInitStandardMapShell === 'function' && !nstInitStandardMapShell._nstUtilHooked) {
        var _init = nstInitStandardMapShell;
        var wrappedInit = function() {
          _init();
          nstSyncUtilChrome();
          nstRenderUtilUnmapped();
        };
        wrappedInit._nstUtilHooked = true;
        nstInitStandardMapShell = wrappedInit;
      }
      if (typeof nstWhyThisLink === 'function' && !nstWhyThisLink._nstUtilHooked) {
        var _why = nstWhyThisLink;
        var wrappedWhy = function(e) {
          _why(e);
          nstAppendUtilWhy(e);
        };
        wrappedWhy._nstUtilHooked = true;
        nstWhyThisLink = wrappedWhy;
      }
      var liveBtn = document.getElementById('nst-util-live-btn');
      var pHook = nstUtilPayload();
      var liveAllowed = pHook.live_controls !== false && pHook.host !== 'discovery';
      if (liveBtn && !liveBtn._nstBound) {
        liveBtn._nstBound = true;
        if (!liveAllowed) {
          liveBtn.disabled = true;
          liveBtn.title = 'Live SSH is Standard L2 only. Discovery is a viewer. Not SNMP.';
        } else if (location.protocol === 'file:') {
          liveBtn.disabled = true;
          liveBtn.title = 'Live SSH requires the operator console (not file://). Open the map from Swiss Tools. Not SNMP.';
        } else {
          liveBtn.disabled = false;
          liveBtn.title = 'Live SSH two-sample collection starts from Swiss Tools with a stored vault credential. This map page does not hold secrets. Not SNMP. Does not certify topology.';
          liveBtn.addEventListener('click', function() {
            window.alert('Start Live SSH utilization from Swiss Tools (Inventory L2) with a vault credential selected. This map page does not hold secrets. Live SSH is not SNMP and does not certify topology.');
          });
          nstPollUtilLiveStatus();
        }
      }
    })();

    function nstPollUtilLiveStatus() {
      if (location.protocol === 'file:') return;
      fetch('/api/utilization-overlay/status', { credentials: 'same-origin' })
        .then(function(r) { return r.ok ? r.json() : null; })
        .then(function(d) {
          if (!d) return;
          var banner = document.getElementById('nst-util-banner');
          if (d.status === 'running' && banner) {
            banner.hidden = false;
            banner.textContent = d.message || 'Live SSH collection in progress — not SNMP. Topology is unchanged.';
          }
        })
        .catch(function() { /* map stays usable */ });
    }
    """
    )
