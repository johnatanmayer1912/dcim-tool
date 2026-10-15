"""P0/P1 Swiss Tools roadmap — v7.0.47 regression tests."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest.mock import patch

import pytest

from modules.adapters import (
    _build_topology_report_header,
    _write_port_map_index_html,
)
from modules.plugins.interface_manager import (
    _determine_vendor,
    _im_vendor_or_error,
    run as im_run,
)
from utils.topo_map_shell import link_rows_from_edges


def test_g005_unknown_device_type_returns_none():
    assert _determine_vendor("arista") is None
    assert _determine_vendor("hp_comware") is None
    assert _determine_vendor("unknown") is None


def test_g005_im_vendor_or_error_blocks_arista():
    vendor, err = _im_vendor_or_error("arista_eos")
    assert vendor is None
    assert err and "Unsupported" in err


def test_g005_im_run_blocks_unsupported_device():
    device = {"host": "sw1", "device_type": "arista_eos"}
    creds = {"username": "u", "password": "p"}
    r = im_run(device, creds, {"operation": "discover"}, {}, None)
    assert r["status"] == "fail"
    assert "Unsupported" in (r.get("error") or "")


def test_topology_report_header_truncation_banner():
    html = _build_topology_report_header(
        map_mode="all",
        devices_requested=200,
        devices_truncated=True,
        devices_scanned=150,
        failed_hosts=["sw-bad"],
        parallel_workers=5,
        node_count=42,
        edge_count=88,
    )
    assert "Truncated" in html
    assert "failed" in html.lower()
    assert "Standard L2" in html


def test_link_inventory_vlan_column():
    edges = [{
        "from": "A", "to": "B",
        "f_port": "Gi1/0/1", "t_port": "Gi1/0/2",
        "protocol": "cdp", "vlan": "100",
    }]
    rows = link_rows_from_edges(edges)
    assert rows[0]["vlan"] == "100"


def test_port_map_index_html():
    with tempfile.TemporaryDirectory() as td:
        idx = os.path.join(td, "index.html")
        maps = [
            {"host": "SW1", "path": os.path.join(td, "sw1.html"), "basename": "sw1.html"},
            {"host": "SW2", "path": os.path.join(td, "sw2.html"), "basename": "sw2.html"},
        ]
        _write_port_map_index_html(idx, maps, td)
        content = open(idx, encoding="utf-8").read()
        assert "SW1" in content and "sw1.html" in content
        assert "2 switch" in content


class TestSwissToolsApi(unittest.TestCase):
    def setUp(self):
        from vlan_checker_web import app
        self.app = app
        self.client = app.test_client()
        app.config["TESTING"] = True

    def test_topology_failed_hosts_api(self):
        import vlan_checker_web as web
        web._last_topology = {
            "status": "complete",
            "failed_hosts": ["10.0.0.1"],
            "diag_folder": tempfile.gettempdir(),
        }
        r = self.client.get("/api/topology/failed-hosts")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["failed_hosts"], ["10.0.0.1"])

    def test_node_analyze_status_api(self):
        import vlan_checker_web as web
        web._last_node_analyze = {
            "status": "complete",
            "target_node": "CORE-01",
            "found_any": True,
            "port_hits": [{"switch": "SW1", "port": "Gi1/0/1", "status": "UP", "desc": "uplink"}],
        }
        r = self.client.get("/api/node-analyze/status")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["target_node"], "CORE-01")

    def test_port_map_status_api(self):
        import vlan_checker_web as web
        web._last_port_map = {
            "status": "complete",
            "html_basename": "index.html",
            "multi_device": True,
        }
        r = self.client.get("/api/port-map/status")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["multi_device"])
