"""vPC Engineering Board HTML generation tests."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.adapters import _build_html_presentation_payload, _assign_vpc_fixed_positions
from utils.report_formatter import generate_topology_html


class TestVpcBoardHtml(unittest.TestCase):
    def test_vpc_html_contains_board_and_payload(self):
        nodes = [
            {
                "id": "N9K-SW1",
                "label": "N9K-SW1",
                "vpc_domain_id": "10",
                "vpc_structured": {
                    "domain_id": "10",
                    "role": "primary",
                    "peer_status": "up",
                    "keepalive_status": "up",
                    "peer_link_po": "Po1",
                    "vpc_table": [
                        {"vpc_id": "10", "po": "Po10", "status": "up", "consistency": "success", "active_vlans": "1-100"},
                    ],
                },
                "port_channels": {"Po10": {"protocol": "LACP", "members": [{"intf": "Eth1/10"}]}},
                "vpc_details": {"_consistency_global": {"raw": "type-1 consistency: success"}},
            },
            {
                "id": "N9K-SW2",
                "label": "N9K-SW2",
                "vpc_domain_id": "10",
                "vpc_structured": {"domain_id": "10", "role": "secondary", "peer_status": "up",
                                   "keepalive_status": "up", "peer_link_po": "Po1", "vpc_table": []},
            },
            {
                "id": "VPC_Domain_10",
                "label": "vPC Domain 10",
                "vpc_domain_id": "10",
                "vpc_members": ["N9K-SW1", "N9K-SW2"],
                "vpc_structured": [
                    {"member": "N9K-SW1", "vpc_structured": {"peer_link_po": "Po1", "vpc_table": []}},
                    {"member": "N9K-SW2", "vpc_structured": {"peer_link_po": "Po1", "vpc_table": []}},
                ],
                "correlation": {"health_score": 100, "health_label": "HEALTHY"},
            },
        ]
        edges = [
            {
                "from": "N9K-SW1", "to": "HOST1", "type": "vpc_shared",
                "f_port": "Po10", "t_port": "Eth0",
                "bundled_links": [{"from": "N9K-SW1", "f_port": "Eth1/10", "to": "HOST1", "t_port": "Eth0"}],
            },
        ]
        _assign_vpc_fixed_positions(nodes, edges)
        pres = _build_html_presentation_payload(nodes, edges, "vpc")
        board = pres.get("board_sections") or {}
        out = os.path.join(os.path.dirname(__file__), "_vpc_board_test.html")
        try:
            generate_topology_html(
                out, len(nodes), len(edges),
                json.dumps(nodes), json.dumps(edges), "var vis = {};",
                map_mode="vpc",
                board_payload_json=json.dumps(board),
            )
            with open(out, encoding="utf-8") as hf:
                html = hf.read()
            self.assertIn("__VPC_BOARD__", html)
            self.assertIn("vpc-engineering-board", html)
            self.assertIn("Engineering Board", html)
            self.assertIn("Simplified Map", html)
            self.assertIn("Global Consistency Parameters", html)
            self.assertIn("peer_link_po", html.lower() + "po1" if "po1" in html.lower() else "Po1")
        finally:
            if os.path.isfile(out):
                os.remove(out)


if __name__ == "__main__":
    unittest.main()
