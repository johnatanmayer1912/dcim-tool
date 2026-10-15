"""
Integration Tests for Interface Manager API
==========================================

Test suite for the interface manager API endpoints.
Tests API integration with the web server.
"""

import unittest
import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class TestInterfaceManagerAPI(unittest.TestCase):
    """Test interface manager API endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        try:
            from vlan_checker_web import app
            from utils.session_cred_cache import clear_session_credentials
            clear_session_credentials()
            self.app = app
            self.client = self.app.test_client()
            self.app.config['TESTING'] = True
        except ImportError:
            self.skipTest("Flask app not available")

    def tearDown(self):
        from utils.session_cred_cache import clear_session_credentials
        clear_session_credentials()
    
    def test_discover_endpoint_exists(self):
        """Test that discover endpoint exists."""
        response = self.client.post('/api/interface/discover',
                                    json={"host": "test", "username": "test", "password": "test"},
                                    content_type='application/json')
        # Should return error (no actual device), but endpoint should exist
        self.assertIn(response.status_code, [400, 500])
    
    def test_validate_endpoint_exists(self):
        """Test that validate endpoint exists."""
        response = self.client.post('/api/interface/validate',
                                    json={
                                        "host": "test",
                                        "username": "test",
                                        "password": "test",
                                        "proposed_config": "interface Ethernet1/1"
                                    },
                                    content_type='application/json')
        # Should return error (no actual device), but endpoint should exist
        self.assertIn(response.status_code, [400, 500])
    
    def test_deploy_endpoint_exists(self):
        """Test that deploy endpoint exists."""
        response = self.client.post('/api/interface/deploy',
                                    json={
                                        "host": "test",
                                        "username": "test",
                                        "password": "test",
                                        "proposed_config": "interface Ethernet1/1"
                                    },
                                    content_type='application/json')
        # Should return error (no actual device), but endpoint should exist
        self.assertIn(response.status_code, [400, 500])
    
    def test_discover_missing_host(self):
        """Test discover endpoint with missing host."""
        response = self.client.post('/api/interface/discover',
                                    json={"username": "test", "password": "test"},
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
    
    def test_discover_missing_credentials(self):
        """Test discover endpoint with missing credentials."""
        response = self.client.post('/api/interface/discover',
                                    json={"host": "test"},
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
    
    def test_validate_missing_config(self):
        """Test validate endpoint with missing configuration."""
        response = self.client.post('/api/interface/validate',
                                    json={
                                        "host": "test",
                                        "username": "test",
                                        "password": "test"
                                    },
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
    
    def test_deploy_missing_config(self):
        """Test deploy endpoint with missing configuration."""
        response = self.client.post('/api/interface/deploy',
                                    json={
                                        "host": "test",
                                        "username": "test",
                                        "password": "test"
                                    },
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
