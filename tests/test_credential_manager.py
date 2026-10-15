"""CredentialManager unit tests (NEXT-003, v7.0.32)."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.credential_manager import CredentialManager


class TestCredentialManager(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cm = CredentialManager(storage_dir=self.tmp)

    def test_add_and_get(self):
        ok, msg = self.cm.add_credential('admin', 'secret', admin_password='enable1', label='Lab')
        self.assertTrue(ok, msg)
        cred = self.cm.get_credential('admin')
        self.assertEqual(cred['password'], 'secret')
        self.assertEqual(cred['admin_password'], 'enable1')
        self.assertEqual(cred['label'], 'Lab')

    def test_duplicate_without_force(self):
        self.cm.add_credential('u1', 'p1')
        ok, msg = self.cm.add_credential('u1', 'p2')
        self.assertFalse(ok)
        self.assertIn('already exists', msg)
        self.assertEqual(self.cm.get_credential('u1')['password'], 'p1')

    def test_duplicate_with_force(self):
        self.cm.add_credential('u1', 'p1')
        ok, msg = self.cm.add_credential('u1', 'p2', force=True)
        self.assertTrue(ok, msg)
        self.assertEqual(self.cm.get_credential('u1')['password'], 'p2')

    def test_list_hides_passwords(self):
        self.cm.add_credential('u1', 'p1', become_password='root', snmp_version='2c', snmp_community='public')
        rows = self.cm.list_credentials()
        self.assertEqual(len(rows), 1)
        self.assertNotIn('password', rows[0])
        self.assertNotIn('snmp_community', rows[0])
        self.assertEqual(rows[0]['credential_id'], 'u1')
        self.assertTrue(rows[0]['has_become'])
        self.assertTrue(rows[0]['has_snmp'])

    def test_remove_and_clear(self):
        self.cm.add_credential('a', '1')
        self.cm.add_credential('b', '2')
        ok, _ = self.cm.remove_credential('a')
        self.assertTrue(ok)
        self.assertEqual(self.cm.get_credential_count(), 1)
        ok, _ = self.cm.clear_all_credentials()
        self.assertTrue(ok)
        self.assertEqual(self.cm.get_credential_count(), 0)

    def test_update_fields(self):
        self.cm.add_credential('u1', 'p1', label='Old')
        ok, _ = self.cm.update_credential('u1', password='p2', label='New', become_password='br')
        self.assertTrue(ok)
        cred = self.cm.get_credential('u1')
        self.assertEqual(cred['password'], 'p2')
        self.assertEqual(cred['label'], 'New')
        self.assertEqual(cred['become_password'], 'br')

    def test_export_import_roundtrip(self):
        self.cm.add_credential('exp', 'pw', admin_password='en')
        path = os.path.join(self.tmp, 'bundle.enc')
        ok, _ = self.cm.export_credentials(path, 'export-pass')
        self.assertTrue(ok)
        sub = os.path.join(self.tmp, 'sub')
        os.makedirs(sub, exist_ok=True)
        cm2 = CredentialManager(storage_dir=sub)
        ok, _ = cm2.import_credentials(path, 'export-pass', merge=False)
        self.assertTrue(ok)
        self.assertEqual(cm2.get_credential('exp')['password'], 'pw')

    def test_master_password_unlock_migrates_to_machine_key(self):
        self.cm.add_credential('u1', 'p1')
        ok, _ = self.cm.set_master_password('master123')
        self.assertTrue(ok)
        cm2 = CredentialManager(storage_dir=self.tmp)
        self.assertTrue(cm2.is_master_password_required())
        self.assertFalse(cm2.unlock_with_master_password('wrong'))
        self.assertTrue(cm2.unlock_with_master_password('master123'))
        self.assertEqual(cm2.get_credential('u1')['password'], 'p1')
        self.assertFalse(cm2.is_master_password_required())
        # After migration, restart needs no unlock
        cm3 = CredentialManager(storage_dir=self.tmp)
        self.assertFalse(cm3.is_master_password_required())
        self.assertEqual(cm3.get_credential('u1')['password'], 'p1')

    def test_set_master_password_refuses_when_locked(self):
        self.cm.add_credential('u1', 'p1')
        ok, _ = self.cm.set_master_password('master123')
        self.assertTrue(ok)
        cm2 = CredentialManager(storage_dir=self.tmp)
        ok2, msg = cm2.set_master_password('newmaster')
        self.assertFalse(ok2)
        self.assertIn('locked', msg.lower())
        self.assertTrue(cm2.unlock_with_master_password('master123'))
        self.assertEqual(cm2.get_credential('u1')['password'], 'p1')
        self.assertFalse(cm2.is_master_password_required())

    def test_daily_use_needs_no_master_password(self):
        self.cm.add_credential('ops', 'secret')
        cm2 = CredentialManager(storage_dir=self.tmp)
        self.assertFalse(cm2.is_master_password_required())
        self.assertEqual(cm2.get_credential('ops')['password'], 'secret')
        rows = cm2.list_credentials()
        self.assertEqual(len(rows), 1)


if __name__ == '__main__':
    unittest.main()
