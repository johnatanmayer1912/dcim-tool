"""SSH collectors for failure correlation (logs + interface/vPC context)."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
import re

from modules.network_base import safe_connection, resolve_hostname_from_connection

LogFn = Optional[Callable[[str], None]]

# Ordered command sets — keep bounded for offline / lab speed
_IOS_CMDS = [
    ('logging', 'show logging'),
    ('iface_status', 'show interfaces status'),
    ('iface_brief', 'show ip interface brief'),
    ('errdisable', 'show errdisable recovery'),
]
_NXOS_CMDS = [
    ('logging', 'show logging logfile'),
    ('logging_last', 'show logging last 200'),
    ('iface_brief', 'show interface brief'),
    ('vpc', 'show vpc'),
    ('vpc_brief', 'show vpc brief'),
]


def _platform(device_type: str) -> str:
    dt = (device_type or '').lower()
    if 'nxos' in dt or 'nexus' in dt:
        return 'cisco_nxos'
    return 'cisco_ios'


def collect_device_failure_evidence(
    device: Dict[str, Any],
    user: str,
    pwd: str,
    enb_pwd: str = '',
    log: LogFn = None,
) -> Dict[str, Any]:
    """Connect and gather logging + operational context for one device."""
    host = device.get('host') or device.get('ip') or '?'
    port = int(device.get('port') or 22)
    dtype = device.get('device_type') or 'cisco_ios'
    platform = _platform(dtype)
    result: Dict[str, Any] = {
        'host': host,
        'true_host': host,
        'port': port,
        'platform': platform,
        'status': 'error',
        'raw': {},
        'errors': [],
        'interfaces_down': {},
        'vpc_peer_down': False,
        'vpc_summary': '',
    }
    _log = log or (lambda _m: None)

    cmds = _NXOS_CMDS if platform == 'cisco_nxos' else _IOS_CMDS
    try:
        with safe_connection(device, user, pwd, enb_pwd, log_func=_log) as conn:
            result['true_host'] = resolve_hostname_from_connection(conn, host) or host
            for key, cmd in cmds:
                try:
                    out = conn.send_command(cmd, read_timeout=60) or ''
                except Exception as exc:
                    # Fallback for NX-OS logfile vs last
                    if key == 'logging' and platform == 'cisco_nxos':
                        try:
                            out = conn.send_command('show logging last 200', read_timeout=60) or ''
                        except Exception as exc2:
                            result['errors'].append(f'{cmd}: {exc2}')
                            out = ''
                    else:
                        result['errors'].append(f'{cmd}: {exc}')
                        out = ''
                result['raw'][key] = out
                _log(f"[CORR] {host}: {cmd} → {len(out)} chars")

            # Parse down interfaces from brief/status
            result['interfaces_down'] = _parse_down_interfaces(
                result['raw'].get('iface_brief') or result['raw'].get('iface_status') or '',
                platform,
            )
            vpc_blob = (result['raw'].get('vpc') or '') + '\n' + (result['raw'].get('vpc_brief') or '')
            result['vpc_summary'], result['vpc_peer_down'] = _parse_vpc(vpc_blob)
            result['status'] = 'success' if result['raw'] else 'partial'
    except Exception as exc:
        result['errors'].append(str(exc))
        result['status'] = 'error'
        _log(f"[CORR] {host}: connect failed — {exc}")
    return result


def merge_logging_blob(raw: Dict[str, str]) -> str:
    """Prefer richest logging output."""
    parts = []
    for key in ('logging', 'logging_last'):
        blob = raw.get(key) or ''
        if blob.strip():
            parts.append(blob)
    return '\n'.join(parts)


def _parse_down_interfaces(text: str, platform: str) -> Dict[str, str]:
    down: Dict[str, str] = {}
    for line in (text or '').splitlines():
        if not line.strip() or line.strip().startswith('-') or 'Interface' in line and 'Status' in line:
            continue
        # NX-OS brief: Eth1/1 ... down ...
        m = re.match(
            r'^(\S+)\s+.*\b(down|out-of-service|disabled|notConnect|err-disabled)\b',
            line.strip(),
            re.I,
        )
        if m:
            iface, st = m.group(1), m.group(2).lower()
            if iface.lower() in ('interface', 'port', 'ethernet'):
                continue
            if 'up' in line.lower() and 'down' not in line.lower():
                continue
            down[iface] = st
            continue
        # IOS status: Gi1/0/1 ... notconnect / disabled
        m2 = re.match(r'^(\S+)\s+\S+\s+\S+\s+(\S+)', line.strip())
        if m2 and m2.group(2).lower() in ('notconnect', 'disabled', 'err-disabled', 'down'):
            down[m2.group(1)] = m2.group(2).lower()
    return down


def _parse_vpc(text: str) -> tuple:
    summary = ''
    peer_down = False
    t = text or ''
    for line in t.splitlines():
        if 'peer status' in line.lower() or 'peer-keepalive' in line.lower() or 'vPC domain' in line:
            summary += line.strip() + '; '
        if re.search(r'peer.*(down|fail)|keepalive.*(down|fail|timeout)|peer adjacency.*fail', line, re.I):
            peer_down = True
        if re.search(r'peer-link\s*:\s*down', line, re.I):
            peer_down = True
    return summary.strip('; '), peer_down
