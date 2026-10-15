"""
modules/plugins/network_discovery.py
-----------------------------------
Network Discovery and Topology Mapping Plugin for Network Swiss Tool Pro v6.9.21.

This plugin implements dynamic network crawling starting from a seed device
by recursively fetching and parsing CDP/LLDP neighbors across multiple platforms.

=============================================================================
HARDCODED REQUIREMENTS - ALL PLUGINS MUST COMPLY
=============================================================================
1. VERSION REQUIREMENTS (MANDATORY):
   - Version: "1.0.0"
2. DOCUMENTATION REQUIREMENTS (MANDATORY):
   - Located in: docs/plugins/network_discovery/
3. CONTRACT COMPLIANCE:
   - Contains METADATA dict
   - Implements run() function
   - Implements validate_plugin() function
=============================================================================
"""

METADATA = {
    "plugin_id": "network_discovery",
    "display_name": "Network Discovery & Crawl",
    "version": "1.0.0",
    "author": "Network Swiss Tool",
    "category": "Discovery",
    "description": "Recursively crawl CDP/LLDP neighbors starting from a seed device to discover inventory and generate topology.",
    "min_platform_version": "6.9.21",
    
    "changelog": [
        {
            "version": "1.0.0",
            "date": "2026-05-26",
            "changes": "Initial release of recursive CDP/LLDP crawler with duplicate detection and dynamic Vis.js mapping.",
            "author": "Network Swiss Tool Team",
            "qa_status": "approved"
        }
    ],
    
    "documentation": {
        "readme": "docs/plugins/network_discovery/README.md",
        "release_notes": "docs/plugins/network_discovery/RELEASE_NOTES.md",
        "prompt": "docs/plugins/network_discovery/PROMPT.md",
        "changelog": "docs/plugins/network_discovery/CHANGELOG.md",
        "test_results": "docs/plugins/network_discovery/TEST_RESULTS.md",
        "compatibility": "docs/plugins/network_discovery/COMPATIBILITY.md",
        "versions_folder": "docs/plugins/network_discovery/versions/",
        "current_version_folder": "docs/plugins/network_discovery/versions/v1.0.0/"
    },
    
    "version_archive": {
        "v1.0.0": {
            "file": "docs/plugins/network_discovery/versions/v1.0.0/network_discovery_v1.0.0.py",
            "manifest": "docs/plugins/network_discovery/versions/v1.0.0/manifest.json",
            "date": "2026-05-26",
            "status": "current"
        }
    },
    
    "required_params": {
        "depth": {
            "type": "integer",
            "label": "Crawl Depth (1-3 hops)",
            "default": 2,
            "min": 1,
            "max": 3,
            "required": True,
            "description": "How many hops away from seed device to crawl."
        },
        "protocol": {
            "type": "dropdown",
            "label": "Discovery Protocol",
            "options": ["CDP", "LLDP", "Both"],
            "default": "Both",
            "required": True,
            "description": "Protocol used to fetch neighbor adjacencies."
        },
        "dry_run": {
            "type": "checkbox",
            "label": "Dry Run Mode (Seed Only)",
            "default": False,
            "description": "Scan seed device only without recursive hops."
        }
    },
    
    "supports_parallel": False,
    "supports_dry_run": True,
    "modifies_device": False,
    "requires_enable": True
}

from modules.network_base import safe_connection, build_json, safe_node_name
from utils.report_formatter import save_plugin_report, append_to_master_report
from datetime import datetime
import re
import os
import json
import socket

# BFS Discovery Crawler
def run(device, credentials, params, config, log_func):
    host = device.get('host', 'unknown')
    device_type = device.get('device_type', 'cisco_ios')
    
    depth = params.get('depth', 2)
    protocol = params.get('protocol', 'Both').upper()
    dry_run = params.get('dry_run', False)
    
    if log_func:
        log_func(f"[{host}] Starting recursive discovery. Depth={depth}, Protocol={protocol}, DryRun={dry_run}")
        
    # Queue for BFS: holds (ip, device_type, current_depth)
    queue = [(host, device_type, 0)]
    visited = set()
    discovered_nodes = {}
    discovered_edges = []
    
    # Store credentials for reuse across all hops
    username = credentials.get('username')
    password = credentials.get('password')
    secret = credentials.get('secret')
    
    # Seed details
    seed_node = {
        "id": host,
        "label": host,
        "ip": host,
        "platform": "unknown",
        "discovered_via": "Seed",
        "depth": 0,
        "is_scanned": False
    }
    discovered_nodes[host.lower()] = seed_node
    
    while queue:
        curr_ip, curr_dtype, curr_depth = queue.pop(0)
        
        # Guard: depth check
        if curr_depth > depth or (dry_run and curr_depth > 0):
            continue
            
        # Normalize visited IP/Host
        visited_key = curr_ip.lower()
        if visited_key in visited:
            continue
        visited.add(visited_key)
        
        if log_func:
            log_func(f"[{curr_ip}] Crawling node at hop {curr_depth}...")
            
        # Create temporary device dict
        curr_device = {
            "host": curr_ip,
            "device_type": curr_dtype,
            "port": 22
        }
        
        try:
            with safe_connection(curr_device, username, password, secret, log_func) as conn:
                # Find true hostname
                ver_output = conn.send_command("show version")
                hostname = safe_node_name(ver_output) or curr_ip
                hostname_lower = hostname.lower()
                
                # Update node registry with true hostname and scanned state
                node_data = discovered_nodes.get(visited_key) or discovered_nodes.get(hostname_lower) or {}
                node_data.update({
                    "id": hostname,
                    "label": hostname,
                    "ip": curr_ip,
                    "depth": curr_depth,
                    "is_scanned": True
                })
                
                # Extract platform/hardware details
                if 'juniper' in curr_dtype.lower():
                    chassis_out = conn.send_command("show chassis hardware")
                    m = re.search(r'chassis\s+(\S+)', chassis_out, re.I)
                    node_data["platform"] = m.group(1) if m else "Juniper"
                else:
                    m = re.search(r'Model\s+Number\s*:\s*(\S+)|Processor\s+board\s+ID\s+(\S+)', ver_output, re.I)
                    node_data["platform"] = (m.group(1) or m.group(2) or "Cisco Switch") if m else "Cisco"
                
                # Register under both IP and hostname to prevent duplicate crawling
                discovered_nodes[visited_key] = node_data
                discovered_nodes[hostname_lower] = node_data
                
                # ── CDP Discovery Adjacency ────────────────────────────────────
                neighbors = []
                if protocol in ["CDP", "BOTH"] and 'juniper' not in curr_dtype.lower():
                    if log_func:
                        log_func(f"[{hostname}] Fetching CDP neighbors detail...")
                    cdp_out = conn.send_command("show cdp neighbors detail")
                    neighbors.extend(_parse_cisco_cdp_detail(cdp_out, hostname, log_func))
                    
                # ── LLDP Discovery Adjacency ───────────────────────────────────
                if protocol in ["LLDP", "BOTH"]:
                    if log_func:
                        log_func(f"[{hostname}] Fetching LLDP neighbors detail...")
                    if 'juniper' in curr_dtype.lower():
                        lldp_out = conn.send_command("show lldp neighbors detail")
                        neighbors.extend(_parse_juniper_lldp_detail(lldp_out, hostname, log_func))
                    else:
                        lldp_out = conn.send_command("show lldp neighbors detail")
                        neighbors.extend(_parse_cisco_lldp_detail(lldp_out, hostname, log_func))
                
                # ── BFS Neighbor Crawl Enqueuing ──────────────────────────────
                for neigh in neighbors:
                    n_host = neigh["hostname"]
                    n_ip = neigh["ip"]
                    n_local_port = neigh["local_port"]
                    n_remote_port = neigh["remote_port"]
                    n_platform = neigh["platform"]
                    n_proto = neigh["protocol"]
                    
                    n_key = n_host.lower()
                    n_ip_key = n_ip.lower() if n_ip else ""
                    
                    # Deduplicate node registry
                    existing_node = discovered_nodes.get(n_key) or (discovered_nodes.get(n_ip_key) if n_ip_key else None)
                    if not existing_node:
                        # Register discovered neighbor
                        new_node = {
                            "id": n_host,
                            "label": n_host,
                            "ip": n_ip or "unknown",
                            "platform": n_platform,
                            "discovered_via": n_proto,
                            "depth": curr_depth + 1,
                            "is_scanned": False
                        }
                        discovered_nodes[n_key] = new_node
                        if n_ip_key:
                            discovered_nodes[n_ip_key] = new_node
                    else:
                        # Preserve existing scanning status
                        new_node = existing_node
                        
                    # Register discovered edge
                    edge_exists = False
                    for edge in discovered_edges:
                        if (edge["from"].lower() == hostname_lower and edge["to"].lower() == n_key) or \
                           (edge["from"].lower() == n_key and edge["to"].lower() == hostname_lower):
                            # Edge matches, prevent duplicates
                            edge_exists = True
                            break
                            
                    if not edge_exists:
                        discovered_edges.append({
                            "from": hostname,
                            "to": n_host,
                            "f_port": n_local_port,
                            "t_port": n_remote_port,
                            "label": f"{n_proto}\n{n_local_port} ↔ {n_remote_port}",
                            "type": "standard",
                            "protocol": n_proto
                        })
                        
                    # Queue next hop BFS crawl
                    if curr_depth + 1 < depth and n_ip and not dry_run:
                        if n_ip_key not in visited and n_key not in visited:
                            # Map platform key to Netmiko device type
                            n_dtype = "cisco_ios"
                            if "nexus" in n_platform.lower() or "n5k" in n_platform.lower() or "n7k" in n_platform.lower():
                                n_dtype = "cisco_nxos"
                            elif "juniper" in n_platform.lower() or "junos" in n_platform.lower():
                                n_dtype = "juniper_junos"
                                
                            queue.append((n_ip, n_dtype, curr_depth + 1))
                            
            if log_func:
                log_func(f"[{curr_ip}] Scan completed successfully.")
                
        except Exception as e:
            if log_func:
                log_func(f"[WARNING] Discovery failed on {curr_ip}: {e}")
            # Mark scanned as failed, but preserve discovered record
            node_key = curr_ip.lower()
            if node_key in discovered_nodes:
                discovered_nodes[node_key]["status"] = f"Failed: {str(e)[:40]}"
                
    # Normalize nodes registry (remove duplicate IP/hostname keys)
    final_nodes = []
    seen_ids = set()
    for node in discovered_nodes.values():
        nid = node["id"]
        if nid not in seen_ids:
            final_nodes.append(node)
            seen_ids.add(nid)
            
    if log_func:
        log_func(f"[Discovery] Crawl finished. Discovered {len(final_nodes)} nodes and {len(discovered_edges)} connections.")
        
    # Write discovered inventory JSON locally
    try:
        if getattr(sys, 'frozen', False):
            p_dir = os.path.dirname(sys.executable)
        else:
            p_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
        inv_path = os.path.join(p_dir, "discovered_inventory.json")
        with open(inv_path, "w", encoding="utf-8") as f:
            json.dump({
                "nodes": final_nodes,
                "edges": discovered_edges,
                "timestamp": datetime.now().isoformat(),
                "depth": depth,
                "protocol": protocol
            }, f, indent=2)
        if log_func:
            log_func(f"[Discovery] Discovered inventory saved to: {inv_path}")
    except Exception as je:
        if log_func:
            log_func(f"[WARNING] Could not save discovered inventory JSON: {je}")
            
    # Generate interactive Vis.js graph HTML
    html_file = ""
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        reports_dir = os.path.join(p_dir, "reports", "discovery")
        os.makedirs(reports_dir, exist_ok=True)
        html_file = os.path.join(reports_dir, f"discovery_map_{ts}.html")
        
        _generate_discovery_html(html_file, final_nodes, discovered_edges)
        if log_func:
            log_func(f"[SUCCESS] Discovered Topology Map generated: {html_file}")
    except Exception as he:
        if log_func:
            log_func(f"[WARNING] Could not generate Vis.js topology graph: {he}")
            
    # Save standard plugin report
    result_data = {
        "discovered_nodes": final_nodes,
        "discovered_edges": discovered_edges,
        "inventory_json_path": "discovered_inventory.json",
        "timestamp": datetime.now().isoformat(),
        "report_path": html_file
    }
    
    report_path = save_plugin_report(
        METADATA['plugin_id'], 
        host, 
        result_data, 
        lambda d, h: _format_discovery_report(d, h)
    )
    result_data["report_path"] = report_path
    
    # Save to master summary
    summary_text = f"Discovered {len(final_nodes)} devices & {len(discovered_edges)} links using {protocol} starting from seed {host}."
    append_to_master_report(METADATA['plugin_id'], host, "success", summary_text, report_path)
    
    return build_json(host, "success", result_data)

# ── Cisco CDP Parser ─────────────────────────────────────────────────────────
def _parse_cisco_cdp_detail(output, local_hostname, log_func):
    neighbors = []
    blocks = output.split("-------------------------")
    for block in blocks:
        if not block.strip() or "Device ID" not in block:
            continue
            
        try:
            # Device ID / Hostname
            m_id = re.search(r'Device ID\s*:\s*(\S+)', block, re.I)
            if not m_id:
                continue
            neigh_host = m_id.group(1).split('(')[0] # remove domains/FQDNS
            
            # Management IP Address
            m_ip = re.search(r'IP\s+address\s*:\s*(\S+)|IPv4\s+Address\s*:\s*(\S+)', block, re.I)
            neigh_ip = (m_ip.group(1) or m_ip.group(2)) if m_ip else None
            
            # Local & Remote Interface
            m_lint = re.search(r'Interface\s*:\s*(\S+)', block, re.I)
            m_rint = re.search(r'Port\s+ID\s*\(outgoing\s+port\)\s*:\s*(\S+)', block, re.I)
            local_port = m_lint.group(1) if m_lint else "unknown"
            remote_port = m_rint.group(1) if m_rint else "unknown"
            
            # Platform model
            m_plat = re.search(r'Platform\s*:\s*([^,\n]+)', block, re.I)
            platform = m_plat.group(1).strip() if m_plat else "Cisco"
            
            # Skip IP Phones/PCs (observability filter)
            if any(x in platform.lower() for x in ["ip phone", "ata", "desktop", "camera"]):
                continue
                
            neighbors.append({
                "hostname": neigh_host,
                "ip": neigh_ip,
                "local_port": local_port,
                "remote_port": remote_port,
                "platform": platform,
                "protocol": "CDP"
            })
        except Exception as e:
            if log_func:
                log_func(f"[Parser WARNING] Failed to parse CDP block: {e}")
                
    return neighbors

# ── Cisco LLDP Parser ────────────────────────────────────────────────────────
def _parse_cisco_lldp_detail(output, local_hostname, log_func):
    neighbors = []
    blocks = output.split("Chassis id")
    for block in blocks:
        if not block.strip() or "System Name" not in block:
            continue
            
        try:
            # System Name / Hostname
            m_host = re.search(r'System\s+Name\s*:\s*(\S+)', block, re.I)
            if not m_host:
                continue
            neigh_host = m_host.group(1).split('(')[0]
            
            # Management IP
            m_ip = re.search(r'Address\s*:\s*(\S+)', block, re.I)
            neigh_ip = m_ip.group(1) if m_ip else None
            
            # Ports
            m_lint = re.search(r'Local\s+Intf\s*:\s*(\S+)', block, re.I)
            m_rint = re.search(r'Port\s+id\s*:\s*(\S+)', block, re.I)
            local_port = m_lint.group(1) if m_lint else "unknown"
            remote_port = m_rint.group(1) if m_rint else "unknown"
            
            # Platform
            m_desc = re.search(r'System\s+Description\s*:\s*([^\n]+)', block, re.I)
            desc = m_desc.group(1).lower() if m_desc else ""
            if "nexus" in desc or "n5k" in desc or "n7k" in desc or "nx-os" in desc:
                platform = "Cisco Nexus"
            elif "juniper" in desc:
                platform = "Juniper"
            else:
                platform = "Cisco Switch"
                
            neighbors.append({
                "hostname": neigh_host,
                "ip": neigh_ip,
                "local_port": local_port,
                "remote_port": remote_port,
                "platform": platform,
                "protocol": "LLDP"
            })
        except Exception as e:
            if log_func:
                log_func(f"[Parser WARNING] Failed to parse LLDP block: {e}")
                
    return neighbors

# ── Juniper LLDP Parser ──────────────────────────────────────────────────────
def _parse_juniper_lldp_detail(output, local_hostname, log_func):
    neighbors = []
    blocks = output.split("Local Interface")
    for block in blocks:
        if not block.strip() or "System name" not in block:
            continue
            
        try:
            # System Name / Hostname
            m_host = re.search(r'System\s+name\s*:\s*(\S+)', block, re.I)
            if not m_host:
                continue
            neigh_host = m_host.group(1).split('(')[0]
            
            # Management IP
            m_ip = re.search(r'Management\s+address\s*:\s*(\S+)', block, re.I)
            neigh_ip = m_ip.group(1) if m_ip else None
            
            # Ports
            m_lint = re.search(r'^\s*(\S+)', block, re.M)
            m_rint = re.search(r'Port\s+ID\s*:\s*(\S+)', block, re.I)
            local_port = m_lint.group(1) if m_lint else "unknown"
            remote_port = m_rint.group(1) if m_rint else "unknown"
            
            neighbors.append({
                "hostname": neigh_host,
                "ip": neigh_ip,
                "local_port": local_port,
                "remote_port": remote_port,
                "platform": "Juniper",
                "protocol": "LLDP"
            })
        except Exception as e:
            if log_func:
                log_func(f"[Parser WARNING] Failed to parse Junos LLDP block: {e}")
                
    return neighbors

# ── Report Formatter ──────────────────────────────────────────────────────────
def _format_discovery_report(data, host):
    nodes = data.get('discovered_nodes', [])
    edges = data.get('discovered_edges', [])
    ts = data.get('timestamp', datetime.now().isoformat())
    
    lines = []
    lines.append("=" * 70)
    lines.append("NETWORK DISCOVERY & NEIGHBOR SCAN REPORT")
    lines.append("=" * 70)
    lines.append(f"Seed Host:        {host}")
    lines.append(f"Scan Finished:    {ts}")
    lines.append(f"Discovered Nodes: {len(nodes)}")
    lines.append(f"Discovered Links: {len(edges)}")
    lines.append("")
    
    lines.append("-" * 70)
    lines.append("DISCOVERED DEVICE CATALOG")
    lines.append("-" * 70)
    lines.append(f"{'Hostname':<22} | {'Management IP':<15} | {'Model/Platform':<15} | {'Hop':<4} | {'State':<10}")
    lines.append("-" * 70)
    for n in sorted(nodes, key=lambda x: x["depth"]):
        scanned = "Scanned" if n.get("is_scanned") else "Discovered"
        lines.append(f"{n['id']:<22} | {n['ip']:<15} | {n.get('platform','unknown'):<15} | {n['depth']:<4} | {scanned:<10}")
        
    lines.append("")
    lines.append("-" * 70)
    lines.append("DISCOVERED NEIGHBOR CONNECTIONS (PHYSICAL LINKS)")
    lines.append("-" * 70)
    for e in edges:
        lines.append(f"  [Link] {e['from']} [{e['f_port']}] ↔ {e['to']} [{e['t_port']}]  ({e['protocol']})")
        
    lines.append("=" * 70)
    return "\n".join(lines)

# ── Vis.js Discovery Map Template Generator ──────────────────────────────────
def _generate_discovery_html(filepath, nodes, edges):
    nodes_json = []
    for n in nodes:
        scanned = n.get("is_scanned", False)
        # Colors: scans = primary blue, discovered = secondary slate gray
        color = "#3b82f6" if scanned else "#94a3b8"
        nodes_json.append({
            "id": n["id"],
            "label": f"{n['id']}\n({n.get('platform','unknown')})",
            "ip": n.get("ip", ""),
            "platform": n.get("platform", ""),
            "discovered_via": n.get("discovered_via", ""),
            "depth": n.get("depth", 0),
            "color": {
                "background": color,
                "border": "#1e3a8a" if scanned else "#475569",
                "highlight": {
                    "background": "#60a5fa",
                    "border": "#2563eb"
                }
            },
            "font": {"color": "#ffffff"},
            "shape": "box",
            "borderWidth": 2,
            "shadow": True
        })
        
    edges_json = []
    for e in edges:
        edges_json.append({
            "from": e["from"],
            "to": e["to"],
            "label": f"{e['f_port']} ↔ {e['t_port']}",
            "title": f"Protocol: {e['protocol']}",
            "color": {"color": "#6366f1", "highlight": "#4f46e5"},
            "width": 2,
            "smooth": {"type": "continuous"}
        })
        
    # Read vis.js internal bundle path safely
    import sys
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        vis_js_path = os.path.join(sys._MEIPASS, "modules", "web", "vis-network.min.js")
    else:
        vis_js_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "vis-network.min.js")
        
    vis_js_content = ""
    if os.path.exists(vis_js_path):
        try:
            with open(vis_js_path, "r", encoding="utf-8") as f:
                vis_js_content = f.read()
        except:
            pass
            
    if not vis_js_content:
        # Fallback to CDN if bundle fails
        vis_script = '<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>'
    else:
        vis_script = f'<script type="text/javascript">{vis_js_content}</script>'
        
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Network Swiss Tool Pro — Discovered Topology</title>
    {vis_script}
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: #0f172a;
            color: #f1f5f9;
            font-family: 'Inter', sans-serif;
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        header {{
            background: #1e293b;
            padding: 15px 30px;
            border-bottom: 1px solid #334155;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        h1 {{
            margin: 0;
            font-size: 18px;
            font-weight: 700;
            color: #38bdf8;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        #container {{
            display: flex;
            flex: 1;
            overflow: hidden;
        }}
        #mynetwork {{
            flex: 1;
            height: 100%;
            background: #0b0f19;
        }}
        #sidebar {{
            width: 320px;
            background: #1e293b;
            border-left: 1px solid #334155;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            overflow-y: auto;
        }}
        .card {{
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 15px;
        }}
        .card-title {{
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #94a3b8;
            margin-bottom: 10px;
        }}
        .table-prop {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }}
        .table-prop td {{
            padding: 6px 0;
        }}
        .table-prop td:first-child {{
            font-weight: 500;
            color: #60a5fa;
            width: 40%;
        }}
        .badge {{
            background: #2563eb;
            color: #ffffff;
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <header>
        <h1>🔌 Network Swiss Tool Pro <span class="badge">v6.9.21</span></h1>
        <div style="font-size: 12px; color: #94a3b8;">Topology Discovered: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </header>
    <div id="container">
        <div id="mynetwork"></div>
        <div id="sidebar">
            <div class="card">
                <div class="card-title">🔍 Scan Inventory Overview</div>
                <table class="table-prop">
                    <tr>
                        <td>Total Devices:</td>
                        <td>{len(nodes)}</td>
                    </tr>
                    <tr>
                        <td>Total Links:</td>
                        <td>{len(edges)}</td>
                    </tr>
                </table>
            </div>
            
            <div class="card" id="detail-card" style="display:none;">
                <div class="card-title">🖥️ Selected Device Details</div>
                <table class="table-prop">
                    <tr>
                        <td>Hostname:</td>
                        <td id="node-name">-</td>
                    </tr>
                    <tr>
                        <td>Management IP:</td>
                        <td id="node-ip">-</td>
                    </tr>
                    <tr>
                        <td>Platform/Model:</td>
                        <td id="node-platform">-</td>
                    </tr>
                    <tr>
                        <td>Discovery Hop:</td>
                        <td id="node-depth">-</td>
                    </tr>
                    <tr>
                        <td>Discovery Via:</td>
                        <td id="node-via">-</td>
                    </tr>
                </table>
            </div>
        </div>
    </div>

    <script type="text/javascript">
        var nodes = new vis.DataSet({json.dumps(nodes_json)});
        var edges = new vis.DataSet({json.dumps(edges_json)});

        var container = document.getElementById('mynetwork');
        var data = {{
            nodes: nodes,
            edges: edges
        }};
        var options = {{
            nodes: {{
                font: {{
                    size: 13,
                    face: 'Inter'
                }}
            }},
            edges: {{
                font: {{
                    size: 10,
                    face: 'Inter',
                    align: 'middle'
                }}
            }},
            physics: {{
                barnesHut: {{
                    gravitationalConstant: -8000,
                    centralGravity: 0.3,
                    springLength: 120
                }}
            }}
        }};
        var network = new vis.Network(container, data, options);

        network.on("selectNode", function (params) {{
            var nodeId = params.nodes[0];
            var nodeData = nodes.get(nodeId);
            if (nodeData) {{
                document.getElementById('node-name').textContent = nodeData.id;
                document.getElementById('node-ip').textContent = nodeData.ip || 'N/A';
                document.getElementById('node-platform').textContent = nodeData.platform || 'N/A';
                document.getElementById('node-depth').textContent = nodeData.depth;
                document.getElementById('node-via').textContent = nodeData.discovered_via || 'Seed';
                document.getElementById('detail-card').style.display = 'block';
            }}
        }});

        network.on("deselectNode", function (params) {{
            document.getElementById('detail-card').style.display = 'none';
        }});
    </script>
</body>
</html>"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

# ── Validation Helper ────────────────────────────────────────────────────────
def validate_plugin():
    errors = []
    required_meta_keys = ['plugin_id', 'display_name', 'version', 'category', 'required_params']
    for key in required_meta_keys:
        if key not in METADATA:
            errors.append(f"Missing METADATA key: {key}")
    if 'run' not in globals() or not callable(globals()['run']):
        errors.append("Missing required 'run' function")
    return len(errors) == 0, errors

if __name__ == "__main__":
    is_valid, errors = validate_plugin()
    if is_valid:
        print(f"✅ Plugin '{METADATA['plugin_id']}' is valid!")
    else:
        for err in errors:
            print(f"❌ {err}")
        exit(1)
