"""
Shared offline-first report chrome for Network Swiss Tool Pro.

All user-facing txt/html outputs should use these helpers for consistent,
dummy-proof headers, hints, contrast, and run-folder README files.
"""
from __future__ import annotations

import os
from datetime import datetime
from html import escape
from typing import Any, Dict, List, Optional, Sequence, Union

from utils.topo_map_shell import read_version_label

OFFLINE_BANNER = (
    'Fully offline — open this file in any browser or text editor; no internet required.'
)

DEFAULT_HINTS = [
    'Green / checkmarks = OK · Red / ✗ = action needed',
    'Keep this folder — it is your audit trail for this run',
]

PLUGIN_DISPLAY_NAMES = {
    'vlan_audit': 'VLAN Audit',
    'vpc_domain': 'vPC Domain Check',
    'serial_number': 'Serial Number Inventory',
    'cisco_asset_warranty': 'Cisco Asset & Warranty Inventory',
    'device_time': 'Device Time / NTP',
    'critical_logs': 'Critical Logs',
    'interface_errors': 'Interface Errors',
    'environment_status': 'Environment / Power / Fans',
    'standards_validator': 'Standards Compliance',
    'interface_vlan_reporter': 'Interface VLAN Reporter',
}

PLUGIN_HINTS: Dict[str, List[str]] = {
    'vlan_audit': [
        'Lists every VLAN ID and name reported by the device',
        'Compare against your VLAN design spreadsheet or IPAM',
    ],
    'vpc_domain': [
        'Confirms vPC domain ID, role, peer-link, and keepalive state',
        'If "not configured", the device may not be a vPC peer',
    ],
    'serial_number': [
        'Use for asset inventory, RMA, and support cases',
        'Stack/module serials appear under Module Serials when present',
    ],
    'cisco_asset_warranty': [
        'SSH collects show version + show inventory; SNMP fallback uses vault SNMP credentials',
        'Click on any Product ID (PID) in the HTML report to view the Cisco EOL/EOS catalog',
        'CSV export includes End of Life, End of Support, and End of Service dates',
        'Warranty status is calculated based on EOL/EOS dates from Cisco database',
        'Export consolidated HTML to PDF via Print; CSV saved alongside HTML in the run folder',
        'Live warranty contract dates require Cisco SN2INFO/EoX API (not on-box CLI)',
    ],
    'device_time': [
        'NTP drift causes log correlation and certificate issues',
        'No ❌ on NTP Synced means fix NTP before trusting timestamps',
    ],
    'critical_logs': [
        'Review each entry — severity and timestamp are shown',
        'Empty report with ✅ means no critical syslog patterns matched',
    ],
    'interface_errors': [
        'Non-zero CRC/input/output errors often indicate bad cable/SFP',
        'Sort by highest error count when prioritizing field work',
    ],
    'environment_status': [
        'Failed PSU or fan entries need immediate hardware attention',
        'Temperature warnings may precede automatic shutdown',
    ],
    'interface_vlan_reporter': [
        'Access ports have a single access VLAN',
        'Trunk ports carry multiple VLANs (check allowed list)',
        'Native VLAN is untagged on trunks (default: VLAN 1)',
        'Voice VLAN is for IP phone traffic (CDP/LLDP-MED required)',
        'Use this report for VLAN compliance audits',
    ],
}


def timestamp_label() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def plugin_display_name(plugin_id: str) -> str:
    return PLUGIN_DISPLAY_NAMES.get(plugin_id, plugin_id.replace('_', ' ').title())


def text_report_header(
    title: str,
    *,
    subtitle: str = '',
    host: str = '',
    hints: Optional[Sequence[str]] = None,
) -> str:
    """Standard plain-text report header (offline-safe, operator hints)."""
    version = read_version_label()
    lines = [
        '=' * 72,
        f'Network Swiss Tool Pro {version}',
        title,
        '=' * 72,
        f'Generated: {timestamp_label()}',
        OFFLINE_BANNER,
    ]
    if host:
        lines.append(f'Device:    {host}')
    if subtitle:
        lines.append(subtitle)
    lines.append('')
    lines.append('HOW TO READ THIS REPORT:')
    for h in (hints or DEFAULT_HINTS):
        lines.append(f'  • {h}')
    lines.append('')
    lines.append('-' * 72)
    lines.append('')
    return '\n'.join(lines)


def text_report_footer(*, summary: str = '') -> str:
    lines = ['', '-' * 72]
    if summary:
        lines.append(summary)
    lines.append(f'End of report · {read_version_label()} · {timestamp_label()}')
    lines.append('-' * 72)
    return '\n'.join(lines)


def wrap_plugin_text_report(plugin_id: str, host: str, body: str) -> str:
    """Prepend chrome to plugin txt if not already present."""
    if 'Network Swiss Tool Pro' in body[:200]:
        return body
    title = plugin_display_name(plugin_id)
    hints = PLUGIN_HINTS.get(plugin_id, DEFAULT_HINTS)
    return text_report_header(title, host=host, hints=hints) + body.lstrip() + text_report_footer()


def offline_report_css() -> str:
    """Light-theme CSS — system fonts only, high contrast, print-friendly."""
    return """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body.nst-report {
      font-family: system-ui, "Segoe UI", sans-serif;
      background: #f1f5f9;
      color: #0f172a;
      line-height: 1.5;
      font-size: 14px;
      padding: 20px 24px 32px;
    }
    .nst-report-wrap { max-width: 1100px; margin: 0 auto; }
    .nst-report-banner {
      background: #eff6ff;
      border: 1px solid #93c5fd;
      border-radius: 10px;
      padding: 10px 14px;
      font-size: 12px;
      color: #1e40af;
      margin-bottom: 16px;
    }
    .nst-report-header {
      background: #1e293b;
      color: #f8fafc;
      border-radius: 12px;
      padding: 20px 22px;
      margin-bottom: 16px;
    }
    .nst-report-header h1 {
      font-size: 20px;
      font-weight: 700;
      margin-bottom: 6px;
    }
    .nst-report-header .nst-sub {
      font-size: 13px;
      color: #cbd5e1;
    }
    .nst-ver-badge {
      display: inline-block;
      background: #4f46e5;
      color: #fff;
      font-size: 11px;
      font-weight: 700;
      padding: 2px 10px;
      border-radius: 12px;
      margin-left: 8px;
      vertical-align: middle;
    }
    .nst-hint-box {
      background: #fff;
      border: 1px solid #e2e8f0;
      border-left: 4px solid #6366f1;
      border-radius: 8px;
      padding: 12px 14px;
      margin-bottom: 16px;
      font-size: 12px;
      color: #475569;
    }
    .nst-hint-box b { color: #1e293b; display: block; margin-bottom: 6px; }
    .nst-hint-box ul { margin: 0; padding-left: 18px; }
    .nst-hint-box li { margin: 4px 0; }
    .nst-kpi-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 16px;
    }
    .nst-kpi-card {
      background: #fff;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      padding: 12px 16px;
      min-width: 120px;
      flex: 1;
    }
    .nst-kpi-card span { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: .04em; }
    .nst-kpi-card b { display: block; font-size: 22px; margin-top: 4px; color: #0f172a; }
    .nst-kpi-card.ok b { color: #16a34a; }
    .nst-kpi-card.bad b { color: #dc2626; }
    .nst-kpi-card.warn b { color: #d97706; }
    .nst-report-body {
      background: #fff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 16px 18px;
      overflow-x: auto;
    }
    .nst-report-body table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    .nst-report-body th {
      text-align: left;
      padding: 8px 10px;
      background: #1e293b;
      color: #f8fafc;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: .03em;
    }
    .nst-report-body td {
      padding: 8px 10px;
      border-bottom: 1px solid #e2e8f0;
      color: #1e293b;
    }
    .nst-report-body tr:nth-child(even) td { background: #f8fafc; }
    .nst-report-body tr:hover td { background: #eff6ff; }
    .nst-report-body pre {
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      line-height: 1.45;
      white-space: pre-wrap;
      word-break: break-word;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 14px;
      color: #1e293b;
    }
    .nst-report-body code, .port-code {
      font-family: Consolas, monospace;
      font-size: 12px;
      background: #e0f2fe;
      color: #0369a1;
      padding: 1px 6px;
      border-radius: 4px;
    }
    mark.nst-match, .nst-match {
      background: #fef08a;
      color: #1e293b;
      padding: 0 2px;
      border-radius: 2px;
    }
    .nst-report-footer {
      margin-top: 16px;
      font-size: 11px;
      color: #94a3b8;
      text-align: center;
    }
    @media print {
      body.nst-report { background: #fff; padding: 0; }
      .nst-report-banner { border-color: #666; }
    }
    """


def _kpi_html(kpis: Optional[Sequence[Dict[str, str]]]) -> str:
    if not kpis:
        return ''
    parts = ['<div class="nst-kpi-row">']
    for k in kpis:
        tone = k.get('tone', '')
        cls = f'nst-kpi-card {tone}'.strip() if tone else 'nst-kpi-card'
        parts.append(
            f'<div class="{cls.strip()}"><span>{escape(k.get("label", ""))}</span>'
            f'<b>{escape(str(k.get("value", "")))}</b></div>'
        )
    parts.append('</div>')
    return ''.join(parts)


def _hints_html(hints: Optional[Sequence[str]]) -> str:
    if not hints:
        return ''
    items = ''.join(f'<li>{escape(h)}</li>' for h in hints)
    return (
        f'<div class="nst-hint-box"><b>How to read this report</b>'
        f'<ul>{items}</ul></div>'
    )


def wrap_html_report(
    title: str,
    body_html: str,
    *,
    subtitle: str = '',
    hints: Optional[Sequence[str]] = None,
    kpis: Optional[Sequence[Dict[str, str]]] = None,
    page_title: str = '',
) -> str:
    """Full offline HTML document with unified chrome."""
    version = read_version_label()
    ts = timestamp_label()
    pt = escape(page_title or title)
    hints = hints or DEFAULT_HINTS
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{pt} — Network Swiss Tool Pro</title>
  <style>{offline_report_css()}</style>
</head>
<body class="nst-report">
  <div class="nst-report-wrap">
    <div class="nst-report-banner">&#128274; {escape(OFFLINE_BANNER)}</div>
    <header class="nst-report-header">
      <h1>{escape(title)}<span class="nst-ver-badge">{escape(version)}</span></h1>
      <div class="nst-sub">{escape(subtitle)} · Generated {escape(ts)}</div>
    </header>
    {_hints_html(hints)}
    {_kpi_html(kpis)}
    <div class="nst-report-body">
      {body_html}
    </div>
    <div class="nst-report-footer">Network Swiss Tool Pro {escape(version)} · Saved for offline review</div>
  </div>
</body>
</html>"""


def wrap_plugin_html_report(plugin_id: str, host: str, text_content: str) -> str:
    """Rich HTML wrapper for Swiss plugin txt output."""
    title = plugin_display_name(plugin_id)
    hints = PLUGIN_HINTS.get(plugin_id, DEFAULT_HINTS)
    body = f'<pre>{escape(text_content)}</pre>'
    return wrap_html_report(
        title,
        body,
        subtitle=f'Device: {host}',
        hints=hints,
        page_title=f'{title} — {host}',
    )


def write_run_readme(
    paths: Dict[str, Any],
    *,
    title: str,
    task_summary: str = '',
    files: Optional[Dict[str, str]] = None,
    hints: Optional[Sequence[str]] = None,
    next_steps: Optional[Sequence[str]] = None,
) -> str:
    """Write 00_README.txt into a prepared run folder (operator guide)."""
    run_dir = paths.get('run_dir')
    if not run_dir:
        return ''
    readme = os.path.join(run_dir, '00_README.txt')
    version = read_version_label()
    ts = paths.get('generated_at') or datetime.now().isoformat()
    category = paths.get('category') or 'output'
    file_map = files or {}
    if not file_map:
        if paths.get('txt_path'):
            file_map['report.txt'] = 'Plain-text summary — open in Notepad'
        if paths.get('html_path'):
            file_map['report.html'] = 'Formatted report — open in Chrome/Edge (works offline)'
        file_map.setdefault('manifest.json', 'Machine metadata — optional for operators')

    lines = [
        '=' * 72,
        f'Network Swiss Tool Pro {version} — Output Guide',
        '=' * 72,
        '',
        f'Task:      {title}',
        f'Category:  {category}',
        f'Run ID:    {paths.get("run_id", "—")}',
        f'Generated: {ts}',
        f'Folder:    {run_dir}',
        '',
    ]
    if task_summary:
        lines += ['SUMMARY:', f'  {task_summary}', '']
    lines += ['FILES IN THIS FOLDER:', '']
    for fname, desc in file_map.items():
        fpath = os.path.join(run_dir, fname)
        mark = '[✓]' if os.path.isfile(fpath) else '[ ]'
        lines.append(f'  {mark} {fname}')
        lines.append(f'      {desc}')
        lines.append('')
    lines += [
        'HOW TO USE (OFFLINE):',
        '  1. Double-click report.html for the best view (no internet needed)',
        '  2. Use report.txt in any text editor for copy/paste into tickets',
        '  3. Keep this entire folder as your change/audit record',
        '',
    ]
    if hints:
        lines.append('NOTES:')
        for h in hints:
            lines.append(f'  • {h}')
        lines.append('')
    if next_steps:
        lines.append('SUGGESTED NEXT STEPS:')
        for n in next_steps:
            lines.append(f'  → {n}')
        lines.append('')
    lines += [
        OFFLINE_BANNER,
        '=' * 72,
    ]
    try:
        with open(readme, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    except OSError:
        return ''
    return readme
