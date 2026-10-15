"""
utils/l3_map_shell_enhanced.py
------------------------------
Enhanced L3/Flow routing map HTML shell (v7.0.77).

Features (per user spec):
  - Multi-view tabs: Map | Route Explorer | Subnet Table
  - Layout algorithms dropdown: Hierarchical, Force-directed, Circular, Breadth-first
  - VRF filter (dynamic, based on collected data)
  - Search bar: highlight nodes matching hostname/IP
  - Focus mode: click node → 1-hop neighborhood (simple toggle)
  - Path tracing: click two nodes → highlight path (simple, graph-hop)
  - Node detail panel: interface IPs, VRF count, protocol breakdown
  - Connected-only filter: hide subnet nodes, show device↔device only
  - Undiscovered peer indicators: dashed border for ghost nodes
  - Save/restore node positions via localStorage
  - Protocol-aware edge colors from graph_builder
"""

import json
import os
import sys
from typing import Any, Dict

from utils.topo_map_shell import load_vis_script, script_safe_json  # offline-honest; no CDN


def render_l3_map_html_enhanced(
    vis_payload: Dict[str, Any],
    title: str = 'L3 Routing Map',
    subtitle: str = '',
    map_kind: str = 'l3',
) -> str:
    """Render enhanced offline HTML for L3 or flow routing map."""
    import html as _html

    # Use script_safe_json (not bare json.dumps) — prevents </script> breakout
    # from device names/platform strings that contain HTML special characters.
    nodes_json       = script_safe_json(vis_payload.get('nodes') or [])
    edges_json       = script_safe_json(vis_payload.get('edges') or [])
    devices_json     = script_safe_json(vis_payload.get('devices') or {})
    gateways_json    = script_safe_json(vis_payload.get('gateway_analysis') or {})
    subnets_json     = script_safe_json(vis_payload.get('subnet_analysis') or {})
    all_routes_json  = script_safe_json(vis_payload.get('all_routes') or [])
    failed_hosts_json = script_safe_json(vis_payload.get('failed_hosts') or [])
    analysis_json    = script_safe_json(vis_payload.get('analysis') or {})
    map_kind_json    = script_safe_json(map_kind)
    storage_key      = f'nst_l3_positions_{map_kind}'

    # Escape title/subtitle for safe HTML interpolation in <title> and header text
    title_esc    = _html.escape(str(title or 'L3 Routing Map'), quote=True)
    subtitle_esc = _html.escape(str(subtitle or ''), quote=True)

    vis_script = load_vis_script()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title_esc}</title>
    {vis_script}
    <style>
        /* ── Reset & Base ─────────────────────────────────────────────── */
        :root {{
            --bg0: #0a0f1e;
            --bg1: #0f172a;
            --bg2: #1e293b;
            --bg3: #334155;
            --bg4: #475569;
            --tx1: #f1f5f9;
            --tx2: #94a3b8;
            --tx3: #64748b;
            --bdr: #334155;
            --blu: #3b82f6;
            --grn: #10b981;
            --ora: #f59e0b;
            --red: #ef4444;
            --pur: #8b5cf6;
            --cyn: #06b6d4;
            --shadow: 0 4px 20px rgba(0,0,0,0.4);
        }}
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
        /* CRITICAL: body → main → tab-map must form a complete flex height chain */
        html, body {{
            height: 100%;
        }}
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg0);
            color: var(--tx1);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        /* main must propagate height to its flex children */
        main {{
            display: flex;
            flex-direction: column;
            flex: 1 1 0%;
            min-height: 0;
            overflow: hidden;
        }}

        /* ── Header ───────────────────────────────────────────────────── */
        #app-header {{
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            border-bottom: 1px solid #4338ca;
            padding: 10px 18px;
            display: flex;
            align-items: center;
            gap: 16px;
            flex-shrink: 0;
            box-shadow: var(--shadow);
        }}
        #app-header .brand {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        #app-header .brand-icon {{
            width: 34px; height: 34px;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-size: 16px;
        }}
        #app-header h1 {{
            font-size: 16px; font-weight: 700;
            color: #c4b5fd;
            letter-spacing: -0.01em;
        }}
        #app-header h1 span {{ color: var(--tx2); font-weight: 400; font-size: 12px; display: block; margin-top: 1px; }}
        #header-stats {{
            margin-left: auto;
            display: flex; gap: 16px; align-items: center;
        }}
        .hstat {{ text-align: center; }}
        .hstat-val {{ font-size: 18px; font-weight: 700; color: var(--cyn); line-height: 1; }}
        .hstat-lbl {{ font-size: 10px; color: var(--tx3); margin-top: 1px; }}
        .vsep {{ width: 1px; height: 32px; background: var(--bdr); }}

        /* ── Tab Bar ──────────────────────────────────────────────────── */
        #tab-bar {{
            background: var(--bg1);
            border-bottom: 1px solid var(--bdr);
            display: flex;
            gap: 0;
            flex-shrink: 0;
            padding: 0 18px;
        }}
        .tab-btn {{
            padding: 10px 18px;
            font-size: 12px; font-weight: 600;
            color: var(--tx2);
            border: none; background: transparent;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.15s;
            letter-spacing: 0.02em;
        }}
        .tab-btn:hover {{ color: var(--tx1); }}
        .tab-btn.active {{
            color: var(--blu);
            border-bottom-color: var(--blu);
        }}

        /* ── Layout: Map Tab ──────────────────────────────────────────── */
        #tab-map {{
            flex: 1;
            display: flex;
            overflow: hidden;
        }}
        #tab-routes, #tab-subnets {{
            flex: 1;
            display: none;
            overflow: hidden;
            flex-direction: column;
        }}

        /* ── Toolbar (inside map tab) ─────────────────────────────────── */
        #toolbar {{
            background: var(--bg2);
            border-right: 1px solid var(--bdr);
            width: 220px;
            flex-shrink: 0;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
            overflow-x: hidden;
        }}
        .tb-section {{
            border-bottom: 1px solid var(--bdr);
            padding: 12px;
        }}
        .tb-label {{
            font-size: 10px; font-weight: 700;
            color: var(--tx3);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 8px;
        }}
        .tb-select {{
            width: 100%;
            background: var(--bg3);
            border: 1px solid var(--bdr);
            color: var(--tx1);
            padding: 6px 8px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
        }}
        .tb-select:focus {{ outline: none; border-color: var(--blu); }}
        .tb-input {{
            width: 100%;
            background: var(--bg3);
            border: 1px solid var(--bdr);
            color: var(--tx1);
            padding: 6px 8px;
            border-radius: 6px;
            font-size: 12px;
        }}
        .tb-input:focus {{ outline: none; border-color: var(--blu); }}
        .tb-input::placeholder {{ color: var(--tx3); }}
        .tb-btn {{
            width: 100%;
            background: var(--bg3);
            border: 1px solid var(--bdr);
            color: var(--tx1);
            padding: 7px 10px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 11px;
            font-weight: 600;
            text-align: left;
            transition: all 0.15s;
            margin-bottom: 5px;
            display: flex; align-items: center; gap: 6px;
        }}
        .tb-btn:hover {{ background: var(--bg4); border-color: var(--blu); }}
        .tb-btn.active {{ background: var(--blu); border-color: var(--blu); color: #fff; }}
        .tb-btn .icon {{ font-size: 13px; }}
        .tb-hint {{
            font-size: 10px; color: var(--tx3);
            margin-top: 4px; line-height: 1.4;
        }}

        /* VRF checkboxes */
        .vrf-list {{
            max-height: 120px;
            overflow-y: auto;
        }}
        .vrf-item {{
            display: flex; align-items: center; gap: 6px;
            padding: 3px 0;
            font-size: 11px; color: var(--tx2);
            cursor: pointer;
        }}
        .vrf-item input {{ accent-color: var(--blu); cursor: pointer; }}

        /* ── Map Canvas ───────────────────────────────────────────────── */
        #map-wrap {{
            flex: 1;
            position: relative;
            overflow: hidden;
        }}
        #l3-network {{
            width: 100%;
            height: 100%;
            background: var(--bg0);
        }}

        /* Map overlay messages */
        #map-overlay {{
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            pointer-events: none;
            display: none;
        }}
        #map-overlay.visible {{ display: block; }}
        #map-overlay p {{
            font-size: 14px; color: var(--tx2);
        }}

        /* Path trace status bar */
        #path-status {{
            position: absolute;
            bottom: 12px; left: 50%;
            transform: translateX(-50%);
            background: rgba(15,23,42,0.92);
            border: 1px solid var(--blu);
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 12px;
            color: var(--tx1);
            display: none;
            backdrop-filter: blur(4px);
        }}
        #path-status.visible {{ display: block; }}

        /* ── Right Sidebar (detail panel) ─────────────────────────────── */
        #detail-sidebar {{
            width: 280px;
            background: var(--bg2);
            border-left: 1px solid var(--bdr);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            flex-shrink: 0;
        }}
        #detail-sidebar-hdr {{
            padding: 12px 14px;
            border-bottom: 1px solid var(--bdr);
            font-size: 12px; font-weight: 700;
            color: var(--tx2);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            display: flex; align-items: center; justify-content: space-between;
        }}
        #detail-close {{
            cursor: pointer; color: var(--tx3); font-size: 16px;
            background: none; border: none; color: var(--tx3);
        }}
        #detail-close:hover {{ color: var(--tx1); }}
        #detail-content {{
            flex: 1;
            overflow-y: auto;
            padding: 12px;
        }}
        #detail-content::-webkit-scrollbar {{ width: 4px; }}
        #detail-content::-webkit-scrollbar-track {{ background: var(--bg2); }}
        #detail-content::-webkit-scrollbar-thumb {{ background: var(--bg4); border-radius: 2px; }}
        .detail-empty {{
            color: var(--tx3); font-size: 12px; text-align: center;
            margin-top: 40px; line-height: 1.6;
        }}
        .detail-block {{
            background: var(--bg3);
            border-radius: 8px;
            padding: 10px 12px;
            margin-bottom: 10px;
        }}
        .detail-block-title {{
            font-size: 11px; font-weight: 700;
            color: var(--cyn);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 8px;
            display: flex; align-items: center; gap: 6px;
        }}
        .detail-row {{
            display: flex;
            font-size: 11px;
            padding: 3px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            gap: 8px;
        }}
        .detail-row:last-child {{ border-bottom: none; }}
        .detail-key {{ color: var(--tx3); flex-shrink: 0; width: 90px; }}
        .detail-val {{ color: var(--tx1); word-break: break-all; }}
        .proto-pill {{
            display: inline-block;
            padding: 1px 7px;
            border-radius: 10px;
            font-size: 10px; font-weight: 700;
            margin: 1px;
        }}
        .pill-c {{ background: #064e3b; color: #6ee7b7; }}
        .pill-s {{ background: #78350f; color: #fcd34d; }}
        .pill-o {{ background: #1e3a8a; color: #93c5fd; }}
        .pill-b {{ background: #7f1d1d; color: #fca5a5; }}
        .pill-d {{ background: #3b0764; color: #d8b4fe; }}
        .pill-i {{ background: #164e63; color: #67e8f9; }}
        .pill-r {{ background: #7c2d12; color: #fdba74; }}
        .pill-x {{ background: #1f2937; color: #9ca3af; }}

        /* ── Route Explorer Tab ───────────────────────────────────────── */
        #routes-toolbar {{
            display: flex; align-items: center; gap: 10px;
            padding: 10px 16px;
            background: var(--bg2);
            border-bottom: 1px solid var(--bdr);
            flex-shrink: 0;
        }}
        #routes-search {{
            flex: 1; max-width: 300px;
            background: var(--bg3); border: 1px solid var(--bdr);
            color: var(--tx1); padding: 6px 10px;
            border-radius: 6px; font-size: 12px;
        }}
        #routes-search:focus {{ outline: none; border-color: var(--blu); }}
        #routes-search::placeholder {{ color: var(--tx3); }}
        #routes-count {{ font-size: 11px; color: var(--tx3); }}
        #routes-table-wrap {{
            flex: 1; overflow: auto;
        }}
        table.data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
        }}
        table.data-table thead th {{
            background: var(--bg3);
            color: var(--tx2);
            padding: 8px 10px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-size: 10px;
            border-bottom: 1px solid var(--bdr);
            cursor: pointer;
            user-select: none;
            white-space: nowrap;
            position: sticky; top: 0; z-index: 1;
        }}
        table.data-table thead th:hover {{ color: var(--tx1); }}
        table.data-table thead th.sort-asc::after {{ content: ' ↑'; color: var(--blu); }}
        table.data-table thead th.sort-desc::after {{ content: ' ↓'; color: var(--blu); }}
        table.data-table tbody tr {{
            border-bottom: 1px solid rgba(51,65,85,0.5);
            transition: background 0.1s;
        }}
        table.data-table tbody tr:hover {{ background: rgba(51,65,85,0.4); }}
        table.data-table tbody td {{
            padding: 6px 10px;
            color: var(--tx2);
        }}
        table.data-table tbody td.mono {{
            font-family: 'Consolas', 'Courier New', monospace;
            color: var(--tx1);
        }}

        /* ── Subnet Table Tab ─────────────────────────────────────────── */
        #subnets-toolbar {{
            display: flex; align-items: center; gap: 10px;
            padding: 10px 16px;
            background: var(--bg2);
            border-bottom: 1px solid var(--bdr);
            flex-shrink: 0;
        }}
        #subnets-search {{
            flex: 1; max-width: 300px;
            background: var(--bg3); border: 1px solid var(--bdr);
            color: var(--tx1); padding: 6px 10px;
            border-radius: 6px; font-size: 12px;
        }}
        #subnets-search:focus {{ outline: none; border-color: var(--blu); }}
        #subnets-search::placeholder {{ color: var(--tx3); }}
        #subnets-table-wrap {{ flex: 1; overflow: auto; }}

        /* Legend bar */
        #legend-bar {{
            position: absolute;
            bottom: 12px; right: 12px;
            background: rgba(15,23,42,0.88);
            border: 1px solid var(--bdr);
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 10px;
            backdrop-filter: blur(4px);
            display: flex; flex-direction: column; gap: 4px;
            pointer-events: none;
        }}
        .leg-row {{ display: flex; align-items: center; gap: 6px; }}
        .leg-dot {{
            width: 10px; height: 10px; border-radius: 50%;
            flex-shrink: 0;
        }}
        .leg-line {{
            width: 18px; height: 2px; flex-shrink: 0;
        }}
        .leg-lbl {{ color: var(--tx2); }}

        /* Failed hosts banner */
        #failed-banner {{
            position: absolute;
            top: 10px; right: 10px;
            background: rgba(127,29,29,0.85);
            border: 1px solid var(--red);
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 11px;
            max-width: 220px;
            backdrop-filter: blur(4px);
            cursor: pointer;
        }}
        #failed-banner .fb-title {{ color: var(--red); font-weight: 700; margin-bottom: 4px; }}
        #failed-banner .fb-list {{ color: #fca5a5; }}

        #empty-routes-banner {{
            position: absolute;
            left: 50%; top: 42%;
            transform: translate(-50%, -50%);
            z-index: 20;
            max-width: 420px;
            padding: 18px 22px;
            border-radius: 12px;
            border: 1px solid #334155;
            background: rgba(15, 23, 42, 0.94);
            color: #e2e8f0;
            text-align: center;
            font-size: 13px;
            line-height: 1.45;
            box-shadow: 0 12px 40px rgba(0,0,0,0.45);
            display: none;
        }}
        #empty-routes-banner .er-title {{
            font-weight: 750; font-size: 15px; color: #fde68a; margin-bottom: 8px;
        }}
        #empty-routes-banner .er-note {{ color: #94a3b8; font-size: 12px; margin-top: 8px; }}

        /* Scrollbar global */
        ::-webkit-scrollbar {{ width: 5px; height: 5px; }}
        ::-webkit-scrollbar-track {{ background: var(--bg1); }}
        ::-webkit-scrollbar-thumb {{ background: var(--bg4); border-radius: 3px; }}
    </style>
</head>
<body>
<main>

<!-- ═══════════════════════ HEADER ═══════════════════════ -->
<div id="app-header">
    <div class="brand">
        <div class="brand-icon">🗺</div>
        <h1>{title_esc}<span>{subtitle_esc}</span></h1>
    </div>
    <div id="header-stats">
        <div class="hstat"><div class="hstat-val" id="hs-devices">–</div><div class="hstat-lbl">Devices</div></div>
        <div class="vsep"></div>
        <div class="hstat"><div class="hstat-val" id="hs-routes">–</div><div class="hstat-lbl">Routes</div></div>
        <div class="vsep"></div>
        <div class="hstat"><div class="hstat-val" id="hs-gateways">–</div><div class="hstat-lbl">Gateways</div></div>
        <div class="vsep"></div>
        <div class="hstat"><div class="hstat-val" id="hs-subnets">–</div><div class="hstat-lbl">Subnets</div></div>
    </div>
</div>

<!-- ═══════════════════════ TAB BAR ══════════════════════ -->
<div id="tab-bar">
    <button class="tab-btn active" onclick="switchTab('map')">🗺 L3 Routing Map</button>
    <button class="tab-btn" onclick="switchTab('flow')">🌊 Flow Map</button>
    <button class="tab-btn" onclick="switchTab('subnets')">🌐 Subnet Table</button>
    <button class="tab-btn" onclick="switchTab('routes')">📋 Route Explorer</button>
</div>

<!-- ═══════════════════════ MAP TAB ══════════════════════ -->
<div id="tab-map">

    <!-- Left toolbar -->
    <div id="toolbar">

        <!-- Layout -->
        <div class="tb-section">
            <div class="tb-label">Layout</div>
            <select class="tb-select" id="layout-select" onchange="applyLayout(this.value)">
                <option value="hierarchical_ud">Hierarchical ↕</option>
                <option value="hierarchical_lr">Hierarchical ↔</option>
                <option value="force">Force-directed</option>
                <option value="circular">Circular</option>
                <option value="breadthfirst">Breadth-first</option>
            </select>
        </div>

        <!-- Search -->
        <div class="tb-section">
            <div class="tb-label">Search</div>
            <input class="tb-input" id="search-input" type="text"
                   placeholder="hostname or IP…"
                   oninput="onSearch(this.value)">
            <div class="tb-hint" id="search-hint"></div>
        </div>

        <!-- Tools -->
        <div class="tb-section">
            <div class="tb-label">Tools</div>
            <button class="tb-btn" id="btn-focus" onclick="toggleFocusMode()">
                <span class="icon">🔍</span> Focus Mode
            </button>
            <div class="tb-hint">Click a node to isolate its neighbourhood</div>
            <button class="tb-btn" id="btn-path" onclick="togglePathMode()" style="margin-top:8px">
                <span class="icon">↗</span> Path Trace
            </button>
            <div class="tb-hint">Click source then destination node</div>
            <button class="tb-btn" id="btn-reset" onclick="resetView()" style="margin-top:8px">
                <span class="icon">↺</span> Reset View
            </button>
        </div>

        <!-- Filters -->
        <div class="tb-section">
            <div class="tb-label">Filters</div>
            <button class="tb-btn" id="btn-devices-only" onclick="toggleDevicesOnly()">
                <span class="icon">📡</span> Devices Only
            </button>
            <div class="tb-hint">Hide subnet nodes</div>
        </div>

        <!-- VRF Filter -->
        <div class="tb-section" id="vrf-section" style="display:none">
            <div class="tb-label">VRF Filter</div>
            <div class="vrf-list" id="vrf-list"></div>
        </div>

        <!-- Save positions -->
        <div class="tb-section">
            <div class="tb-label">Positions</div>
            <button class="tb-btn" onclick="savePositions()">
                <span class="icon">💾</span> Save Layout
            </button>
            <button class="tb-btn" onclick="clearSavedPositions()">
                <span class="icon">🗑</span> Clear Saved
            </button>
        </div>

    </div><!-- /toolbar -->

    <!-- Map canvas -->
    <div id="map-wrap">
        <div id="l3-network"></div>

        <!-- Empty observation (SSH OK but no routes / no graph) -->
        <div id="empty-routes-banner" role="status" aria-live="polite">
            <div class="er-title">No L3 routing graph to draw</div>
            <div id="er-body">No usable routes were parsed from SSH <code>show ip route</code> / <code>show route</code>.</div>
            <div class="er-note">This is an observation — not invented topology. Check inventory credentials, platform parsers, and that devices have a routing table.</div>
        </div>

        <!-- Failed hosts -->
        <div id="failed-banner" onclick="toggleFailedDetail()" style="display:none">
            <div class="fb-title">⚠ Failed Hosts <span id="fb-count"></span></div>
            <div class="fb-list" id="fb-list"></div>
        </div>

        <!-- Path trace status -->
        <div id="path-status"></div>

        <!-- Legend -->
        <div id="legend-bar">
            <div class="leg-row"><div class="leg-dot" style="background:#3b82f6"></div><div class="leg-lbl">Device</div></div>
            <div class="leg-row"><div class="leg-dot" style="background:#f59e0b"></div><div class="leg-lbl">Gateway</div></div>
            <div class="leg-row"><div class="leg-dot" style="background:#ef4444"></div><div class="leg-lbl">Default GW</div></div>
            <div class="leg-row"><div class="leg-dot" style="background:#8b5cf6"></div><div class="leg-lbl">Subnet</div></div>
            <div style="margin-top:4px;border-top:1px solid rgba(255,255,255,0.1);padding-top:4px">
            <div class="leg-row"><div class="leg-line" style="background:#10b981"></div><div class="leg-lbl">Connected</div></div>
            <div class="leg-row"><div class="leg-line" style="background:#3b82f6"></div><div class="leg-lbl">OSPF</div></div>
            <div class="leg-row"><div class="leg-line" style="background:#ef4444"></div><div class="leg-lbl">BGP</div></div>
            <div class="leg-row"><div class="leg-line" style="background:#f59e0b;border-top:2px dashed #f59e0b;height:0"></div><div class="leg-lbl">Static</div></div>
            <div class="leg-row"><div class="leg-line" style="background:#8b5cf6"></div><div class="leg-lbl">EIGRP</div></div>
            </div>
        </div>
    </div>

    <!-- Right detail sidebar -->
    <div id="detail-sidebar">
        <div id="detail-sidebar-hdr">
            Node Details
            <button id="detail-close" onclick="clearDetail()">✕</button>
        </div>
        <div id="detail-content">
            <div class="detail-empty">Click any node<br>to see details</div>
        </div>
    </div>

</div><!-- /tab-map -->

<!-- ═══════════════════════ FLOW MAP TAB ══════════════════════ -->
<div id="tab-flow" style="display:none; flex:1; align-items:center; justify-content:center; flex-direction:column; color:var(--tx2);">
    <div style="font-size:48px; margin-bottom:16px;">🌊</div>
    <h2>Flow Map</h2>
    <p style="margin-top:8px; max-width:400px; text-align:center;">
        To view the Flow Map, run the <b>Advanced Flow Mapping</b> tool from the Swiss Tools page.
    </p>
</div>

<!-- ═══════════════════════ ROUTE EXPLORER TAB ══════════════════════ -->
<div id="tab-routes">
    <div id="routes-toolbar">
        <input id="routes-search" type="text" placeholder="Filter by device, destination, next-hop, protocol…"
               oninput="filterRoutes(this.value)">
        <span id="routes-count"></span>
    </div>
    <div id="routes-table-wrap">
        <table class="data-table" id="routes-table">
            <thead>
                <tr>
                    <th onclick="sortRoutes('device_id')">Device</th>
                    <th onclick="sortRoutes('destination')">Destination</th>
                    <th onclick="sortRoutes('next_hop')">Next Hop</th>
                    <th onclick="sortRoutes('protocol')">Protocol</th>
                    <th onclick="sortRoutes('interface')">Interface</th>
                    <th onclick="sortRoutes('admin_distance')">AD</th>
                    <th onclick="sortRoutes('vrf')">VRF</th>
                </tr>
            </thead>
            <tbody id="routes-tbody"></tbody>
        </table>
    </div>
</div>

<!-- ═══════════════════════ SUBNET TABLE TAB ══════════════════════ -->
<div id="tab-subnets">
    <div id="subnets-toolbar">
        <input id="subnets-search" type="text" placeholder="Filter subnets…"
               oninput="filterSubnets(this.value)">
        <span id="subnets-count"></span>
    </div>
    <div id="subnets-table-wrap">
        <table class="data-table" id="subnets-table">
            <thead>
                <tr>
                    <th onclick="sortSubnets('subnet')">Subnet</th>
                    <th onclick="sortSubnets('prefix_len')">Prefix</th>
                    <th onclick="sortSubnets('route_count')">Routes</th>
                    <th onclick="sortSubnets('gateways')">Gateways</th>
                    <th onclick="sortSubnets('devices')">Devices</th>
                    <th onclick="sortSubnets('protocols')">Protocols</th>
                    <th onclick="sortSubnets('is_private')">Scope</th>
                    <th onclick="sortSubnets('is_shared')">Segment</th>
                </tr>
            </thead>
            <tbody id="subnets-tbody"></tbody>
        </table>
    </div>
</div>

<script>
/* ═══════════════════════════════════════════════════════════════════
   DATA
═══════════════════════════════════════════════════════════════════ */
const RAW_NODES    = {nodes_json};
const RAW_EDGES    = {edges_json};
const DEVICES_META = {devices_json};
const GW_META      = {gateways_json};
const SN_META      = {subnets_json};
const ALL_ROUTES   = {all_routes_json};
const FAILED_HOSTS = {failed_hosts_json};
const ANALYSIS     = {analysis_json};
const MAP_KIND     = {map_kind_json};
const STORAGE_KEY  = '{storage_key}';

/* ═══════════════════════════════════════════════════════════════════
   GLOBALS
═══════════════════════════════════════════════════════════════════ */
let network = null;
let nodesDataset = null;
let edgesDataset = null;
let selectedNode = null;
let focusModeActive = false;
let pathModeActive = false;
let pathSource = null;
let devicesOnlyActive = false;
let activeVrfs = new Set(['all']);
let allVrfs = new Set();

// Route explorer state
let routesSortCol = 'device_id';
let routesSortAsc = true;
let routesFilter  = '';
let subnetsSortCol = 'subnet';
let subnetsSortAsc = true;
let subnetsFilter  = '';

/* ═══════════════════════════════════════════════════════════════════
   INIT
═══════════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', init);

function init() {{
    updateHeaderStats();
    buildVrfFilter();
    showFailedHosts();
    showEmptyRoutesBanner();
    buildRoutesTable();
    buildSubnetsTable();
    initNetwork();
}}

function updateHeaderStats() {{
    const devCount = RAW_NODES.filter(n => n.group === 'device').length;
    const gwCount  = RAW_NODES.filter(n => n.group === 'gateway' || n.group === 'default_gateway').length;
    const snCount  = RAW_NODES.filter(n => n.group === 'subnet').length;
    document.getElementById('hs-devices').textContent   = devCount;
    document.getElementById('hs-routes').textContent    = ALL_ROUTES.length.toLocaleString();
    document.getElementById('hs-gateways').textContent  = gwCount;
    document.getElementById('hs-subnets').textContent   = snCount;
}}

function showEmptyRoutesBanner() {{
    const el = document.getElementById('empty-routes-banner');
    if (!el) return;
    const noRoutes = !ALL_ROUTES || ALL_ROUTES.length === 0;
    const noNodes = !RAW_NODES || RAW_NODES.length === 0;
    const onlyDevicesNoGraph = noRoutes && RAW_NODES.length > 0
        && RAW_NODES.every(n => n.group === 'device');
    if (!noRoutes && !noNodes) {{
        el.style.display = 'none';
        return;
    }}
    el.style.display = 'block';
    const body = document.getElementById('er-body');
    if (!body) return;
    if (noNodes) {{
        body.textContent = 'No devices or routes in this offline map payload. Re-run L3 Routing Map from Swiss Tools with vault credential_id + inventory scope.';
    }} else if (onlyDevicesNoGraph) {{
        body.textContent = 'Devices were reachable over SSH, but zero usable routes were parsed — showing device markers only (not invented links).';
    }} else {{
        body.textContent = 'No usable routes were parsed from SSH show ip route / show route.';
    }}
}}

function buildVrfFilter() {{
    ALL_ROUTES.forEach(r => {{ if (r.vrf && r.vrf !== 'default') allVrfs.add(r.vrf); }});
    const sec = document.getElementById('vrf-section');
    const lst = document.getElementById('vrf-list');
    if (allVrfs.size === 0) return;
    sec.style.display = 'block';
    // "All" option
    const allItem = document.createElement('label');
    allItem.className = 'vrf-item';
    allItem.innerHTML = `<input type="checkbox" id="vrf-all" checked onchange="onVrfAll(this)"> <span>All VRFs</span>`;
    lst.appendChild(allItem);
    allVrfs.forEach(vrf => {{
        activeVrfs.add(vrf);
        const item = document.createElement('label');
        item.className = 'vrf-item';
        item.innerHTML = `<input type="checkbox" class="vrf-cb" data-vrf="${{vrf}}" checked onchange="onVrfChange()"> <span>${{vrf}}</span>`;
        lst.appendChild(item);
    }});
}}

function onVrfAll(cb) {{
    document.querySelectorAll('.vrf-cb').forEach(el => el.checked = cb.checked);
    if (cb.checked) {{
        activeVrfs = new Set(['all', ...allVrfs]);
    }} else {{
        activeVrfs = new Set();
    }}
    applyVrfFilter();
}}

function onVrfChange() {{
    activeVrfs = new Set(['all']);
    document.querySelectorAll('.vrf-cb').forEach(el => {{
        if (el.checked) activeVrfs.add(el.dataset.vrf);
    }});
    const allCb = document.getElementById('vrf-all');
    if (allCb) allCb.checked = activeVrfs.size > allVrfs.size;
    applyVrfFilter();
}}

function applyVrfFilter() {{
    if (!nodesDataset) return;
    // Nodes are never hidden by VRF directly (they may serve multiple VRFs)
    // Instead dim edges that carry routes only in hidden VRFs
    // Simple approach: just update visible state
    applyAllFilters();
}}

function showFailedHosts() {{
    if (!FAILED_HOSTS || FAILED_HOSTS.length === 0) return;
    const banner = document.getElementById('failed-banner');
    banner.style.display = 'block';
    document.getElementById('fb-count').textContent = `(${{FAILED_HOSTS.length}})`;
    const max = 5;
    const shown = FAILED_HOSTS.slice(0, max);
    document.getElementById('fb-list').textContent = shown.join(', ') + (FAILED_HOSTS.length > max ? ` +${{FAILED_HOSTS.length - max}} more` : '');
}}

function toggleFailedDetail() {{
    const el = document.getElementById('fb-list');
    el.textContent = FAILED_HOSTS.join(', ');
}}

/* ═══════════════════════════════════════════════════════════════════
   NETWORK INIT
═══════════════════════════════════════════════════════════════════ */
function initNetwork() {{
    const container = document.getElementById('l3-network');

    /* Safety net: if the flex height chain collapsed to 0, force a minimum height. */
    if (container && container.offsetHeight < 10) {{
        container.style.minHeight = '600px';
        console.warn('L3 enhanced map: container had 0 height — applied 600px fallback');
    }}

    // Load saved positions
    const savedPos = loadSavedPositions();

    // Build nodes
    const nodeData = RAW_NODES.map(n => {{
        const base = buildNodeVisuals(n);
        if (savedPos && savedPos[n.id]) {{
            base.x = savedPos[n.id].x;
            base.y = savedPos[n.id].y;
            base.fixed = false;
        }}
        return base;
    }});

    // Build edges
    const edgeData = RAW_EDGES.map((e, idx) => {{
        return buildEdgeVisuals(e, idx);
    }});

    nodesDataset = new vis.DataSet(nodeData);
    edgesDataset = new vis.DataSet(edgeData);

    const options = getLayoutOptions('hierarchical_ud');

    network = new vis.Network(container, {{ nodes: nodesDataset, edges: edgesDataset }}, options);

    network.on('click', onNetworkClick);
    network.on('stabilizationIterationsDone', () => {{
        network.setOptions({{ physics: {{ enabled: false }} }});
        /* Redraw after stabilization in case container was resized from 0px */
        network.redraw();
        if (!savedPos) network.fit({{ animation: {{ duration: 600, easingFunction: 'easeInOutQuad' }} }});
    }});
}}

function buildNodeVisuals(n) {{
    const colors = {{
        device:          {{ background: '#1e3a5f', border: '#3b82f6', highlight: {{ background: '#2563eb', border: '#60a5fa' }} }},
        gateway:         {{ background: '#451a03', border: '#f59e0b', highlight: {{ background: '#78350f', border: '#fbbf24' }} }},
        default_gateway: {{ background: '#450a0a', border: '#ef4444', highlight: {{ background: '#7f1d1d', border: '#f87171' }} }},
        subnet:          {{ background: '#2e1065', border: '#8b5cf6', highlight: {{ background: '#4c1d95', border: '#a78bfa' }} }},
    }};
    const shapes = {{
        device: 'box', gateway: 'dot',
        default_gateway: 'dot', subnet: 'ellipse',
    }};
    const sizes = {{
        device: 28, gateway: 20, default_gateway: 24, subnet: 18,
    }};
    const g = n.group || 'device';
    const color = colors[g] || colors.device;
    const shape = shapes[g] || 'box';
    const size  = sizes[g]  || 20;

    // Short label
    let lbl = n.label || n.id || '';
    if (lbl.length > 20) {{
        lbl = lbl.includes('.') ? lbl.split('.')[0] : lbl.substring(0, 17) + '…';
    }}

    const node = {{
        id: n.id, label: lbl, group: g,
        title: n.title || n.id,
        color, shape, size,
        font: {{ color: '#e2e8f0', size: 12, bold: g === 'device' }},
        _ghost: n._ghost || false,
        _protocols: n._protocols || [],
        _vrfs: n._vrfs || [],
    }};

    // Ghost / undiscovered peer → dashed border
    if (n._ghost || n.borderDashes) {{
        node.shapeProperties = {{ borderDashes: [5, 5] }};
        node.color.border = '#475569';
        node.opacity = 0.7;
    }}

    return node;
}}

function buildEdgeVisuals(e, idx) {{
    return {{
        id: `e${{idx}}`,
        from: e.from, to: e.to,
        label: e.label || '',
        title: e.title || `${{e.from}} → ${{e.to}}`,
        color: e.color || {{ color: '#475569', opacity: 0.7 }},
        width: e.width || 1,
        arrows: e.arrows || 'to',
        dashes: e.dashes || false,
        font: {{ color: '#64748b', size: 9, align: 'middle' }},
        smooth: {{ type: 'curvedCW', roundness: 0.1 }},
        _protocol: e.protocol || '',
    }};
}}

/* ═══════════════════════════════════════════════════════════════════
   LAYOUT
═══════════════════════════════════════════════════════════════════ */
function getLayoutOptions(layout) {{
    const base = {{
        interaction: {{ hover: true, zoomView: true, dragView: true, tooltipDelay: 200 }},
        nodes: {{ borderWidth: 2, shadow: {{ enabled: true, size: 8, color: 'rgba(0,0,0,0.3)' }} }},
        edges: {{ smooth: {{ type: 'dynamic' }} }},
    }};

    switch (layout) {{
        case 'hierarchical_ud':
            return {{ ...base,
                layout: {{ hierarchical: {{ enabled: true, direction: 'UD', levelSeparation: 220,
                    nodeSpacing: 120, sortMethod: 'directed', shakeTowards: 'leaves' }} }},
                physics: {{ enabled: true, hierarchicalRepulsion: {{ nodeDistance: 160 }} }}
            }};
        case 'hierarchical_lr':
            return {{ ...base,
                layout: {{ hierarchical: {{ enabled: true, direction: 'LR', levelSeparation: 280,
                    nodeSpacing: 100, sortMethod: 'directed' }} }},
                physics: {{ enabled: true, hierarchicalRepulsion: {{ nodeDistance: 120 }} }}
            }};
        case 'force':
            return {{ ...base,
                layout: {{ hierarchical: {{ enabled: false }} }},
                physics: {{ enabled: true,
                    forceAtlas2Based: {{ gravitationalConstant: -80, centralGravity: 0.01,
                        springLength: 160, springConstant: 0.05 }},
                    solver: 'forceAtlas2Based', stabilization: {{ iterations: 200 }}
                }}
            }};
        case 'circular':
            return {{ ...base,
                layout: {{ hierarchical: {{ enabled: false }} }},
                physics: {{ enabled: true,
                    repulsion: {{ nodeDistance: 160, centralGravity: 0.5, springLength: 200 }},
                    solver: 'repulsion', stabilization: {{ iterations: 150 }}
                }}
            }};
        case 'breadthfirst':
            return {{ ...base,
                layout: {{ hierarchical: {{ enabled: true, direction: 'UD', levelSeparation: 180,
                    nodeSpacing: 100, sortMethod: 'hubsize' }} }},
                physics: {{ enabled: true, hierarchicalRepulsion: {{ nodeDistance: 130 }} }}
            }};
        default:
            return base;
    }}
}}

function applyLayout(layout) {{
    if (!network) return;
    clearFocusMode();
    clearPathMode();
    const opts = getLayoutOptions(layout);
    network.setOptions(opts);
    network.setOptions({{ physics: {{ enabled: true }} }});
    network.stabilize();
}}

/* ═══════════════════════════════════════════════════════════════════
   SEARCH
═══════════════════════════════════════════════════════════════════ */
function onSearch(q) {{
    if (!nodesDataset) return;
    const hint = document.getElementById('search-hint');
    q = (q || '').trim().toLowerCase();
    if (!q) {{
        nodesDataset.forEach(n => nodesDataset.update({{ id: n.id, borderWidth: 2 }}));
        hint.textContent = '';
        return;
    }}
    let hits = 0;
    nodesDataset.forEach(n => {{
        const match = (n.id || '').toLowerCase().includes(q) ||
                      (n.label || '').toLowerCase().includes(q);
        nodesDataset.update({{
            id: n.id,
            borderWidth: match ? 5 : 1,
            color: match
                ? {{ border: '#06b6d4' }}
                : undefined,
        }});
        if (match) hits++;
    }});
    hint.textContent = hits ? `${{hits}} match${{hits > 1 ? 'es' : ''}}` : 'No matches';
    if (hits > 0) {{
        // Zoom to first match
        const first = nodesDataset.get({{ filter: n =>
            (n.id || '').toLowerCase().includes(q) || (n.label || '').toLowerCase().includes(q)
        }})[0];
        if (first) network.focus(first.id, {{ scale: 1.2, animation: true }});
    }}
}}

/* ═══════════════════════════════════════════════════════════════════
   FILTERS
═══════════════════════════════════════════════════════════════════ */
function applyAllFilters() {{
    if (!nodesDataset) return;
    nodesDataset.forEach(n => {{
        let hidden = false;
        // Devices-only: hide subnet nodes
        if (devicesOnlyActive && n.group === 'subnet') hidden = true;
        nodesDataset.update({{ id: n.id, hidden }});
    }});
    // Hide edges connected to hidden nodes
    if (edgesDataset) {{
        const hiddenNodes = new Set(nodesDataset.get({{ filter: n => n.hidden }}).map(n => n.id));
        edgesDataset.forEach(e => {{
            edgesDataset.update({{ id: e.id, hidden: hiddenNodes.has(e.from) || hiddenNodes.has(e.to) }});
        }});
    }}
}}

function toggleDevicesOnly() {{
    devicesOnlyActive = !devicesOnlyActive;
    const btn = document.getElementById('btn-devices-only');
    btn.classList.toggle('active', devicesOnlyActive);
    applyAllFilters();
}}

/* ═══════════════════════════════════════════════════════════════════
   FOCUS MODE
═══════════════════════════════════════════════════════════════════ */
function toggleFocusMode() {{
    focusModeActive = !focusModeActive;
    document.getElementById('btn-focus').classList.toggle('active', focusModeActive);
    if (!focusModeActive) {{
        clearFocusMode();
    }} else {{
        setPathStatus('Focus mode ON — click a node to isolate it');
    }}
    // Disable path mode if enabling focus
    if (focusModeActive && pathModeActive) {{
        pathModeActive = false;
        document.getElementById('btn-path').classList.remove('active');
        clearPathMode();
    }}
}}

function clearFocusMode() {{
    if (!nodesDataset) return;
    nodesDataset.forEach(n => nodesDataset.update({{ id: n.id, hidden: false }}));
    if (edgesDataset) edgesDataset.forEach(e => edgesDataset.update({{ id: e.id, hidden: false }}));
    applyAllFilters();
    clearPathStatus();
}}

function applyFocus(nodeId) {{
    if (!network || !nodesDataset) return;
    const connected = new Set(network.getConnectedNodes(nodeId));
    connected.add(nodeId);
    nodesDataset.forEach(n => {{
        const hide = !connected.has(n.id);
        nodesDataset.update({{ id: n.id, hidden: hide }});
    }});
    if (edgesDataset) {{
        edgesDataset.forEach(e => {{
            const hide = !connected.has(e.from) || !connected.has(e.to);
            edgesDataset.update({{ id: e.id, hidden: hide }});
        }});
    }}
    setPathStatus(`Focused on: ${{nodeId}} — ${{connected.size - 1}} neighbours`);
}}

/* ═══════════════════════════════════════════════════════════════════
   PATH TRACE
═══════════════════════════════════════════════════════════════════ */
function togglePathMode() {{
    pathModeActive = !pathModeActive;
    document.getElementById('btn-path').classList.toggle('active', pathModeActive);
    if (!pathModeActive) {{
        clearPathMode();
    }} else {{
        pathSource = null;
        setPathStatus('Path Trace: click source node…');
    }}
    if (pathModeActive && focusModeActive) {{
        focusModeActive = false;
        document.getElementById('btn-focus').classList.remove('active');
        clearFocusMode();
    }}
}}

function clearPathMode() {{
    pathSource = null;
    // Restore all edge/node colors
    if (nodesDataset) nodesDataset.forEach(n => nodesDataset.update({{ id: n.id, borderWidth: 2 }}));
    if (edgesDataset) edgesDataset.forEach(e => edgesDataset.update({{ id: e.id, color: e._origColor || e.color, width: e.width }}));
    clearPathStatus();
}}

function tracePath(srcId, dstId) {{
    if (!network) return;
    // Use vis.js getConnectedEdges + BFS for simple path finding
    const path = bfsPath(srcId, dstId);
    if (!path) {{
        setPathStatus(`No path found: ${{srcId}} → ${{dstId}}`);
        return;
    }}
    const pathNodeSet = new Set(path);
    // Highlight path nodes
    nodesDataset.forEach(n => {{
        nodesDataset.update({{ id: n.id, borderWidth: pathNodeSet.has(n.id) ? 5 : 1 }});
    }});
    // Highlight path edges
    if (edgesDataset) {{
        edgesDataset.forEach(e => {{
            const onPath = pathNodeSet.has(e.from) && pathNodeSet.has(e.to);
            edgesDataset.update({{
                id: e.id,
                color: onPath ? {{ color: '#06b6d4', opacity: 1 }} : {{ color: '#1e293b', opacity: 0.2 }},
                width: onPath ? 4 : 1,
            }});
        }});
    }}
    setPathStatus(`Path: ${{path.join(' → ')}} (${{path.length - 1}} hop${{path.length > 2 ? 's' : ''}})`);
}}

function bfsPath(src, dst) {{
    // BFS over nodesDataset/edgesDataset
    const adj = {{}};
    nodesDataset.forEach(n => {{ adj[n.id] = []; }});
    edgesDataset.forEach(e => {{
        if (adj[e.from]) adj[e.from].push(e.to);
        if (adj[e.to])   adj[e.to].push(e.from);
    }});
    const prev = {{}};
    const visited = new Set([src]);
    const queue = [src];
    while (queue.length) {{
        const cur = queue.shift();
        if (cur === dst) {{
            // Reconstruct path
            const path = [];
            let node = dst;
            while (node !== undefined) {{ path.unshift(node); node = prev[node]; }}
            return path;
        }}
        for (const nb of (adj[cur] || [])) {{
            if (!visited.has(nb)) {{
                visited.add(nb);
                prev[nb] = cur;
                queue.push(nb);
            }}
        }}
    }}
    return null;
}}

/* ═══════════════════════════════════════════════════════════════════
   CLICK HANDLER
═══════════════════════════════════════════════════════════════════ */
function onNetworkClick(params) {{
    if (params.nodes.length > 0) {{
        const nodeId = params.nodes[0];
        selectedNode = nodeId;

        if (pathModeActive) {{
            if (!pathSource) {{
                pathSource = nodeId;
                setPathStatus(`Path Trace: source = ${{nodeId}} — now click destination…`);
                nodesDataset.update({{ id: nodeId, borderWidth: 5 }});
            }} else if (pathSource !== nodeId) {{
                tracePath(pathSource, nodeId);
                pathSource = null;
            }}
            return;
        }}

        if (focusModeActive) {{
            applyFocus(nodeId);
            return;
        }}

        showNodeDetail(nodeId);
    }} else {{
        // Click empty — clear selection
        if (!focusModeActive && !pathModeActive) {{
            clearDetail();
        }}
    }}
}}

/* ═══════════════════════════════════════════════════════════════════
   NODE DETAIL
═══════════════════════════════════════════════════════════════════ */
function showNodeDetail(nodeId) {{
    const nodeRaw = RAW_NODES.find(n => n.id === nodeId);
    if (!nodeRaw) return;
    const g = nodeRaw.group || 'device';
    const panel = document.getElementById('detail-content');

    let html = '';

    if (g === 'device') {{
        const meta = DEVICES_META[nodeId] || {{}};
        const protos = (meta.protocols || []);
        const ifaces = meta.interfaces || {{}};
        const vrfs   = meta.vrf_names || [];
        const routes = meta.route_count || 0;
        const routesByProto = meta.route_count_by_protocol || {{}};

        html += `<div class="detail-block">
            <div class="detail-block-title">📡 Device</div>
            <div class="detail-row"><div class="detail-key">Hostname</div><div class="detail-val">${{nodeId}}</div></div>
            <div class="detail-row"><div class="detail-key">Platform</div><div class="detail-val">${{meta.platform || '—'}}</div></div>
            <div class="detail-row"><div class="detail-key">Mgmt IP</div><div class="detail-val">${{meta.management_ip || nodeId}}</div></div>
            <div class="detail-row"><div class="detail-key">SSH Port</div><div class="detail-val">${{meta.ssh_port || 22}}</div></div>
            <div class="detail-row"><div class="detail-key">Routes</div><div class="detail-val">${{routes}}</div></div>
            <div class="detail-row"><div class="detail-key">VRFs</div><div class="detail-val">${{vrfs.length > 0 ? vrfs.join(', ') : 'default only'}}</div></div>
            <div class="detail-row"><div class="detail-key">Default GW</div><div class="detail-val">${{meta.default_gateway || '—'}}</div></div>
        </div>`;

        // Protocols
        if (protos.length) {{
            html += `<div class="detail-block">
                <div class="detail-block-title">🔀 Routing Protocols</div>`;
            protos.forEach(p => {{
                const cnt = routesByProto[p] || 0;
                html += `<div class="detail-row"><div class="detail-key">${{protoPill(p)}}</div><div class="detail-val">${{cnt}} routes</div></div>`;
            }});
            html += `</div>`;
        }}

        // Interfaces
        if (Object.keys(ifaces).length > 0) {{
            html += `<div class="detail-block">
                <div class="detail-block-title">🔌 Interfaces</div>`;
            Object.entries(ifaces).slice(0, 15).forEach(([iface, subnet]) => {{
                html += `<div class="detail-row"><div class="detail-key" style="font-family:monospace">${{iface}}</div><div class="detail-val">${{subnet}}</div></div>`;
            }});
            html += `</div>`;
        }}

        // Local IPs
        const localIPs = meta.local_ips || [];
        if (localIPs.length > 0) {{
            html += `<div class="detail-block">
                <div class="detail-block-title">🏷 Local IPs</div>
                ${{localIPs.slice(0, 10).map(ip => `<div class="detail-row"><div class="detail-val" style="font-family:monospace">${{ip}}</div></div>`).join('')}}
            </div>`;
        }}

        // BGP/OSPF Peers placeholder logic
        const peers = meta.bgp_ospf_peers || [];
        if (peers.length > 0) {{
            html += `<div class="detail-block">
                <div class="detail-block-title">🤝 BGP/OSPF Peers</div>
                ${{peers.slice(0, 10).map(p => `<div class="detail-row"><div class="detail-val" style="font-family:monospace">${{p}}</div></div>`).join('')}}
            </div>`;
        }}

        // Errors
        const errs = meta.errors || [];
        if (errs.length > 0) {{
            html += `<div class="detail-block" style="border:1px solid #7f1d1d">
                <div class="detail-block-title" style="color:#f87171">⚠ Errors (${{errs.length}})</div>
                ${{errs.slice(0, 5).map(e => `<div style="font-size:10px;color:#fca5a5;padding:2px 0">${{e}}</div>`).join('')}}
            </div>`;
        }}

    }} else if (g === 'gateway' || g === 'default_gateway') {{
        const meta = GW_META[nodeId] || {{}};
        html += `<div class="detail-block">
            <div class="detail-block-title">${{g === 'default_gateway' ? '🌐 Default Gateway' : '🔀 Gateway'}}</div>
            <div class="detail-row"><div class="detail-key">IP</div><div class="detail-val">${{nodeId}}</div></div>
            <div class="detail-row"><div class="detail-key">Subnets</div><div class="detail-val">${{meta.subnet_count || 0}}</div></div>
            <div class="detail-row"><div class="detail-key">Seen from</div><div class="detail-val">${{(meta.routing_devices || []).length}} device(s)</div></div>
            <div class="detail-row"><div class="detail-key">Protocols</div><div class="detail-val">${{(meta.protocols || []).join(', ') || '—'}}</div></div>
            ${{g === 'default_gateway' ? '<div class="detail-row"><div class="detail-val" style="color:#ef4444;font-weight:700">Default Route Provider</div></div>' : ''}}
        </div>`;

        const devices = meta.routing_devices || [];
        if (devices.length) {{
            html += `<div class="detail-block">
                <div class="detail-block-title">📡 Routing Devices</div>
                ${{devices.map(d => `<div class="detail-row"><div class="detail-val">${{d}}</div></div>`).join('')}}
            </div>`;
        }}

        const subnets = meta.subnets || [];
        if (subnets.length) {{
            html += `<div class="detail-block">
                <div class="detail-block-title">🌐 Served Subnets (top 10)</div>
                ${{subnets.slice(0, 10).map(s => `<div class="detail-row"><div class="detail-val" style="font-family:monospace">${{s}}</div></div>`).join('')}}
            </div>`;
        }}

    }} else if (g === 'subnet') {{
        const meta = SN_META[nodeId] || {{}};
        html += `<div class="detail-block">
            <div class="detail-block-title">🌐 Subnet</div>
            <div class="detail-row"><div class="detail-key">Prefix</div><div class="detail-val" style="font-family:monospace">${{nodeId}}</div></div>
            <div class="detail-row"><div class="detail-key">Prefix len</div><div class="detail-val">/${{meta.prefix_len || '?'}}</div></div>
            <div class="detail-row"><div class="detail-key">Addresses</div><div class="detail-val">${{(meta.subnet_size || 0).toLocaleString()}}</div></div>
            <div class="detail-row"><div class="detail-key">Scope</div><div class="detail-val">${{meta.is_private ? 'Private (RFC1918)' : 'Public'}}</div></div>
            <div class="detail-row"><div class="detail-key">Routes</div><div class="detail-val">${{meta.route_count || 0}}</div></div>
            <div class="detail-row"><div class="detail-key">Segment</div><div class="detail-val">${{meta.is_shared_segment ? '✅ Shared LAN' : 'Point-to-point'}}</div></div>
        </div>`;

        const gws = meta.gateway_ips || [];
        if (gws.length) {{
            html += `<div class="detail-block">
                <div class="detail-block-title">🔀 Gateways</div>
                ${{gws.map(g => `<div class="detail-row"><div class="detail-val" style="font-family:monospace">${{g}}</div></div>`).join('')}}
            </div>`;
        }}

        const devs = meta.advertising_devices || [];
        if (devs.length) {{
            html += `<div class="detail-block">
                <div class="detail-block-title">📡 Devices</div>
                ${{devs.map(d => `<div class="detail-row"><div class="detail-val">${{d}}</div></div>`).join('')}}
            </div>`;
        }}
    }}

    // Bottom: focus button
    html += `<button onclick="applyFocus('${{nodeId}}')" style="width:100%;padding:8px;margin-top:8px;background:#1e3a5f;border:1px solid #3b82f6;color:#93c5fd;border-radius:6px;cursor:pointer;font-size:11px">
        🔍 Focus on this node
    </button>`;

    panel.innerHTML = html;
}}

function clearDetail() {{
    document.getElementById('detail-content').innerHTML =
        '<div class="detail-empty">Click any node<br>to see details</div>';
}}

function protoPill(p) {{
    const cls = {{
        'Connected': 'pill-c', 'Local': 'pill-c',
        'Static': 'pill-s',
        'OSPF': 'pill-o', 'OSPF-InterArea': 'pill-o',
        'BGP': 'pill-b',
        'EIGRP': 'pill-d', 'EIGRP-External': 'pill-d',
        'ISIS': 'pill-i',
        'RIP': 'pill-r',
    }};
    return `<span class="proto-pill ${{cls[p] || 'pill-x'}}">${{p}}</span>`;
}}

/* ═══════════════════════════════════════════════════════════════════
   RESET VIEW
═══════════════════════════════════════════════════════════════════ */
function resetView() {{
    if (!network) return;
    clearFocusMode();
    clearPathMode();
    focusModeActive = false;
    pathModeActive = false;
    devicesOnlyActive = false;
    document.getElementById('btn-focus').classList.remove('active');
    document.getElementById('btn-path').classList.remove('active');
    document.getElementById('btn-devices-only').classList.remove('active');
    document.getElementById('search-input').value = '';
    onSearch('');
    network.fit({{ animation: {{ duration: 600, easingFunction: 'easeInOutQuad' }} }});
}}

/* ═══════════════════════════════════════════════════════════════════
   POSITION PERSISTENCE
═══════════════════════════════════════════════════════════════════ */
function savePositions() {{
    if (!network) return;
    const positions = network.getPositions();
    try {{
        localStorage.setItem(STORAGE_KEY, JSON.stringify(positions));
        setPathStatus('Layout saved ✓', 2000);
    }} catch(e) {{
        setPathStatus('Save failed: ' + e.message, 2000);
    }}
}}

function loadSavedPositions() {{
    try {{
        const raw = localStorage.getItem(STORAGE_KEY);
        return raw ? JSON.parse(raw) : null;
    }} catch(e) {{
        return null;
    }}
}}

function clearSavedPositions() {{
    try {{
        localStorage.removeItem(STORAGE_KEY);
        setPathStatus('Saved positions cleared ✓', 2000);
    }} catch(e) {{}}
}}

/* ═══════════════════════════════════════════════════════════════════
   PATH STATUS BAR
═══════════════════════════════════════════════════════════════════ */
function setPathStatus(msg, autoDismissMs) {{
    const el = document.getElementById('path-status');
    el.textContent = msg;
    el.classList.add('visible');
    if (autoDismissMs) setTimeout(clearPathStatus, autoDismissMs);
}}

function clearPathStatus() {{
    const el = document.getElementById('path-status');
    el.classList.remove('visible');
    el.textContent = '';
}}

/* ═══════════════════════════════════════════════════════════════════
   TAB SWITCHING
═══════════════════════════════════════════════════════════════════ */
function switchTab(tab) {{
    document.querySelectorAll('.tab-btn').forEach((b, i) => {{
        b.classList.toggle('active', ['map', 'routes', 'subnets'][i] === tab);
    }});
    document.getElementById('tab-map').style.display    = tab === 'map'     ? 'flex' : 'none';
    document.getElementById('tab-routes').style.display = tab === 'routes'  ? 'flex' : 'none';
    document.getElementById('tab-subnets').style.display= tab === 'subnets' ? 'flex' : 'none';

    if (tab === 'map' && network) {{
        setTimeout(() => network.redraw(), 50);
    }}
}}

/* ═══════════════════════════════════════════════════════════════════
   ROUTE EXPLORER
═══════════════════════════════════════════════════════════════════ */
function buildRoutesTable() {{
    renderRoutes();
}}

function getFilteredRoutes() {{
    const q = routesFilter.toLowerCase();
    return ALL_ROUTES.filter(r => {{
        if (!q) return true;
        return (r.device_id || '').toLowerCase().includes(q) ||
               (r.destination || '').toLowerCase().includes(q) ||
               (r.next_hop || '').toLowerCase().includes(q) ||
               (r.protocol || '').toLowerCase().includes(q) ||
               (r.interface || '').toLowerCase().includes(q) ||
               (r.vrf || '').toLowerCase().includes(q);
    }}).sort((a, b) => {{
        const va = (a[routesSortCol] || '').toString();
        const vb = (b[routesSortCol] || '').toString();
        return routesSortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
    }});
}}

function renderRoutes() {{
    const rows = getFilteredRoutes();
    document.getElementById('routes-count').textContent = `${{rows.length.toLocaleString()}} routes`;
    const tbody = document.getElementById('routes-tbody');
    const BATCH = 1000;
    const shown = rows.slice(0, BATCH);
    tbody.innerHTML = shown.map(r => `
        <tr>
            <td class="mono">${{esc(r.device_id || '—')}}</td>
            <td class="mono">${{esc(r.destination || '—')}}</td>
            <td class="mono">${{esc(r.next_hop || 'direct')}}</td>
            <td>${{protoPill(r.protocol || '?')}}</td>
            <td class="mono">${{esc(r.interface || '—')}}</td>
            <td>${{esc(r.admin_distance || '—')}}</td>
            <td>${{esc(r.vrf || 'default')}}</td>
        </tr>`).join('');
    if (rows.length > BATCH) {{
        const tr = document.createElement('tr');
        tr.innerHTML = `<td colspan="7" style="text-align:center;color:#64748b;padding:10px">
            … ${{(rows.length - BATCH).toLocaleString()}} more rows (refine filter to see all)
        </td>`;
        tbody.appendChild(tr);
    }}

    // Update sort indicators
    document.querySelectorAll('#routes-table thead th').forEach((th, i) => {{
        const cols = ['device_id','destination','next_hop','protocol','interface','admin_distance','vrf'];
        th.className = (cols[i] === routesSortCol) ? (routesSortAsc ? 'sort-asc' : 'sort-desc') : '';
    }});
}}

function filterRoutes(q) {{
    routesFilter = q;
    renderRoutes();
}}

function sortRoutes(col) {{
    if (routesSortCol === col) routesSortAsc = !routesSortAsc;
    else {{ routesSortCol = col; routesSortAsc = true; }}
    renderRoutes();
}}

/* ═══════════════════════════════════════════════════════════════════
   SUBNET TABLE
═══════════════════════════════════════════════════════════════════ */
function buildSubnetsTable() {{
    renderSubnets();
}}

function getSubnetRows() {{
    const q = subnetsFilter.toLowerCase();
    const rows = Object.entries(SN_META).map(([k, v]) => ({{
        subnet: k,
        prefix_len: v.prefix_len || 0,
        route_count: v.route_count || 0,
        gateways: (v.gateway_ips || []).join(', '),
        devices: (v.advertising_devices || []).join(', '),
        protocols: (v.protocols || []).join(', '),
        is_private: v.is_private ? 'Private' : 'Public',
        is_shared: v.is_shared_segment ? 'Shared LAN' : '',
        _is_multicast: v.is_multicast,
        _is_host: v.is_host_route,
    }}));

    return rows.filter(r => {{
        if (r._is_multicast || r._is_host) return false;
        if (!q) return true;
        return r.subnet.includes(q) || r.gateways.includes(q) ||
               r.devices.toLowerCase().includes(q) || r.protocols.toLowerCase().includes(q);
    }}).sort((a, b) => {{
        const va = (a[subnetsSortCol] !== undefined ? a[subnetsSortCol] : '').toString();
        const vb = (b[subnetsSortCol] !== undefined ? b[subnetsSortCol] : '').toString();
        const numA = parseFloat(va), numB = parseFloat(vb);
        if (!isNaN(numA) && !isNaN(numB)) return subnetsSortAsc ? numA - numB : numB - numA;
        return subnetsSortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
    }});
}}

function renderSubnets() {{
    const rows = getSubnetRows();
    document.getElementById('subnets-count').textContent = `${{rows.length.toLocaleString()}} subnets`;
    const tbody = document.getElementById('subnets-tbody');
    tbody.innerHTML = rows.map(r => `
        <tr>
            <td class="mono" style="font-weight:600;color:#e2e8f0">${{esc(r.subnet)}}</td>
            <td>/${{r.prefix_len}}</td>
            <td>${{r.route_count}}</td>
            <td class="mono">${{esc(r.gateways) || '—'}}</td>
            <td style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${{esc(r.devices)}}">${{esc(r.devices) || '—'}}</td>
            <td>${{r.protocols.split(',').map(p => p.trim()).filter(Boolean).map(p => protoPill(p)).join(' ')}}</td>
            <td style="color:${{r.is_private === 'Private' ? '#6ee7b7' : '#f87171'}}">${{r.is_private}}</td>
            <td style="color:#10b981">${{r.is_shared}}</td>
        </tr>`).join('');

    document.querySelectorAll('#subnets-table thead th').forEach((th, i) => {{
        const cols = ['subnet','prefix_len','route_count','gateways','devices','protocols','is_private','is_shared'];
        th.className = (cols[i] === subnetsSortCol) ? (subnetsSortAsc ? 'sort-asc' : 'sort-desc') : '';
    }});
}}

function filterSubnets(q) {{
    subnetsFilter = q;
    renderSubnets();
}}

function sortSubnets(col) {{
    if (subnetsSortCol === col) subnetsSortAsc = !subnetsSortAsc;
    else {{ subnetsSortCol = col; subnetsSortAsc = true; }}
    renderSubnets();
}}

/* ═══════════════════════════════════════════════════════════════════
   UTILITIES
═══════════════════════════════════════════════════════════════════ */
function esc(s) {{
    return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}

</script>
</main>
</body>
</html>"""
