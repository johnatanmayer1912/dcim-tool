"""Unit tests for Cisco EOL/EOS database module."""
import unittest
import sqlite3
import os
import tempfile
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.cisco_eol_database import (
    init_database,
    get_model_info,
    enrich_asset_data,
    get_all_models,
    seed_demo_data,
    _calculate_warranty_status,
)


class TestCiscoEolDatabase(unittest.TestCase):
    """Test suite for Cisco EOL/EOS database functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Use a temporary database for testing
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Monkey-patch the database path
        import modules.cisco_eol_database as db_module
        self.original_get_path = db_module._get_database_path
        db_module._get_database_path = lambda: self.test_db.name

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original function
        import modules.cisco_eol_database as db_module
        db_module._get_database_path = self.original_get_path
        
        # Delete test database
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)

    def test_database_initialization(self):
        """Test that database initializes correctly."""
        conn = init_database()
        self.assertIsNotNone(conn)
        
        # Verify schema exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cisco_models'")
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'cisco_models')
        
        # Verify index exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_pid'")
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        
        conn.close()

    def test_pid_lookup_valid(self):
        """Test PID lookup with a valid PID."""
        # Seed test data
        conn = init_database()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cisco_models (pid, model_name, end_of_life, end_of_support, end_of_service)
            VALUES ('TEST-PID', 'Test Model', '2030-01-01', '2033-01-01', '2036-01-01')
        ''')
        conn.commit()
        conn.close()
        
        # Test lookup
        result = get_model_info('TEST-PID')
        self.assertEqual(result['pid'], 'TEST-PID')
        self.assertEqual(result['model_name'], 'Test Model')
        self.assertEqual(result['end_of_life'], '2030-01-01')
        self.assertEqual(result['end_of_support'], '2033-01-01')
        self.assertEqual(result['end_of_service'], '2036-01-01')

    def test_pid_lookup_invalid(self):
        """Test PID lookup with an invalid PID."""
        result = get_model_info('INVALID-PID')
        self.assertEqual(result, {})

    def test_pid_lookup_case_insensitive(self):
        """Test that PID lookup is case-insensitive."""
        # Seed test data (stored as uppercase as per implementation)
        conn = init_database()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cisco_models (pid, model_name, end_of_life, end_of_support, end_of_service)
            VALUES ('TEST-PID', 'Test Model', '2030-01-01', '2033-01-01', '2036-01-01')
        ''')
        conn.commit()
        conn.close()
        
        # Test lookup with different case (implementation converts to uppercase)
        result = get_model_info('test-pid')
        self.assertEqual(result['pid'], 'TEST-PID')

    def test_asset_enrichment_valid_pid(self):
        """Test asset enrichment with a valid PID."""
        # Seed test data
        conn = init_database()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cisco_models (pid, model_name, end_of_life, end_of_support, end_of_service)
            VALUES ('TEST-PID', 'Test Model', '2030-01-01', '2033-01-01', '2036-01-01')
        ''')
        conn.commit()
        conn.close()
        
        # Test enrichment
        asset = {'pid': 'TEST-PID', 'hostname': 'test-host'}
        enriched = enrich_asset_data(asset)
        
        self.assertEqual(enriched['model_name'], 'Test Model')
        self.assertEqual(enriched['end_of_life'], '2030-01-01')
        self.assertEqual(enriched['end_of_support'], '2033-01-01')
        self.assertEqual(enriched['end_of_service'], '2036-01-01')
        self.assertEqual(enriched['warranty_status'], 'active')

    def test_asset_enrichment_invalid_pid(self):
        """Test asset enrichment with an invalid PID."""
        asset = {'pid': 'INVALID-PID', 'hostname': 'test-host'}
        enriched = enrich_asset_data(asset)
        
        self.assertEqual(enriched['model_name'], '')
        self.assertEqual(enriched['end_of_life'], '')
        self.assertEqual(enriched['end_of_support'], '')
        self.assertEqual(enriched['end_of_service'], '')
        self.assertEqual(enriched['warranty_status'], 'unknown')

    def test_asset_enrichment_no_pid(self):
        """Test asset enrichment when PID is missing - should use demo data."""
        asset = {'hostname': 'test-host'}
        enriched = enrich_asset_data(asset)
        
        # Should not crash and should use demo data for enrichment
        self.assertEqual(enriched['hostname'], 'test-host')
        # Now includes demo data enrichment when PID is missing
        self.assertIn('model_name', enriched)
        self.assertIn('end_of_life', enriched)
        self.assertIn('end_of_support', enriched)
        self.assertIn('end_of_service', enriched)
        self.assertEqual(enriched['warranty_status'], 'demo')

    def test_warranty_status_calculation_active(self):
        """Test warranty status calculation for active status."""
        status = _calculate_warranty_status('2030-01-01', '2033-01-01')
        self.assertEqual(status, 'active')

    def test_warranty_status_calculation_expired(self):
        """Test warranty status calculation for expired status."""
        status = _calculate_warranty_status('2019-01-01', '2020-01-01')
        self.assertEqual(status, 'expired')

    def test_warranty_status_calculation_warning(self):
        """Test warranty status calculation for warning status (within 1 year)."""
        from datetime import datetime, timedelta
        future_date = (datetime.now() + timedelta(days=200)).strftime('%Y-%m-%d')
        status = _calculate_warranty_status(future_date, future_date)
        self.assertEqual(status, 'warning')

    def test_warranty_status_calculation_unknown(self):
        """Test warranty status calculation with no dates."""
        status = _calculate_warranty_status('', '')
        self.assertEqual(status, 'unknown')

    def test_warranty_status_calculation_invalid_date(self):
        """Test warranty status calculation with invalid date format."""
        status = _calculate_warranty_status('invalid-date', 'invalid-date')
        self.assertEqual(status, 'unknown')

    def test_get_all_models(self):
        """Test retrieving all models from database."""
        # Seed test data
        conn = init_database()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cisco_models (pid, model_name, end_of_life, end_of_support, end_of_service)
            VALUES ('TEST-PID-1', 'Test Model 1', '2030-01-01', '2033-01-01', '2036-01-01')
        ''')
        cursor.execute('''
            INSERT INTO cisco_models (pid, model_name, end_of_life, end_of_support, end_of_service)
            VALUES ('TEST-PID-2', 'Test Model 2', '2025-01-01', '2026-01-01', '2027-01-01')
        ''')
        conn.commit()
        conn.close()
        
        # Test retrieval
        models = get_all_models()
        self.assertEqual(len(models), 2)
        
        # Verify warranty status is calculated
        for model in models:
            self.assertIn('warranty_status', model)
            self.assertIn(model['warranty_status'], ['active', 'expired', 'warning', 'unknown'])

    def test_demo_data_fallback(self):
        """Test demo mode data fallback."""
        demo_models = seed_demo_data()
        
        self.assertIsInstance(demo_models, list)
        self.assertGreater(len(demo_models), 0)
        
        # Verify demo data has required fields
        for model in demo_models:
            self.assertIn('pid', model)
            self.assertIn('model_name', model)
            self.assertIn('warranty_status', model)
            self.assertIn(model['warranty_status'], ['active', 'expired', 'warning'])


if __name__ == '__main__':
    unittest.main()
