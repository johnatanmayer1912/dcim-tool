"""DOM / transceiver optics from device CLI. Snapshot only — not a cable cert."""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional


def _norm_port(name: str) -> str:
    s = (name or '').strip()
    return (
        s.replace('Ethernet', 'Eth')
        .replace('GigabitEthernet', 'Gi')
        .replace('TenGigabitEthernet', 'Te')
        .replace('FastEthernet', 'Fa')
        .replace('HundredGigE', 'Hu')
        .strip()
    )


def _cli_unsupported(text: str) -> bool:
    low = (text or '').lower()
    return (not low.strip()) or any(tok in low for tok in (
        'invalid input', 'invalid command', 'syntax error', 'not supported',
        'no such', 'unknown command',
    ))


def parse_nxos_transceiver(text: str) -> Dict[str, Dict[str, Any]]:
    """Parse NX-OS `show interface transceiver details` (or per-port)."""
    out: Dict[str, Dict[str, Any]] = {}
    current = ''
    for line in (text or '').splitlines():
        m = re.match(r'^(Eth(?:ernet)?\S+|Gi\S+|Te\S+|Hu\S+)\s*$', line.strip(), re.I)
        if m and 'transceiver' not in line.lower():
            current = _norm_port(m.group(1))
            out.setdefault(current, {})
            continue
        if not current:
            hm = re.match(r'^(Eth(?:ernet)?\S+)\s+', line.strip(), re.I)
            if hm:
                current = _norm_port(hm.group(1))
                out.setdefault(current, {})
        if not current:
            continue
        rx = re.search(r'Rx\s*Power\s*[:=]\s*([+\-]?\d+(?:\.\d+)?)\s*dBm', line, re.I)
        tx = re.search(r'Tx\s*Power\s*[:=]\s*([+\-]?\d+(?:\.\d+)?)\s*dBm', line, re.I)
        if rx:
            out[current]['rx_dbm'] = float(rx.group(1))
        if tx:
            out[current]['tx_dbm'] = float(tx.group(1))
        if 'not present' in line.lower() or 'transceiver is not' in line.lower():
            out[current]['present'] = False
        if 'transceiver is present' in line.lower():
            out[current]['present'] = True
        if re.search(r'\b(alarm|warning)\b', line, re.I) and 'no alarm' not in line.lower():
            if 'low' in line.lower() or 'high' in line.lower():
                out[current]['alarm'] = True
    return {k: v for k, v in out.items() if v}


def parse_ios_transceiver_table(text: str) -> Dict[str, Dict[str, Any]]:
    """Parse IOS-XE `show interfaces transceiver` table (Tx/Rx dBm columns)."""
    out: Dict[str, Dict[str, Any]] = {}
    if _cli_unsupported(text):
        return out
    for line in (text or '').splitlines():
        m = re.match(
            r'^((?:Gi|Te|Fa|Hu|Tw|Fo)\S+)\s+[+\-]?\d+(?:\.\d+)?\s+([+\-]?\d+(?:\.\d+)?)\s+([+\-]?\d+(?:\.\d+)?)',
            line.strip(),
        )
        if not m:
            m = re.match(
                r'^((?:Gi|Te|Fa|Hu|GigabitEthernet|TenGigabitEthernet)\S+)\s+.*?([+\-]?\d+(?:\.\d+)?)\s+([+\-]?\d+(?:\.\d+)?)\s*$',
                line.strip(),
            )
            if not m:
                continue
            port, tx, rx = m.group(1), m.group(2), m.group(3)
        else:
            port, tx, rx = m.group(1), m.group(2), m.group(3)
        key = _norm_port(port)
        rec = {'tx_dbm': float(tx), 'rx_dbm': float(rx), 'present': True}
        if rec['rx_dbm'] <= -30 or rec['tx_dbm'] <= -30:
            rec['alarm'] = True
        out[key] = rec
    return out


def parse_junos_optics(text: str) -> Dict[str, Dict[str, Any]]:
    """Parse `show interfaces diagnostics optics`."""
    out: Dict[str, Dict[str, Any]] = {}
    current = ''
    if _cli_unsupported(text):
        return out
    for line in (text or '').splitlines():
        im = re.search(r'(?:Physical interface|Interface)\s*:\s*(\S+)', line, re.I)
        if im:
            current = _norm_port(im.group(1))
            out.setdefault(current, {'present': True})
            continue
        if not current:
            continue
        rx = re.search(r'receiver power.*?([+\-]?\d+(?:\.\d+)?)\s*dBm', line, re.I)
        tx = re.search(r'(?:output|transmit) power.*?([+\-]?\d+(?:\.\d+)?)\s*dBm', line, re.I)
        if rx:
            out[current]['rx_dbm'] = float(rx.group(1))
        if tx:
            out[current]['tx_dbm'] = float(tx.group(1))
        if 'laser rx power low alarm' in line.lower() or 'laser tx power low alarm' in line.lower():
            if 'off' not in line.lower():
                out[current]['alarm'] = True
    return {k: v for k, v in out.items() if 'rx_dbm' in v or 'tx_dbm' in v or v.get('alarm')}


def optics_alarm(rec: Dict[str, Any], rx_low: float = -16.0, tx_low: float = -10.0) -> bool:
    if rec.get('alarm'):
        return True
    if rec.get('present') is False:
        return True
    rx, tx = rec.get('rx_dbm'), rec.get('tx_dbm')
    if rx is not None and rx <= rx_low:
        return True
    if tx is not None and tx <= tx_low:
        return True
    return False


def collect_optics(
    dtype: str,
    send_fn: Callable,
) -> Dict[str, Dict[str, Any]]:
    """Run vendor optics CLI. collected ports keyed by normalized ifName."""
    dtype_l = (dtype or '').lower()

    def _run(cmd: str) -> str:
        try:
            try:
                return send_fn(cmd, 60)
            except TypeError:
                return send_fn(cmd)
        except Exception:
            return ''

    if 'juniper' in dtype_l:
        return parse_junos_optics(_run('show interfaces diagnostics optics'))
    if 'nxos' in dtype_l or 'nexus' in dtype_l:
        return parse_nxos_transceiver(_run('show interface transceiver details'))
    parsed = parse_ios_transceiver_table(_run('show interfaces transceiver'))
    if not parsed:
        parsed = parse_nxos_transceiver(_run('show interfaces transceiver details'))
    return parsed


def _optics_for_host(optics_by_host: Dict[str, Dict[str, Dict[str, Any]]], host: str) -> Dict[str, Dict[str, Any]]:
    if not optics_by_host:
        return {}
    if host in optics_by_host:
        return optics_by_host.get(host) or {}
    hl = (host or '').lower()
    for key, val in optics_by_host.items():
        if str(key).lower() == hl:
            return val or {}
    return {}


def _optics_for_port(port_map: Dict[str, Dict[str, Any]], port: str) -> Optional[Dict[str, Any]]:
    if not port_map or not port:
        return None
    if port in port_map:
        return port_map.get(port)
    pl = port.lower()
    for key, val in port_map.items():
        if str(key).lower() == pl or _norm_port(str(key)).lower() == pl:
            return val
    return None


def apply_optics_to_edges(
    edges: List[Dict[str, Any]],
    optics_by_host: Dict[str, Dict[str, Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Stamp DOM on edges when both or one end has optics. Not a cable cert."""
    for e in edges:
        if e.get('not_physical') or str(e.get('layer') or '').lower() in ('overlay', 'l3'):
            continue
        f_host, t_host = e.get('from') or '', e.get('to') or ''
        fp, tp = _norm_port(str(e.get('f_port') or '')), _norm_port(str(e.get('t_port') or ''))
        f_map = _optics_for_host(optics_by_host, f_host)
        t_map = _optics_for_host(optics_by_host, t_host)
        f_rec = _optics_for_port(f_map, fp)
        t_rec = _optics_for_port(t_map, tp)
        if not f_rec and not t_rec:
            e.setdefault('optics_collected', False)
            continue
        e['optics_collected'] = True
        e['optics'] = {'local': f_rec or {}, 'remote': t_rec or {}}
        issues = list(e.get('cable_issues') or [])
        witnesses = list(e.get('cable_witnesses') or [])
        if f_rec and optics_alarm(f_rec):
            issues.append('dom_alarm_local')
            witnesses.append(f"local Rx {f_rec.get('rx_dbm', '?')} dBm alarm/low")
        if t_rec and optics_alarm(t_rec):
            issues.append('dom_alarm_remote')
            witnesses.append(f"remote Rx {t_rec.get('rx_dbm', '?')} dBm alarm/low")
        if f_rec and t_rec and not optics_alarm(f_rec) and not optics_alarm(t_rec):
            witnesses.append('both-end DOM in range (snapshot)')
        e['cable_issues'] = issues
        e['cable_witnesses'] = witnesses
        e['cable_note'] = 'DOM/optics snapshot from CLI. Not a certified cable.'
    return edges
