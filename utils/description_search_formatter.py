"""Description search HTML report (search_it)."""
from utils.match_highlight import escape_html, highlight_text_match
from utils.output_chrome import wrap_html_report
from utils.search_relevance import sort_description_rows, text_match_score


def write_description_search_html(
    filepath,
    search_term,
    device_rows,
    *,
    total_matches=0,
    devices_scanned=0,
):
    """
    device_rows: list of dicts with keys hostname, device_ip, interface, status, description, source, error
    """
    ranked = sort_description_rows(search_term, [r for r in device_rows if not r.get('error')])
    errors = [r for r in device_rows if r.get('error')]
    ordered = ranked + errors

    tr_html = []
    for r in ordered:
        if r.get('error'):
            tr_html.append(
                f'<tr class="err"><td colspan="6"><b>{r.get("hostname", r.get("device_ip", "?"))}</b> — '
                f'{r.get("error")}</td></tr>'
            )
            continue
        score = text_match_score(search_term, r.get('description', ''), r.get('interface', ''))
        match_cls = 'match-exact' if score >= 85 else ('match-partial' if score >= 50 else '')
        tr_html.append(
            f'<tr class="{match_cls}"><td>{r.get("hostname", "")}</td><td>{r.get("device_ip", "")}</td>'
            f'<td><code class="port-code">{highlight_text_match(r.get("interface", ""), search_term)}</code></td>'
            f'<td>{r.get("status", "")}</td>'
            f'<td>{highlight_text_match(r.get("description", ""), search_term)}</td>'
            f'<td class="score">{score}</td></tr>'
        )
    body_rows = ''.join(tr_html) or '<tr><td colspan="6">No matches found for this search term.</td></tr>'
    body = f"""
<style>
  tr.err td {{ background: #fef2f2; color: #991b1b; }}
  tr.match-exact td {{ background: #f0fdf4; }}
  tr.match-partial td {{ background: #fffbeb; }}
  td.score {{ color: #64748b; font-size: 11px; width: 48px; text-align: right; }}
</style>
<p>Searched for: <b>{escape_html(search_term)}</b></p>
<table>
<thead><tr><th>Hostname</th><th>Mgmt IP</th><th>Interface</th><th>Status</th><th>Description</th><th>Score</th></tr></thead>
<tbody>{body_rows}</tbody>
</table>
"""
    html = wrap_html_report(
        'Interface Description Search',
        body,
        subtitle=f'{total_matches} match(es) across {devices_scanned} device(s)',
        hints=[
            'Results ranked by relevance — higher Score = stronger match',
            'Green rows = strong match · Amber = partial · Red = device error',
            'Use interface + description columns to locate circuits and handoff ports',
        ],
        kpis=[
            {'label': 'Matches', 'value': str(total_matches), 'tone': 'ok' if total_matches else 'warn'},
            {'label': 'Devices scanned', 'value': str(devices_scanned)},
            {'label': 'Errors', 'value': str(len(errors)), 'tone': 'bad' if errors else 'ok'},
        ],
        page_title=f'Description Search — {search_term}',
    )
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    return filepath
