"""
_generate_sample_maps.py
------------------------
Generates realistic sample HTML maps for all map types in Network Swiss Tool Pro.

Devices: NOC-realistic 7-device topology (Cisco IOS/XE/NX-OS, Juniper JunOS)
Maps produced:
  sample_map_l3.html          — L3 routing map  (render_l3_map_html)
  sample_map_l3_flow.html     — L3 flow map     (render_l3_map_html, map_kind='flow')
  sample_map_l3_enhanced.html — Enhanced L3     (render_l3_map_html_enhanced)
  sample_map_combined.html    — Combined L2+L3  (render_combined_l2l3_html)
  sample_map_l2.html          — Standard L2     (render_topology_page)

Run from the project root:
  python _generate_sample_maps.py
"""
import json
import os
import sys
import traceback
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ---------------------------------------------------------------------------
# Realistic NOC device data
# ---------------------------------------------------------------------------

DEVICES = {
    "core-rtr-01": {
        "platform": "cisco_ios",
        "management_ip": "10.0.0.1",
        "ssh_port": 22,
        "default_gateway": "0.0.0.0",
        "route_count": 42,
        "vrf_count": 2,
        "vrf_names": ["MGMT", "PROD"],
        "protocols": ["OSPF", "BGP", "Connected", "Static"],
        "route_count_by_protocol": {"OSPF": 18, "BGP": 12, "Connected": 8, "Static": 4},
        "interfaces": {
            "GigabitEthernet0/0": "10.0.0.1/30",
            "GigabitEthernet0/1": "10.0.0.5/30",
            "Loopback0": "192.168.100.1/32",
        },
        "local_ips": ["10.0.0.1", "10.0.0.5", "192.168.100.1"],
    },
    "core-rtr-02": {
        "platform": "cisco_xe",
        "management_ip": "10.0.0.2",
        "ssh_port": 22,
        "default_gateway": "0.0.0.0",
        "route_count": 38,
        "vrf_count": 2,
        "vrf_names": ["MGMT", "PROD"],
        "protocols": ["OSPF", "BGP", "Connected", "Static"],
        "route_count_by_protocol": {"OSPF": 16, "BGP": 12, "Connected": 7, "Static": 3},
        "interfaces": {
            "GigabitEthernet0/0/0": "10.0.0.2/30",
            "GigabitEthernet0/0/1": "10.0.0.9/30",
            "Loopback0": "192.168.100.2/32",
        },
        "local_ips": ["10.0.0.2", "10.0.0.9", "192.168.100.2"],
    },
    "dist-sw-01": {
        "platform": "cisco_nxos",
        "management_ip": "172.16.1.1",
        "ssh_port": 22,
        "default_gateway": "10.0.0.1",
        "route_count": 22,
        "vrf_count": 2,
        "vrf_names": ["MGMT", "PROD"],
        "protocols": ["OSPF", "Connected", "Static"],
        "route_count_by_protocol": {"OSPF": 14, "Connected": 6, "Static": 2},
        "interfaces": {
            "Ethernet1/1": "10.0.0.6/30",
            "Ethernet1/2": "172.16.1.1/24",
            "Loopback0": "192.168.100.11/32",
        },
        "local_ips": ["10.0.0.6", "172.16.1.1", "192.168.100.11"],
    },
    "dist-sw-02": {
        "platform": "cisco_nxos",
        "management_ip": "172.16.2.1",
        "ssh_port": 22,
        "default_gateway": "10.0.0.2",
        "route_count": 20,
        "vrf_count": 2,
        "vrf_names": ["MGMT", "PROD"],
        "protocols": ["OSPF", "Connected", "Static"],
        "route_count_by_protocol": {"OSPF": 13, "Connected": 5, "Static": 2},
        "interfaces": {
            "Ethernet1/1": "10.0.0.10/30",
            "Ethernet1/2": "172.16.2.1/24",
            "Loopback0": "192.168.100.12/32",
        },
        "local_ips": ["10.0.0.10", "172.16.2.1", "192.168.100.12"],
    },
    "edge-rtr-01": {
        "platform": "juniper_junos",
        "management_ip": "10.0.0.13",
        "ssh_port": 22,
        "default_gateway": "0.0.0.0",
        "route_count": 55,
        "vrf_count": 1,
        "vrf_names": ["PROD"],
        "protocols": ["BGP", "OSPF", "Connected", "Static"],
        "route_count_by_protocol": {"BGP": 30, "OSPF": 15, "Connected": 7, "Static": 3},
        "interfaces": {
            "ge-0/0/0.0": "10.0.0.13/30",
            "ge-0/0/1.0": "10.0.0.17/30",
            "lo0.0": "192.168.100.21/32",
        },
        "local_ips": ["10.0.0.13", "10.0.0.17", "192.168.100.21"],
    },
    "access-sw-01": {
        "platform": "cisco_ios",
        "management_ip": "192.168.10.1",
        "ssh_port": 22,
        "default_gateway": "172.16.1.1",
        "route_count": 8,
        "vrf_count": 1,
        "vrf_names": ["MGMT"],
        "protocols": ["Connected", "Static"],
        "route_count_by_protocol": {"Connected": 6, "Static": 2},
        "interfaces": {
            "GigabitEthernet0/1": "172.16.1.2/24",
            "GigabitEthernet0/2": "192.168.10.1/24",
            "Loopback0": "192.168.100.31/32",
        },
        "local_ips": ["172.16.1.2", "192.168.10.1", "192.168.100.31"],
    },
    "access-sw-02": {
        "platform": "cisco_ios",
        "management_ip": "192.168.20.1",
        "ssh_port": 22,
        "default_gateway": "172.16.2.1",
        "route_count": 8,
        "vrf_count": 1,
        "vrf_names": ["MGMT"],
        "protocols": ["Connected", "Static"],
        "route_count_by_protocol": {"Connected": 6, "Static": 2},
        "interfaces": {
            "GigabitEthernet0/1": "172.16.2.2/24",
            "GigabitEthernet0/2": "192.168.20.1/24",
            "Loopback0": "192.168.100.32/32",
        },
        "local_ips": ["172.16.2.2", "192.168.20.1", "192.168.100.32"],
    },
}

COLLECTED_AT = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _l3_vis_payload():
    """Build a complete vis_payload for the L3 map shells."""
    nodes = []
    for dev_id, info in DEVICES.items():
        p = info["platform"]
        if "junos" in p or "juniper" in p:
            shape = "diamond"
            color_bg = "#f97316"
            color_border = "#c2410c"
        elif "nxos" in p:
            shape = "box"
            color_bg = "#6366f1"
            color_border = "#4338ca"
        elif "xe" in p:
            shape = "box"
            color_bg = "#00bceb"
            color_border = "#0085a3"
        else:
            shape = "box"
            color_bg = "#00bceb"
            color_border = "#0085a3"
        nodes.append({
            "id": dev_id,
            "label": dev_id,
            "group": "device",
            "platform": p,
            "shape": shape,
            "title": f"{dev_id} | {p} | {info['management_ip']}",
            "color": {"background": color_bg, "border": color_border,
                      "highlight": {"background": color_bg, "border": "#fff"}},
        })

    # Subnet nodes
    subnets = [
        "10.0.0.0/30", "10.0.0.4/30", "10.0.0.8/30",
        "172.16.1.0/24", "172.16.2.0/24",
        "192.168.10.0/24", "192.168.20.0/24",
    ]
    for sn in subnets:
        nodes.append({
            "id": sn,
            "label": sn,
            "group": "subnet",
            "shape": "ellipse",
            "title": f"Subnet {sn}",
            "color": {"background": "#8b5cf6", "border": "#6d28d9",
                      "highlight": {"background": "#a78bfa", "border": "#8b5cf6"}},
        })

    # Gateway node for default routes
    nodes.append({
        "id": "0.0.0.0/0",
        "label": "Default GW\n0.0.0.0/0",
        "group": "default_gateway",
        "shape": "star",
        "title": "Default Gateway / Internet",
        "color": {"background": "#ef4444", "border": "#b91c1c",
                  "highlight": {"background": "#f87171", "border": "#dc2626"}},
    })

    edges = []
    eid = 1

    def add_edge(frm, to, label, protocol, color="#475569", dashes=False):
        nonlocal eid
        edges.append({
            "id": eid, "from": frm, "to": to,
            "label": label,
            "protocol": protocol,
            "layer": "l3",
            "color": {"color": color, "highlight": "#818cf8"},
            "dashes": dashes,
            "width": 1.5,
        })
        eid += 1

    # Device-to-subnet connections
    add_edge("core-rtr-01", "10.0.0.0/30", "Gi0/0\n10.0.0.1/30", "Connected", "#10b981")
    add_edge("core-rtr-02", "10.0.0.0/30", "Gi0/0/0\n10.0.0.2/30", "Connected", "#10b981")
    add_edge("core-rtr-01", "10.0.0.4/30", "Gi0/1\n10.0.0.5/30", "Connected", "#10b981")
    add_edge("dist-sw-01", "10.0.0.4/30", "Eth1/1\n10.0.0.6/30", "Connected", "#10b981")
    add_edge("core-rtr-02", "10.0.0.8/30", "Gi0/0/1\n10.0.0.9/30", "Connected", "#10b981")
    add_edge("dist-sw-02", "10.0.0.8/30", "Eth1/1\n10.0.0.10/30", "Connected", "#10b981")
    add_edge("dist-sw-01", "172.16.1.0/24", "Eth1/2\nOSPF", "OSPF", "#1d4ed8")
    add_edge("access-sw-01", "172.16.1.0/24", "Gi0/1", "Connected", "#10b981")
    add_edge("dist-sw-02", "172.16.2.0/24", "Eth1/2\nOSPF", "OSPF", "#1d4ed8")
    add_edge("access-sw-02", "172.16.2.0/24", "Gi0/1", "Connected", "#10b981")
    add_edge("access-sw-01", "192.168.10.0/24", "Gi0/2", "Connected", "#10b981")
    add_edge("access-sw-02", "192.168.20.0/24", "Gi0/2", "Connected", "#10b981")
    # BGP to edge router
    add_edge("core-rtr-01", "edge-rtr-01", "eBGP AS65001↔65002", "BGP", "#065f46", dashes=True)
    add_edge("core-rtr-02", "edge-rtr-01", "eBGP backup", "BGP", "#065f46", dashes=True)
    # Default gateway from edge routers
    add_edge("core-rtr-01", "0.0.0.0/0", "ip route 0.0.0.0/0", "Static", "#ef4444", dashes=True)
    add_edge("edge-rtr-01", "0.0.0.0/0", "static default", "Static", "#ef4444", dashes=True)

    # OSPF edges between core and distribution
    add_edge("core-rtr-01", "dist-sw-01", "OSPF area 0", "OSPF", "#1d4ed8")
    add_edge("core-rtr-02", "dist-sw-02", "OSPF area 0", "OSPF", "#1d4ed8")

    all_routes = []
    for dev_id, info in DEVICES.items():
        for dest, nh in [
            ("10.0.0.0/30", "direct"), ("10.0.0.4/30", "direct"),
            ("172.16.1.0/24", "10.0.0.6"), ("172.16.2.0/24", "10.0.0.10"),
            ("192.168.10.0/24", "172.16.1.2"), ("192.168.20.0/24", "172.16.2.2"),
            ("0.0.0.0/0", "10.0.0.13"),
        ]:
            proto = "Connected" if nh == "direct" else "OSPF"
            all_routes.append({
                "device_id": dev_id,
                "destination": dest,
                "next_hop": nh,
                "protocol": proto,
                "interface": list(info["interfaces"].keys())[0],
                "vrf": "PROD",
            })

    analysis = {
        "total_devices": len(DEVICES),
        "total_gateways": 1,
        "total_subnets": len(subnets),
        "total_routes": len(all_routes),
        "protocol_distribution": {"OSPF": 18, "BGP": 12, "Connected": 35, "Static": 9},
        "vrf_count": 2,
    }

    gateway_analysis = {
        "0.0.0.0/0": {
            "type": "default_gateway",
            "subnet_count": 1,
            "routing_devices": list(DEVICES.keys()),
            "subnets": ["0.0.0.0/0"],
            "protocols": ["Static", "BGP"],
        }
    }

    subnet_analysis = {}
    for sn in subnets:
        pl = int(sn.split("/")[1])
        size = 2 ** (32 - pl)
        subnet_analysis[sn] = {
            "prefix_len": pl,
            "subnet_size": size,
            "is_private": True,
            "gateway_ips": [],
            "advertising_devices": [],
        }

    return {
        "nodes": nodes,
        "edges": edges,
        "devices": DEVICES,
        "analysis": analysis,
        "gateway_analysis": gateway_analysis,
        "subnet_analysis": subnet_analysis,
        "all_routes": all_routes,
        "route_count": len(all_routes),
        "failed_hosts": [],
    }


def _combined_bundle():
    """Build a combined_bundle for render_combined_l2l3_html."""
    nodes = []
    for dev_id, info in DEVICES.items():
        p = info["platform"]
        if "junos" in p or "juniper" in p:
            grp = "gateway"
            color = "#f97316"
        elif "nxos" in p:
            grp = "switch"
            color = "#6366f1"
        else:
            grp = "switch"
            color = "#10b981"
        nodes.append({
            "id": dev_id,
            "label": dev_id,
            "group": grp,
            "layer": "l2",
            "platform": p,
            "protocols": info["protocols"],
            "title": f"{dev_id} | {p} | {info['management_ip']}",
            "color": {"background": color, "border": color},
        })

    # Also add subnet nodes as L3 layer
    for sn in ["10.0.0.0/30", "10.0.0.4/30", "172.16.1.0/24", "172.16.2.0/24",
               "192.168.10.0/24", "192.168.20.0/24"]:
        nodes.append({
            "id": sn,
            "label": sn,
            "group": "subnet",
            "layer": "l3",
            "title": f"Subnet {sn}",
            "color": {"background": "#8b5cf6", "border": "#6d28d9"},
        })

    edges = []
    eid = 1

    def l2_edge(frm, to, local_port, remote_port, link_type="lldp-neighbor"):
        nonlocal eid
        edges.append({
            "id": eid, "from": frm, "to": to,
            "label": f"{local_port}↔{remote_port}",
            "layer": "l2",
            "link_type": link_type,
            "local_port": local_port,
            "remote_port": remote_port,
            "physical_link": f"{frm}:{local_port}—{to}:{remote_port}",
            "color": {"color": "#10b981", "highlight": "#34d399"},
            "width": 2,
        })
        eid += 1

    def l3_edge(frm, to, label, protocol, physical_link=None):
        nonlocal eid
        edges.append({
            "id": eid, "from": frm, "to": to,
            "label": label,
            "layer": "l3",
            "protocol": protocol,
            "physical_link": physical_link or "",
            "color": {"color": "#3b82f6", "highlight": "#818cf8"},
            "dashes": True,
            "width": 1.5,
        })
        eid += 1

    # L2 physical links with realistic port names
    l2_edge("core-rtr-01", "dist-sw-01", "Gi0/1", "Eth1/1")
    l2_edge("core-rtr-01", "core-rtr-02", "Gi0/2", "Gi0/2", "cdp-neighbor")
    l2_edge("core-rtr-02", "dist-sw-02", "Gi0/0/1", "Eth1/1")
    l2_edge("dist-sw-01", "access-sw-01", "Eth1/3", "Gi0/1")
    l2_edge("dist-sw-02", "access-sw-02", "Eth1/3", "Gi0/1")
    l2_edge("core-rtr-01", "edge-rtr-01", "Gi0/3", "ge-0/0/0.0", "lldp-neighbor")
    l2_edge("core-rtr-02", "edge-rtr-01", "Gi0/0/2", "ge-0/0/1.0", "lldp-neighbor")

    # L3 routing edges (correlated over physical links)
    l3_edge("core-rtr-01", "dist-sw-01", "OSPF area 0", "OSPF",
            "core-rtr-01:Gi0/1—dist-sw-01:Eth1/1")
    l3_edge("core-rtr-02", "dist-sw-02", "OSPF area 0", "OSPF",
            "core-rtr-02:Gi0/0/1—dist-sw-02:Eth1/1")
    l3_edge("core-rtr-01", "edge-rtr-01", "eBGP AS65001↔65002", "BGP",
            "core-rtr-01:Gi0/3—edge-rtr-01:ge-0/0/0.0")
    l3_edge("core-rtr-02", "edge-rtr-01", "eBGP backup", "BGP",
            "core-rtr-02:Gi0/0/2—edge-rtr-01:ge-0/0/1.0")
    l3_edge("dist-sw-01", "10.0.0.4/30", "Connected", "Connected")
    l3_edge("dist-sw-02", "172.16.2.0/24", "Connected", "Connected")

    n_l2 = sum(1 for e in edges if e.get("layer") == "l2")
    n_l3 = sum(1 for e in edges if e.get("layer") == "l3")
    n_correlated = sum(1 for e in edges if e.get("layer") == "l3" and e.get("physical_link"))

    analysis = {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "l2_edge_count": n_l2,
        "l3_edge_count": n_l3,
        "correlated_edges": n_correlated,
        "gateway_count": 1,
    }

    correlation = {
        "core-rtr-01→dist-sw-01": {"physical_link": "Gi0/1—Eth1/1", "protocols": ["OSPF"]},
        "core-rtr-02→dist-sw-02": {"physical_link": "Gi0/0/1—Eth1/1", "protocols": ["OSPF"]},
        "core-rtr-01→edge-rtr-01": {"physical_link": "Gi0/3—ge-0/0/0.0", "protocols": ["BGP"]},
    }

    return {
        "nodes": nodes,
        "edges": edges,
        "analysis": analysis,
        "correlation": correlation,
    }


def _topo_link_rows():
    """Build link_rows for render_topology_page (standard L2 map)."""
    rows = [
        {
            "from": "core-rtr-01", "to": "dist-sw-01",
            "local_port": "Gi0/1", "remote_port": "Eth1/1",
            "link_type": "cdp-neighbor", "protocol": "CDP",
            "vlan": "trunk", "trust_tier": "verified",
            "sources": ["CDP"], "evidence": [],
            "collected_at": COLLECTED_AT, "freshness": "fresh",
        },
        {
            "from": "core-rtr-01", "to": "core-rtr-02",
            "local_port": "Gi0/2", "remote_port": "Gi0/2",
            "link_type": "cdp-neighbor", "protocol": "CDP",
            "vlan": "trunk", "trust_tier": "verified",
            "sources": ["CDP"], "evidence": [],
            "collected_at": COLLECTED_AT, "freshness": "fresh",
        },
        {
            "from": "core-rtr-02", "to": "dist-sw-02",
            "local_port": "Gi0/0/1", "remote_port": "Eth1/1",
            "link_type": "cdp-neighbor", "protocol": "CDP",
            "vlan": "trunk", "trust_tier": "verified",
            "sources": ["CDP"], "evidence": [],
            "collected_at": COLLECTED_AT, "freshness": "fresh",
        },
        {
            "from": "dist-sw-01", "to": "access-sw-01",
            "local_port": "Eth1/3", "remote_port": "Gi0/1",
            "link_type": "lldp-neighbor", "protocol": "LLDP",
            "vlan": "10,20", "trust_tier": "verified",
            "sources": ["LLDP"], "evidence": [],
            "collected_at": COLLECTED_AT, "freshness": "fresh",
        },
        {
            "from": "dist-sw-02", "to": "access-sw-02",
            "local_port": "Eth1/3", "remote_port": "Gi0/1",
            "link_type": "lldp-neighbor", "protocol": "LLDP",
            "vlan": "10,20", "trust_tier": "verified",
            "sources": ["LLDP"], "evidence": [],
            "collected_at": COLLECTED_AT, "freshness": "fresh",
        },
        {
            "from": "core-rtr-01", "to": "edge-rtr-01",
            "local_port": "Gi0/3", "remote_port": "ge-0/0/0.0",
            "link_type": "lldp-neighbor", "protocol": "LLDP",
            "vlan": "none", "trust_tier": "medium",
            "sources": ["LLDP"], "evidence": [],
            "one_sided": False,
            "collected_at": COLLECTED_AT, "freshness": "fresh",
        },
        {
            "from": "core-rtr-02", "to": "edge-rtr-01",
            "local_port": "Gi0/0/2", "remote_port": "ge-0/0/1.0",
            "link_type": "lldp-neighbor", "protocol": "LLDP",
            "vlan": "none", "trust_tier": "medium",
            "sources": ["LLDP"], "evidence": [],
            "collected_at": COLLECTED_AT, "freshness": "fresh",
        },
    ]
    return rows


def _topo_vis_nodes_edges():
    """Vis.js nodes/edges for render_topology_page (standard L2 map)."""
    device_roles = {
        "core-rtr-01": ("core", "#00bceb"),
        "core-rtr-02": ("core", "#00bceb"),
        "dist-sw-01": ("distribution", "#6366f1"),
        "dist-sw-02": ("distribution", "#6366f1"),
        "edge-rtr-01": ("core", "#f97316"),
        "access-sw-01": ("access", "#10b981"),
        "access-sw-02": ("access", "#10b981"),
    }
    nodes = []
    for dev_id, info in DEVICES.items():
        role, color = device_roles.get(dev_id, ("unknown", "#64748b"))
        nodes.append({
            "id": dev_id,
            "label": dev_id,
            "group": role,
            "role": role,
            "platform": info["platform"],
            "shape": "box",
            "color": {"background": color, "border": color,
                      "highlight": {"background": "#fff", "border": color}},
            "title": f"{dev_id} | {info['platform']} | {info['management_ip']}",
        })

    edges = []
    link_rows = _topo_link_rows()
    for i, lr in enumerate(link_rows):
        edges.append({
            "id": i + 1,
            "from": lr["from"],
            "to": lr["to"],
            "label": f"{lr['local_port']}↔{lr['remote_port']}",
            "local_port": lr["local_port"],
            "remote_port": lr["remote_port"],
            "link_type": lr["link_type"],
            "protocol": lr["protocol"],
            "trust_tier": lr["trust_tier"],
            "relation_key": f"{lr['from']}|{lr['local_port']}|{lr['to']}|{lr['remote_port']}|l2",
            "color": {"color": "#475569", "highlight": "#8b5cf6"},
            "width": 2,
        })

    return nodes, edges


# ---------------------------------------------------------------------------
# Map generators
# ---------------------------------------------------------------------------

def generate_l3_map():
    from utils.l3_map_shell import render_l3_map_html
    payload = _l3_vis_payload()
    html = render_l3_map_html(
        payload,
        title="NOC L3 Routing Map — Sample",
        subtitle=f"7 devices · OSPF/BGP/Static · VRFs: MGMT, PROD · {COLLECTED_AT}",
        map_kind="l3",
    )
    out = os.path.join(ROOT, "sample_map_l3.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  [OK] {out}  ({len(html):,} bytes)")


def generate_l3_flow_map():
    from utils.l3_map_shell import render_l3_map_html
    payload = _l3_vis_payload()
    # For flow map, add flow-direction labels on edges
    for e in payload["edges"]:
        if e.get("protocol") == "BGP":
            e["label"] = e.get("label", "") + "\n→ flow"
    html = render_l3_map_html(
        payload,
        title="NOC L3 Flow Map — Sample",
        subtitle=f"Traffic flow overlay · {COLLECTED_AT}",
        map_kind="flow",
    )
    out = os.path.join(ROOT, "sample_map_l3_flow.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  [OK] {out}  ({len(html):,} bytes)")


def generate_l3_enhanced_map():
    from utils.l3_map_shell_enhanced import render_l3_map_html_enhanced
    payload = _l3_vis_payload()
    html = render_l3_map_html_enhanced(
        payload,
        title="NOC L3 Enhanced Map — Sample",
        subtitle=f"OSPF/BGP · 7 devices · {COLLECTED_AT}",
        map_kind="l3",
    )
    out = os.path.join(ROOT, "sample_map_l3_enhanced.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  [OK] {out}  ({len(html):,} bytes)")


def generate_combined_map():
    from utils.combined_l2l3_shell import render_combined_l2l3_html
    bundle = _combined_bundle()
    html = render_combined_l2l3_html(
        bundle,
        title="NOC Combined L2+L3 Topology — Sample",
        subtitle=f"CDP/LLDP + OSPF/BGP correlation · {COLLECTED_AT}",
        map_kind="combined",
    )
    out = os.path.join(ROOT, "sample_map_combined.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  [OK] {out}  ({len(html):,} bytes)")


def generate_l2_standard_map():
    """Use render_topology_page from utils/topo_map_shell.py for the standard L2 map."""
    from utils.topo_map_shell import render_topology_page
    nodes, edges = _topo_vis_nodes_edges()
    link_rows = _topo_link_rows()
    out = os.path.join(ROOT, "sample_map_l2.html")
    render_topology_page(
        filepath=out,
        title="NOC Standard L2 Map — Sample",
        nodes_json=nodes,
        edges_json=edges,
        link_rows=link_rows,
        subtitle=f"7 devices · CDP/LLDP · {COLLECTED_AT}",
        accent="#8b5cf6",
        links_default=True,
    )
    size = os.path.getsize(out)
    print(f"  [OK] {out}  ({size:,} bytes)")


# ---------------------------------------------------------------------------
# CSS inspection helpers
# ---------------------------------------------------------------------------

def inspect_standard_map_shell():
    """Report CSS facts from utils/standard_map_shell.py as requested."""
    shell_path = os.path.join(ROOT, "utils", "standard_map_shell.py")
    with open(shell_path, encoding="utf-8") as f:
        src = f.read()

    lines = src.splitlines()
    first_100 = "\n".join(lines[:100])

    has_bg0_var = "--bg0:" in src
    has_var_bg0 = "var(--bg0)" in src
    has_old_padding = "padding: 12px 16px" in src
    has_new_flex = "flex: 1 1 0%" in src

    # Find body.nst-standard-map rule text
    body_map_lines = []
    in_body_rule = False
    for line in lines:
        if "body.nst-standard-map {" in line or "body.nst-standard-map{" in line:
            in_body_rule = True
        if in_body_rule:
            body_map_lines.append(line)
            if "}" in line and in_body_rule and len(body_map_lines) > 1:
                break

    # Find nst-top-row h1 font-size
    h1_font_size = None
    for i, line in enumerate(lines):
        if "nst-top-row h1" in line or (".nst-top-row h1" in line):
            # look ahead for font-size
            for j in range(i, min(i + 8, len(lines))):
                if "font-size:" in lines[j]:
                    h1_font_size = lines[j].strip()
                    break

    print("\n" + "=" * 65)
    print("CSS INSPECTION — utils/standard_map_shell.py (first 100 lines)")
    print("=" * 65)
    print(first_100)
    print("\n" + "=" * 65)
    print("CSS VARIABLE CHECK")
    print("=" * 65)
    print(f"  --bg0 CSS variable defined:     {has_bg0_var}")
    print(f"  var(--bg0) used:                {has_var_bg0}")
    print()
    print("BODY.NST-STANDARD-MAP CHECK")
    print("-" * 65)
    print("  Found rule:")
    for ln in body_map_lines:
        print(f"    {ln}")
    print()
    print(f"  OLD padding: 12px 16px present: {has_old_padding}")
    print(f"  NEW flex: 1 1 0% present:       {has_new_flex}")
    if has_old_padding:
        print("  => CONCLUSION: OLD CSS (has padding: 12px 16px)")
    elif has_new_flex:
        print("  => CONCLUSION: NEW CSS (no old padding — flex: 1 1 0%)")
    else:
        print("  => CONCLUSION: Neither old padding nor new flex found in body rule")
    print()
    print("NST-TOP-ROW H1 FONT-SIZE")
    print("-" * 65)
    if h1_font_size:
        print(f"  {h1_font_size}")
    else:
        print("  (not found in first pass — check manually)")
    print("=" * 65 + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

GENERATORS = [
    ("L3 routing map",     generate_l3_map),
    ("L3 flow map",        generate_l3_flow_map),
    ("L3 enhanced map",    generate_l3_enhanced_map),
    ("Combined L2+L3 map", generate_combined_map),
    ("Standard L2 map",    generate_l2_standard_map),
]

def main():
    print(f"\nGenerating sample maps in: {ROOT}\n")
    errors = []
    for name, fn in GENERATORS:
        print(f"  Generating {name}...")
        try:
            fn()
        except Exception as exc:
            print(f"  [ERROR] {name}: {exc}")
            traceback.print_exc()
            errors.append((name, exc))

    inspect_standard_map_shell()

    print("\n" + "=" * 65)
    if errors:
        print(f"DONE with {len(errors)} error(s):")
        for name, exc in errors:
            print(f"  - {name}: {exc}")
    else:
        print("ALL 5 MAPS GENERATED SUCCESSFULLY — no errors.")
    print("=" * 65)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
