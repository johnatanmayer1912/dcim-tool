"""Discovery Command Center HTML contract (v7.0.4)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.discovery_map_formatter import build_vis_payload, generate_discovery_html


class TestDiscoveryMapHtmlContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes = [
            {
                'id': 'CORE-NXOS-01',
                'ip': '10.0.0.1',
                'platform': 'N9K',
                'device_type': 'cisco_nxos',
                'depth': 0,
                'is_scanned': True,
                'scan_state': 'seed',
            },
            {
                'id': 'DIST-IOS-02',
                'ip': '10.0.0.2',
                'platform': 'C9300',
                'device_type': 'cisco_ios',
                'depth': 1,
                'is_scanned': True,
                'scan_state': 'scanned',
            },
            {
                'id': 'ACCESS-03',
                'ip': '10.0.0.3',
                'platform': 'unknown',
                'device_type': 'cisco_ios',
                'depth': 2,
                'is_scanned': False,
                'scan_state': 'neighbor_only',
            },
        ]
        cls.edges = [
            {
                'from': 'CORE-NXOS-01',
                'to': 'DIST-IOS-02',
                'f_port': 'Eth1/1',
                't_port': 'Gi1/1',
                'protocol': 'CDP',
            },
            {
                'from': 'DIST-IOS-02',
                'to': 'ACCESS-03',
                'f_port': 'Gi1/48',
                't_port': 'Gi0/1',
                'protocol': 'LLDP',
            },
        ]
        cls.tmp = tempfile.mkdtemp()
        cls.html_path = os.path.join(cls.tmp, 'discovery_contract.html')
        generate_discovery_html(cls.html_path, cls.nodes, cls.edges)
        with open(cls.html_path, encoding='utf-8') as f:
            cls.html = f.read()
        cls.nodes_json, cls.edges_json, _ = build_vis_payload(cls.nodes, cls.edges)

    def test_command_center_shell(self):
        self.assertIn('discovery-command-center', self.html)
        self.assertIn('__DISCOVERY__', self.html)
        self.assertIn('discCommandCenterInit', self.html)
        self.assertIn('discBootMap', self.html)
        self.assertIn('disc-split-overview', self.html)

    def test_overlay_honesty_banner(self):
        self.assertIn('Overlay layer = NVE/EVPN CLI peers only (not cables).', self.html)

    def test_layer_switch_present(self):
        self.assertIn('nstSetLayer', self.html)
        self.assertIn('nstMarkFreshness', self.html)
        self.assertIn('nstBlastRadius', self.html)
        self.assertIn('nstWhyThisLink', self.html)
        self.assertIn('id="nst-why-link"', self.html)
        self.assertIn('id="nst-evidence-inspector"', self.html)
        self.assertIn('nstOpenEvidenceInspector', self.html)
        self.assertIn('nstInspectLinkRowByIndex', self.html)
        self.assertIn('>Inspect</th>', self.html)
        self.assertIn('nstSyncHighlightRelation', self.html)
        self.assertIn('nstRelationKey', self.html)
        self.assertIn('nstRevealLinkInventoryIfNeeded', self.html)
        self.assertIn('id="nst-overlay-empty"', self.html)
        self.assertIn('Overlay not collected', self.html)
        self.assertIn('nstBlastRadius(2)', self.html)

    def test_map_search_inputs_present(self):
        self.assertIn('id="disc-map-search-input"', self.html)
        self.assertIn('discApplyMapSearch', self.html)
        self.assertIn('id="topo-search-input"', self.html)

    def test_vis_nodes_have_xy(self):
        for n in self.nodes_json:
            self.assertIn('x', n)
            self.assertIn('y', n)
            self.assertTrue(n.get('fixed'))

    def test_scan_state_on_nodes(self):
        states = {n['id']: n.get('scan_state') for n in self.nodes_json}
        self.assertEqual(states['CORE-NXOS-01'], 'seed')
        self.assertEqual(states['DIST-IOS-02'], 'scanned')
        self.assertEqual(states['ACCESS-03'], 'neighbor_only')

    def test_demo_generator_smoke(self):
        r = subprocess.run(
            [sys.executable, 'create_demo_discovery_map_v7.py'],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )
        self.assertEqual(r.returncode, 0, r.stderr or r.stdout)
        demo = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'DEMO_DISCOVERY_COMMAND_CENTER_v7.0.4.html',
        )
        self.assertTrue(os.path.isfile(demo))
        with open(demo, encoding='utf-8') as f:
            body = f.read()
        self.assertIn('discovery-command-center', body)


if __name__ == '__main__':
    unittest.main()
