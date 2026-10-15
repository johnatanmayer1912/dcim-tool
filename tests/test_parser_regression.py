"""
tests/test_parser_regression.py
---------------------------------
Regression tests for all parsers to ensure they handle edge cases and weird scenarios.
Tests network discovery, interface manager, and VPC parsers with various input formats.
"""

import unittest
import re
from modules.plugins.network_discovery import (
    _parse_cisco_cdp_detail,
    _parse_cisco_cdp_brief,
    _parse_cisco_lldp_detail,
    _parse_cisco_lldp_brief,
    _parse_juniper_lldp_detail,
    _parse_juniper_lldp_brief,
    _parse_juniper_lldp_table,
    _parse_juniper_lldp_alternative,
)
from modules.plugins.interface_manager import (
    _parse_nxos_interfaces,
    _parse_nxos_interfaces_fallback,
    _parse_ios_interfaces,
    _parse_ios_interfaces_fallback,
    _parse_junos_interfaces,
    _parse_junos_interfaces_fallback,
)
from modules.plugins.vpc_domain_plugin import (
    _parse_vpc_domain,
    _normalize_peer_status,
    _normalize_keepalive_status,
)


class TestCiscoCDPParserRegression(unittest.TestCase):
    """Regression tests for Cisco CDP parser with edge cases."""

    def test_cdp_detail_standard_format(self):
        """Test standard CDP detail output."""
        output = """
Device ID: NEXUS-01
Entry address(es): 
  IP address: 10.1.1.1
Platform: cisco N9K-C93180YC-FX,  Capabilities: Router Switch
Interface: Ethernet1/1,  Port ID (outgoing port): Ethernet1/1
Holdtime : 140 sec
"""
        neighbors = _parse_cisco_cdp_detail(output, 'test_host', None)
        self.assertEqual(len(neighbors), 1)
        self.assertEqual(neighbors[0]['hostname'], 'NEXUS-01')
        self.assertEqual(neighbors[0]['ip'], '10.1.1.1')

    def test_cdp_detail_empty_output(self):
        """Test empty CDP output."""
        neighbors = _parse_cisco_cdp_detail('', 'test_host', None)
        self.assertEqual(len(neighbors), 0)

    def test_cdp_detail_malformed_output(self):
        """Test malformed CDP output."""
        output = "garbage text that doesn't match CDP format"
        neighbors = _parse_cisco_cdp_detail(output, 'test_host', None)
        self.assertEqual(len(neighbors), 0)

    def test_cdp_detail_missing_ip(self):
        """Test CDP output without IP address."""
        output = """
Device ID: SWITCH-01
Platform: cisco WS-C3850
Interface: GigabitEthernet1/0/1
"""
        neighbors = _parse_cisco_cdp_detail(output, 'test_host', None)
        self.assertEqual(len(neighbors), 1)
        self.assertIsNone(neighbors[0]['ip'])

    def test_cdp_brief_table_format(self):
        """Test CDP brief table format."""
        output = """
Device ID    Local Intrf  Holdtme  Capability  Platform  Port ID
-----------  ----------  ------  ----------  --------  ------------
SWITCH-01    Gi1/0/1     140     R S         WS-C3850  Gi1/0/1
"""
        neighbors = _parse_cisco_cdp_brief(output, 'test_host', None)
        self.assertEqual(len(neighbors), 1)
        self.assertEqual(neighbors[0]['hostname'], 'SWITCH-01')


class TestCiscoLLDPParserRegression(unittest.TestCase):
    """Regression tests for Cisco LLDP parser with edge cases."""

    def test_lldp_detail_standard_format(self):
        """Test standard LLDP detail output."""
        output = """
Local Interface: Ethernet1/1
Chassis id: mac 00:1A:2B:3C:4D:5E
System Name: NEXUS-01
Management address: 10.1.1.1
Port id: Ethernet1/1
"""
        neighbors = _parse_cisco_lldp_detail(output, 'test_host', None)
        self.assertEqual(len(neighbors), 1)
        self.assertEqual(neighbors[0]['hostname'], 'NEXUS-01')

    def test_lldp_detail_not_advertised(self):
        """Test LLDP with 'not advertised' system name."""
        output = """
Local Interface: Ethernet1/1
Chassis id: mac 00:1A:2B:3C:4D:5E
System Name: not advertised
Port id: Ethernet1/1
"""
        neighbors = _parse_cisco_lldp_detail(output, 'test_host', None)
        self.assertEqual(len(neighbors), 1)
        self.assertIsNotNone(neighbors[0]['hostname'])

    def test_lldp_detail_mac_as_port_id(self):
        """Test LLDP with MAC as port ID."""
        output = """
Local Interface: Ethernet1/1
Chassis id: mac 00:1A:2B:3C:4D:5E
System Name: SWITCH-01
Port id: mac 00:1A:2B:3C:4D:5E
Port Description: Ethernet1/1
"""
        neighbors = _parse_cisco_lldp_detail(output, 'test_host', None)
        self.assertEqual(len(neighbors), 1)
        self.assertEqual(neighbors[0]['remote_port'], 'Eth1/1')

    def test_lldp_brief_format(self):
        """Test LLDP brief table format."""
        output = """
Local Intf   Neighbor   Vlan
-----------  ---------  -----
Eth1/1       SWITCH-01  1
"""
        neighbors = _parse_cisco_lldp_brief(output, 'test_host', None)
        self.assertEqual(len(neighbors), 1)


class TestJunosLLDPParserRegression(unittest.TestCase):
    """Regression tests for Junos LLDP parser with edge cases."""

    def test_junos_lldp_detail_standard_format(self):
        """Test standard Junos LLDP detail output."""
        output = """
Local Interface: ge-0/0/0
System name: JUNOS-01
Management address: 10.1.1.1
Port ID: ge-0/0/0
"""
        neighbors = _parse_juniper_lldp_detail(output, 'test_host', None)
        self.assertEqual(len(neighbors), 1)
        self.assertEqual(neighbors[0]['hostname'], 'JUNOS-01')

    def test_junos_lldp_detail_xe_interface(self):
        """Test Junos LLDP with xe- (10GbE) interfaces."""
        output = """
Local Interface: xe-0/0/0
System name: JUNOS-01
Management address: 10.1.1.1
Port ID: xe-0/0/0
"""
        neighbors = _parse_juniper_lldp_detail(output, 'test_host', None)
        self.assertEqual(len(neighbors), 1)
        self.assertEqual(neighbors[0]['local_port'], 'xe-0/0/0')

    def test_junos_lldp_detail_empty_output(self):
        """Test empty Junos LLDP output."""
        neighbors = _parse_juniper_lldp_detail('', 'test_host', None)
        self.assertEqual(len(neighbors), 0)

    def test_junos_lldp_brief_format(self):
        """Test Junos LLDP brief table format."""
        output = """
Local Interface  Parent Interface  Chassis Id        Port info      System Name
ge-0/0/0         -                 00:1A:2B:3C:4D:5E  ge-0/0/0        JUNOS-01
xe-0/0/0         -                 00:1A:2B:3C:4D:5E  xe-0/0/0        JUNOS-02
"""
        neighbors = _parse_juniper_lldp_brief(output, 'test_host', None)
        self.assertGreaterEqual(len(neighbors), 1)
        hosts = {n['hostname'] for n in neighbors}
        self.assertIn('JUNOS-01', hosts)
        self.assertNotIn('-', hosts)

    def test_junos_lldp_table_format(self):
        """Test Junos LLDP table format."""
        output = """
Local Interface  Parent Interface  Chassis Id        Port info      System Name
ge-0/0/0         -                 00:1A:2B:3C:4D:5E  ge-0/0/0        JUNOS-01
xe-0/0/0         -                 00:1A:2B:3C:4D:5E  xe-0/0/0        JUNOS-02
"""
        neighbors = _parse_juniper_lldp_table(output, 'test_host', None)
        self.assertGreaterEqual(len(neighbors), 1)

    def test_junos_lldp_alternative_format(self):
        """Test Junos LLDP alternative format."""
        output = """
ge-0/0/0
  System Name: JUNOS-01
  Management address: 10.1.1.1
xe-0/0/0
  System Name: JUNOS-02
"""
        neighbors = _parse_juniper_lldp_alternative(output, 'test_host', None)
        self.assertGreaterEqual(len(neighbors), 1)


class TestInterfaceParserRegression(unittest.TestCase):
    """Regression tests for interface parsers with edge cases."""

    def test_nxos_interfaces_standard_format(self):
        """Test standard NXOS interface output."""
        output = """
Ethernet1/1
  status: connected
  speed: 10G
  duplex: full
  mtu: 1500
"""
        interfaces = _parse_nxos_interfaces(output)
        self.assertEqual(len(interfaces), 1)
        self.assertEqual(interfaces[0]['name'], 'Ethernet1/1')
        self.assertEqual(interfaces[0]['status'], 'connected')

    def test_nxos_interfaces_empty_output(self):
        """Test empty NXOS interface output."""
        interfaces = _parse_nxos_interfaces('')
        self.assertEqual(len(interfaces), 0)

    def test_nxos_interfaces_fallback_format(self):
        """Test NXOS interface fallback parsing."""
        output = "Eth1/1 up 10G full"
        interfaces = _parse_nxos_interfaces_fallback(output)
        self.assertGreaterEqual(len(interfaces), 1)

    def test_ios_interfaces_standard_format(self):
        """Test standard IOS interface output."""
        output = """
GigabitEthernet1/0/1 is up, line protocol is up
  Hardware is Gigabit Ethernet, address is 00:1A:2B:3C:4D:5E
  MTU 1500 bytes, BW 1000000 Kbit
"""
        interfaces = _parse_ios_interfaces(output)
        self.assertEqual(len(interfaces), 1)
        self.assertEqual(interfaces[0]['name'], 'GigabitEthernet1/0/1')

    def test_ios_interfaces_fallback_format(self):
        """Test IOS interface fallback parsing."""
        output = "GigabitEthernet1/0/1 up"
        interfaces = _parse_ios_interfaces_fallback(output)
        self.assertGreaterEqual(len(interfaces), 1)

    def test_junos_interfaces_standard_format(self):
        """Test standard Junos interface output."""
        output = """
Physical interface: ge-0/0/0, Enabled, Physical link is Up
  Speed: 1Gbps
  Duplex: Full-Duplex
  MTU: 1514
"""
        interfaces = _parse_junos_interfaces(output)
        self.assertEqual(len(interfaces), 1)
        self.assertEqual(interfaces[0]['name'], 'ge-0/0/0')
        self.assertEqual(interfaces[0]['status'], 'up')

    def test_junos_interfaces_xe_format(self):
        """Test Junos xe- interface format."""
        output = """
Physical interface: xe-0/0/0, Enabled, Physical link is Up
  Speed: 10Gbps
  Duplex: Full-Duplex
  MTU: 1514
"""
        interfaces = _parse_junos_interfaces(output)
        self.assertEqual(len(interfaces), 1)
        self.assertEqual(interfaces[0]['name'], 'xe-0/0/0')
        self.assertEqual(interfaces[0]['status'], 'up')

    def test_junos_interfaces_physical_link_down(self):
        """Test Junos Physical link is Down detection."""
        output = """
Physical interface: ge-0/0/0, Enabled, Physical link is Down
"""
        interfaces = _parse_junos_interfaces(output)
        self.assertEqual(len(interfaces), 1)
        self.assertEqual(interfaces[0]['status'], 'down')

    def test_junos_interfaces_fallback_format(self):
        """Test Junos interface fallback parsing."""
        output = "ge-0/0/0\nxe-0/0/0"
        interfaces = _parse_junos_interfaces_fallback(output)
        self.assertGreaterEqual(len(interfaces), 2)


class TestVPCParserRegression(unittest.TestCase):
    """Regression tests for VPC parser with edge cases."""

    def test_vpc_domain_standard_format(self):
        """Test standard VPC domain output."""
        output = """
vPC domain id : 1
Peer status : peer link is up
vPC keep-alive status : peer is alive
Configuration consistency status : success
Per-vlan consistency status : success
"""
        info = _parse_vpc_domain(output)
        self.assertEqual(info['domain_id'], '1')
        self.assertEqual(info['peer_status'], 'up')

    def test_vpc_domain_empty_output(self):
        """Test empty VPC output."""
        info = _parse_vpc_domain('')
        self.assertFalse(info['present'])

    def test_vpc_domain_invalid_command(self):
        """Test invalid command output."""
        output = "% Invalid input detected"
        info = _parse_vpc_domain(output)
        self.assertFalse(info['present'])

    def test_vpc_domain_alternative_formats(self):
        """Test alternative VPC domain formats."""
        output = "VPC domain id : 100"
        info = _parse_vpc_domain(output)
        self.assertEqual(info['domain_id'], '100')

    def test_normalize_peer_status(self):
        """Test peer status normalization."""
        self.assertEqual(_normalize_peer_status('peer link is up'), 'up')
        self.assertEqual(_normalize_peer_status('peer link is down'), 'down')
        self.assertEqual(_normalize_peer_status('peer link is alive'), 'up')

    def test_normalize_keepalive_status(self):
        """Test keepalive status normalization."""
        self.assertEqual(_normalize_keepalive_status('peer is alive'), 'up')
        self.assertEqual(_normalize_keepalive_status('suspended'), 'down')
        self.assertEqual(_normalize_keepalive_status('destination ip not reachable'), 'down')


class TestOfflineEnvironmentValidation(unittest.TestCase):
    """Tests for offline environment validation."""

    def test_demo_mode_discovery(self):
        """Test discovery demo mode works without network."""
        from modules.plugins.network_discovery import _build_demo_discovery_data
        data = _build_demo_discovery_data(['10.0.0.1'], 2, None)
        self.assertIn('discovered_nodes', data)
        self.assertIn('discovered_edges', data)
        self.assertTrue(len(data['discovered_nodes']) > 0)

    def test_demo_mode_vpc(self):
        """Test VPC demo mode works without network."""
        from modules.plugins.vpc_domain_plugin import _vpc_domain_cache
        # Demo mode should use cached or synthetic data
        self.assertIsInstance(_vpc_domain_cache, dict)


class TestDuplicateDeviceDetection(unittest.TestCase):
    """Tests for duplicate device detection and merging."""

    def test_duplicate_ip_merging(self):
        """Test merging devices with same IP."""
        from utils.discovery_graph import merge_nodes, canonical_device_key
        
        nodes = [
            {'id': 'switch01', 'ip': '10.1.1.1', 'is_scanned': True, 'serial': 'SN123'},
            {'id': 'switch01.example.com', 'ip': '10.1.1.1', 'is_scanned': False, 'serial': 'SN123'},
        ]
        
        merged, alias_map = merge_nodes(nodes)
        self.assertEqual(len(merged), 1)
        self.assertIn('10.1.1.1', alias_map)

    def test_duplicate_hostname_merging(self):
        """Test merging devices with same hostname."""
        from utils.discovery_graph import merge_nodes
        
        nodes = [
            {'id': 'switch01', 'ip': '10.1.1.1', 'is_scanned': True, 'serial': 'SN123'},
            {'id': 'switch01', 'ip': '10.1.1.2', 'is_scanned': False, 'serial': 'SN123'},
        ]
        
        merged, alias_map = merge_nodes(nodes)
        self.assertEqual(len(merged), 1)

    def test_duplicate_serial_merging(self):
        """Test merging devices with same serial."""
        from utils.discovery_graph import merge_nodes
        
        nodes = [
            {'id': 'switch01', 'ip': '10.1.1.1', 'is_scanned': True, 'serial': 'SN123'},
            {'id': 'switch02', 'ip': '10.1.1.2', 'is_scanned': False, 'serial': 'SN123'},
        ]
        
        merged, alias_map = merge_nodes(nodes)
        self.assertEqual(len(merged), 1)


if __name__ == '__main__':
    unittest.main()
