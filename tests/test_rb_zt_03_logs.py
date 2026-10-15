"""RB-ZT-03: GET /api/logs is a bounded snapshot; it never drains."""
from __future__ import annotations

import threading
import unittest
import uuid

from utils.api_security import plugin_upload_is_enabled
from utils.operator_console_logs import OperatorConsoleLogBuffer
from vlan_checker_web import add_log, app, console_log_buffer


class TestOperatorConsoleLogBuffer(unittest.TestCase):
    def test_snapshot_does_not_consume(self):
        buf = OperatorConsoleLogBuffer()
        buf.append('a')
        buf.append('b')
        first, c1 = buf.snapshot(0, 50)
        second, c2 = buf.snapshot(0, 50)
        self.assertEqual(first, ['a', 'b'])
        self.assertEqual(second, ['a', 'b'])
        self.assertEqual(c1, c2)
        more, c3 = buf.snapshot(c1, 50)
        self.assertEqual(more, [])
        self.assertEqual(c3, c1)

    def test_limit_and_since(self):
        buf = OperatorConsoleLogBuffer()
        for i in range(10):
            buf.append(str(i))
        chunk, cur = buf.snapshot(0, 3)
        self.assertEqual(chunk, ['0', '1', '2'])
        rest, _ = buf.snapshot(cur, 50)
        self.assertEqual(rest, ['3', '4', '5', '6', '7', '8', '9'])

    def test_concurrent_snapshots(self):
        buf = OperatorConsoleLogBuffer()
        for i in range(100):
            buf.append(f'n{i}')
        seen = []

        def worker():
            logs, _ = buf.snapshot(0, 500)
            seen.append(len(logs))

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertTrue(all(n == 100 for n in seen))
        self.assertEqual(len(buf), 100)


class TestApiLogsLifecycle(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.local = {'REMOTE_ADDR': '127.0.0.1'}
        # Isolate from full-suite buffer fill: since=0&limit=500 only returns the
        # oldest window, which would miss a fresh marker after thousands of lines.
        console_log_buffer.clear_for_tests()
        self.marker = f'rb-zt-03-{uuid.uuid4().hex}'
        add_log(self.marker)

    def test_get_returns_logs_and_cursor(self):
        r = self.client.get('/api/logs?since=0&limit=500', environ_base=self.local)
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn(self.marker, data.get('logs') or [])
        self.assertIn('next_cursor', data)
        self.assertNotIn('file', data)
        self.assertNotIn('path', data)
        blob = str(data.get('logs'))
        self.assertNotIn('password=', blob.lower())

    def test_get_does_not_drain(self):
        r1 = self.client.get('/api/logs?since=0&limit=500', environ_base=self.local)
        r2 = self.client.get('/api/logs?since=0&limit=500', environ_base=self.local)
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        self.assertIn(self.marker, r1.get_json()['logs'])
        self.assertIn(self.marker, r2.get_json()['logs'])

    def test_cursor_pagination(self):
        cur = 0
        for _ in range(20):
            r = self.client.get(
                f'/api/logs?since={cur}&limit=500',
                environ_base=self.local,
            )
            self.assertEqual(r.status_code, 200)
            data = r.get_json()
            cur = data['next_cursor']
            if data.get('count', 0) < 500:
                break
        add_log(self.marker + '-late')
        r2 = self.client.get(f'/api/logs?since={cur}&limit=500', environ_base=self.local)
        logs = r2.get_json()['logs']
        self.assertIn(self.marker + '-late', logs)
        self.assertNotIn(self.marker, logs)

    def test_drain_query_rejected(self):
        before = len(console_log_buffer)
        r = self.client.get('/api/logs?drain=1', environ_base=self.local)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(len(console_log_buffer), before)
        self.assertIn('read-only', (r.get_json() or {}).get('error', '').lower())

    def test_path_query_rejected(self):
        r = self.client.get('/api/logs?file=/etc/passwd', environ_base=self.local)
        self.assertEqual(r.status_code, 400)
        r2 = self.client.get('/api/logs?path=../../audit.log', environ_base=self.local)
        self.assertEqual(r2.status_code, 400)
        r3 = self.client.get('/api/logs?clear=1', environ_base=self.local)
        self.assertEqual(r3.status_code, 400)

    def test_post_and_delete_not_allowed(self):
        r = self.client.post('/api/logs', json={'drain': True}, environ_base=self.local)
        self.assertEqual(r.status_code, 405)
        r2 = self.client.delete('/api/logs', environ_base=self.local)
        self.assertEqual(r2.status_code, 405)

    def test_header_cannot_force_drain(self):
        before = len(console_log_buffer)
        r = self.client.get(
            '/api/logs?since=0&limit=10',
            environ_base=self.local,
            headers={'X-Drain': '1', 'X-Clear': 'true'},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(console_log_buffer), before)

    def test_remote_rejected(self):
        r = self.client.get(
            '/api/logs',
            environ_base={'REMOTE_ADDR': '203.0.113.10'},
        )
        self.assertEqual(r.status_code, 403)

    def test_cross_origin_get_does_not_mutate(self):
        """Origin is not enforced on GET (browser CORS hides the body). GET must not drain."""
        before = len(console_log_buffer)
        r = self.client.get(
            '/api/logs?since=0&limit=5',
            environ_base=self.local,
            headers={'Origin': 'http://evil.example'},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(console_log_buffer), before)

    def test_empty_origin_get_is_read_only(self):
        before = len(console_log_buffer)
        r = self.client.get('/api/logs?since=0&limit=5', environ_base=self.local)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(console_log_buffer), before)

    def test_invalid_since(self):
        r = self.client.get('/api/logs?since=-1', environ_base=self.local)
        self.assertEqual(r.status_code, 400)
        r2 = self.client.get('/api/logs?since=abc', environ_base=self.local)
        self.assertEqual(r2.status_code, 400)

    def test_plugin_upload_still_disabled(self):
        self.assertFalse(plugin_upload_is_enabled())
        r = self.client.post('/api/plugins/upload', environ_base=self.local)
        self.assertEqual(r.status_code, 403)
        self.assertFalse((r.get_json() or {}).get('runtime_upload', True))


if __name__ == '__main__':
    unittest.main()
