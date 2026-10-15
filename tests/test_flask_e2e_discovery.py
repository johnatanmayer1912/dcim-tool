"""Best-possible Flask E2E for discovery without Playwright: demo crawl → poll → schema export → HTML."""
from __future__ import annotations

import json
import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.discovery_schema import validate_discovery_export


class TestFlaskDemoDiscoveryE2E(unittest.TestCase):
    def setUp(self):
        import vlan_checker_web as web
        web._discovery_jobs.clear()
        self.web = web
        self.client = web.app.test_client()

    def tearDown(self):
        self.web._discovery_jobs.clear()

    def test_demo_run_status_export_report(self):
        resp = self.client.post(
            '/api/discovery/run',
            json={
                'seed_hosts': ['10.0.0.1'],
                'target_source': 'discovery_seeds',
                'demo_mode': True,
                'max_depth': 2,
                'generate_topology_html': True,
                'export_json': True,
            },
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
        )
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        job_id = resp.get_json()['job_id']
        self.assertTrue(job_id)

        final = None
        for _ in range(80):
            st = self.client.get(
                f'/api/discovery/status/{job_id}',
                environ_base={'REMOTE_ADDR': '127.0.0.1'},
            )
            body = st.get_json()
            if body.get('status') not in ('running', None):
                final = body
                break
            time.sleep(0.05)
        self.assertIsNotNone(final, 'demo discovery job did not finish')
        self.assertEqual(final['status'], 'complete', final)
        self.assertNotEqual(final.get('collection_status'), 'error')
        result = final.get('result') or {}
        data = result.get('data') or result
        self.assertTrue(data.get('demo_mode') is True or data.get('devices'))
        self.assertTrue(data.get('overlay_collected'))

        exp = self.client.get(
            f'/api/discovery/export/{job_id}',
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
        )
        self.assertEqual(exp.status_code, 200)
        ctype = exp.headers.get('Content-Type', '')
        if 'json' in ctype:
            payload = exp.get_json()
            if payload is None:
                payload = json.loads(exp.get_data(as_text=True))
        else:
            payload = json.loads(exp.get_data(as_text=True))
        ok, errors = validate_discovery_export(payload)
        self.assertTrue(ok, errors)
        self.assertTrue(payload.get('overlay_collected'))
        self.assertTrue(payload.get('overlay_links'))
        self.assertTrue(all(lk.get('not_physical') for lk in payload.get('overlay_links') or []))
        self.assertIn('links', payload)
        self.assertGreaterEqual(len(payload.get('devices') or []), 1)

        html_resp = self.client.get(
            f'/api/discovery/report/{job_id}',
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
        )
        self.assertEqual(html_resp.status_code, 200, html_resp.get_data(as_text=True)[:400])
        html = html_resp.get_data(as_text=True)
        self.assertIn('mynetwork', html)
        self.assertNotIn('unpkg.com', html.lower())
        self.assertNotIn('cdn.jsdelivr', html.lower())


if __name__ == '__main__':
    unittest.main()
