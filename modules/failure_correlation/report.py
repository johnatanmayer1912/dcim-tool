"""Offline HTML + JSON reports for failure correlation."""
from __future__ import annotations

from html import escape
from typing import Any, Dict, List
import json


def render_correlation_html(bundle: Dict[str, Any]) -> str:
    roll = bundle.get('rollups') or {}
    devices = bundle.get('devices') or []
    top = roll.get('top_hypotheses') or []
    gen = escape(str(bundle.get('generated_at') or ''))
    cards = []
    for h in top:
        conf = escape(str(h.get('confidence_label') or ''))
        sev = escape(str(h.get('severity') or 'info'))
        evid = ''.join(
            f'<li><code>{escape(e)}</code></li>' for e in (h.get('evidence') or [])[:6]
        )
        incomplete = (
            '<div class="badge warn">incomplete observation</div>'
            if h.get('incomplete') else ''
        )
        cards.append(f'''
        <article class="card sev-{sev}">
          <header>
            <h3>{escape(str(h.get('title') or ''))}</h3>
            <div class="meta">
              <span class="badge">{escape(str(h.get('host') or ''))}</span>
              <span class="badge">{escape(str(h.get('object') or ''))}</span>
              <span class="badge conf-{conf}">confidence {conf} ({h.get('confidence')})</span>
              <span class="badge">{sev}</span>
              {incomplete}
            </div>
          </header>
          <p class="why">{escape(str(h.get('why') or ''))}</p>
          <p class="hint"><strong>Next check:</strong> {escape(str(h.get('hint') or ''))}</p>
          <details>
            <summary>Evidence ({h.get('evidence_count') or 0})</summary>
            <ul class="evid">{evid or '<li><em>No log lines — CLI context only</em></li>'}</ul>
          </details>
        </article>''')

    host_rows = []
    for d in devices:
        c = d.get('counts') or {}
        host_rows.append(
            '<tr>'
            f'<td>{escape(str(d.get("true_host") or d.get("host")))}</td>'
            f'<td>{escape(str(d.get("platform") or ""))}</td>'
            f'<td>{escape(str(d.get("status") or ""))}</td>'
            f'<td>{c.get("relevant", 0)}</td>'
            f'<td>{len(d.get("hypotheses") or [])}</td>'
            f'<td>{len(d.get("errors") or [])}</td>'
            '</tr>'
        )

    by_cat = roll.get('by_category') or {}
    cat_chips = ' '.join(
        f'<span class="chip">{escape(k)}: {v}</span>' for k, v in sorted(by_cat.items())
    ) or '<span class="chip">No findings</span>'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Failure Correlation — Network Swiss Tool Pro</title>
  <style>
    :root {{
      --bg:#070d18; --panel:#0f172a; --bdr:#1e293b; --tx:#e2e8f0; --mut:#94a3b8;
      --acc:#00c2d7; --red:#ef4444; --ora:#f59e0b; --grn:#10b981;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin:0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif;
      background: radial-gradient(1200px 600px at 10% -10%, #123 0%, var(--bg) 55%);
      color: var(--tx); line-height: 1.45;
    }}
    header.app {{
      padding: 18px 22px; border-bottom: 1px solid var(--bdr);
      background: rgba(15,23,42,0.92); position: sticky; top:0; z-index:5;
      display:flex; flex-wrap:wrap; gap:12px; align-items:center; justify-content:space-between;
    }}
    header.app h1 {{ margin:0; font-size:18px; }}
    header.app .sub {{ color:var(--mut); font-size:12px; }}
    .brand {{
      width:34px; height:34px; border-radius:10px; display:flex; align-items:center; justify-content:center;
      background: linear-gradient(145deg,#00c2d7,#14b8a6); font-weight:800; font-size:11px;
    }}
    main {{ padding: 18px 22px 40px; max-width: 1200px; margin: 0 auto; }}
    .kpis {{ display:flex; flex-wrap:wrap; gap:10px; margin: 14px 0 18px; }}
    .kpi {{
      background: var(--panel); border:1px solid var(--bdr); border-radius:10px;
      padding:10px 14px; min-width:110px;
    }}
    .kpi b {{ display:block; font-size:20px; color: var(--acc); }}
    .kpi span {{ font-size:11px; color:var(--mut); text-transform:uppercase; letter-spacing:.04em; }}
    .chips {{ display:flex; flex-wrap:wrap; gap:6px; margin-bottom:16px; }}
    .chip {{
      font-size:11px; padding:3px 8px; border-radius:999px; border:1px solid var(--bdr);
      background:#111827; color:var(--mut);
    }}
    .card {{
      background: var(--panel); border:1px solid var(--bdr); border-radius:12px;
      padding:14px 16px; margin-bottom:12px;
    }}
    .card.sev-critical {{ border-left: 4px solid var(--red); }}
    .card.sev-error {{ border-left: 4px solid #f97316; }}
    .card.sev-warning {{ border-left: 4px solid var(--ora); }}
    .card h3 {{ margin:0 0 8px; font-size:15px; }}
    .meta {{ display:flex; flex-wrap:wrap; gap:6px; margin-bottom:8px; }}
    .badge {{
      font-size:10px; font-weight:700; padding:2px 7px; border-radius:6px;
      background:#1e293b; color:#cbd5e1; text-transform:uppercase;
    }}
    .badge.conf-high {{ background: rgba(16,185,129,.15); color:#6ee7b7; }}
    .badge.conf-medium {{ background: rgba(245,158,11,.15); color:#fde68a; }}
    .badge.conf-low {{ background: rgba(148,163,184,.15); color:#cbd5e1; }}
    .badge.warn {{ background: rgba(245,158,11,.2); color:#fde68a; }}
    .why {{ margin:8px 0; color:#f1f5f9; font-size:13px; }}
    .hint {{ margin:6px 0 0; color:var(--mut); font-size:12px; }}
    details {{ margin-top:8px; }}
    summary {{ cursor:pointer; color:var(--acc); font-size:12px; font-weight:650; }}
    ul.evid {{ margin:8px 0 0; padding-left:18px; }}
    ul.evid code {{
      font-size:11px; color:#cbd5e1; white-space:pre-wrap; word-break:break-word;
    }}
    table {{ width:100%; border-collapse:collapse; font-size:12px; margin-top:8px; }}
    th, td {{ border-bottom:1px solid var(--bdr); padding:8px 6px; text-align:left; }}
    th {{ color:var(--mut); font-size:11px; text-transform:uppercase; }}
    .note {{
      margin-top:18px; padding:12px 14px; border-radius:10px; border:1px solid #334155;
      background: rgba(15,23,42,.8); color:var(--mut); font-size:12px;
    }}
  </style>
</head>
<body>
  <header class="app">
    <div style="display:flex;gap:12px;align-items:center;">
      <div class="brand">NST</div>
      <div>
        <h1>Failure Correlation Engine</h1>
        <div class="sub">SSH logs + interface/vPC context · offline · not a SIEM · {gen}</div>
      </div>
    </div>
  </header>
  <main>
    <div class="kpis">
      <div class="kpi"><b>{roll.get("hypothesis_count", 0)}</b><span>Hypotheses</span></div>
      <div class="kpi"><b>{len(devices)}</b><span>Devices</span></div>
      <div class="kpi"><b>{len(roll.get("hosts_with_findings") or [])}</b><span>Hosts w/ findings</span></div>
      <div class="kpi"><b>{(roll.get("by_severity") or {}).get("critical", 0)}</b><span>Critical</span></div>
    </div>
    <div class="chips">{cat_chips}</div>

    <h2 style="font-size:14px;color:var(--mut);margin:8px 0;">Ranked explanations</h2>
    {''.join(cards) if cards else '<div class="card"><p class="why">No correlated failures. Either the fabric is healthy, or logging buffers were empty (incomplete observation).</p></div>'}

    <h2 style="font-size:14px;color:var(--mut);margin:20px 0 8px;">Per-device collection</h2>
    <div class="card">
      <table>
        <thead><tr><th>Host</th><th>Platform</th><th>Status</th><th>Relevant</th><th>Hypotheses</th><th>Errors</th></tr></thead>
        <tbody>{''.join(host_rows)}</tbody>
      </table>
    </div>
    <div class="note">
      Honesty: NST explains failures from CLI evidence only. It does not invent root causes,
      does not replace your SIEM, and marks incomplete observations when logs and operational
      state disagree or logs are missing. Peer tools (LibreNMS eventlog, SuzieQ queries, Loki)
      remain complementary for long-term retention.
    </div>
  </main>
</body>
</html>
'''


def write_json(path: str, bundle: Dict[str, Any]) -> None:
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(bundle, fh, indent=2, default=str)
