"""Regression: /api/execute mac_trace vs mac_check — Swiss Tools dispatch contract (v7.0.61)."""
from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from modules.credential_manager import CredentialManager
from tests.execute_test_helpers import execute_json, seed_execute_vault


class TestMacTraceExecuteAlias(unittest.TestCase):
  def setUp(self):
    from vlan_checker_web import app
    import vlan_checker_web as web
    self.app = app
    self.web = web
    self.client = app.test_client()
    app.config['TESTING'] = True
    self._tmp = tempfile.mkdtemp()
    seed_execute_vault(web, self._tmp)

  def _payload(self, action: str, mac: str = 'aa:bb:cc:dd:ee:ff'):
    return execute_json(
      action=action,
      inventory='10.0.0.1,cisco_ios',
      target_mode='bulk',
      filter='',
      group='All',
      single_host='',
      mac_address=mac,
    )

  @patch('vlan_checker_web.threading.Thread')
  def test_mac_trace_alias_starts_task(self, mock_thread):
    inst = mock_thread.return_value
    inst.start = lambda: None
    r = self.client.post('/api/execute', json=self._payload('mac_trace'), environ_base={'REMOTE_ADDR': '127.0.0.1'})
    self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
    body = r.get_json()
    self.assertEqual(body.get('status'), 'started')
    self.assertIn('task_id', body)

  @patch('vlan_checker_web.threading.Thread')
  def test_mac_check_still_starts_task(self, mock_thread):
    inst = mock_thread.return_value
    inst.start = lambda: None
    r = self.client.post('/api/execute', json=self._payload('mac_check'), environ_base={'REMOTE_ADDR': '127.0.0.1'})
    self.assertEqual(r.status_code, 200)
    self.assertEqual(r.get_json().get('status'), 'started')

  def test_mac_trace_empty_mac_returns_400(self):
    r = self.client.post('/api/execute', json=self._payload('mac_trace', mac=''), environ_base={'REMOTE_ADDR': '127.0.0.1'})
    self.assertEqual(r.status_code, 400)
    self.assertIn('MAC', r.get_json().get('error', ''))

  def test_invalid_action_rejected(self):
    r = self.client.post('/api/execute', json=self._payload('not_a_real_action'), environ_base={'REMOTE_ADDR': '127.0.0.1'})
    self.assertEqual(r.status_code, 200)
    self.assertIn('Invalid API Action', r.get_json().get('error', ''))


class TestSwissToolsUiContract(unittest.TestCase):
  def test_swiss_tools_start_here_uses_mac_check_not_mac_trace(self):
    path = os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html')
    html = open(path, encoding='utf-8').read()
    self.assertNotIn("runAction('mac_trace')", html)
    self.assertIn("runAction('mac_check')", html)

  def test_run_action_normalizes_mac_trace_in_js(self):
    path = os.path.join(ROOT, 'modules', 'web', 'templates', 'index.html')
    html = open(path, encoding='utf-8').read()
    self.assertIn("if (action === 'mac_trace')", html)
    self.assertIn("action = 'mac_check'", html)


class TestExecuteActionRegistry(unittest.TestCase):
  """Guardrail: known /api/execute actions must stay registered."""

  EXPECTED = frozenset({
    'connectivity', 'vlan_check', 'find_missing_vlan', 'mac_check',
    'description_search', 'add_vlan', 'rename_vlan', 'delete_vlan',
    'interfaces', 'vlan_compare', 'node_analyze', 'node_interface_topology',
    'topology', 'audit', 'backup', 'save_config',
  })
  ALIASES = frozenset({'mac_trace'})

  def test_api_execute_source_lists_core_actions(self):
    path = os.path.join(ROOT, 'vlan_checker_web.py')
    src = open(path, encoding='utf-8').read()
    for act in self.EXPECTED:
      self.assertIn(f"'{act}':", src, f'missing execute action {act}')
    self.assertIn("action == 'mac_trace'", src)
