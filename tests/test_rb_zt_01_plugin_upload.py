"""RB-ZT-01: runtime HTTP plugin upload is disabled; trusted local load remains."""
from __future__ import annotations

import io
import os
import tempfile
import unittest
import zipfile

from modules.plugin_registry import PluginRegistry
from utils.api_security import plugin_upload_is_enabled
from utils.output_paths import get_scratch_dir

_META = """
METADATA = {
    'plugin_id': 'evil_probe',
    'display_name': 'Evil',
    'version': '1.0.0',
    'category': 'audit',
}
def run(*args, **kwargs):
    return {}
"""


class TestRuntimeUploadDisabled(unittest.TestCase):
    def setUp(self):
        from vlan_checker_web import app
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.local = {'REMOTE_ADDR': '127.0.0.1'}

    def _post_upload(self, filename, data=b'print(1)\n', extra_headers=None):
        kw = {
            'data': {'file': (io.BytesIO(data), filename)},
            'content_type': 'multipart/form-data',
            'environ_base': dict(self.local),
        }
        if extra_headers:
            kw['headers'] = extra_headers
        return self.client.post('/api/plugins/upload', **kw)

    def test_upload_enabled_flag_is_false(self):
        self.assertFalse(plugin_upload_is_enabled())

    def test_loopback_upload_is_403_and_does_not_write_scratch(self):
        scratch = get_scratch_dir()
        marker = 'rb_zt_01_must_not_land.py'
        path = os.path.join(scratch, marker)
        if os.path.isfile(path):
            os.unlink(path)
        r = self._post_upload(marker, _META.encode())
        self.assertEqual(r.status_code, 403)
        body = r.get_json()
        self.assertFalse(body.get('runtime_upload'))
        self.assertEqual(body.get('install_model'), 'offline_local_directory')
        self.assertIn('disabled', body.get('error', '').lower())
        self.assertFalse(os.path.isfile(path))
        self.assertNotIn('password', str(body).lower())

    def test_path_traversal_filename_rejected(self):
        r = self._post_upload('../../etc/passwd.py', _META.encode())
        self.assertEqual(r.status_code, 403)
        self.assertFalse(r.get_json().get('runtime_upload'))

    def test_absolute_path_filename_rejected(self):
        r = self._post_upload('/tmp/evil.py', _META.encode())
        self.assertEqual(r.status_code, 403)

    def test_null_byte_and_backslash_rejected(self):
        r = self._post_upload('evil.py\x00.exe', _META.encode())
        self.assertEqual(r.status_code, 403)
        r2 = self._post_upload('..\\..\\windows\\evil.py', _META.encode())
        self.assertEqual(r2.status_code, 403)

    def test_symlink_looking_name_rejected(self):
        r = self._post_upload('link.py', _META.encode())
        self.assertEqual(r.status_code, 403)

    def test_zip_and_case_variant_extension_rejected(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('../evil.py', _META)
        r = self._post_upload('plugin.zip', buf.getvalue())
        self.assertEqual(r.status_code, 403)
        r2 = self._post_upload('plugin.PY', _META.encode())
        self.assertEqual(r2.status_code, 403)
        r3 = self._post_upload('plugin.py.exe', b'MZ')
        self.assertEqual(r3.status_code, 403)

    def test_oversized_payload_rejected_without_promote(self):
        r = self._post_upload('huge.py', b'x' * (2 * 1024 * 1024))
        self.assertEqual(r.status_code, 403)
        self.assertFalse(os.path.isfile(os.path.join(get_scratch_dir(), 'huge.py')))

    def test_duplicate_overwrite_name_rejected(self):
        r = self._post_upload('network_discovery.py', _META.encode())
        self.assertEqual(r.status_code, 403)
        from modules.plugin_registry import get_registry
        dest = os.path.join(get_registry().plugins_dir, 'network_discovery.py')
        self.assertTrue(os.path.isfile(dest))

    def test_malformed_json_body_still_403(self):
        r = self.client.post(
            '/api/plugins/upload',
            data='{not-json',
            content_type='application/json',
            environ_base=self.local,
        )
        self.assertEqual(r.status_code, 403)

    def test_cross_origin_upload_rejected(self):
        r = self.client.post(
            '/api/plugins/upload',
            data={'file': (io.BytesIO(_META.encode()), 'x.py')},
            content_type='multipart/form-data',
            environ_base=self.local,
            headers={'Origin': 'http://evil.example'},
        )
        self.assertEqual(r.status_code, 403)

    def test_list_shows_install_model_and_builtin_plugins(self):
        r = self.client.get('/api/plugins/list', environ_base=self.local)
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertFalse(data.get('runtime_upload'))
        self.assertEqual(data.get('install_model'), 'offline_local_directory')
        ids = {p.get('plugin_id') for p in data.get('plugins') or []}
        self.assertIn('interface_manager', ids)
        self.assertGreaterEqual(data.get('count', 0), 10)

    def test_reload_ignores_request_plugins_dir(self):
        r = self.client.post(
            '/api/plugins/reload',
            json={'plugins_dir': '/tmp/evil-plugins', 'path': '/etc'},
            environ_base=self.local,
        )
        self.assertEqual(r.status_code, 200)
        from modules.plugin_registry import get_registry
        self.assertNotIn('/tmp/evil-plugins', get_registry().plugins_dir.replace('\\', '/'))

    def test_blocked_attempt_logged_without_secret(self):
        from unittest.mock import patch
        with patch('vlan_checker_web.add_log') as log:
            r = self._post_upload('password=hunter2.py', _META.encode())
            self.assertEqual(r.status_code, 403)
            joined = ' '.join(str(c) for c in log.call_args_list)
            self.assertIn('Runtime upload blocked', joined)
            self.assertNotIn('hunter2', joined.lower())


class TestBannedImportsUnchanged(unittest.TestCase):
    def test_banned_imports_not_weakened(self):
        required = (
            'os.system', 'os.popen', 'subprocess.call', 'subprocess.Popen',
            'eval', 'exec', 'ctypes', 'pickle.loads', 'socket.socket',
        )
        for item in required:
            self.assertIn(item, PluginRegistry.BANNED_IMPORTS)

    def test_validate_upload_still_rejects_os_system(self):
        reg = PluginRegistry()
        fd, path = tempfile.mkstemp(suffix='.py')
        os.close(fd)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(_META + '\nos.system("id")\n')
            ok, msg = reg.validate_upload(path)
            self.assertFalse(ok)
            self.assertIn('os.system', msg.lower())
        finally:
            os.unlink(path)

    def test_validate_upload_rejects_missing_metadata(self):
        reg = PluginRegistry()
        fd, path = tempfile.mkstemp(suffix='.py')
        os.close(fd)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write('def run(*a, **k):\n    return {}\n')
            ok, msg = reg.validate_upload(path)
            self.assertFalse(ok)
            self.assertIn('METADATA', msg)
        finally:
            os.unlink(path)

    def test_promote_plugin_refuses(self):
        reg = PluginRegistry()
        fd, path = tempfile.mkstemp(suffix='.py')
        os.close(fd)
        try:
            ok, msg = reg.promote_plugin(path)
            self.assertFalse(ok)
            self.assertIn('disabled', msg.lower())
            self.assertTrue(os.path.isfile(path))
        finally:
            os.unlink(path)


if __name__ == '__main__':
    unittest.main()
