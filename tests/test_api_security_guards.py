"""Localhost guards on admin, plugin, debug, and shutdown routes."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_security import client_is_localhost, resolve_web_bind_host


class TestClientIsLocalhost(unittest.TestCase):
    def test_empty_remote_addr_is_not_localhost(self):
        from flask import Flask
        from utils import api_security as sec

        app = Flask(__name__)

        @app.route('/t')
        def t():
            return 'yes' if client_is_localhost() else 'no'

        c = app.test_client()
        r = c.get('/t', environ_base={'REMOTE_ADDR': ''})
        self.assertEqual(r.data.decode(), 'no')

        r2 = c.get('/t', environ_base={'REMOTE_ADDR': '127.0.0.1'})
        self.assertEqual(r2.data.decode(), 'yes')

        r3 = c.get('/t', environ_base={'REMOTE_ADDR': '10.9.9.9'})
        self.assertEqual(r3.data.decode(), 'no')
        self.assertIs(sec.client_is_localhost, client_is_localhost)


class TestResolveWebBindHost(unittest.TestCase):
    def test_default_is_loopback(self):
        self.assertEqual(resolve_web_bind_host(requested='', allow_nonlocal_env=''), '127.0.0.1')
        self.assertEqual(resolve_web_bind_host(requested='127.0.0.1'), '127.0.0.1')

    def test_wildcard_refused_without_override(self):
        with self.assertRaises(ValueError) as ctx:
            resolve_web_bind_host(requested='0.0.0.0', allow_nonlocal_env='')
        self.assertIn('NST_ALLOW_NONLOCAL_BIND', str(ctx.exception))
        with self.assertRaises(ValueError):
            resolve_web_bind_host(requested='192.168.1.10', allow_nonlocal_env='')

    def test_wildcard_allowed_with_override(self):
        self.assertEqual(
            resolve_web_bind_host(requested='0.0.0.0', allow_nonlocal_env='1'),
            '0.0.0.0',
        )


class TestAdminRouteGuards(unittest.TestCase):
    def setUp(self):
        from vlan_checker_web import app
        app.config['TESTING'] = True
        self.client = app.test_client()

    def _remote(self, method, path, **kwargs):
        kwargs.setdefault('environ_base', {'REMOTE_ADDR': '203.0.113.10'})
        return getattr(self.client, method)(path, **kwargs)

    def test_debug_status_rejects_non_loopback(self):
        r = self._remote('get', '/debug_status')
        self.assertEqual(r.status_code, 403)

    def test_debug_status_allows_loopback(self):
        r = self.client.get('/debug_status', environ_base={'REMOTE_ADDR': '127.0.0.1'})
        self.assertEqual(r.status_code, 200)

    def test_plugin_upload_rejects_non_loopback(self):
        r = self._remote('post', '/api/plugins/upload')
        self.assertEqual(r.status_code, 403)

    def test_plugin_reload_rejects_non_loopback(self):
        r = self._remote('post', '/api/plugins/reload')
        self.assertEqual(r.status_code, 403)

    def test_plugin_debug_rejects_non_loopback(self):
        r = self._remote('get', '/api/plugins/debug')
        self.assertEqual(r.status_code, 403)

    def test_shutdown_rejects_non_loopback(self):
        r = self._remote('post', '/api/shutdown')
        self.assertEqual(r.status_code, 403)

    def test_execute_rejects_non_loopback(self):
        r = self._remote(
            'post',
            '/api/execute',
            json={'action': 'connectivity', 'inventory': '10.0.0.1,cisco_ios'},
        )
        self.assertEqual(r.status_code, 403)

    def test_mutation_apis_reject_non_loopback(self):
        paths = [
            ('post', '/api/vlan/validate', {'json': {}}),
            ('post', '/api/interface/discover', {'json': {'host': '10.0.0.1'}}),
            ('post', '/api/interface/validate', {'json': {'host': '10.0.0.1'}}),
            ('post', '/api/interface/deploy', {'json': {'host': '10.0.0.1'}}),
            ('post', '/api/discovery/run', {'json': {}}),
            ('post', '/api/discovery/cancel/job1', {'json': {}}),
            ('post', '/api/ping_scan', {'json': {}}),
            ('post', '/api/stp/run', {'json': {}}),
            ('post', '/api/standards/run', {'json': {}}),
            ('post', '/api/health-check/run', {'json': {'quick': True}}),
            ('post', '/api/templates/save', {'json': {'name': 'x.j2', 'content': ''}}),
            ('post', '/api/templates/render', {'json': {'template_name': 'x.j2'}}),
            ('post', '/api/extract_docs', {'json': {}}),
            ('post', '/api/control-plane/tasks/t1/cancel', {'json': {}}),
            ('post', '/api/standards/upload', {}),
            ('get', '/api/health-check/run', {}),
            ('post', '/api/interface/restore-guide', {'json': {'backup_path': 'x'}}),
            ('post', '/api/path-trace', {'json': {'mac': 'aa:bb:cc:dd:ee:ff'}}),
            ('get', '/api/topology/issues', {}),
            ('post', '/api/inventory/preview', {'json': {'text': '10.0.0.1,cisco_ios'}}),
            ('post', '/api/inventory/commit', {'json': {'text': '10.0.0.1,cisco_ios', 'confirm': True}}),
            ('post', '/api/inventory/restore', {'json': {'bak': 'inventory.txt.bak.x', 'confirm': True}}),
            ('post', '/api/inventory/source', {'json': {'text': '10.0.0.1,cisco_ios'}}),
            ('get', '/api/jobs', {}),
            ('get', '/api/jobs/abc', {}),
            ('get', '/api/ping-scan/last', {}),
            ('get', '/api/ping-scan/report', {}),
            ('get', '/api/stp/status/x', {}),
            ('get', '/api/stp/report/x', {}),
        ]
        for method, path, extra in paths:
            r = self._remote(method, path, **extra)
            self.assertEqual(r.status_code, 403, msg=f'{path} expected 403, got {r.status_code}')

    def test_sensitive_gets_reject_non_loopback(self):
        for path in ('/api/logs', '/api/inventory', '/api/plugins/list', '/'):
            r = self._remote('get', path)
            self.assertEqual(r.status_code, 403, msg=f'{path} expected 403, got {r.status_code}')

    def test_health_probe_allows_non_loopback(self):
        r = self._remote('get', '/health')
        self.assertEqual(r.status_code, 200)

    def test_cross_origin_post_rejected_even_from_loopback(self):
        r = self.client.post(
            '/api/execute',
            json={'action': 'connectivity', 'inventory': '10.0.0.1,cisco_ios'},
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
            headers={'Origin': 'http://evil.example'},
        )
        self.assertEqual(r.status_code, 403)

    def test_plugin_upload_disabled_always(self):
        import os
        from unittest.mock import patch
        r = self.client.post(
            '/api/plugins/upload',
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
        )
        self.assertEqual(r.status_code, 403)
        data = r.get_json()
        self.assertIn('Runtime plugin upload is disabled', data.get('error', ''))
        self.assertFalse(data.get('runtime_upload', True))
        with patch.dict(os.environ, {'NST_ENABLE_PLUGIN_UPLOAD': '1', 'NST_DISABLE_PLUGIN_UPLOAD': '0'}):
            r2 = self.client.post(
                '/api/plugins/upload',
                environ_base={'REMOTE_ADDR': '127.0.0.1'},
            )
            self.assertEqual(r2.status_code, 403)

    def test_vlan_validate_allows_loopback(self):
        r = self.client.post(
            '/api/vlan/validate',
            json={},
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
        )
        self.assertNotEqual(r.status_code, 403)


if __name__ == '__main__':
    unittest.main()
