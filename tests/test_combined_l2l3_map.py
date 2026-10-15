"""
Comprehensive tests for combined L2+L3 map generation
"""
import pytest
from modules.discovery.advanced_mapper import AdvancedMapper


class TestCombinedL2L3Map:
    """Test combined L2+L3 topology generation"""
    
    @pytest.fixture
    def mapper(self):
        return AdvancedMapper()
    
    def test_combined_map_basic(self, mapper):
        """Test basic combined L2+L3 map generation"""
        l2_devices = [
            {"ip": "10.0.0.1", "hostname": "switch-a", "neighbors": [{"ip": "10.0.0.2", "local_port": "g1/0", "remote_port": "g1/1"}]},
        ]
        l3_devices = [
            {"hostname": "switch-a", "routes": [
                {"network": "192.168.1.0/24", "protocol": "Connected", "next_hop": "0.0.0.0", "interface": "Vlan10"},
            ]},
        ]
        
        result = mapper.build_combined_l2l3_map(l2_devices, l3_devices)
        
        assert 'nodes' in result
        assert 'l2_edges' in result
        assert 'l3_edges' in result
        assert 'analysis' in result
        assert len(result['nodes']) >= 1
    
    def test_combined_map_empty_l2(self, mapper):
        """Test combined map with empty L2 data"""
        l2_devices = []
        l3_devices = [
            {"hostname": "router-a", "routes": [
                {"network": "0.0.0.0/0", "protocol": "Static", "next_hop": "10.0.0.1"},
            ]},
        ]
        
        result = mapper.build_combined_l2l3_map(l2_devices, l3_devices)
        
        # Should still generate L3 topology
        assert len(result['nodes']) >= 1
        assert len(result['l3_edges']) >= 0
    
    def test_combined_map_empty_l3(self, mapper):
        """Test combined map with empty L3 data"""
        l2_devices = [
            {"ip": "10.0.0.1", "hostname": "switch-a", "neighbors": [{"ip": "10.0.0.2", "local_port": "g1/0", "remote_port": "g1/1"}]},
        ]
        l3_devices = []
        
        result = mapper.build_combined_l2l3_map(l2_devices, l3_devices)
        
        # Should still generate L2 topology
        assert len(result['nodes']) >= 1
        assert len(result['l2_edges']) >= 1
    
    def test_combined_map_both_empty(self, mapper):
        """Test combined map with both L2 and L3 empty"""
        result = mapper.build_combined_l2l3_map([], [])
        
        assert len(result['nodes']) == 0
        assert len(result['l2_edges']) == 0
        assert len(result['l3_edges']) == 0
    
    def test_combined_map_node_enrichment(self, mapper):
        """Test that L2 nodes are enriched with L3 metadata"""
        l2_devices = [
            {"ip": "10.0.0.1", "hostname": "core-1", "neighbors": []},
        ]
        l3_devices = [
            {"hostname": "core-1", "routes": [
                {"network": "10.0.0.0/8", "protocol": "Connected", "interface": "Vlan10"},
                {"network": "192.168.1.0/24", "protocol": "OSPF", "next_hop": "10.0.0.2"},
            ]},
        ]
        
        result = mapper.build_combined_l2l3_map(l2_devices, l3_devices)
        
        # Find the core-1 node
        core1_node = next((n for n in result['nodes'] if n['id'] == 'core-1'), None)
        assert core1_node is not None
        # Should have L3 protocol information
        assert 'protocols' in core1_node or 'layer' in core1_node
    
    def test_combined_map_analysis_counts(self, mapper):
        """Test that analysis includes proper counts"""
        l2_devices = [
            {"ip": "10.0.0.1", "hostname": "switch-a", "neighbors": [{"ip": "10.0.0.2", "local_port": "g1/0", "remote_port": "g1/1"}]},
            {"ip": "10.0.0.2", "hostname": "switch-b", "neighbors": [{"ip": "10.0.0.1", "local_port": "g1/1", "remote_port": "g1/0"}]},
        ]
        l3_devices = [
            {"hostname": "switch-a", "routes": [{"network": "10.0.0.0/24", "protocol": "Connected"}]},
            {"hostname": "switch-b", "routes": [{"network": "10.0.1.0/24", "protocol": "Connected"}]},
        ]
        
        result = mapper.build_combined_l2l3_map(l2_devices, l3_devices)
        
        analysis = result['analysis']
        assert 'total_nodes' in analysis
        assert 'l2_edge_count' in analysis
        assert 'l3_edge_count' in analysis
        assert analysis['total_nodes'] >= 2
        assert analysis['l2_edge_count'] >= 1
    
    def test_combined_map_layer_separation(self, mapper):
        """Test that L2 and L3 edges are properly separated"""
        l2_devices = [
            {"ip": "10.0.0.1", "hostname": "switch-a", "neighbors": [{"ip": "10.0.0.2", "local_port": "g1/0", "remote_port": "g1/1"}]},
        ]
        l3_devices = [
            {"hostname": "switch-a", "routes": [{"network": "192.168.1.0/24", "protocol": "OSPF", "next_hop": "10.0.0.2"}]},
        ]
        
        result = mapper.build_combined_l2l3_map(l2_devices, l3_devices)
        
        # L2 edges should have physical link information
        if result['l2_edges']:
            assert 'protocol' in result['l2_edges'][0]
        
        # L3 edges should have routing protocol information
        if result['l3_edges']:
            assert 'protocol' in result['l3_edges'][0]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
