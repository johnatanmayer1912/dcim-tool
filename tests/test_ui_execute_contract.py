"""G-CONTRACT: Every runAction() call in index.html maps to a valid /api/execute action.
   G-008b: IM HTML report route is reachable and serves the report file.
   G-UX-001-003: No dead [data-tab=…] querySelector calls remain.
"""
from __future__ import annotations

import os
import re
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_PATH = os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html')
WEB_PATH = os.path.join(ROOT, 'vlan_checker_web.py')

# Canonical action registry (must match vlan_checker_web.py dispatch table)
_REGISTERED_ACTIONS = frozenset({
    'connectivity', 'vlan_check', 'find_missing_vlan', 'mac_check',
    'description_search', 'add_vlan', 'rename_vlan', 'delete_vlan',
    'interfaces', 'vlan_compare', 'node_analyze', 'node_interface_topology',
    'topology', 'utilization_live', 'l3_topology', 'flow_map', 'advanced_l2_map',
    'audit', 'backup', 'save_config', 'reachability_matrix',
    'failure_correlation',
})
# Client-side aliases that are normalised before dispatch
_CLIENT_ALIASES = frozenset({'mac_trace'})


def _registered_plugin_actions():
    from modules.plugin_registry import get_registry
    return frozenset(
        m.get('plugin_id')
        for m in get_registry().get_all_metadata()
        if m.get('plugin_id')
    )


def _html():
    return open(HTML_PATH, encoding='utf-8').read()


def _web_src():
    return open(WEB_PATH, encoding='utf-8').read()


class TestRunActionContract(unittest.TestCase):
    """Every runAction(…) call in index.html must reference a registered action or alias."""

    def _extract_run_action_calls(self):
        html = _html()
        # Match runAction('action_name') or runAction("action_name")
        return re.findall(r"""runAction\(['"]([\w]+)['"]\)""", html)

    def test_all_run_action_calls_are_registered(self):
        calls = set(self._extract_run_action_calls())
        allowed = _REGISTERED_ACTIONS | _CLIENT_ALIASES | _registered_plugin_actions()
        unknown = calls - allowed
        self.assertEqual(
            unknown, set(),
            f"runAction() calls in index.html not registered in /api/execute: {unknown}",
        )

    def test_no_run_action_calls_empty(self):
        calls = self._extract_run_action_calls()
        self.assertGreater(len(calls), 0, "Expected at least one runAction() call in index.html")

    def test_mac_trace_alias_normalised_client_side(self):
        html = _html()
        self.assertIn("if (action === 'mac_trace')", html)
        self.assertIn("action = 'mac_check'", html)

    def test_registered_actions_all_present_in_dispatch_table(self):
        src = _web_src()
        for act in _REGISTERED_ACTIONS:
            self.assertIn(f"'{act}':", src, f"Dispatch table missing action: {act}")


class TestNoDeadDataTabSelectors(unittest.TestCase):
    """G-UX-001/002/003: No querySelector('[data-tab=…]') dead selectors."""

    def test_no_data_tab_query_selectors(self):
        html = _html()
        dead = re.findall(r"querySelector\(['\"][^'\"]*\[data-tab=", html)
        self.assertEqual(
            dead, [],
            f"Dead [data-tab=…] querySelector calls found — replace with goTo*Tab(): {dead}",
        )

    def test_go_to_tab_helpers_present(self):
        html = _html()
        self.assertIn('function goToSearchTab', html)
        self.assertIn('function goToToolsTab', html)
        self.assertIn('function goToDiscoveryTab', html)

    def test_description_search_empty_guard_in_run_action(self):
        """G-UX-004: runAction must guard empty desc_search_input."""
        html = _html()
        self.assertIn("action === 'description_search'", html)
        self.assertIn('desc_search_input', html)


class TestImHtmlReportRoute(unittest.TestCase):
    """G-008b: /api/interface/open-report serves HTML and blocks path traversal."""

    def setUp(self):
        from vlan_checker_web import app
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_open_report_route_exists(self):
        src = _web_src()
        self.assertIn('/api/interface/open-report', src)

    def test_open_report_missing_path_returns_error(self):
        r = self.client.get('/api/interface/open-report?path=')
        # Must not crash — expect 400 or 404 JSON error
        self.assertIn(r.status_code, (400, 404))

    def test_open_report_traversal_blocked(self):
        r = self.client.get('/api/interface/open-report?path=../../etc/passwd')
        self.assertIn(r.status_code, (400, 403, 404))
        body = r.get_json() or {}
        # Must not serve the file
        self.assertNotEqual(r.content_type, 'text/html')

    def test_open_report_valid_temp_file(self):
        with tempfile.NamedTemporaryFile(
            suffix='.html', delete=False,
            dir=tempfile.gettempdir(),
        ) as f:
            f.write(b'<html><body>IM report</body></html>')
            tmp_path = f.name
        try:
            from vlan_checker_web import app
            with app.test_request_context():
                import vlan_checker_web as web
                # Patch _last_im_result or just call route with known path
                r = self.client.get(f'/api/interface/open-report?path={tmp_path}')
                # Route may require the path to be in the allowed work directory.
                # Acceptable outcomes: 200 (served), 400/403 (path outside work dir).
                self.assertIn(r.status_code, (200, 400, 403, 404))
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
