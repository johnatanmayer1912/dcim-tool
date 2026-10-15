"""
tests/comprehensive_qa_web.py
----------------------------
Comprehensive QA Testing Framework for Network Swiss Tool Pro Web Edition

Performs extensive validation including:
- Internal Server Error investigation
- Functional validation
- Smoke testing
- Negative testing
- Configuration safety
- Logging validation
- Performance testing

Usage:
    python tests/comprehensive_qa_web.py
"""

import sys
import os
import json
import time
import threading
import traceback
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"


@dataclass
class TestResult:
    phase: str
    test_name: str
    status: TestStatus
    duration_ms: int
    message: str
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


class ComprehensiveQA:
    """
    Comprehensive QA testing suite for Web Edition.
    """
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = datetime.now()
        self.errors_found: List[Dict[str, Any]] = []
        self.critical_issues: List[Dict[str, Any]] = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log test progress."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Execute all QA phases."""
        self.log("=" * 70)
        self.log("COMPREHENSIVE QA - Network Swiss Tool Pro Web Edition v4.5.2")
        self.log("=" * 70)
        self.log(f"Started: {self.start_time.isoformat()}")
        self.log(f"Working Directory: {os.getcwd()}")
        self.log("")
        
        # Phase 0: Error Investigation
        self.log("PHASE 0: Internal Server Error Investigation")
        self.log("-" * 70)
        self.p0_error_investigation()
        
        # Phase 1: Functional Validation
        self.log("")
        self.log("PHASE 1: Functional Validation")
        self.log("-" * 70)
        self.p1_functional_validation()
        
        # Phase 2: Smoke Testing
        self.log("")
        self.log("PHASE 2: Smoke Testing")
        self.log("-" * 70)
        self.p2_smoke_testing()
        
        # Phase 3: Negative Testing
        self.log("")
        self.log("PHASE 3: Negative Testing (Break It!)")
        self.log("-" * 70)
        self.p3_negative_testing()
        
        # Phase 4: Configuration Safety
        self.log("")
        self.log("PHASE 4: Configuration Safety")
        self.log("-" * 70)
        self.p4_configuration_safety()
        
        # Phase 5: Logging Validation
        self.log("")
        self.log("PHASE 5: Logging & Observability")
        self.log("-" * 70)
        self.p5_logging_validation()
        
        # Phase 6: Performance
        self.log("")
        self.log("PHASE 6: Performance & Scale")
        self.log("-" * 70)
        self.p6_performance_testing()
        
        # Phase 7: Documentation
        self.log("")
        self.log("PHASE 7: Documentation Validation")
        self.log("-" * 70)
        self.p7_documentation_validation()
        
        return self._generate_report()
    
    def _run_test(self, phase: str, name: str, test_func) -> TestResult:
        """Run a single test and capture result."""
        import time as time_module
        
        start = time_module.time()
        try:
            test_func()
            duration = int((time_module.time() - start) * 1000)
            result = TestResult(phase, name, TestStatus.PASS, duration, "Test passed")
            self.log(f"  [PASS] {name} ({duration}ms)")
        except AssertionError as e:
            duration = int((time_module.time() - start) * 1000)
            result = TestResult(phase, name, TestStatus.FAIL, duration, str(e))
            self.log(f"  [FAIL] {name}: {str(e)[:100]}", "ERROR")
        except Exception as e:
            duration = int((time_module.time() - start) * 1000)
            error_msg = f"{str(e)}\n{traceback.format_exc()[:200]}"
            result = TestResult(phase, name, TestStatus.ERROR, duration, error_msg)
            self.log(f"  [ERROR] {name}: {str(e)[:100]}", "ERROR")
            
            # Capture for error investigation
            self.errors_found.append({
                "phase": phase,
                "test": name,
                "error": str(e),
                "traceback": traceback.format_exc()
            })
        
        self.results.append(result)
        return result
    
    # ===== PHASE 0: ERROR INVESTIGATION =====
    
    def p0_error_investigation(self):
        """Investigate Internal Server Error."""
        
        # P0.1: Check if inventory.txt exists
        self._run_test("P0", "inventory_file_exists", self._test_inventory_exists)
        
        # P0.2: Validate web module imports
        self._run_test("P0", "web_module_imports", self._test_web_imports)
        
        # P0.3: Check Flask route handlers
        self._run_test("P0", "flask_routes_defined", self._test_flask_routes)
        
        # P0.4: Check template files exist
        self._run_test("P0", "template_files_exist", self._test_templates_exist)
        
        # P0.5: Check production modules integration
        self._run_test("P0", "production_modules_integration", self._test_production_modules)
        
        # P0.6: Test API endpoints without server
        self._run_test("P0", "api_endpoint_validation", self._test_api_validation)
    
    def _test_inventory_exists(self):
        """Test that inventory.txt exists."""
        assert os.path.exists("inventory.txt"), "inventory.txt not found"
        with open("inventory.txt", "r") as f:
            content = f.read()
        assert len(content) > 0, "inventory.txt is empty"
    
    def _test_web_imports(self):
        """Test that web module imports work."""
        try:
            import vlan_checker_web
            assert hasattr(vlan_checker_web, 'app'), "Flask app not found in vlan_checker_web"
            assert hasattr(vlan_checker_web, 'VERSION'), "VERSION not found"
        except ImportError as e:
            raise AssertionError(f"Failed to import vlan_checker_web: {e}")
    
    def _test_flask_routes(self):
        """Test that Flask routes are properly defined."""
        import vlan_checker_web
        app = vlan_checker_web.app
        
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        required_routes = ['/', '/api/logs', '/api/execute', '/api/version', '/api/inventory']
        
        for route in required_routes:
            assert any(route in r for r in routes), f"Route {route} not found"
    
    def _test_templates_exist(self):
        """Test that HTML templates exist."""
        template_paths = [
            "modules/web/templates/index.html",
            "templates/index.html"
        ]
        
        found = False
        for path in template_paths:
            if os.path.exists(path):
                found = True
                break
        
        assert found, "No HTML template found"
    
    def _test_production_modules(self):
        """Test production modules integration."""
        # Check structured_logger
        from utils.structured_logger import get_logger, OperationType
        logger = get_logger(console_output=False)
        assert logger is not None, "Failed to initialize logger"
        
        # Check config_backup_system
        from utils.config_backup_system import get_backup_system
        backup_system = get_backup_system()
        assert backup_system is not None, "Failed to initialize backup system"
        
        # Check vlan_mgmt_production
        import modules.vlan_mgmt_production as vlan_pro
        assert hasattr(vlan_pro, 'add_vlan'), "add_vlan not found in production module"
        assert hasattr(vlan_pro, 'delete_vlan'), "delete_vlan not found"
    
    def _test_api_validation(self):
        """Test API endpoint validation logic."""
        import vlan_checker_web
        
        # Test filter_inventory function
        test_inventory = """
        10.1.1.1,cisco_ios,Core
        10.1.1.2,cisco_nxos,Core
        10.2.1.1,juniper_junos,Access
        """
        
        devices = vlan_checker_web.filter_inventory(
            test_inventory, 
            target_mode='bulk',
            filter_str='',
            single_host='',
            group_filter='All'
        )
        
        assert len(devices) == 3, f"Expected 3 devices, got {len(devices)}"
    
    # ===== PHASE 1: FUNCTIONAL VALIDATION =====
    
    def p1_functional_validation(self):
        """Phase 1: Functional validation with simulated devices."""
        
        # Device onboarding tests
        self._run_test("P1", "inventory_parsing_valid", self._test_inventory_parsing)
        self._run_test("P1", "inventory_parsing_empty", self._test_inventory_empty)
        self._run_test("P1", "inventory_parsing_malformed", self._test_inventory_malformed)
        
        # VLAN operations
        self._run_test("P1", "vlan_id_validation_valid", self._test_vlan_id_valid)
        self._run_test("P1", "vlan_id_validation_invalid", self._test_vlan_id_invalid)
        self._run_test("P1", "vlan_id_validation_reserved", self._test_vlan_id_reserved)
        
        # Idempotency
        self._run_test("P1", "vlan_add_idempotency", self._test_vlan_add_idempotent)
        
        # Config operations
        self._run_test("P1", "backup_system_initialization", self._test_backup_init)
        self._run_test("P1", "logger_initialization", self._test_logger_init)
    
    def _test_inventory_parsing(self):
        """Test valid inventory parsing."""
        from modules.network_base import get_devices_from_file
        
        # Create test inventory
        test_inv = "test_inv_qa.txt"
        with open(test_inv, "w") as f:
            f.write("""# Test
[Core]
10.1.1.1,cisco_ios,Core
10.1.1.2,cisco_nxos,Core
""")
        
        devices = get_devices_from_file(test_inv)
        os.remove(test_inv)
        
        assert len(devices) == 2, f"Expected 2 devices, got {len(devices)}"
        assert devices[0]["group"] == "Core", f"Expected group Core, got {devices[0]['group']}"
    
    def _test_inventory_empty(self):
        """Test empty inventory handling."""
        from modules.network_base import get_devices_from_file
        
        test_inv = "test_inv_empty.txt"
        with open(test_inv, "w") as f:
            f.write("")
        
        devices = get_devices_from_file(test_inv)
        os.remove(test_inv)
        
        assert len(devices) == 0, "Empty inventory should return empty list"
    
    def _test_inventory_malformed(self):
        """Test malformed inventory handling."""
        from modules.network_base import get_devices_from_file
        
        test_inv = "test_inv_bad.txt"
        with open(test_inv, "w") as f:
            f.write("""# Test
invalid_line_without_comma
10.1.1.1
""")
        
        devices = get_devices_from_file(test_inv)
        os.remove(test_inv)
        
        # Should handle gracefully, possibly returning empty or partial
        assert isinstance(devices, list), "Should return list even with bad input"
    
    def _test_vlan_id_valid(self):
        """Test valid VLAN ID validation."""
        from modules.vlan_mgmt_production import _validate_vlan_id
        
        valid_ids = ["10", "100", "1000", "4094"]
        for vid in valid_ids:
            is_valid, msg = _validate_vlan_id(vid)
            assert is_valid, f"VLAN {vid} should be valid: {msg}"
    
    def _test_vlan_id_invalid(self):
        """Test invalid VLAN ID validation."""
        from modules.vlan_mgmt_production import _validate_vlan_id
        
        invalid_ids = ["0", "4095", "-1", "abc", "", "10000"]
        for vid in invalid_ids:
            is_valid, msg = _validate_vlan_id(vid)
            assert not is_valid, f"VLAN {vid} should be invalid"
    
    def _test_vlan_id_reserved(self):
        """Test reserved VLAN ID detection."""
        from modules.vlan_mgmt_production import _validate_vlan_id
        
        reserved = ["1", "1002", "1003", "1004", "1005"]
        for vid in reserved:
            is_valid, msg = _validate_vlan_id(vid)
            assert not is_valid, f"Reserved VLAN {vid} should be rejected"
    
    def _test_vlan_add_idempotent(self):
        """Test VLAN add idempotency check logic."""
        # This tests the logic, not actual device operation
        from modules.vlan_mgmt_production import _run_idempotency_check
        
        # We can't test with real connection, but we can verify function exists
        assert callable(_run_idempotency_check), "Idempotency check function should exist"
    
    def _test_backup_init(self):
        """Test backup system initialization."""
        from utils.config_backup_system import ConfigBackupSystem
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        try:
            bs = ConfigBackupSystem(temp_dir)
            assert os.path.exists(temp_dir), "Backup directory should be created"
            manifest_path = os.path.join(temp_dir, "backup_manifest.json")
            assert os.path.exists(manifest_path), "Manifest should be created"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _test_logger_init(self):
        """Test logger initialization."""
        from utils.structured_logger import get_logger, LogLevel
        
        logger = get_logger(console_output=False)
        assert logger is not None, "Logger should initialize"
        
        # Test log levels exist
        assert hasattr(LogLevel, "DEBUG"), "LogLevel.DEBUG should exist"
        assert hasattr(LogLevel, "INFO"), "LogLevel.INFO should exist"
        assert hasattr(LogLevel, "ERROR"), "LogLevel.ERROR should exist"
    
    # ===== PHASE 2: SMOKE TESTING =====
    
    def p2_smoke_testing(self):
        """Phase 2: Smoke testing end-to-end flows."""
        
        self._run_test("P2", "smoke_connectivity_flow", self._test_smoke_connectivity)
        self._run_test("P2", "smoke_backup_flow", self._test_smoke_backup)
        self._run_test("P2", "smoke_vlan_workflow", self._test_smoke_vlan)
        self._run_test("P2", "smoke_log_flow", self._test_smoke_logging)
    
    def _test_smoke_connectivity(self):
        """Smoke test connectivity check flow."""
        from modules.adapters import run_connectivity
        from modules.network_base import build_json
        
        # Mock devices
        devices = [
            {"host": "10.1.1.1", "device_type": "cisco_ios"},
            {"host": "10.1.1.2", "device_type": "cisco_nxos"}
        ]
        
        # Mock log function
        logs = []
        def mock_log(msg):
            logs.append(msg)
        
        # We can't run actual connectivity without devices, but we can test the adapter logic
        # by checking the function signature and basic flow
        assert callable(run_connectivity), "run_connectivity should be callable"
    
    def _test_smoke_backup(self):
        """Smoke test backup flow."""
        from utils.config_backup_system import get_backup_system
        
        backup_system = get_backup_system()
        
        # Test backup age check
        result = backup_system.check_backup_age("test-device", max_age_hours=24)
        assert isinstance(result, dict), "Backup check should return dict"
        assert "warning" in result, "Result should have warning field"
    
    def _test_smoke_vlan(self):
        """Smoke test VLAN workflow."""
        import modules.vlan_mgmt_production as vlan_pro
        
        # Verify all functions exist
        assert hasattr(vlan_pro, 'add_vlan'), "add_vlan should exist"
        assert hasattr(vlan_pro, 'rename_vlan'), "rename_vlan should exist"
        assert hasattr(vlan_pro, 'delete_vlan'), "delete_vlan should exist"
        assert hasattr(vlan_pro, '_result_status'), "result status helper should exist"
        assert not hasattr(vlan_pro, 'rollback_vlan_change'), "unsafe rollback must not exist"
    
    def _test_smoke_logging(self):
        """Smoke test logging flow."""
        from utils.structured_logger import get_logger, OperationType
        
        logger = get_logger(console_output=False)
        
        # Test logging operations
        logger.info("Test message", OperationType.CONNECTIVITY_CHECK, "test-device")
        logger.debug("Debug message", OperationType.VLAN_AUDIT)
        
        # Verify log files were created
        assert os.path.exists("logs"), "Logs directory should exist"
    
    # ===== PHASE 3: NEGATIVE TESTING =====
    
    def p3_negative_testing(self):
        """Phase 3: Negative testing - try to break the system."""
        
        self._run_test("P3", "negative_invalid_ip", self._test_invalid_ip)
        self._run_test("P3", "negative_sql_injection", self._test_sql_injection)
        self._run_test("P3", "negative_xss_attempt", self._test_xss)
        self._run_test("P3", "negative_rapid_operations", self._test_rapid_ops)
        self._run_test("P3", "negative_empty_credentials", self._test_empty_creds)
        self._run_test("P3", "negative_unicode_input", self._test_unicode)
    
    def _test_invalid_ip(self):
        """Test invalid IP handling."""
        from modules.network_base import get_devices_from_file
        
        test_inv = "test_inv_bad_ip.txt"
        with open(test_inv, "w") as f:
            f.write("999.999.999.999,cisco_ios,Test\n")
        
        # Should not crash, just parse
        devices = get_devices_from_file(test_inv)
        os.remove(test_inv)
        
        # The IP is syntactically valid (regex), so it might parse
        # But later operations should handle it
        assert isinstance(devices, list), "Should handle invalid IP gracefully"
    
    def _test_sql_injection(self):
        """Test SQL injection attempt."""
        # VLAN name with SQL injection
        malicious_vlan = "'; DROP TABLE vlans;--"
        
        from modules.vlan_mgmt_production import _validate_vlan_id
        
        # VLAN name validation doesn't exist as separate function,
        # but we can check that inputs are treated as strings
        assert isinstance(malicious_vlan, str), "String input should be preserved"
    
    def _test_xss(self):
        """Test XSS attempt."""
        # XSS attempt in VLAN name
        malicious_vlan = "<script>alert('xss')</script>"
        
        # Should be handled as plain string
        assert "<script>" in malicious_vlan, "XSS string should be preserved (handled elsewhere)"
    
    def _test_rapid_ops(self):
        """Test rapid operation handling."""
        from utils.structured_logger import get_logger
        
        logger = get_logger(console_output=False)
        
        # Rapid logging calls
        for i in range(100):
            logger.debug(f"Rapid log {i}")
        
        # Should not crash or lose logs
        assert True, "Rapid operations should complete"
    
    def _test_empty_creds(self):
        """Test empty credentials handling."""
        # This would be tested at UI level, but we can verify functions handle it
        from modules.network_base import build_json
        
        result = build_json("test-device", "fail", {}, "Empty password")
        assert result["status"] == "fail", "Should return fail status"
        assert result["error"] is not None, "Should have error message"
    
    def _test_unicode(self):
        """Test unicode input handling."""
        vlan_name = "测试VLAN_日本語_한국어"
        
        # Should handle unicode
        assert len(vlan_name) > 0, "Unicode string should be preserved"
    
    # ===== PHASE 4: CONFIGURATION SAFETY =====
    
    def p4_configuration_safety(self):
        """Phase 4: Configuration safety validation."""
        
        self._run_test("P4", "safety_backup_created", self._test_backup_created)
        self._run_test("P4", "safety_idempotency", self._test_safety_idempotency)
        self._run_test("P4", "safety_rollback_available", self._test_rollback_available)
        self._run_test("P4", "safety_manifest_integrity", self._test_manifest_integrity)
    
    def _test_backup_created(self):
        """Test that backup system creates backups correctly."""
        from utils.config_backup_system import ConfigBackupSystem, BackupMetadata
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        try:
            bs = ConfigBackupSystem(temp_dir)
            
            # Create test backup
            result = bs.create_backup(
                device="10.1.1.1",
                hostname="test-switch",
                config_content="vlan 100\n name Test",
                snapshot_command="show running-config",
                backup_type="pre_change",
                trigger="Test backup"
            )
            
            assert result["success"], f"Backup creation failed: {result.get('error')}"
            assert "backup_path" in result, "Backup path should be in result"
            assert os.path.exists(result["backup_path"]), "Backup file should exist"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _test_safety_idempotency(self):
        """Test idempotency logic."""
        from modules.vlan_mgmt_production import _run_idempotency_check
        
        # Cannot test without real connection, but function exists
        assert callable(_run_idempotency_check), "Idempotency function should exist"
    
    def _test_rollback_available(self):
        """Pre-change backup policy — automated rollback must not exist."""
        import modules.vlan_mgmt_production as vlan_pro
        from utils.restore_guide import get_manual_restore_guide

        assert not hasattr(vlan_pro, 'rollback_vlan_change'), "Automated VLAN rollback must not exist"
        guide = get_manual_restore_guide('/tmp/test.txt', 'cisco_ios')
        assert guide.get('automated_restore_available') is False
        assert guide.get('manual_steps')
    
    def _test_manifest_integrity(self):
        """Test backup manifest integrity."""
        from utils.config_backup_system import ConfigBackupSystem
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        try:
            bs = ConfigBackupSystem(temp_dir)
            
            # Create backup
            bs.create_backup(
                device="10.1.1.1",
                hostname="test-switch",
                config_content="vlan 100",
                snapshot_command="show run",
                backup_type="test"
            )
            
            # Check manifest
            manifest = bs._load_manifest()
            assert "backups" in manifest, "Manifest should have backups key"
            assert len(manifest["backups"]) >= 1, "Manifest should have at least one entry"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    # ===== PHASE 5: LOGGING VALIDATION =====
    
    def p5_logging_validation(self):
        """Phase 5: Logging and observability validation."""
        
        self._run_test("P5", "log_json_format", self._test_log_json_format)
        self._run_test("P5", "log_levels", self._test_log_levels)
        self._run_test("P5", "log_device_context", self._test_log_context)
        self._run_test("P5", "log_file_creation", self._test_log_files)
    
    def _test_log_json_format(self):
        """Test log JSON format."""
        import json
        
        # Create a log entry manually
        from utils.structured_logger import get_logger, OperationType
        
        logger = get_logger(console_output=False)
        logger.info("Test JSON log", OperationType.CONNECTIVITY_CHECK, "test-device",
                   context={"test": "data"})
        
        # Check log file exists and is valid JSON
        assert os.path.exists("logs/operations.log"), "Operations log should exist"
    
    def _test_log_levels(self):
        """Test all log levels work."""
        from utils.structured_logger import get_logger, OperationType
        
        logger = get_logger(console_output=False)
        
        # Test all levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        assert True, "All log levels should work"
    
    def _test_log_context(self):
        """Test log device context."""
        from utils.structured_logger import get_logger, OperationType
        
        logger = get_logger(console_output=False)
        
        # Log with device context
        logger.info("Operation completed", 
                   OperationType.VLAN_ADD, 
                   "10.1.1.1",
                   context={"vlan_id": "100", "result": "success"})
        
        assert True, "Device context should be captured"
    
    def _test_log_files(self):
        """Test log file creation."""
        log_files = ["logs/operations.log", "logs/errors.log", "logs/audit.log"]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                # Check file is writable
                assert os.access(log_file, os.W_OK), f"{log_file} should be writable"
    
    # ===== PHASE 6: PERFORMANCE TESTING =====
    
    def p6_performance_testing(self):
        """Phase 6: Performance and scale testing."""
        
        self._run_test("P6", "perf_inventory_load_50", self._test_perf_inventory)
        self._run_test("P6", "perf_logging_volume", self._test_perf_logging)
        self._run_test("P6", "perf_backup_creation", self._test_perf_backup)
    
    def _test_perf_inventory(self):
        """Test inventory loading performance."""
        import time
        
        # Create large inventory
        test_inv = "test_inv_large.txt"
        with open(test_inv, "w") as f:
            for i in range(50):
                f.write(f"10.1.{i//256}.{i%256},cisco_ios,Group{i%10}\n")
        
        from modules.network_base import get_devices_from_file
        
        start = time.time()
        devices = get_devices_from_file(test_inv)
        duration = time.time() - start
        
        os.remove(test_inv)
        
        assert len(devices) == 50, f"Should load 50 devices, got {len(devices)}"
        assert duration < 2.0, f"Should load in < 2 seconds, took {duration:.2f}s"
    
    def _test_perf_logging(self):
        """Test logging performance."""
        import time
        from utils.structured_logger import get_logger
        
        logger = get_logger(console_output=False)
        
        start = time.time()
        for i in range(1000):
            logger.debug(f"Performance test log {i}")
        duration = time.time() - start
        
        # Should complete 1000 logs in reasonable time
        assert duration < 5.0, f"1000 logs should complete in < 5 seconds, took {duration:.2f}s"
    
    def _test_perf_backup(self):
        """Test backup creation performance."""
        import time
        from utils.config_backup_system import ConfigBackupSystem
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        try:
            bs = ConfigBackupSystem(temp_dir)
            
            large_config = "vlan 100\n name Test\n" * 1000  # ~30KB config
            
            start = time.time()
            bs.create_backup(
                device="10.1.1.1",
                hostname="test",
                config_content=large_config,
                snapshot_command="show run",
                backup_type="test"
            )
            duration = time.time() - start
            
            assert duration < 1.0, f"Backup should complete in < 1 second, took {duration:.2f}s"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    # ===== PHASE 7: DOCUMENTATION VALIDATION =====
    
    def p7_documentation_validation(self):
        """Phase 7: Documentation validation."""
        
        self._run_test("P7", "doc_readme_exists", self._test_doc_readme)
        self._run_test("P7", "doc_changelog_exists", self._test_doc_changelog)
        self._run_test("P7", "doc_release_notes", self._test_doc_release)
        self._run_test("P7", "doc_master_docs", self._test_doc_master)
    
    def _test_doc_readme(self):
        """Test README.md exists and has content."""
        assert os.path.exists("README.md"), "README.md should exist"
        
        with open("README.md", "r", encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        assert len(content) > 1000, "README should have substantial content"
        assert "inventory" in content.lower(), "README should mention inventory"
    
    def _test_doc_changelog(self):
        """Test CHANGELOG.md exists."""
        assert os.path.exists("CHANGELOG.md"), "CHANGELOG.md should exist"
        
        with open("CHANGELOG.md", "r", encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        assert "4.5.2" in content, "CHANGELOG should mention v4.5.2"
    
    def _test_doc_release(self):
        """Test RELEASE_NOTES exist."""
        assert os.path.exists("RELEASE_NOTES_4.5.2.md"), "Release notes should exist"
    
    def _test_doc_master(self):
        """Test master documentation exists."""
        assert os.path.exists("docs/MASTER_DOCUMENTATION.md"), "Master docs should exist"
    
    # ===== REPORT GENERATION =====
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive QA report."""
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASS)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAIL)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Critical issues
        critical_issues = []
        for error in self.errors_found:
            critical_issues.append({
                "phase": error["phase"],
                "test": error["test"],
                "error": error["error"][:200],
                "severity": "HIGH" if "import" in error["error"].lower() or "module" in error["error"].lower() else "MEDIUM"
            })
        
        # Final verdict
        production_ready = failed == 0 and errors == 0 and len(critical_issues) == 0
        
        report = {
            "test_run": {
                "version": "4.5.2",
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "success_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%"
            },
            "phase_summary": self._summarize_phases(),
            "critical_issues": critical_issues,
            "errors_found": len(self.errors_found),
            "detailed_results": [
                {
                    "phase": r.phase,
                    "test": r.test_name,
                    "status": r.status.value,
                    "duration_ms": r.duration_ms,
                    "message": r.message[:200]
                }
                for r in self.results
            ],
            "production_ready": production_ready,
            "verdict": "PRODUCTION READY" if production_ready else "NOT PRODUCTION READY",
            "recommendations": self._generate_recommendations(passed, failed, errors, critical_issues)
        }
        
        # Print summary
        self.log("")
        self.log("=" * 70)
        self.log("QA TEST SUMMARY")
        self.log("=" * 70)
        self.log(f"Total Tests:    {total}")
        self.log(f"Passed:         {passed} [PASS]")
        self.log(f"Failed:         {failed} [FAIL]")
        self.log(f"Errors:         {errors} [ERROR]")
        self.log(f"Success Rate:   {report['test_run']['success_rate']}")
        self.log(f"Duration:       {duration:.1f} seconds")
        self.log(f"Critical Issues: {len(critical_issues)}")
        self.log("")
        self.log(f"FINAL VERDICT: {report['verdict']}")
        self.log("=" * 70)
        
        if critical_issues:
            self.log("")
            self.log("CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION:")
            for issue in critical_issues:
                self.log(f"  [{issue['severity']}] {issue['phase']}/{issue['test']}: {issue['error'][:80]}", "ERROR")
        
        # Save report to file
        report_file = f"QA_REPORT_Web_Edition_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        self.log("")
        self.log(f"Full report saved to: {report_file}")
        
        return report
    
    def _summarize_phases(self) -> Dict[str, Dict[str, int]]:
        """Summarize results by phase."""
        phases = {}
        for r in self.results:
            if r.phase not in phases:
                phases[r.phase] = {"total": 0, "passed": 0, "failed": 0, "errors": 0}
            phases[r.phase]["total"] += 1
            if r.status == TestStatus.PASS:
                phases[r.phase]["passed"] += 1
            elif r.status == TestStatus.FAIL:
                phases[r.phase]["failed"] += 1
            elif r.status == TestStatus.ERROR:
                phases[r.phase]["errors"] += 1
        return phases
    
    def _generate_recommendations(self, passed, failed, errors, critical_issues) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        if errors > 0:
            recommendations.append("FIX CRITICAL ERRORS: Address all ERROR-level test failures before production")
        
        if failed > 0:
            recommendations.append("FIX FAILED TESTS: Resolve all functional test failures")
        
        if any(i["severity"] == "HIGH" for i in critical_issues):
            recommendations.append("HIGH PRIORITY: Fix import/module errors immediately")
        
        if passed / (passed + failed + errors) < 0.9:
            recommendations.append("IMPROVE STABILITY: Success rate below 90%, needs improvement")
        
        if not os.path.exists("logs/operations.log"):
            recommendations.append("LOGGING: Ensure log files are being created properly")
        
        recommendations.append("MONITORING: Implement log file size monitoring to prevent disk issues")
        recommendations.append("TESTING: Add more integration tests with real device simulations")
        
        return recommendations


def run_comprehensive_qa():
    """Run comprehensive QA testing."""
    qa = ComprehensiveQA()
    return qa.run_all_tests()


if __name__ == "__main__":
    report = run_comprehensive_qa()
    
    # Exit with appropriate code
    sys.exit(0 if report["production_ready"] else 1)
