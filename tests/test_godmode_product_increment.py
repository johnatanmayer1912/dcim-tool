"""God-mode product increment — schema, cancel, offline CSS, overlay honesty, Physical≠L2."""
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.discovery_map_formatter import generate_discovery_html
from utils.discovery_schema import annotate_export, validate_discovery_export
from utils.map_acceptance import assert_html_map_acceptance
from utils.topo_map_shell import load_vis_script


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestDiscoverySchema(unittest.TestCase):
    def test_valid_partial_export(self):
        data = {
            'devices': [{'id': 'A', 'hostname': 'A', 'scan_state': 'scanned'}],
            'links': [{'from': 'A', 'to': 'B'}],
            'collection_status': 'partial',
            'cancelled': False,
            'overlay_collected': False,
        }
        ok, errors = validate_discovery_export(data)
        self.assertTrue(ok, errors)

    def test_cancelled_must_not_be_complete(self):
        ok, errors = validate_discovery_export({
            'devices': [], 'links': [],
            'collection_status': 'complete', 'cancelled': True,
            'overlay_collected': False,
        })
        self.assertFalse(ok)
        self.assertTrue(any('cancelled' in e for e in errors))

    def test_overlay_collected_true_requires_not_physical_links(self):
        ok, errors = validate_discovery_export({
            'devices': [], 'links': [],
            'overlay_links': [{'from': 'A', 'to': 'B', 'layer': 'physical'}],
            'collection_status': 'complete',
            'overlay_collected': True,
        })
        self.assertFalse(ok)
        self.assertTrue(any('overlay' in e for e in errors))
        ok2, err2 = validate_discovery_export({
            'devices': [{'id': 'A', 'hostname': 'A', 'scan_state': 'scanned'}],
            'links': [{
                'from': 'A', 'to': '10.0.0.5', 'layer': 'overlay',
                'edge_kind': 'nve-peer', 'not_physical': True,
            }],
            'overlay_links': [{
                'from': 'A', 'to': '10.0.0.5', 'layer': 'overlay',
                'edge_kind': 'nve-peer', 'not_physical': True,
            }],
            'collection_status': 'complete',
            'overlay_collected': True,
        })
        self.assertTrue(ok2, err2)

    def test_annotate_adds_overlay_false(self):
        out = annotate_export({
            'devices': [{'id': 'A', 'hostname': 'A', 'scan_state': 'seed'}],
            'links': [],
            'collection_status': 'complete',
        })
        self.assertIs(out['overlay_collected'], False)
        self.assertIn('schema_ok', out)


class TestOfflineConsoleAndMaps(unittest.TestCase):
    def test_index_html_has_no_css_cdn(self):
        html = open(os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html'), encoding='utf-8').read()
        self.assertNotIn('cdn.jsdelivr', html)
        self.assertNotIn('fonts.googleapis.com', html)
        self.assertNotIn('unpkg.com', html)
        self.assertIn('tools-overlay-empty', html)
        self.assertIn('#nst-layer=', html)

    def test_vis_script_not_cdn(self):
        script = load_vis_script()
        self.assertNotIn('unpkg.com', script.lower())
        self.assertNotIn('cdn.jsdelivr', script.lower())

    def test_generated_map_physical_filter_and_stale_clock(self):
        path = os.path.join(tempfile.mkdtemp(), 'm.html')
        generate_discovery_html(
            path,
            [{'id': 'a', 'ip': '10.0.0.1', 'is_scanned': True, 'scan_state': 'scanned'}],
            [{'from': 'a', 'to': 'b', 'f_port': 'Gi0/1', 't_port': 'Gi0/2', 'protocol': 'CDP',
              'one_sided': True, 'spoof_risk': True, 'confidence': 'Medium'}],
        )
        html = open(path, encoding='utf-8').read()
        assert_html_map_acceptance(html)
        self.assertIn('function nstPhysicalEligible', html)
        self.assertIn('nstStartFreshnessClock', html)
        self.assertIn('nstApplyHashLayer', html)
        self.assertIn('id="nst-physical-note"', html)
        self.assertIn('setInterval', html)

    def test_architecture_docs_not_tk_tier(self):
        path = os.path.join(ROOT, 'docs', '01-architecture', 'system-architecture.md')
        text = open(path, encoding='utf-8').read()
        self.assertIn('web only', text.lower())
        self.assertIn('out of scope', text.lower())
        self.assertNotIn('Desktop GUI  │ │  (Tkinter)', text)


class TestControlPlaneCancelBeforeConnect(unittest.TestCase):
    def test_send_cli_raises_before_send_when_cancelled(self):
        from unittest.mock import MagicMock
        from modules.plugins.network_discovery import DiscoveryCancelled, _send_cli

        conn = MagicMock()
        with self.assertRaises(DiscoveryCancelled):
            _send_cli(conn, 'show version', 10, cancel_check=lambda: True)
        conn.send_command.assert_not_called()

    def test_topology_mapper_send_cli_raises_before_send_when_cancelled(self):
        from unittest.mock import MagicMock
        from modules.topology_mapper import TopologyCancelled, _send_cli
        conn = MagicMock()
        with patch('utils.task_control_plane.should_abort', return_value=True):
            with self.assertRaises(TopologyCancelled):
                _send_cli(conn, 'show version')
        conn.send_command.assert_not_called()

    def test_safe_connection_aborts_when_cancelled(self):
        from modules.network_base import safe_connection
        with patch('modules.network_base.connect_permissive') as mock_conn:
            with patch('utils.task_control_plane.should_abort', return_value=True):
                with self.assertRaises(RuntimeError) as ctx:
                    with safe_connection({'host': '10.0.0.1', 'device_type': 'cisco_ios'}, 'u', 'p', ''):
                        pass
        self.assertIn('cancelled', str(ctx.exception).lower())
        mock_conn.assert_not_called()


class TestOverlayHonesty(unittest.TestCase):
    def test_overlay_empty_explains_nve_cli(self):
        html = open(os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html'), encoding='utf-8').read()
        self.assertIn('id="tools-overlay-empty"', html)
        self.assertIn('show nve peers', html)
        self.assertIn('not overlay evidence', html)
        shell = open(os.path.join(ROOT, 'utils', 'topo_map_shell.py'), encoding='utf-8').read()
        self.assertIn('This product does not gather EVPN/VXLAN', shell)
        self.assertIn('nst-overlay-empty-zero', shell)


class TestLoop3OperatorHonesty(unittest.TestCase):
    def test_swiss_tools_splits_l2_and_routing_groups(self):
        html = open(os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html'), encoding='utf-8').read()
        self.assertIn('id="tools-map-group-l2"', html)
        self.assertIn('id="tools-map-group-routing"', html)
        self.assertIn('Routing maps (SSH collection — not overlay)', html)
        for btn_id in ('btn-map-all', 'btn-map-vpc', 'btn-map-adv-l2', 'btn-map-adv-l3', 'btn-map-adv-flow'):
            self.assertIn(btn_id, html)
        self.assertIn("toolsRunTopology('all')", html)
        self.assertIn("toolsRunL3Map('l3')", html)

    def test_plugin_upload_warns_in_process_exec(self):
        html = open(os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html'), encoding='utf-8').read()
        self.assertIn('offline_local_directory', html)
        self.assertIn('in-process as Python code', html)
        self.assertIn('Runtime HTTP upload is disabled', html)

    def test_operator_log_does_not_call_add_log_traceback(self):
        src = open(os.path.join(ROOT, 'vlan_checker_web.py'), encoding='utf-8').read()
        self.assertIn('def _log_exception_off_console', src)
        self.assertNotIn('add_log(traceback.format_exc())', src)

    def test_vlan_reporter_escapes_hostname(self):
        from modules.plugins.interface_vlan_reporter import _generate_html_report
        html = _generate_html_report({
            'true_host': '<script>alert(1)</script>',
            'device_type': 'cisco_ios',
            'interfaces': [{'name': 'Gi0/1', 'status': 'up', 'vlan_info': {'mode': 'access', 'access_vlan': '10'}}],
        }, '10.0.0.1')
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertIn('&lt;script&gt;', html)


if __name__ == '__main__':
    unittest.main()
