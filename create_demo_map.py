import json
import os
from utils.report_formatter import generate_topology_html

def create_demo():
    # Load vis.js for offline functionality
    vis_js_path = os.path.join("modules", "web", "vis-network.min.js")
    vis_js_content = ""
    if os.path.exists(vis_js_path):
        with open(vis_js_path, "r", encoding="utf-8") as f:
            vis_js_content = f.read()
    else:
        print(f"WARNING: {vis_js_path} not found. Map might not work offline.")

    nodes = [
        {
            "id": "N9K-1",
            "label": "N9K-1",
            "group": "nexus",
            "title": "Nexus 9000 Switch",
            "metadata": {
                "vpc_structured": {
                    "domain_id": "10", "role": "Primary", "peer_status": "peer adjacency formed ok", "keepalive_status": "peer is alive",
                    "vpc_table": [{"vpc_id": "100", "po": "Po100", "status": "up", "consistency": "success", "active_vlans": "10,20"}]
                },
                "port_channel_detail": {
                    "Po100": {"protocol": "LACP", "members": [{"intf": "Eth1/1", "status": "up", "flags": "P"}]}
                }
            }
        },
        {
            "id": "N9K-2",
            "label": "N9K-2",
            "group": "nexus",
            "title": "Nexus 9000 Switch",
            "metadata": {
                "vpc_structured": {
                    "domain_id": "10", "role": "Secondary", "peer_status": "peer adjacency formed ok", "keepalive_status": "peer is alive",
                    "vpc_table": [{"vpc_id": "100", "po": "Po100", "status": "up", "consistency": "success", "active_vlans": "10,20"}]
                }
            }
        },
        {
            "id": "Server-A",
            "label": "Server-A",
            "group": "server",
            "title": "Downstream Host"
        },
        {
            "id": "VPC_Domain_10",
            "label": "vPC Domain 10",
            "group": "vpc_domain",
            "title": "vPC Domain 10 (N9K-1, N9K-2)",
            "vpc_members": ["N9K-1", "N9K-2"],
            "metadata": {
                "vpc_structured": {
                    "domain_id": "10", "role": "Primary/Secondary", "peer_status": "peer adjacency formed ok", "keepalive_status": "peer is alive",
                    "vpc_table": [{"vpc_id": "100", "po": "Po100", "status": "up", "consistency": "success", "active_vlans": "10,20"}]
                }
            }
        }
    ]

    edges = [
        {
            "from": "VPC_Domain_10",
            "to": "Server-A",
            "label": "vPC 100",
            "f_port": "Po100",
            "t_port": "eth0",
            "color": {"color": "#3b82f6", "highlight": "#2563eb"},
            "is_vpc_member": True,
            "f_int_data": {"status": "up", "speed": "10G", "desc": "LACP Trunk to Server-A"},
            "metadata": {
                "cdp_validated": True,
                "is_orphan": False,
                "is_vpc_member": True,
                "lacp_partner": "32768,00-aa-bb-cc-dd-ee",
                "lacp_state": "bndl",
                "bundled_links": [
                    {"from_node": "N9K-1", "f_port": "Eth1/1", "t_port": "eth0", "is_vpc_member": True, "cdp_validated": True},
                    {"from_node": "N9K-2", "f_port": "Eth1/1", "t_port": "eth1", "is_vpc_member": True, "cdp_validated": True}
                ]
            }
        },
        {
            "from": "N9K-1",
            "to": "VPC_Domain_10",
            "label": "Member",
            "hidden": True
        },
        {
            "from": "N9K-2",
            "to": "VPC_Domain_10",
            "label": "Member",
            "hidden": True
        }
    ]
    
    output_file = "DEMO_VPC_TOPOLOGY_v6.9.1.html"
    generate_topology_html(output_file, len(nodes), len(edges), json.dumps(nodes), json.dumps(edges), vis_js_content, map_mode="vpc")
    print(f"Demo created: {output_file}")

if __name__ == "__main__":
    create_demo()
