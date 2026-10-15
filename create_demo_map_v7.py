import json
import os
from utils.report_formatter import generate_topology_html
from modules.adapters import _build_html_presentation_payload, _assign_vpc_fixed_positions

def create_v7_demo():
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
            "id": "N9K-SW1",
            "label": "N9K-SW1\n3 UP | 0 DOWN",
            "shape": "box",
            "role": "vpc_primary",
            "group": "vpc_primary",
            "vpc_domain_id": "10",
            "is_scanned": True,
            "port_stats": {"up": 3, "down": 0, "err": 0, "total": 3},
            "device_info": {"platform": "Cisco Nexus 9000 C93180YC-EX", "version": "9.3(5)", "mgmt_ip": "192.168.10.1", "caps": "Switch"},
            "interfaces": {
                "Eth1/1": {"status": "up", "speed": "40G", "duplex": "full", "desc": "vPC Peer-Link 1/2", "vlan": "trunk", "macs": []},
                "Eth1/2": {"status": "up", "speed": "40G", "duplex": "full", "desc": "vPC Peer-Link 2/2", "vlan": "trunk", "macs": []},
                "Eth1/10": {"status": "up", "speed": "10G", "duplex": "full", "desc": "vPC Member Eth1/10 to Access-SW", "vlan": "trunk", "macs": []},
                "Eth1/20": {"status": "up", "speed": "10G", "duplex": "full", "desc": "vPC Member Eth1/20 to Database-SRV", "vlan": "10", "macs": []}
            },
            "vpc_details": {
                "Po1": {"type": "peer-link", "status": "up", "vpc_id": None, "consistency": "success"},
                "Po10": {"type": "vpc", "status": "up", "vpc_id": "10", "consistency": "success"},
                "Po20": {"type": "vpc", "status": "up", "vpc_id": "20", "consistency": "success"}
            },
            "port_channel_detail": {
                "Po1": {"protocol": "LACP", "members": [{"intf": "Eth1/1"}, {"intf": "Eth1/2"}]},
                "Po10": {"protocol": "LACP", "members": [{"intf": "Eth1/10"}]},
                "Po20": {"protocol": "LACP", "members": [{"intf": "Eth1/20"}]}
            },
            "vpc_structured": {
                "domain_id": "10",
                "role": "primary",
                "peer_status": "up",
                "keepalive_status": "alive",
                "peer_link_po": "Po1",
                "vpc_table": [
                    {"vpc_id": "10", "po": "Po10", "status": "up", "consistency": "success", "active_vlans": "1-4094"},
                    {"vpc_id": "20", "po": "Po20", "status": "up", "consistency": "success", "active_vlans": "10"}
                ]
            }
        },
        {
            "id": "N9K-SW2",
            "label": "N9K-SW2\n3 UP | 0 DOWN",
            "shape": "box",
            "role": "vpc_secondary",
            "group": "vpc_secondary",
            "vpc_domain_id": "10",
            "is_scanned": True,
            "port_stats": {"up": 3, "down": 0, "err": 0, "total": 3},
            "device_info": {"platform": "Cisco Nexus 9000 C93180YC-EX", "version": "9.3(5)", "mgmt_ip": "192.168.10.2", "caps": "Switch"},
            "interfaces": {
                "Eth1/1": {"status": "up", "speed": "40G", "duplex": "full", "desc": "vPC Peer-Link 1/2", "vlan": "trunk", "macs": []},
                "Eth1/2": {"status": "up", "speed": "40G", "duplex": "full", "desc": "vPC Peer-Link 2/2", "vlan": "trunk", "macs": []},
                "Eth1/10": {"status": "up", "speed": "10G", "duplex": "full", "desc": "vPC Member Eth1/10 to Access-SW", "vlan": "trunk", "macs": []},
                "Eth1/20": {"status": "up", "speed": "10G", "duplex": "full", "desc": "vPC Member Eth1/20 to Database-SRV", "vlan": "10", "macs": []}
            },
            "vpc_details": {
                "Po1": {"type": "peer-link", "status": "up", "vpc_id": None, "consistency": "success"},
                "Po10": {"type": "vpc", "status": "up", "vpc_id": "10", "consistency": "success"},
                "Po20": {"type": "vpc", "status": "up", "vpc_id": "20", "consistency": "success"}
            },
            "port_channel_detail": {
                "Po1": {"protocol": "LACP", "members": [{"intf": "Eth1/1"}, {"intf": "Eth1/2"}]},
                "Po10": {"protocol": "LACP", "members": [{"intf": "Eth1/10"}]},
                "Po20": {"protocol": "LACP", "members": [{"intf": "Eth1/20"}]}
            },
            "vpc_structured": {
                "domain_id": "10",
                "role": "secondary",
                "peer_status": "up",
                "keepalive_status": "alive",
                "peer_link_po": "Po1",
                "vpc_table": [
                    {"vpc_id": "10", "po": "Po10", "status": "up", "consistency": "success", "active_vlans": "1-4094"},
                    {"vpc_id": "20", "po": "Po20", "status": "up", "consistency": "success", "active_vlans": "10"}
                ]
            }
        },
        {
            "id": "VPC_Domain_10",
            "label": "vPC Domain 10\n(N9K-SW1, N9K-SW2)",
            "shape": "box",
            "role": "vpc_domain",
            "group": "vpc_domain",
            "vpc_domain_id": "10",
            "vpc_members": ["N9K-SW1", "N9K-SW2"],
            "port_stats": {"up": 6, "down": 0, "err": 0, "total": 6},
            "vpc_details": {
                "N9K-SW1: Po1": {"type": "peer-link", "status": "up", "vpc_id": None},
                "N9K-SW1: Po10": {"type": "vpc", "status": "up", "vpc_id": "10"},
                "N9K-SW1: Po20": {"type": "vpc", "status": "up", "vpc_id": "20"},
                "N9K-SW2: Po1": {"type": "peer-link", "status": "up", "vpc_id": None},
                "N9K-SW2: Po10": {"type": "vpc", "status": "up", "vpc_id": "10"},
                "N9K-SW2: Po20": {"type": "vpc", "status": "up", "vpc_id": "20"}
            },
            "vpc_structured": [
                {
                    "member": "N9K-SW1",
                    "vpc_structured": {
                        "domain_id": "10", "role": "primary", "keepalive_status": "alive",
                        "vpc_table": [
                            {"vpc_id": "10", "po": "Po10", "status": "up", "consistency": "success", "active_vlans": "1-4094"},
                            {"vpc_id": "20", "po": "Po20", "status": "up", "consistency": "success", "active_vlans": "10"}
                        ]
                    }
                },
                {
                    "member": "N9K-SW2",
                    "vpc_structured": {
                        "domain_id": "10", "role": "secondary", "keepalive_status": "alive",
                        "vpc_table": [
                            {"vpc_id": "10", "po": "Po10", "status": "up", "consistency": "success", "active_vlans": "1-4094"},
                            {"vpc_id": "20", "po": "Po20", "status": "up", "consistency": "success", "active_vlans": "10"}
                        ]
                    }
                }
            ],
            "vpc_member_interfaces": {
                "N9K-SW1": {
                    "switch": "N9K-SW1",
                    "entries": [
                        {"vpc_id": "10", "port_channel": "Po10", "status": "up", "member_interfaces": ["Eth1/10"], "source": "demo"},
                        {"vpc_id": "20", "port_channel": "Po20", "status": "up", "member_interfaces": ["Eth1/20"], "source": "demo"}
                    ]
                },
                "N9K-SW2": {
                    "switch": "N9K-SW2",
                    "entries": [
                        {"vpc_id": "10", "port_channel": "Po10", "status": "up", "member_interfaces": ["Eth1/10"], "source": "demo"},
                        {"vpc_id": "20", "port_channel": "Po20", "status": "up", "member_interfaces": ["Eth1/20"], "source": "demo"}
                    ]
                }
            }
        },
        {
            "id": "Access-SW",
            "label": "Access-SW\n2 UP | 0 DOWN",
            "shape": "box",
            "role": "access",
            "group": "access",
            "is_scanned": True,
            "port_stats": {"up": 2, "down": 0, "err": 0, "total": 2},
            "device_info": {"platform": "Cisco Catalyst 3850", "version": "16.12.5", "mgmt_ip": "192.168.10.10", "caps": "Switch"},
            "interfaces": {
                "Gi1/0/1": {"status": "up", "speed": "10G", "duplex": "full", "desc": "Gi1/0/1 member of Po10 to SW1 Eth1/10", "vlan": "trunk", "macs": []},
                "Gi1/0/2": {"status": "up", "speed": "10G", "duplex": "full", "desc": "Gi1/0/2 member of Po10 to SW2 Eth1/10", "vlan": "trunk", "macs": []}
            }
        },
        {
            "id": "Database-SRV",
            "label": "Database-SRV\n2 UP | 0 DOWN",
            "shape": "box",
            "role": "access",
            "group": "access",
            "is_scanned": True,
            "port_stats": {"up": 2, "down": 0, "err": 0, "total": 2},
            "device_info": {"platform": "Dell PowerEdge R740", "version": "RHEL 8.4", "mgmt_ip": "192.168.10.20", "caps": "Host"},
            "interfaces": {
                "ens1f0": {"status": "up", "speed": "10G", "duplex": "full", "desc": "ens1f0 bond0 member to SW1 Eth1/20", "vlan": "10", "macs": []},
                "ens1f1": {"status": "up", "speed": "10G", "duplex": "full", "desc": "ens1f1 bond0 member to SW2 Eth1/20", "vlan": "10", "macs": []}
            }
        }
    ]

    edges = [
        # Peer link between physical switches
        {
            "from": "N9K-SW1",
            "to": "N9K-SW2",
            "label": "vPC Peer-Link (2x 40G Bundle)",
            "title": "N9K-SW1 (Eth1/1, Eth1/2) ↔ N9K-SW2 (Eth1/1, Eth1/2)",
            "type": "vpc-peer-link",
            "color": {"color": "#a55eea"},
            "width": 10,
            "edge_data": {
                "from": "N9K-SW1",
                "to": "N9K-SW2",
                "f_port": "Po1",
                "t_port": "Po1",
                "type": "vpc-peer-link",
                "label": "vPC Peer-Link (LACP Active)",
                "confidence": "High",
                "f_int_data": {"status": "up", "speed": "40G", "desc": "Peer Link to SW2"},
                "t_int_data": {"status": "up", "speed": "40G", "desc": "Peer Link to SW1"},
                "bundled_links": [
                    {"from": "N9K-SW1", "f_port": "Eth1/1", "to": "N9K-SW2", "t_port": "Eth1/1", "f_int_data": {"status": "up", "speed": "40G", "duplex": "full", "desc": "Peer Link Member"}},
                    {"from": "N9K-SW1", "f_port": "Eth1/2", "to": "N9K-SW2", "t_port": "Eth1/2", "f_int_data": {"status": "up", "speed": "40G", "duplex": "full", "desc": "Peer Link Member"}}
                ]
            }
        },
        # Logical association: SW1 to Domain 10
        {
            "from": "VPC_Domain_10",
            "to": "N9K-SW1",
            "label": "Logical Association",
            "type": "vpc-domain-peer",
            "color": {"color": "#8854d0"},
            "width": 4,
            "dashes": True,
            "edge_data": {
                "from": "VPC_Domain_10",
                "to": "N9K-SW1",
                "f_port": "Logical Domain",
                "t_port": "Physical Node",
                "type": "vpc-domain-peer",
                "label": "Logical Association",
                "confidence": "High",
                "f_int_data": {"status": "up", "desc": "Logical switch association"},
                "t_int_data": {"status": "up", "desc": "Logical switch association"}
            }
        },
        # Logical association: SW2 to Domain 10
        {
            "from": "VPC_Domain_10",
            "to": "N9K-SW2",
            "label": "Logical Association",
            "type": "vpc-domain-peer",
            "color": {"color": "#8854d0"},
            "width": 4,
            "dashes": True,
            "edge_data": {
                "from": "VPC_Domain_10",
                "to": "N9K-SW2",
                "f_port": "Logical Domain",
                "t_port": "Physical Node",
                "type": "vpc-domain-peer",
                "label": "Logical Association",
                "confidence": "High",
                "f_int_data": {"status": "up", "desc": "Logical switch association"},
                "t_int_data": {"status": "up", "desc": "Logical switch association"}
            }
        },
        # Shared connection: Domain 10 to Access-SW
        {
            "from": "VPC_Domain_10",
            "to": "Access-SW",
            "label": "vPC 10 (2/2 Active)",
            "title": "vPC Domain 10 (Po10) ↔ Access-SW (Port-Channel)",
            "type": "vpc_shared",
            "color": {"color": "#0984e3"},
            "width": 8,
            "bundled_links": [
                {
                    "from": "N9K-SW1",
                    "f_port": "Eth1/10",
                    "to": "Access-SW",
                    "t_port": "Gi1/0/1",
                    "f_int_data": {"status": "up", "speed": "10G", "duplex": "full", "desc": "vPC Member Eth1/10 to Access-SW"}
                },
                {
                    "from": "N9K-SW2",
                    "f_port": "Eth1/10",
                    "to": "Access-SW",
                    "t_port": "Gi1/0/2",
                    "f_int_data": {"status": "up", "speed": "10G", "duplex": "full", "desc": "vPC Member Eth1/10 to Access-SW"}
                }
            ],
            "edge_data": {
                "from": "VPC_Domain_10",
                "to": "Access-SW",
                "f_port": "Po10",
                "t_port": "Po10",
                "type": "vpc_shared",
                "label": "vPC 10 (2/2 Active)",
                "confidence": "High",
                "f_int_data": {"status": "up", "desc": "Logical vPC trunk to Access-SW"},
                "t_int_data": {"status": "up", "desc": "LACP trunk back to N9K cluster"},
                "bundled_links": [
                    {
                        "from": "N9K-SW1",
                        "f_port": "Eth1/10",
                        "to": "Access-SW",
                        "t_port": "Gi1/0/1",
                        "f_int_data": {"status": "up", "speed": "10G", "duplex": "full", "desc": "vPC Member Eth1/10 to Access-SW"}
                    },
                    {
                        "from": "N9K-SW2",
                        "f_port": "Eth1/10",
                        "to": "Access-SW",
                        "t_port": "Gi1/0/2",
                        "f_int_data": {"status": "up", "speed": "10G", "duplex": "full", "desc": "vPC Member Eth1/10 to Access-SW"}
                    }
                ]
            }
        },
        # Shared connection: Domain 10 to Database-SRV
        {
            "from": "VPC_Domain_10",
            "to": "Database-SRV",
            "label": "vPC 20 (2/2 Active)",
            "title": "vPC Domain 10 (Po20) ↔ Database-SRV (ens1f0, ens1f1)",
            "type": "vpc_shared",
            "color": {"color": "#0984e3"},
            "width": 8,
            "bundled_links": [
                {
                    "from": "N9K-SW1",
                    "f_port": "Eth1/20",
                    "to": "Database-SRV",
                    "t_port": "ens1f0",
                    "f_int_data": {"status": "up", "speed": "10G", "duplex": "full", "desc": "vPC Member Eth1/20 to Database-SRV"}
                },
                {
                    "from": "N9K-SW2",
                    "f_port": "Eth1/20",
                    "to": "Database-SRV",
                    "t_port": "ens1f1",
                    "f_int_data": {"status": "up", "speed": "10G", "duplex": "full", "desc": "vPC Member Eth1/20 to Database-SRV"}
                }
            ],
            "edge_data": {
                "from": "VPC_Domain_10",
                "to": "Database-SRV",
                "f_port": "Po20",
                "t_port": "Bond0",
                "type": "vpc_shared",
                "label": "vPC 20 (2/2 Active)",
                "confidence": "High",
                "f_int_data": {"status": "up", "desc": "Logical vPC trunk to Database-SRV"},
                "t_int_data": {"status": "up", "desc": "LACP bond to N9K cluster"},
                "bundled_links": [
                    {
                        "from": "N9K-SW1",
                        "f_port": "Eth1/20",
                        "to": "Database-SRV",
                        "t_port": "ens1f0",
                        "f_int_data": {"status": "up", "speed": "10G", "duplex": "full", "desc": "vPC Member Eth1/20 to Database-SRV"}
                    },
                    {
                        "from": "N9K-SW2",
                        "f_port": "Eth1/20",
                        "to": "Database-SRV",
                        "t_port": "ens1f1",
                        "f_int_data": {"status": "up", "speed": "10G", "duplex": "full", "desc": "vPC Member Eth1/20 to Database-SRV"}
                    }
                ]
            }
        }
    ]

    _assign_vpc_fixed_positions(nodes, edges)
    presentation = _build_html_presentation_payload(nodes, edges, "vpc")
    board_json = json.dumps(presentation.get("board_sections") or {})
    presentation_json = json.dumps(presentation)

    from utils.output_paths import get_demo_vpc_topology_path
    output_file = get_demo_vpc_topology_path()
    generate_topology_html(
        output_file, len(nodes), len(edges),
        json.dumps(nodes), json.dumps(edges), vis_js_content,
        map_mode="vpc",
        board_payload_json=board_json,
        presentation_json=presentation_json,
    )
    print(f"Demo created: {output_file}")

if __name__ == "__main__":
    create_v7_demo()
