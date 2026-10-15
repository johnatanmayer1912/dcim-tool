"""Tests for organized search_it report folders."""
import json
import os
import tempfile
import unittest
from unittest import mock

from utils.search_report_output import prepare_search_run, slugify, write_run_manifest


class TestSearchReportOutput(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(slugify('aa:bb:cc'), 'aa_bb_cc')
        self.assertTrue(slugify(''))

    def test_prepare_search_run_creates_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch('utils.output_paths.get_data_root', return_value=tmp):
                paths = prepare_search_run('mac_trace', '00-11-22-aa-bb-cc')
            self.assertTrue(os.path.isdir(paths['run_dir']))
            self.assertTrue(paths['txt_path'].endswith('report.txt'))
            self.assertTrue(paths['html_path'].endswith('report.html'))
            self.assertIn('mac_trace', paths['run_dir'])
            write_run_manifest(paths, {'target_mac': '00:11:22:aa:bb:cc'})
            with open(paths['manifest_path'], encoding='utf-8') as f:
                doc = json.load(f)
            self.assertEqual(doc['category'], 'mac_trace')
            self.assertEqual(doc['target_mac'], '00:11:22:aa:bb:cc')


if __name__ == '__main__':
    unittest.main()
