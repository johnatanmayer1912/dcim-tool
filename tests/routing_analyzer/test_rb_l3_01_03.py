"""RB-L3-01–03 regressions: parser alias, collector contract, multicast nodes."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from modules.routing_analyzer.collector import RoutingCollector, collect_routing_table
from modules.routing_analyzer.graph_builder import L3TopologyGraphBuilder, _is_usable_unicast_dest
from modules.routing_analyzer.parser import RoutingParser


class TestParserTemplateDirAlias:
    def test_template_dir_and_tdir_are_same_path(self):
        p = RoutingParser()
        assert p.template_dir == p._tdir
        assert p.template_dir.exists()
        p._tdir = p.template_dir
        assert p.template_dir == p._tdir

    def test_construct_with_explicit_template_dir(self, tmp_path):
        p = RoutingParser(template_dir=tmp_path)
        assert p.template_dir == tmp_path
        assert p._tdir == tmp_path

    def test_empty_template_dir_uses_default(self):
        p = RoutingParser(template_dir='')
        assert p.template_dir == p._tdir
        assert (p.template_dir / 'cisco' / 'show_ip_route.textfsm').is_file()

    def test_repeated_parse_uses_same_dir(self):
        p = RoutingParser()
        d1 = p.template_dir
        p.parse_routing_output_regex('cisco_ios', 'C    192.168.1.0/24 is directly connected, Gi0/0')
        assert p.template_dir == d1

    def test_parse_cisco_ip_route_missing_file(self, tmp_path):
        p = RoutingParser(template_dir=tmp_path)
        with pytest.raises(FileNotFoundError):
            p.parse_cisco_ip_route('C    192.168.1.0/24 is directly connected, Gi0/0')


class TestCollectorContract:
    def test_get_platform_commands_matches_commands(self):
        c = RoutingCollector('cisco_ios')
        assert c._get_platform_commands() == c.commands
        assert c.commands == list(dict.fromkeys(c.commands))

    def test_injected_transport_no_live_ssh(self):
        c = RoutingCollector('cisco_ios')
        conn = Mock()
        conn.send_command.return_value = 'C    10.0.0.0/8 is directly connected, GigabitEthernet0/0'
        out = c.collect_routing_table(conn)
        assert out['errors'] == []
        assert 'show ip route' in out['routing_tables']
        assert 'password' not in str(out).lower()

    def test_timeout_recorded_without_secret(self):
        c = RoutingCollector('cisco_ios')
        conn = Mock()
        conn.send_command.side_effect = TimeoutError('password=hunter2 timeout')
        out = c.collect_routing_table(conn)
        assert out['errors']
        blob = ' '.join(out['errors']).lower()
        assert 'hunter2' not in blob
        assert 'timeout' in blob

    @patch('modules.routing_analyzer.collector.safe_connection')
    def test_module_collect_redacts_and_records(self, mock_sc):
        mock_sc.side_effect = Exception('auth failed password=secret')
        out = collect_routing_table('10.1.1.1', 'cisco_ios', {'username': 'a', 'password': 'x'})
        assert out['errors']
        assert 'secret' not in out['errors'][0].lower() or 'password' not in out['errors'][0].lower()


class TestMulticastDeviceNodes:
    def test_ipv4_multicast_only(self):
        g = L3TopologyGraphBuilder()
        r = g.build_topology([{
            'device_id': 'r1', 'destination': '224.0.0.0/4',
            'next_hop': '0.0.0.0', 'protocol': 'Connected', 'route_type': 'Connected',
        }])
        assert r['nodes'] == []
        assert r['edges'] == []

    def test_default_route_not_multicast(self):
        assert _is_usable_unicast_dest('0.0.0.0/0') is True
        assert _is_usable_unicast_dest('::/0') is True
        g = L3TopologyGraphBuilder()
        r = g.build_topology([{
            'device_id': 'r1', 'destination': '0.0.0.0/0',
            'next_hop': '10.0.0.1', 'protocol': 'Static', 'route_type': 'Static',
        }])
        assert any(n['id'] == 'r1' for n in r['nodes'])

    def test_two_devices_one_multicast_only(self):
        g = L3TopologyGraphBuilder()
        r = g.build_topology([
            {'device_id': 'only-mcast', 'destination': '224.0.0.1/32',
             'next_hop': '0.0.0.0', 'protocol': 'Connected', 'route_type': 'Connected'},
            {'device_id': 'real', 'destination': '10.2.2.0/24',
             'next_hop': '0.0.0.0', 'protocol': 'Connected', 'route_type': 'Connected'},
        ])
        ids = [n['id'] for n in r['nodes']]
        assert 'real' in ids
        assert 'only-mcast' not in ids

    def test_ipv6_multicast_ff02(self):
        g = L3TopologyGraphBuilder()
        r = g.build_topology([{
            'device_id': 'r1', 'destination': 'ff02::1/128',
            'next_hop': '::', 'protocol': 'Connected', 'route_type': 'Connected',
        }])
        assert r['nodes'] == []

    def test_host_and_connected_unicast_keep_device(self):
        g = L3TopologyGraphBuilder()
        r = g.build_topology([
            {'device_id': 'r1', 'destination': '10.9.9.9/32',
             'next_hop': '0.0.0.0', 'protocol': 'Local', 'route_type': 'Local'},
            {'device_id': 'r1', 'destination': '10.9.9.0/24',
             'next_hop': '0.0.0.0', 'protocol': 'Connected', 'route_type': 'Connected'},
        ])
        assert any(n['id'] == 'r1' for n in r['nodes'])

    def test_empty_and_missing_fields(self):
        g = L3TopologyGraphBuilder()
        r = g.build_topology([
            {},
            {'device_id': 'r1'},
            {'device_id': 'r1', 'destination': ''},
        ])
        assert r['nodes'] == []

    def test_duplicate_unicast_routes_one_device(self):
        g = L3TopologyGraphBuilder()
        dup = {
            'device_id': 'r1', 'destination': '172.16.0.0/16',
            'next_hop': '0.0.0.0', 'protocol': 'Connected', 'route_type': 'Connected',
        }
        r = g.build_topology([dup, dict(dup)])
        assert [n['id'] for n in r['nodes'] if n.get('type') == 'device'] == ['r1']

    def test_multicast_plus_management_unicast(self):
        g = L3TopologyGraphBuilder()
        r = g.build_topology([
            {'device_id': 'r1', 'destination': '224.0.0.5/32',
             'next_hop': '0.0.0.0', 'protocol': 'Connected', 'route_type': 'Connected'},
            {'device_id': 'r1', 'destination': '192.0.2.10/32',
             'next_hop': '0.0.0.0', 'protocol': 'Connected', 'route_type': 'Connected'},
        ])
        assert any(n['id'] == 'r1' for n in r['nodes'])
        assert '224.0.0.5/32' not in [n['id'] for n in r['nodes']]

    def test_empty_route_list(self):
        assert L3TopologyGraphBuilder().build_topology([])['nodes'] == []


class TestCollectorEmptyAndUnsupported:
    def test_empty_output_skipped_not_error(self):
        c = RoutingCollector('cisco_ios')
        conn = Mock()
        conn.send_command.return_value = '   '
        out = c.collect_routing_table(conn)
        assert out['routing_tables'] == {}
        assert out['errors'] == []

    def test_invalid_input_skipped(self):
        c = RoutingCollector('cisco_ios')
        conn = Mock()
        conn.send_command.return_value = '% Invalid input detected at \'^\' marker.'
        out = c.collect_routing_table(conn)
        assert out['routing_tables'] == {}
        assert out['errors'] == []

    def test_unsupported_platform_defaults_to_cisco_commands(self):
        c = RoutingCollector('acme_toaster')
        assert 'show ip route' in c._get_platform_commands()

    def test_command_order_matches_platform_map(self):
        c = RoutingCollector('cisco_ios')
        assert c.commands[0] == 'show ip route'
        assert c.commands[-1] == 'show ipv6 route'
