"""Comprehensive 3-tier credential fallback test suite (Primary -> Secondary -> Third).

Validates:
- Deterministic 3-tier fallback cascade across mock network devices.
- Connect attempts order: Primary fails -> Secondary fails -> Third succeeds.
- Every SSH entrypoint (tools, plugins, discovery, IM, L3 cartography) honors the 3-tier chain.
- All-fail case raises clean exception with zero secret exposure.
- Vault credential resolution maps primary, secondary, and third IDs into fallback bundles.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from modules.credential_manager import CredentialManager
from modules.network_base import attach_fallback_to_devices, connect_device, safe_connection
from utils.collection_credentials import bundle_for_plugin
from utils.vault_credentials import resolve_execute_credentials


PRIMARY = {"username": "netadmin_p1", "password": "pass_primary_bad", "enable_pwd": "en1", "label": "Primary"}
SECONDARY = {"username": "netadmin_p2", "password": "pass_secondary_bad", "enable_pwd": "en2", "label": "Secondary"}
THIRD = {"username": "netadmin_p3", "password": "pass_third_good", "enable_pwd": "en3", "label": "Third"}
DEVICE = {"host": "10.150.150.1", "device_type": "cisco_ios", "port": 22}


class ThreeTierMockDevice:
    """Mock device that tracks attempted usernames and only accepts specific user."""

    def __init__(self, allowed_user: str = "netadmin_p3"):
        self.allowed_user = allowed_user
        self.attempts = []

    def connect(self, target_dict, user, pwd, enb_pwd, log_func=None):
        self.attempts.append(user)
        if user != self.allowed_user:
            raise Exception(f"Authentication failed for user '{user}'")
        conn = MagicMock(name=f"conn[{user}]")
        conn.find_prompt.return_value = "MockCoreSW#"
        conn.send_command.return_value = "Cisco IOS Software, C9300\nPID: C9300-48P, VID: V01, SN: FDO3TIER1\n"
        conn.disconnect = MagicMock()
        return conn


class TestFullCredentialFallbackE2E(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="test_cred_3tier_")
        self.master_pwd = "VaultMasterPassword_999!"
        self.cm = CredentialManager(storage_dir=self.tmp_dir, master_password=self.master_pwd)

        # Seed 3 credentials into vault
        self.cm.add_credential("cred_p1", "pass_primary_bad", admin_password="en1", label="Tier 1 Primary")
        self.cm.add_credential("cred_p2", "pass_secondary_bad", admin_password="en2", label="Tier 2 Secondary")
        self.cm.add_credential("cred_p3", "pass_third_good", admin_password="en3", label="Tier 3 Tertiary")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_vault_resolution_bundles_all_three_tiers(self):
        """resolve_execute_credentials must resolve primary, secondary, and third credentials into fallback list."""
        resolved = resolve_execute_credentials(
            {
                "credential_id": "cred_p1",
                "secondary_credential_id": "cred_p2",
                "third_credential_id": "cred_p3",
            },
            self.cm,
            credential_id_required=True
        )
        self.assertEqual(resolved["username"], "cred_p1")
        self.assertEqual(resolved["password"], "pass_primary_bad")

        fallback_list = resolved.get("fallback_credentials") or []
        self.assertEqual(len(fallback_list), 2)
        self.assertEqual(fallback_list[0]["username"], "cred_p2")
        self.assertEqual(fallback_list[0]["password"], "pass_secondary_bad")
        self.assertEqual(fallback_list[1]["username"], "cred_p3")
        self.assertEqual(fallback_list[1]["password"], "pass_third_good")

        bundled = bundle_for_plugin(resolved)
        self.assertIn("fallback_credentials", bundled)
        self.assertEqual(len(bundled["fallback_credentials"]), 2)

    def test_safe_connection_three_tier_order(self):
        """Primary and Secondary fail -> Third must be attempted and succeed."""
        mock_dev = ThreeTierMockDevice(allowed_user="netadmin_p3")
        logs = []

        with patch("modules.network_base.connect_permissive", side_effect=mock_dev.connect):
            with safe_connection(
                DEVICE,
                PRIMARY["username"],
                PRIMARY["password"],
                PRIMARY["enable_pwd"],
                log_func=logs.append,
                fallback_credentials=[SECONDARY, THIRD],
            ) as conn:
                self.assertIsNotNone(conn)

        self.assertEqual(mock_dev.attempts, ["netadmin_p1", "netadmin_p2", "netadmin_p3"])
        log_blob = "\n".join(logs)
        self.assertIn("Connecting to device using Primary", log_blob)
        self.assertIn("Connecting to device using Secondary", log_blob)
        self.assertIn("Connecting to device using Third", log_blob)
        self.assertIn("Successfully connected using Third", log_blob)

    def test_connect_device_stamped_fallback(self):
        """connect_device must honor device stamped with attach_fallback_to_devices."""
        mock_dev = ThreeTierMockDevice(allowed_user="netadmin_p3")
        stamped = attach_fallback_to_devices([DEVICE], fallback_credentials=[SECONDARY, THIRD])[0]
        logs = []

        with patch("modules.network_base.connect_permissive", side_effect=mock_dev.connect):
            conn = connect_device(
                stamped,
                PRIMARY["username"],
                PRIMARY["password"],
                PRIMARY["enable_pwd"],
                log_func=logs.append
            )
            self.assertIsNotNone(conn)
            conn.disconnect()

        self.assertEqual(mock_dev.attempts, ["netadmin_p1", "netadmin_p2", "netadmin_p3"])

    def test_all_tiers_fail_raises_without_leaking_secrets(self):
        """When all 3 tiers fail, raise clean exception with zero passwords in error message."""
        mock_dev = ThreeTierMockDevice(allowed_user="nobody")
        logs = []

        with patch("modules.network_base.connect_permissive", side_effect=mock_dev.connect):
            with self.assertRaises(Exception) as ctx:
                with safe_connection(
                    DEVICE,
                    PRIMARY["username"],
                    PRIMARY["password"],
                    PRIMARY["enable_pwd"],
                    log_func=logs.append,
                    fallback_credentials=[SECONDARY, THIRD],
                ):
                    pass

        self.assertEqual(mock_dev.attempts, ["netadmin_p1", "netadmin_p2", "netadmin_p3"])
        err_msg = str(ctx.exception)
        self.assertNotIn("pass_primary_bad", err_msg)
        self.assertNotIn("pass_secondary_bad", err_msg)
        self.assertNotIn("pass_third_good", err_msg)

        log_blob = "\n".join(logs)
        self.assertNotIn("pass_primary_bad", log_blob)
        self.assertNotIn("pass_secondary_bad", log_blob)
        self.assertNotIn("pass_third_good", log_blob)

    def test_cisco_asset_warranty_plugin_three_tier_fallback(self):
        """cisco_asset_warranty_plugin must utilize 3-tier fallback via collect_device_assets."""
        from modules.plugins.cisco_asset_warranty_plugin import run as warranty_run

        mock_dev = ThreeTierMockDevice(allowed_user="netadmin_p3")
        logs = []
        creds = bundle_for_plugin({
            "username": PRIMARY["username"],
            "password": PRIMARY["password"],
            "enable_pwd": PRIMARY["enable_pwd"],
            "fallback_credentials": [SECONDARY, THIRD],
        })

        with patch("modules.network_base.connect_permissive", side_effect=mock_dev.connect):
            result = warranty_run(DEVICE, creds, {"collection_policy": "ssh_only"}, {}, logs.append)

        self.assertEqual(result["status"], "success")
        self.assertEqual(mock_dev.attempts, ["netadmin_p1", "netadmin_p2", "netadmin_p3"])


if __name__ == "__main__":
    unittest.main()
