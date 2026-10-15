"""Regression tests for v7.0.60 council remediation."""
import unittest

from modules.plugins.interface_manager import _validate_vendor_syntax


class TestImBlockingValidation(unittest.TestCase):
    def test_no_switchport_blocked(self):
        cfg = 'interface Eth1/1\n no switchport\n'
        r = _validate_vendor_syntax(cfg, 'cisco_nxos', None)
        self.assertFalse(r['passed'])
        self.assertTrue(any('switchport' in str(e).lower() for e in r['errors']))


class TestTopologySkippedHostsMeta(unittest.TestCase):
    def test_adapters_manifest_field(self):
        import modules.adapters as ad
        src = open(ad.__file__, encoding='utf-8').read()
        self.assertIn('devices_skipped_hosts', src)
