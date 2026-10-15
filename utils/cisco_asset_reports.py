"""HTML + CSV consolidated Cisco asset / warranty reports with print-to-PDF."""
from __future__ import annotations

import csv
import os
from html import escape
from typing import Any, Dict, List, Optional, Sequence

from utils.output_chrome import plugin_display_name, wrap_html_report
from utils.output_paths import CAT_PLUGINS, path_in_run, prepare_run_output, slugify, write_run_manifest


CSV_COLUMNS = [
    'host',
    'hostname',
    'collection_method',
    'pid',
    'vid',
    'serial_number',
    'software_version',
    'model_name',
    'end_of_life',
    'end_of_support',
    'end_of_service',
    'warranty_status',
    'warranty_end',
    'contract_status',
    'severity',
    'error',
]


def _flatten_results(results: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for res in results:
        data = res.get('data') or {}
        for asset in data.get('assets') or []:
            row = dict(asset)
            row.setdefault('host', res.get('device') or res.get('host') or '')
            if res.get('status') == 'fail' and not row.get('error'):
                row['error'] = res.get('error') or 'collection failed'
                row['severity'] = row.get('severity') or 'critical'
            rows.append(row)
    return rows


def _severity_class(severity: str) -> str:
    sev = (severity or '').lower()
    if sev in ('critical', 'expired'):
        return 'sev-critical'
    if sev in ('warn', 'expiring_soon'):
        return 'sev-warn'
    if sev in ('ok', 'active'):
        return 'sev-ok'
    return 'sev-info'


def _build_table_html(rows: List[Dict[str, Any]]) -> str:
    """Build HTML table matching demo format with clickable PIDs and EOL/EOS fields."""
    # Match demo format columns: Host, Hostname, Product ID (PID), Serial Number, Software Version, Warranty Status, End of Life, End of Support
    demo_columns = [
        'host',
        'hostname',
        'pid',
        'serial_number',
        'software_version',
        'warranty_status',
        'end_of_life',
        'end_of_support',
    ]
    
    head = ''.join(f'<th scope="col">{escape(c.replace("_", " ").title())}</th>' for c in demo_columns)
    body_parts = []
    
    # Load EOL catalog data for modal
    try:
        from modules.cisco_eol_database import get_all_models, seed_demo_data
        eol_models = get_all_models()
        if not eol_models:
            eol_models = seed_demo_data()
    except Exception:
        eol_models = []
    
    # Build JavaScript data for modal
    import json
    js_eol_data = json.dumps([
        {
            'pid': m.get('pid', ''),
            'name': m.get('model_name', ''),
            'eol': m.get('end_of_life', ''),
            'eos': m.get('end_of_support', ''),
            'eosvc': m.get('end_of_service', ''),
            'status': m.get('warranty_status', 'unknown')
        }
        for m in eol_models
    ])
    
    for row in rows:
        sev = _severity_class(str(row.get('severity') or ''))
        tds = []
        
        for col in demo_columns:
            val = row.get(col, '')
            
            # Make PID clickable
            if col == 'pid' and val:
                val = f'<a class="nst-clickable-pid" onclick="openCiscoEolCatalog(\'{escape(val)}\')">{escape(val)}</a>'
            elif isinstance(val, list):
                val = f'{len(val)} items'
            else:
                val = escape(str(val or ''))
            
            tds.append(f'<td>{val}</td>')
        
        body_parts.append(f'<tr class="{sev}">{"".join(tds)}</tr>')
    
    table_html = (
        f'<table class="nst-asset-table"><thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(body_parts)}</tbody></table>'
    )
    
    # Add modal and JavaScript
    modal_js = _get_cisco_eol_modal_and_js(js_eol_data)
    
    return table_html + modal_js


def _extra_css() -> str:
    return """
    .nst-toolbar { display:flex; gap:10px; flex-wrap:wrap; margin: 12px 0 16px; }
    .nst-toolbar button {
      background:#1d4ed8; color:#fff; border:none; border-radius:8px;
      padding:8px 14px; font-size:13px; cursor:pointer;
    }
    .nst-toolbar button.secondary { background:#475569; }
    .nst-asset-table { width:100%; border-collapse:collapse; font-size:12px; }
    .nst-asset-table th { position:sticky; top:0; z-index:1; }
    .nst-asset-table td, .nst-asset-table th { border:1px solid #e2e8f0; padding:6px 8px; text-align:left; }
    tr.sev-critical td { background:#fee2e2; }
    tr.sev-warn td { background:#fef3c7; }
    tr.sev-ok td { background:#ecfdf5; }
    tr.sev-info td { background:#f8fafc; }
    @media print {
      .nst-toolbar, .nst-no-print { display:none !important; }
      body.nst-report { padding:0; }
      .nst-report-body { border:none; box-shadow:none; }
    }
    /* Clickable PID styles from demo */
    .nst-clickable-pid {
        color: #007aff;
        cursor: pointer;
        font-weight: 600;
        text-decoration: none;
        padding: 4px 8px;
        border-radius: 6px;
        transition: all 0.2s;
        background: rgba(0, 122, 255, 0.1);
    }
    .nst-clickable-pid:hover {
        background: #007aff;
        color: white;
        transform: scale(1.05);
    }
    /* Modal styles from demo */
    .nst-modal-overlay {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(10px);
        z-index: 10000;
        justify-content: center;
        align-items: center;
    }
    .nst-modal-content {
        background: #1c1c1e;
        border-radius: 24px;
        width: 90%;
        max-width: 1200px;
        max-height: 85vh;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        display: flex;
        flex-direction: column;
    }
    .nst-modal-header {
        padding: 24px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.12);
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: linear-gradient(135deg, rgba(0, 122, 255, 0.1) 0%, rgba(88, 86, 214, 0.1) 100%);
    }
    .nst-modal-title {
        font-size: 20px;
        font-weight: 700;
        color: #ffffff;
    }
    .nst-modal-close {
        background: rgba(255, 255, 255, 0.12);
        border: none;
        color: #ffffff;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        cursor: pointer;
        font-size: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
    }
    .nst-modal-close:hover {
        background: #007aff;
        color: white;
        transform: rotate(90deg);
    }
    .nst-modal-body {
        padding: 24px;
        overflow-y: auto;
        flex: 1;
    }
    .nst-highlighted-row {
        background: rgba(0, 122, 255, 0.2) !important;
        border-left: 4px solid #007aff;
    }
    """


def _toolbar_html(csv_name: str) -> str:
    return f"""
    <div class="nst-toolbar nst-no-print">
      <button type="button" onclick="window.print()">Export as PDF (Print)</button>
      <button type="button" class="secondary" onclick="window.location.href='{escape(csv_name)}'">Download CSV</button>
    </div>
    """


def _get_cisco_eol_modal_and_js(js_eol_data: str) -> str:
    """Generate modal and JavaScript for Cisco EOL catalog matching demo format."""
    return f'''
    <div id="nst-cisco-eol-modal" class="nst-modal-overlay" style="display: none;">
        <div class="nst-modal-content">
            <div class="nst-modal-header">
                <div class="nst-modal-title">📚 Cisco EOL/EOS Model Catalog</div>
                <button class="nst-modal-close" onclick="closeCiscoEolCatalog()">×</button>
            </div>
            <div class="nst-modal-body">
                <div class="nst-toolbar">
                    <input type="text" id="nst-eol-search" placeholder="Search by PID, model name..." oninput="filterCiscoEolCatalog()" style="background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.12); color: #ffffff; border-radius: 10px; padding: 8px 12px; font-size: 13px; outline: none; min-width: 240px; flex: 1;">
                    <button onclick="clearCiscoEolSearch()" style="background: #475569; color: white; border: none; border-radius: 10px; padding: 8px 16px; font-size: 13px; cursor: pointer;">Clear</button>
                    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                        <button class="nst-filter-btn active" id="nst-btn-all" onclick="setCiscoEolFilter('all')" style="padding: 6px 12px; border-radius: 12px; font-size: 12px; cursor: pointer; border: 2px solid transparent; background: #007aff; color: white;">All</button>
                        <button class="nst-filter-btn" id="nst-btn-active" onclick="setCiscoEolFilter('active')" style="padding: 6px 12px; border-radius: 12px; font-size: 12px; cursor: pointer; border: 2px solid transparent; background: rgba(255, 255, 255, 0.1); color: rgba(255,255,255,0.7);">Active</button>
                        <button class="nst-filter-btn" id="nst-btn-expired" onclick="setCiscoEolFilter('expired')" style="padding: 6px 12px; border-radius: 12px; font-size: 12px; cursor: pointer; border: 2px solid transparent; background: rgba(255, 255, 255, 0.1); color: rgba(255,255,255,0.7);">Expired</button>
                        <button class="nst-filter-btn" id="nst-btn-warning" onclick="setCiscoEolFilter('warning')" style="padding: 6px 12px; border-radius: 12px; font-size: 12px; cursor: pointer; border: 2px solid transparent; background: rgba(255, 255, 255, 0.1); color: rgba(255,255,255,0.7);">Expiring Soon</button>
                    </div>
                </div>
                <table id="nst-eol-table" style="width: 100%; border-collapse: collapse; font-size: 13px;">
                    <thead>
                        <tr>
                            <th style="background: rgba(0, 122, 255, 0.1); color: #007aff; font-weight: 600; padding: 12px 16px; text-align: left; border-bottom: 2px solid #007aff;">PID</th>
                            <th style="background: rgba(0, 122, 255, 0.1); color: #007aff; font-weight: 600; padding: 12px 16px; text-align: left; border-bottom: 2px solid #007aff;">Model Name</th>
                            <th style="background: rgba(0, 122, 255, 0.1); color: #007aff; font-weight: 600; padding: 12px 16px; text-align: left; border-bottom: 2px solid #007aff;">End of Life</th>
                            <th style="background: rgba(0, 122, 255, 0.1); color: #007aff; font-weight: 600; padding: 12px 16px; text-align: left; border-bottom: 2px solid #007aff;">End of Support</th>
                            <th style="background: rgba(0, 122, 255, 0.1); color: #007aff; font-weight: 600; padding: 12px 16px; text-align: left; border-bottom: 2px solid #007aff;">End of Service</th>
                            <th style="background: rgba(0, 122, 255, 0.1); color: #007aff; font-weight: 600; padding: 12px 16px; text-align: left; border-bottom: 2px solid #007aff;">Status</th>
                        </tr>
                    </thead>
                    <tbody id="nst-eol-body">
                        <!-- Populated by JavaScript -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    <script>
    // Data loaded from Cisco EOL/EOS database
    const ciscoEolData = {js_eol_data};
    
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
            'active': '<span style="display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; background: rgba(39, 174, 96, 0.2); color: #27ae60; border: 1px solid #27ae60;">Active</span>',
            'expired': '<span style="display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; background: rgba(231, 76, 60, 0.2); color: #e74c3c; border: 1px solid #e74c3c;">Expired</span>',
            'warning': '<span style="display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; background: rgba(243, 156, 18, 0.2); color: #f39c12; border: 1px solid #f39c12;">Expiring Soon</span>',
            'unknown': '<span style="display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; background: rgba(149, 165, 166, 0.2); color: #95a5a6; border: 1px solid #95a5a6;">Unknown</span>'
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
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 40px; color: rgba(255,255,255,0.5);">No models found matching your search.</td></tr>';
            return;
        }}
        
        tbody.innerHTML = filteredData.map(item => `
            <tr data-pid="${{item.pid}}" class="${{item.pid === ciscoEolHighlightedPid ? 'nst-highlighted-row' : ''}}" style="padding: 12px 16px; border-bottom: 1px solid rgba(255, 255, 255, 0.12);">
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
            btn.style.background = 'rgba(255, 255, 255, 0.1)';
            btn.style.color = 'rgba(255,255,255,0.7)';
        }});
        document.getElementById(`nst-btn-${{filter}}`).style.background = '#007aff';
        document.getElementById(`nst-btn-${{filter}}`).style.color = 'white';
        
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


def generate_cisco_asset_consolidated_reports(
    results: Sequence[Dict[str, Any]],
    plugin_id: str = 'cisco_asset_warranty',
) -> Dict[str, str]:
    rows = _flatten_results(results)
    paths = prepare_run_output(CAT_PLUGINS, slugify(f'{plugin_id}_consolidated'))
    csv_path = path_in_run(paths, 'asset_warranty_inventory.csv')
    html_path = path_in_run(paths, 'asset_warranty_inventory.html')

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, '') for k in CSV_COLUMNS})

    success = sum(1 for r in results if r.get('status') == 'success')
    fail = len(results) - success
    critical = sum(1 for r in rows if _severity_class(str(r.get('severity'))) == 'sev-critical')
    warn = sum(1 for r in rows if _severity_class(str(r.get('severity'))) == 'sev-warn')

    # Calculate model summary/quantities
    model_counts = {}
    for row in rows:
        pid = row.get('pid', 'Unknown')
        model_name = row.get('model_name', 'Unknown Model')
        key = f"{pid}|{model_name}"
        model_counts[key] = model_counts.get(key, 0) + 1
    
    # Sort by count (descending)
    sorted_models = sorted(model_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Build model summary HTML
    model_summary_html = ''
    if sorted_models:
        model_summary_rows = []
        for idx, (key, count) in enumerate(sorted_models[:20], 1):  # Top 20 models
            pid, model_name = key.split('|', 1)
            model_summary_rows.append(f'''
                <tr>
                    <td>{idx}</td>
                    <td><strong>{escape(pid)}</strong></td>
                    <td>{escape(model_name)}</td>
                    <td style="text-align: center; font-weight: 600;">{count}</td>
                </tr>
            ''')
        
        model_summary_html = f'''
        <div style="margin-top: 32px; padding: 24px; background: rgba(0, 122, 255, 0.05); border-radius: 16px; border: 1px solid rgba(0, 122, 255, 0.2);">
            <h3 style="font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #007aff;">📊 Model Summary (Top 20 by Quantity)</h3>
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <thead>
                    <tr>
                        <th style="background: rgba(0, 122, 255, 0.1); color: #007aff; font-weight: 600; padding: 12px 16px; text-align: left; border-bottom: 2px solid #007aff;">#</th>
                        <th style="background: rgba(0, 122, 255, 0.1); color: #007aff; font-weight: 600; padding: 12px 16px; text-align: left; border-bottom: 2px solid #007aff;">Product ID (PID)</th>
                        <th style="background: rgba(0, 122, 255, 0.1); color: #007aff; font-weight: 600; padding: 12px 16px; text-align: left; border-bottom: 2px solid #007aff;">Model Name</th>
                        <th style="background: rgba(0, 122, 255, 0.1); color: #007aff; font-weight: 600; padding: 12px 16px; text-align: center; border-bottom: 2px solid #007aff;">Count</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(model_summary_rows)}
                </tbody>
            </table>
            <p style="margin-top: 12px; font-size: 12px; color: rgba(255,255,255,0.6);">Total unique models: {len(sorted_models)}</p>
        </div>
        '''

    kpis = [
        {'label': 'Devices', 'value': str(len(results)), 'tone': ''},
        {'label': 'Asset rows', 'value': str(len(rows)), 'tone': ''},
        {'label': 'Unique models', 'value': str(len(sorted_models)), 'tone': ''},
        {'label': 'Success', 'value': str(success), 'tone': 'ok'},
        {'label': 'Failed', 'value': str(fail), 'tone': 'bad' if fail else ''},
        {'label': 'Critical', 'value': str(critical), 'tone': 'bad' if critical else ''},
        {'label': 'Warnings', 'value': str(warn), 'tone': 'warn' if warn else ''},
    ]
    hints = [
        'SSH is primary; SNMP fallback uses vault SNMP credentials when SSH fails or PID/SN missing.',
        'Contract dates require Cisco SN2INFO/EoX API unless mock lab enrichment is active.',
        'Use Export as PDF to save this report from your browser print dialog.',
        'Click on any Product ID (PID) to view the full Cisco EOL/EOS catalog.',
    ]
    csv_basename = os.path.basename(csv_path)
    inner = f'<style>{_extra_css()}</style>' + _toolbar_html(csv_basename) + _build_table_html(rows) + model_summary_html
    title = f'{plugin_display_name(plugin_id)} — Consolidated Inventory'
    html_doc = wrap_html_report(
        title,
        inner,
        subtitle=f'{len(results)} device(s) · {len(rows)} asset row(s) · {len(sorted_models)} unique model(s)',
        kpis=kpis,
        hints=hints,
        page_title=title,
    )
    with open(html_path, 'w', encoding='utf-8') as fh:
        fh.write(html_doc)

    write_run_manifest(
        paths,
        extra={
            'plugin_id': plugin_id,
            'artifacts': [html_path, csv_path],
            'summary': f'{len(rows)} asset rows from {len(results)} device(s)',
            'task_title': plugin_display_name(plugin_id),
        },
    )
    return {'html': html_path, 'csv': csv_path}
