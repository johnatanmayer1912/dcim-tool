"""Fleet reachability matrix — Netdisco/LibreNMS-inspired daily ops view.

Builds a host × {ping, ssh} table for inventory scope. Uses modules.connectivity
logic without inventing device state. Offline/mock friendly via injectable runners.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


RowRunner = Callable[[Dict[str, Any], str, str, str, Optional[Callable[[str], None]]], Dict[str, Any]]


def _status_of(result: Dict[str, Any]) -> str:
    st = (result or {}).get('status')
    if st == 'success':
        return 'ok'
    data = (result or {}).get('data') or {}
    if data.get('ping') and not data.get('ssh'):
        return 'ping_only'
    if data.get('ping') is False:
        return 'unreachable'
    return 'fail'


def build_reachability_matrix(
    devices: List[Dict[str, Any]],
    user: str,
    pwd: str,
    enb_pwd: str = '',
    log_func: Optional[Callable[[str], None]] = None,
    runner: Optional[RowRunner] = None,
) -> Dict[str, Any]:
    """Run connectivity checks and aggregate a matrix summary."""
    from modules.connectivity import run as default_runner

    check = runner or default_runner
    rows: List[Dict[str, Any]] = []
    counts = {'ok': 0, 'ping_only': 0, 'unreachable': 0, 'fail': 0}

    for device in devices or []:
        host = device.get('host') or 'unknown'
        dtype = device.get('device_type') or ''
        try:
            result = check(device, user, pwd, enb_pwd, log_func=log_func)
        except Exception as exc:
            result = {
                'device': host,
                'status': 'fail',
                'data': {'ping': False, 'ssh': False},
                'error': str(exc).splitlines()[0] if str(exc) else 'error',
            }
        data = result.get('data') or {}
        bucket = _status_of(result)
        counts[bucket] = counts.get(bucket, 0) + 1
        rows.append({
            'host': host,
            'device_type': dtype,
            'ping': bool(data.get('ping')),
            'ssh': bool(data.get('ssh')),
            'status': bucket,
            'error': result.get('error'),
        })

    summary = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'device_count': len(rows),
        'counts': counts,
        'rows': rows,
    }
    return summary


def matrix_to_csv(summary: Dict[str, Any]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(['Host', 'Device Type', 'Ping', 'SSH', 'Status', 'Error'])
    for row in summary.get('rows') or []:
        w.writerow([
            row.get('host'),
            row.get('device_type'),
            'yes' if row.get('ping') else 'no',
            'yes' if row.get('ssh') else 'no',
            row.get('status'),
            row.get('error') or '',
        ])
    return buf.getvalue()


def matrix_to_html(summary: Dict[str, Any]) -> str:
    counts = summary.get('counts') or {}
    rows_html = []
    for row in summary.get('rows') or []:
        st = row.get('status') or ''
        color = {
            'ok': '#166534',
            'ping_only': '#a16207',
            'unreachable': '#b91c1c',
            'fail': '#b91c1c',
        }.get(st, '#334155')
        err = (row.get('error') or '').replace('<', '&lt;').replace('>', '&gt;')
        rows_html.append(
            f"<tr><td>{row.get('host')}</td><td>{row.get('device_type')}</td>"
            f"<td>{'✓' if row.get('ping') else '✗'}</td>"
            f"<td>{'✓' if row.get('ssh') else '✗'}</td>"
            f"<td style='color:{color};font-weight:600'>{st}</td>"
            f"<td style='font-size:12px;color:#64748b'>{err}</td></tr>"
        )
    body = '\n'.join(rows_html) or '<tr><td colspan="6">No devices</td></tr>'
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Fleet Reachability Matrix</title>
<style>
body{{font-family:ui-sans-serif,system-ui,sans-serif;margin:24px;background:#f8fafc;color:#0f172a}}
h1{{font-size:22px;margin:0 0 8px}}
.meta{{color:#475569;font-size:13px;margin-bottom:16px}}
.cards{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px}}
.card{{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:12px 16px;min-width:110px}}
.card b{{display:block;font-size:20px}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden}}
th,td{{padding:8px 10px;border-bottom:1px solid #e2e8f0;text-align:left;font-size:13px}}
th{{background:#f1f5f9}}
</style></head><body>
<h1>Fleet Reachability Matrix</h1>
<div class="meta">Generated {summary.get('generated_at')} · {summary.get('device_count')} device(s)
 · Inspired by Netdisco/LibreNMS daily reachability checks (offline-capable)</div>
<div class="cards">
  <div class="card"><span>OK</span><b>{counts.get('ok', 0)}</b></div>
  <div class="card"><span>Ping only</span><b>{counts.get('ping_only', 0)}</b></div>
  <div class="card"><span>Unreachable</span><b>{counts.get('unreachable', 0)}</b></div>
  <div class="card"><span>Fail</span><b>{counts.get('fail', 0)}</b></div>
</div>
<table><thead><tr><th>Host</th><th>Type</th><th>Ping</th><th>SSH</th><th>Status</th><th>Error</th></tr></thead>
<tbody>
{body}
</tbody></table>
</body></html>"""
