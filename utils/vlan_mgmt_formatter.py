"""HTML report for VLAN management (add/rename/delete) runs."""
from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any, Dict, List

from utils.output_chrome import wrap_html_report


def write_vlan_mgmt_html(
    html_path: str,
    action: str,
    vlan_id: str,
    vlan_name: str,
    results: List[Dict[str, Any]],
    *,
    dry_run: bool = False,
) -> str:
    rows = []
    for r in results:
        status = r.get('status', '?')
        host = escape(str(r.get('device', '?')))
        err = escape(str(r.get('error', '') or ''))
        skipped = r.get('data', {}).get('skipped')
        note = 'skipped (already exists or policy)' if skipped else err
        cls = 'ok' if status == 'success' and not skipped else (
            'warn' if status in ('skipped',) or skipped else (
                'bad' if status in ('fail', 'verification_failed') else 'warn'
            )
        )
        color = {'ok': '#16a34a', 'bad': '#dc2626', 'warn': '#d97706'}.get(cls, '#475569')
        rows.append(
            f'<tr><td style="color:{color};font-weight:700;">{escape(status)}</td><td>{host}</td>'
            f'<td>{escape(note)}</td></tr>'
        )
    ok = sum(1 for r in results if r.get('status') == 'success' and not r.get('data', {}).get('skipped'))
    verify_fail = sum(1 for r in results if r.get('status') == 'verification_failed')
    skipped_n = sum(1 for r in results if r.get('status') == 'skipped' or r.get('data', {}).get('skipped'))
    failed_n = sum(1 for r in results if r.get('status') == 'fail')
    mode = 'DRY-RUN (no changes applied)' if dry_run else 'LIVE (changes attempted)'
    body = f"""
<style>.ok {{ color: #16a34a; }} .bad {{ color: #dc2626; }} .warn {{ color: #d97706; }}</style>
<p><b>Action:</b> VLAN {escape(action.title())} · <b>ID:</b> {escape(vlan_id)} · <b>Name:</b> {escape(vlan_name or '—')}</p>
<p><b>Mode:</b> {mode}</p>
<table><thead><tr><th>Status</th><th>Device</th><th>Notes</th></tr></thead>
<tbody>{''.join(rows) if rows else '<tr><td colspan="3">No devices processed</td></tr>'}</tbody></table>
"""
    hints = [
        'DRY-RUN shows what would happen — always review before LIVE mode',
        'verification_failed means config was sent but post-check did not confirm VLAN',
        'skipped usually means VLAN already exists or device policy blocked the change',
    ]
    if dry_run:
        hints.insert(0, 'This was a dry run — no configuration was pushed to devices')
    html = wrap_html_report(
        f'VLAN {action.title()} — ID {vlan_id}',
        body,
        subtitle=f'{ok}/{len(results)} succeeded · {mode}',
        hints=hints,
        kpis=[
            {'label': 'Success', 'value': f'{ok}/{len(results)}', 'tone': 'ok' if ok == len(results) else 'warn'},
            {'label': 'Failed', 'value': str(failed_n), 'tone': 'bad' if failed_n else 'ok'},
            {'label': 'Verify failed', 'value': str(verify_fail), 'tone': 'bad' if verify_fail else 'ok'},
            {'label': 'Skipped', 'value': str(skipped_n)},
        ],
        page_title=f'VLAN {action} {vlan_id}',
    )
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return html_path
