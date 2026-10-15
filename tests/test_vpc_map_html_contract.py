"""VPC Command Center HTML contract (v7.0.4)."""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.adapters import (
    _assign_vpc_fixed_positions,
    _build_html_presentation_payload,
    _ensure_vpc_nodes_positioned,
)
from utils.report_formatter import generate_topology_html


class TestVpcMapHtmlContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        vis_path = os.path.join("modules", "web", "vis-network.min.js")
        cls.vis_js = ""
        if os.path.exists(vis_path):
            with open(vis_path, encoding="utf-8") as f:
                cls.vis_js = f.read()

        nodes = [
            {
                "id": "N9K-SW1",
                "label": "N9K-SW1",
                "shape": "box",
                "role": "vpc_primary",
                "group": "vpc_primary",
                "vpc_domain_id": "10",
                "x": 0,
                "y": 0,
            },
            {
                "id": "N9K-SW2",
                "label": "N9K-SW2",
                "shape": "box",
                "role": "vpc_secondary",
                "group": "vpc_secondary",
                "vpc_domain_id": "10",
                "x": 200,
                "y": 0,
            },
        ]
        edges = [
            {
                "from": "N9K-SW1",
                "to": "N9K-SW2",
                "type": "vpc-peer-link",
                "label": "Peer-Link",
            }
        ]
        _assign_vpc_fixed_positions(nodes, edges)
        presentation = _build_html_presentation_payload(nodes, edges, "vpc")
        cls.presentation = presentation
        cls.board_json = json.dumps(presentation.get("board_sections") or {})
        cls.presentation_json = json.dumps(presentation)
        cls.nodes_json = json.dumps(nodes)
        cls.edges_json = json.dumps(edges)

        cls.tmp = tempfile.mkdtemp()
        cls.html_path = os.path.join(cls.tmp, "vpc_contract.html")
        generate_topology_html(
            cls.html_path,
            len(nodes),
            len(edges),
            cls.nodes_json,
            cls.edges_json,
            cls.vis_js,
            map_mode="vpc",
            board_payload_json=cls.board_json,
            presentation_json=cls.presentation_json,
        )
        with open(cls.html_path, encoding="utf-8") as f:
            cls.html = f.read()

    def test_presentation_and_board_embedded(self):
        self.assertIn("__VPC_PRESENTATION__", self.html)
        self.assertIn("__VPC_BOARD__", self.html)
        self.assertIn("vpc_domains", self.html)

    def test_light_theme_and_command_center(self):
        self.assertIn("vpc-command-center", self.html)
        self.assertIn("vpc-split-overview", self.html)
        self.assertIn("vpc-cc-tabs", self.html)
        self.assertIn("vpcBootMap", self.html)
        self.assertIn("vpcCommandCenterInit", self.html)
        self.assertNotIn('id="vpc-view-tabs"', self.html)

    def test_map_not_hidden_by_default(self):
        self.assertNotRegex(
            self.html,
            r'id="mynetwork"\s+class="[^"]*map-tab-hidden',
        )
        self.assertIn('id="mynetwork" class="vpc-map-pane"', self.html)

    def test_physics_off_and_deferred_init(self):
        self.assertIn("physics: { enabled: false }", self.html)
        self.assertIn("createTopologyNetwork", self.html)
        self.assertIn("improvedLayout: false", self.html)

    def test_all_nodes_have_fixed_xy(self):
        nodes = json.loads(self.nodes_json)
        for n in nodes:
            if n.get('hidden'):
                continue
            self.assertIn('x', n, msg=n.get('id'))
            self.assertIn('y', n, msg=n.get('id'))

    def test_no_domain_fallback_positions(self):
        nodes = [
            {'id': 'SW-A', 'label': 'SW-A', 'shape': 'box'},
            {'id': 'SW-B', 'label': 'SW-B', 'shape': 'box'},
            {'id': 'SW-C', 'label': 'SW-C', 'shape': 'box'},
        ]
        edges = [
            {'from': 'SW-A', 'to': 'SW-B', 'type': 'cdp'},
            {'from': 'SW-B', 'to': 'SW-C', 'type': 'cdp'},
        ]
        _assign_vpc_fixed_positions(nodes, edges)
        _ensure_vpc_nodes_positioned(nodes, edges)
        for n in nodes:
            self.assertIsNotNone(n.get('x'))
            self.assertIsNotNone(n.get('y'))

    def test_link_inventory_readable_on_light_theme(self):
        self.assertIn('body.vpc-command-center #topo-link-inventory', self.html)
        self.assertIn('color: #1e293b !important', self.html)
        self.assertIn('topo-trust-pill', self.html)
        self.assertIn('topo-inv-hint', self.html)
        self.assertNotIn('background:#0f172a;min-height:200px', self.html)

    def test_map_hint_and_legend(self):
        self.assertIn('vpc-map-hint', self.html)
        self.assertIn('How to read this map', self.html)
        self.assertIn('Fit view', self.html)

        self.assertIn('clamp(420px', self.html)
        self.assertRegex(
            self.html,
            r'#mynetwork\.vpc-map-pane\s*\{[^}]*max-height:\s*680px',
        )
        self.assertNotRegex(
            self.html,
            r'#mynetwork\.vpc-map-pane\s*\{[^}]*height:\s*100%',
        )

    def test_vis_embedded_not_cdn_only(self):
        if self.vis_js:
            self.assertNotIn("unpkg.com/vis-network", self.html.lower())

    def test_demo_generation_smoke(self):
        r = subprocess.run(
            [sys.executable, "create_demo_map_v7.py"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )
        self.assertEqual(r.returncode, 0, r.stderr or r.stdout)
        demo = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "DEMO_VPC_TOPOLOGY_v7.0.4.html",
        )
        self.assertTrue(os.path.isfile(demo))
        with open(demo, encoding="utf-8") as f:
            body = f.read()
        self.assertIn("vpc-light", body)
        self.assertIn("__VPC_PRESENTATION__", body)
        m = re.search(r'var nodes_raw\s*=\s*(\[.*?\]);', body, re.S)
        if m:
            demo_nodes = json.loads(m.group(1))
            for n in demo_nodes:
                if n.get('hidden'):
                    continue
                self.assertIn('x', n)
                self.assertIn('y', n)


class TestJunosLldpLocalPort(unittest.TestCase):
    def test_junos_local_interface(self):
        block = """
Local Interface    : ge-0/0/1
Parent Interface   : ge-0/0/1
Neighbor interface : ge-0/0/2
"""
        m = re.search(r"Local Interface\s*:\s*(\S+)", block, re.I)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "ge-0/0/1")


if __name__ == "__main__":
    unittest.main()
