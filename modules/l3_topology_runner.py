"""
modules/l3_topology_runner.py
-------------------------------
SSH-based L3 routing collection per device (Cisco IOS/XE/NX-OS, Juniper Junos).
Inspired by Netdisco routing inventory + Secure Cartography offline graph model.

collect_device_routing():
  - Connects to device, runs platform-appropriate routing commands
  - Parses with TextFSM → regex fallback
  - Normalizes + deduplicates routes
  - Collects VRF routes if VRFs are present
  - Returns structured result dict

AI_CONTEXT: SSH L3 collection per inventory device (IOS/XE/NX-OS/Junos).
AI_FLOW: collect_device_routing → collector/parser/normalizer → graph_builder → HTML
AI_DEPENDS_ON: modules.network_base.safe_connection, routing_analyzer.*
AI_IMPACTS: Swiss Tools L3 / flow maps
AI_MAP_NOTE: Output is routing adjacency, not L2 cables.
AI_CRAWL_NOTE: Separate from CDP/LLDP discovery. Partial device failures stay in bundle.
AI_OFFLINE_NOTE: Needs SSH unless tests mock safe_connection.
AI_BREADCRUMB: next — utils/l3_map_formatter.py, utils/l3_map_shell.py
AI_TODO_NEXT: EVPN/VXLAN overlay collectors are absent — keep Overlay layer empty.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from modules.network_base import safe_connection, resolve_hostname_from_connection
from modules.routing_analyzer.collector import RoutingCollector
from modules.routing_analyzer.parser import RoutingParser
from modules.routing_analyzer.normalizer import RoutingNormalizer
from modules.routing_analyzer.graph_builder import (
    L3TopologyGraphBuilder,
    SubnetAnalyzer,
    GatewayDetector,
)


# ---------------------------------------------------------------------------
# Platform resolution
# ---------------------------------------------------------------------------

def _resolve_platform(device_type: str) -> str:
    dt = (device_type or 'cisco_ios').lower()
    if 'junos' in dt or 'juniper' in dt:
        return 'juniper_junos'
    if 'nxos' in dt or 'nx-os' in dt or 'nexus' in dt:
        return 'cisco_nxos'
    if 'xe' in dt:
        return 'cisco_xe'
    return 'cisco_ios'


def _device_conn_dict(dev: Dict[str, Any]) -> Dict[str, Any]:
    """Build the device dict expected by safe_connection / connect_permissive."""
    host = dev.get('host') or dev.get('ip') or '?'
    device = {
        'host': host,
        'device_type': dev.get('device_type') or 'cisco_ios',
        'port': dev.get('port') or 22,
    }
    if dev.get('group'):
        device['group'] = dev['group']
    return device


def _extract_network_meta(
    routes: List[Dict[str, Any]],
    mgmt_ip: str,
    ssh_port: int,
    platform: str,
) -> Dict[str, Any]:
    """Derive operator-facing network metadata from normalized routes."""
    interfaces: Dict[str, str] = {}
    connected_subnets: List[str] = []
    local_ips: List[str] = []
    default_gw: Optional[str] = None
    routing_protocols: set = set()
    vrf_names: set = set()
    route_count_by_proto: Dict[str, int] = {}

    for route in routes:
        dest = route.get('destination') or ''
        proto = route.get('protocol') or ''
        nhop = route.get('next_hop') or ''
        iface = (route.get('interface') or '').strip()
        vrf = route.get('vrf') or 'default'

        # Track protocols
        if proto:
            routing_protocols.add(proto)
            route_count_by_proto[proto] = route_count_by_proto.get(proto, 0) + 1

        # Track VRFs
        if vrf and vrf != 'default':
            vrf_names.add(vrf)

        if dest in ('0.0.0.0/0', '::/0') and nhop:
            default_gw = nhop
        elif proto in ('Connected', 'Local'):
            if iface and iface not in interfaces:
                interfaces[iface] = dest
            if dest and dest not in connected_subnets:
                connected_subnets.append(dest)
            if proto == 'Local' and dest.endswith('/32'):
                ip = dest.split('/')[0]
                if ip not in local_ips:
                    local_ips.append(ip)

    return {
        'management_ip': mgmt_ip,
        'ssh_port': ssh_port,
        'platform': platform,
        'default_gateway': default_gw,
        'interfaces': interfaces,
        'local_ips': local_ips[:20],
        'connected_subnets': connected_subnets[:30],
        'routing_protocols': sorted(list(routing_protocols)),
        'vrf_names': sorted(list(vrf_names)),
        'route_count_by_protocol': route_count_by_proto,
    }


# ---------------------------------------------------------------------------
# Per-device routing collection
# ---------------------------------------------------------------------------

def collect_device_routing(
    dev: Dict[str, Any],
    user: str,
    pwd: str,
    enb_pwd: str,
    log: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """
    Collect and parse routing table for one inventory device.

    Parameters
    ----------
    dev      : inventory device dict  {host, device_type, port, ...}
    user     : SSH username
    pwd      : SSH password
    enb_pwd  : enable / secret password
    log      : optional callable for console output

    Returns
    -------
    {
      host, device_type, platform, status,
      device_id, true_host,
      routes_raw_count, routes_normalized,
      errors, protocols,
      vrf_routes_by_vrf,   # {vrf_name: [normalized_routes]}
    }
    """
    host = dev.get('host') or dev.get('ip') or '?'
    dtype = dev.get('device_type') or 'cisco_ios'
    platform = _resolve_platform(dtype)
    port = dev.get('port') or 22
    device = _device_conn_dict(dev)

    result: Dict[str, Any] = {
        'host': host,
        'device_type': dtype,
        'platform': platform,
        'management_ip': host,
        'ssh_port': port,
        'status': 'error',
        'device_id': host,
        'true_host': host,
        'routes_raw_count': 0,
        'routes_normalized': [],
        'errors': [],
        'protocols': [],
        'vrf_routes_by_vrf': {},
        'network_meta': {},
    }

    parser = RoutingParser()
    normalizer = RoutingNormalizer()
    collector = RoutingCollector(platform)

    try:
        with safe_connection(device, user, pwd, enb_pwd, log_func=log, fallback_credentials=device.get('fallback_credentials')) as conn:
            # Resolve actual hostname from prompt
            true_host = resolve_hostname_from_connection(conn, host, dtype, log_func=log)
            result['true_host'] = true_host
            result['device_id'] = true_host

            # Log connection state for debugging
            if log:
                log(f"[L3] {host}: Connection established, enable mode: {conn.check_enable_mode() if hasattr(conn, 'check_enable_mode') else 'N/A'}")

            # Collect all routing data
            collected = collector.collect_routing_table(conn, log_func=log)
            result['errors'].extend(collected.get('errors') or [])
            
            # Log collection results for debugging
            if log:
                log(f"[L3] {host}: Collected routing tables: {list(collected.get('routing_tables', {}).keys())}")
                log(f"[L3] {host}: Routing table count: {len(collected.get('routing_tables', {}))}")
                for cmd, out in collected.get('routing_tables', {}).items():
                    log(f"[L3] {host}: {cmd} output length: {len(out) if out else 0}")
                    # Log full output for ALL outputs for debugging
                    if out:
                        log(f"[L3] {host}: {cmd} FULL OUTPUT:\n{out}")
                    else:
                        log(f"[L3] {host}: {cmd} OUTPUT IS EMPTY OR NONE")

            # --- Parse default VRF routes ---
            parsed_all: List[Dict[str, Any]] = []
            for cmd, output in (collected.get('routing_tables') or {}).items():
                _parse_and_extend(parser, normalizer, parsed_all, platform, cmd, output,
                                  true_host, 'default', result['errors'], log)
            for cmd, output in (collected.get('routing_v6') or {}).items():
                _parse_and_extend(parser, normalizer, parsed_all, platform, cmd, output,
                                  true_host, 'default', result['errors'], log)

            result['routes_raw_count'] = len(parsed_all)
            
            if log:
                log(f"[L3] {host}: Parsed {len(parsed_all)} routes from output")

            # --- Parse MAC address table if available ---
            mac_entries = []
            for cmd, output in (collected.get('mac_table') or {}).items():
                try:
                    parsed_mac = parser.parse_mac_address_table(platform, cmd, output)
                    mac_entries.extend(parsed_mac)
                except Exception as exc:
                    msg = f"{true_host}: MAC table parse failed for '{cmd}': {exc}"
                    result['errors'].append(msg)
                    if log:
                        log(f"[L3] {msg}")
            result['mac_address_table'] = mac_entries

            # --- Parse per-VRF routes ---
            vrf_routes_by_vrf: Dict[str, List[Dict[str, Any]]] = {}
            for vrf, vrf_cmds in (collected.get('vrf_routes') or {}).items():
                vrf_parsed: List[Dict[str, Any]] = []
                for cmd, output in vrf_cmds.items():
                    _parse_and_extend(parser, normalizer, vrf_parsed, platform, cmd, output,
                                      true_host, vrf, result['errors'], log)
                if vrf_parsed:
                    vrf_routes_by_vrf[vrf] = vrf_parsed
                    parsed_all.extend(vrf_parsed)
            result['vrf_routes_by_vrf'] = vrf_routes_by_vrf

            # Final normalization (dedup already handled inside _parse_and_extend)
            result['routes_normalized'] = parsed_all
            result['protocols'] = sorted({r.get('protocol', '') for r in parsed_all if r.get('protocol')})
            result['network_meta'] = _extract_network_meta(
                parsed_all, host, port, platform,
            )
            result['management_ip'] = host
            result['ssh_port'] = port

            if parsed_all:
                result['status'] = 'success'
            elif not result['errors']:
                result['status'] = 'success'  # Connected but no routes (rare)
            else:
                result['status'] = 'partial'

    except Exception as exc:
        result['errors'].append(str(exc))
        if log:
            log(f"[L3] {host}: collection failed — {exc}")

    return result


def _parse_and_extend(
    parser: RoutingParser,
    normalizer: RoutingNormalizer,
    out: List[Dict[str, Any]],
    platform: str,
    cmd: str,
    output: str,
    device_id: str,
    vrf: str,
    errors: List[str],
    log: Optional[Callable],
) -> None:
    """Parse one command output and append normalized routes to `out`."""
    if not output or not str(output).strip():
        if log:
            log(f"[L3-PARSE] {device_id}: {cmd} output is empty, skipping")
        return
    
    if log:
        log(f"[L3-PARSE] {device_id}: Starting parse for {cmd}, output length: {len(output)}")
    
    try:
        parsed = parser.parse_routing_output(platform, cmd, output)
        if log:
            log(f"[L3-PARSE] {device_id}: TextFSM parser returned {len(parsed) if parsed else 0} routes")
        
        if not parsed:
            parsed = parser.parse_routing_output_regex(platform, output)
            if log:
                log(f"[L3-PARSE] {device_id}: Regex parser returned {len(parsed) if parsed else 0} routes")
        
        if log:
            log(f"[L3-PARSE] {device_id}: Total parsed routes before normalization: {len(parsed) if parsed else 0}")
        
        normalized = normalizer.normalize_routing_table(parsed, device_id, vrf)
        if log:
            log(f"[L3-PARSE] {device_id}: Normalized to {len(normalized)} routes")
        
        out.extend(normalized)
    except Exception as exc:
        msg = f"{device_id}: parse failed for '{cmd}': {exc}"
        errors.append(msg)
        if log:
            log(f"[L3-PARSE] ERROR: {msg}")


# ---------------------------------------------------------------------------
# Topology bundle builders
# ---------------------------------------------------------------------------

def _vendor_label(platform: str) -> str:
    p = (platform or '').lower()
    if 'junos' in p or 'juniper' in p:
        return 'Juniper'
    if 'nxos' in p or 'nexus' in p:
        return 'NX-OS'
    if 'xe' in p:
        return 'IOS-XE'
    return 'IOS'


def _enrich_topology_nodes(
    nodes: List[Dict[str, Any]],
    devices_meta: Dict[str, Any],
) -> None:
    """Patch vis.js device nodes with management IP, SSH port, and vendor context."""
    for node in nodes:
        if node.get('group') != 'device':
            continue
        nid = node.get('id') or ''
        meta = devices_meta.get(nid) or {}
        mgmt = meta.get('management_ip') or nid
        port = meta.get('ssh_port') or 22
        platform = meta.get('platform') or ''
        vendor = _vendor_label(platform)
        default_gw = meta.get('default_gateway')
        local_ips = meta.get('local_ips') or []
        label_lines = [nid]
        if mgmt and mgmt != nid:
            label_lines.append(mgmt)
        if port and port != 22:
            label_lines.append(f":{port}")
        node['label'] = '\n'.join(label_lines)
        title_parts = [
            f"<b>{nid}</b>",
            f"Vendor: {vendor}",
            f"Platform: {platform or 'unknown'}",
            f"Mgmt IP: {mgmt}",
            f"SSH port: {port}",
            f"Routes: {meta.get('route_count', 0)}",
        ]
        if default_gw:
            title_parts.append(f"Default GW: {default_gw}")
        if local_ips:
            title_parts.append(f"Local IPs: {', '.join(local_ips[:5])}")
        protos = ', '.join(meta.get('protocols') or [])
        if protos:
            title_parts.append(f"Protocols: {protos}")
        node['title'] = '<br>'.join(title_parts)
        node['vendor'] = vendor


def build_l3_topology_bundle(
    device_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Merge per-device routing into L3 topology analysis bundle."""
    all_routes: List[Dict[str, Any]] = []
    devices_meta: Dict[str, Any] = {}
    failed_hosts: List[str] = []

    for res in device_results:
        host = res.get('true_host') or res.get('host') or '?'
        routes = res.get('routes_normalized') or []

        if res.get('status') not in ('success', 'partial') and not routes:
            failed_hosts.append(host)
            continue

        if res.get('status') != 'success' and not routes:
            failed_hosts.append(host)
            continue

        all_routes.extend(routes)
        net_meta = res.get('network_meta') or {}
        devices_meta[host] = {
            'route_count': len(routes),
            'protocols':   res.get('protocols') or [],
            'platform':    res.get('platform') or '',
            'errors':      res.get('errors') or [],
            'vrf_count':   len(res.get('vrf_routes_by_vrf') or {}),
            'management_ip': res.get('management_ip') or res.get('host') or host,
            'ssh_port':      res.get('ssh_port') or 22,
            'default_gateway': net_meta.get('default_gateway'),
            'interfaces':    net_meta.get('interfaces') or {},
            'local_ips':     net_meta.get('local_ips') or [],
            'connected_subnets': net_meta.get('connected_subnets') or [],
            'routing_protocols': net_meta.get('routing_protocols') or [],
            'vrf_names': net_meta.get('vrf_names') or [],
            'route_count_by_protocol': net_meta.get('route_count_by_protocol') or {},
        }

    graph_builder = L3TopologyGraphBuilder()
    subnet_analyzer = SubnetAnalyzer()
    gateway_detector = GatewayDetector()

    topology = graph_builder.build_topology(all_routes)
    nodes = list(topology.get('nodes') or [])
    edges = list(topology.get('edges') or [])
    analysis = dict(topology.get('analysis') or {})

    # SSH-reachable devices with zero usable routes still belong on the map
    # (empty black canvas with 0/0/0/0 was operator-hostile and hid reachability).
    if not nodes and devices_meta:
        for host, meta in devices_meta.items():
            nodes.append({
                'id': host,
                'label': host,
                'group': 'device',
                'title': (
                    f"<b>{host}</b><br>SSH OK · 0 usable routes parsed<br>"
                    f"Platform: {meta.get('platform') or 'unknown'}<br>"
                    "Not a blank failure — routing table empty or unparsed."
                ),
            })
        analysis['empty_routes_but_devices_reachable'] = True
        analysis['total_devices'] = len(nodes)

    _enrich_topology_nodes(nodes, devices_meta)
    subnet_analysis = subnet_analyzer.analyze_subnets(all_routes)
    gateway_analysis = gateway_detector.detect_gateways(all_routes)

    return {
        'generated_at':    datetime.now(timezone.utc).isoformat(),
        'topology': {
            'nodes':    nodes,
            'edges':    edges,
            'analysis': analysis,
        },
        'subnet_analysis':  subnet_analysis,
        'gateway_analysis': gateway_analysis,
        'devices':          devices_meta,
        'all_routes':       all_routes,
        'failed_hosts':     failed_hosts,
        'route_count':      len(all_routes),
        'observation': (
            'no_routes_parsed'
            if not all_routes and devices_meta
            else ('routes_present' if all_routes else 'no_devices')
        ),
    }


def build_flow_topology_bundle(l3_bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Build gateway-centric flow map from L3 routing bundle (Netdisco-style)."""
    gateway_analysis = l3_bundle.get('gateway_analysis') or {}
    subnet_analysis  = l3_bundle.get('subnet_analysis') or {}
    devices          = l3_bundle.get('devices') or {}

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    node_ids: set = set()

    def _add_node(nid: str, label: str, group: str, title: str = ''):
        if nid in node_ids:
            return
        node_ids.add(nid)
        nodes.append({'id': nid, 'label': label, 'group': group, 'title': title or label})

    for device_id, info in devices.items():
        protos = ', '.join(info.get('protocols') or [])
        rc = info.get('route_count', 0)
        _add_node(
            device_id, device_id, 'device',
            f"<b>{device_id}</b><br>{info.get('platform', 'device')}"
            f"<br>{rc} routes<br>{protos}",
        )

    for gw, info in gateway_analysis.items():
        is_default = info.get('is_default_gateway')
        group = 'default_gateway' if is_default else 'gateway'
        label = f"{gw}\n{'default-gw' if is_default else 'gw'}"
        _add_node(
            gw, label, group,
            f"<b>Gateway {gw}</b>"
            f"<br>Subnets: {info.get('subnet_count', 0)}"
            f"{'<br><span style=color:#ef4444>Default Route</span>' if is_default else ''}",
        )
        for dev in info.get('routing_devices') or []:
            if dev in node_ids:
                protos = ','.join(info.get('protocols') or [])
                edges.append({
                    'from': dev, 'to': gw,
                    'label': protos[:12] or 'via',
                    'arrows': 'to',
                })

    for subnet, info in subnet_analysis.items():
        if info.get('is_multicast'):
            continue
        if info.get('prefix_len', 0) == 32:
            continue  # skip host routes from flow map
        _add_node(
            subnet, subnet, 'subnet',
            f"<b>Subnet {subnet}</b><br>"
            f"Devices: {info.get('route_count', 0)}<br>"
            f"GWs: {', '.join((info.get('gateway_ips') or [])[:3])}",
        )
        for gw in info.get('gateway_ips') or []:
            if gw in node_ids:
                edges.append({'from': gw, 'to': subnet, 'label': 'serves', 'arrows': 'to'})

    return {
        'generated_at':  l3_bundle.get('generated_at'),
        'nodes':         nodes,
        'edges':         edges,
        'gateway_count': len(gateway_analysis),
        'subnet_count':  len(subnet_analysis),
        'device_count':  len(devices),
        'devices':       devices,
        'gateway_analysis': gateway_analysis,
        'subnet_analysis':  subnet_analysis,
        'all_routes':    l3_bundle.get('all_routes') or [],
        'failed_hosts':  l3_bundle.get('failed_hosts') or [],
        'route_count':   l3_bundle.get('route_count', 0),
    }


# ---------------------------------------------------------------------------
# Diagnostics writer
# ---------------------------------------------------------------------------

def write_l3_diagnostics(run_dir: str, bundle: Dict[str, Any], map_kind: str = 'l3') -> None:
    """Write JSON diagnostics alongside the HTML map."""
    os.makedirs(run_dir, exist_ok=True)

    # Manifest
    manifest = {
        '_meta': {
            'map_kind':   map_kind,
            'generated_at': bundle.get('generated_at'),
            'node_count': len(
                (bundle.get('topology') or {}).get('nodes') or bundle.get('nodes') or []
            ),
            'edge_count': len(
                (bundle.get('topology') or {}).get('edges') or bundle.get('edges') or []
            ),
            'route_count':  bundle.get('route_count', 0),
            'failed_hosts': bundle.get('failed_hosts') or [],
            'device_count': len(bundle.get('devices') or {}),
        }
    }
    manifest_path = os.path.join(run_dir, 'l3_topology_manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    # Full normalized routes
    routes_path = os.path.join(run_dir, 'l3_routes_normalized.json')
    all_routes = bundle.get('all_routes') or []
    with open(routes_path, 'w', encoding='utf-8') as f:
        json.dump(all_routes, f, indent=2, default=str)

    # Gateway analysis
    gw_path = os.path.join(run_dir, 'l3_gateways.json')
    with open(gw_path, 'w', encoding='utf-8') as f:
        json.dump(bundle.get('gateway_analysis') or {}, f, indent=2, default=str)

    # Subnet analysis
    sn_path = os.path.join(run_dir, 'l3_subnets.json')
    with open(sn_path, 'w', encoding='utf-8') as f:
        json.dump(bundle.get('subnet_analysis') or {}, f, indent=2, default=str)
