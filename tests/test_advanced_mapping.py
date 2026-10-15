import pytest
from modules.discovery.advanced_mapper import AdvancedMapper

def test_l2_map_generation():
    mapper = AdvancedMapper()
    devices = [
        {"ip": "10.0.0.1", "hostname": "switch-a", "neighbors": [{"ip": "10.0.0.2", "local_port": "g1/0", "remote_port": "g1/1"}]}
    ]
    result = mapper.build_l2_map(devices)
    assert len(result["nodes"]) == 2
    # After deduplication enhancement, hostname is used as primary key
    assert result["nodes"][0]["id"] == "switch-a"
    assert len(result["edges"]) == 1
    assert result["edges"][0]["from"] == "switch-a"
    assert result["edges"][0]["to"] == "10.0.0.2"

def test_l3_map_generation():
    mapper = AdvancedMapper()
    devices = [
        {"ip": "10.0.0.1", "hostname": "router-a", "routes": [
            {"network": "192.168.1.0/24", "protocol": "C", "next_hop": "0.0.0.0", "interface": "Vlan10"},
        ]}
    ]
    result = mapper.build_l3_map(devices)
    assert len(result["nodes"]) >= 2
    assert any(n["id"] == "router-a" for n in result["nodes"])
    assert any("192.168.1.0/24" in str(n.get("id", "")) for n in result["nodes"])
    assert len(result["edges"]) >= 1

def test_flow_map_generation():
    mapper = AdvancedMapper()
    devices = [{
        "ip": "10.0.0.1",
        "hostname": "gw-1",
        "routes": [
            {"network": "0.0.0.0/0", "protocol": "S", "next_hop": "203.0.113.1"},
            {"network": "192.168.1.0/24", "protocol": "C", "interface": "Vlan10"},
        ],
    }]
    result = mapper.build_flow_map(devices)
    assert len(result["nodes"]) >= 2
    assert len(result["edges"]) >= 1
