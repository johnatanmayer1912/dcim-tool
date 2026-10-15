# P23: Integration Tests

| Field | Value |
|-------|-------|
| **Prompt ID** | P23 |
| **Phase** | 07-testing |
| **Dependency Level** | 6 (Depends on Phase 6) |
| **Estimated Time** | 10 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct integration tests for module interactions. This provides test coverage for module integration, API integration, and database integration.

---

## Prerequisites

- Phase 6 (Integration) completed
- Phase 7 (Unit Tests) completed
- pytest installed
- Python environment set up

---

## Instructions

### Step 1: Create tests/integration/test_module_integration.py

```python
"""
Integration tests for module_integration module
"""

import pytest
from modules.module_integration import ModuleIntegrator
from modules.plugin_registry import PluginRegistry

@pytest.fixture
def integrator():
    """Create module integrator fixture"""
    return ModuleIntegrator()

def test_integrator_initialization(integrator):
    """Test integrator initialization"""
    assert integrator.plugin_registry is not None
    assert integrator.connection_pool is not None
    assert integrator.logger is not None

def test_plugin_registry_integration(integrator):
    """Test plugin registry integration"""
    plugins = integrator.plugin_registry.list_plugins()
    assert len(plugins) > 0

def test_execute_plugin_on_device(integrator):
    """Test plugin execution on device"""
    device = {'host': '10.1.1.1', 'device_type': 'cisco_ios'}
    credentials = {'username': 'admin', 'password': 'password'}
    params = {}
    
    result = integrator.execute_plugin_on_device(
        'network_discovery',
        device,
        credentials,
        params
    )
    
    assert result is not None
    assert 'status' in result

def test_execute_plugin_on_devices(integrator):
    """Test plugin execution on multiple devices"""
    devices = [
        {'host': '10.1.1.1', 'device_type': 'cisco_ios'},
        {'host': '10.1.1.2', 'device_type': 'cisco_ios'}
    ]
    credentials = {'username': 'admin', 'password': 'password'}
    params = {}
    
    result = integrator.execute_plugin_on_devices(
        'network_discovery',
        devices,
        credentials,
        params
    )
    
    assert result is not None
    assert result['total_devices'] == 2
    assert 'results' in result
```

---

### Step 2: Create tests/integration/test_database_integration.py

```python
"""
Integration tests for database_integration module
"""

import pytest
import os
from modules.database_integration import DatabaseManager

@pytest.fixture
def db_manager():
    """Create database manager fixture"""
    db_path = 'test_integration.db'
    db = DatabaseManager(db_path)
    yield db
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)

def test_database_initialization(db_manager):
    """Test database initialization"""
    assert db_manager.db_path == 'test_integration.db'

def test_add_device(db_manager):
    """Test adding device to database"""
    device = {
        'host': '10.1.1.1',
        'device_type': 'cisco_ios',
        'hostname': 'router1',
        'serial_number': 'SN12345'
    }
    device_id = db_manager.add_device(device)
    assert device_id > 0

def test_get_device(db_manager):
    """Test retrieving device from database"""
    device = {
        'host': '10.1.1.1',
        'device_type': 'cisco_ios',
        'hostname': 'router1'
    }
    db_manager.add_device(device)
    
    retrieved = db_manager.get_device('10.1.1.1')
    assert retrieved is not None
    assert retrieved['host'] == '10.1.1.1'

def test_create_and_get_job(db_manager):
    """Test job creation and retrieval"""
    device = {'host': '10.1.1.1', 'device_type': 'cisco_ios'}
    db_manager.add_device(device)
    
    job_id = 'test-job-123'
    db_manager.create_job(job_id, 'network_discovery', [device])
    
    job = db_manager.get_job(job_id)
    assert job is not None
    assert job['job_id'] == job_id
    assert job['status'] == 'pending'

def test_update_job_status(db_manager):
    """Test updating job status"""
    device = {'host': '10.1.1.1', 'device_type': 'cisco_ios'}
    db_manager.add_device(device)
    
    job_id = 'test-job-456'
    db_manager.create_job(job_id, 'network_discovery', [device])
    
    db_manager.update_job_status(job_id, 'complete', results=[{'test': 'data'}])
    
    job = db_manager.get_job(job_id)
    assert job['status'] == 'complete'
    assert job['results'] == [{'test': 'data'}]
```

---

### Step 3: Create tests/integration/test_api_integration.py

```python
"""
Integration tests for API integration
"""

import pytest
import json
from flask import Flask
from flask_socketio import SocketIO
from modules.api_integration import APIIntegrator

@pytest.fixture
def api_integrator():
    """Create API integrator fixture"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret'
    socketio = SocketIO(app)
    
    integrator = APIIntegrator(app, socketio)
    return integrator, app

def test_api_route_registration(api_integrator):
    """Test API route registration"""
    integrator, app = api_integrator
    
    with app.test_client() as client:
        response = client.get('/api/v1/plugins')
        assert response.status_code in [200, 500]

def test_plugin_execution_endpoint(api_integrator):
    """Test plugin execution endpoint"""
    integrator, app = api_integrator
    
    with app.test_client() as client:
        response = client.post('/api/v1/plugins/network_discovery/execute',
                               json={
                                   'device': {'host': '10.1.1.1', 'device_type': 'cisco_ios'},
                                   'credentials': {'username': 'admin', 'password': 'password'},
                                   'params': {}
                               })
        assert response.status_code in [200, 500]
```

---

### Step 4: Validate Integration Tests

```bash
# Run integration tests
pytest tests/integration/ -v

# Check coverage
pytest tests/integration/ --cov=modules --cov-report=term-missing
```

---

## Validation Checklist

- [ ] test_module_integration.py created
- [ ] test_database_integration.py created
- [ ] test_api_integration.py created
- [ ] Integration tests passing
- [ ] Module interactions tested
- [ ] Database operations tested
- [ ] API endpoints tested
- [ ] Ready for test execution reconstruction

---

## Troubleshooting

### Issue: Integration tests fail

**Solution:**
- Verify module dependencies
- Check database initialization
- Test with mock data

### Issue: API tests fail

**Solution:**
- Verify Flask app initialization
- Check route registration
- Test with test client

---

## Next Steps

After completing this prompt, proceed to P24: Test Execution

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- AUTOMATED_TESTING_DOCUMENTATION.md: ../../02-codebase/AUTOMATED_TESTING_DOCUMENTATION.md
- COMPREHENSIVE_TESTING_COVERAGE.md: ../../02-codebase/COMPREHENSIVE_TESTING_COVERAGE.md
