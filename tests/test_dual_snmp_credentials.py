"""Dual SSH + separate SNMP vault profile resolution."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.credential_manager import CredentialManager
from utils.collection_credentials import bundle_for_plugin, overlay_snmp_fields
from utils.vault_credentials import (
    CredentialResolveError,
    mapping_has_secret_fields,
    public_credential_view,
    resolve_execute_credentials,
)


class TestDualSnmpCredentials(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cm = CredentialManager(storage_dir=self.tmp)
        self.cm.add_credential('sshops', 'ssh-secret', label='SSH Ops', profile_type='ssh_only')
        self.cm.add_credential(
            'snmpops', '-', label='SNMP Ops', profile_type='snmp_only',
            snmp_version='2c', snmp_community='public-lab',
        )

    def test_snmp_only_rejected_as_primary_execute_id(self):
        with self.assertRaises(CredentialResolveError) as ctx:
            resolve_execute_credentials(
                {'credential_id': 'snmpops'}, self.cm, None, credential_id_required=True,
            )
        self.assertIn('SSH-capable', str(ctx.exception.message))

    def test_separate_snmp_profile_overlays_ssh(self):
        resolved = resolve_execute_credentials(
            {'credential_id': 'sshops', 'snmp_credential_id': 'snmpops'},
            self.cm,
            None,
            credential_id_required=True,
        )
        self.assertEqual(resolved['password'], 'ssh-secret')
        self.assertEqual(resolved['snmp_community'], 'public-lab')
        self.assertEqual(resolved['snmp_credential_id'], 'snmpops')
        bundle = bundle_for_plugin(resolved)
        self.assertEqual(bundle['password'], 'ssh-secret')
        self.assertEqual(bundle['snmp_community'], 'public-lab')
        self.assertEqual(bundle['snmp_credential_id'], 'snmpops')

    def test_session_snmp_id_used_when_payload_omits(self):
        session = {'snmp_credential_id': 'snmpops'}
        resolved = resolve_execute_credentials(
            {'credential_id': 'sshops'}, self.cm, session, credential_id_required=True,
        )
        self.assertEqual(resolved['snmp_community'], 'public-lab')

    def test_public_views_never_expose_snmp_secrets(self):
        cred = self.cm.get_credential('snmpops')
        view = public_credential_view(cred, 'snmpops')
        self.assertEqual(view['profile_type'], 'snmp_only')
        self.assertFalse(view['has_ssh'])
        self.assertTrue(view['has_snmp'])
        self.assertFalse(mapping_has_secret_fields(view))

    def test_overlay_snmp_fields_replaces_base(self):
        base = {'username': 'u', 'snmp_version': 'none', 'snmp_community': ''}
        snmp = self.cm.get_credential('snmpops')
        out = overlay_snmp_fields(base, snmp)
        self.assertEqual(out['snmp_community'], 'public-lab')
        self.assertEqual(out['snmp_version'], '2c')


class TestSessionSnmpCache(unittest.TestCase):
    def setUp(self):
        from utils.session_cred_cache import clear_session_credentials
        clear_session_credentials()

    def tearDown(self):
        from utils.session_cred_cache import clear_session_credentials
        clear_session_credentials()

    def test_public_session_view_includes_snmp_id_not_secrets(self):
        from utils.session_cred_cache import public_session_view, set_session_credentials
        set_session_credentials(
            username='sshops',
            credential_id='sshops',
            snmp_credential_id='snmpops',
            snmp_label='SNMP Ops',
        )
        view = public_session_view()
        self.assertEqual(view['snmp_credential_id'], 'snmpops')
        self.assertTrue(view['has_snmp_profile'])
        self.assertNotIn('snmp_community', view)


if __name__ == '__main__':
    unittest.main()
