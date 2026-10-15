"""Plugin lifecycle: HTTP upload stays off; load fail-closed; reload is local and audited."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.plugin_registry import PluginRegistry, get_registry

_SAFE_META = """
METADATA = {
    'plugin_id': 'rb_p1_safe_probe',
    'display_name': 'Safe',
    'version': '1.0.0',
    'category': 'audit',
}
def run(*args, **kwargs):
    return {'status': 'ok', 'data': {}}
"""

_EVIL_META = """
METADATA = {
    'plugin_id': 'rb_p1_evil_probe',
    'display_name': 'Evil',
    'version': '1.0.0',
    'category': 'audit',
}
def run(*args, **kwargs):
    import os
    os.system('id')
    return {}
"""

_NO_META = """
def run(*args, **kwargs):
    return {}
"""


class TestPluginAstDenylist(unittest.TestCase):
    def test_re_compile_is_not_banned(self):
        src = 'import re\nMETADATA={"plugin_id":"x","display_name":"X","version":"1","category":"audit"}\nre.compile(r"a")\n'
        self.assertIsNone(PluginRegistry.banned_content_reason(src))

    def test_datetime_import_trick_is_not_banned(self):
        src = "x = __import__('datetime').datetime.now()\n"
        self.assertIsNone(PluginRegistry.banned_content_reason(src))

    def test_os_system_call_is_banned(self):
        self.assertEqual(PluginRegistry.banned_content_reason(_EVIL_META), 'os.system')


class TestPluginLoadFailClosed(unittest.TestCase):
    def setUp(self):
        self.reg = get_registry()
        self._before = set(self.reg._plugins)

    def _write(self, src):
        fd, path = tempfile.mkstemp(suffix='.py')
        os.close(fd)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(src)
        return path

    def tearDown(self):
        extra = set(self.reg._plugins) - self._before
        for pid in extra:
            self.reg._plugins.pop(pid, None)
            sys.modules.pop(f'plugin_{pid}', None)

    def test_malicious_disk_drop_is_not_executed(self):
        path = self._write(_EVIL_META)
        try:
            with self.assertRaises(ValueError) as ctx:
                self.reg._load_plugin(path)
            self.assertIn('Untrusted', str(ctx.exception))
            self.assertNotIn('rb_p1_evil_probe', self.reg._plugins)
        finally:
            os.unlink(path)

    def test_malformed_plugin_missing_metadata(self):
        path = self._write(_NO_META)
        try:
            with self.assertRaises(ValueError) as ctx:
                self.reg._load_plugin(path)
            self.assertIn('METADATA', str(ctx.exception))
        finally:
            os.unlink(path)

    def test_safe_plugin_executes(self):
        path = self._write(_SAFE_META)
        try:
            self.reg._load_plugin(path)
            rec = self.reg.get_plugin('rb_p1_safe_probe')
            self.assertIsNotNone(rec)
            out = self.reg.execute(
                'rb_p1_safe_probe',
                {'host': '10.0.0.1'},
                {'username': 'u', 'password': 'p'},
                {},
                {},
            )
            self.assertEqual(out.get('status'), 'ok')
        finally:
            os.unlink(path)


class TestPluginReloadApi(unittest.TestCase):
    def setUp(self):
        from vlan_checker_web import app
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.local = {'REMOTE_ADDR': '127.0.0.1'}

    def test_reload_rejects_nonlocal(self):
        r = self.client.post(
            '/api/plugins/reload',
            json={},
            environ_base={'REMOTE_ADDR': '203.0.113.10'},
        )
        self.assertEqual(r.status_code, 403)

    def test_reload_loopback_records_trust_model(self):
        with patch('vlan_checker_web.add_log') as log:
            r = self.client.post(
                '/api/plugins/reload',
                json={'plugins_dir': '/tmp/evil-plugins'},
                environ_base=self.local,
            )
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body.get('status'), 'reloaded')
        self.assertFalse(body.get('runtime_upload', True))
        self.assertEqual(body.get('install_model'), 'offline_local_directory')
        self.assertEqual(body.get('execution_model'), 'in_process')
        self.assertFalse(body.get('sandbox'))
        self.assertIn('not a sandbox', (body.get('trust_warning') or '').lower())
        joined = ' '.join(str(c) for c in log.call_args_list)
        self.assertIn('Registry reload requested', joined)
        self.assertNotIn('/tmp/evil-plugins', get_registry().plugins_dir.replace('\\', '/'))

    def test_list_includes_trust_warning(self):
        r = self.client.get('/api/plugins/list', environ_base=self.local)
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn('not a sandbox', (data.get('trust_warning') or '').lower())
        self.assertGreaterEqual(data.get('count', 0), 10)

    def test_upload_still_403(self):
        r = self.client.post('/api/plugins/upload', environ_base=self.local)
        self.assertEqual(r.status_code, 403)


class TestReloadUiIsDeliberate(unittest.TestCase):
    def test_html_posts_reload_with_confirm(self):
        html = open(
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'modules', 'web', 'templates', 'index.html'),
            encoding='utf-8',
        ).read()
        self.assertIn('/api/plugins/reload', html)
        self.assertIn("method: 'POST'", html)
        self.assertIn('not a sandbox', html)
        fn = html.split('async function reloadPlugins', 1)[1].split('function renderPluginList', 1)[0]
        self.assertIn('confirm(', fn)
        self.assertIn('/api/plugins/reload', fn)


if __name__ == '__main__':
    unittest.main()
