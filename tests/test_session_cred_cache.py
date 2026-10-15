"""Session credential cache — in-memory, process lifetime only."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.session_cred_cache import (
    clear_session_credentials,
    get_session_credentials,
    set_session_credentials,
    update_from_execute_payload,
)


class TestSessionCredCache(unittest.TestCase):
    def setUp(self):
        clear_session_credentials()

    def tearDown(self):
        clear_session_credentials()

    def test_set_and_get(self):
        set_session_credentials(
            username='admin',
            password='secret',
            enable_password='enable1',
            become_password='root',
            label='Lab',
        )
        creds = get_session_credentials()
        self.assertIsNotNone(creds)
        self.assertEqual(creds['username'], 'admin')
        self.assertEqual(creds['password'], 'secret')
        self.assertEqual(creds['enable_password'], 'enable1')
        self.assertEqual(creds['become_password'], 'root')
        self.assertEqual(creds['label'], 'Lab')

    def test_clear_on_empty_set(self):
        set_session_credentials(username='u', password='p')
        set_session_credentials()
        self.assertIsNone(get_session_credentials())

    def test_update_from_execute_payload(self):
        update_from_execute_payload({
            'username': 'netops',
            'password': 'pw',
            'enable_pwd': 'en',
            'become_password': 'be',
        })
        creds = get_session_credentials()
        self.assertEqual(creds['username'], 'netops')
        self.assertEqual(creds['enable_password'], 'en')
        self.assertEqual(creds['become_password'], 'be')

    def test_credential_id_clears_ram_secrets(self):
        set_session_credentials(username='netops', password='secret', credential_id='netops')
        creds = get_session_credentials()
        self.assertEqual(creds['credential_id'], 'netops')
        self.assertEqual(creds['password'], '')
        from utils.session_cred_cache import public_session_view
        view = public_session_view()
        self.assertEqual(view['credential_id'], 'netops')
        self.assertFalse(view['has_password'])
        self.assertNotIn('secret', str(view))

    def test_snmp_credential_id_persisted(self):
        set_session_credentials(
            username='sshops',
            credential_id='sshops',
            snmp_credential_id='snmpops',
            snmp_label='SNMP Ops',
        )
        creds = get_session_credentials()
        self.assertEqual(creds['snmp_credential_id'], 'snmpops')
        from utils.session_cred_cache import public_session_view
        view = public_session_view()
        self.assertEqual(view['snmp_credential_id'], 'snmpops')
        self.assertTrue(view['has_snmp_profile'])


class TestSessionCredApi(unittest.TestCase):
    def setUp(self):
        clear_session_credentials()
        from vlan_checker_web import app
        self.app = app
        self.client = app.test_client()
        app.config['TESTING'] = True

    def tearDown(self):
        clear_session_credentials()

    def test_get_empty_session_credentials(self):
        r = self.client.get('/api/session/credentials')
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(data['username'], '')

    def test_post_and_get_session_credentials(self):
        r = self.client.post(
            '/api/session/credentials',
            json={
                'username': 'ops',
                'password': 'pw1',
                'enable_password': 'en1',
                'become_password': 'be1',
                'label': 'Session',
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json().get('ok'))
        r2 = self.client.get('/api/session/credentials')
        data = r2.get_json()
        self.assertEqual(data['username'], 'ops')
        self.assertTrue(data.get('has_password'))
        self.assertNotIn('password', data)
        self.assertNotEqual(data.get('password', ''), 'pw1')
        self.assertEqual(data['label'], 'Session')

    def test_public_session_view_omits_secrets(self):
        from utils.session_cred_cache import public_session_view, set_session_credentials
        set_session_credentials(username='u', password='secret')
        view = public_session_view()
        self.assertTrue(view['has_password'])
        self.assertNotIn('password', view)


if __name__ == '__main__':
    unittest.main()
