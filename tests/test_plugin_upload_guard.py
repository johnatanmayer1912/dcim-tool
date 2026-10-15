"""Plugin upload AST gate — not a security boundary, but must reject obvious RCE patterns."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.plugin_registry import PluginRegistry


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


class TestPluginUploadValidate(unittest.TestCase):
    def setUp(self):
        self.reg = PluginRegistry()

    def _write(self, body):
        fd, path = tempfile.mkstemp(suffix='.py')
        os.close(fd)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(body)
        return path

    def test_os_system_rejected(self):
        path = self._write(_META + '\nos.system("id")\n')
        try:
            ok, msg = self.reg.validate_upload(path)
            self.assertFalse(ok)
            self.assertIn('os.system', msg.lower())
        finally:
            os.unlink(path)

    def test_valid_metadata_accepted(self):
        path = self._write(_META)
        try:
            ok, msg = self.reg.validate_upload(path)
            self.assertTrue(ok, msg)
        finally:
            os.unlink(path)


if __name__ == '__main__':
    unittest.main()
