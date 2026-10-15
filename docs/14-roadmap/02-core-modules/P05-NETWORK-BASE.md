# P05: Network Base

| Field | Value |
|-------|-------|
| **Prompt ID** | P05 |
| **Phase** | 02-core-modules |
| **Dependency Level** | 1 (Depends on Phase 1) |
| **Estimated Time** | 8 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct the network_base module with core network operations. This module provides the foundation for all network operations including device connections, command execution, and data processing.

---

## Prerequisites

- Phase 1 (Foundation) completed
- Python environment set up
- Dependencies installed
- Project structure created

---

## Instructions

### Step 1: Create network_base Module Structure

```bash
cd modules/network_base
```

---

### Step 2: Create __init__.py

```python
"""
Network Base Module

Core network operations for device connectivity and command execution.
"""

from .network_base import (
    build_json,
    safe_connection,
    resolve_hostname_from_prompt,
    get_device_type_from_prompt
)

__all__ = [
    'build_json',
    'safe_connection',
    'resolve_hostname_from_prompt',
    'get_device_type_from_prompt'
]
```

---

### Step 3: Create network_base.py

```python
"""
Network Base Module

Core network operations for device connectivity and command execution.
"""

import re
import time
from contextlib import contextmanager
from netmiko import ConnectHandler, NetmikoTimeoutException
from paramiko import SSHException

def build_json(host, status, data, error):
    """
    Build standardized JSON response
    
    Args:
        host: Device hostname or IP
        status: Operation status (success, error, warning)
        data: Operation data
        error: Error message if any
    
    Returns:
        dict: Standardized JSON response
    """
    return {
        'host': host,
        'status': status,
        'data': data,
        'error': error,
        'timestamp': time.time()
    }

@contextmanager
def safe_connection(device, username, password, secret, log_func):
    """
    Context manager for safe device connection
    
    Args:
        device: Device dictionary
        username: SSH username
        password: SSH password
        secret: Enable secret
        log_func: Logging function
    
    Yields:
        Netmiko connection object
    """
    conn = None
    try:
        device_params = {
            'device_type': device['device_type'],
            'host': device['host'],
            'username': username,
            'password': password,
            'secret': secret,
            'timeout': 30,
            'global_delay_factor': 2
        }
        
        conn = ConnectHandler(**device_params)
        log_func(f"Connected to {device['host']}")
        yield conn
        
    except NetmikoTimeoutException as e:
        log_func(f"Connection timeout to {device['host']}: {e}")
        raise
    except SSHException as e:
        log_func(f"SSH error connecting to {device['host']}: {e}")
        raise
    except Exception as e:
        log_func(f"Error connecting to {device['host']}: {e}")
        raise
    finally:
        if conn:
            try:
                conn.disconnect()
                log_func(f"Disconnected from {device['host']}")
            except:
                pass

def resolve_hostname_from_prompt(prompt):
    """
    Resolve hostname from device prompt
    
    Args:
        prompt: Device prompt string
    
    Returns:
        str: Resolved hostname
    """
    # Try to extract hostname from prompt
    match = re.search(r'(\S+)(>|#|\$)', prompt)
    if match:
        return match.group(1)
    return 'unknown'

def get_device_type_from_prompt(prompt):
    """
    Determine device type from prompt
    
    Args:
        prompt: Device prompt string
    
    Returns:
        str: Device type (cisco_ios, cisco_nxos, juniper_junos)
    """
    if 'nx-os' in prompt.lower():
        return 'cisco_nxos'
    elif 'junos' in prompt.lower():
        return 'juniper_junos'
    else:
        return 'cisco_ios'
```

---

### Step 4: Validate Module

```python
# Test module import
from modules.network_base import build_json, safe_connection

# Test build_json
result = build_json('10.1.1.1', 'success', {'test': 'data'}, None)
assert result['host'] == '10.1.1.1'
assert result['status'] == 'success'
assert result['data'] == {'test': 'data'}
assert result['error'] is None

print("Module validation successful")
```

---

## Validation Checklist

- [ ] network_base module structure created
- [ ] __init__.py created
- [ ] network_base.py created
- [ ] build_json function implemented
- [ ] safe_connection context manager implemented
- [ ] resolve_hostname_from_prompt implemented
- [ ] get_device_type_from_prompt implemented
- [ ] Module validation successful
- [ ] Ready for adapters reconstruction

---

## Troubleshooting

### Issue: Module import fails

**Solution:**
- Verify __init__.py exists
- Check Python path
- Verify module structure

### Issue: Function validation fails

**Solution:**
- Check function signatures
- Verify return values
- Test with sample data

---

## Next Steps

After completing this prompt, proceed to P06: Adapters

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- MODULE_ARCHITECTURE.md: ../../01-architecture/MODULE_ARCHITECTURE.md
- NETWORK_BASE_DOCUMENTATION.md: ../../02-codebase/UTILITIES_DOCUMENTATION.md
