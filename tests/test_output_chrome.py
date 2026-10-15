"""Output chrome contract — offline UX for all report types."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.output_chrome import (
    OFFLINE_BANNER,
    wrap_html_report,
    wrap_plugin_html_report,
    wrap_plugin_text_report,
    write_run_readme,
)
from utils.output_paths import prepare_run_output, CAT_PLUGINS
from utils.ping_scan_formatter import write_ping_scan_html


class TestOutputChrome(unittest.TestCase):
    def test_offline_banner_in_html(self):
        html = wrap_html_report('Test Report', '<p>Body</p>', hints=['Hint one'])
        self.assertIn(OFFLINE_BANNER, html)
        self.assertIn('nst-report-header', html)
        self.assertIn('nst-hint-box', html)
        self.assertNotIn('fonts.googleapis', html.lower())

    def test_plugin_text_wrap_adds_header(self):
        body = 'Serial Number: ABC123'
        out = wrap_plugin_text_report('serial_number', 'SW1', body)
        self.assertIn('Network Swiss Tool Pro', out)
        self.assertIn('HOW TO READ', out)
        self.assertIn('Serial Number: ABC123', out)

    def test_plugin_html_wrap(self):
        html = wrap_plugin_html_report('vlan_audit', 'SW1', 'VLAN 10 test')
        self.assertIn('VLAN Audit', html)
        self.assertIn('nst-report-body', html)
        self.assertIn('<pre>', html)

    def test_write_run_readme(self):
        paths = prepare_run_output(CAT_PLUGINS, 'test_readme')
        path = write_run_readme(paths, title='Test Task', task_summary='Smoke test')
        self.assertTrue(os.path.isfile(path))
        with open(path, encoding='utf-8') as f:
            text = f.read()
        self.assertIn('00_README', os.path.basename(path))
        self.assertIn('report.html', text)
        self.assertIn('offline', text.lower())

    def test_ping_scan_uses_chrome(self):
        tmp = tempfile.mkdtemp()
        fp = os.path.join(tmp, 'ping.html')
        write_ping_scan_html(fp, '10.0.0.0/24', ['10.0.0.1'], ['10.0.0.2'], total_hosts=2)
        with open(fp, encoding='utf-8') as f:
            html = f.read()
        self.assertIn('nst-kpi-row', html)
        self.assertIn('How to read this report', html)


if __name__ == '__main__':
    unittest.main()
