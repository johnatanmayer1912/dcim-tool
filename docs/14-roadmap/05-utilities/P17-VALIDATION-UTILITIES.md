# P17: Validation Utilities

| Field | Value |
|-------|-------|
| **Prompt ID** | P17 |
| **Phase** | 05-utilities |
| **Dependency Level** | 1 (Depends on Phase 1) |
| **Estimated Time** | 10 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct validation utilities for data validation. This module provides functions for validating IP addresses, MAC addresses, VLANs, and other network data.

---

## Prerequisites

- Phase 1 (Foundation) completed
- Python environment set up
- ipaddress module available

---

## Instructions

### Step 1: Create validation_utilities Module

```bash
cd modules
```

---

### Step 2: Create validation_utilities.py

```python
"""
Validation Utilities

Data validation functions for network data.
"""

import re
import ipaddress

def validate_ip_address(ip):
    """
    Validate IP address format
    
    Args:
        ip: IP address string
    
    Returns:
        dict: Validation result with valid boolean and message
    """
    try:
        ipaddress.ip_address(ip)
        return {'valid': True, 'ip': ip, 'message': 'Valid IP address'}
    except ValueError:
        return {'valid': False, 'ip': ip, 'message': 'Invalid IP address format'}

def validate_ip_range(start_ip, end_ip):
    """
    Validate IP address range
    
    Args:
        start_ip: Start IP address
        end_ip: End IP address
    
    Returns:
        dict: Validation result
    """
    try:
        start = ipaddress.ip_address(start_ip)
        end = ipaddress.ip_address(end_ip)
        
        if start > end:
            return {'valid': False, 'message': 'Start IP must be less than end IP'}
        
        return {'valid': True, 'start': str(start), 'end': str(end), 'message': 'Valid IP range'}
        
    except ValueError as e:
        return {'valid': False, 'message': f'Invalid IP range: {e}'}

def validate_mac_address(mac):
    """
    Validate MAC address format
    
    Args:
        mac: MAC address string
    
    Returns:
        dict: Validation result
    """
    # MAC address patterns
    patterns = [
        r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',  # XX:XX:XX:XX:XX:XX
        r'^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})$',      # XXXX.XXXX.XXXX
    ]
    
    for pattern in patterns:
        if re.match(pattern, mac):
            return {'valid': True, 'mac': mac, 'message': 'Valid MAC address'}
    
    return {'valid': False, 'mac': mac, 'message': 'Invalid MAC address format'}

def validate_vlan_id(vlan_id):
    """
    Validate VLAN ID
    
    Args:
        vlan_id: VLAN ID (string or integer)
    
    Returns:
        dict: Validation result
    """
    try:
        vlan = int(vlan_id)
        
        if vlan < 1 or vlan > 4094:
            return {'valid': False, 'vlan_id': vlan, 'message': 'VLAN ID must be between 1 and 4094'}
        
        return {'valid': True, 'vlan_id': vlan, 'message': 'Valid VLAN ID'}
        
    except ValueError:
        return {'valid': False, 'vlan_id': vlan_id, 'message': 'VLAN ID must be an integer'}

def validate_hostname(hostname):
    """
    Validate hostname format
    
    Args:
        hostname: Hostname string
    
    Returns:
        dict: Validation result
    """
    # Hostname pattern (RFC 1123)
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$'
    
    if re.match(pattern, hostname):
        if len(hostname) <= 63:
            return {'valid': True, 'hostname': hostname, 'message': 'Valid hostname'}
    
    return {'valid': False, 'hostname': hostname, 'message': 'Invalid hostname format'}

def validate_subnet_mask(mask):
    """
    Validate subnet mask
    
    Args:
        mask: Subnet mask (CIDR or dotted decimal)
    
    Returns:
        dict: Validation result
    """
    try:
        # Try CIDR notation
        if '/' in mask:
            ip, prefix = mask.split('/')
            prefix = int(prefix)
            
            if prefix < 0 or prefix > 32:
                return {'valid': False, 'message': 'Prefix must be between 0 and 32'}
            
            return {'valid': True, 'mask': mask, 'message': 'Valid CIDR notation'}
        
        # Try dotted decimal
        ipaddress.IPv4Network(f'0.0.0.0/{mask}')
        return {'valid': True, 'mask': mask, 'message': 'Valid subnet mask'}
        
    except ValueError:
        return {'valid': False, 'mask': mask, 'message': 'Invalid subnet mask format'}

def validate_port_number(port):
    """
    Validate port number
    
    Args:
        port: Port number (string or integer)
    
    Returns:
        dict: Validation result
    """
    try:
        port_num = int(port)
        
        if port_num < 1 or port_num > 65535:
            return {'valid': False, 'port': port_num, 'message': 'Port must be between 1 and 65535'}
        
        return {'valid': True, 'port': port_num, 'message': 'Valid port number'}
        
    except ValueError:
        return {'valid': False, 'port': port, 'message': 'Port must be an integer'}

def validate_device_type(device_type):
    """
    Validate device type
    
    Args:
        device_type: Device type string
    
    Returns:
        dict: Validation result
    """
    valid_types = ['cisco_ios', 'cisco_nxos', 'juniper_junos']
    
    if device_type in valid_types:
        return {'valid': True, 'device_type': device_type, 'message': 'Valid device type'}
    
    return {'valid': False, 'device_type': device_type, 'message': f'Invalid device type. Valid types: {valid_types}'}
```

---

### Step 3: Validate Validation Utilities

```python
# Test validation utilities
from modules.validation_utilities import (
    validate_ip_address,
    validate_mac_address,
    validate_vlan_id,
    validate_hostname
)

# Test IP validation
result = validate_ip_address('10.1.1.1')
assert result['valid'] == True

result = validate_ip_address('invalid')
assert result['valid'] == False

# Test MAC validation
result = validate_mac_address('00:11:22:33:44:55')
assert result['valid'] == True

# Test VLAN validation
result = validate_vlan_id('100')
assert result['valid'] == True

result = validate_vlan_id('5000')
assert result['valid'] == False

# Test hostname validation
result = validate_hostname('router1')
assert result['valid'] == True

print("Validation utilities validation successful")
```

---

## Validation Checklist

- [ ] validation_utilities.py created
- [ ] validate_ip_address implemented
- [ ] validate_ip_range implemented
- [ ] validate_mac_address implemented
- [ ] validate_vlan_id implemented
- [ ] validate_hostname implemented
- [ ] validate_subnet_mask implemented
- [ ] validate_port_number implemented
- [ ] validate_device_type implemented
- [ ] Validation utilities validation successful
- [ ] Ready for logging utilities reconstruction

---

## Troubleshooting

### Issue: IP validation fails

**Solution:**
- Check ipaddress module availability
- Verify IP format
- Test with valid IP addresses

### Issue: MAC validation fails

**Solution:**
- Check MAC format patterns
- Verify separator characters
- Test with valid MAC addresses

---

## Next Steps

After completing this prompt, proceed to P18: Logging Utilities

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- UTILITIES_DOCUMENTATION.md: ../../02-codebase/UTILITIES_DOCUMENTATION.md
