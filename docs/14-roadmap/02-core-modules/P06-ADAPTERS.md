# P06: Adapters

| Field | Value |
|-------|-------|
| **Prompt ID** | P06 |
| **Phase** | 02-core-modules |
| **Dependency Level** | 2 (Depends on P05) |
| **Estimated Time** | 7 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct the adapters module for platform-specific operations. This module provides platform-specific adapters for Cisco IOS, Cisco NX-OS, and Juniper JunOS devices.

---

## Prerequisites

- P05: Network Base completed
- network_base module functional
- Dependencies installed

---

## Instructions

### Step 1: Create adapters Module Structure

```bash
cd modules/adapters
```

---

### Step 2: Create __init__.py

```python
"""
Adapters Module

Platform-specific adapters for different network device types.
"""

from .cisco_ios_adapter import CiscoIOSAdapter
from .cisco_nxos_adapter import CiscoNXOSAdapter
from .juniper_junos_adapter import JuniperJunOSAdapter
from .adapter_factory import get_adapter

__all__ = [
    'CiscoIOSAdapter',
    'CiscoNXOSAdapter',
    'JuniperJunOSAdapter',
    'get_adapter'
]
```

---

### Step 3: Create adapter_factory.py

```python
"""
Adapter Factory

Factory for creating platform-specific adapters.
"""

from .cisco_ios_adapter import CiscoIOSAdapter
from .cisco_nxos_adapter import CiscoNXOSAdapter
from .juniper_junos_adapter import JuniperJunOSAdapter

ADAPTER_MAP = {
    'cisco_ios': CiscoIOSAdapter,
    'cisco_nxos': CiscoNXOSAdapter,
    'juniper_junos': JuniperJunOSAdapter
}

def get_adapter(device_type):
    """
    Get adapter for device type
    
    Args:
        device_type: Device type string
    
    Returns:
        Adapter class for device type
    """
    adapter_class = ADAPTER_MAP.get(device_type)
    if adapter_class:
        return adapter_class
    raise ValueError(f"Unsupported device type: {device_type}")
```

---

### Step 4: Create cisco_ios_adapter.py

```python
"""
Cisco IOS Adapter

Platform-specific adapter for Cisco IOS devices.
"""

class CiscoIOSAdapter:
    """Adapter for Cisco IOS devices"""
    
    def __init__(self):
        self.device_type = 'cisco_ios'
    
    def get_connection_params(self, device):
        """Get connection parameters for Cisco IOS"""
        return {
            'device_type': 'cisco_ios',
            'host': device['host'],
            'username': device['username'],
            'password': device['password'],
            'secret': device.get('secret'),
            'timeout': 30,
            'global_delay_factor': 2,
            'fast_cli': True
        }
    
    def configure_terminal(self, conn):
        """Configure terminal settings for Cisco IOS"""
        conn.send_command('terminal length 0')
        conn.send_command('terminal width 512')
        conn.send_command('terminal no exec-timeout')
    
    def get_show_command(self, operation):
        """Get show command for operation"""
        commands = {
            'version': 'show version',
            'interfaces': 'show interface brief',
            'vlan': 'show vlan brief',
            'running_config': 'show running-config'
        }
        return commands.get(operation, '')
```

---

### Step 5: Create cisco_nxos_adapter.py

```python
"""
Cisco NX-OS Adapter

Platform-specific adapter for Cisco NX-OS devices.
"""

class CiscoNXOSAdapter:
    """Adapter for Cisco NX-OS devices"""
    
    def __init__(self):
        self.device_type = 'cisco_nxos'
    
    def get_connection_params(self, device):
        """Get connection parameters for Cisco NX-OS"""
        return {
            'device_type': 'cisco_nxos',
            'host': device['host'],
            'username': device['username'],
            'password': device['password'],
            'secret': device.get('secret'),
            'timeout': 30,
            'global_delay_factor': 2,
            'fast_cli': True
        }
    
    def configure_terminal(self, conn):
        """Configure terminal settings for Cisco NX-OS"""
        conn.send_command('terminal length 0')
        conn.send_command('terminal width 512')
    
    def get_show_command(self, operation):
        """Get show command for operation with JSON output"""
        commands = {
            'version': 'show version | json',
            'interfaces': 'show interface brief | json',
            'vlan': 'show vlan | json',
            'running_config': 'show running-config'
        }
        return commands.get(operation, '')
```

---

### Step 6: Create juniper_junos_adapter.py

```python
"""
Juniper JunOS Adapter

Platform-specific adapter for Juniper JunOS devices.
"""

class JuniperJunOSAdapter:
    """Adapter for Juniper JunOS devices"""
    
    def __init__(self):
        self.device_type = 'juniper_junos'
    
    def get_connection_params(self, device):
        """Get connection parameters for Juniper JunOS"""
        return {
            'device_type': 'juniper_junos',
            'host': device['host'],
            'username': device['username'],
            'password': device['password'],
            'secret': device.get('secret'),
            'timeout': 30,
            'global_delay_factor': 2,
            'fast_cli': True
        }
    
    def configure_terminal(self, conn):
        """Configure terminal settings for Juniper JunOS"""
        conn.send_command('set cli screen-length 0')
        conn.send_command('set cli screen-width 512')
    
    def get_show_command(self, operation):
        """Get show command for operation with XML output"""
        commands = {
            'version': 'show version | display xml',
            'interfaces': 'show interfaces terse | display xml',
            'vlan': 'show vlan | display xml',
            'configuration': 'show configuration | display set'
        }
        return commands.get(operation, '')
```

---

### Step 7: Validate Module

```python
# Test module import
from modules.adapters import get_adapter, CiscoIOSAdapter, CiscoNXOSAdapter, JuniperJunOSAdapter

# Test adapter factory
ios_adapter = get_adapter('cisco_ios')
assert isinstance(ios_adapter, CiscoIOSAdapter)

nxos_adapter = get_adapter('cisco_nxos')
assert isinstance(nxos_adapter, CiscoNXOSAdapter)

junos_adapter = get_adapter('juniper_junos')
assert isinstance(junos_adapter, JuniperJunOSAdapter)

# Test adapter methods
ios_adapter = CiscoIOSAdapter()
params = ios_adapter.get_connection_params({'host': '10.1.1.1', 'username': 'admin', 'password': 'password'})
assert params['device_type'] == 'cisco_ios'

print("Module validation successful")
```

---

## Validation Checklist

- [ ] adapters module structure created
- [ ] __init__.py created
- [ ] adapter_factory.py created
- [ ] cisco_ios_adapter.py created
- [ ] cisco_nxos_adapter.py created
- [ ] juniper_junos_adapter.py created
- [ ] Adapter factory implemented
- [ ] All adapters implemented
- [ ] Module validation successful
- [ ] Ready for connectivity reconstruction

---

## Troubleshooting

### Issue: Adapter import fails

**Solution:**
- Verify __init__.py exists
- Check Python path
- Verify adapter files exist

### Issue: Adapter factory returns wrong adapter

**Solution:**
- Check ADAPTER_MAP configuration
- Verify device type strings
- Test adapter instantiation

---

## Next Steps

After completing this prompt, proceed to P07: Connectivity

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- MODULE_ARCHITECTURE.md: ../../01-architecture/MODULE_ARCHITECTURE.md
- PLATFORM_SPECIFIC_OPTIMIZATIONS.md: ../../02-codebase/PLATFORM_SPECIFIC_OPTIMIZATIONS.md
