"""Interface Manager HTML reports (v7.0.45)."""
from __future__ import annotations

from datetime import datetime
from html import escape

from utils.output_chrome import wrap_html_report


def write_interface_report_html(filepath, data: dict, host: str, operation: str) -> str:
    """Write structured HTML report for IM discover/validate/deploy operations."""
    ts = data.get('timestamp') or datetime.now().isoformat()
    true_host = escape(str(data.get('true_host', host)))
    vendor = escape(str(data.get('vendor', 'N/A')))
    dtype = escape(str(data.get('device_type', 'N/A')))
    op = escape(operation)

    sections = []

    validation = data.get('validation_results') or data.get('validation')
    pass_n = fail_n = 0
    if validation and operation in ('validate', 'deploy'):
        rows = []
        for key, block in validation.items():
            if not isinstance(block, dict):
                continue
            passed = block.get('passed', False)
            if passed:
                pass_n += 1
            else:
                fail_n += 1
            color = '#16a34a' if passed else '#dc2626'
            rows.append(
                f"<tr><td>{escape(key)}</td>"
                f"<td style='color:{color};font-weight:700;'>{'PASS' if passed else 'FAIL'}</td>"
                f"<td>{escape(block.get('message', '') or '')}</td></tr>"
            )
        if rows:
            sections.append(
                "<h2 style='font-size:14px;margin:16px 0 8px;'>Validation pipeline</h2>"
                "<table><thead><tr><th>Check</th><th>Result</th><th>Detail</th></tr></thead><tbody>"
                + ''.join(rows) + "</tbody></table>"
            )

    if operation == 'discover':
        interfaces = data.get('interfaces') or []
        iface_rows = []
        for iface in interfaces[:200]:
            iface_rows.append(
                f"<tr><td><code class='port-code'>{escape(str(iface.get('name', '')))}</code></td>"
                f"<td>{escape(str(iface.get('status', '')))}</td>"
                f"<td>{escape(str(iface.get('l2_l3_mode', '')))}</td>"
                f"<td>{escape(str(iface.get('description', '')))}</td></tr>"
            )
        more = (
            f"<p style='font-size:12px;color:#64748b;'>Showing first 200 of {len(interfaces)} interfaces.</p>"
            if len(interfaces) > 200 else ''
        )
        sections.append(
            f"<h2 style='font-size:14px;margin:16px 0 8px;'>Interfaces ({len(interfaces)})</h2>{more}"
            "<table><thead><tr><th>Name</th><th>Status</th><th>Mode</th><th>Description</th>"
            "</tr></thead><tbody>" + ''.join(iface_rows) + "</tbody></table>"
        )

    deploy = data.get('deployment') or data.get('deploy_result')
    if deploy and operation == 'deploy':
        sections.append(f"<h2 style='font-size:14px;margin:16px 0 8px;'>Deployment log</h2><pre>{escape(str(deploy))}</pre>")

    body = (
        f"<p><b>Hostname:</b> {true_host} · <b>IP:</b> {escape(host)}</p>"
        f"<p><b>Vendor:</b> {vendor} · <b>Type:</b> {dtype} · <b>Operation:</b> {op}</p>"
        f"<p style='font-size:12px;color:#64748b;'>Timestamp: {escape(ts)}</p>"
        + (''.join(sections) or "<p>No detailed sections for this operation.</p>")
    )

    hints = [
        'discover = read-only inventory · validate = pre-change checks · deploy = live push',
        'All FAIL rows must be resolved before approving a production deploy',
        'Keep this report with your change ticket for audit trail',
    ]
    if operation == 'deploy':
        hints.insert(0, 'DEPLOY operation — verify validation PASS on every row before closing the change')

    kpis = [{'label': 'Operation', 'value': operation.title()}]
    if validation:
        kpis.append({'label': 'Validation PASS', 'value': str(pass_n), 'tone': 'ok'})
        if fail_n:
            kpis.append({'label': 'Validation FAIL', 'value': str(fail_n), 'tone': 'bad'})

    html = wrap_html_report(
        'Interface Manager Report',
        body,
        subtitle=f'{true_host} ({host})',
        hints=hints,
        kpis=kpis,
        page_title=f'Interface Manager — {true_host}',
    )
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    return filepath
