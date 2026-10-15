"""
tests/routing_analyzer/test_parser.py
------------------------------------
Comprehensive automated tests for routing parser module.
"""

import pytest
from textfsm import TextFSM
from pathlib import Path
from modules.routing_analyzer.parser import RoutingParser



class TestRoutingParser:
    """Test RoutingParser class"""
    
    @pytest.fixture
    def parser(self):
        return RoutingParser()
    
    @pytest.fixture
    def template_dir(self):
        """Get template directory path"""
        return Path(__file__).parent.parent.parent / 'modules' / 'templates'
    
    def test_parser_initialization(self, parser):
        """Test parser initialization"""
        assert parser is not None
        assert parser.template_dir is not None
        assert parser._tdir == parser.template_dir
        assert parser.template_dir.is_absolute() or parser.template_dir.exists()
    
    def test_template_dir_exists(self, parser):
        """Test that template directory exists"""
        assert parser.template_dir.exists()
    
    def test_cisco_template_exists(self, parser, template_dir):
        """Test that Cisco template exists"""
        cisco_template = template_dir / 'cisco' / 'show_ip_route.textfsm'
        assert cisco_template.exists()
    
    def test_juniper_template_exists(self, parser, template_dir):
        """Test that Juniper template exists"""
        juniper_template = template_dir / 'juniper' / 'show_route.textfsm'
        assert juniper_template.exists()
    
    def test_parse_cisco_ip_route_basic(self, parser):
        """Test basic Cisco IP route parsing"""
        output = """
C    192.168.1.0/24 is directly connected, GigabitEthernet1/0/1
S    10.0.0.0/8 [1/0] via 10.0.0.1
O    172.16.0.0/16 [110/2] via 10.0.0.2, 00:01:23, GigabitEthernet1/0/2
"""
        
        results = parser.parse_routing_output_regex('cisco_ios', output)
        
        # The parser should at least return a list
        assert isinstance(results, list)
        # If parsing works, we should get some results
        assert len(results) >= 3
    
    def test_parse_cisco_ip_route_empty_output(self, parser):
        """Test parsing empty Cisco output"""
        output = ""
        results = parser.parse_routing_output_regex('cisco_ios', output)
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_parse_cisco_ip_route_invalid_output(self, parser):
        """Test parsing invalid Cisco output"""
        output = "Invalid routing output that doesn't match pattern"
        results = parser.parse_routing_output_regex('cisco_ios', output)
        # Should return empty list rather than crash
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_parse_juniper_show_route_basic(self, parser):
        """Test basic Juniper route parsing"""
        output = """
10.0.0.0/8          *[Static/5] 00:01:23
                    > to 10.0.0.1 via ge-0/0/0
192.168.1.0/24      *[Direct/0] 00:02:34
                    > via ge-0/0/1
172.16.0.0/16       *[OSPF/10] 00:03:45, metric 2
                    > to 10.0.0.2 via ge-0/0/0
"""
        
        results = parser.parse_routing_output_regex('juniper_junos', output)
        
        assert len(results) == 3
        assert results[0]['network'] == '10.0.0.0/8'
        assert results[0]['protocol'] == 'Static'
        assert results[0]['next_hop'] == '10.0.0.1'
        assert results[0]['interface'] == 'ge-0/0/0'
        
        assert results[1]['network'] == '192.168.1.0/24'
        assert results[1]['protocol'] == 'Connected'
        
        assert results[2]['network'] == '172.16.0.0/16'
        assert results[2]['protocol'] == 'OSPF'
    
    def test_parse_juniper_show_route_empty_output(self, parser):
        """Test parsing empty Juniper output"""
        output = ""
        results = parser.parse_routing_output_regex('juniper_junos', output)
        assert len(results) == 0
    
    def test_parse_routing_output_cisco_route(self, parser):
        """Test parse_routing_output with Cisco route command"""
        output = "C    192.168.1.0/24 is directly connected, GigabitEthernet1/0/1"
        results = parser.parse_routing_output('cisco_ios', 'show ip route', output)
        
        assert len(results) > 0
        assert results[0]['protocol'] == 'Connected'
    
    def test_parse_routing_output_juniper_route(self, parser):
        """Test parse_routing_output with Juniper route command"""
        output = """
10.0.0.0/8          *[Static/5] 00:01:23
                    > to 10.0.0.1 via ge-0/0/0
"""
        results = parser.parse_routing_output('juniper_junos', 'show route', output)
        
        assert len(results) > 0
        assert results[0]['protocol'] == 'Static'
    
    def test_parse_routing_output_unknown_platform(self, parser):
        """Test parse_routing_output with unknown platform (defaults to Cisco)"""
        output = "C    192.168.1.0/24 is directly connected, GigabitEthernet1/0/1"
        results = parser.parse_routing_output('unknown_platform', 'show ip route', output)
        
        # Should default to Cisco parser
        assert len(results) > 0
    
    def test_parse_routing_output_case_insensitive(self, parser):
        """Test that command matching is case insensitive"""
        output = "C    192.168.1.0/24 is directly connected, GigabitEthernet1/0/1"
        
        # Should work with different case variations
        results1 = parser.parse_routing_output('cisco_ios', 'show ip route', output)
        results2 = parser.parse_routing_output('CISCO_IOS', 'SHOW IP ROUTE', output)
        results3 = parser.parse_routing_output('Cisco_IOS', 'Show Ip Route', output)
        
        assert len(results1) == len(results2) == len(results3)


class TestCiscoRouteTemplates:
    """Test Cisco routing template patterns"""
    
    @pytest.fixture
    def parser(self):
        return RoutingParser()
    
    def test_connected_route_pattern(self, parser):
        """Test connected route pattern"""
        output = "C    192.168.1.0/24 is directly connected, GigabitEthernet1/0/1"
        results = parser.parse_routing_output_regex('cisco_ios', output)
        
        assert len(results) == 1
        assert results[0]['protocol'] == 'Connected'
        assert results[0]['interface'] == 'GigabitEthernet1/0/1'
        assert results[0]['next_hop'] == '0.0.0.0'  # Connected routes have no next hop
    
    def test_static_route_pattern(self, parser):
        """Test static route pattern"""
        output = "S    10.0.0.0/8 [1/0] via 10.0.0.1"
        results = parser.parse_routing_output_regex('cisco_ios', output)
        
        assert len(results) == 1
        assert results[0]['protocol'] == 'Static'
        assert results[0]['next_hop'] == '10.0.0.1'
    
    def test_ospf_route_pattern(self, parser):
        """Test OSPF route pattern"""
        output = "O    172.16.0.0/16 [110/2] via 10.0.0.2, 00:01:23, GigabitEthernet1/0/2"
        results = parser.parse_routing_output_regex('cisco_ios', output)
        
        assert len(results) == 1
        assert results[0]['protocol'] == 'OSPF'
        assert results[0]['next_hop'] == '10.0.0.2'
        assert results[0]['interface'] == 'GigabitEthernet1/0/2'
    
    def test_bgp_route_pattern(self, parser):
        """Test BGP route pattern"""
        output = "B    203.0.113.0/24 [20/0] via 192.0.2.1, 00:05:30"
        results = parser.parse_routing_output_regex('cisco_ios', output)
        
        assert len(results) == 1
        assert results[0]['protocol'] == 'BGP'
        assert results[0]['next_hop'] == '192.0.2.1'
    
    def test_eigrp_route_pattern(self, parser):
        """Test EIGRP route pattern"""
        output = "D    10.10.0.0/16 [90/2172416] via 10.0.0.1, 00:00:23, GigabitEthernet1/0/1"
        results = parser.parse_routing_output_regex('cisco_ios', output)
        
        assert len(results) == 1
        assert results[0]['protocol'] == 'EIGRP'
        assert results[0]['next_hop'] == '10.0.0.1'
    
    def test_rip_route_pattern(self, parser):
        """Test RIP route pattern"""
        output = "R    192.168.100.0/24 [120/4] via 10.0.0.3, 00:00:15, GigabitEthernet1/0/3"
        results = parser.parse_routing_output_regex('cisco_ios', output)
        
        assert len(results) == 1
        assert results[0]['protocol'] == 'RIP'
        assert results[0]['next_hop'] == '10.0.0.3'


class TestJuniperRouteTemplates:
    """Test Juniper routing template patterns"""
    
    @pytest.fixture
    def parser(self):
        return RoutingParser()
    
    def test_static_route_pattern(self, parser):
        """Test Juniper static route pattern"""
        output = """
10.0.0.0/8          *[Static/5] 00:01:23
                    > to 10.0.0.1 via ge-0/0/0
"""
        results = parser.parse_routing_output_regex('juniper_junos', output)
        
        assert len(results) == 1
        assert results[0]['protocol'] == 'Static'
        assert results[0]['next_hop'] == '10.0.0.1'
    
    def test_direct_route_pattern(self, parser):
        """Test Juniper direct route pattern"""
        output = """
192.168.1.0/24      *[Direct/0] 00:02:34
                    > via ge-0/0/1
"""
        results = parser.parse_routing_output_regex('juniper_junos', output)
        
        assert len(results) == 1
        assert results[0]['protocol'] == 'Connected'
    
    def test_ospf_route_pattern(self, parser):
        """Test Juniper OSPF route pattern"""
        output = """
172.16.0.0/16       *[OSPF/10] 00:03:45, metric 2
                    > to 10.0.0.2 via ge-0/0/0
"""
        results = parser.parse_routing_output_regex('juniper_junos', output)
        
        assert len(results) == 1
        assert results[0]['protocol'] == 'OSPF'
        assert results[0]['next_hop'] == '10.0.0.2'
    
    def test_bgp_route_pattern(self, parser):
        """Test Juniper BGP route pattern"""
        output = """
203.0.113.0/24      *[BGP/170] 00:05:30, localpref 100
                    > to 192.0.2.1 via ge-0/0/1
"""
        results = parser.parse_routing_output_regex('juniper_junos', output)
        
        assert len(results) == 1
        assert results[0]['protocol'] == 'BGP'
        assert results[0]['next_hop'] == '192.0.2.1'


class TestTemplateFileValidation:
    """Test TextFSM template file validation"""
    
    @pytest.fixture
    def parser(self):
        return RoutingParser()
    
    def test_cisco_template_valid_textfsm(self, parser):
        """Test that Cisco template is valid TextFSM"""
        template_path = parser.template_dir / 'cisco' / 'show_ip_route.textfsm'
        
        with open(template_path) as f:
            template = TextFSM(f)
        
        assert template is not None
    
    def test_juniper_template_valid_textfsm(self, parser):
        """Test that Juniper template is valid TextFSM"""
        template_path = parser.template_dir / 'juniper' / 'show_route.textfsm'
        
        with open(template_path) as f:
            template = TextFSM(f)
        
        assert template is not None
    
    def test_template_file_not_empty(self, parser):
        """Test that template files are not empty"""
        template_files = [
            parser.template_dir / 'cisco' / 'show_ip_route.textfsm',
            parser.template_dir / 'juniper' / 'show_route.textfsm'
        ]
        
        for template_file in template_files:
            assert template_file.exists()
            assert template_file.stat().st_size > 0
    
    def test_template_has_required_sections(self, parser):
        """Test that templates have required TextFSM sections"""
        template_path = parser.template_dir / 'cisco' / 'show_ip_route.textfsm'
        
        with open(template_path) as f:
            content = f.read()
        
        # Should have Value, Start, and Record sections
        assert 'Value' in content
        assert 'Start' in content
        assert 'Record' in content


class TestErrorHandling:
    """Test error handling in parser"""
    
    @pytest.fixture
    def parser(self):
        return RoutingParser()
    
    def test_parse_with_missing_template(self, parser):
        """Test parser behavior when template is missing"""
        # Temporarily rename template to simulate missing file
        template_path = parser.template_dir / 'cisco' / 'show_ip_route.textfsm'
        backup_path = template_path.with_suffix('.backup')
        
        # Rename if exists
        if template_path.exists():
            template_path.rename(backup_path)
        
        try:
            with pytest.raises(FileNotFoundError):
                parser.parse_cisco_ip_route("C    192.168.1.0/24 is directly connected")
        finally:
            # Restore original template
            if backup_path.exists():
                backup_path.rename(template_path)
    
    def test_parse_with_malformed_template(self, parser):
        """Test parser behavior with malformed template"""
        # This would require creating a malformed template file
        # For now, just test that current templates are valid
        template_path = parser.template_dir / 'cisco' / 'show_ip_route.textfsm'
        
        with open(template_path) as f:
            try:
                TextFSM(f)
                # If we get here, template is valid
                assert True
            except Exception as e:
                pytest.fail(f"Template is malformed: {e}")
    
    def test_parse_with_none_output(self, parser):
        """Test parser with None output"""
        with pytest.raises((TypeError, AttributeError)):
            parser.parse_cisco_ip_route(None)
    
    def test_parse_with_numeric_output(self, parser):
        """Test parser with numeric instead of string output"""
        with pytest.raises((TypeError, AttributeError)):
            parser.parse_cisco_ip_route(12345)


class TestComplexRoutingScenarios:
    """Test complex routing scenarios"""
    
    @pytest.fixture
    def parser(self):
        return RoutingParser()
    
    def test_multi_protocol_cisco_output(self, parser):
        """Test Cisco output with multiple protocols"""
        output = """
C    192.168.1.0/24 is directly connected, GigabitEthernet1/0/1
S    10.0.0.0/8 [1/0] via 10.0.0.1
O    172.16.0.0/16 [110/2] via 10.0.0.2, 00:01:23, GigabitEthernet1/0/2
B    203.0.113.0/24 [20/0] via 192.0.2.1, 00:05:30
D    10.10.0.0/16 [90/2172416] via 10.0.0.1, 00:00:23, GigabitEthernet1/0/1
R    192.168.100.0/24 [120/4] via 10.0.0.3, 00:00:15, GigabitEthernet1/0/3
"""
        
        results = parser.parse_routing_output_regex('cisco_ios', output)
        
        assert len(results) == 6
        protocols = [r['protocol'] for r in results]
        assert 'Connected' in protocols
        assert 'Static' in protocols
        assert 'OSPF' in protocols
        assert 'BGP' in protocols
        assert 'EIGRP' in protocols
        assert 'RIP' in protocols
    
    def test_long_cisco_output(self, parser):
        """Test parser with long Cisco output"""
        # Generate many routes
        routes = []
        for i in range(100):
            routes.append(f"C    192.168.{i}.0/24 is directly connected, GigabitEthernet1/0/{i}")
        
        output = '\n'.join(routes)
        results = parser.parse_routing_output_regex('cisco_ios', output)
        
        assert len(results) == 100
    
    def test_cisco_output_with_headers(self, parser):
        """Test Cisco output with header lines"""
        output = """
Codes: C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area
       N1 - EIGRP, N2 - EIGRP, E1 - OSPF external type 1, E2 - OSPF external type 2
       i - IS-IS, su - IS-IS summary, L1 - IS-IS level-1, L2 - IS-IS level-2
       ia - IS-IS inter area, * - candidate default, U - per-user static route
       o - ODR, P - periodic downloaded static route, H - NHRP

Gateway of last resort is 10.0.0.1 to network 0.0.0.0

C    192.168.1.0/24 is directly connected, GigabitEthernet1/0/1
S    10.0.0.0/8 [1/0] via 10.0.0.1
"""
        
        results = parser.parse_routing_output_regex('cisco_ios', output)
        
        # Should parse only the actual routes, not headers
        assert len(results) == 2
        assert all(r['protocol'] in ['Connected', 'Static'] for r in results)
    
    def test_cisco_output_with_gateway_of_last_resort(self, parser):
        """Test Cisco output with gateway of last resort"""
        output = """
Gateway of last resort is 10.0.0.1 to network 0.0.0.0

S*   0.0.0.0/0 [1/0] via 10.0.0.1
C    192.168.1.0/24 is directly connected, GigabitEthernet1/0/1
"""
        
        results = parser.parse_routing_output_regex('cisco_ios', output)
        
        # Should parse the default route
        assert len(results) >= 1
        assert any(r['network'] == '0.0.0.0/0' for r in results)
    
    def test_ios_connected_with_ad_notation(self, parser):
        """Test IOS connected routes with [AD/metric] notation (new enhancement)"""
        output = "C    10.0.0.0/8 [0/0] is directly connected, GigabitEthernet0/0"
        results = parser.parse_routing_output_regex('cisco_ios', output)
        
        assert len(results) == 1
        assert results[0]['protocol'] == 'Connected'
        assert results[0]['network'] == '10.0.0.0/8'
        assert results[0]['interface'] == 'GigabitEthernet0/0'
    
    def test_nxos_modern_ubest_format(self, parser):
        """Test NX-OS modern ubest/mbest format"""
        output = """
10.1.0.0/24, ubest/mbest: 1/0, attached
  *via 10.0.0.1, Eth1/1, [110/20], 00:01:00, ospf-101, intra
"""
        results = parser.parse_routing_output_regex('cisco_nxos', output)
        
        assert len(results) >= 1
        assert any(r['network'] == '10.1.0.0/24' for r in results)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
