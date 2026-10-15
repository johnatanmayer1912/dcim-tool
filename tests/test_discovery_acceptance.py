"""Discovery acceptance — profiles, operator_truth, empty neighbors. Not live vendor."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.plugins.network_discovery import (
    NEIGHBOR_EVIDENCE_NOTES,
    classify_neighbor_evidence,
    cisco_neighbor_collection_disabled,
)
from utils.discovery_acceptance import (
    BLOCKED_CONDITIONS,
    cancelled_must_not_look_complete,
    operator_truth_for_collection,
    profiles_must_not_claim_census,
)
from utils.discovery_map_formatter import generate_discovery_html
from utils.discovery_profiles import PROFILES, classify_discovery_failure, resolve_scan_profile


class TestDiscoveryAcceptanceBlocked(unittest.TestCase):
    def test_blocked_conditions_documented(self):
        self.assertTrue(BLOCKED_CONDITIONS)

    def test_profiles_are_not_census(self):
        profiles_must_not_claim_census(PROFILES)
        for name in ('conservative', 'standard', 'wide'):
            p = resolve_scan_profile(name)
            self.assertIs(p['census'], False)
            self.assertTrue(p.get('not_snmp'))

    def test_cancelled_operator_truth(self):
        truth = operator_truth_for_collection('cancelled')
        cancelled_must_not_look_complete('cancelled', truth)
        self.assertNotIn('complete as collected', truth.lower())

    def test_partial_operator_truth(self):
        truth = operator_truth_for_collection('partial')
        self.assertIn('not complete truth', truth)
        self.assertNotIn('complete as collected', truth.lower())

    def test_flask_status_matches_contract(self):
        import vlan_checker_web as web
        web._discovery_jobs.clear()
        web._discovery_jobs['c1'] = {
            'status': 'complete',
            'result': {'data': {'collection_status': 'cancelled', 'partial': True, 'devices': []}},
            'error': None,
            'started_at': '2026-08-17T00:00:00',
            'seed_hosts': ['10.0.0.1'],
            'max_depth': 1,
            'progress': {},
        }
        with web.app.test_client() as client:
            r = client.get('/api/discovery/status/c1', environ_base={'REMOTE_ADDR': '127.0.0.1'})
            body = r.get_json()
        self.assertEqual(body['collection_status'], 'cancelled')
        self.assertEqual(body['operator_truth'], operator_truth_for_collection('cancelled'))
        cancelled_must_not_look_complete(body['collection_status'], body['operator_truth'])

    def test_auth_timeout_failed_distinct(self):
        self.assertEqual(classify_discovery_failure(Exception('Authentication failed')), 'auth_denied')
        self.assertEqual(classify_discovery_failure(Exception('TCP connection timed out')), 'timeout')
        self.assertEqual(classify_discovery_failure(Exception('socket error')), 'failed')
        self.assertNotEqual(
            classify_discovery_failure(Exception('Authentication failed')),
            classify_discovery_failure(Exception('socket error')),
        )

    def test_empty_neighbors_are_lack_of_evidence(self):
        self.assertEqual(classify_neighbor_evidence([], []), 'none_collected')
        note = NEIGHBOR_EVIDENCE_NOTES['none_collected'].lower()
        self.assertIn('lack of', note)
        self.assertIn('not proof the device is isolated', note)
        disabled = 'LLDP is disabled'
        self.assertTrue(cisco_neighbor_collection_disabled(disabled))
        self.assertEqual(classify_neighbor_evidence([], [disabled]), 'protocol_disabled')
        self.assertEqual(
            classify_neighbor_evidence([{'hostname': 'x'}], [disabled]),
            'collected',
        )

    def test_html_empty_neighbor_subtitle(self):
        nodes = [{
            'id': 'lonely', 'ip': '10.0.0.1', 'is_scanned': True,
            'scan_state': 'scanned', 'neighbor_evidence': 'none_collected',
        }]
        path = os.path.join(tempfile.mkdtemp(), 'd.html')
        generate_discovery_html(path, nodes, [])
        html = open(path, encoding='utf-8').read()
        self.assertIn('lack of evidence, not isolation', html)
        self.assertNotIn('network is empty', html.lower())

    def test_hop_bounded_profiles(self):
        self.assertLessEqual(max(p['max_depth'] for p in PROFILES.values()), 3)
        self.assertGreaterEqual(min(p['max_depth'] for p in PROFILES.values()), 1)

    def test_index_complete_copy_is_not_census(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        html = open(
            os.path.join(root, 'modules', 'web', 'templates', 'index.html'),
            encoding='utf-8',
        ).read()
        self.assertIn('Complete as collected (CDP/LLDP hop-bounded, not overlay, not a census)', html)
        self.assertNotIn('✓ Complete — ${devices.length} device(s), ${links.length} link(s) found', html)
        self.assertIn('not authoritative', html)
        self.assertIn('empty panel is not an empty overlay fabric', html)

    def test_index_discovery_table_evidence_and_escape(self):
        html = self._index_html()
        self.assertIn('function discEsc(s)', html)
        self.assertIn('function discEvidenceCell(dev)', html)
        self.assertIn('>Evidence</th>', html)
        self.assertIn('const hn = discEsc(dev.hostname', html)
        self.assertIn("identity_conflict — two nodes, same name", html)
        self.assertIn('no CDP/LLDP evidence (not isolation)', html)

    def test_index_discovery_filters_auth_timeout(self):
        html = self._index_html()
        self.assertIn('value="auth_denied"', html)
        self.assertIn('value="timeout"', html)

    def test_index_csv_honesty_columns(self):
        html = self._index_html()
        self.assertIn(
            "from,local_port,to,remote_port,protocol,confidence,one_sided,bundle_kind",
            html,
        )

    def test_index_swiss_map_inventory_warning(self):
        html = self._index_html()
        self.assertIn('not the Discovery crawl graph', html)
        self.assertIn('not this crawl', html)

    def test_index_physical_l2_same_job_honesty(self):
        html = self._index_html()
        self.assertIn('same inventory CDP/LLDP job as L2', html)
        self.assertIn('nstPhysicalEligible', open(
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         'utils', 'topo_map_shell.py'), encoding='utf-8').read())
        self.assertIn('Not verified cables', html)

    def test_index_empty_and_wide_not_census(self):
        html = self._index_html()
        self.assertIn('Not L3 routing, not overlay, not a fabric census', html)
        self.assertNotIn('Discover L2/L3 neighbors for observability', html)
        self.assertIn('Wide — 3 hops (still not a census)', html)

    def test_export_fallback_includes_links_and_status(self):
        import vlan_checker_web as web
        web._discovery_jobs.clear()
        web._discovery_jobs['e1'] = {
            'status': 'complete',
            'result': {
                'data': {
                    'devices': [{'id': 'A', 'hostname': 'A'}],
                    'links': [{
                        'from': 'A', 'to': 'B', 'local_port': 'Gi0/1',
                        'remote_port': 'Gi0/2', 'protocol': 'CDP',
                        'confidence': 'Medium', 'one_sided': True,
                    }],
                    'collection_status': 'partial',
                    'partial': True,
                    'cancelled': False,
                }
            },
            'error': None,
            'started_at': '2026-08-17T00:00:00',
            'seed_hosts': ['10.0.0.1'],
            'max_depth': 1,
            'progress': {},
        }
        with web.app.test_client() as client:
            r = client.get(
                '/api/discovery/export/e1',
                environ_base={'REMOTE_ADDR': '127.0.0.1'},
            )
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body['collection_status'], 'partial')
        self.assertTrue(body['partial'])
        self.assertFalse(body['cancelled'])
        self.assertEqual(len(body['links']), 1)
        self.assertEqual(body['links'][0]['confidence'], 'Medium')
        self.assertEqual(len(body['devices']), 1)

    def test_api_devices_and_links_honesty_fields(self):
        from modules.plugins.network_discovery import (
            _edges_to_api_links,
            _nodes_to_api_devices,
        )
        devices = _nodes_to_api_devices([{
            'id': 'EDGE-01',
            'ip': '10.0.0.8',
            'platform': 'C9300',
            'device_type': 'cisco_ios',
            'serial': 'SN1',
            'depth': 1,
            'is_scanned': True,
            'scan_state': 'scanned',
            'neighbor_evidence': 'none_collected',
            'neighbor_evidence_note': 'lack of evidence',
            'identity_conflict': True,
        }])
        self.assertTrue(devices[0]['identity_conflict'])
        self.assertEqual(devices[0]['neighbor_evidence'], 'none_collected')
        links = _edges_to_api_links([{
            'from': 'A', 'to': 'B', 'f_port': 'Gi0/1', 't_port': 'Gi0/2',
            'protocol': 'CDP', 'confidence': 'Medium', 'one_sided': True,
            'spoof_risk': True, 'contradictions': ['port mismatch'],
            'bundle_kind': 'member', 'sources': ['CDP'], 'not_physical': False,
        }])
        self.assertEqual(links[0]['confidence'], 'Medium')
        self.assertTrue(links[0]['one_sided'])
        self.assertTrue(links[0]['spoof_risk'])
        self.assertEqual(links[0]['bundle_kind'], 'member')
        self.assertEqual(links[0]['sources'], ['CDP'])
        self.assertEqual(links[0]['contradictions'], ['port mismatch'])

    def _index_html(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return open(
            os.path.join(root, 'modules', 'web', 'templates', 'index.html'),
            encoding='utf-8',
        ).read()


if __name__ == '__main__':
    unittest.main()
