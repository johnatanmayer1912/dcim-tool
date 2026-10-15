"""Cisco ACI APIC fabric node inventory via REST."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from urllib import error, request

from modules.mock_asset_lab import is_mock_host, mock_aci_inventory


def collect_aci_fabric_nodes(
    host: str,
    credentials: Dict[str, Any],
    log_func=None,
    timeout: float = 15.0,
) -> List[Dict[str, Any]]:
    host = (host or '').strip()
    if is_mock_host(host):
        rows = mock_aci_inventory(host)
        if log_func:
            log_func(f'[{host}] Mock ACI fabric inventory: {len(rows)} node(s)')
        return rows

    user = (credentials.get('username') or '').strip()
    password = credentials.get('password') or ''
    if not user or not password:
        raise RuntimeError('APIC credentials required (username/password)')

    url = f'https://{host}/api/class/fabricNode.json'
    req = request.Request(url)
    token = f'{user}:{password}'.encode('utf-8')
    import base64
    req.add_header('Authorization', 'Basic ' + base64.b64encode(token).decode('ascii'))
    req.add_header('Accept', 'application/json')
    ctx = None
    try:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    except Exception:
        ctx = None

    if log_func:
        log_func(f'[{host}] Querying APIC fabric nodes...')
    try:
        with request.urlopen(req, timeout=timeout, context=ctx) as resp:
            payload = json.loads(resp.read().decode('utf-8', errors='replace'))
    except error.HTTPError as exc:
        raise RuntimeError(f'APIC HTTP {exc.code}') from exc
    except error.URLError as exc:
        raise RuntimeError(f'APIC unreachable: {exc.reason}') from exc

    rows: List[Dict[str, Any]] = []
    for item in payload.get('imdata', []):
        attrs = (item.get('fabricNode') or {}).get('attributes') or {}
        rows.append({
            'hostname': attrs.get('name') or host,
            'pid': attrs.get('model') or '',
            'serial_number': attrs.get('serial') or '',
            'software_version': attrs.get('version') or '',
            'role': attrs.get('role') or '',
            'node_id': attrs.get('id') or '',
            'address': attrs.get('address') or host,
            'collection_method': 'aci_rest',
        })
    return rows
