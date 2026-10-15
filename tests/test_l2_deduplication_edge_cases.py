"""
Comprehensive edge case tests for L2 map deduplication
"""
import pytest
from modules.discovery.advanced_mapper import AdvancedMapper


class TestL2DeduplicationEdgeCases:
    """Test L2 map deduplication with various edge cases"""
    
    @pytest.fixture
    def mapper(self):
        return AdvancedMapper()
    
    def test_basic_deduplication_by_hostname(self, mapper):
        """Test basic deduplication using hostname as primary key"""
        devices = [
            {"ip": "10.0.0.1", "hostname": "switch-a", "neighbors": [{"ip": "10.0.0.2", "local_port": "g1/0", "remote_port": "g1/1"}]},
            {"ip": "10.0.0.1", "hostname": "switch-a", "neighbors": [{"ip": "10.0.0.3", "local_port": "g1/1", "remote_port": "g1/0"}]},
        ]
        result = mapper.build_l2_map(devices)
        
        # Should deduplicate to single node for switch-a, plus neighbors
        assert len(result["nodes"]) == 3  # switch-a, 10.0.0.2, 10.0.0.3
        assert any(n["id"] == "switch-a" for n in result["nodes"])
    
    def test_deduplication_same_device_different_ips(self, mapper):
        """Test deduplication when same device appears with different IPs"""
        devices = [
            {"ip": "10.0.0.1", "hostname": "switch-a", "neighbors": []},
            {"ip": "10.0.0.2", "hostname": "switch-a", "neighbors": []},
        ]
        result = mapper.build_l2_map(devices)
        
        # Should deduplicate to single node by hostname
        assert len(result["nodes"]) == 1
        assert result["nodes"][0]["id"] == "switch-a"
    
    def test_deduplication_ip_fallback_no_hostname(self, mapper):
        """Test IP fallback when hostname equals IP"""
        devices = [
            {"ip": "10.0.0.1", "hostname": "10.0.0.1", "neighbors": [{"ip": "10.0.0.2", "local_port": "g1/0", "remote_port": "g1/1"}]},
        ]
        result = mapper.build_l2_map(devices)
        
        # Should use IP as node ID when hostname equals IP
        assert len(result["nodes"]) == 2
        assert result["nodes"][0]["id"] == "10.0.0.1"
    
    def test_deduplication_with_missing_hostname(self, mapper):
        """Test deduplication when hostname is missing"""
        devices = [
            {"ip": "10.0.0.1", "neighbors": [{"ip": "10.0.0.2", "local_port": "g1/0", "remote_port": "g1/1"}]},
            {"ip": "10.0.0.2", "neighbors": [{"ip": "10.0.0.1", "local_port": "g1/1", "remote_port": "g1/0"}]},
        ]
        result = mapper.build_l2_map(devices)
        
        # Should use IP as node ID when hostname missing
        assert len(result["nodes"]) == 2
        assert any(n["id"] == "10.0.0.1" for n in result["nodes"])
        assert any(n["id"] == "10.0.0.2" for n in result["nodes"])
    
    def test_deduplication_peer_hostname_resolution(self, mapper):
        """Test peer hostname resolution from IP mapping"""
        devices = [
            {"ip": "10.0.0.1", "hostname": "switch-a", "neighbors": [{"ip": "10.0.0.2", "local_port": "g1/0", "remote_port": "g1/1"}]},
            {"ip": "10.0.0.2", "hostname": "switch-b", "neighbors": [{"ip": "10.0.0.1", "local_port": "g1/1", "remote_port": "g1/0"}]},
        ]
        result = mapper.build_l2_map(devices)
        
        # Should resolve peer hostnames from mapping
        assert len(result["nodes"]) == 2
        assert any(n["id"] == "switch-a" for n in result["nodes"])
        assert any(n["id"] == "switch-b" for n in result["nodes"])
        # Edges should use hostnames
        assert result["edges"][0]["from"] == "switch-a"
        assert result["edges"][0]["to"] == "switch-b"
    
    def test_deduplication_empty_neighbors(self, mapper):
        """Test deduplication with empty neighbor lists"""
        devices = [
            {"ip": "10.0.0.1", "hostname": "switch-a", "neighbors": []},
            {"ip": "10.0.0.2", "hostname": "switch-b", "neighbors": []},
        ]
        result = mapper.build_l2_map(devices)
        
        assert len(result["nodes"]) == 2
        assert len(result["edges"]) == 0
    
    def test_deduplication_missing_neighbor_ip(self, mapper):
        """Test handling of neighbors with missing IP"""
        devices = [
            {"ip": "10.0.0.1", "hostname": "switch-a", "neighbors": [{"local_port": "g1/0", "remote_port": "g1/1"}]},
        ]
        result = mapper.build_l2_map(devices)
        
        # Should skip neighbor with missing IP
        assert len(result["nodes"]) == 1
        assert len(result["edges"]) == 0
    
    def test_deduplication_complex_topology(self, mapper):
        """Test deduplication with complex multi-device topology"""
        devices = [
            {"ip": "10.0.0.1", "hostname": "core-1", "neighbors": [
                {"ip": "10.0.0.2", "local_port": "g1/0", "remote_port": "g1/1"},
                {"ip": "10.0.0.3", "local_port": "g1/1", "remote_port": "g1/0"},
            ]},
            {"ip": "10.0.0.2", "hostname": "core-2", "neighbors": [
                {"ip": "10.0.0.1", "local_port": "g1/1", "remote_port": "g1/0"},
                {"ip": "10.0.0.4", "local_port": "g1/0", "remote_port": "g1/1"},
            ]},
            {"ip": "10.0.0.3", "hostname": "core-3", "neighbors": [
                {"ip": "10.0.0.1", "local_port": "g1/0", "remote_port": "g1/1"},
            ]},
            {"ip": "10.0.0.4", "hostname": "edge-1", "neighbors": [
                {"ip": "10.0.0.2", "local_port": "g1/1", "remote_port": "g1/0"},
            ]},
        ]
        result = mapper.build_l2_map(devices)
        
        # Should deduplicate to 4 unique nodes
        assert len(result["nodes"]) == 4
        # Edges are bidirectional (each device reports its neighbors)
        assert len(result["edges"]) == 6  # core-1<->core-2 (2), core-1<->core-3 (2), core-2<->edge-1 (2)
    
    def test_deduplication_management_ip_preserved(self, mapper):
        """Test that management IP is preserved in node data"""
        devices = [
            {"ip": "10.0.0.1", "hostname": "switch-a", "neighbors": []},
        ]
        result = mapper.build_l2_map(devices)
        
        assert result["nodes"][0]["management_ip"] == "10.0.0.1"
    
    def test_deduplication_no_management_ip_when_hostname_equals_ip(self, mapper):
        """Test management_ip is empty when hostname equals IP"""
        devices = [
            {"ip": "10.0.0.1", "hostname": "10.0.0.1", "neighbors": []},
        ]
        result = mapper.build_l2_map(devices)
        
        assert result["nodes"][0]["management_ip"] == ""
    
    def test_deduplication_peer_remote_hostname(self, mapper):
        """Test peer hostname from remote_host field in neighbor data"""
        devices = [
            {"ip": "10.0.0.1", "hostname": "switch-a", "neighbors": [
                {"ip": "10.0.0.2", "remote_host": "switch-b", "local_port": "g1/0", "remote_port": "g1/1"},
            ]},
        ]
        result = mapper.build_l2_map(devices)
        
        # Should use remote_host for peer hostname
        assert len(result["nodes"]) == 2
        assert any(n["id"] == "switch-b" for n in result["nodes"])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
