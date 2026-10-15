"""
STP Swiss Tools runner (v7.0.0) — aggregate STP scan across inventory for offline map/table.
"""
import re
from datetime import datetime

from modules.plugins.stp_topology_visualizer import run as stp_plugin_run

_STP_INTF_RE = re.compile(
    r'^(Eth|Gi|Te|Fa|Fo|Hu|Po|Vl|Ethernet|Gigabit|TenGig|FastEth|Vlan)',
    re.I,
)
_STP_BLOCKED_RE = re.compile(r'\b(blocking|blocked|blk)\b', re.I)
_STP_FORWARDING_RE = re.compile(r'\b(forwarding|fwd)\b', re.I)


def _parse_blocked_ports(blocked_text, hostname):
    """Parse blocked port CLI into link inventory rows. Forwarding ports are excluded."""
    rows = []
    if not blocked_text or not str(blocked_text).strip():
        return rows
    for line in str(blocked_text).splitlines():
        line = line.strip()
        if not line or line.startswith('-'):
            continue
        low = line.lower()
        parts = line.split()
        if not parts:
            continue
        if re.match(r'^VLAN\d+$', parts[0], re.I):
            continue
        if low.startswith(('flags', 'spanning tree', 'root id')):
            continue
        if 'none' in low and len(parts) <= 3:
            continue
        intf = parts[0]
        if intf.lower() in ('interface', 'port', 'vlan'):
            continue
        if not _STP_INTF_RE.match(intf):
            continue
        status_blob = ' '.join(parts[1:])
        is_blocked = bool(_STP_BLOCKED_RE.search(status_blob))
        is_fwd = bool(_STP_FORWARDING_RE.search(status_blob))
        if is_fwd and not is_blocked:
            continue
        if not is_blocked:
            continue
        rows.append({
            'from': hostname,
            'to': 'BLOCKED',
            'local_port': intf,
            'remote_port': '-',
            'protocol': 'STP',
            'link_type': 'stp-blocked',
            'edge_type': 'stp-derived',
            'confidence': 'High',
        })
    return rows


def run_demo_stp_scan(vlan_id=0):
    """Synthetic 3-switch STP lab for offline validation."""
    nodes = [
        {'id': 'STP-CORE-01', 'label': 'STP-CORE-01', 'ip': '10.0.0.1', 'is_root': True, 'platform': 'NX-OS'},
        {'id': 'STP-LEAF-02', 'label': 'STP-LEAF-02', 'ip': '10.0.0.2', 'is_root': False, 'platform': 'NX-OS'},
        {'id': 'STP-LEAF-03', 'label': 'STP-LEAF-03', 'ip': '10.0.0.3', 'is_root': False, 'platform': 'NX-OS'},
    ]
    link_rows = [
        {'from': 'STP-LEAF-02', 'to': 'BLOCKED', 'local_port': 'Eth1/2', 'remote_port': '-', 'protocol': 'STP', 'link_type': 'stp-blocked'},
    ]
    edges = [
        {'id': 1, 'from': 'STP-CORE-01', 'to': 'STP-LEAF-02', 'label': 'Po1', 'protocol': 'L2'},
        {'id': 2, 'from': 'STP-CORE-01', 'to': 'STP-LEAF-03', 'label': 'Po2', 'protocol': 'L2'},
        {'id': 3, 'from': 'STP-LEAF-02', 'to': 'BLOCKED', 'label': 'blocked', 'protocol': 'STP', 'dashes': True},
    ]
    return {
        'status': 'success',
        'nodes': nodes,
        'edges': edges,
        'link_rows': link_rows,
        'devices': nodes,
        'vlan_id': vlan_id,
        'demo': True,
    }


def run_stp_inventory_scan(devices, credentials, vlan_id=0, log_func=None, demo_mode=False):
    """Scan inventory devices; return nodes, edges, link_rows for topo_map_shell."""
    if demo_mode:
        return run_demo_stp_scan(vlan_id)

    nodes = []
    link_rows = []
    edge_id = 1
    errors = []

    for dev in devices:
        host = dev.get('host', 'unknown')
        try:
            res = stp_plugin_run(
                dev,
                credentials,
                {'vlan_id': int(vlan_id or 0)},
                {'timeout': 30},
                log_func,
            )
            if res.get('status') != 'success':
                errors.append({'host': host, 'error': res.get('error', 'failed')})
                continue
            data = res.get('data') or {}
            hn = data.get('true_host') or host
            nodes.append({
                'id': hn,
                'label': hn,
                'ip': host,
                'is_root': bool(data.get('is_root_any')),
                'platform': data.get('device_type', ''),
            })
            blocked = data.get('blocked_ports', '')
            link_rows.extend(_parse_blocked_ports(blocked, hn))
        except Exception as exc:
            errors.append({'host': host, 'error': str(exc)})

    edges = []
    eid = 1
    for row in link_rows:
        edges.append({
            'id': eid,
            'from': row['from'],
            'to': row['to'],
            'label': row['local_port'],
            'protocol': 'STP',
            'dashes': True,
        })
        eid += 1

    return {
        'status': 'success' if nodes else 'error',
        'nodes': nodes,
        'edges': edges,
        'link_rows': link_rows,
        'errors': errors,
        'vlan_id': vlan_id,
        'demo': False,
    }
