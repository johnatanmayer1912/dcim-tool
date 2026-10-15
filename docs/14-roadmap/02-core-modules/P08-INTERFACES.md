# P08: Interfaces

| Field | Value |
|-------|-------|
| **Prompt ID** | P08 |
| **Phase** | 02-core-modules |
| **Dependency Level** | 3 (Depends on P05, P06) |
| **Estimated Time** | 7 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct the interfaces module for interface operations. This module handles interface discovery, configuration, and validation.

---

## Prerequisites

- P05: Network Base completed
- P06: Adapters completed
- network_base module functional
- adapters module functional

---

## Instructions

### Step 1: Create interfaces Module Structure

```bash
cd modules/interfaces
```

---

### Step 2: Create __init__.py

```python
"""
Interfaces Module

Interface operations and management.
"""

from .interfaces import (
    get_interface_status,
    get_interface_config,
    validate_interface,
    parse_interface_output
)

__all__ = [
    'get_interface_status',
    'get_interface_config',
    'validate_interface',
    'parse_interface_output'
]
```

---

### Step 3: Create interfaces.py

```python
"""
Interfaces Module

Interface operations and management.
"""

import re
from modules.adapters import get_adapter
from modules.network_base import build_json

def get_interface_status(conn, device, log_func):
    """
    Get interface status from device
    
    Args:
        conn: Netmiko connection object
        device: Device dictionary
        log_func: Logging function
    
    Returns:
        dict: Interface status result
    """
    try:
        # Get adapter for device type
        adapter = get_adapter(device['device_type'])
        
        # Get show command
        command = adapter.get_show_command('interfaces')
        
        # Execute command
        output = conn.send_command(command, read_timeout=30)
        
        # Parse output
        interfaces = parse_interface_output(output, device['device_type'])
        
        log_func(f"Retrieved interface status from {device['host']}")
        
        return build_json(device['host'], 'success', {'interfaces': interfaces}, None)
        
    except Exception as e:
        log_func(f"Error getting interface status from {device['host']}: {e}")
        return build_json(device['host'], 'error', None, f"Interface status error: {e}")

def get_interface_config(conn, device, interface_name, log_func):
    """
    Get interface configuration from device
    
    Args:
        conn: Netmiko connection object
        device: Device dictionary
        interface_name: Interface name
        log_func: Logging function
    
    Returns:
        dict: Interface configuration result
    """
    try:
        # Get adapter for device type
        adapter = get_adapter(device['device_type'])
        
        # Execute interface configuration command
        output = conn.send_command(f'show running-config interface {interface_name}', read_timeout=30)
        
        log_func(f"Retrieved interface config for {interface_name} from {device['host']}")
        
        return build_json(device['host'], 'success', {'interface': interface_name, 'config': output}, None)
        
    except Exception as e:
        log_func(f"Error getting interface config from {device['host']}: {e}")
        return build_json(device['host'], 'error', None, f"Interface config error: {e}")

def validate_interface(interface_name):
    """
    Validate interface name format
    
    Args:
        interface_name: Interface name string
    
    Returns:
        dict: Validation result
    """
    # Common interface patterns
    patterns = [
        r'^GigabitEthernet\d+/\d+(/\d+)?(/\d+)?$',
        r'^FastEthernet\d+/\d+(/\d+)?$',
        r'^TenGigabitEthernet\d+/\d+(/\d+)?(/\d+)?$',
        r'^Port-Channel\d+$',
        r'^Vlan\d+$',
        r'^ge-\d+/\d+/\d+$',
        r'^xe-\d+/\d+/\d+$',
        r'^et-\d+/\d+/\d+$'
    ]
    
    for pattern in patterns:
        if re.match(pattern, interface_name):
            return {'valid': True, 'interface': interface_name}
    
    return {'valid': False, 'interface': interface_name, 'error': 'Invalid interface format'}

def parse_interface_output(output, device_type):
    """
    Parse interface output based on device type
    
    Args:
        output: Command output string
        device_type: Device type string
    
    Returns:
        list: List of interface dictionaries
    """
    interfaces = []
    
    if device_type == 'cisco_ios':
        # Parse Cisco IOS output
        lines = output.split('\n')
        for line in lines:
            if 'GigabitEthernet' in line or 'FastEthernet' in line or 'Port-channel' in line:
                parts = line.split()
                if len(parts) >= 3:
                    interface = {
                        'name': parts[0],
                        'status': parts[1],
                        'vlan': parts[2] if len(parts) > 2 else 'N/A'
                    }
                    interfaces.append(interface)
    
    elif device_type == 'cisco_nxos':
        # Parse Cisco NX-OS JSON output
        import json
        try:
            data = json.loads(output)
            # Parse JSON structure
            # Implementation depends on actual JSON structure
        except:
            pass
    
    elif device_type == 'juniper_junos':
        # Parse Juniper JunOS XML output
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(output)
            # Parse XML structure
            # Implementation depends on actual XML structure
        except:
            pass
    
    return interfaces
```

---

### Step 4: Validate Module

```python
# Test module import
from modules.interfaces import get_interface_status, validate_interface, parse_interface_output

# Test interface validation
result = validate_interface('GigabitEthernet0/1')
assert result['valid'] == True

result = validate_interface('invalid-interface')
assert result['valid'] == False

# Test interface parsing
output = "GigabitEthernet0/1 connected trunk 10"
interfaces = parse_interface_output(output, 'cisco_ios')
assert len(interfaces) == 1
assert interfaces[0]['name'] == 'GigabitEthernet0/1'

print("Module validation successful")
```

---

## Validation Checklist

- [ ] interfaces module structure created
- [ ] __init__.py created
- [ ] interfaces.py created
- [ ] get_interface_status implemented
- [ ] get_interface_config implemented
- [ ] validate_interface implemented
- [ ] parse_interface_output implemented
- [ ] Module validation successful
- [ ] Core modules phase complete
- [ ] Ready for plugin system reconstruction

---

## Troubleshooting

### Issue: Interface parsing fails

**Solution:**
- Check device type
- Verify output format
- Update parsing logic for device type

### Issue: Interface validation fails

**Solution:**
- Check interface name format
- Update validation patterns
- Test with various interface types

---

## Next Steps

After completing this prompt, Phase 2 (Core Modules) is complete. Proceed to Phase 3: Plugin System

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- MODULE_ARCHITECTURE.md: ../../01-architecture/MODULE_ARCHITECTURE.md
- PLATFORM_SPECIFIC_OPTIMIZATIONS.md: ../../02-codebase/PLATFORM_SPECIFIC_OPTIMIZATIONS.md
