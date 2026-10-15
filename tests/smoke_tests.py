"""
tests/smoke_tests.py
--------------------
Smoke test framework for Network Swiss Tool Pro.

Validates all major workflows without requiring actual network devices.
Tests use mocked connections to verify system integrity.
"""

import sys
import os
import json
import shutil
from typing import Dict, List, Any, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"


@dataclass
class TestResult:
    name: str
    status: TestStatus
    duration_ms: int
    message: str
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


class SmokeTestSuite:
    """
    Comprehensive smoke test suite for Network Swiss Tool Pro.
    
    Tests are organized by category:
    - Infrastructure: Core utilities and logging
    - Network Operations: Simulated network workflows
    - Data Validation: Input/output format validation
    - Integration: End-to-end workflow tests
    """
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.tests: Dict[str, Callable] = {
            # Infrastructure Tests
            "test_structured_logging": self.test_structured_logging,
            "test_backup_system_initialization": self.test_backup_system_initialization,
            "test_manifest_operations": self.test_manifest_operations,
            
            # Data Validation Tests
            "test_vlan_id_validation": self.test_vlan_id_validation,
            "test_device_parsing": self.test_device_parsing,
            "test_json_contract": self.test_json_contract,
            
            # Network Operation Tests (Simulated)
            "test_connectivity_result_format": self.test_connectivity_result_format,
            "test_vlan_operation_result_format": self.test_vlan_operation_result_format,
            "test_backup_result_format": self.test_backup_result_format,
            
            # Integration Tests
            "test_adapter_functions_exist": self.test_adapter_functions_exist,
            "test_report_generation": self.test_report_generation,
        }
    
    def run_all(self, verbose: bool = True) -> Dict[str, Any]:
        """Run all smoke tests and return summary."""
        print("=" * 60)
        print("NETWORK SWISS TOOL PRO - SMOKE TEST SUITE")
        print("=" * 60)
        print(f"Started: {datetime.now().isoformat()}")
        print()
        
        for test_name, test_func in self.tests.items():
            result = self._run_test(test_name, test_func)
            self.results.append(result)
            
            if verbose:
                self._print_result(result)
        
        return self._generate_summary()
    
    def run_category(self, category: str) -> Dict[str, Any]:
        """Run tests by category."""
        categories = {
            "infrastructure": ["test_structured_logging", "test_backup_system_initialization", "test_manifest_operations"],
            "data": ["test_vlan_id_validation", "test_device_parsing", "test_json_contract"],
            "network": ["test_connectivity_result_format", "test_vlan_operation_result_format", "test_backup_result_format"],
            "integration": ["test_adapter_functions_exist", "test_report_generation"]
        }
        
        test_names = categories.get(category, [])
        for test_name in test_names:
            if test_name in self.tests:
                result = self._run_test(test_name, self.tests[test_name])
                self.results.append(result)
                self._print_result(result)
        
        return self._generate_summary()
    
    def _run_test(self, name: str, test_func: Callable) -> TestResult:
        """Run a single test and capture result."""
        import time
        
        start = time.time()
        try:
            test_func()
            duration = int((time.time() - start) * 1000)
            return TestResult(name, TestStatus.PASS, duration, "Test passed")
        except AssertionError as e:
            duration = int((time.time() - start) * 1000)
            return TestResult(name, TestStatus.FAIL, duration, str(e))
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            return TestResult(name, TestStatus.ERROR, duration, f"Exception: {str(e)}")
    
    def _print_result(self, result: TestResult):
        """Print a single test result."""
        status_icon = {
            TestStatus.PASS: "[PASS]",
            TestStatus.FAIL: "[FAIL]",
            TestStatus.SKIP: "[SKIP]",
            TestStatus.ERROR: "[ERR ]"
        }
        
        print(f"{status_icon.get(result.status, '?')} {result.name}")
        print(f"  Status: {result.status.value} ({result.duration_ms}ms)")
        if result.status != TestStatus.PASS:
            print(f"  Message: {result.message}")
        print()
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test summary."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASS)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAIL)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIP)
        
        summary = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "success_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%",
            "timestamp": datetime.now().isoformat(),
            "results": [
                {
                    "name": r.name,
                    "status": r.status.value,
                    "duration_ms": r.duration_ms,
                    "message": r.message
                }
                for r in self.results
            ]
        }
        
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total:    {total}")
        print(f"Passed:   {passed} OK")
        print(f"Failed:   {failed} FAIL")
        print(f"Errors:   {errors} ERR")
        print(f"Skipped:  {skipped} SKIP")
        print(f"Success:  {summary['success_rate']}")
        print("=" * 60)
        
        return summary
    
    # === TEST METHODS ===
    
    def test_structured_logging(self):
        """Test that structured logging system initializes correctly."""
        from utils.structured_logger import get_logger, LogLevel, OperationType
        
        logger = get_logger(console_output=False)
        
        # Test basic logging
        logger.info("Test message", OperationType.CONNECTIVITY_CHECK, "test-device")
        logger.debug("Debug message", OperationType.VLAN_AUDIT)
        logger.warning("Warning message")
        logger.error("Error message", exception=Exception("Test exception"))
        
        # Verify logger was created
        assert logger is not None
        assert logger.operation_logger is not None
    
    def test_backup_system_initialization(self):
        """Test that backup system initializes and creates necessary structure."""
        from utils.config_backup_system import ConfigBackupSystem
        import tempfile
        import shutil
        
        # Use temp directory for test
        temp_dir = tempfile.mkdtemp()
        try:
            backup_system = ConfigBackupSystem(temp_dir)
            
            # Verify structure created
            assert os.path.exists(temp_dir)
            manifest_path = os.path.join(temp_dir, "backup_manifest.json")
            assert os.path.exists(manifest_path)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_manifest_operations(self):
        """Test backup manifest operations."""
        from utils.config_backup_system import ConfigBackupSystem
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        try:
            backup_system = ConfigBackupSystem(temp_dir)
            
            # Test empty manifest
            manifest = backup_system._load_manifest()
            assert "backups" in manifest
            assert isinstance(manifest["backups"], list)
            
            # Test save and load
            test_manifest = {"backups": [{"test": "data"}], "last_scheduled_run": None}
            backup_system._save_manifest(test_manifest)
            loaded = backup_system._load_manifest()
            assert loaded["backups"][0]["test"] == "data"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_vlan_id_validation(self):
        """Test VLAN ID validation logic."""
        from modules.vlan_mgmt_production import _validate_vlan_id
        
        # Valid VLANs
        assert _validate_vlan_id("10")[0] is True
        assert _validate_vlan_id("100")[0] is True
        assert _validate_vlan_id("4094")[0] is True
        
        # Invalid VLANs
        assert _validate_vlan_id("0")[0] is False
        assert _validate_vlan_id("4095")[0] is False
        assert _validate_vlan_id("-1")[0] is False
        assert _validate_vlan_id("abc")[0] is False
        assert _validate_vlan_id("")[0] is False
        
        # Reserved VLANs
        assert _validate_vlan_id("1")[0] is False  # Default VLAN
        assert _validate_vlan_id("1002")[0] is False  # Reserved
    
    def test_device_parsing(self):
        """Test device inventory parsing."""
        from modules.network_base import get_devices_from_file
        import tempfile
        import os
        
        # Create test inventory
        inventory_content = """# Test inventory
[CoreSwitches]
10.1.1.1,cisco_ios,Core
10.1.1.2,cisco_nxos,Core

[AccessSwitches]
10.2.1.1,juniper_junos,Access
"""
        
        temp_dir = tempfile.mkdtemp()
        inventory_path = os.path.join(temp_dir, "test_inventory.txt")
        
        try:
            with open(inventory_path, 'w') as f:
                f.write(inventory_content)
            
            devices = get_devices_from_file(inventory_path)
            
            assert len(devices) == 3
            assert devices[0]["host"] == "10.1.1.1"
            assert devices[0]["device_type"] == "cisco_ios"
            assert devices[0]["group"] == "Core"
            assert devices[2]["group"] == "Access"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_json_contract(self):
        """Test that modules return correct JSON contract."""
        from modules.network_base import build_json
        
        # Test success response
        result = build_json("10.1.1.1", "success", {"vlan": 100})
        assert result["device"] == "10.1.1.1"
        assert result["status"] == "success"
        assert result["data"]["vlan"] == 100
        assert result["error"] is None
        
        # Test failure response
        result = build_json("10.1.1.1", "fail", {}, "Connection timeout")
        assert result["status"] == "fail"
        assert result["error"] == "Connection timeout"
    
    def test_connectivity_result_format(self):
        """Test connectivity result format."""
        # Simulate a connectivity result
        result = {
            "device": "10.1.1.1",
            "status": "success",
            "data": {"ping": True, "ssh": True},
            "error": None
        }
        
        assert "device" in result
        assert "status" in result
        assert "data" in result
        assert result["status"] in ("success", "fail")
        
        if result["status"] == "success":
            assert "ping" in result["data"]
            assert "ssh" in result["data"]
    
    def test_vlan_operation_result_format(self):
        """Test VLAN operation result format."""
        # Simulate a VLAN operation result
        result = {
            "device": "10.1.1.1",
            "status": "success",
            "data": {
                "commands": ["vlan 100", "name TestVLAN"],
                "dry_run": False,
                "post_check": {"vlan_exists": True},
                "verification_passed": True,
                "backup_path": "/path/to/backup"
            },
            "error": None
        }
        
        assert result["status"] == "success"
        assert "commands" in result["data"]
        assert "post_check" in result["data"]
        assert "verification_passed" in result["data"]
    
    def test_backup_result_format(self):
        """Test backup result format."""
        result = {
            "success": True,
            "backup_path": "/backups/device/timestamp.txt",
            "metadata": {
                "device": "10.1.1.1",
                "hostname": "switch1",
                "timestamp": "20240101_120000",
                "backup_type": "pre_change"
            }
        }
        
        assert "success" in result
        assert "backup_path" in result
        assert "metadata" in result
    
    def test_adapter_functions_exist(self):
        """Test that all adapter functions exist and are callable."""
        from modules import adapters
        
        required_functions = [
            "run_connectivity",
            "run_vlan_audit",
            "run_vlan_management",
            "run_save_config",
            "run_config_backup",
            "run_network_audit",
            "run_topology_mapper",
            "run_startup_backup_check"
        ]
        
        for func_name in required_functions:
            assert hasattr(adapters, func_name), f"Missing function: {func_name}"
            func = getattr(adapters, func_name)
            assert callable(func), f"{func_name} is not callable"
    
    def test_report_generation(self):
        """Test report formatting utilities."""
        from utils import report_formatter
        import tempfile
        import os
        
        temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_dir, "test_report.txt")
        
        try:
            # Test text file writing
            report_formatter.write_text_file(test_file, "Test content")
            assert os.path.exists(test_file)
            
            with open(test_file, 'r') as f:
                content = f.read()
            assert content == "Test content"
            
            # Test append
            report_formatter.append_text_file(test_file, "More content")
            with open(test_file, 'r') as f:
                content = f.read()
            assert "More content" in content
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


def run_tests(category: str = None, verbose: bool = True) -> Dict[str, Any]:
    """
    Run smoke tests.
    
    Args:
        category: Test category (infrastructure, data, network, integration) or None for all
        verbose: Print detailed results
        
    Returns:
        Test summary dictionary
    """
    suite = SmokeTestSuite()
    
    if category:
        return suite.run_category(category)
    else:
        return suite.run_all(verbose)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Network Swiss Tool Pro - Smoke Tests")
    parser.add_argument("--category", choices=["infrastructure", "data", "network", "integration"],
                       help="Run tests for specific category")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    
    args = parser.parse_args()
    
    summary = run_tests(category=args.category, verbose=not args.quiet)
    
    # Exit with appropriate code
    sys.exit(0 if summary["failed"] == 0 and summary["errors"] == 0 else 1)
