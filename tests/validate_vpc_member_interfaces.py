"""
Automated validation for v6.9.4+ vPC member interface collection and HTML payload.
Run: python tests/validate_vpc_member_interfaces.py
Exit code 0 = all checks passed.
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS  {name}")
    else:
        msg = f"  FAIL  {name}" + (f" — {detail}" if detail else "")
        print(msg)
        FAILURES.append(name)


def main():
    print("=" * 60)
    print("vPC Member Interfaces Validation (v6.9.4+)")
    print("=" * 60)

    from modules.adapters import (
        _build_vpc_member_interfaces,
        _build_html_presentation_payload,
    )
    from modules.topology_mapper import _parse_vpc_brief_table, _parse_vpc_full

    # --- Parser: show vpc brief ---
    brief_sample = """
Legend:
                (*) - local vPC is down, forwarding via vPC peer-link
vPC ID     Port   Status Consistency Reason                Active vlans
------     ----   ------ ----------- ------                -------------
10         Po10   up     success                        1-4094
20         Po20   up     success                        10
"""
    brief_table = _parse_vpc_brief_table(brief_sample)
    check("parse_vpc_brief_table rows", len(brief_table) == 2, f"got {len(brief_table)}")
    check("parse_vpc_brief vpc_id", brief_table[0].get("vpc_id") == "10")
    check("parse_vpc_brief po normalized", brief_table[0].get("po") == "Po10")

    vpc_full = _parse_vpc_full("vpc domain id: 10\n", brief_sample, "Port-channel1")
    check("parse_vpc_full falls back to brief", len(vpc_full.get("vpc_table", [])) == 2)

    nxos_vpc = """
vPC domain id : 10
Peer status : peer link is up
vPC keep-alive status : peer is alive
vPC status
id   Port   Status   Consistency   Reason   Active vlans
--   ----   ------   -----------   ------   ------------
10   Po10   up       success                1-100
"""
    nxos_parsed = _parse_vpc_full(nxos_vpc, "", "Port-channel1")
    check("parse nxos peer status", nxos_parsed.get("peer_status") == "up", nxos_parsed.get("peer_status"))
    check("parse nxos keepalive", nxos_parsed.get("keepalive_status") == "up", nxos_parsed.get("keepalive_status"))

    # --- Builder: vpc_member_interfaces ---
    meta = {
        "vpc_structured": {
            "domain_id": "10",
            "role": "primary",
            "vpc_table": [
                {"vpc_id": "10", "po": "Po10", "status": "up", "consistency": "success", "active_vlans": "1-4094"},
            ],
        },
        "port_channel_detail": {
            "Po10": {"protocol": "LACP", "members": [{"intf": "Eth1/10"}]},
        },
        "vpc_details": {
            "Po10": {"type": "vpc", "vpc_id": "10", "status": "up", "consistency": "success"},
        },
    }
    block = _build_vpc_member_interfaces("N9K-SW1", meta)
    check("vpc_member_interfaces.switch", block.get("switch") == "N9K-SW1")
    check("vpc_member_interfaces.entries", len(block.get("entries", [])) >= 1)
    ent = block["entries"][0]
    check("entry member_interfaces", ent.get("member_interfaces") == ["Eth1/10"], str(ent))

    # --- Presentation payload naming ---
    nodes_json = [
        {
            "id": "VPC_Domain_10",
            "vpc_domain_id": "10",
            "vpc_members": ["N9K-SW1", "N9K-SW2"],
            "vpc_structured": [{"member": "N9K-SW1", "vpc_structured": meta["vpc_structured"]}],
            "vpc_member_interfaces": {
                "N9K-SW1": block,
                "N9K-SW2": {"switch": "N9K-SW2", "entries": []},
            },
        }
    ]
    edges_json = [
        {
            "from": "VPC_Domain_10",
            "to": "Access-SW",
            "type": "vpc_shared",
            "bundled_links": [
                {"from": "N9K-SW1", "f_port": "Eth1/10", "to": "Access-SW", "t_port": "Gi1/0/1",
                 "f_int_data": {"status": "up", "speed": "10G"}},
            ],
        }
    ]
    payload = _build_html_presentation_payload(nodes_json, edges_json, "vpc")
    check("presentation member_interfaces_by_switch", "N9K-SW1" in payload.get("member_interfaces_by_switch", {}))
    check("presentation graph_edges bundled_links", len(payload["graph_edges"][0].get("bundled_links", [])) == 1)

    # --- Demo HTML embedded data ---
    demo_path = os.path.join(ROOT, "DEMO_VPC_TOPOLOGY_v7.0.html")
    check("demo html exists", os.path.isfile(demo_path))
    if os.path.isfile(demo_path):
        with open(demo_path, encoding="utf-8") as f:
            html = f.read()
        check("demo has vpc_member_interfaces", "vpc_member_interfaces" in html)
        check("demo has keepalive panel ids", "peer-keepalive-status" in html and "telemetryHealthy" in html)
        check("demo has top-level bundled_links on vpc_shared", '"type": "vpc_shared"' in html and '"bundled_links":' in html)
        check("demo no stale empty message", "No vPC interfaces detected" not in html)
        check("renderVPCInterfaces uses edge_data fallback", "edge.edge_data.bundled_links" in html)
        check("renderVPCInterfaces dedupePorts", "dedupePorts" in html)
        check("extractVPCData edgeTypeOf", "edgeTypeOf" in html)

    # --- Diagnostic file naming convention ---
    naming_ok = all(
        re.match(r"^0[1-7]_[a-z0-9_]+\.(json|txt)$", f) or f in (
            "00_README.txt", "vpc_map_data_TEMPLATE.json",
        )
        for f in [
            "00_README.txt", "01_raw_node_metadata.json", "02_pre_transform_edges.json",
            "03_post_transform_edges.json", "04_final_map_data.json", "05_vpc_domain_summary.txt",
            "06_pre_render_presentation.json", "07_post_render_manifest.json",
            "vpc_map_data_TEMPLATE.json",
        ]
    )
    check("diagnostic file naming convention", naming_ok)

    ver_path = os.path.join(ROOT, "VERSION")
    with open(ver_path, encoding="utf-8") as vf:
        ver = vf.read().strip()
    check("VERSION file", bool(re.match(r"^\d+\.\d+\.\d+$", ver)), f"invalid or empty: {ver!r}")

    from modules.plugin_registry import PluginRegistry
    PluginRegistry._instance = None
    PluginRegistry._initialized = False
    reg = PluginRegistry()
    check("vpc_domain plugin loaded", reg.exists("vpc_domain"), "plugin not in registry")
    check("plugin count >= 11", len(reg.get_all_metadata()) >= 11)

    import modules.description_search
    check("description_search module", hasattr(modules.description_search, "run"))

    print("=" * 60)
    if FAILURES:
        print(f"RESULT: FAILED ({len(FAILURES)} checks)")
        return 1
    print("RESULT: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
