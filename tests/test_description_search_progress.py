"""Description search progress — pre-arm and completion state."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.search_it_progress import (
    get_all_progress,
    progress_done,
    progress_start,
    progress_start_if_needed,
    progress_tick,
)


class TestDescriptionSearchProgress(unittest.TestCase):
    def test_prearm_then_complete(self):
        """Simulates API pre-arm before worker thread (fixes UI idle race)."""
        progress_start('description_search', 3, label='Searching for "uplink"…')
        st = get_all_progress()['description_search']
        self.assertEqual(st['status'], 'running')
        self.assertIn('uplink', st['label'])
        progress_tick('description_search', 1, 3, host='10.0.0.1', match_count=2)
        progress_tick('description_search', 3, 3, host='10.0.0.3', match_count=5)
        progress_done('description_search', message='Description search complete')
        st = get_all_progress()['description_search']
        self.assertEqual(st['status'], 'complete')
        self.assertEqual(st['percent'], 100)
        self.assertEqual(st['match_count'], 5)

    def test_prearm_mac_trace_then_complete(self):
        """MAC trace pre-arm in /api/execute path (same idle-race fix as description search)."""
        progress_start('mac_trace', 2, label='Tracing aa:bb…')
        st = get_all_progress()['mac_trace']
        self.assertEqual(st['status'], 'running')
        progress_tick('mac_trace', 1, 2, host='10.0.0.1')
        progress_done('mac_trace', message='MAC trace complete')
        st = get_all_progress()['mac_trace']
        self.assertEqual(st['status'], 'complete')

    def test_ping_scan_prearm_then_complete(self):
        progress_start('ping_scan', 10, label='Ping sweep 10.0.0.0/24…')
        st = get_all_progress()['ping_scan']
        self.assertEqual(st['status'], 'running')
        progress_tick('ping_scan', 5, 10, host='10.0.0.5', responsive_count=3)
        progress_done('ping_scan', message='Ping scan complete')
        st = get_all_progress()['ping_scan']
        self.assertEqual(st['status'], 'complete')
        self.assertEqual(st['responsive_count'], 3)

    def test_empty_term_error(self):
        progress_start('description_search', 1, label='Preparing…')
        progress_done('description_search', error='Search term is empty')
        st = get_all_progress()['description_search']
        self.assertEqual(st['status'], 'error')

    def test_empty_mac_error(self):
        progress_start('mac_trace', 2, label='Preparing MAC trace…')
        progress_done('mac_trace', error='Target MAC is empty')
        st = get_all_progress()['mac_trace']
        self.assertEqual(st['status'], 'error')

    def test_invalid_ping_cidr_error(self):
        progress_start('ping_scan', 1, label='Starting ping scan…')
        progress_done('ping_scan', error='Invalid network: foo')
        st = get_all_progress()['ping_scan']
        self.assertEqual(st['status'], 'error')

    def test_progress_start_if_needed_preserves_prearm(self):
        progress_start('mac_trace', 5, label='Tracing aa:bb…')
        progress_tick('mac_trace', 1, 5, host='10.0.0.1')
        progress_start_if_needed('mac_trace', 5, label='Tracing aa:bb:cc:dd:ee:ff…')
        st = get_all_progress()['mac_trace']
        self.assertEqual(st['status'], 'running')
        self.assertEqual(st['current'], 1)
        self.assertEqual(st['total'], 5)


if __name__ == '__main__':
    unittest.main()
