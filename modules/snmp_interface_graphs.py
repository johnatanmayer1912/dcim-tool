"""SNMP interface counter snapshot → offline HTML sparkline graphs.

Uses IF-MIB ifInOctets/ifOutOctets when SNMP credentials are configured.
Falls back to empty series (honest UI) when SNMP is unavailable — never invents traffic.
"""
from __future__ import annotations

import html
import time
from typing import Any, Dict, List, Optional, Tuple


# IF-MIB
OID_IF_DESCR = '1.3.6.1.2.1.2.2.1.2'
OID_IF_IN_OCTETS = '1.3.6.1.2.1.2.2.1.10'
OID_IF_OUT_OCTETS = '1.3.6.1.2.1.2.2.1.16'
OID_IF_OPER_STATUS = '1.3.6.1.2.1.2.2.1.8'


def _snmp_walk(host: str, credentials: Dict[str, Any], oid: str) -> List[Tuple[str, str]]:
    """Return list of (oid_suffix, value) from SNMP walk. Empty on any failure."""
    try:
        from pysnmp.hlapi import (
            CommunityData,
            ContextData,
            ObjectIdentity,
            ObjectType,
            SnmpEngine,
            UdpTransportTarget,
            nextCmd,
            UsmUserData,
            usmHMACMD5AuthProtocol,
            usmHMACSHAAuthProtocol,
            usmNoAuthProtocol,
            usmNoPrivProtocol,
        )
    except ImportError:
        try:
            from pysnmp_lextudio.hlapi import (  # type: ignore
                CommunityData,
                ContextData,
                ObjectIdentity,
                ObjectType,
                SnmpEngine,
                UdpTransportTarget,
                nextCmd,
                UsmUserData,
                usmHMACMD5AuthProtocol,
                usmHMACSHAAuthProtocol,
                usmNoAuthProtocol,
                usmNoPrivProtocol,
            )
        except ImportError:
            return []

    ver = str(credentials.get('snmp_version') or '').strip().lower()
    port = int(credentials.get('snmp_port') or 161)
    timeout = float(credentials.get('snmp_timeout') or 2.0)
    auth = None
    if ver in ('2c', 'v2c', '2'):
        community = (credentials.get('snmp_community') or '').strip()
        if not community:
            return []
        auth = CommunityData(community, mpModel=1)
    elif ver in ('3', 'v3'):
        user = (credentials.get('snmp_v3_user') or '').strip()
        if not user:
            return []
        auth = UsmUserData(user)
    else:
        return []

    rows: List[Tuple[str, str]] = []
    try:
        for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
            SnmpEngine(),
            auth,
            UdpTransportTarget((host, port), timeout=timeout, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
            lexicographicMode=False,
        ):
            if errorIndication or errorStatus:
                break
            for varBind in varBinds:
                name, val = varBind
                rows.append((str(name), str(val)))
                if len(rows) >= 128:
                    return rows
    except Exception:
        return []
    return rows


def collect_interface_counters(
    host: str,
    credentials: Dict[str, Any],
    samples: int = 2,
    interval_sec: float = 1.0,
) -> Dict[str, Any]:
    """Two-sample SNMP counter delta for sparkline HTML.

    Honest: if SNMP missing/fails, returns status=unavailable (no fake graphs).
    """
    from modules.snmp_asset_collector import snmp_credentials_configured

    if not snmp_credentials_configured(credentials):
        return {
            'status': 'unavailable',
            'host': host,
            'reason': 'SNMP credentials not configured on selected profile',
            'interfaces': [],
        }

    samples = max(2, min(int(samples or 2), 6))
    interval_sec = max(0.5, min(float(interval_sec or 1.0), 10.0))

    def _one_shot() -> Dict[str, Dict[str, Any]]:
        descrs = _snmp_walk(host, credentials, OID_IF_DESCR)
        inns = dict(_snmp_walk(host, credentials, OID_IF_IN_OCTETS))
        outs = dict(_snmp_walk(host, credentials, OID_IF_OUT_OCTETS))
        by_idx: Dict[str, Dict[str, Any]] = {}
        for oid, name in descrs:
            idx = oid.rsplit('.', 1)[-1]
            by_idx[idx] = {
                'name': name,
                'in_octets': _to_int(inns.get(oid) or inns.get(OID_IF_IN_OCTETS + '.' + idx)),
                'out_octets': _to_int(outs.get(oid) or outs.get(OID_IF_OUT_OCTETS + '.' + idx)),
            }
        # match by index if OID strings differ
        if not by_idx and inns:
            for oid, val in inns.items():
                idx = oid.rsplit('.', 1)[-1]
                by_idx.setdefault(idx, {'name': f'if{idx}', 'in_octets': 0, 'out_octets': 0})
                by_idx[idx]['in_octets'] = _to_int(val)
            for oid, val in outs.items():
                idx = oid.rsplit('.', 1)[-1]
                by_idx.setdefault(idx, {'name': f'if{idx}', 'in_octets': 0, 'out_octets': 0})
                by_idx[idx]['out_octets'] = _to_int(val)
        return by_idx

    series: List[Dict[str, Dict[str, Any]]] = []
    for i in range(samples):
        series.append(_one_shot())
        if i + 1 < samples:
            time.sleep(interval_sec)

    if not series or not series[0]:
        return {
            'status': 'unavailable',
            'host': host,
            'reason': 'SNMP walk returned no IF-MIB rows',
            'interfaces': [],
        }

    # Build per-interface delta series (Bps between samples)
    names = {}
    for shot in series:
        for idx, row in shot.items():
            names[idx] = row.get('name') or f'if{idx}'

    interfaces: List[Dict[str, Any]] = []
    for idx, name in sorted(names.items(), key=lambda x: x[1]):
        in_bps: List[float] = []
        out_bps: List[float] = []
        for i in range(1, len(series)):
            a = series[i - 1].get(idx) or {}
            b = series[i].get(idx) or {}
            din = max(0, _to_int(b.get('in_octets')) - _to_int(a.get('in_octets')))
            dout = max(0, _to_int(b.get('out_octets')) - _to_int(a.get('out_octets')))
            in_bps.append(round(din / interval_sec, 1))
            out_bps.append(round(dout / interval_sec, 1))
        interfaces.append({
            'index': idx,
            'name': name,
            'in_bps': in_bps,
            'out_bps': out_bps,
            'in_last': in_bps[-1] if in_bps else 0,
            'out_last': out_bps[-1] if out_bps else 0,
        })

    # Prefer up/busy interfaces first
    interfaces.sort(key=lambda r: -(r['in_last'] + r['out_last']))
    return {
        'status': 'ok',
        'host': host,
        'samples': samples,
        'interval_sec': interval_sec,
        'interfaces': interfaces[:48],
        'note': 'IF-MIB octet deltas — not NetFlow. Offline HTML snapshot only.',
    }


def _to_int(v: Any) -> int:
    try:
        return int(str(v).strip())
    except Exception:
        return 0


def counters_to_html(payload: Dict[str, Any]) -> str:
    host = html.escape(str(payload.get('host') or ''))
    status = payload.get('status') or 'unavailable'
    rows = payload.get('interfaces') or []
    note = html.escape(str(payload.get('note') or payload.get('reason') or ''))

    def spark(vals: List[float], color: str) -> str:
        if not vals:
            return '<span class="empty">—</span>'
        mx = max(vals) or 1.0
        bars = ''.join(
            f'<i style="height:{max(4, int(40 * (v / mx)))}px;background:{color}"></i>'
            for v in vals
        )
        return f'<span class="spark">{bars}</span>'

    body_rows = []
    for r in rows:
        body_rows.append(
            '<tr>'
            f'<td>{html.escape(str(r.get("name") or ""))}</td>'
            f'<td>{spark(r.get("in_bps") or [], "#0a84ff")}</td>'
            f'<td>{spark(r.get("out_bps") or [], "#30d158")}</td>'
            f'<td class="num">{html.escape(str(r.get("in_last") or 0))}</td>'
            f'<td class="num">{html.escape(str(r.get("out_last") or 0))}</td>'
            '</tr>'
        )
    if not body_rows:
        body_rows.append('<tr><td colspan="5">No interface counters. Configure SNMP on the credential profile.</td></tr>')

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>SNMP Interface Graphs — {host}</title>
<style>
  :root {{ --bg:#f5f5f7; --card:#fff; --text:#1d1d1f; --muted:#86868b; --line:#d2d2d7; }}
  body {{ margin:0; font:13px/1.45 -apple-system,BlinkMacSystemFont,"SF Pro Text",system-ui,sans-serif;
         background:linear-gradient(180deg,#fbfbfd 0%,var(--bg) 100%); color:var(--text); }}
  .wrap {{ max-width:960px; margin:32px auto; padding:0 20px; }}
  h1 {{ font-size:22px; font-weight:650; letter-spacing:-.02em; margin:0 0 6px; }}
  .meta {{ color:var(--muted); margin-bottom:18px; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:16px;
           box-shadow:0 8px 28px rgba(0,0,0,.06); overflow:hidden; }}
  table {{ width:100%; border-collapse:collapse; }}
  th,td {{ padding:10px 14px; border-bottom:1px solid var(--line); text-align:left; }}
  th {{ font-size:11px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); }}
  .num {{ font-variant-numeric:tabular-nums; text-align:right; }}
  .spark {{ display:inline-flex; align-items:flex-end; gap:2px; height:40px; }}
  .spark i {{ display:block; width:8px; border-radius:2px 2px 0 0; }}
  .badge {{ display:inline-block; padding:3px 10px; border-radius:999px; font-size:11px; font-weight:600;
            background:{'#d1fadf' if status=='ok' else '#ffe8cc'}; color:{'#0b7a3b' if status=='ok' else '#9a3412'}; }}
</style></head><body><div class="wrap">
  <h1>Interface counter graphs</h1>
  <p class="meta"><span class="badge">{html.escape(status)}</span> · {host} · {note}</p>
  <div class="card"><table>
    <thead><tr><th>Interface</th><th>In B/s</th><th>Out B/s</th><th>In last</th><th>Out last</th></tr></thead>
    <tbody>{''.join(body_rows)}</tbody>
  </table></div>
</div></body></html>"""
