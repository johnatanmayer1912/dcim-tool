"""MAC trace path summary HTML (v7.0.0)."""
import re

from utils.match_highlight import escape_html, highlight_mac_match
from utils.output_chrome import wrap_html_report
from utils.mac_utils import format_mac_for_display, normalize_mac_hex

_MAC_SEP_RE = re.compile(r'[.:\-\s_]')


def _target_mac_display(mac: str) -> str:
    try:
        h = normalize_mac_hex(mac)
    except ValueError:
        return mac or ''
    if len(h) == 12:
        return format_mac_for_display(h)
    return ':'.join(h[i:i + 2] for i in range(0, len(h), 2))


def _hop_mac_cell(hop, target_mac: str) -> str:
    """HTML for MAC found column — full MAC with partial query highlighted."""
    if hop.get('resolved_mac'):
        return highlight_mac_match(hop['resolved_mac'], target_mac)
    if hop.get('ambiguous') and hop.get('distinct_macs'):
        macs = [
            highlight_mac_match(format_mac_for_display(m), target_mac)
            for m in hop['distinct_macs'][:6]
        ]
        suffix = ' …' if len(hop['distinct_macs']) > 6 else ''
        return ', '.join(macs) + suffix
    return '—'


def _first_found_mac(path_hops) -> str | None:
    for hop in path_hops or []:
        if hop.get('resolved_mac'):
            return hop['resolved_mac']
    return None


def write_mac_trace_html(filepath, target_mac, path_hops, *, found_endpoint=None, ambiguous_summary=None):
    """Write offline HTML path report for inventory MAC trace."""
    rows_html = []
    for hop in path_hops:
        status = hop.get('status', 'not_found')
        cls = 'found' if status == 'found' else ('ambiguous' if status == 'ambiguous' else ('error' if status == 'error' else ''))
        mac_cell = _hop_mac_cell(hop, target_mac)
        rows_html.append(
            f"<tr class='{cls}'><td>{hop.get('hop_index', '')}</td>"
            f"<td>{escape_html(hop.get('hostname', hop.get('device_ip', '')))}</td>"
            f"<td class='port-code'>{escape_html(hop.get('device_ip', ''))}</td>"
            f"<td class='port-code'>{mac_cell}</td>"
            f"<td>{hop.get('vlan') or '—'}</td>"
            f"<td class='port-code'>{hop.get('port') or '—'}</td>"
            f"<td>{status}</td></tr>"
        )

    found_mac = _first_found_mac(path_hops)
    endpoint = found_endpoint or '—'
    target_display = _target_mac_display(target_mac)
    target_html = highlight_mac_match(target_display, target_mac) if target_mac else '—'

    found_banner = ''
    if found_mac:
        found_html = highlight_mac_match(found_mac, target_mac)
        found_banner = (
            f"<div style='background:#f0fdf4;border-left:4px solid #22c55e;padding:12px;border-radius:8px;margin:12px 0;'>"
            f"<b>MAC found:</b> <code class='port-code'>{found_html}</code>"
            f"</div>"
        )

    endpoint_html = escape_html(str(endpoint))
    if found_mac and target_mac:
        endpoint_html = highlight_mac_match(found_mac, target_mac)
        if endpoint != found_mac:
            endpoint_html = f"{endpoint_html} <span style='color:#64748b;font-size:12px;'>({escape_html(str(endpoint))})</span>"

    amb_banner = ''
    if ambiguous_summary:
        amb_banner = (
            f"<div style='background:#fffbeb;border-left:4px solid #f59e0b;padding:12px;border-radius:8px;margin-bottom:12px;'>"
            f"<b>Partial MAC — multiple matches</b><br>{escape_html(ambiguous_summary)}</div>"
        )

    row_style = """
    tr.found td { background: #f0fdf4; }
    tr.ambiguous td { background: #fffbeb; }
    tr.error td { background: #fef2f2; }
    """
    body = f"""
<style>{row_style}</style>
<p><b>Searched for:</b> <code class="port-code">{target_html}</code></p>
{amb_banner}
{found_banner}
<div style="background:#f8fafc;border-left:4px solid #64748b;padding:12px;border-radius:8px;margin:12px 0;">
  <b>Endpoint:</b> {endpoint_html if found_mac else escape_html(str(endpoint))}
</div>
<p style="font-size:12px;color:#64748b;">Hop order follows the trace path — green rows show where the MAC was located. The <b>MAC found</b> column shows the full address with your search term highlighted.</p>
<table><thead><tr>
<th>#</th><th>Hostname</th><th>IP</th><th>MAC found</th><th>VLAN</th><th>Port</th><th>Status</th>
</tr></thead><tbody>{''.join(rows_html) or '<tr><td colspan="7">No hops recorded</td></tr>'}</tbody></table>
"""
    found = sum(1 for h in path_hops if h.get('status') == 'found')
    kpi_endpoint = found_mac or endpoint
    html = wrap_html_report(
        'MAC Path Trace',
        body,
        subtitle=f'{len(path_hops)} hop(s) scanned',
        hints=[
            'Trace walks your inventory in order until the MAC is located',
            'Partial search: yellow highlight shows which part of the full MAC matched',
            'found = exact match · ambiguous = multiple partial matches on that device',
        ],
        kpis=[
            {'label': 'Hops', 'value': str(len(path_hops))},
            {'label': 'Found', 'value': str(found), 'tone': 'ok' if found else 'bad'},
            {'label': 'MAC', 'value': (str(kpi_endpoint)[:24] + '…') if len(str(kpi_endpoint)) > 24 else str(kpi_endpoint)},
        ],
        page_title=f'MAC Trace — {target_mac}',
    )
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    return filepath
