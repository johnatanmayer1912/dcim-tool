"""Tests for search_it live progress state."""
import unittest

from utils.search_it_progress import get_all_progress, progress_done, progress_start, progress_tick


class TestSearchItProgress(unittest.TestCase):
    def test_lifecycle(self):
        progress_start('mac_trace', 5, label='Test')
        progress_tick('mac_trace', 2, 5, host='10.0.0.1', found_count=0)
        progress_done('mac_trace')
        all_p = get_all_progress()
        self.assertEqual(all_p['mac_trace']['status'], 'complete')
        self.assertEqual(all_p['mac_trace']['percent'], 100)
        self.assertEqual(all_p['mac_trace']['current'], 2)


if __name__ == '__main__':
    unittest.main()
