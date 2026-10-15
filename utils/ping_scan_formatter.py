"""Network ping scan HTML report (search_it)."""
from datetime import datetime

from utils.output_chrome import wrap_html_report


def write_ping_scan_html(
    filepath,
    network,
    used_ips,
    unused_ips,
    *,
    total_hosts=0,
):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    used_rows = ''.join(
        f'<tr><td class="port-code">{ip}</td><td style="color:#16a34a;font-weight:600;">Responsive</td></tr>'
        for ip in sorted(used_ips)
    )
    unused_rows = ''.join(
        f'<tr><td class="port-code">{ip}</td><td style="color:#64748b;">No ICMP reply</td></tr>'
        for ip in sorted(unused_ips)
    )
    body = f"""
<p><b>Network:</b> {network} · Scanned {ts}</p>
<h2 style="font-size:14px;margin:20px 0 8px;color:#166534;">Responsive IPs ({len(used_ips)})</h2>
<p style="font-size:12px;color:#64748b;margin-bottom:8px;">These addresses replied to ping — likely in use on the subnet.</p>
<table><thead><tr><th>IP Address</th><th>State</th></tr></thead>
<tbody>{used_rows or '<tr><td colspan="2">None responded</td></tr>'}</tbody></table>
<h2 style="font-size:14px;margin:24px 0 8px;color:#475569;">Unresponsive IPs ({len(unused_ips)})</h2>
<p style="font-size:12px;color:#64748b;margin-bottom:8px;">No reply does not always mean free — firewalls may block ICMP.</p>
<table><thead><tr><th>IP Address</th><th>State</th></tr></thead>
<tbody>{unused_rows or '<tr><td colspan="2">All hosts responded</td></tr>'}</tbody></table>
"""
    html = wrap_html_report(
        'Network Ping Scan',
        body,
        subtitle=f'Subnet {network}',
        hints=[
            'Responsive = device answered ICMP within the scan timeout',
            'Unresponsive may be free IP, powered off, or ACL blocking ping',
            'Use responsive list to update IPAM; verify unresponsive before assigning',
        ],
        kpis=[
            {'label': 'Hosts scanned', 'value': str(total_hosts)},
            {'label': 'Responsive', 'value': str(len(used_ips)), 'tone': 'ok'},
            {'label': 'Unresponsive', 'value': str(len(unused_ips)), 'tone': 'warn' if unused_ips else ''},
        ],
        page_title=f'Ping Scan — {network}',
    )
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    return filepath
