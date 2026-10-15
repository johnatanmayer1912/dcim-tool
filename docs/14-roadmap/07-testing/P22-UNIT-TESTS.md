# P22: Unit Tests

| Field | Value |
|-------|-------|
| **Prompt ID** | P22 |
| **Phase** | 07-testing |
| **Dependency Level** | 6 (Depends on Phases 2, 5) |
| **Estimated Time** | 10 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct unit tests for individual modules. This provides test coverage for core modules and utilities.

---

## Prerequisites

- Phase 2 (Core Modules) completed
- Phase 5 (Utilities) completed
- pytest installed
- Python environment set up

---

## Instructions

### Step 1: Create tests Directory Structure

```bash
mkdir -p tests/modules
mkdir -p tests/integration
```

---

### Step 2: Create tests/__init__.py

```python
"""
Test Suite
"""
```

---

### Step 3: Create tests/modules/test_network_base.py

```python
"""
Unit tests for network_base module
"""

import pytest
from modules.network_base import build_json, resolve_hostname_from_prompt, get_device_type_from_prompt

def test_build_json():
    """Test build_json function"""
    result = build_json('10.1.1.1', 'success', {'test': 'data'}, None)
    assert result['host'] == '10.1.1.1'
    assert result['status'] == 'success'
    assert result['data'] == {'test': 'data'}
    assert result['error'] is None
    assert 'timestamp' in result

def test_build_json_with_error():
    """Test build_json with error"""
    result = build_json('10.1.1.1', 'error', None, 'Test error')
    assert result['status'] == 'error'
    assert result['error'] == 'Test error'
    assert result['data'] is None

def test_resolve_hostname_from_prompt():
    """Test hostname resolution"""
    prompt = 'Router1#'
    hostname = resolve_hostname_from_prompt(prompt)
    assert hostname == 'Router1'

def test_get_device_type_from_prompt():
    """Test device type detection"""
    ios_prompt = 'Router1#'
    nxos_prompt = 'Switch1(nx-os)#'
    junos_prompt = 'Router1@junos>'
    
    assert get_device_type_from_prompt(ios_prompt) == 'cisco_ios'
    assert get_device_type_from_prompt(nxos_prompt) == 'cisco_nxos'
    assert get_device_type_from_prompt(junos_prompt) == 'juniper_junos'
```

---

### Step 4: Create tests/modules/test_validation_utilities.py

```python
"""
Unit tests for validation_utilities module
"""

import pytest
from modules.validation_utilities import (
    validate_ip_address,
    validate_mac_address,
    validate_vlan_id,
    validate_hostname
)

def test_validate_ip_address_valid():
    """Test valid IP address"""
    result = validate_ip_address('10.1.1.1')
    assert result['valid'] == True

def test_validate_ip_address_invalid():
    """Test invalid IP address"""
    result = validate_ip_address('invalid')
    assert result['valid'] == False

def test_validate_mac_address_valid():
    """Test valid MAC address"""
    result = validate_mac_address('00:11:22:33:44:55')
    assert result['valid'] == True

def test_validate_mac_address_invalid():
    """Test invalid MAC address"""
    result = validate_mac_address('invalid')
    assert result['valid'] == False

def test_validate_vlan_id_valid():
    """Test valid VLAN ID"""
    result = validate_vlan_id('100')
    assert result['valid'] == True

def test_validate_vlan_id_invalid():
    """Test invalid VLAN ID"""
    result = validate_vlan_id('5000')
    assert result['valid'] == False

def test_validate_hostname_valid():
    """Test valid hostname"""
    result = validate_hostname('router1')
    assert result['valid'] == True

def test_validate_hostname_invalid():
    """Test invalid hostname"""
    result = validate_hostname('invalid hostname!')
    assert result['valid'] == False
```

---

### Step 5: Create tests/modules/test_parsing_utilities.py

```python
"""
Unit tests for parsing_utilities module
"""

import pytest
from modules.parsing_utilities import (
    parse_cisco_ios_show_version,
    parse_vlan_output
)

def test_parse_cisco_ios_show_version():
    """Test Cisco IOS version parsing"""
    output = "Cisco IOS Software, Version 15.2(4)E5"
    result = parse_cisco_ios_show_version(output)
    assert 'version' in result
    assert result['version'] == '15.2(4)E5'

def test_parse_vlan_output():
    """Test VLAN output parsing"""
    output = "1  default  active\n10  data  active"
    result = parse_vlan_output(output, 'cisco_ios')
    assert len(result) == 2
    assert result[0]['vlan_id'] == '1'
    assert result[1]['vlan_id'] == '10'
```

---

### Step 6: Create pytest.ini

```bash
cat > pytest.ini << 'EOF'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --tb=short
    --cov=modules
    --cov-report=html
    --cov-report=term-missing
EOF
```

---

### Step 7: Validate Unit Tests

```bash
# Run unit tests
pytest tests/modules/ -v

# Check coverage
pytest tests/modules/ --cov=modules --cov-report=term-missing
```

---

## Validation Checklist

- [ ] tests directory structure created
- [ ] tests/__init__.py created
- [ ] test_network_base.py created
- [ ] test_validation_utilities.py created
- [ ] test_parsing_utilities.py created
- [ ] pytest.ini created
- [ ] Unit tests passing
- [ ] Test coverage >= 80%
- [ ] Ready for integration tests reconstruction

---

## Troubleshooting

### Issue: Tests fail to import

**Solution:**
- Verify Python path
- Check module structure
- Validate __init__.py files

### Issue: Coverage below 80%

**Solution:**
- Add more test cases
- Test edge cases
- Cover all functions

---

## Next Steps

After completing this prompt, proceed to P23: Integration Tests

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- AUTOMATED_TESTING_DOCUMENTATION.md: ../../02-codebase/AUTOMATED_TESTING_DOCUMENTATION.md
- COMPREHENSIVE_TESTING_COVERAGE.md: ../../02-codebase/COMPREHENSIVE_TESTING_COVERAGE.md
