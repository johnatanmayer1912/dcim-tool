"""God-mode v7.4.23 perfection regression — containment, vendor cmds, UI contracts."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


class TestGodmodeVersion(unittest.TestCase):
    def test_version_7423(self):
        ver = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
        self.assertGreaterEqual(tuple(int(x) for x in ver.split('.')), (7, 4, 23))


class TestContainedRunDirRealpath(unittest.TestCase):
    def test_rejects_symlink_escape(self):
        from utils.job_index import contained_run_dir, is_safe_outputs_file
        from utils.output_paths import get_data_root, get_outputs_root

        data = Path(get_data_root())
        outputs = Path(get_outputs_root())
        outputs.mkdir(parents=True, exist_ok=True)
        outside = Path(tempfile.mkdtemp(prefix='nst_godmode_out_'))
        secret = outside / 'secret.html'
        secret.write_text('<html>x</html>', encoding='utf-8')
        link_dir = outputs / '_godmode_symlink_test'
        if link_dir.exists() or link_dir.is_symlink():
            if link_dir.is_symlink() or link_dir.is_file():
                link_dir.unlink()
            else:
                import shutil
                shutil.rmtree(link_dir, ignore_errors=True)
        try:
            link_dir.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('symlink not permitted')
        try:
            evil = str(link_dir / 'secret.html')
            self.assertIsNone(contained_run_dir(evil))
            self.assertIsNone(is_safe_outputs_file(evil, require_html=True))
            # Honest file under outputs still ok
            good = outputs / '_godmode_ok.html'
            good.write_text('<html>ok</html>', encoding='utf-8')
            rel = contained_run_dir(str(good))
            self.assertIsNotNone(rel)
            self.assertTrue(str(rel).startswith('outputs/'))
            self.assertIsNotNone(is_safe_outputs_file(str(good), require_html=True))
            good.unlink(missing_ok=True)
        finally:
            if link_dir.is_symlink():
                link_dir.unlink()
            import shutil
            shutil.rmtree(outside, ignore_errors=True)


class TestVendorCommandMaps(unittest.TestCase):
    def test_junos_ipv6_route_table(self):
        from modules.routing_analyzer.collector import PLATFORM_COMMAND_MAP
        cmds = [c for c, _ in PLATFORM_COMMAND_MAP['juniper_junos']]
        self.assertIn('show route table inet6.0', cmds)
        self.assertNotIn('show route inet6', cmds)

    def test_junos_lacp_command(self):
        from modules.plugins.interface_manager import VENDOR_COMMANDS
        self.assertEqual(
            VENDOR_COMMANDS['juniper_junos']['port_channel'],
            'show lacp interfaces',
        )

    def test_path_trace_junos_port_norm(self):
        from modules.path_trace import _norm_port
        self.assertEqual(_norm_port('ge-0/0/0.0'), 'ge-0/0/0')
        self.assertEqual(_norm_port('GigabitEthernet1/0/1'), 'gi1/0/1')

    def test_nxos_platform_not_bare_nx(self):
        src = (ROOT / 'modules/routing_analyzer/parser.py').read_text(encoding='utf-8')
        self.assertNotIn("'nx' in platform", src)
        self.assertIn('nexus', src)


class TestDiscoveryDriverHelpers(unittest.TestCase):
    def test_seed_ip_only_empty_type(self):
        from modules.plugins.network_discovery import _parse_seed_entry
        host, dtype = _parse_seed_entry('10.1.1.1')
        self.assertEqual(host, '10.1.1.1')
        self.assertEqual(dtype, '')

    def test_neighbor_junos_not_ios(self):
        from modules.plugins.network_discovery import _ssh_type_for_neighbor
        t = _ssh_type_for_neighbor({'platform': 'Juniper QFX5120', 'protocol': 'LLDP'})
        self.assertEqual(t, 'juniper_junos')

    def test_driver_try_order(self):
        from modules.plugins.network_discovery import _driver_try_order
        order = _driver_try_order('')
        self.assertEqual(order[0], 'cisco_ios')
        self.assertIn('juniper_junos', order)


class TestUiContracts(unittest.TestCase):
    def setUp(self):
        self.html = (ROOT / 'modules/web/templates/index.html').read_text(encoding='utf-8')

    def test_no_inter_font(self):
        self.assertNotIn("'Inter'", self.html)

    def test_no_warning_warning(self):
        self.assertNotIn('WARNING: WARNING:', self.html)

    def test_im_uses_data_im_name(self):
        self.assertIn('data-im-name', self.html)
        self.assertNotIn('onclick="selectInterface', self.html)

    def test_standards_escape(self):
        self.assertIn('nstEscape(trueHost)', self.html)
        self.assertIn('nstEscape(v.description', self.html)

    def test_health_wizard_dialog(self):
        self.assertIn('nstSetDialogOpen(m, true)', self.html)
        self.assertIn('health-wizard-modal', self.html)

    def test_vlan_step_base(self):
        self.assertIn('VLAN_VSTEP_BASE', self.html)

    def test_overlay_requires_credential_id(self):
        src = (ROOT / 'vlan_checker_web.py').read_text(encoding='utf-8')
        self.assertIn(
            '_resolve_task_credentials(data, credential_id_required=True)',
            src,
        )


class TestVaultSaveFailClosed(unittest.TestCase):
    def test_save_credentials_propagates(self):
        from modules.credential_manager import CredentialManager
        cm = CredentialManager.__new__(CredentialManager)
        cm.credentials = {'u': {'username': 'u', 'password': 'p'}}
        cm.fernet = mock.Mock()
        cm.fernet.encrypt.side_effect = RuntimeError('disk full')
        cm.credentials_file = '/tmp/nst_godmode_should_not_write.enc'
        with self.assertRaises(RuntimeError):
            cm._save_credentials()


class TestResolveWebPort(unittest.TestCase):
    def test_default_port(self):
        from utils.api_security import resolve_web_port, DEFAULT_WEB_PORT
        with mock.patch.dict(os.environ, {}, clear=False):
            for k in ('NST_WEB_PORT', 'NST_CLI_BROWSER_QA_PORT', 'PORT'):
                os.environ.pop(k, None)
            self.assertEqual(resolve_web_port(), DEFAULT_WEB_PORT)


if __name__ == '__main__':
    unittest.main()
