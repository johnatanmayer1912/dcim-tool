# ============================================================================
# AI_NAVIGATION_BREADCRUMBS - modules/routing_analyzer/path_tracer.py
# ============================================================================
# PURPOSE:
#   End-to-End L3 Path Tracer and Hop-by-Hop Flow Simulation Engine.
#   Uses Longest Prefix Match (LPM) over multi-vendor routing tables (Cisco IOS/XE/NX-OS, Junos)
#   to trace the deterministic forwarding path between any Source IP and Destination IP.
#
# ARCHITECTURAL ROLE:
#   Simulates forwarding plane hop progression without needing live ICMP/traceroute packets.
#   Operates completely offline on normalized routing bundles collected via SSH.
#
# KEY FUNCTIONS:
#   - L3PathTracer.trace_path(source_ip, destination_ip, vrf): Main entry point
#   - _find_ingress_device(source_ip): Resolves initial ingress switch/router
#   - _longest_prefix_match(routes, dest_ip): Finds the most specific route
#   - _resolve_next_hop_device(next_hop_ip): Maps next-hop IP to target device
#
# CONNECTIONS:
#   - Called by: vlan_checker_web.py (POST /api/l3/trace-path)
#   - Consumes: modules/routing_analyzer/normalizer.py, modules/l3_topology_runner.py
#   - Visualized in: utils/l3_map_shell.py (interactive animated flow path)
#
# INVARIANTS:
#   - Zero Trust: No credentials or secrets accessed or exposed.
#   - Pure Deterministic Logic: Maximum 30 hops with loop/cycle detection.
# ============================================================================

from __future__ import annotations

import ipaddress
from typing import Any, Dict, List, Optional, Set, Tuple


class L3PathTracer:
    """Simulates hop-by-hop packet forwarding across multi-vendor routing tables.
    
    Uses Longest Prefix Match (LPM) to determine ingress, transit hops, and egress.
    """

    def __init__(
        self,
        all_routes: List[Dict[str, Any]],
        devices_meta: Dict[str, Any],
        subnet_analysis: Optional[Dict[str, Any]] = None,
        gateway_analysis: Optional[Dict[str, Any]] = None,
    ):
        self.all_routes = all_routes or []
        self.devices_meta = devices_meta or {}
        self.subnet_analysis = subnet_analysis or {}
        self.gateway_analysis = gateway_analysis or {}

        # Index routes by device
        self._routes_by_device: Dict[str, List[Dict[str, Any]]] = {}
        for r in self.all_routes:
            dev = r.get('device_id') or r.get('device') or r.get('host') or ''
            if dev:
                self._routes_by_device.setdefault(dev, []).append(r)

        # Index local interface IPs to devices: {ip_str: (device_id, iface_name)}
        self._ip_to_device: Dict[str, Tuple[str, str]] = {}
        self._build_ip_index()

    def _build_ip_index(self) -> None:
        """Map known interface/local IPs to their owning device."""
        for dev_id, meta in self.devices_meta.items():
            # Check local_ips
            for ip_str in meta.get('local_ips') or []:
                clean_ip = ip_str.split('/')[0].strip()
                if clean_ip:
                    self._ip_to_device[clean_ip] = (dev_id, 'local')
            # Check interfaces
            ifaces = meta.get('interfaces') or {}
            for if_name, if_data in ifaces.items():
                if isinstance(if_data, dict):
                    ip_val = if_data.get('ip') or if_data.get('ipv4')
                    if ip_val:
                        clean_ip = str(ip_val).split('/')[0].strip()
                        self._ip_to_device[clean_ip] = (dev_id, if_name)
                elif isinstance(if_data, str) and if_data:
                    clean_ip = if_data.split('/')[0].strip()
                    self._ip_to_device[clean_ip] = (dev_id, if_name)
            # Management IP
            mgmt_ip = meta.get('management_ip')
            if mgmt_ip:
                clean_ip = str(mgmt_ip).split('/')[0].strip()
                self._ip_to_device.setdefault(clean_ip, (dev_id, 'mgmt'))

    def _find_ingress_device(self, source_ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> Optional[Tuple[str, str, str]]:
        """Identify which device connects directly to source_ip.
        
        Returns: (device_id, interface_name, subnet_str) or None
        """
        # Exact match on local IP
        str_ip = str(source_ip)
        if str_ip in self._ip_to_device:
            dev_id, iface = self._ip_to_device[str_ip]
            return dev_id, iface, f"{str_ip}/32"

        # Check connected routes across all devices (longest prefix match)
        best_dev: Optional[str] = None
        best_iface: str = 'unknown'
        best_net: Optional[ipaddress.IPv4Network | ipaddress.IPv6Network] = None

        for dev_id, routes in self._routes_by_device.items():
            for r in routes:
                proto = str(r.get('protocol') or '').lower()
                if proto not in ('connected', 'local', 'direct'):
                    continue
                net_str = r.get('network') or r.get('prefix') or ''
                if not net_str or net_str == '0.0.0.0/0':
                    continue
                try:
                    net = ipaddress.ip_network(net_str, strict=False)
                    if source_ip in net:
                        if best_net is None or net.prefixlen > best_net.prefixlen:
                            best_net = net
                            best_dev = dev_id
                            best_iface = r.get('interface') or 'connected'
                except ValueError:
                    continue

        if best_dev and best_net:
            return best_dev, best_iface, str(best_net)

        # Fallback: check subnet_analysis
        for subnet_str, s_info in self.subnet_analysis.items():
            try:
                s_net = ipaddress.ip_network(subnet_str, strict=False)
                if source_ip in s_net:
                    devices = s_info.get('devices') or []
                    if devices:
                        return devices[0], 'subnet-gw', subnet_str
            except ValueError:
                continue

        # If still not found, check if any device is registered
        if self._routes_by_device:
            first_dev = next(iter(self._routes_by_device.keys()))
            return first_dev, 'default', '0.0.0.0/0'

        return None

    def _longest_prefix_match(
        self,
        device_id: str,
        dest_ip: ipaddress.IPv4Address | ipaddress.IPv6Address,
    ) -> Optional[Dict[str, Any]]:
        """Find the best matching route for dest_ip in device_id's routing table."""
        routes = self._routes_by_device.get(device_id) or []
        best_route: Optional[Dict[str, Any]] = None
        best_prefixlen = -1

        for r in routes:
            net_str = r.get('network') or r.get('prefix') or ''
            if not net_str:
                continue
            try:
                net = ipaddress.ip_network(net_str, strict=False)
                if dest_ip in net:
                    if net.prefixlen > best_prefixlen:
                        best_prefixlen = net.prefixlen
                        best_route = r
            except ValueError:
                continue

        return best_route

    def _resolve_next_hop_device(self, next_hop_ip: str) -> Optional[str]:
        """Find which device owns next_hop_ip or is in the same transit subnet."""
        clean_nh = next_hop_ip.strip()
        if clean_nh in self._ip_to_device:
            return self._ip_to_device[clean_nh][0]

        try:
            nh_obj = ipaddress.ip_address(clean_nh)
            for dev_id, meta in self.devices_meta.items():
                for sub_str in meta.get('connected_subnets') or []:
                    try:
                        sub_net = ipaddress.ip_network(sub_str, strict=False)
                        if nh_obj in sub_net and dev_id != clean_nh:
                            return dev_id
                    except ValueError:
                        continue
        except ValueError:
            pass

        return None

    def trace_path(
        self,
        source_ip_str: str,
        dest_ip_str: str,
        max_hops: int = 30,
    ) -> Dict[str, Any]:
        """Trace hop-by-hop forwarding from source_ip_str to dest_ip_str.
        
        Returns a dictionary with status, hops, path_nodes, path_edges, and summary.
        """
        src_clean = source_ip_str.strip()
        dst_clean = dest_ip_str.strip()

        try:
            src_ip = ipaddress.ip_address(src_clean)
            dst_ip = ipaddress.ip_address(dst_clean)
        except ValueError as err:
            return {
                'status': 'error',
                'error': f"Invalid IP address format: {err}",
                'source_ip': src_clean,
                'destination_ip': dst_clean,
                'hops': [],
                'path_nodes': [],
                'path_edges': [],
                'complete': False,
            }

        ingress = self._find_ingress_device(src_ip)
        if not ingress:
            return {
                'status': 'failed',
                'error': f"No ingress device found for Source IP {src_clean}",
                'source_ip': src_clean,
                'destination_ip': dst_clean,
                'hops': [],
                'path_nodes': [],
                'path_edges': [],
                'complete': False,
            }

        current_dev, ingress_iface, ingress_subnet = ingress
        hops: List[Dict[str, Any]] = []
        path_nodes: List[str] = [current_dev]
        path_edges: List[str] = []
        visited_devices: Set[str] = {current_dev}
        hop_num = 1
        complete = False
        termination_reason = 'unknown'

        # Record Ingress Hop
        hops.append({
            'hop': hop_num,
            'device': current_dev,
            'action': 'ingress',
            'ingress_interface': ingress_iface,
            'egress_interface': '',
            'matched_prefix': ingress_subnet,
            'protocol': 'Connected/Local',
            'next_hop': '',
            'description': f"Source {src_clean} enters network at {current_dev} via {ingress_iface} ({ingress_subnet})",
        })

        while hop_num < max_hops:
            best_route = self._longest_prefix_match(current_dev, dst_ip)
            if not best_route:
                # Check for default route
                best_route = self._longest_prefix_match(current_dev, ipaddress.ip_address('0.0.0.0'))
                if not best_route:
                    termination_reason = f"No route to destination {dst_clean} on device {current_dev} (packet dropped)"
                    break

            proto = str(best_route.get('protocol') or 'Static')
            prefix = best_route.get('network') or best_route.get('prefix') or '0.0.0.0/0'
            next_hop = best_route.get('next_hop') or best_route.get('nexthop') or ''
            egress_iface = best_route.get('interface') or best_route.get('egress_interface') or 'out'

            # If route is connected/local to destination
            if proto.lower() in ('connected', 'local', 'direct'):
                hop_num += 1
                hops.append({
                    'hop': hop_num,
                    'device': current_dev,
                    'action': 'delivered',
                    'ingress_interface': '',
                    'egress_interface': egress_iface,
                    'matched_prefix': prefix,
                    'protocol': proto,
                    'next_hop': str(dst_ip),
                    'description': f"Destination {dst_clean} directly connected on {current_dev} ({egress_iface} in {prefix})",
                })
                complete = True
                termination_reason = f"Delivered to destination {dst_clean} on {current_dev}"
                break

            # Forward to next hop
            if not next_hop:
                termination_reason = f"Route {prefix} on {current_dev} has no next-hop IP (unreachable)"
                break

            next_dev = self._resolve_next_hop_device(next_hop)
            if not next_dev or next_dev == current_dev:
                # Try finding any device with this next-hop IP or gateway
                gw_info = self.gateway_analysis.get(next_hop)
                if gw_info and gw_info.get('routing_devices'):
                    candidates = [d for d in gw_info['routing_devices'] if d != current_dev]
                    if candidates:
                        next_dev = candidates[0]

            if not next_dev or next_dev == current_dev:
                hop_num += 1
                hops.append({
                    'hop': hop_num,
                    'device': current_dev,
                    'action': 'forward_external',
                    'ingress_interface': '',
                    'egress_interface': egress_iface,
                    'matched_prefix': prefix,
                    'protocol': proto,
                    'next_hop': next_hop,
                    'description': f"Forwarded out {current_dev} ({egress_iface}) to external gateway {next_hop}",
                })
                complete = True
                termination_reason = f"Routed towards external gateway {next_hop}"
                break

            # Loop detection
            if next_dev in visited_devices:
                hop_num += 1
                hops.append({
                    'hop': hop_num,
                    'device': current_dev,
                    'action': 'loop_detected',
                    'ingress_interface': '',
                    'egress_interface': egress_iface,
                    'matched_prefix': prefix,
                    'protocol': proto,
                    'next_hop': next_hop,
                    'description': f"Routing loop detected: {current_dev} -> {next_dev} (already visited)",
                })
                termination_reason = f"Routing loop detected at {current_dev} -> {next_dev}"
                break

            # Record forward hop
            hop_num += 1
            hops.append({
                'hop': hop_num,
                'device': current_dev,
                'action': 'forward',
                'ingress_interface': '',
                'egress_interface': egress_iface,
                'matched_prefix': prefix,
                'protocol': proto,
                'next_hop': next_hop,
                'target_device': next_dev,
                'description': f"Forward via {proto} ({prefix}) -> Next hop {next_hop} on {next_dev}",
            })

            path_nodes.append(next_dev)
            path_edges.append(f"{current_dev}->{next_dev}")
            visited_devices.add(next_dev)
            current_dev = next_dev

        if hop_num >= max_hops and not complete:
            termination_reason = f"Exceeded maximum hop count ({max_hops})"

        return {
            'status': 'success' if complete else ('loop_detected' if 'loop' in termination_reason.lower() else 'partial'),
            'complete': complete,
            'source_ip': src_clean,
            'destination_ip': dst_clean,
            'ingress_device': path_nodes[0] if path_nodes else None,
            'egress_device': path_nodes[-1] if path_nodes else None,
            'hop_count': len(hops),
            'hops': hops,
            'path_nodes': path_nodes,
            'path_edges': path_edges,
            'termination_reason': termination_reason,
            'summary': termination_reason,
        }
