# Automated Testing Documentation

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | active |
| **Owner** | QA Engineer (R-QA) + Lead Developer (R-ENG) |
| **Last Updated** | 2026-06-02 |
| **Application Version** | 7.0.10 |

---

## Overview

This document provides comprehensive automated testing documentation for Network Swiss Tool Pro, including test suites, testing procedures, test coverage, and CI/CD integration.

---

## Testing Framework

### Test Framework: pytest

**Purpose:** Primary testing framework for unit and integration tests

**Installation:**
```bash
pip install pytest pytest-cov pytest-mock pytest-asyncio
```

**Configuration:** pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --cov=modules
    --cov-report=html
    --cov-report=term-missing
    --tb=short
```

---

## Test Suites

### 1. Unit Tests

**Purpose:** Test individual functions and classes in isolation

**Location:** tests/unit/

**Test Categories:**
- Module tests
- Function tests
- Class tests
- Utility tests

**Example Test:**
```python
import pytest
from modules.network_base import build_json

def test_build_json_success():
    result = build_json('10.1.1.1', 'success', {'data': 'test'}, None)
    assert result['host'] == '10.1.1.1'
    assert result['status'] == 'success'
    assert result['data'] == {'data': 'test'}
    assert result['error'] is None

def test_build_json_error():
    result = build_json('10.1.1.1', 'error', None, 'Test error')
    assert result['host'] == '10.1.1.1'
    assert result['status'] == 'error'
    assert result['data'] is None
    assert result['error'] == 'Test error'
```

**Coverage Target:** 80% minimum for core modules

---

### 2. Integration Tests

**Purpose:** Test interactions between modules and components

**Location:** tests/integration/

**Test Categories:**
- Module integration tests
- API integration tests
- Plugin integration tests
- Database integration tests

**Example Test:**
```python
import pytest
from modules.plugin_registry import PluginRegistry

def test_plugin_discovery():
    registry = PluginRegistry()
    registry.discover_plugins()
    
    assert len(registry.plugins) > 0
    assert 'network_discovery' in registry.plugins

def test_plugin_execution():
    registry = PluginRegistry()
    registry.discover_plugins()
    
    device = get_test_device()
    credentials = get_test_credentials()
    
    result = registry.execute_plugin('network_discovery', device, credentials, {}, {}, log_func)
    assert result['status'] in ['success', 'error']
```

**Coverage Target:** 70% minimum for integration paths

---

### 3. API Tests

**Purpose:** Test REST API endpoints

**Location:** tests/api/

**Test Categories:**
- Endpoint tests
- Request validation tests
- Response validation tests
- Error handling tests

**Example Test:**
```python
import pytest
from flask import Flask
from vlan_checker_web import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    response = client.get('/api/health-check/run')
    assert response.status_code == 200
    data = response.get_json()
    assert 'ok' in data

def test_execute_endpoint(client):
    response = client.post('/api/execute', json={
        'action': 'connectivity',
        'username': 'admin',
        'password': 'password',
        'scope': 'single',
        'devices': ['10.1.1.1']
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
```

**Coverage Target:** 90% minimum for API endpoints

---

### 4. Plugin Tests

**Purpose:** Test plugin functionality

**Location:** tests/plugins/

**Test Categories:**
- Plugin metadata tests
- Plugin execution tests
- Plugin validation tests
- Plugin error handling tests

**Example Test:**
```python
import pytest
from modules.plugins.network_discovery import METADATA, run

def test_plugin_metadata():
    assert 'plugin_id' in METADATA
    assert 'display_name' in METADATA
    assert 'version' in METADATA
    assert METADATA['plugin_id'] == 'network_discovery'

def test_plugin_execution():
    device = get_test_device()
    credentials = get_test_credentials()
    
    result = run(device, credentials, {}, {}, log_func)
    assert result['status'] in ['success', 'error']
```

**Coverage Target:** 85% minimum for plugins

---

### 5. Performance Tests

**Purpose:** Test application performance under load

**Location:** tests/performance/

**Test Categories:**
- Response time tests
- Throughput tests
- Memory usage tests
- CPU usage tests

**Example Test:**
```python
import pytest
import time

def test_api_response_time():
    start_time = time.time()
    response = client.get('/api/health-check/run')
    end_time = time.time()
    
    assert end_time - start_time < 5  # Response time < 5 seconds

def test_bulk_operation_performance():
    devices = get_test_devices(100)
    start_time = time.time()
    
    results = process_devices_parallel(devices, credentials, operation)
    
    end_time = time.time()
    assert end_time - start_time < 60  # Complete in < 60 seconds
```

**Performance Targets:**
- API response time < 5 seconds
- Bulk operation (100 devices) < 60 seconds
- Memory usage < 1 GB peak
- CPU usage < 50% peak

---

### 6. End-to-End Tests

**Purpose:** Test complete user workflows

**Location:** tests/e2e/

**Test Categories:**
- User workflow tests
- Multi-step operation tests
- Cross-platform tests
- Recovery scenario tests

**Example Test:**
```python
def test_complete_discovery_workflow():
    # 1. Load inventory
    inventory = load_inventory('inventory.txt')
    assert len(inventory) > 0
    
    # 2. Run discovery
    job_id = start_discovery(inventory, credentials)
    assert job_id is not None
    
    # 3. Monitor progress
    status = monitor_job(job_id)
    while status['status'] == 'running':
        time.sleep(1)
        status = monitor_job(job_id)
    
    # 4. Verify results
    assert status['status'] == 'complete'
    assert status['devices_discovered'] > 0
    
    # 5. Generate report
    report = generate_discovery_report(job_id)
    assert report is not None
```

**Coverage Target:** 60% minimum for critical workflows

---

## Test Data Management

### Test Fixtures

**Purpose:** Provide reusable test data

**Location:** tests/fixtures/

**Example Fixtures:**
```python
import pytest

@pytest.fixture
def test_device():
    return {
        'host': '10.1.1.1',
        'device_type': 'cisco_ios',
        'username': 'admin',
        'password': 'password'
    }

@pytest.fixture
def test_credentials():
    return {
        'username': 'admin',
        'password': 'password',
        'enable_pwd': 'enable_password'
    }

@pytest.fixture
def mock_connection(mocker):
    mock_conn = mocker.MagicMock()
    mock_conn.send_command.return_value = 'test output'
    return mock_conn
```

---

### Test Data Files

**Purpose:** Provide test data files

**Location:** tests/data/

**File Types:**
- inventory_test.txt - Test inventory file
- policies_test.yaml - Test policy file
- config_test.yaml - Test configuration file
- mock_outputs/ - Mock CLI outputs

---

## Test Execution

### Running All Tests

**Command:**
```bash
pytest
```

**With Coverage:**
```bash
pytest --cov=modules --cov-report=html
```

**Verbose Output:**
```bash
pytest -v
```

---

### Running Specific Test Suites

**Unit Tests:**
```bash
pytest tests/unit/
```

**Integration Tests:**
```bash
pytest tests/integration/
```

**API Tests:**
```bash
pytest tests/api/
```

**Plugin Tests:**
```bash
pytest tests/plugins/
```

**Performance Tests:**
```bash
pytest tests/performance/
```

**E2E Tests:**
```bash
pytest tests/e2e/
```

---

### Running Specific Tests

**By File:**
```bash
pytest tests/unit/test_network_base.py
```

**By Function:**
```bash
pytest tests/unit/test_network_base.py::test_build_json_success
```

**By Class:**
```bash
pytest tests/unit/test_network_base.py::TestNetworkBase
```

**By Marker:**
```bash
pytest -m slow
```

---

## Test Markers

### Marker Definitions

**Purpose:** Categorize tests for selective execution

**Configuration:** pytest.ini
```ini
[pytest]
markers =
    unit: Unit tests
    integration: Integration tests
    api: API tests
    plugin: Plugin tests
    performance: Performance tests
    e2e: End-to-end tests
    slow: Slow running tests
    fast: Fast running tests
```

**Usage:**
```python
import pytest

@pytest.mark.unit
def test_unit_function():
    pass

@pytest.mark.integration
def test_integration_function():
    pass

@pytest.mark.slow
def test_slow_function():
    pass
```

**Execution:**
```bash
pytest -m unit
pytest -m "not slow"
```

---

## Continuous Integration

### CI/CD Pipeline

**Purpose:** Automated testing on code changes

**Platform:** GitHub Actions

**Workflow:** .github/workflows/test.yml

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-mock
    
    - name: Run unit tests
      run: pytest tests/unit/ --cov=modules --cov-report=xml
    
    - name: Run integration tests
      run: pytest tests/integration/
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

---

### Pre-Commit Hooks

**Purpose:** Run tests before committing code

**Tool:** pre-commit

**Configuration:** .pre-commit-config.yaml

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

---

## Test Coverage

### Coverage Goals

| Component | Target Coverage | Current Coverage |
|-----------|----------------|------------------|
| Core Modules | 80% | 85% |
| API Endpoints | 90% | 92% |
| Plugins | 85% | 88% |
| Utilities | 75% | 78% |
| Integration Paths | 70% | 72% |

### Coverage Report

**Generate Coverage Report:**
```bash
pytest --cov=modules --cov-report=html
```

**View Report:**
```bash
open htmlcov/index.html
```

---

## Test Maintenance

### Test Review Process

**Frequency:** Weekly

**Checklist:**
- [ ] All tests passing
- [ ] Coverage meets targets
- [ ] No flaky tests
- [ ] Tests are up to date
- [ ] Test documentation is current

---

### Flaky Test Detection

**Purpose:** Identify and fix flaky tests

**Tool:** pytest-rerunfailures

**Installation:**
```bash
pip install pytest-rerunfailures
```

**Usage:**
```bash
pytest --reruns 3
```

---

### Test Data Updates

**Purpose:** Keep test data current

**Procedure:**
1. Review test data monthly
2. Update with latest device configurations
3. Validate test data format
4. Update test fixtures if needed

---

## Test Documentation

### Test Documentation Requirements

**Each test file must include:**
- Purpose of tests
- Test scenarios covered
- Prerequisites
- Expected results
- Dependencies

**Example:**
```python
"""
Test Network Base Module

Purpose: Test core network operations

Scenarios:
- build_json() with success status
- build_json() with error status
- safe_connection() context manager
- resolve_hostname_from_prompt()

Prerequisites:
- None

Expected Results:
- All tests pass
- Coverage >= 80%

Dependencies:
- modules.network_base
"""
```

---

## Troubleshooting Tests

### Common Test Failures

**Issue:** Test fails intermittently

**Diagnosis:**
1. Check for timing issues
2. Verify test isolation
3. Check for external dependencies
4. Review test data

**Resolution:**
- Add retry logic
- Improve test isolation
- Mock external dependencies
- Update test data

---

**Issue:** Coverage not meeting targets

**Diagnosis:**
1. Review coverage report
2. Identify untested code paths
3. Check for dead code
4. Review test gaps

**Resolution:**
- Add tests for uncovered paths
- Remove dead code
- Improve test coverage
- Update coverage targets

---

**Issue:** Tests too slow

**Diagnosis:**
1. Profile test execution
2. Identify slow tests
3. Check for unnecessary waits
4. Review test setup

**Resolution:**
- Optimize slow tests
- Use mocking for slow operations
- Parallelize test execution
- Improve test fixtures

---

## Best Practices

### Test Design

**Best Practices:**
- Write isolated tests
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Use fixtures for reusable data
- Mock external dependencies

---

### Test Maintenance

**Best Practices:**
- Keep tests up to date with code
- Review tests regularly
- Remove obsolete tests
- Update test data as needed
- Document test changes

---

### Test Execution

**Best Practices:**
- Run tests before committing
- Run tests in CI/CD pipeline
- Monitor test execution time
- Review test results regularly
- Fix failing tests immediately

---

## References

- MODULE_ARCHITECTURE.md - Module architecture
- ERROR_HANDLING_DOCUMENTATION.md - Error handling
- ADVANCED_DEBUGGING_GUIDE.md - Debugging procedures
- PERFORMANCE_OPTIMIZATION.md - Performance optimization
