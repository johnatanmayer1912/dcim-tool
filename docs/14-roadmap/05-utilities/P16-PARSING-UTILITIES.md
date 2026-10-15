# P16: Parsing Utilities

| Field | Value |
|-------|-------|
| **Prompt ID** | P16 |
| **Phase** | 05-utilities |
| **Dependency Level** | 1 (Depends on Phase 1) |
| **Estimated Time** | 10 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-10 |
| **Application Version** | 7.0.29 |

---

## Purpose

Reconstruct parsing utilities for CLI output parsing. This module provides functions for parsing CLI output from network devices using TextFSM and custom parsers.

---

## Prerequisites

- Phase 1 (Foundation) completed
- textfsm installed
- Python environment set up

---

## Instructions

### Step 1: Create parsing_utilities Module

```bash
cd modules
```

---

### Step 2: Create parsing_utilities.py

```python
"""
Parsing Utilities

CLI output parsing functions using TextFSM and custom parsers.
"""

import re
from textfsm import TextFSM

def parse_with_textfsm(output, template):
    """
    Parse CLI output using TextFSM template
    
    Args:
        output: CLI output string
        template: TextFSM template string
    
    Returns:
        list: Parsed data as list of dictionaries
    """
    try:
        fsm = TextFSM(template)
        fsm.Reset()
        result = fsm.ParseText(output)
        
        # Convert to list of dictionaries
        parsed_data = []
        for entry in result:
            data_point = {}
            for i, header in enumerate(fsm.header):
                data_point[header] = entry[i]
            parsed_data.append(data_point)
        
        return parsed_data
        
    except Exception as e:
        print(f"TextFSM parsing error: {e}")
        return []

def parse_cisco_ios_show_version(output):
    """
    Parse Cisco IOS 'show version' output
    
    Args:
        output: CLI output string
    
    Returns:
        dict: Parsed version information
    """
    version_info = {}
    
    # Parse version
    version_match = re.search(r'Version (\d+\.\d+\.\d+)', output)
    if version_match:
        version_info['version'] = version_match.group(1)
    
    # Parse hostname
    hostname_match = re.search(r'(\S+) uptime', output)
    if hostname_match:
        version_info['hostname'] = hostname_match.group(1)
    
    # Parse serial number
    serial_match = re.search(r'System serial number:\s*(\S+)', output)
    if serial_match:
        version_info['serial'] = serial_match.group(1)
    
    return version_info

def parse_cisco_nxos_show_interface(output):
    """
    Parse Cisco NX-OS 'show interface' JSON output
    
    Args:
        output: CLI output string (JSON)
    
    Returns:
        list: Parsed interface information
    """
    import json
    
    try:
        data = json.loads(output)
        interfaces = []
        
        if 'TABLE_interface' in data:
            for entry in data['TABLE_interface']['ROW_interface']:
                interface = {
                    'interface': entry.get('interface'),
                    'state': entry.get('state'),
                    'speed': entry.get('speed'),
                    'mtu': entry.get('mtu')
                }
                interfaces.append(interface)
        
        return interfaces
        
    except Exception as e:
        print(f"JSON parsing error: {e}")
        return []

def parse_junos_show_interface(output):
    """
    Parse Juniper JunOS 'show interface' XML output
    
    Args:
        output: CLI output string (XML)
    
    Returns:
        list: Parsed interface information
    """
    import xml.etree.ElementTree as ET
    
    try:
        root = ET.fromstring(output)
        interfaces = []
        
        for interface in root.findall('.//interface'):
            interface_info = {
                'name': interface.find('name').text,
                'status': interface.find('oper-status').text
            }
            interfaces.append(interface_info)
        
        return interfaces
        
    except Exception as e:
        print(f"XML parsing error: {e}")
        return []

def parse_vlan_output(output, device_type):
    """
    Parse VLAN output based on device type
    
    Args:
        output: CLI output string
        device_type: Device type string
    
    Returns:
        list: Parsed VLAN information
    """
    vlans = []
    
    if device_type == 'cisco_ios':
        lines = output.split('\n')
        for line in lines:
            if re.match(r'^\d+\s+', line):
                parts = line.split()
                if len(parts) >= 3:
                    vlan = {
                        'vlan_id': parts[0],
                        'name': parts[1],
                        'status': parts[2]
                    }
                    vlans.append(vlan)
    
    elif device_type == 'cisco_nxos':
        import json
        try:
            data = json.loads(output)
            if 'TABLE_vlanbrief' in data:
                for entry in data['TABLE_vlanbrief']['ROW_vlanbrief']:
                    vlan = {
                        'vlan_id': entry.get('vlanshowbr-vlanid'),
                        'name': entry.get('vlanshowbr-vlanname'),
                        'status': entry.get('vlanshowbr-vlanstate')
                    }
                    vlans.append(vlan)
        except:
            pass
    
    return vlans
```

---

### Step 3: Create TextFSM Templates Directory

```bash
mkdir -p templates/textfsm
```

---

### Step 4: Create TextFSM Template for Cisco IOS Show Interface

```bash
cat > templates/textfsm/cisco_ios_show_interface.template << 'EOF'
Value INTERFACE (\S+)
Value STATUS (\S+)
Value VLAN (\d+)
Value DUPLEX (\S+)
Value SPEED (\S+)

Start
  ^${INTERFACE}\s+${STATUS}\s+${VLAN}\s+${DUPLEX}\s+${SPEED} -> Record
EOF
```

---

### Step 5: Validate Parsing Utilities

```python
# Test parsing utilities
from modules.parsing_utilities import (
    parse_with_textfsm,
    parse_cisco_ios_show_version,
    parse_vlan_output
)

# Test TextFSM parsing
template = """
Value INTERFACE (\S+)
Value STATUS (\S+)

Start
  ^${INTERFACE}\s+${STATUS} -> Record
"""
output = "GigabitEthernet0/1 connected"
result = parse_with_textfsm(output, template)
assert len(result) == 1

# Test Cisco IOS version parsing
version_output = "Cisco IOS Software, Version 15.2(4)E5"
result = parse_cisco_ios_show_version(version_output)
assert 'version' in result

# Test VLAN parsing
vlan_output = "1  default  active"
result = parse_vlan_output(vlan_output, 'cisco_ios')
assert len(result) == 1

print("Parsing utilities validation successful")
```

---

## Validation Checklist

- [ ] parsing_utilities.py created
- [ ] parse_with_textfsm implemented
- [ ] parse_cisco_ios_show_version implemented
- [ ] parse_cisco_nxos_show_interface implemented
- [ ] parse_junos_show_interface implemented
- [ ] parse_vlan_output implemented
- [ ] TextFSM templates directory created
- [ ] TextFSM template created
- [ ] Parsing utilities validation successful
- [ ] Ready for validation utilities reconstruction

---

## Troubleshooting

### Issue: TextFSM parsing fails

**Solution:**
- Verify template syntax
- Check output format
- Test template manually

### Issue: JSON parsing fails

**Solution:**
- Verify JSON format
- Check for JSON errors
- Validate output structure

---

## v7.0.28+ required utilities (MAC + Juniper)

Create these modules per `UTILITIES_DOCUMENTATION.md`:

### `utils/mac_utils.py`
- `normalize_mac_hex`, `to_cisco_dotted`, `to_junos_colon`
- `cisco_search_terms`, `junos_search_terms` for CLI `include` / `match`
- `extract_junos_interface` for Junos MAC table rows

### `utils/juniper_iface.py`
- `split_junos_unit`, `resolve_junos_iface_key`
- `collect_juniper_lag_detail` (LACP/AE from device)
- `enrich_interfaces_with_lag` for interface map ae bundles

**Used by:** `modules/mac_trace.py`, `modules/plugins/interface_manager.py`, `node_interface_topology.py`

**Validation:**
```python
from utils.mac_utils import cisco_search_terms
assert cisco_search_terms('00:11:22:33:44:55')[0] == '0011.2233.4455'
from utils.juniper_iface import split_junos_unit
assert split_junos_unit('ge-0/0/0.0')[0] == 'ge-0/0/0'
```

---

## Next Steps

After completing this prompt, proceed to P17: Validation Utilities

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- UTILITIES_DOCUMENTATION.md: ../../02-codebase/UTILITIES_DOCUMENTATION.md
- PLATFORM_SPECIFIC_OPTIMIZATIONS.md: ../../02-codebase/PLATFORM_SPECIFIC_OPTIMIZATIONS.md
