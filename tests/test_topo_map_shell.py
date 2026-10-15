import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.topo_map_shell import link_rows_from_edges, render_topology_page, script_safe_json


class TestTopoMapShell(unittest.TestCase):
    def test_html_contract(self):
        nodes = [{'id': 'sw1', 'ip': '10.0.0.1', 'platform': 'Nexus'}]
        edges = [{'from': 'sw1', 'to': 'sw2', 'f_port': 'Eth1/1', 't_port': 'Eth1/2', 'protocol': 'CDP'}]
        rows = link_rows_from_edges(edges)
        nodes_json = [{
            'id': 'sw1', 'label': 'sw1', 'ip': '10.0.0.1', 'x': 0, 'y': 0, 'fixed': True,
            'color': {'background': '#3b82f6', 'border': '#1e3a8a'},
            'font': {'color': '#fff'}, 'shape': 'box',
        }]
        edges_json = [{
            'id': 'e0', 'from': 'sw1', 'to': 'sw2', 'label': 'Eth1/1 ↔ Eth1/2',
            'f_port': 'Eth1/1', 't_port': 'Eth1/2', 'protocol': 'CDP',
            'color': {'color': '#6366f1'}, 'width': 2,
        }]
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as tf:
            path = tf.name
        try:
            render_topology_page(path, 'Test Map', nodes_json, edges_json, rows)
            html = open(path, encoding='utf-8').read()
            self.assertIn('__TOPO_LINKS__', html)
            self.assertIn('topo-search-input', html)
            self.assertIn('Link Inventory', html)
            self.assertIn('Evidence', html)
            self.assertIn('t.indexOf(\'high\')', html)
            self.assertIn('enabled: false', html)
            self.assertIn('nstSetLayer', html)
            self.assertIn('nstMarkFreshness', html)
            self.assertIn('nstBlastRadius', html)
            self.assertIn('nstWhyThisLink', html)
            self.assertIn('id="nst-why-link"', html)
            self.assertIn('id="nst-evidence-inspector"', html)
            self.assertIn('nstOpenEvidenceInspector', html)
            self.assertIn('nstCloseEvidenceInspector', html)
            self.assertIn('nstInspectLinkRowByIndex', html)
            self.assertIn('>Inspect</th>', html)
            self.assertIn('nstSyncHighlightRelation', html)
            self.assertIn('nstRevealLinkInventoryIfNeeded', html)
            self.assertIn('id="nst-overlay-empty"', html)
            self.assertIn('Overlay not collected', html)
            self.assertIn('nstBlastRadius(2)', html)
            self.assertIn('not a forwarding path', html)
            self.assertIn('EVPN/VXLAN overlay is not collected', html)
            self.assertNotIn('</script><img', html)
        finally:
            os.unlink(path)

    def test_script_safe_json_neutralizes_script_breakout(self):
        dumped = script_safe_json({'id': '</script><img src=x onerror=alert(1)>'})
        self.assertNotIn('</script>', dumped)
        self.assertIn('\\u003c', dumped)


if __name__ == '__main__':
    unittest.main()
