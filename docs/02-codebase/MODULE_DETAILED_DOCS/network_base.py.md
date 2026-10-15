# network_base.py Documentation

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | active |
| **Owner** | Lead Developer (R-ENG) |
| **Last Updated** | 2026-07-21 |
| **Application Version** | 7.0.85 |

## Overview

`modules/network_base.py` provides foundational network connection and device parsing utilities for Network Swiss Tool Pro. It handles SSH connections with legacy algorithm fallback, hostname resolution, VLAN parsing, and inventory loading.

## File Location

- **Path**: `modules/network_base.py`
- **Lines**: 411
- **Dependencies**: re, contextlib, netmiko, telnetlib/telnetlib_compat

## Dependencies

### External Dependencies
- `netmiko` - SSH connection management
- `telnetlib` / `telnetlib_compat` - Telnet compatibility for Python 3.13+
- `re` - Regular expressions for parsing
- `contextlib` - Context manager utilities

### Internal Dependencies
- `utils.task_credentials` - Task credential management

## Key Functions

### `build_json(device_host, status, data=None, error=None)`

**Purpose**: Build standardized JSON response object

**Parameters**:
- `device_host` (str): Device hostname/IP
- `status` (str): "success" or "fail"
- `data` (dict, optional): Response data
- `error` (str, optional): Error message

**Returns**: `dict` - Standardized response object

**Format**:
```python
{
    "device": device_host,
    "status": status,
    "data": data if data is not None else {},
    "error": str(error) if error else None
}
```

### `connect_permissive(target_dict, user, pwd, enb_pwd, log_func=None)`

**Purpose**: Two-pass SSH connection strategy with legacy algorithm fallback

**Parameters**:
- `target_dict` (dict): Device dict with host, device_type, port
- `user` (str): Username
- `pwd` (str): Password
- `enb_pwd` (str): Enable password
- `log_func` (callable, optional): Logging function

**Returns**: `netmiko.ConnectHandler` - Connection object

**Strategy**:
- **Pass 1**: Modern algorithms (default Paramiko behavior)
  - Works on IOS-XE 17.3+, NX-OS 9.3+, Juniper 21.x+
- **Pass 2**: Legacy fallback
  - Disables rsa-sha2-512/256 for older devices
  - Supports devices that only use ssh-rsa (SHA-1)

**Security Note**: Only falls back on SSH algorithm negotiation failures. Auth failures (wrong password) are NOT retried to prevent account lockout.

**Base Parameters**:
```python
{
    "host": host,
    "device_type": dtype,
    "username": user,
    "password": pwd,
    "global_delay_factor": 1.5,
    "timeout": 20,
    "auth_timeout": 20,
    "banner_timeout": 20,
    "port": target_dict.get('port', 22),
    "secret": enb_pwd or become_password
}
```

### `safe_node_name(hostname)`

**Purpose**: Sanitize and validate hostname candidates

**Parameters**:
- `hostname` (str): Raw hostname string

**Returns**: `str` or `None` - Sanitized hostname or None if invalid

**Validation Rules**:
- Strips CLI prompt characters (`:>#)]`)
- Rejects banner-like strings
- Rejects blacklisted words (password, login, username, etc.)
- Rejects strings < 2 characters
- Returns IP addresses as-is
- Returns first part of FQDN (before first dot)

### `resolve_device_hostname(conn, ver_output, fallback_ip, device_type=None, log_func=None)`

**Purpose**: Resolve stable device hostname for graph labels

**Parameters**:
- `conn` (netmiko.ConnectHandler, optional): Active connection
- `ver_output` (str, optional): Output from "show version"
- `fallback_ip` (str): Management IP as fallback
- `device_type` (str, optional): Device type for parsing
- `log_func` (callable, optional): Logging function

**Returns**: `str` - Resolved hostname

**Resolution Order**:
1. SSH prompt parsing
2. show version fields parsing
3. show hostname command
4. Fallback to management IP

### `resolve_hostname_from_prompt(conn, fallback_ip, device_type=None)`

**Purpose**: Resolve hostname from SSH prompt only

**Parameters**:
- `conn` (netmiko.ConnectHandler, optional): Active connection
- `fallback_ip` (str): Management IP as fallback
- `device_type` (str, optional): Device type

**Returns**: `str` - Resolved hostname

### `resolve_hostname_from_connection(conn, fallback_ip, device_type=None, log_func=None, fetch_version=True)`

**Purpose**: Resolve hostname using prompt and optionally show version

**Parameters**:
- `conn` (netmiko.ConnectHandler, optional): Active connection
- `fallback_ip` (str): Management IP as fallback
- `device_type` (str, optional): Device type
- `log_func` (callable, optional): Logging function
- `fetch_version` (bool): Whether to fetch show version

**Returns**: `str` - Resolved hostname

### `normalize_neighbor_hostname(hostname, fallback=None)`

**Purpose**: Sanitize neighbor CDP/LLDP names

**Parameters**:
- `hostname` (str): Raw neighbor hostname
- `fallback` (str, optional): Fallback value

**Returns**: `str` - Sanitized hostname

**Behavior**:
- Removes parenthetical information
- Rejects banner-like strings
- Applies safe_node_name validation
- Returns lowercase first part of FQDN

### `parse_vlan_output(output, device_type)`

**Purpose**: Parse VLAN output from show commands

**Parameters**:
- `output` (str): Raw command output
- `device_type` (str): Device type for parser selection

**Returns**: `list` - List of tuples (vlan_id, name, status)

**Parsers**:
- **Cisco Family**: Pattern `^(\d+)\s+([\w-]+)\s+([\w-]+)`
- **Juniper ELS**: Pattern `^\S+\s+([\w-]+)\s+(\d+)`
- **Juniper Legacy**: Pattern `^([\w-]+)\s+(\d+)`

### `get_devices_from_file(path)`

**Purpose**: Centralized inventory loader supporting group headers

**Parameters**:
- `path` (str): Path to inventory file

**Returns**: `list` - List of device dictionaries

**File Format**:
```
# Comment line
[GroupName]
host1,cisco_ios,22,group1
host2,cisco_nxos,22,group1
host3,juniper,22
```

**Device Object**:
```python
{
    "host": "host1",
    "device_type": "cisco_ios",
    "port": 22,
    "group": "group1"
}
```

**Behavior**:
- Skips comment lines (starting with #)
- Supports [GroupName] headers
- Supports comma or space separation
- Default port: 22
- Default group: "Default"

### `safe_connection(device, user, pwd, enb_pwd, log_func=None)`

**Purpose**: Context manager for safe connect/disconnect with logging

**Parameters**:
- `device` (dict): Device dict with host, device_type, port
- `user` (str): Username
- `pwd` (str): Password
- `enb_pwd` (str): Enable password
- `log_func` (callable, optional): Logging function

**Yields**: `netmiko.ConnectHandler` - Connection object

**Example**:
```python
with safe_connection(device, user, pwd, enb_pwd, log) as conn:
    output = conn.send_command("show version")
```

**Behavior**:
- Logs connection attempt
- Uses connect_permissive for connection
- Logs success/failure
- Ensures proper cleanup on exit

## Helper Functions

### `_enable_if_needed(conn, device_type, secret_password=None, log_func=None)`

**Purpose**: Attempt enable mode for Cisco-family devices

**Parameters**:
- `conn` (netmiko.ConnectHandler): Connection object
- `device_type` (str): Device type
- `secret_password` (str, optional): Enable password
- `log_func` (callable, optional): Logging function

**Behavior**:
- Checks if already in enable mode
- Attempts enable if needed
- Logs success/failure
- Does not raise on failure (some devices don't need enable)

### `_hostname_looks_like_banner(value)`

**Purpose**: Reject show-version banner blobs mistaken for hostnames

**Parameters**:
- `value` (str): Candidate hostname

**Returns**: `bool` - True if looks like banner

**Markers**: 'software', 'http://', 'copyright', 'cisco nexus', 'nx-os', 'ios software'

### `_prompt_looks_invalid(value)`

**Purpose**: Reject SSH/login noise mistaken for hostname

**Parameters**:
- `value` (str): Candidate hostname

**Returns**: `bool` - True if invalid prompt

**Markers**: 'password', 'username', 'login:', 'authentication failed', 'access denied'

### `_fallback_hostname_label(fallback_ip)`

**Purpose**: Management IP or inventory label as fallback

**Parameters**:
- `fallback_ip` (str): IP address or label

**Returns**: `str` - Fallback hostname

### `_hostname_from_prompt_text(prompt)`

**Purpose**: Normalize find_prompt() text to hostname candidate

**Parameters**:
- `prompt` (str): Raw prompt text

**Returns**: `str` or `None` - Hostname candidate

**Behavior**:
- Removes config mode suffixes
- Strips prompt characters (#, >, :)
- Extracts username@hostname format
- Validates with safe_node_name

### `_hostname_from_ver_output(ver_output, device_type)`

**Purpose**: Parse hostname from show version output

**Parameters**:
- `ver_output` (str): show version output
- `device_type` (str): Device type for pattern selection

**Returns**: `str` or `None` - Parsed hostname

**Patterns**:
- `switchname : (\S+)`
- `Device name : (\S+)`
- `hostname : (\S+)`
- `hostname (\S+)`
- NX-OS uptime pattern

## Data Structures

### Device Object
```python
{
    "host": "device_ip_or_hostname",
    "device_type": "cisco_ios|cisco_nxos|juniper|etc",
    "port": 22,
    "group": "group_name"
}
```

### VLAN Result
```python
(vlan_id, vlan_name, status)
# Example: ("100", "DATA_VLAN", "active")
```

### Response Object
```python
{
    "device": "device_ip_or_hostname",
    "status": "success|fail",
    "data": {},
    "error": "error_message_if_failed"
}
```

## Error Handling

### SSH Algorithm Negotiation
- **Error**: "no acceptable kex", "algorithm negotiation"
- **Action**: Retry with legacy algorithms (disable SHA-2 pubkeys)
- **Log**: "SSH algorithm mismatch, trying legacy mode..."

### Authentication Failure
- **Error**: Wrong password, authentication failed
- **Action**: Propagate immediately (no retry to prevent lockout)
- **Log**: Connection/operation failed message

### Network Errors
- **Error**: Timeout, connection refused
- **Action**: Propagate immediately
- **Log**: Connection/operation failed message

### Hostname Resolution Failure
- **Error**: All hostname resolution methods fail
- **Action**: Use management IP as fallback
- **Log**: "Using management IP as hostname label"

## Security Features

### Two-Pass Connection Strategy
- Pass 1: Modern algorithms (secure)
- Pass 2: Legacy fallback (only for algorithm negotiation)
- No retry on auth failures (prevents lockout)

### Input Validation
- Hostname validation against blacklists
- Banner detection and rejection
- Prompt validation to prevent injection

### Credential Handling
- Enable password from parameter or task credentials
- Secure credential storage via task_credentials module

## Usage Examples

### Connect to Device
```python
from modules.network_base import connect_permissive

device = {'host': '192.168.1.1', 'device_type': 'cisco_ios', 'port': 22}
conn = connect_permissive(device, 'admin', 'password', 'enable', print)
output = conn.send_command('show version')
conn.disconnect()
```

### Safe Connection with Context Manager
```python
from modules.network_base import safe_connection

with safe_connection(device, 'admin', 'password', 'enable', print) as conn:
    output = conn.send_command('show version')
```

### Load Inventory
```python
from modules.network_base import get_devices_from_file

devices = get_devices_from_file('inventory.txt')
for device in devices:
    print(f"Host: {device['host']}, Type: {device['device_type']}")
```

### Resolve Hostname
```python
from modules.network_base import resolve_device_hostname

hostname = resolve_device_hostname(conn, ver_output, '192.168.1.1', 'cisco_ios', print)
```

### Parse VLAN Output
```python
from modules.network_base import parse_vlan_output

vlans = parse_vlan_output(output, 'cisco_ios')
for vlan_id, name, status in vlans:
    print(f"VLAN {vlan_id}: {name} ({status})")
```

## Related Documentation

- `main.py.md` - Entry point documentation
- `adapters.py.md` - Adapters module documentation
- `modules/credential_manager.py.md` - Credential manager documentation

## Cross-References

- References: `netmiko` (SSH library)
- References: `utils/task_credentials.py` (credential management)
- Referenced by: `adapters.py` (device operations)
- Referenced by: All feature modules (network operations)
