"""Overlay collectors — NVE/EVPN CLI only; never hostname guessing."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.overlay_collector import (
    collect_overlay,
    parse_junos_evpn_neighbors,
    parse_nve_peers,
)
from utils.discovery_schema import validate_discovery_export

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'overlay')


def _read(name):
    return open(os.path.join(FIX, name), encoding='utf-8').read()


class TestOverlayCollector(unittest.TestCase):
    def test_nxos_nve_peers_become_not_physical_edges(self):
        links = parse_nve_peers(_read('nxos_nve_peers.txt'), 'CORE-NXOS-01')
        self.assertEqual(len(links), 2)
        peers = {e['to'] for e in links}
        self.assertEqual(peers, {'10.0.0.5', '10.0.0.6'})
        for e in links:
            self.assertTrue(e['not_physical'])
            self.assertEqual(e['layer'], 'overlay')
            self.assertEqual(e['edge_kind'], 'nve-peer')
            self.assertEqual(e['protocol'], 'EVPN')
            self.assertNotEqual(e.get('layer'), 'physical')

    def test_junos_evpn_neighbors(self):
        links = parse_junos_evpn_neighbors(_read('junos_evpn_instance.txt'), 'qfx1')
        self.assertGreaterEqual(len(links), 2)
        self.assertTrue(all(e.get('not_physical') for e in links))
        peers = {e['to'] for e in links}
        self.assertIn('10.0.0.8', peers)
        self.assertNotIn('10.0.0.1', peers)

    def test_invalid_command_not_collected(self):
        invalid = _read('ios_invalid_nve.txt')

        def send(cmd, timeout=60):
            return invalid

        out = collect_overlay(None, 'leaf-01', 'cisco_ios', send)
        self.assertFalse(out['collected'])
        self.assertEqual(out['links'], [])
        self.assertIn('not collected', out['overlay_note'].lower())

    def test_hostname_leaf_spine_is_not_overlay_evidence(self):
        def send(cmd, timeout=60):
            return _read('ios_invalid_nve.txt')

        out = collect_overlay(None, 'leaf-spine-vtep-01', 'cisco_nxos', send)
        self.assertFalse(out['collected'])
        self.assertEqual(out['links'], [])

    def test_supported_cli_sets_collected_even_without_peers(self):
        def send(cmd, timeout=60):
            if 'nve peers' in cmd:
                return 'Interface Peer-IP          State\n--------- ---------------  -----\n'
            return '% Invalid input detected'

        out = collect_overlay(None, 'CORE', 'cisco_nxos', send)
        self.assertTrue(out['collected'])
        self.assertEqual(out['links'], [])
        self.assertIn('no overlay peers', out['overlay_note'].lower())

    def test_schema_accepts_collected_not_physical_links(self):
        links = parse_nve_peers(_read('nxos_nve_peers.txt'), 'CORE-NXOS-01')
        ok, errors = validate_discovery_export({
            'devices': [{'id': 'CORE-NXOS-01', 'hostname': 'CORE-NXOS-01', 'scan_state': 'scanned'}],
            'links': links,
            'overlay_links': links,
            'collection_status': 'complete',
            'overlay_collected': True,
        })
        self.assertTrue(ok, errors)

    def test_schema_rejects_physical_overlay_link(self):
        ok, errors = validate_discovery_export({
            'devices': [{'id': 'A', 'hostname': 'A', 'scan_state': 'scanned'}],
            'links': [],
            'overlay_links': [{
                'from': 'A', 'to': 'B', 'layer': 'physical', 'not_physical': False,
            }],
            'collection_status': 'complete',
            'overlay_collected': True,
        })
        self.assertFalse(ok)
        self.assertTrue(any('overlay' in e for e in errors))

    def test_schema_accepts_collected_zero_peers(self):
        ok, errors = validate_discovery_export({
            'devices': [],
            'links': [],
            'overlay_links': [],
            'collection_status': 'complete',
            'overlay_collected': True,
        })
        self.assertTrue(ok, errors)


if __name__ == '__main__':
    unittest.main()
