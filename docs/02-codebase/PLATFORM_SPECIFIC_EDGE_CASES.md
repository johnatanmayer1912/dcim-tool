# Platform-Specific Edge Cases Documentation

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | active |
| **Owner** | System Architect (R-ARCH) + Lead Developer (R-ENG) |
| **Last Updated** | 2026-06-02 |
| **Application Version** | 7.0.10 |

---

## Overview

This document provides comprehensive platform-specific edge cases for Network Swiss Tool Pro, including Cisco IOS, Cisco NX-OS, and Juniper JunOS platforms. These edge cases cover platform-specific behaviors, version differences, and handling strategies.

---

## Cisco IOS Edge Cases

### 1. IOS Version Compatibility

**Edge Case:** Different IOS versions have different command outputs

**Scenarios:**
- IOS 12.x vs 15.x command syntax differences
- Feature availability varies by version
- Output format changes between versions
- Deprecated commands in newer versions

**Handling Strategy:**
```python
def get_ios_command(device_type, ios_version, operation):
    commands = {
        'interface_status': {
            '12.x': 'show interface status',
            '15.x': 'show interface brief',
            'default': 'show interface'
        }
    }
    
    version_key = ios_version.split('.')[0] + '.x'
    operation_commands = commands.get(operation, {})
    
    if version_key in operation_commands:
        return operation_commands[version_key]
    
    return operation_commands.get('default', '')
```

**Detection:**
```python
def detect_ios_version(conn):
    output = conn.send_command('show version')
    version_match = re.search(r'Version (\d+\.\d+)', output)
    if version_match:
        return version_match.group(1)
    return '15.x'  # Default to latest
```

---

### 2. Privilege Level Variations

**Edge Case:** Different privilege levels have different command access

**Scenarios:**
- Level 1: Limited commands
- Level 15: Full access
- Custom privilege levels
- Role-based access control (RBAC)

**Handling Strategy:**
```python
def check_privilege_level(conn):
    output = conn.send_command('show privilege')
    privilege_match = re.search(r'Current privilege level is (\d+)', output)
    if privilege_match:
        return int(privilege_match.group(1))
    return 1  # Default to level 1

def escalate_privilege(conn, credentials):
    current_level = check_privilege_level(conn)
    if current_level < 15:
        try:
            conn.enable()
            return True
        except Exception as e:
            return False
    return True
```

---

### 3. Interface Naming Conventions

**Edge Case:** Different interface naming conventions across IOS versions

**Scenarios:**
- GigabitEthernet0/1 vs GigabitEthernet0/0/1
- FastEthernet vs GigabitEthernet
- Subinterface naming (GigabitEthernet0/1.100)
- Port-channel naming (Port-Channel1 vs Port-channel1)

**Handling Strategy:**
```python
def normalize_interface_name(interface_name):
    # Normalize interface name to standard format
    normalized = interface_name.lower()
    normalized = normalized.replace('gigabitethernet', 'GigabitEthernet')
    normalized = normalized.replace('fastethernet', 'FastEthernet')
    normalized = normalized.replace('port-channel', 'Port-Channel')
    return normalized

def parse_interface_name(interface_name):
    # Parse interface name into components
    pattern = r'(\w+)(\d+)(?:/(\d+))?(?:/(\d+))?(?:\.(\d+))?'
    match = re.match(pattern, interface_name)
    if match:
        return {
            'type': match.group(1),
            'slot': match.group(2),
            'subslot': match.group(3),
            'port': match.group(4),
            'subinterface': match.group(5)
        }
    return None
```

---

### 4. VLAN Database Differences

**Edge Case:** VLAN database format varies by IOS version

**Scenarios:**
- VLAN database mode vs VTP mode
- VLAN ID range differences
- VLAN name length limits
- Private VLAN support

**Handling Strategy:**
```python
def get_vlan_command(ios_version):
    if ios_version.startswith('12.'):
        return 'show vlan brief'
    else:
        return 'show vlan'

def parse_vlan_output(output, ios_version):
    if ios_version.startswith('12.'):
        return parse_vlan_legacy(output)
    else:
        return parse_vlan_modern(output)
```

---

### 5. Configuration Mode Differences

**Edge Case:** Configuration mode behavior varies

**Scenarios:**
- Global configuration vs interface configuration
- Sub-mode navigation
- Configuration confirmation prompts
- Configuration rollback behavior

**Handling Strategy:**
```python
def configure_interface(conn, interface, config_commands):
    conn.config_mode()
    conn.send_command(f'interface {interface}')
    
    for cmd in config_commands:
        try:
            output = conn.send_command(cmd, expect_string=r'#')
            if 'Invalid' in output or 'Incomplete' in output:
                log_func(f"Command failed: {cmd}")
        except Exception as e:
            log_func(f"Command error: {e}")
    
    conn.send_command('exit')
    conn.send_command('exit')
```

---

## Cisco NX-OS Edge Cases

### 1. NX-API Availability

**Edge Case:** NX-API may not be enabled or available

**Scenarios:**
- NX-API not licensed
- NX-API not configured
- NX-API version incompatibility
- NX-API port conflicts

**Handling Strategy:**
```python
def check_nxapi_availability(device):
    try:
        response = requests.get(
            f"http://{device['host']}:8080/api/mo/sys.json",
            auth=(device['username'], device['password']),
            timeout=5
        )
        return response.status_code == 200
    except:
        return False

def get_nxapi_data(device, query):
    if check_nxapi_availability(device):
        try:
            response = requests.get(
                f"http://{device['host']}:8080/api/mo/{query}.json",
                auth=(device['username'], device['password'])
            )
            return response.json()
        except Exception as e:
            log_func(f"NX-API error: {e}")
    
    # Fallback to CLI
    return get_cli_data(device, query)
```

---

### 2. VPC Domain Complexity

**Edge Case:** vPC domain configuration has complex consistency checks

**Scenarios:**
- vPC role conflict
- Type-1 inconsistency
- Type-2 inconsistency
- vPC peer-link failure

**Handling Strategy:**
```python
def validate_vpc_consistency(vpc_data):
    inconsistencies = []
    
    # Check type-1 consistency
    type1_params = ['spanning-tree mode', 'vlan', 'port-channel']
    for param in type1_params:
        if not check_type1_consistency(vpc_data, param):
            inconsistencies.append(f"Type-1 inconsistency: {param}")
    
    # Check type-2 consistency
    type2_params = ['qos', 'pfc', 'mtu']
    for param in type2_params:
        if not check_type2_consistency(vpc_data, param):
            inconsistencies.append(f"Type-2 inconsistency: {param}")
    
    return inconsistencies
```

---

### 3. Interface Speed and Duplex

**Edge Case:** Interface speed/duplex auto-negotiation issues

**Scenarios:**
- Speed mismatch
- Duplex mismatch
- Auto-negotiation failure
- Forced speed/duplex settings

**Handling Strategy:**
```python
def check_interface_speed_duplex(conn, interface):
    output = conn.send_command(f'show interface {interface} | json')
    data = json.loads(output)
    
    speed = data['TABLE_interface']['ROW_interface']['speed']
    duplex = data['TABLE_interface']['ROW_interface']['duplex']
    
    if speed == 'auto' and duplex == 'auto':
        return {'status': 'auto', 'message': 'Auto-negotiation enabled'}
    elif speed == 'auto' or duplex == 'auto':
        return {'status': 'warning', 'message': 'Mixed auto/manual settings'}
    else:
        return {'status': 'manual', 'speed': speed, 'duplex': duplex}
```

---

### 4. ACL Configuration Complexity

**Edge Case:** ACL configuration has complex syntax and limitations

**Scenarios:**
- ACL sequence numbers
- Object group usage
- ACL logging
- ACL hit counters

**Handling Strategy:**
```python
def configure_acl_nxos(conn, acl_name, acl_rules):
    conn.config_mode()
    
    # Check if ACL exists
    try:
        output = conn.send_command(f'show access-lists {acl_name}')
        if acl_name in output:
            conn.send_command(f'no access-list {acl_name}')
    except:
        pass
    
    # Configure ACL
    for rule in acl_rules:
        sequence = rule.get('sequence', '')
        action = rule['action']
        protocol = rule['protocol']
        source = rule['source']
        destination = rule['destination']
        
        cmd = f'access-list {acl_name} {sequence} {action} {protocol} {source} {destination}'
        conn.send_command(cmd)
    
    conn.send_command('exit')
```

---

### 5. Feature Licensing

**Edge Case:** Features may require licenses

**Scenarios:**
- Feature not licensed
- License expired
- License not installed
- License conflicts

**Handling Strategy:**
```python
def check_feature_license(conn, feature):
    output = conn.send_command('show license usage')
    
    if feature in output:
        return {'status': 'licensed', 'feature': feature}
    else:
        output = conn.send_command('show feature')
        if feature in output and 'enabled' in output:
            return {'status': 'enabled', 'feature': feature}
        else:
            return {'status': 'not_licensed', 'feature': feature}

def enable_feature_with_license(conn, feature):
    license_status = check_feature_license(conn, feature)
    
    if license_status['status'] == 'not_licensed':
        log_func(f"Feature {feature} requires license")
        return False
    
    try:
        conn.config_mode()
        conn.send_command(f'feature {feature}')
        conn.send_command('exit')
        return True
    except Exception as e:
        log_func(f"Failed to enable feature: {e}")
        return False
```

---

## Juniper JunOS Edge Cases

### 1. Configuration Hierarchy

**Edge Case:** JunOS uses hierarchical configuration structure

**Scenarios:**
- Configuration mode navigation
- Configuration commit behavior
- Configuration rollback
- Configuration validation

**Handling Strategy:**
```python
def configure_junos_hierarchical(conn, config_hierarchy):
    conn.send_command('configure')
    
    def navigate_and_set(hierarchy, value=None):
        for level in hierarchy[:-1]:
            conn.send_command(f'set {level}')
        
        if value:
            conn.send_command(f'set {hierarchy[-1]} {value}')
        else:
            conn.send_command(f'set {hierarchy[-1]}')
    
    for config_item in config_hierarchy:
        navigate_and_set(config_item['path'], config_item.get('value'))
    
    conn.send_command('commit')
    conn.send_command('exit')
```

---

### 2. Junos XML Output

**Edge Case:** JunOS XML output format variations

**Scenarios:**
- XML schema differences
- XML namespace handling
- XML parsing errors
- XML vs JSON output

**Handling Strategy:**
```python
def get_junos_xml_output(conn, command):
    xml_command = f'{command} | display xml'
    output = conn.send_command(xml_command)
    
    try:
        # Parse XML
        root = ET.fromstring(output)
        return root
    except ET.ParseError as e:
        log_func(f"XML parse error: {e}")
        # Fallback to text parsing
        return parse_text_output(output)
```

---

### 3. Routing Instance Support

**Edge Case:** Multiple routing instances (VRFs)

**Scenarios:**
- Default routing instance
- Custom routing instances
- VRF configuration
- Route leaking between instances

**Handling Strategy:**
```python
def get_routing_instances(conn):
    output = conn.send_command('show configuration routing-instances | display xml')
    root = ET.fromstring(output)
    
    instances = []
    for instance in root.findall('.//routing-instance'):
        instance_name = instance.find('name').text
        instances.append(instance_name)
    
    return instances

def execute_in_routing_instance(conn, command, routing_instance):
    if routing_instance:
        command = f'run routing-instance {routing_instance} {command}'
    return conn.send_command(command)
```

---

### 4. Commit Confirmation

**Edge Case:** JunOS commit confirmation behavior

**Scenarios:**
- Commit confirmed timeout
- Commit rollback on timeout
- Commit check validation
- Commit synchronization

**Handling Strategy:**
```python
def commit_junos_safe(conn, config_commands, confirm_timeout=5):
    conn.send_command('configure')
    
    for cmd in config_commands:
        conn.send_command(cmd)
    
    # Commit with confirmation
    conn.send_command(f'commit confirmed {confirm_timeout}')
    
    # Verify configuration
    if verify_junos_config(conn):
        conn.send_command('commit')
        conn.send_command('exit')
        return True
    else:
        conn.send_command('rollback')
        conn.send_command('exit')
        return False
```

---

### 5. Interface Naming

**Edge Case:** JunOS interface naming conventions

**Scenarios:**
- ge-0/0/0 vs xe-0/0/0
- et- interfaces (40GbE)
- irb interfaces (IRB)
- st0 interfaces (secure tunnel)

**Handling Strategy:**
```python
def normalize_junos_interface(interface_name):
    # Normalize interface name
    normalized = interface_name.lower()
    
    # Handle interface type variations
    if normalized.startswith('ge-'):
        normalized = normalized.replace('ge-', 'ge-')
    elif normalized.startswith('xe-'):
        normalized = normalized.replace('xe-', 'xe-')
    elif normalized.startswith('et-'):
        normalized = normalized.replace('et-', 'et-')
    
    return normalized

def parse_junos_interface(interface_name):
    # Parse JunOS interface name
    pattern = r'(\w+)-(\d+)/(\d+)/(\d+)'
    match = re.match(pattern, interface_name)
    if match:
        return {
            'type': match.group(1),
            'fpc': match.group(2),
            'pic': match.group(3),
            'port': match.group(4)
        }
    return None
```

---

## Cross-Platform Edge Cases

### 1. SSH Key Authentication

**Edge Case:** SSH key authentication varies by platform

**Scenarios:**
- Key type support (RSA, DSA, ECDSA, ED25519)
- Key format differences
- Key exchange algorithms
- Authentication order

**Handling Strategy:**
```python
def configure_ssh_auth(device_type, credentials):
    ssh_config = {
        'cisco_ios': {
            'key_file': credentials.get('ssh_key_file'),
            'allow_agent': True,
            'ssh_strict': False
        },
        'cisco_nxos': {
            'key_file': credentials.get('ssh_key_file'),
            'allow_agent': True,
            'ssh_strict': False
        },
        'juniper_junos': {
            'key_file': credentials.get('ssh_key_file'),
            'allow_agent': True,
            'ssh_strict': False
        }
    }
    
    return ssh_config.get(device_type, {})
```

---

### 2. Timeout Handling

**Edge Case:** Timeout behavior varies by platform and operation

**Scenarios:**
- Connection timeout
- Command execution timeout
- Configuration timeout
- Bulk operation timeout

**Handling Strategy:**
```python
def get_platform_timeout(device_type, operation):
    timeouts = {
        'cisco_ios': {
            'connection': 30,
            'command': 30,
            'configuration': 60,
            'bulk': 300
        },
        'cisco_nxos': {
            'connection': 30,
            'command': 30,
            'configuration': 60,
            'bulk': 300
        },
        'juniper_junos': {
            'connection': 30,
            'command': 30,
            'configuration': 120,
            'bulk': 600
        }
    }
    
    return timeouts.get(device_type, {}).get(operation, 30)
```

---

### 3. Output Pagination

**Edge Case:** Output pagination varies by platform

**Scenarios:**
- Cisco IOS: terminal length
- Cisco NX-OS: terminal length
- Juniper JunOS: set cli screen-length

**Handling Strategy:**
```python
def disable_pagination(conn, device_type):
    if device_type == 'cisco_ios':
        conn.send_command('terminal length 0')
        conn.send_command('terminal width 512')
    elif device_type == 'cisco_nxos':
        conn.send_command('terminal length 0')
        conn.send_command('terminal width 512')
    elif device_type == 'juniper_junos':
        conn.send_command('set cli screen-length 0')
        conn.send_command('set cli screen-width 512')
```

---

### 4. Error Message Format

**Edge Case:** Error message format varies by platform

**Scenarios:**
- Cisco IOS: %Error message
- Cisco NX-OS: ERROR: message
- Juniper JunOS: error: message

**Handling Strategy:**
```python
def parse_platform_error(device_type, error_message):
    error_patterns = {
        'cisco_ios': r'%\s*(.+)',
        'cisco_nxos': r'ERROR:\s*(.+)',
        'juniper_junos': r'error:\s*(.+)'
    }
    
    pattern = error_patterns.get(device_type, r'(.+)')
    match = re.search(pattern, error_message)
    
    if match:
        return match.group(1)
    
    return error_message
```

---

### 5. Configuration Backup Format

**Edge Case:** Configuration backup format varies by platform

**Scenarios:**
- Cisco IOS: show running-config
- Cisco NX-OS: show running-config
- Juniper JunOS: show configuration | display set

**Handling Strategy:**
```python
def get_config_backup_command(device_type):
    commands = {
        'cisco_ios': 'show running-config',
        'cisco_nxos': 'show running-config',
        'juniper_junos': 'show configuration | display set'
    }
    
    return commands.get(device_type, 'show running-config')

def normalize_config_backup(config, device_type):
    if device_type == 'juniper_junos':
        # Convert set commands to standard format
        return convert_set_to_standard(config)
    else:
        return config
```

---

## Version-Specific Edge Cases

### Cisco IOS 12.x

**Edge Cases:**
- Limited JSON support
- Different command syntax
- Feature limitations
- Output format differences

**Handling:**
```python
def handle_ios_12x(conn, operation):
    # Use legacy commands
    if operation == 'interface_status':
        return conn.send_command('show interface status')
    elif operation == 'vlan':
        return conn.send_command('show vlan brief')
    else:
        return conn.send_command(operation)
```

---

### Cisco IOS 15.x

**Edge Cases:**
- Enhanced JSON support
- New command syntax
- Additional features
- Improved output format

**Handling:**
```python
def handle_ios_15x(conn, operation):
    # Use modern commands
    if operation == 'interface_status':
        return conn.send_command('show interface brief')
    elif operation == 'vlan':
        return conn.send_command('show vlan')
    else:
        return conn.send_command(operation)
```

---

### Cisco NX-OS 7.x

**Edge Cases:**
- NX-API improvements
- Enhanced JSON support
- New features
- Improved performance

**Handling:**
```python
def handle_nxos_7x(conn, operation):
    # Use NX-API when available
    if check_nxapi_available(conn):
        return get_nxapi_data(conn, operation)
    else:
        return conn.send_command(operation)
```

---

### Juniper JunOS 18.x

**Edge Cases:**
- Enhanced XML support
- New configuration features
- Improved performance
- New CLI features

**Handling:**
```python
def handle_junos_18x(conn, operation):
    # Use XML output
    xml_command = f'{operation} | display xml'
    return conn.send_command(xml_command)
```

---

## Error Recovery

### Platform-Specific Error Recovery

**Cisco IOS:**
```python
def recover_ios_error(conn, error):
    if 'Invalid input' in error:
        # Try alternative command
        return try_alternative_command(conn)
    elif 'Incomplete command' in error:
        # Complete command
        return complete_command(conn)
    else:
        # Generic recovery
        return generic_recovery(conn)
```

**Cisco NX-OS:**
```python
def recover_nxos_error(conn, error):
    if 'Invalid command' in error:
        # Try NX-API
        return try_nxapi(conn)
    elif 'Syntax error' in error:
        # Fix syntax
        return fix_syntax(conn)
    else:
        # Generic recovery
        return generic_recovery(conn)
```

**Juniper JunOS:**
```python
def recover_junos_error(conn, error):
    if 'syntax error' in error:
        # Fix syntax
        return fix_syntax(conn)
    elif 'permission denied' in error:
        # Escalate privilege
        return escalate_privilege(conn)
    else:
        # Generic recovery
        return generic_recovery(conn)
```

---

## References

- PLATFORM_SPECIFIC_OPTIMIZATIONS.md - Platform-specific optimizations
- ADVANCED_DEBUGGING_GUIDE.md - Debugging procedures
- ERROR_HANDLING_DOCUMENTATION.md - Error handling and recovery
- MODULE_ARCHITECTURE.md - Module architecture and adapters
