"""Best-possible Flask E2E for operator APIs without Playwright or live SSH."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.session_cred_cache import clear_session_credentials


class TestFlaskOperatorE2E(unittest.TestCase):
    def setUp(self):
        import tempfile
        import vlan_checker_web as web
        from tests.execute_test_helpers import EXECUTE_CREDENTIAL_ID, seed_execute_vault
        self.web = web
        self.client = web.app.test_client()
        self.env = {'REMOTE_ADDR': '127.0.0.1'}
        self._vault_tmp = tempfile.mkdtemp(prefix='nst-e2e-vault-')
        self.cred_id = seed_execute_vault(web, self._vault_tmp)
        assert self.cred_id == EXECUTE_CREDENTIAL_ID
        clear_session_credentials()

    def tearDown(self):
        import shutil
        clear_session_credentials()
        shutil.rmtree(getattr(self, '_vault_tmp', ''), ignore_errors=True)

    def test_health_and_version(self):
        health = self.client.get('/health')
        self.assertEqual(health.status_code, 200)
        self.assertIn(b'OK', health.data)
        ver = self.client.get('/api/version', environ_base=self.env)
        self.assertEqual(ver.status_code, 200)
        body = ver.get_json()
        self.assertTrue(body.get('version'))
        # Accept any 7.x product line (do not pin a stale minor like 7.0)
        self.assertRegex(str(body.get('version')), r'^7\.\d+')

    def test_control_plane_list_and_missing_cancel(self):
        listed = self.client.get('/api/control-plane/tasks', environ_base=self.env)
        self.assertEqual(listed.status_code, 200)
        self.assertIn('tasks', listed.get_json())
        missing = self.client.post(
            '/api/control-plane/tasks/no-such-task/cancel',
            environ_base=self.env,
        )
        self.assertEqual(missing.status_code, 404)

    def test_session_credentials_redacted_and_remote_denied(self):
        posted = self.client.post(
            '/api/session/credentials',
            json={'username': 'op', 'password': 's3cret-value', 'label': 'lab'},
            environ_base=self.env,
        )
        self.assertEqual(posted.status_code, 200)
        got = self.client.get('/api/session/credentials', environ_base=self.env)
        self.assertEqual(got.status_code, 200)
        body = got.get_json()
        blob = str(body)
        self.assertNotIn('s3cret-value', blob)
        self.assertTrue(body.get('has_password'))
        self.assertEqual(body.get('username'), 'op')
        remote = self.client.get(
            '/api/session/credentials',
            environ_base={'REMOTE_ADDR': '203.0.113.10'},
        )
        self.assertEqual(remote.status_code, 403)

    def test_vlan_validate_juniper_rename_no_ssh(self):
        resp = self.client.post(
            '/api/vlan/validate',
            json={
                'action': 'rename_vlan',
                'credential_id': self.cred_id,
                'inventory': '10.0.0.1,juniper_junos,lab',
                'target_mode': 'bulk',
                'vlan_id': '10',
                'vlan_name': 'NEW',
            },
            environ_base=self.env,
        )
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        payload = resp.get_json()
        data = payload.get('data') or payload
        self.assertEqual(data.get('overall_status'), 'failed')
        self.assertFalse(data['validation_results']['vendor_syntax']['passed'])

    def test_interface_validate_requires_proposed_config(self):
        resp = self.client.post(
            '/api/interface/validate',
            json={
                'host': '10.0.0.1',
                'credential_id': self.cred_id,
                'device_type': 'cisco_ios',
            },
            environ_base=self.env,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Proposed configuration', resp.get_json().get('error', ''))

    def test_path_trace_reconstructs_from_body_no_invented_hop(self):
        resp = self.client.post(
            '/api/path-trace',
            json={
                'mac': 'aa:bb:cc:dd:ee:ff',
                'mac_hits': [
                    {'hostname': 'CORE', 'port': 'Eth1/1', 'found': True, 'vlan': '20'},
                    {'hostname': 'GHOST', 'port': 'Eth9/9', 'found': True},
                ],
                'edges': [
                    {'from': 'CORE', 'to': 'DIST', 'f_port': 'Eth1/1', 't_port': 'Eth1/1', 'protocol': 'cdp'},
                ],
            },
            environ_base=self.env,
        )
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        path = (resp.get_json() or {}).get('data') or {}
        self.assertEqual([h['hostname'] for h in path.get('hops') or []], ['CORE'])
        self.assertEqual(path.get('unlinked_hits'), [{'hostname': 'GHOST', 'port': 'Eth9/9'}])
        self.assertIn('not a forwarding path', (path.get('path_note') or '').lower())

    def test_topology_issues_localhost_ok(self):
        resp = self.client.get('/api/topology/issues', environ_base=self.env)
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertIn('issues', body)
        self.assertIn('not a certified cable', (body.get('note') or '').lower())

    def test_vlan_validate_golden_blocks_1002(self):
        resp = self.client.post(
            '/api/vlan/validate',
            json={
                'action': 'add_vlan',
                'credential_id': self.cred_id,
                'inventory': '10.0.0.1,cisco_ios,lab',
                'target_mode': 'bulk',
                'vlan_id': '1002',
                'vlan_name': 'RESERVED',
            },
            environ_base=self.env,
        )
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        data = (resp.get_json() or {}).get('data') or {}
        self.assertEqual(data.get('overall_status'), 'failed')
        self.assertFalse(data['validation_results']['golden_config']['passed'])


if __name__ == '__main__':
    unittest.main()
