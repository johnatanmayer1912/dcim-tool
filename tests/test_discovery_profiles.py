"""Scan profile resolution — fixture/simulation only, not live vendor."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.discovery_profiles import PROFILES, resolve_scan_profile


class TestDiscoveryProfiles(unittest.TestCase):
    def test_conservative_defaults(self):
        p = resolve_scan_profile('conservative')
        self.assertEqual(p['max_depth'], 1)
        self.assertEqual(p['timeout'], 20)
        self.assertIn('not complete truth', p['truth_note'].lower())

    def test_explicit_depth_wins(self):
        p = resolve_scan_profile('wide', max_depth=1, timeout=10)
        self.assertEqual(p['max_depth'], 1)
        self.assertEqual(p['timeout'], 10)
        self.assertEqual(p['profile'], 'wide')

    def test_unknown_falls_back_to_standard(self):
        p = resolve_scan_profile('nope')
        self.assertEqual(p['profile'], 'standard')
        self.assertEqual(p['max_depth'], 2)

    def test_all_profiles_hop_bounded(self):
        for name, spec in PROFILES.items():
            self.assertIn(spec['max_depth'], (1, 2, 3), msg=name)


class TestDiscoveryProfilesApi(unittest.TestCase):
    def test_profiles_endpoint_loopback(self):
        import vlan_checker_web as web
        with web.app.test_client() as client:
            r = client.get('/api/discovery/profiles', environ_base={'REMOTE_ADDR': '127.0.0.1'})
            self.assertEqual(r.status_code, 200)
            body = r.get_json()
            self.assertIn('conservative', body['profiles'])
            self.assertEqual(body['default'], 'standard')

    def test_status_includes_collection_status(self):
        import vlan_checker_web as web
        web._discovery_jobs.clear()
        web._discovery_jobs['abc'] = {
            'status': 'complete',
            'result': {'data': {'collection_status': 'cancelled', 'partial': True, 'devices': []}},
            'error': None,
            'started_at': '2026-08-17T00:00:00',
            'seed_hosts': ['10.0.0.1'],
            'max_depth': 1,
            'progress': {},
        }
        with web.app.test_client() as client:
            r = client.get('/api/discovery/status/abc', environ_base={'REMOTE_ADDR': '127.0.0.1'})
            self.assertEqual(r.status_code, 200)
            body = r.get_json()
            self.assertEqual(body['collection_status'], 'cancelled')
            self.assertIn('not complete truth', body['operator_truth'])


if __name__ == '__main__':
    unittest.main()
