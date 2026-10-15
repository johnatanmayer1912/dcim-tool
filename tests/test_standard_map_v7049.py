"""Standard Map v7.0.49+ — NOC/NetEng shell, Cisco edge cases."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.adapters import (
    _detect_device_role,
    _finalize_standard_map_edges,
    _topology_edge_link_key,
)
from utils import standard_map_shell as sms
from utils.report_formatter import generate_topology_html
from utils.topo_map_shell import link_rows_from_edges

def _norm_int(n):
    return (n.replace("GigabitEthernet", "Gi")
            .replace("Port-channel", "Po").strip())


class TestStandardMapLinkRows(unittest.TestCase):
    """Cisco L2 edge cases for connection index."""

    def test_cisco_trunk_uplink_row(self):
        edges = [{
            "from": "CORE-01", "to": "DIST-N1",
            "f_port": "Te1/0/1", "t_port": "Te1/1/1",
            "type": "standard",
            "confidence": "High",
            "f_int_data": {"vlan": "trunk", "speed": "10G", "status": "up", "desc": "UPLINK-DIST"},
            "t_int_data": {"vlan": "trunk", "status": "up"},
            "peer_info": {"platform": "Cisco C9300-48P", "version": "17.9"},
        }]
        nodes = [
            {"id": "CORE-01", "role": "core"},
            {"id": "DIST-N1", "role": "distribution"},
        ]
        rows = link_rows_from_edges(edges, nodes)
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["from"], "CORE-01")
        self.assertEqual(r["local_port"], "Te1/0/1")
        self.assertEqual(r["vlan"], "trunk")
        self.assertEqual(r["speed"], "10G")
        self.assertEqual(r["status"], "up")
        self.assertEqual(r["local_role"], "core")
        self.assertEqual(r["remote_role"], "distribution")
        self.assertIn("C9300", r["remote_platform"])

    def test_nexus_port_channel_vpc(self):
        edges = [{
            "from": "N7K-1", "to": "N7K-2",
            "f_port": "Po1", "t_port": "Po1",
            "type": "vpc-peer-link",
            "confidence": "High",
            "f_int_data": {"status": "up", "speed": "40G", "vlan": ""},
            "peer_info": {"platform": "Nexus7000"},
        }]
        rows = link_rows_from_edges(edges)
        self.assertEqual(rows[0]["link_type"], "vpc-peer-link")
        self.assertEqual(rows[0]["speed"], "40G")

    def test_asymmetric_cdp_unidirectional(self):
        edges = [{
            "from": "DIST-S1", "to": "SW-ACC-03",
            "f_port": "Gi1/0/48", "t_port": "Gi1/0/1",
            "type": "asymmetric",
            "confidence": "Medium",
            "f_int_data": {"status": "up", "vlan": "110"},
        }]
        rows = link_rows_from_edges(edges)
        self.assertEqual(rows[0]["confidence"], "Medium")
        self.assertEqual(rows[0]["protocol"], "CDP (unidir)")

    def test_access_vlan_and_description(self):
        edges = [{
            "from": "SW-ACC-01", "to": "AP-FLOOR2-03",
            "f_port": "Gi1/0/24", "t_port": "eth0",
            "type": "standard",
            "f_int_data": {"vlan": "120", "status": "up", "desc": "AP-FLOOR2", "speed": "1G"},
        }]
        rows = link_rows_from_edges(edges)
        self.assertEqual(rows[0]["vlan"], "120")
        self.assertEqual(rows[0]["description"], "AP-FLOOR2")

    def test_vis_edge_data_enrichment(self):
        vis_edges = [{
            "from": "A", "to": "B", "f_port": "Gi1/0/1", "t_port": "Gi1/0/2",
            "type": "port-channel",
            "edge_data": {
                "from": "A", "to": "B", "f_port": "Gi1/0/1", "t_port": "Gi1/0/2",
                "type": "port-channel", "confidence": "High",
                "f_int_data": {"speed": "20G", "vlan": "trunk", "status": "up"},
            },
        }]
        rows = sms.enrich_link_rows_from_vis_edges(vis_edges)
        self.assertEqual(rows[0]["link_type"], "port-channel")
        self.assertEqual(rows[0]["speed"], "20G")

    def test_parallel_link_dedup_key_cisco_ports(self):
        k1 = _topology_edge_link_key("SW1", "Gi1/0/1", "SW2", "Gi1/0/2", _norm_int)
        k2 = _topology_edge_link_key("SW1", "Gi1/0/3", "SW2", "Gi1/0/4", _norm_int)
        self.assertNotEqual(k1, k2)

    def test_role_detection_cisco_hostnames(self):
        role, _ = _detect_device_role("CORE-SW-01", 5, {})
        self.assertEqual(role, "core")
        role, _ = _detect_device_role("DIST-N1", 3, {})
        self.assertEqual(role, "distribution")
        role, _ = _detect_device_role("SW-ACC-FLOOR3", 1, {"Gi1/0/1": {}})
        self.assertEqual(role, "access")


class TestStandardMapPeerLinkFinalize(unittest.TestCase):
    """v7.0.51 peer-link upgrade and synthesis."""

    def _log(self, msg):
        pass

    def test_upgrade_existing_edge_to_peer_link(self):
        edges = [{
            'from': 'N7K-1', 'to': 'N7K-2',
            'f_port': 'Po1', 't_port': 'Po1',
            'type': 'port-channel', 'label': 'Po1',
        }]
        meta = {
            'N7K-1': {
                'vpc_domain_id': '100',
                'vpc_structured': {'peer_link_po': 'Po1'},
                'vpc_details': {'Po1': {'type': 'peer-link'}},
            },
            'N7K-2': {'vpc_domain_id': '100'},
        }
        out = _finalize_standard_map_edges(edges, meta, _norm_int, self._log)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]['type'], 'vpc-peer-link')
        self.assertTrue(out[0].get('is_vpc_peer_link'))

    def test_synthesize_missing_peer_link_two_member_domain(self):
        edges = [{
            'from': 'N7K-1', 'to': 'SW-01',
            'f_port': 'Eth1/1', 't_port': 'Gi1/0/1',
            'type': 'standard',
        }]
        meta = {
            'N7K-1': {'vpc_domain_id': '200', 'vpc_structured': {'peer_link_po': 'Po10'}},
            'N7K-2': {'vpc_domain_id': '200'},
        }
        out = _finalize_standard_map_edges(edges, meta, _norm_int, self._log)
        peer = [e for e in out if e.get('type') == 'vpc-peer-link']
        self.assertEqual(len(peer), 1)
        self.assertEqual(set([peer[0]['from'], peer[0]['to']]), {'N7K-1', 'N7K-2'})
        self.assertEqual(peer[0]['f_port'], 'Po10')


class TestStandardMapHtmlContract(unittest.TestCase):
    """Exported HTML must include split-pane NOC shell."""

    def test_standard_map_html_contract(self):
        nodes = [
            {"id": "CORE-01", "label": "CORE-01", "role": "core", "level": 0,
             "shape": "box", "color": {"background": "#c0392b", "border": "#333"},
             "font": {"color": "#fff"}},
            {"id": "DIST-N1", "label": "DIST-N1", "role": "distribution", "level": 1,
             "shape": "box", "color": {"background": "#e67e22", "border": "#333"},
             "font": {"color": "#fff"}},
        ]
        edges = [{
            "id": "e0", "from": "CORE-01", "to": "DIST-N1",
            "f_port": "Te1/0/1", "t_port": "Te1/1/1", "label": "",
            "map_label": "Te1/0/1 ↔ Te1/1/1",
            "type": "standard",
            "edge_data": {
                "from": "CORE-01", "to": "DIST-N1",
                "f_port": "Te1/0/1", "t_port": "Te1/1/1",
                "type": "standard", "confidence": "High",
                "f_int_data": {"vlan": "trunk", "speed": "10G", "status": "up"},
            },
            "color": "#607d8b", "width": 2,
        }]
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tf:
            path = tf.name
        try:
            generate_topology_html(
                path, 2, 1,
                json.dumps(nodes), json.dumps(edges),
                "/* vis stub */",
                map_mode="all",
                briefing_extra={"failed_hosts": 1, "truncated": False},
            )
            html = open(path, encoding="utf-8").read()
            self.assertIn("nst-standard-split", html)
            self.assertIn("nst-standard-map", html)
            self.assertIn("nst-top-chrome", html)
            self.assertIn("nst-legend-pill", html)
            self.assertIn("Show port labels", html)
            self.assertIn("nstTogglePortLabels", html)
            self.assertNotIn('<div class="legend">', html)
            self.assertIn("nstBootStandardMap", html)
            self.assertIn("nst-conn-panel", html)
            self.assertIn("nst-map-style-btn", html)
            self.assertIn("nstSetMapStyle", html)
            self.assertIn("__NST_LINKS__", html)
            self.assertIn("Tier", html)
            self.assertIn("Focus", html)
            self.assertIn("Schematic", html)
            self.assertNotIn("Matrix", html)
            self.assertNotIn("tab-btn-links", html)
        finally:
            os.unlink(path)

    def test_briefing_stats(self):
        edges = [{"type": "port-channel"}, {"type": "asymmetric", "edge_data": {"confidence": "Medium"}}]
        nodes = [{"role": "core"}, {"role": "access"}]
        b = sms.build_briefing_stats(edges, nodes, {"failed_hosts": 2, "truncated": True})
        self.assertEqual(b["po_vpc"], 1)
        self.assertEqual(b["asymmetric"], 1)
        self.assertEqual(b["failed_hosts"], 2)
        self.assertTrue(b["truncated"])


if __name__ == "__main__":
    unittest.main()
