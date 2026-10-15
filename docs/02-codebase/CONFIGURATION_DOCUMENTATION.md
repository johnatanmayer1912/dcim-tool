# Configuration Documentation

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | active |
| **Owner** | Documentation Steward (R-LIB) + Lead Developer (R-ENG) |
| **Last Updated** | 2026-06-02 |
| **Application Version** | 7.0.10 |

---

## Overview

This document provides comprehensive configuration documentation for Network Swiss Tool Pro, including all configuration parameters, default values, validation rules, and error messages.

---

## Configuration Files

### 1. inventory.txt

**Location:** `inventory.txt` (root directory)  
**Purpose:** Device inventory for network operations  
**Format:** INI-style with sections for device groups

#### File Structure

```ini
# Test Inventory for QA Validation
# Format: IP,device_type,group

[CoreSwitches]
10.1.1.1,cisco_ios,CoreSwitches
10.1.1.2,cisco_nxos,CoreSwitches

[AccessLayer]
10.2.1.1,juniper_junos,AccessLayer
10.2.1.2,cisco_ios,AccessLayer

[Distribution]
10.3.1.1,cisco_ios,Distribution
```

#### Configuration Parameters

| Parameter | Description | Format | Required | Default | Validation |
|-----------|-------------|--------|----------|---------|------------|
| Section Header | Device group name | `[GroupName]` | Yes | None | Must be unique, alphanumeric |
| IP Address | Device IP address | IPv4/IPv6 | Yes | None | Must be valid IP address |
| Device Type | Platform identifier | String | Yes | None | Must be supported platform |
| Group | Device group name | String | Yes | None | Must match section header |

#### Supported Device Types

- `cisco_ios` - Cisco IOS devices
- `cisco_nxos` - Cisco NX-OS devices
- `cisco_xe` - Cisco IOS XE devices
- `juniper_junos` - Juniper Junos devices

#### Validation Rules

1. **IP Address Validation:**
   - Must be valid IPv4 or IPv6 address
   - No duplicate IP addresses allowed
   - IP addresses must be reachable from application host

2. **Device Type Validation:**
   - Must be one of supported device types
   - Case-sensitive
   - Must match Netmiko device type mapping

3. **Group Validation:**
   - Group names must match section headers
   - No duplicate section headers allowed
   - Group names must be alphanumeric with underscores

4. **File Format Validation:**
   - Must use INI-style format
   - Comments start with `#`
   - Empty lines are ignored
   - Trailing whitespace is trimmed

#### Error Messages

| Error | Message | Resolution |
|-------|---------|------------|
| Invalid IP | `Invalid IP address: {ip}` | Verify IP address format |
| Duplicate IP | `Duplicate IP address: {ip}` | Remove duplicate entry |
| Invalid Device Type | `Unsupported device type: {type}` | Use supported device type |
| Duplicate Group | `Duplicate group: {group}` | Remove duplicate section |
| Missing Section | `Missing section header` | Add section header before devices |
| Invalid Format | `Invalid inventory format` | Check INI-style format |

#### Example Configurations

**Minimal Configuration:**
```ini
[CoreSwitches]
10.1.1.1,cisco_ios,CoreSwitches
```

**Full Configuration:**
```ini
# Production Inventory
# Updated: 2026-06-02

[CoreSwitches]
10.1.1.1,cisco_ios,CoreSwitches
10.1.1.2,cisco_nxos,CoreSwitches
10.1.1.3,cisco_xe,CoreSwitches

[AccessLayer]
10.2.1.1,juniper_junos,AccessLayer
10.2.1.2,cisco_ios,AccessLayer
10.2.1.3,cisco_ios,AccessLayer

[Distribution]
10.3.1.1,cisco_ios,Distribution
10.3.1.2,cisco_ios,Distribution

[Edge]
10.4.1.1,cisco_ios,Edge
10.4.1.2,cisco_ios,Edge
```

#### Configuration Precedence

1. Device-level parameters override group-level parameters
2. Later sections override earlier sections for duplicate group names
3. Comments are ignored during parsing

---

### 2. policies/standards.yaml

**Location:** `policies/standards.yaml`  
**Purpose:** Network configuration standards for validation  
**Format:** YAML with policy definitions

#### File Structure

```yaml
metadata:
  org: "Your Organization"
  version: "1.0.0"
  last_updated: "2026-04-28"
  author: "Network Team"
  description: "Organization-wide network configuration standards"

policies:
  - id: telnet_disabled
    category: Security
    description: "Telnet must be disabled on all VTY lines"
    severity: critical
    platforms: [cisco_ios, cisco_nxos, cisco_xe]
    check_command: "show line vty 0 4"
    check_type: not_contains
    pattern: "transport input telnet"
    remediation: |
      line vty 0 4
       transport input ssh
```

#### Configuration Parameters

| Parameter | Description | Format | Required | Default | Validation |
|-----------|-------------|--------|----------|---------|------------|
| metadata.org | Organization name | String | Yes | None | Non-empty string |
| metadata.version | Policy version | String | Yes | None | Semantic versioning |
| metadata.last_updated | Last update date | Date (YYYY-MM-DD) | Yes | None | Valid date format |
| metadata.author | Author name | String | Yes | None | Non-empty string |
| metadata.description | Description | String | Yes | None | Non-empty string |
| policies[].id | Policy ID | String | Yes | None | Unique, alphanumeric with underscores |
| policies[].category | Policy category | String | Yes | None | Predefined category |
| policies[].description | Policy description | String | Yes | None | Non-empty string |
| policies[].severity | Severity level | String | Yes | None | critical, high, medium, low |
| policies[].platforms | Target platforms | List of strings | No | All platforms | Supported device types |
| policies[].check_command | Check command | String | Yes | None | Valid CLI command |
| policies[].check_type | Check type | String | Yes | None | Predefined check type |
| policies[].pattern | Pattern to match | String/Regex | Yes | None | Valid pattern |
| policies[].remediation | Remediation steps | String | Yes | None | Valid CLI commands |

#### Check Types

| Check Type | Description | Pattern Format |
|------------|-------------|----------------|
| `contains` | Output must contain pattern | String or regex |
| `not_contains` | Output must not contain pattern | String or regex |
| `regex_match` | Output must match regex | Regex pattern |
| `regex_extract` | Extract value and compare format | Regex with capture group |
| `line_format` | Lines matching filter must match pattern | Regex patterns |

#### Severity Levels

| Severity | Description | Action Required |
|----------|-------------|-----------------|
| `critical` | Security risk | Fix immediately |
| `high` | Important standard | Fix before next audit |
| `medium` | Best practice | Fix in next maintenance window |
| `low` | Nice to have | Fix when convenient |

#### Policy Categories

- Security
- NTP
- SNMP
- Logging
- Banner
- Naming
- Standards
- Redundancy
- Interface
- Management
- Health
- Crypto
- Compliance

#### Validation Rules

1. **Policy ID Validation:**
   - Must be unique across all policies
   - Must be alphanumeric with underscores
   - Case-sensitive

2. **Severity Validation:**
   - Must be one of: critical, high, medium, low
   - Case-sensitive

3. **Platform Validation:**
   - Must be supported device type or empty (all platforms)
   - Case-sensitive
   - Must match Netmiko device type mapping

4. **Check Type Validation:**
   - Must be one of predefined check types
   - Case-sensitive

5. **Pattern Validation:**
   - Must be valid string or regex pattern
   - Regex patterns must be valid Python regex

6. **Remediation Validation:**
   - Must be valid CLI commands
   - Can use placeholders: `{PLACEHOLDER}`
   - Multi-line strings supported

#### Error Messages

| Error | Message | Resolution |
|-------|---------|------------|
| Invalid YAML | `Invalid YAML format` | Check YAML syntax |
| Duplicate Policy ID | `Duplicate policy ID: {id}` | Use unique policy ID |
| Invalid Severity | `Invalid severity: {severity}` | Use valid severity level |
| Invalid Platform | `Invalid platform: {platform}` | Use supported device type |
| Invalid Check Type | `Invalid check type: {type}` | Use valid check type |
| Invalid Pattern | `Invalid pattern: {pattern}` | Check pattern syntax |
| Missing Required Field | `Missing required field: {field}` | Add required field |
| Invalid Date Format | `Invalid date format: {date}` | Use YYYY-MM-DD format |

#### Example Configurations

**Minimal Configuration:**
```yaml
metadata:
  org: "My Org"
  version: "1.0.0"
  last_updated: "2026-06-02"
  author: "Network Team"
  description: "Basic standards"

policies:
  - id: telnet_disabled
    category: Security
    description: "Telnet must be disabled"
    severity: critical
    platforms: [cisco_ios]
    check_command: "show line vty 0 4"
    check_type: not_contains
    pattern: "transport input telnet"
    remediation: "line vty 0 4\n transport input ssh"
```

**Full Configuration:**
```yaml
metadata:
  org: "Enterprise Network"
  version: "2.0.0"
  last_updated: "2026-06-02"
  author: "Network Engineering"
  description: "Enterprise-wide network configuration standards"

policies:
  # Security Policies
  - id: telnet_disabled
    category: Security
    description: "Telnet must be disabled on all VTY lines"
    severity: critical
    platforms: [cisco_ios, cisco_nxos, cisco_xe]
    check_command: "show line vty 0 4"
    check_type: not_contains
    pattern: "transport input telnet"
    remediation: |
      line vty 0 4
       transport input ssh
      line vty 5 15
       transport input ssh

  - id: ssh_version_2
    category: Security
    description: "SSH must be version 2 only"
    severity: critical
    platforms: [cisco_ios, cisco_nxos, cisco_xe]
    check_command: "show ip ssh"
    check_type: contains
    pattern: "SSH Enabled - version 2"
    remediation: "ip ssh version 2"

  # NTP Policies
  - id: ntp_synchronized
    category: NTP
    description: "NTP must be synchronized"
    severity: high
    platforms: [cisco_ios, cisco_nxos, cisco_xe, juniper_junos]
    check_command: "show ntp status"
    check_type: contains
    pattern: "Clock is synchronized"
    remediation: |
      ntp server {NTP_SERVER_1} prefer
      ntp server {NTP_SERVER_2}
```

#### Configuration Precedence

1. Policy-specific parameters override metadata defaults
2. Platform-specific policies override generic policies
3. Later policies override earlier policies for duplicate IDs

---

## Application Configuration

### 3. Application Settings

**Location:** Environment variables and application defaults  
**Purpose:** Application runtime configuration

#### Configuration Parameters

| Parameter | Description | Format | Required | Default | Validation |
|-----------|-------------|--------|----------|---------|------------|
| APP_HOST | Application host | String | No | 127.0.0.1 | Valid IP or hostname |
| APP_PORT | Application port | Integer | No | 5051 | 1-65535 |
| DEBUG_MODE | Debug mode | Boolean | No | False | true/false |
| LOG_LEVEL | Logging level | String | No | INFO | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| MAX_DEVICES | Maximum concurrent devices | Integer | No | 100 | 1-1000 |
| TIMEOUT | Device timeout (seconds) | Integer | No | 30 | 1-300 |

#### Environment Variables

```bash
# Application Host
export APP_HOST=127.0.0.1

# Application Port
export APP_PORT=5051

# Debug Mode
export DEBUG_MODE=false

# Log Level
export LOG_LEVEL=INFO

# Maximum Concurrent Devices
export MAX_DEVICES=100

# Device Timeout (seconds)
export TIMEOUT=30
```

#### Validation Rules

1. **Host Validation:**
   - Must be valid IP address or hostname
   - Must be reachable from application host
   - Cannot be empty

2. **Port Validation:**
   - Must be valid port number (1-65535)
   - Must not be in use by other applications
   - Cannot be 0

3. **Log Level Validation:**
   - Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL
   - Case-insensitive

4. **Max Devices Validation:**
   - Must be positive integer
   - Must be within system resource limits
   - Recommended: 10-1000

5. **Timeout Validation:**
   - Must be positive integer
   - Must be reasonable for network operations
   - Recommended: 10-300 seconds

#### Error Messages

| Error | Message | Resolution |
|-------|---------|------------|
| Invalid Host | `Invalid host: {host}` | Use valid IP or hostname |
| Invalid Port | `Invalid port: {port}` | Use port 1-65535 |
| Port in Use | `Port {port} already in use` | Use different port |
| Invalid Log Level | `Invalid log level: {level}` | Use valid log level |
| Invalid Max Devices | `Invalid max devices: {n}` | Use positive integer |
| Invalid Timeout | `Invalid timeout: {t}` | Use positive integer |

#### Example Configurations

**Development Configuration:**
```bash
export APP_HOST=127.0.0.1
export APP_PORT=5051
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG
export MAX_DEVICES=10
export TIMEOUT=30
```

**Production Configuration:**
```bash
export APP_HOST=0.0.0.0
export APP_PORT=5051
export DEBUG_MODE=false
export LOG_LEVEL=INFO
export MAX_DEVICES=100
export TIMEOUT=60
```

---

## Plugin Configuration

### 4. Plugin Settings

**Location:** Individual plugin directories  
**Purpose:** Plugin-specific configuration

#### Configuration Parameters

| Parameter | Description | Format | Required | Default | Validation |
|-----------|-------------|--------|----------|---------|------------|
| plugin_id | Plugin identifier | String | Yes | None | Unique, alphanumeric |
| version | Plugin version | String | Yes | None | Semantic versioning |
| enabled | Plugin enabled | Boolean | No | True | true/false |
| config_file | Configuration file path | String | No | None | Valid file path |

#### Example Configuration

```yaml
plugin_id: network_discovery
version: 1.4.0
enabled: true
config_file: plugins/network_discovery/config.yaml
```

---

## Configuration File Locations

| Configuration File | Location | Purpose |
|-------------------|----------|---------|
| inventory.txt | Root directory | Device inventory |
| standards.yaml | policies/ directory | Network standards |
| Application config | Environment variables | Runtime settings |
| Plugin configs | plugins/*/ directories | Plugin settings |

---

## Configuration Validation

### Validation Checklist

- [ ] inventory.txt format is valid INI
- [ ] All IP addresses are valid
- [ ] All device types are supported
- [ ] No duplicate IP addresses
- [ ] standards.yaml format is valid YAML
- [ ] All policy IDs are unique
- [ ] All severity levels are valid
- [ ] All platforms are supported
- [ ] All check types are valid
- [ ] All patterns are valid
- [ ] All remediation commands are valid
- [ ] Environment variables are set correctly
- [ ] Port is not in use
- [ ] Host is reachable
- [ ] Log level is valid

---

## Configuration Troubleshooting

### Common Issues

1. **Inventory File Not Found**
   - Error: `Inventory file not found: inventory.txt`
   - Resolution: Ensure inventory.txt exists in root directory

2. **Invalid Inventory Format**
   - Error: `Invalid inventory format`
   - Resolution: Check INI-style format, section headers, and device entries

3. **Policy File Not Found**
   - Error: `Policy file not found: standards.yaml`
   - Resolution: Ensure standards.yaml exists in policies/ directory

4. **Invalid Policy Format**
   - Error: `Invalid YAML format`
   - Resolution: Check YAML syntax, indentation, and structure

5. **Port Already in Use**
   - Error: `Port 5051 already in use`
   - Resolution: Use different port or stop conflicting application

6. **Invalid Device Type**
   - Error: `Unsupported device type: {type}`
   - Resolution: Use supported device type (cisco_ios, cisco_nxos, etc.)

---

## Configuration Best Practices

1. **Inventory File:**
   - Use descriptive group names
   - Organize devices by function or location
   - Add comments for clarity
   - Keep inventory file under version control

2. **Policy File:**
   - Use descriptive policy IDs
   - Group related policies by category
   - Include clear remediation steps
   - Test policies before deployment

3. **Application Configuration:**
   - Use environment variables for sensitive settings
   - Document all configuration parameters
   - Use appropriate log levels for environment
   - Set reasonable timeout values

4. **Plugin Configuration:**
   - Enable only required plugins
   - Keep plugin configurations up to date
   - Test plugin configurations before deployment
   - Document plugin-specific settings

---

## References

- API Documentation: docs/02-codebase/API_DOCUMENTATION.md
- Code Inventory: docs/02-codebase/CODE_INVENTORY.md
- Module Architecture: docs/01-architecture/MODULE_ARCHITECTURE.md
- Standards Validator Plugin: docs/plugins/standards_validator/README.md
