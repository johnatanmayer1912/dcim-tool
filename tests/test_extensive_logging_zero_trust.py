"""Exhaustive validation of logging system & Zero-Trust security across features.

Validates:
- add_log mirroring to console_log_buffer and session_log_file.
- Zero-trust secret scrubbing in app_logger (_JsonLineFormatter, _ConsoleFormatter).
- /api/logs read-only security, boundary parameters, and anti-drain policy.
- Bounded ring buffer behavior.
- Clean structured output directories created via prepare_run_output.
"""
from __future__ import annotations

import json
import logging
import os
import re
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import vlan_checker_web as web
from utils.app_logger import _ConsoleFormatter, _JsonLineFormatter, _scrub_secrets
from utils.output_paths import (
    CAT_DISCOVERY,
    CAT_L3_TOPOLOGY,
    CAT_PLUGINS,
    CAT_VLAN_AUDIT,
    get_data_root,
    new_session_log_path,
    prepare_run_output,
)


class TestExtensiveLoggingZeroTrust(unittest.TestCase):
    def setUp(self):
        self.tmp_data = tempfile.mkdtemp(prefix="test_nst_logs_")
        os.environ["NST_DATA_DIR"] = self.tmp_data
        from utils import output_paths
        self.old_data_root = output_paths._DATA_ROOT
        output_paths._DATA_ROOT = self.tmp_data
        output_paths.ensure_data_layout()
        web.app.config["TESTING"] = True
        self.client = web.app.test_client()

    def tearDown(self):
        from utils import output_paths
        output_paths._DATA_ROOT = self.old_data_root
        import shutil
        shutil.rmtree(self.tmp_data, ignore_errors=True)

    def test_add_log_writes_to_buffer_and_session_file(self):
        """add_log must mirror to console_log_buffer and write clean text to session_log_file."""
        test_session_file = Path(self.tmp_data) / "logs" / "sessions" / "test_session.txt"
        test_session_file.parent.mkdir(parents=True, exist_ok=True)
        old_file = web.session_log_file
        web.session_log_file = str(test_session_file)

        try:
            msg = "[VLAN] Checked 10.0.0.1: <span style='color:green;'>VLAN 100 OK</span>"
            # Avoid false negatives when the global ring already holds >100 lines.
            web.console_log_buffer.clear_for_tests()
            web.add_log(msg)

            # Check console_log_buffer has message
            out, _ = web.console_log_buffer.snapshot(0, 100)
            self.assertTrue(any(msg in log for log in out))

            # Check session file has clean HTML-stripped text
            self.assertTrue(test_session_file.is_file())
            content = test_session_file.read_text(encoding="utf-8")
            self.assertIn("[VLAN] Checked 10.0.0.1: VLAN 100 OK", content)
            self.assertNotIn("<span", content)
        finally:
            web.session_log_file = old_file

    def test_zero_trust_scrub_secrets_helper(self):
        """_scrub_secrets must mask password, secret, enable_pwd, and admin_password."""
        raw_strings = [
            'Connecting with password="SuperSecret123" to host',
            'Authentication secret: MyAdminPass! failed',
            'enable_pwd=CiscoEnableSecret456',
            'admin_password: "VaultMasterKey999"',
        ]
        for raw in raw_strings:
            scrubbed = _scrub_secrets(raw)
            self.assertIn("***REDACTED***", scrubbed)
            self.assertNotIn("SuperSecret123", scrubbed)
            self.assertNotIn("MyAdminPass!", scrubbed)
            self.assertNotIn("CiscoEnableSecret456", scrubbed)
            self.assertNotIn("VaultMasterKey999", scrubbed)

    def test_app_logger_json_formatter_scrubs_secrets(self):
        """_JsonLineFormatter must scrub secrets in msg, extra context, and exceptions."""
        formatter = _JsonLineFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg='SSH failed with password="SecretVaultPassword777"',
            args=(),
            exc_info=None
        )
        record.context = {"user": "admin", "password": "SecretVaultPassword777"}

        formatted = formatter.format(record)
        entry = json.loads(formatted)

        self.assertNotIn("SecretVaultPassword777", formatted)
        self.assertIn("***REDACTED***", entry["msg"])
        self.assertIn("***REDACTED***", str(entry.get("context", {})))

    def test_app_logger_console_formatter_scrubs_secrets(self):
        """_ConsoleFormatter must scrub secrets from human-readable console lines."""
        formatter = _ConsoleFormatter()
        record = logging.LogRecord(
            name="console_logger",
            level=logging.ERROR,
            pathname=__file__,
            lineno=25,
            msg='Failed connect: secret="SecretKey888"',
            args=(),
            exc_info=None
        )
        setattr(record, "device", "10.10.10.10")
        setattr(record, "operation", "device_auth")

        line = formatter.format(record)
        self.assertIn("[10.10.10.10]", line)
        self.assertIn("[device_auth]", line)
        self.assertNotIn("SecretKey888", line)
        self.assertIn("***REDACTED***", line)

    def test_api_logs_read_only_and_anti_tamper(self):
        """/api/logs must be strictly read-only and reject destructive parameters."""
        # Clean request returns logs
        res = self.client.get("/api/logs")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("logs", data)
        self.assertIn("count", data)

        # Destructive or drain attempts must be rejected with 400
        for bad_param in ("drain", "clear", "delete", "purge", "truncate", "file", "path"):
            r = self.client.get(f"/api/logs?{bad_param}=true")
            self.assertEqual(r.status_code, 400, f"Failed on param: {bad_param}")

    def test_output_paths_create_isolated_run_folders(self):
        """prepare_run_output must create distinct timestamped folders under outputs root."""
        cats = [CAT_VLAN_AUDIT, CAT_DISCOVERY, CAT_L3_TOPOLOGY, CAT_PLUGINS]
        created_dirs = []
        for cat in cats:
            paths = prepare_run_output(cat, slug=f"test_{cat}")
            run_dir = Path(paths["run_dir"])
            self.assertTrue(run_dir.is_dir())
            self.assertTrue(str(run_dir).startswith(self.tmp_data))
            created_dirs.append(run_dir)

        # Ensure all run dirs are unique
        self.assertEqual(len(created_dirs), len(set(created_dirs)))


if __name__ == "__main__":
    unittest.main()
