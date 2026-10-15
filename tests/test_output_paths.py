"""Tests for centralized output path layout."""
import json
import os
import tempfile
import unittest
from unittest import mock

from utils import output_paths


class TestOutputPaths(unittest.TestCase):
    def setUp(self):
        output_paths._DATA_ROOT = None

    def tearDown(self):
        output_paths._DATA_ROOT = None

    def test_slugify(self):
        self.assertEqual(output_paths.slugify('aa:bb:cc'), 'aa_bb_cc')
        self.assertTrue(output_paths.slugify(''))

    def test_prepare_run_output_unique_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(output_paths, 'get_data_root', return_value=tmp):
                a = output_paths.prepare_run_output('mac_trace', 'aa-bb-cc')
                b = output_paths.prepare_run_output('mac_trace', 'aa-bb-cc')
            self.assertNotEqual(a['run_dir'], b['run_dir'])
            self.assertTrue(os.path.isdir(a['run_dir']))
            self.assertIn('outputs', a['run_dir'])
            self.assertIn('mac_trace', a['run_dir'])

    def test_data_root_not_install_root(self):
        with tempfile.TemporaryDirectory() as install:
            with tempfile.TemporaryDirectory() as data:
                with mock.patch.object(output_paths, 'get_install_root', return_value=install):
                    with mock.patch.dict(os.environ, {'NST_DATA_DIR': data}, clear=False):
                        output_paths._DATA_ROOT = None
                        root = output_paths.get_data_root()
                self.assertEqual(os.path.abspath(root), os.path.abspath(data))
                self.assertNotEqual(os.path.abspath(root), os.path.abspath(install))

    def test_write_run_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(output_paths, 'get_data_root', return_value=tmp):
                paths = output_paths.prepare_run_output('description_search', 'core')
                output_paths.write_run_manifest(paths, {'needle': 'core'})
            with open(paths['manifest_path'], encoding='utf-8') as f:
                doc = json.load(f)
            self.assertEqual(doc['category'], 'description_search')
            self.assertEqual(doc['needle'], 'core')


if __name__ == '__main__':
    unittest.main()
