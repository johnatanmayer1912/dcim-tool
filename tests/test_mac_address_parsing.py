"""
Comprehensive tests for MAC address table parsing (IOS/NX-OS)
"""
import pytest
from modules.routing_analyzer.parser import RoutingParser


class TestMACAddressParsing:
    """Test MAC address table parsing for IOS and NX-OS"""
    
    @pytest.fixture
    def parser(self):
        return RoutingParser()
    
    def test_ios_mac_table_basic(self, parser):
        """Test basic IOS MAC address table parsing"""
        output = """
Mac Address Table
-------------------------------------------

Vlan    Mac Address       Type        Ports
----    -----------        --------    -----
 100    0000.0c12.3456    DYNAMIC     Gi1/0/1
 200    0000.0c12.7890    STATIC      Gi1/0/2
"""
        results = parser.parse_mac_address_table('cisco_ios', 'show mac address-table', output)
        
        assert len(results) == 2
        assert results[0]['mac_address'] == '0000.0c12.3456'
        assert results[0]['vlan'] == '100'
        assert results[0]['interface'] == 'Gi1/0/1'
        assert results[0]['type'] == 'DYNAMIC'
    
    def test_nxos_mac_table_basic(self, parser):
        """Test basic NX-OS MAC address table parsing"""
        output = """
`Legend: * - primary entry, G - Gateway MAC, (R) - Routed MAC, O - Overlay MAC
        age - seconds since last seen,+ - primary entry with port

VLAN     MAC Address      Type      Age      Port
---------+---------------+--------+---------+----------
 10       00:00:00:00:00:01 dynamic   10       Ethernet1/1
 20       00:00:00:00:00:02 static    -        Ethernet1/2
"""
        results = parser.parse_mac_address_table('cisco_nxos', 'show mac address-table', output)
        
        assert len(results) >= 2
        assert any(r['mac_address'] == '00:00:00:00:00:01' for r in results)
        assert any(r['vlan'] == '10' for r in results)
    
    def test_ios_mac_empty_output(self, parser):
        """Test empty MAC table output"""
        output = ""
        results = parser.parse_mac_address_table('cisco_ios', 'show mac address-table', output)
        assert len(results) == 0
    
    def test_ios_mac_malformed_output(self, parser):
        """Test malformed MAC table output"""
        output = "Invalid MAC table output that doesn't match pattern"
        results = parser.parse_mac_address_table('cisco_ios', 'show mac address-table', output)
        assert len(results) == 0
    
    def test_ios_mac_multiple_entries(self, parser):
        """Test MAC table with multiple entries"""
        output = """
Vlan    Mac Address       Type        Ports
----    -----------        --------    -----
 100    0000.0c12.3456    DYNAMIC     Gi1/0/1
 100    0000.0c12.3457    DYNAMIC     Gi1/0/2
 200    0000.0c12.3458    STATIC      Gi1/0/3
 300    0000.0c12.3459    DYNAMIC     Gi1/0/4
"""
        results = parser.parse_mac_address_table('cisco_ios', 'show mac address-table', output)
        
        assert len(results) == 4
        vlans = [r['vlan'] for r in results]
        assert '100' in vlans
        assert '200' in vlans
        assert '300' in vlans
    
    def test_nxos_mac_colon_format(self, parser):
        """Test NX-OS colon-separated MAC format"""
        output = """
VLAN     MAC Address      Type      Age      Port
---------+---------------+--------+---------+----------
 10       00:11:22:33:44:55 dynamic   10       Ethernet1/1
"""
        results = parser.parse_mac_address_table('cisco_nxos', 'show mac address-table', output)
        
        assert len(results) == 1
        assert results[0]['mac_address'] == '00:11:22:33:44:55'
    
    def test_ios_mac_dot_format(self, parser):
        """Test IOS dot-separated MAC format"""
        output = """
Vlan    Mac Address       Type        Ports
----    -----------        --------    -----
 100    0011.2233.4455    DYNAMIC     Gi1/0/1
"""
        results = parser.parse_mac_address_table('cisco_ios', 'show mac address-table', output)
        
        assert len(results) == 1
        assert results[0]['mac_address'] == '0011.2233.4455'
    
    def test_mac_table_with_hyphen_interface(self, parser):
        """Test MAC table with hyphenated interface names"""
        output = """
Vlan    Mac Address       Type        Ports
----    -----------        --------    -----
 100    0000.0c12.3456    DYNAMIC     Gi1/0-1
"""
        results = parser.parse_mac_address_table('cisco_ios', 'show mac address-table', output)
        
        assert len(results) == 1
        assert 'Gi1/0-1' in results[0]['interface']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
