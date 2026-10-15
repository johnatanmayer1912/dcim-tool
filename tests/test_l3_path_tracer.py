# ============================================================================
# tests/test_l3_path_tracer.py
# ============================================================================
# PURPOSE:
#   Comprehensive unit and integration test suite for L3PathTracer and
#   POST /api/l3/trace-path endpoint.
# ============================================================================

import ipaddress
import json
import pytest
from modules.routing_analyzer.path_tracer import L3PathTracer


@pytest.fixture
def sample_topology_data():
    devices_meta = {
        "access-sw01": {
            "management_ip": "10.0.0.1",
            "local_ips": ["10.10.1.1/30", "192.168.10.1/24"],
            "interfaces": {
                "Vlan10": {"ip": "192.168.10.1/24"},
                "GigabitEthernet0/1": {"ip": "10.10.1.1/30"},
            },
        },
        "core-rtr01": {
            "management_ip": "10.0.0.2",
            "local_ips": ["10.10.1.2/30", "10.10.2.1/30"],
            "interfaces": {
                "GigabitEthernet0/1": {"ip": "10.10.1.2/30"},
                "GigabitEthernet0/2": {"ip": "10.10.2.1/30"},
            },
        },
        "dist-sw01": {
            "management_ip": "10.0.0.3",
            "local_ips": ["10.10.2.2/30", "192.168.20.1/24"],
            "interfaces": {
                "GigabitEthernet0/2": {"ip": "10.10.2.2/30"},
                "Vlan20": {"ip": "192.168.20.1/24"},
            },
        },
    }

    all_routes = [
        # access-sw01 routes
        {
            "device_id": "access-sw01",
            "network": "192.168.10.0/24",
            "protocol": "connected",
            "interface": "Vlan10",
            "next_hop": None,
        },
        {
            "device_id": "access-sw01",
            "network": "10.10.1.0/30",
            "protocol": "connected",
            "interface": "GigabitEthernet0/1",
            "next_hop": None,
        },
        {
            "device_id": "access-sw01",
            "network": "0.0.0.0/0",
            "protocol": "static",
            "interface": "GigabitEthernet0/1",
            "next_hop": "10.10.1.2",
        },
        # core-rtr01 routes
        {
            "device_id": "core-rtr01",
            "network": "10.10.1.0/30",
            "protocol": "connected",
            "interface": "GigabitEthernet0/1",
            "next_hop": None,
        },
        {
            "device_id": "core-rtr01",
            "network": "10.10.2.0/30",
            "protocol": "connected",
            "interface": "GigabitEthernet0/2",
            "next_hop": None,
        },
        {
            "device_id": "core-rtr01",
            "network": "192.168.10.0/24",
            "protocol": "ospf",
            "interface": "GigabitEthernet0/1",
            "next_hop": "10.10.1.1",
        },
        {
            "device_id": "core-rtr01",
            "network": "192.168.20.0/24",
            "protocol": "ospf",
            "interface": "GigabitEthernet0/2",
            "next_hop": "10.10.2.2",
        },
        # dist-sw01 routes
        {
            "device_id": "dist-sw01",
            "network": "10.10.2.0/30",
            "protocol": "connected",
            "interface": "GigabitEthernet0/2",
            "next_hop": None,
        },
        {
            "device_id": "dist-sw01",
            "network": "192.168.20.0/24",
            "protocol": "connected",
            "interface": "Vlan20",
            "next_hop": None,
        },
        {
            "device_id": "dist-sw01",
            "network": "0.0.0.0/0",
            "protocol": "static",
            "interface": "GigabitEthernet0/2",
            "next_hop": "10.10.2.1",
        },
    ]

    return devices_meta, all_routes


def test_path_tracer_initialization(sample_topology_data):
    devices_meta, all_routes = sample_topology_data
    tracer = L3PathTracer(all_routes, devices_meta)
    
    assert "access-sw01" in tracer._routes_by_device
    assert "core-rtr01" in tracer._routes_by_device
    assert "dist-sw01" in tracer._routes_by_device
    assert len(tracer._routes_by_device["access-sw01"]) == 3
    assert tracer._ip_to_device.get("10.10.1.1")[0] == "access-sw01"


def test_ingress_resolution(sample_topology_data):
    devices_meta, all_routes = sample_topology_data
    tracer = L3PathTracer(all_routes, devices_meta)

    # Ingress in subnet 192.168.10.0/24 -> access-sw01
    ingress = tracer._find_ingress_device(ipaddress.ip_address("192.168.10.55"))
    assert ingress is not None
    dev_id, iface, subnet = ingress
    assert dev_id == "access-sw01"
    assert iface == "Vlan10"

    # Ingress in subnet 192.168.20.0/24 -> dist-sw01
    ingress2 = tracer._find_ingress_device(ipaddress.ip_address("192.168.20.99"))
    assert ingress2 is not None
    assert ingress2[0] == "dist-sw01"
    assert ingress2[1] == "Vlan20"


def test_longest_prefix_match():
    routes = [
        {"device_id": "dev1", "network": "0.0.0.0/0", "protocol": "static", "next_hop": "1.1.1.1"},
        {"device_id": "dev1", "network": "10.0.0.0/8", "protocol": "ospf", "next_hop": "2.2.2.2"},
        {"device_id": "dev1", "network": "10.20.0.0/16", "protocol": "ospf", "next_hop": "3.3.3.3"},
        {"device_id": "dev1", "network": "10.20.30.0/24", "protocol": "connected", "next_hop": None, "interface": "Gig1"},
        {"device_id": "dev1", "network": "10.20.30.40/32", "protocol": "host", "next_hop": "5.5.5.5"},
    ]
    tracer = L3PathTracer(routes, {})
    
    # Matches /32 exactly
    m1 = tracer._longest_prefix_match("dev1", ipaddress.ip_address("10.20.30.40"))
    assert m1 is not None and m1["network"] == "10.20.30.40/32"

    # Matches /24
    m2 = tracer._longest_prefix_match("dev1", ipaddress.ip_address("10.20.30.99"))
    assert m2 is not None and m2["network"] == "10.20.30.0/24"

    # Matches /16
    m3 = tracer._longest_prefix_match("dev1", ipaddress.ip_address("10.20.50.1"))
    assert m3 is not None and m3["network"] == "10.20.0.0/16"

    # Matches /8
    m4 = tracer._longest_prefix_match("dev1", ipaddress.ip_address("10.1.1.1"))
    assert m4 is not None and m4["network"] == "10.0.0.0/8"

    # Matches default
    m5 = tracer._longest_prefix_match("dev1", ipaddress.ip_address("8.8.8.8"))
    assert m5 is not None and m5["network"] == "0.0.0.0/0"


def test_end_to_end_forwarding_trace(sample_topology_data):
    devices_meta, all_routes = sample_topology_data
    tracer = L3PathTracer(all_routes, devices_meta)

    res = tracer.trace_path(
        source_ip_str="192.168.10.50",
        dest_ip_str="192.168.20.100",
    )

    assert res["complete"] is True
    assert res["status"] in ("success", "complete")
    assert res["ingress_device"] == "access-sw01"
    assert res["egress_device"] == "dist-sw01"

    # Hops should be access-sw01 -> core-rtr01 -> dist-sw01
    hops = res["hops"]
    assert len(hops) == 4  # ingress + forward to core + forward to dist + delivered
    assert hops[0]["device"] == "access-sw01"
    assert hops[0]["action"] == "ingress"
    assert hops[1]["device"] == "access-sw01"
    assert hops[1]["next_hop"] == "10.10.1.2"
    assert hops[2]["device"] == "core-rtr01"
    assert hops[2]["next_hop"] == "10.10.2.2"
    assert hops[3]["device"] == "dist-sw01"
    assert hops[3]["action"] == "delivered"

    # Flow path IDs
    assert res["path_nodes"] == ["access-sw01", "core-rtr01", "dist-sw01"]
    assert "access-sw01->core-rtr01" in res["path_edges"]
    assert "core-rtr01->dist-sw01" in res["path_edges"]


def test_routing_loop_detection():
    devices_meta = {
        "r1": {"local_ips": ["10.0.0.1/30"], "management_ip": "10.0.0.1"},
        "r2": {"local_ips": ["10.0.0.2/30"], "management_ip": "10.0.0.2"},
    }
    all_routes = [
        # r1 points to r2 for 192.168.1.0/24
        {
            "device_id": "r1",
            "network": "192.168.1.0/24",
            "protocol": "static",
            "next_hop": "10.0.0.2",
            "interface": "Gi0/1",
        },
        {
            "device_id": "r1",
            "network": "10.0.0.0/30",
            "protocol": "connected",
            "interface": "Gi0/1",
        },
        # r2 points back to r1 for 192.168.1.0/24
        {
            "device_id": "r2",
            "network": "192.168.1.0/24",
            "protocol": "static",
            "next_hop": "10.0.0.1",
            "interface": "Gi0/2",
        },
        {
            "device_id": "r2",
            "network": "10.0.0.0/30",
            "protocol": "connected",
            "interface": "Gi0/2",
        },
    ]

    tracer = L3PathTracer(all_routes, devices_meta)
    res = tracer.trace_path("10.0.0.1", "192.168.1.100")

    assert res["complete"] is False
    assert res["status"] == "loop_detected"
    assert "Routing loop detected" in res["summary"]


def test_api_trace_path_endpoint(sample_topology_data):
    from vlan_checker_web import app
    app.config["TESTING"] = True
    client = app.test_client()

    # Missing parameters
    resp = client.post("/api/l3/trace-path", json={})
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert "error" in data

    # Invalid IPs
    resp2 = client.post("/api/l3/trace-path", json={"source_ip": "not-an-ip", "destination_ip": "10.1.1.1"})
    assert resp2.status_code == 400
    data2 = json.loads(resp2.data)
    assert "Invalid IP address" in data2.get("error", "")

    # Valid trace with embedded routes
    devices_meta, all_routes = sample_topology_data
    resp3 = client.post("/api/l3/trace-path", json={
        "source_ip": "192.168.10.50",
        "destination_ip": "192.168.20.100",
        "all_routes": all_routes,
        "devices": devices_meta,
    })
    assert resp3.status_code == 200
    data3 = json.loads(resp3.data)
    assert data3.get("complete") is True
    assert data3.get("ingress_device") == "access-sw01"
    assert data3.get("egress_device") == "dist-sw01"
