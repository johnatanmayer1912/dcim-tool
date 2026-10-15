"""HTML/API contract for credential_id-only /cli_terminal (no browser required)."""
from __future__ import annotations

import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, 'modules', 'web', 'templates', 'cli_terminal.html')


class TestCliTerminalHtmlContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(HTML, encoding='utf-8') as f:
            cls.html = f.read()

    def test_has_credential_selector(self):
        self.assertIn('id="connCredentialSelect"', self.html)

    def test_no_password_inputs(self):
        self.assertNotRegex(self.html, r'id="connPassword"')
        self.assertNotRegex(self.html, r'id="connEnablePassword"')
        self.assertNotRegex(self.html, r'type=["\']password["\']')

    def test_no_plaintext_compat_ui(self):
        self.assertNotIn('NST_CLI_PLAINTEXT_COMPAT', self.html)
        self.assertNotIn('plaintext_compat', self.html)
        self.assertNotIn('cli_plaintext_compat', self.html)

    def test_emit_payload_is_credential_id_only(self):
        self.assertIn('credential_id: credentialId', self.html)
        self.assertIn('socket.emit(\'cli_connect\'', self.html)
        # Must not send password keys in the connect payload object
        emit_block = re.search(
            r"const payload = \{([\s\S]*?)\};\s*socket\.emit\('cli_connect'",
            self.html,
        )
        self.assertIsNotNone(emit_block)
        body = emit_block.group(1)
        self.assertIn('credential_id', body)
        self.assertNotIn('password', body.lower().replace('credential_id', ''))

    def test_loads_metadata_list_endpoint(self):
        self.assertIn("/api/credentials/list", self.html)

    def test_primary_controls_named(self):
        self.assertIn('id="connectBtn"', self.html)
        self.assertIn('id="connCredentialSelect"', self.html)
        self.assertRegex(self.html, r'aria-label=["\']Stored vault credential_id["\']')
        self.assertRegex(self.html, r'id="connectBtn"[^>]*aria-label=["\']Connect to device["\']')

    def test_visible_focus_styles(self):
        self.assertIn(':focus-visible', self.html)


if __name__ == '__main__':
    unittest.main()
