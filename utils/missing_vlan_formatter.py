"""HTML report for Find Missing VLAN results."""
from __future__ import annotations

from typing import Any, Dict, List

from utils.output_chrome import wrap_html_report


def write_missing_vlan_html(
    html_path: str,
    vlan_id: str,
    present_devices: List[str],
    missing_devices: List[str],
    errors: List[Dict[str, str]] = None,
    meta: Dict[str, Any] = None,
) -> str:
    errors = errors or []
    meta = meta or {}
    total = len(present_devices) + len(missing_devices)
    pct_missing = (len(missing_devices) / total * 100) if total else 0

    rows_present = ''.join(
        f'<tr><td style="color:#16a34a;font-weight:700;">✓</td><td>{_esc(d)}</td><td>Present</td></tr>'
        for d in sorted(present_devices)
    )
    rows_missing = ''.join(
        f'<tr><td style="color:#dc2626;font-weight:700;">✗</td><td>{_esc(d)}</td>'
        f'<td style="color:#dc2626;">Missing VLAN {vlan_id}</td></tr>'
        for d in sorted(missing_devices)
    )
    rows_err = ''.join(
        f'<tr><td style="color:#d97706;font-weight:700;">!</td><td>{_esc(e.get("host", "?"))}</td>'
        f'<td>{_esc(e.get("error", ""))}</td></tr>'
        for e in errors
    )

    rec = (
        f'<div style="background:#fff7ed;border-left:4px solid #d97706;padding:12px;border-radius:8px;margin-top:16px;">'
        f'<strong>Recommendation:</strong> Provision VLAN {vlan_id} on {len(missing_devices)} device(s) listed above.</div>'
        if missing_devices else
        f'<div style="background:#f0fdf4;border-left:4px solid #16a34a;padding:12px;border-radius:8px;margin-top:16px;">'
        f'<strong>All clear:</strong> Every scanned device has VLAN {vlan_id}.</div>'
    )

    err_block = (
        f'<h2 style="font-size:14px;margin:20px 0 8px;">Scan errors ({len(errors)})</h2>'
        f'<table><thead><tr><th></th><th>Device</th><th>Error</th></tr></thead><tbody>{rows_err}</tbody></table>'
        if rows_err else ''
    )

    body = f"""
<h2 style="font-size:14px;margin:0 0 8px;color:#dc2626;">Devices missing VLAN {vlan_id}</h2>
<table><thead><tr><th></th><th>Device</th><th>Status</th></tr></thead>
<tbody>{rows_missing or '<tr><td colspan="3">None — all devices have this VLAN</td></tr>'}</tbody></table>
<h2 style="font-size:14px;margin:20px 0 8px;color:#16a34a;">Devices with VLAN {vlan_id}</h2>
<table><thead><tr><th></th><th>Device</th><th>Status</th></tr></thead>
<tbody>{rows_present or '<tr><td colspan="3">None</td></tr>'}</tbody></table>
{err_block}
{rec}
"""
    html = wrap_html_report(
        f'Missing VLAN Audit — VLAN {vlan_id}',
        body,
        subtitle=f'{len(missing_devices)} missing · {len(present_devices)} present · {pct_missing:.0f}% gap',
        hints=[
            'Missing = VLAN ID not found in device VLAN database',
            'Errors = SSH/parse failure — fix access and re-run for those devices',
            'Use the missing list as your provisioning work queue',
        ],
        kpis=[
            {'label': 'Scanned', 'value': str(total + len(errors))},
            {'label': 'Present', 'value': str(len(present_devices)), 'tone': 'ok'},
            {'label': 'Missing', 'value': str(len(missing_devices)), 'tone': 'bad' if missing_devices else 'ok'},
            {'label': 'Gap rate', 'value': f'{pct_missing:.0f}%', 'tone': 'bad' if pct_missing > 0 else 'ok'},
        ],
        page_title=f'Missing VLAN {vlan_id}',
    )
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return html_path


def _esc(s: str) -> str:
    return (s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
