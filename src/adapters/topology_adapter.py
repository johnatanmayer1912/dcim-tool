"""
Topology Adapter

Orchestrates network topology discovery and visualization.

v7.0.0 - Enterprise Architecture Refactor
Split from adapters.py for maintainability.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
import json

from src.network.topology.mapper import TopologyMapper
from src.network.topology.cdp_parser import CdpParser
from src.network.topology.lldp_parser import LldpParser
from src.network.topology.vpc_detector import VpcDetector
from src.network.topology.mac_correlator import MacCorrelator
from src.reporting.formatters.topology_report import TopologyReportFormatter
from src.network.base import safe_node_name


class TopologyAdapter:
    """
    Adapter for network topology operations.
    
    Responsibilities:
    - CDP/LLDP discovery across devices
    - Topology graph construction
    - vPC detection
    - MAC address correlation
    - HTML visualization generation
    """
    
    def __init__(self):
        self.mapper = TopologyMapper()
        self.cdp_parser = CdpParser()
        self.lldp_parser = LldpParser()
        self.vpc_detector = VpcDetector()
        self.mac_correlator = MacCorrelator()
        self.formatter = TopologyReportFormatter()
    
    def discover_topology(
        self,
        devices: List[Dict[str, Any]],
        username: str,
        password: str,
        enable_password: str = "",
        map_mode: str = 'all',
        log_func: Optional[callable] = None
    ) -> Tuple[List[Dict], str]:
        """
        Discover network topology from multiple devices.
        
        Args:
            devices: List of device dictionaries
            username: SSH username
            password: SSH password
            enable_password: Enable password
            map_mode: 'all' or 'vpc'
            log_func: Logging function
            
        Returns:
            Tuple of (results, html_file_path)
        """
        if log_func is None:
            log_func = print
        
        log_func(f"\n--- Topology Mapper Generating {map_mode.upper()} Physics Graph... ---")
        
        # Device limit to prevent browser crash
        if len(devices) > 150:
            log_func(f"\n[WARNING] Topology mapper limited to 150 devices")
            devices = devices[:150]
        
        edges = []
        uniq_nodes: Set[str] = set()
        node_metadata = {}
        results = []
        vpc_info_all = {}
        peer_info_registry = {}
        
        # Phase 1: Collect data from all devices
        for dev in devices:
            host = dev.get('host', 'unknown')
            log_func(f"Gathering topology for {host}...")
            
            res = self.mapper.run(
                device=dev,
                user=username,
                pwd=password,
                enb_pwd=enable_password,
                log_func=log_func
            )
            results.append(res)
            
            if res.get('status') == 'success':
                true_host = res['data'].get('true_host', host)
                uniq_nodes.add(true_host)
                node_metadata[true_host] = {
                    "interfaces": res['data'].get('int_meta', {}),
                    "bundles": res['data'].get('bundles', {}),
                    "vpcs": res['data'].get('vpcs', []),
                    "vpc_details": res['data'].get('vpc_details', {}),
                    "interface_macs": res['data'].get('interface_macs', {})
                }
                
                # Collect vPC info
                if res['data'].get('vpc_details'):
                    vpc_info_all[true_host] = res['data']['vpc_details']
                
                # Collect peer info from enriched edges
                for e in res['data'].get('edges', []):
                    peer_name = safe_node_name(e.get('to', ''))
                    if peer_name and any([
                        e.get('peer_platform'),
                        e.get('peer_version'),
                        e.get('peer_mgmt_ip')
                    ]):
                        existing = peer_info_registry.get(peer_name, {})
                        peer_info_registry[peer_name] = {
                            "platform": e.get('peer_platform') or existing.get('platform', ''),
                            "version": e.get('peer_version') or existing.get('version', ''),
                            "mgmt_ip": e.get('peer_mgmt_ip') or existing.get('mgmt_ip', ''),
                            "caps": e.get('peer_caps') or existing.get('caps', ''),
                        }
                
                edges.extend(res['data'].get('edges', []))
                log_func(f"  [SUCCESS] Topology data extracted for {true_host}")
            else:
                log_func(f"  [ERROR] {host}: {res.get('error', 'Unknown error')}")
        
        # Summary banner
        success_count = sum(1 for r in results if r.get('status') == 'success')
        failure_count = len(results) - success_count
        
        if failure_count > 0:
            log_func(f"\n{'='*60}")
            log_func(f"⚠️  TOPOLOGY PARTIAL: {success_count} succeeded, {failure_count} failed")
            log_func(f"{'='*60}")
            for r in results:
                if r.get('status') != 'success':
                    log_func(f"   ❌ {r.get('host', 'unknown')}: {r.get('error', 'Unknown error')}")
            log_func(f"{'='*60}\n")
        else:
            log_func(f"\n✅ Topology complete: All {success_count} devices successful\n")
        
        # Phase 2: Build unified graph
        final_edges = self._build_unified_graph(
            edges=edges,
            nodes=uniq_nodes,
            node_metadata=node_metadata,
            peer_info=peer_info_registry,
            vpc_info=vpc_info_all
        )
        
        # Phase 3: Generate HTML visualization
        html_file = self._generate_visualization(
            nodes=uniq_nodes,
            edges=final_edges,
            node_metadata=node_metadata,
            vpc_info=vpc_info_all,
            peer_info=peer_info_registry,
            map_mode=map_mode
        )
        
        log_func(f"--- Topology Graph Generated: {html_file} ---")
        return results, html_file
    
    def _build_unified_graph(
        self,
        edges: List[Dict],
        nodes: Set[str],
        node_metadata: Dict,
        peer_info: Dict,
        vpc_info: Dict
    ) -> List[Dict]:
        """Build unified topology graph with deduplication."""
        # Metadata-merging edge deduplication
        final_edges = []
        edge_registry = {}
        
        for e in edges:
            f_node = e.get('from', '')
            t_node = e.get('to', '')
            f_port = e.get('f_port', '')
            t_port = e.get('t_port', '')
            
            f_safe = safe_node_name(f_node)
            t_safe = safe_node_name(t_node)
            
            if not f_safe or not t_safe:
                continue
            
            # Create unique link key
            p1 = f"{f_safe}:{self._normalize_interface(f_port)}"
            p2 = f"{t_safe}:{self._normalize_interface(t_port)}"
            link_key = tuple(sorted([p1, p2]))
            
            # Merge metadata from duplicates
            if link_key in edge_registry:
                existing = edge_registry[link_key]
                existing['peer_platform'] = e.get('peer_platform') or existing.get('peer_platform', '')
                existing['peer_version'] = e.get('peer_version') or existing.get('peer_version', '')
                existing['peer_mgmt_ip'] = e.get('peer_mgmt_ip') or existing.get('peer_mgmt_ip', '')
                existing['peer_caps'] = e.get('peer_caps') or existing.get('peer_caps', '')
                continue
            
            # First occurrence
            edge_registry[link_key] = e.copy()
            final_edges.append(e)
        
        return final_edges
    
    def _generate_visualization(
        self,
        nodes: Set[str],
        edges: List[Dict],
        node_metadata: Dict,
        vpc_info: Dict,
        peer_info: Dict,
        map_mode: str
    ) -> str:
        """Generate HTML visualization."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_file = f"topology_map_{map_mode}_{timestamp}.html"
        
        # Use formatter to generate HTML
        self.formatter.generate(
            nodes=nodes,
            edges=edges,
            node_metadata=node_metadata,
            vpc_info=vpc_info,
            peer_info=peer_info,
            map_mode=map_mode,
            output_file=html_file
        )
        
        return html_file
    
    def _normalize_interface(self, interface_name: str) -> str:
        """Normalize interface name."""
        return (interface_name
                .replace("Ethernet", "Eth")
                .replace("GigabitEthernet", "Gi")
                .replace("FastEthernet", "Fa")
                .replace("TenGigabitEthernet", "Te")
                .replace("HundredGigE", "Hu")
                .replace("FortyGigabitEthernet", "Fo")
                .replace("Port-channel", "Po")
                .replace("port-channel", "Po")
                .strip())
