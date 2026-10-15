"""Network Discovery plugin — parser and demo-mode tests (no live SSH)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.plugins import network_discovery as nd

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures', 'discovery')


class TestDiscoveryParsers(unittest.TestCase):
    def test_ios_cdp_detail(self):
        with open(os.path.join(FIXTURES, 'ios_cdp_detail.txt'), encoding='utf-8') as f:
            text = f.read()
        neighbors = nd._parse_cisco_cdp_detail(text, 'CORE', None)
        hosts = {n['hostname'] for n in neighbors}
        self.assertIn('DIST-SW01.example.com', hosts)
        self.assertNotIn('AP-FLOOR2', hosts)  # phone filtered
        dist = next(n for n in neighbors if 'DIST' in n['hostname'])
        self.assertEqual(dist['ip'], '10.0.0.2')

    def test_nxos_lldp_detail(self):
        with open(os.path.join(FIXTURES, 'nxos_lldp_detail.txt'), encoding='utf-8') as f:
            text = f.read()
        neighbors = nd._parse_cisco_lldp_detail(text, 'CORE', None)
        finalized = [nd._finalize_neighbor(n) for n in neighbors]
        finalized = [n for n in finalized if n]
        self.assertTrue(any('SPINE-NXOS-05' in n['hostname'] for n in finalized))
        spine = next(n for n in finalized if 'SPINE-NXOS-05' in n['hostname'])
        self.assertEqual(spine['local_port'], 'Eth1/2')
        self.assertEqual(spine['remote_port'], 'Eth1/1')

    def test_nxos_lldp_local_port_id_and_mac_remote(self):
        with open(os.path.join(FIXTURES, 'nxos_lldp_mac_portid.txt'), encoding='utf-8') as f:
            text = f.read()
        raw = nd._parse_cisco_lldp_detail(text, 'LEAF', None)
        n = nd._finalize_neighbor(raw[0])
        self.assertEqual(n['local_port'], 'Eth1/3')
        self.assertEqual(n['remote_port'], 'Eth2/11')
        self.assertEqual(n['hostname'], 'SPINE-NXOS-02')

    def test_nxos_lldp_not_advertised_uses_chassis(self):
        with open(os.path.join(FIXTURES, 'nxos_lldp_not_advertised.txt'), encoding='utf-8') as f:
            text = f.read()
        raw = nd._parse_cisco_lldp_detail(text, 'LEAF', None)
        n = nd._finalize_neighbor(raw[0])
        self.assertEqual(n['hostname'], '0050.5689.12ab')
        self.assertEqual(n['remote_port'], 'Eth1/10')

    def test_nxos_lldp_chassis_only_block(self):
        with open(os.path.join(FIXTURES, 'nxos_lldp_chassis_only.txt'), encoding='utf-8') as f:
            text = f.read()
        raw = nd._parse_cisco_lldp_detail(text, 'LEAF', None)
        self.assertEqual(len(raw), 1)
        n = nd._finalize_neighbor(raw[0])
        self.assertEqual(n['hostname'], '748f.c2dd.ee11')
        self.assertEqual(n['local_port'], 'Eth1/48')
        self.assertEqual(n['remote_port'], 'Eth1/1')

    def test_nxos_lldp_disabled_yields_no_neighbors(self):
        with open(os.path.join(FIXTURES, 'nxos_lldp_disabled.txt'), encoding='utf-8') as f:
            text = f.read()
        self.assertTrue(nd.cisco_neighbor_collection_disabled(text))
        self.assertEqual(nd._parse_cisco_lldp_brief(text, 'LEAF', None), [])
        self.assertEqual(nd._parse_cisco_lldp_detail(text, 'LEAF', None), [])

    def test_nxos_cdp_disabled_yields_no_neighbors(self):
        with open(os.path.join(FIXTURES, 'nxos_cdp_disabled.txt'), encoding='utf-8') as f:
            text = f.read()
        self.assertTrue(nd.cisco_neighbor_collection_disabled(text))
        self.assertEqual(nd._parse_cisco_cdp_brief(text, 'LEAF', None), [])
        self.assertEqual(nd._parse_cisco_cdp_detail(text, 'LEAF', None), [])

    def test_junos_lldp_detail(self):
        with open(os.path.join(FIXTURES, 'junos_lldp_detail.txt'), encoding='utf-8') as f:
            text = f.read()
        neighbors = nd._parse_juniper_lldp_detail(text, 'CORE', None)
        self.assertTrue(any('edge-junos-04' in n['hostname'].lower() for n in neighbors))

    def test_junos_lldp_brief_older_table(self):
        with open(os.path.join(FIXTURES, 'junos_lldp_brief.txt'), encoding='utf-8') as f:
            text = f.read()
        neighbors = nd._parse_juniper_lldp_brief(text, 'QFX-CORE', None)
        hosts = {n['hostname'] for n in neighbors}
        self.assertIn('DIST-QFX-01', hosts)
        self.assertIn('SPINE-QFX-02', hosts)
        self.assertNotIn('-', hosts)
        dist = next(n for n in neighbors if n['hostname'] == 'DIST-QFX-01')
        self.assertEqual(dist['local_port'], 'ge-0/0/0')
        self.assertEqual(dist['remote_port'], 'ge-0/0/1')

    def test_iosxe_lldp_brief_holdtime_not_used_as_port(self):
        with open(os.path.join(FIXTURES, 'iosxe_lldp_brief.txt'), encoding='utf-8') as f:
            text = f.read()
        neighbors = nd._parse_cisco_lldp_brief(text, 'CORE-XE', None)
        hosts = {n['hostname'] for n in neighbors}
        self.assertIn('DIST-C9300', hosts)
        dist = next(n for n in neighbors if n['hostname'] == 'DIST-C9300')
        self.assertEqual(dist['local_port'], 'Gi1/0/1')
        self.assertEqual(dist['remote_port'], 'Gi1/0/48')
        self.assertNotEqual(dist['remote_port'], '120')

    def test_ios_15x_lldp_brief(self):
        with open(os.path.join(FIXTURES, 'ios_lldp_brief.txt'), encoding='utf-8') as f:
            text = f.read()
        neighbors = nd._parse_cisco_lldp_brief(text, 'CORE-IOS', None)
        dist = next(n for n in neighbors if n['hostname'] == 'DIST-SW01')
        self.assertEqual(dist['local_port'], 'Gi0/1')
        self.assertEqual(dist['remote_port'], 'Gi0/2')

    def test_nxos_lldp_brief_table(self):
        with open(os.path.join(FIXTURES, 'nxos_lldp_brief.txt'), encoding='utf-8') as f:
            text = f.read()
        neighbors = nd._parse_cisco_lldp_brief(text, 'LEAF', None)
        hosts = {n['hostname'] for n in neighbors}
        self.assertIn('SPINE-NXOS-01', hosts)
        spine = next(n for n in neighbors if n['hostname'] == 'SPINE-NXOS-01')
        self.assertEqual(spine['local_port'], 'Eth1/1')
        self.assertEqual(spine['remote_port'], 'Eth1/2')


class TestHostnameResolver(unittest.TestCase):
    def test_resolve_hostname_nxos_banner(self):
        from modules.network_base import resolve_device_hostname, _hostname_from_ver_output

        with open(os.path.join(FIXTURES, 'nxos_show_version.txt'), encoding='utf-8') as f:
            ver = f.read()
        parsed = _hostname_from_ver_output(ver, 'cisco_nxos')
        self.assertEqual(parsed, 'n9k-core-01')

        class FakeConn:
            def find_prompt(self):
                return 'N9K-CORE-01#'

            def send_command(self, cmd, read_timeout=15):
                return 'hostname N9K-CORE-01'

        host = resolve_device_hostname(FakeConn(), ver, '10.0.0.1', 'cisco_nxos')
        self.assertEqual(host, 'n9k-core-01')
        self.assertNotIn('software', host)
        self.assertNotIn('http', host)

    def test_banner_blob_rejected(self):
        from modules.network_base import safe_node_name

        blob = 'cisco nexus operating system (nx-os) software tac support http://www.cisco.com'
        self.assertIsNone(safe_node_name(blob))


class TestDiscoveryMapHtml(unittest.TestCase):
    def test_discovery_html_link_inventory(self):
        import tempfile
        from utils.discovery_map_formatter import generate_discovery_html

        nodes = [
            {'id': 'sw1', 'ip': '10.0.0.1', 'platform': 'Nexus', 'depth': 0, 'is_scanned': True},
            {'id': 'sw2', 'ip': '10.0.0.2', 'platform': 'Nexus', 'depth': 1, 'is_scanned': False},
        ]
        edges = [{
            'from': 'sw1', 'to': 'sw2', 'f_port': 'Eth1/1', 't_port': 'Eth1/2', 'protocol': 'CDP',
        }]
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as tf:
            path = tf.name
        try:
            generate_discovery_html(path, nodes, edges)
            with open(path, encoding='utf-8') as f:
                html = f.read()
            self.assertIn('__TOPO_LINKS__', html)
            self.assertIn('Link Inventory', html)
            self.assertIn('enabled: false', html)
            self.assertNotIn('fonts.googleapis.com', html)
        finally:
            os.unlink(path)


class TestDiscoveryPlatformFromCdp(unittest.TestCase):
    def test_nexus_platform_not_junos(self):
        dtype = nd._platform_from_neighbor_string('Nexus 9000 Switch')
        self.assertEqual(dtype, 'cisco_nxos')


class TestDiscoverySeeds(unittest.TestCase):
    def test_crawl_seed_tuple_is_two_values(self):
        """Regression: seeds are (host, device_type), not queue 3-tuples."""
        seeds = [('10.0.0.1', 'cisco_ios')]
        nodes = {}
        for host, dtype in seeds:
            nodes[host.lower()] = {'id': host, 'device_type': dtype}
        self.assertEqual(nodes['10.0.0.1']['device_type'], 'cisco_ios')

    def test_live_crawl_entry_does_not_unpack_error(self):
        from unittest.mock import MagicMock, patch

        seeds = [('10.0.0.1', 'cisco_ios')]
        credentials = {'username': 'u', 'password': 'p', 'secret': ''}
        mock_conn = MagicMock()
        mock_conn.find_prompt.return_value = 'N9K-CORE-01#'
        _nxos_ver = open(os.path.join(FIXTURES, 'nxos_show_version.txt'), encoding='utf-8').read()

        def _mock_cmd(cmd, read_timeout=60):
            if 'version' in cmd.lower():
                return _nxos_ver
            return 'hostname N9K-CORE-01'

        mock_conn.send_command.side_effect = _mock_cmd

        with patch('modules.plugins.network_discovery.safe_connection') as mock_sc:
            mock_sc.return_value.__enter__.return_value = mock_conn
            mock_sc.return_value.__exit__.return_value = None
            with patch('modules.plugins.network_discovery._fetch_neighbors', return_value=([], 'none_collected')):
                result = nd.crawl_network_multi_seed(
                    seeds, credentials, 1, 'Both', {}, log_func=None,
                )
        self.assertGreaterEqual(len(result.get('devices', [])), 1)
        ids = {d.get('id', '').lower() for d in result.get('devices', [])}
        self.assertIn('n9k-core-01', ids)


class TestDiscoveryDemo(unittest.TestCase):
    def test_demo_mode_plugin(self):
        plugin = nd.NetworkDiscoveryPlugin()
        result = plugin.execute(
            {'host': '10.0.0.1'},
            {'username': 'u', 'password': 'p'},
            {'seed_hosts': ['10.0.0.1'], 'max_depth': 2, 'demo_mode': True},
            {},
            log_func=None,
        )
        self.assertEqual(result['status'], 'success')
        data = result['data']
        self.assertGreaterEqual(len(data['devices']), 3)
        self.assertGreaterEqual(len(data['links']), 2)
        self.assertTrue(os.path.exists(data['topology_path']))

    def test_validate_plugin(self):
        ok, errors = nd.validate_plugin()
        self.assertTrue(ok, errors)
        self.assertTrue(hasattr(nd, 'NetworkDiscoveryPlugin'))


class TestDiscoveryApiJobStatus(unittest.TestCase):
    def test_job_status_error_when_plugin_returns_error(self):
        import time
        from unittest.mock import patch

        import vlan_checker_web as web

        web._discovery_jobs.clear()
        err_result = {
            'device': 'unknown',
            'status': 'error',
            'data': {},
            'error': 'No valid seed hosts',
        }

        import tempfile
        from tests.execute_test_helpers import seed_execute_vault
        vault_dir = tempfile.mkdtemp(prefix='nst-disc-vault-')
        cid = seed_execute_vault(web, vault_dir)
        with patch('modules.plugins.network_discovery.NetworkDiscoveryPlugin') as mock_cls:
            mock_cls.return_value.execute.return_value = err_result
            with web.app.test_client() as client:
                resp = client.post(
                    '/api/discovery/run',
                    json={
                        'seed_hosts': ['10.0.0.1'],
                        'target_source': 'discovery_seeds',
                        'credential_id': cid,
                        'demo_mode': False,
                    },
                    environ_base={'REMOTE_ADDR': '127.0.0.1'},
                )
                self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
                job_id = resp.get_json()['job_id']
                final = None
                for _ in range(30):
                    time.sleep(0.05)
                    st = client.get(
                        f'/api/discovery/status/{job_id}',
                        environ_base={'REMOTE_ADDR': '127.0.0.1'},
                    )
                    body = st.get_json()
                    if body.get('status') != 'running':
                        final = body
                        break
                self.assertIsNotNone(final)
                self.assertEqual(final['status'], 'error')
                self.assertIn('seed', (final.get('error') or '').lower())


class TestDiscoveryCancel(unittest.TestCase):
    def test_cancel_check_returns_partial_without_ssh(self):
        result = nd.crawl_network_multi_seed(
            [('10.0.0.1', 'cisco_ios')],
            {'username': 'u', 'password': 'p'},
            1,
            'Both',
            {},
            cancel_check=lambda: True,
        )
        self.assertTrue(result['cancelled'])
        self.assertTrue(result['partial'])
        self.assertEqual(result['collection_status'], 'cancelled')
        self.assertTrue(result.get('devices'))
        inv_path = result.get('inventory_json_path')
        self.assertTrue(inv_path and os.path.exists(inv_path))
        import json
        dumped = json.load(open(inv_path, encoding='utf-8'))
        self.assertEqual(dumped.get('collection_status'), 'cancelled')
        self.assertTrue(dumped.get('cancelled'))
        self.assertTrue(dumped.get('partial'))
        self.assertIn('devices', dumped)
        self.assertIn('links', dumped)


class TestDiscoveryApiHonesty(unittest.TestCase):
    def test_nodes_to_api_devices_identity_conflict(self):
        devices = nd._nodes_to_api_devices([{
            'id': 'DUP',
            'ip': '10.1.1.1',
            'identity_conflict': True,
            'neighbor_evidence': 'none_collected',
            'is_scanned': True,
            'scan_state': 'scanned',
        }])
        self.assertTrue(devices[0]['identity_conflict'])
        self.assertEqual(devices[0]['neighbor_evidence'], 'none_collected')

    def test_edges_to_api_links_honesty_fields(self):
        links = nd._edges_to_api_links([{
            'from': 'A', 'to': 'B', 'f_port': 'Po1', 't_port': 'Po2',
            'protocol': 'LLDP', 'confidence': 'High', 'one_sided': False,
            'spoof_risk': False, 'bundle_kind': 'bundle',
            'sources': ['CDP', 'LLDP'], 'not_physical': False,
        }])
        self.assertEqual(links[0]['confidence'], 'High')
        self.assertEqual(links[0]['bundle_kind'], 'bundle')
        self.assertEqual(links[0]['sources'], ['CDP', 'LLDP'])
        self.assertFalse(links[0]['one_sided'])

    def test_demo_inventory_json_has_collection_status(self):
        import json
        plugin = nd.NetworkDiscoveryPlugin()
        result = plugin.execute(
            {'host': '10.0.0.1'},
            {'username': 'u', 'password': 'p'},
            {'seed_hosts': ['10.0.0.1'], 'max_depth': 2, 'demo_mode': True},
            {},
            log_func=None,
        )
        data = result['data']
        self.assertEqual(data.get('collection_status'), 'complete')
        self.assertTrue(data.get('demo_mode'))
        path = data.get('inventory_json_path')
        self.assertTrue(path and os.path.exists(path))
        dumped = json.load(open(path, encoding='utf-8'))
        self.assertEqual(dumped.get('collection_status'), 'complete')
        self.assertTrue(dumped.get('demo_mode'))
        self.assertIn('devices', dumped)
        self.assertIn('links', dumped)
        self.assertGreaterEqual(len(dumped['devices']), 3)


class TestDiscoveryFailureClass(unittest.TestCase):
    def test_auth_and_timeout(self):
        from utils.discovery_profiles import classify_discovery_failure
        self.assertEqual(classify_discovery_failure(Exception('Authentication failed')), 'auth_denied')
        self.assertEqual(classify_discovery_failure(Exception('TCP connection timed out')), 'timeout')
        self.assertEqual(classify_discovery_failure(Exception('socket error')), 'failed')


if __name__ == '__main__':
    unittest.main()
