"""MAC search on interface maps — format-agnostic partial/full (v7.0.34)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.mac_utils import mac_query_matches, mac_search_blob, macs_search_blob


class TestMacInterfaceSearch(unittest.TestCase):
    def test_cisco_dotted_partial(self):
        blob = mac_search_blob('00:11:22:33:44:55')
        self.assertTrue(mac_query_matches(blob, '2233.4455'))
        self.assertTrue(mac_query_matches(blob, '4455'))
        self.assertTrue(mac_query_matches(blob, '0011.2233.4455'))

    def test_junos_colon_partial(self):
        blob = mac_search_blob('0011.2233.4455')
        self.assertTrue(mac_query_matches(blob, '00:11:22'))
        self.assertTrue(mac_query_matches(blob, '33:44:55'))

    def test_nxos_mixed_input(self):
        macs = ['aabb.ccdd.eeff', '00:11:22:33:44:55']
        blob = macs_search_blob(macs)
        self.assertTrue(mac_query_matches(blob, 'aabbcc'))
        self.assertTrue(mac_query_matches(blob, 'ccddeeff'))
        self.assertTrue(mac_query_matches(blob, '001122'))

    def test_full_mac_all_formats(self):
        for fmt in ('00:11:22:33:44:55', '0011.2233.4455', '001122334455'):
            blob = mac_search_blob(fmt)
            self.assertTrue(mac_query_matches(blob, '00:11:22:33:44:55'), fmt)
            self.assertTrue(mac_query_matches(blob, '0011.2233.4455'), fmt)


if __name__ == '__main__':
    unittest.main()
