"""RB-ZT-02: Origin/CSRF contract for the local operator console.

Empty Origin remains allowed on loopback for pytest and local curl.
Loopback is not identity. Prefix-lookalike origins are denied.
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_security import (
    EMPTY_ORIGIN_POLICY,
    _origin_parts,
    request_origin_is_trusted,
)


class TestOriginParsing(unittest.TestCase):
    def test_empty_origin_policy_is_local_automation(self):
        self.assertEqual(EMPTY_ORIGIN_POLICY, 'loopback_local_automation')

    def test_trusted_ui_origin(self):
        self.assertEqual(
            _origin_parts('http://127.0.0.1:5051', allow_path=False),
            ('http', '127.0.0.1', 5051),
        )
        self.assertEqual(
            _origin_parts('http://localhost:5051/', allow_path=False),
            ('http', 'localhost', 5051),
        )

    def test_prefix_lookalike_is_malformed_or_untrusted(self):
        self.assertFalse(_origin_parts('http://127.0.0.1:5051.evil.com', allow_path=False))
        parts = _origin_parts('http://127.0.0.1:50519', allow_path=False)
        self.assertEqual(parts, ('http', '127.0.0.1', 50519))
        self.assertNotEqual(parts, ('http', '127.0.0.1', 5051))

    def test_malformed_origin(self):
        self.assertFalse(_origin_parts('not-a-url', allow_path=False))
        self.assertFalse(_origin_parts('http://', allow_path=False))
        self.assertFalse(_origin_parts('http://127.0.0.1:5051/path', allow_path=False))
        self.assertFalse(_origin_parts('http://user@127.0.0.1:5051', allow_path=False))
        self.assertIsNone(_origin_parts('', allow_path=False))
        self.assertIsNone(_origin_parts('   ', allow_path=False))

    def test_referer_allows_path(self):
        self.assertEqual(
            _origin_parts('http://127.0.0.1:5051/settings', allow_path=True),
            ('http', '127.0.0.1', 5051),
        )


class TestOriginFlaskContract(unittest.TestCase):
    def setUp(self):
        from vlan_checker_web import app
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.local = {'REMOTE_ADDR': '127.0.0.1'}

    def _post(self, headers=None, environ_base=None, **kwargs):
        kw = {
            'json': {'action': 'connectivity', 'inventory': '10.0.0.1,cisco_ios'},
            'environ_base': environ_base or dict(self.local),
        }
        if headers:
            kw['headers'] = headers
        kw.update(kwargs)
        return self.client.post('/api/execute', **kw)

    def test_loopback_empty_origin_allowed(self):
        r = self._post()
        self.assertNotEqual(r.status_code, 403)

    def test_loopback_trusted_origin_allowed(self):
        r = self._post(headers={'Origin': 'http://127.0.0.1:5051'})
        self.assertNotEqual(r.status_code, 403)

    def test_foreign_origin_rejected(self):
        r = self._post(headers={'Origin': 'http://evil.example'})
        self.assertEqual(r.status_code, 403)

    def test_prefix_origin_rejected(self):
        r = self._post(headers={'Origin': 'http://127.0.0.1:5051.evil.com'})
        self.assertEqual(r.status_code, 403)
        r2 = self._post(headers={'Origin': 'http://127.0.0.1:50519'})
        self.assertEqual(r2.status_code, 403)

    def test_malformed_origin_rejected(self):
        r = self._post(headers={'Origin': 'totally-bogus'})
        self.assertEqual(r.status_code, 403)
        r2 = self._post(headers={'Origin': 'http://'})
        self.assertEqual(r2.status_code, 403)

    def test_nonlocal_empty_origin_rejected(self):
        r = self._post(environ_base={'REMOTE_ADDR': '203.0.113.10'})
        self.assertEqual(r.status_code, 403)

    def test_nonlocal_trusted_origin_still_rejected(self):
        r = self._post(
            headers={'Origin': 'http://127.0.0.1:5051'},
            environ_base={'REMOTE_ADDR': '203.0.113.10'},
        )
        self.assertEqual(r.status_code, 403)

    def test_options_skips_origin_but_stays_localhost(self):
        r = self.client.open(
            '/api/execute',
            method='OPTIONS',
            environ_base=self.local,
            headers={'Origin': 'http://evil.example'},
        )
        self.assertNotEqual(r.status_code, 403)
        r2 = self.client.open(
            '/api/execute',
            method='OPTIONS',
            environ_base={'REMOTE_ADDR': '203.0.113.10'},
        )
        self.assertEqual(r2.status_code, 403)

    def test_get_skips_origin_check(self):
        r = self.client.get(
            '/api/logs',
            environ_base=self.local,
            headers={'Origin': 'http://evil.example'},
        )
        self.assertEqual(r.status_code, 200)

    def test_trusted_referer_without_origin(self):
        r = self._post(headers={'Referer': 'http://127.0.0.1:5051/settings'})
        self.assertNotEqual(r.status_code, 403)

    def test_foreign_referer_without_origin(self):
        r = self._post(headers={'Referer': 'http://evil.example/attack'})
        self.assertEqual(r.status_code, 403)


class TestOriginHelperInRequestContext(unittest.TestCase):
    def test_empty_headers_trusted(self):
        from flask import Flask
        from utils import api_security as sec
        app = Flask(__name__)

        @app.route('/t', methods=['POST'])
        def t():
            return 'yes' if request_origin_is_trusted() else 'no'

        c = app.test_client()
        r = c.post('/t')
        self.assertEqual(r.data.decode(), 'yes')
        r2 = c.post('/t', headers={'Origin': 'http://127.0.0.1:5051'})
        self.assertEqual(r2.data.decode(), 'yes')
        r3 = c.post('/t', headers={'Origin': 'http://evil.example'})
        self.assertEqual(r3.data.decode(), 'no')


if __name__ == '__main__':
    unittest.main()
