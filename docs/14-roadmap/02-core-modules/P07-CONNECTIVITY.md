# P07: Connectivity

| Field | Value |
|-------|-------|
| **Prompt ID** | P07 |
| **Phase** | 02-core-modules |
| **Dependency Level** | 3 (Depends on P05, P06) |
| **Estimated Time** | 8 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct the connectivity module for device connections. This module handles device connectivity, connection pooling, and connection management.

---

## Prerequisites

- P05: Network Base completed
- P06: Adapters completed
- network_base module functional
- adapters module functional

---

## Instructions

### Step 1: Create connectivity Module Structure

```bash
cd modules/connectivity
```

---

### Step 2: Create __init__.py

```python
"""
Connectivity Module

Device connectivity and connection management.
"""

from .connection_pool import ConnectionPool
from .connectivity import (
    connect_to_device,
    disconnect_from_device,
    test_connection
)

__all__ = [
    'ConnectionPool',
    'connect_to_device',
    'disconnect_from_device',
    'test_connection'
]
```

---

### Step 3: Create connection_pool.py

```python
"""
Connection Pool

Connection pooling for efficient device connections.
"""

import threading
from queue import Queue
from netmiko import ConnectHandler

class ConnectionPool:
    """Connection pool for device connections"""
    
    def __init__(self, max_connections=10):
        self.max_connections = max_connections
        self.connections = {}
        self.lock = threading.Lock()
        self.available = Queue(max_connections)
    
    def get_connection(self, device, username, password, secret):
        """Get connection from pool or create new one"""
        with self.lock:
            device_key = f"{device['host']}:{device['device_type']}"
            
            if device_key in self.connections:
                return self.connections[device_key]
            
            if len(self.connections) >= self.max_connections:
                raise Exception("Connection pool exhausted")
            
            # Create new connection
            conn = ConnectHandler(
                device_type=device['device_type'],
                host=device['host'],
                username=username,
                password=password,
                secret=secret,
                timeout=30
            )
            
            self.connections[device_key] = conn
            return conn
    
    def release_connection(self, device):
        """Release connection back to pool"""
        with self.lock:
            device_key = f"{device['host']}:{device['device_type']}"
            
            if device_key in self.connections:
                conn = self.connections[device_key]
                try:
                    conn.disconnect()
                except:
                    pass
                del self.connections[device_key]
    
    def clear_pool(self):
        """Clear all connections from pool"""
        with self.lock:
            for device_key, conn in self.connections.items():
                try:
                    conn.disconnect()
                except:
                    pass
            self.connections.clear()
```

---

### Step 4: Create connectivity.py

```python
"""
Connectivity Module

Device connectivity functions.
"""

from netmiko import ConnectHandler, NetmikoTimeoutException
from paramiko import SSHException
from modules.adapters import get_adapter
from modules.network_base import build_json

def connect_to_device(device, username, password, secret, log_func):
    """
    Connect to network device
    
    Args:
        device: Device dictionary
        username: SSH username
        password: SSH password
        secret: Enable secret
        log_func: Logging function
    
    Returns:
        dict: Connection result
    """
    try:
        # Get adapter for device type
        adapter = get_adapter(device['device_type'])
        
        # Get connection parameters
        params = adapter.get_connection_params(device)
        params['username'] = username
        params['password'] = password
        params['secret'] = secret
        
        # Connect to device
        conn = ConnectHandler(**params)
        
        # Configure terminal settings
        adapter.configure_terminal(conn)
        
        log_func(f"Connected to {device['host']}")
        
        return build_json(device['host'], 'success', {'connected': True}, None)
        
    except NetmikoTimeoutException as e:
        log_func(f"Connection timeout to {device['host']}: {e}")
        return build_json(device['host'], 'error', None, f"Connection timeout: {e}")
        
    except SSHException as e:
        log_func(f"SSH error connecting to {device['host']}: {e}")
        return build_json(device['host'], 'error', None, f"SSH error: {e}")
        
    except Exception as e:
        log_func(f"Error connecting to {device['host']}: {e}")
        return build_json(device['host'], 'error', None, f"Connection error: {e}")

def disconnect_from_device(conn, device, log_func):
    """
    Disconnect from network device
    
    Args:
        conn: Netmiko connection object
        device: Device dictionary
        log_func: Logging function
    
    Returns:
        dict: Disconnection result
    """
    try:
        if conn:
            conn.disconnect()
            log_func(f"Disconnected from {device['host']}")
            return build_json(device['host'], 'success', {'disconnected': True}, None)
        return build_json(device['host'], 'warning', None, 'No active connection')
        
    except Exception as e:
        log_func(f"Error disconnecting from {device['host']}: {e}")
        return build_json(device['host'], 'error', None, f"Disconnection error: {e}")

def test_connection(device, username, password, secret, log_func):
    """
    Test connection to device
    
    Args:
        device: Device dictionary
        username: SSH username
        password: SSH password
        secret: Enable secret
        log_func: Logging function
    
    Returns:
        dict: Test result
    """
    try:
        # Get adapter for device type
        adapter = get_adapter(device['device_type'])
        
        # Get connection parameters
        params = adapter.get_connection_params(device)
        params['username'] = username
        params['password'] = password
        params['secret'] = secret
        
        # Connect to device
        conn = ConnectHandler(**params)
        
        # Test with simple command
        output = conn.send_command('show version', read_timeout=10)
        
        # Disconnect
        conn.disconnect()
        
        if output:
            log_func(f"Connection test successful for {device['host']}")
            return build_json(device['host'], 'success', {'test': 'passed'}, None)
        else:
            return build_json(device['host'], 'error', None, 'No output received')
            
    except Exception as e:
        log_func(f"Connection test failed for {device['host']}: {e}")
        return build_json(device['host'], 'error', None, f"Test failed: {e}")
```

---

### Step 5: Validate Module

```python
# Test module import
from modules.connectivity import ConnectionPool, connect_to_device, test_connection

# Test connection pool
pool = ConnectionPool(max_connections=5)
assert pool.max_connections == 5
assert len(pool.connections) == 0

# Test connection pool clear
pool.clear_pool()
assert len(pool.connections) == 0

print("Module validation successful")
```

---

## Validation Checklist

- [ ] connectivity module structure created
- [ ] __init__.py created
- [ ] connection_pool.py created
- [ ] connectivity.py created
- [ ] ConnectionPool implemented
- [ ] connect_to_device implemented
- [ ] disconnect_from_device implemented
- [ ] test_connection implemented
- [ ] Module validation successful
- [ ] Ready for interfaces reconstruction

---

## Troubleshooting

### Issue: Connection pool exhaustion

**Solution:**
- Increase max_connections
- Implement connection timeout
- Check for connection leaks

### Issue: Connection test fails

**Solution:**
- Verify device credentials
- Check network connectivity
- Verify device accessibility

---

## Next Steps

After completing this prompt, proceed to P08: Interfaces

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- MODULE_ARCHITECTURE.md: ../../01-architecture/MODULE_ARCHITECTURE.md
- NETWORK_BASE_DOCUMENTATION.md: ../../02-codebase/UTILITIES_DOCUMENTATION.md
