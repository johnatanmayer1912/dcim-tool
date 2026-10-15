# Plugin Multi-Platform Compatibility Guide

**Version:** v6.0.0-BETA  
**Date:** 2026-04-20

---

## Supported Platforms

All 7 plugins support the following platforms with fallback commands for older versions:

- **Cisco IOS** (12.x, 15.x, 16.x, 17.x)
- **Cisco IOS-XE** (3.x, 16.x, 17.x)
- **Cisco NXOS** (4.x, 5.x, 6.x, 7.x, 9.x, 10.x)
- **Juniper JunOS** (10.x, 11.x, 12.x, 15.x, 18.x, 20.x, 21.x)

---

## Plugin Commands by Platform

### 1. Device Time Check (`device_time`)

| Platform | Time Commands | NTP Commands |
|----------|--------------|--------------|
| **Cisco IOS/XE** | `show clock detail`, `show clock`, `show calendar` | `show ntp status`, `show ntp associations`, `show ntp peer-status`, `show clock source` |
| **Cisco NXOS** | `show clock detail`, `show clock` | `show ntp peers`, `show ntp status` |
| **Juniper JunOS** | `show system uptime`, `show system information \| match time` | `show ntp associations`, `show ntp status`, `show system information \| match NTP` |

### 2. Serial Number Inventory (`serial_number`)

| Platform | Version Commands | Inventory Commands |
|----------|-----------------|-------------------|
| **Cisco IOS/XE** | `show version`, `show ver` | `show inventory`, `show diag`, `show module` |
| **Cisco NXOS** | `show version`, `show ver` | `show inventory` |
| **Juniper JunOS** | `show version`, `show version detail`, `show system information` | `show chassis hardware`, `show chassis hardware detail`, `show chassis fpc` |

**Serial Number Patterns:**
- `Serial Number:`, `Chassis Serial`, `System Serial`
- `Processor Board ID`, `Hardware Serial`
- Juniper format: `SN:`, `Serial #`

### 3. Critical Log Scanner (`critical_logs`)

| Platform | Log Commands |
|----------|-------------|
| **Cisco IOS/XE** | `show logging`, `show log`, `show logging \| tail N` |
| **Cisco NXOS** | `show logging last N`, `show logg last N`, `show logging` |
| **Juniper JunOS** | `show log messages \| last N`, `show log \| last N`, `show log messages` |

**Severity Keywords:**
- `EMERGENCY`, `ALERT`, `CRITICAL`, `ERROR`, `WARNING`

### 4. Interface Error Check (`interface_errors`)

| Platform | Error Counter Commands |
|----------|----------------------|
| **Cisco IOS/XE** | `show interfaces counters errors`, `show interfaces counter error`, `show controllers`, `show interfaces`, `show ip interface brief` |
| **Cisco NXOS** | `show interface counters errors`, `show interface counters error`, `show interface brief` |
| **Juniper JunOS** | `show interfaces extensive`, `show interfaces detail`, `show interface extensive` |

**Error Types Detected:**
- Input/Output Errors, CRC Errors, Giants, Runts, Collisions

### 5. Environment Health Check (`environment_status`)

| Platform | Temperature | Fan | Power |
|----------|------------|-----|-------|
| **Cisco IOS/XE** | `show environment`, `show env` | Same command | Same command |
| **Cisco NXOS** | `show environment temperature`, `show env temperature`, `show temp` | `show environment fan`, `show env fan`, `show fan` | `show environment power`, `show env power`, `show power` |
| **Juniper JunOS** | `show chassis temperature-thresholds`, `show chassis temp` | `show chassis fan`, `show chassis cooling` | `show chassis power`, `show chassis pem` |

### 6. VLAN Audit (`vlan_audit`)

| Platform | VLAN Commands |
|----------|--------------|
| **Cisco IOS/XE** | `show vlan brief`, `show vlan` |
| **Cisco NXOS** | `show vlan brief`, `show vlan` |
| **Juniper JunOS** | `show vlans` |

### 7. Base Plugin Template (`base_template`)

Reference implementation using `safe_connection` context manager with proper error handling.

---

## Hostname Detection

All plugins use multi-command hostname detection:

### Cisco Platforms:
1. `show running-config \| include hostname`
2. `show run \| inc hostname`
3. `show hostname`
4. `show version \| include hostname`

### Juniper Platforms:
1. `show configuration system host-name`
2. `show system information \| match Hostname`
3. `show host-name`

---

## Error Handling Strategy

### Command Fallback Pattern:
```python
commands = [
    "primary command",
    "alternative syntax",
    "older version command"
]
for cmd in commands:
    try:
        output = conn.send_command(cmd)
        if output and not error:
            break
    except:
        continue
```

### Error Detection:
- `%` symbol (Cisco error indicator)
- `error` in output (Juniper/Linux style)
- `invalid` in output (syntax errors)
- `not available` / `not supported`

---

## Testing Recommendations

### Minimum Versions Tested:
- **Cisco IOS**: 12.2(55)SE
- **Cisco IOS-XE**: 3.6.0E
- **Cisco NXOS**: 4.2(1)N2
- **Juniper JunOS**: 10.4R3

### Test Each Platform:
1. Start web server: `python vlan_checker_web.py`
2. Select device type in inventory
3. Test each plugin against real devices
4. Verify fallback commands work on older versions

---

## Troubleshooting

### If plugin fails on specific device:

1. **Check device_type in inventory** - Must match:
   - `cisco_ios`, `cisco_xe`, `cisco_nxos`
   - `juniper_junos`, `juniper`

2. **Enable logging** to see which commands were tried

3. **Manual test commands** via CLI terminal

4. **Check for privilege level** - Some commands need enable mode

---

## Version Compatibility Matrix

| Plugin | IOS 12.x | IOS 15.x | IOS-XE | NXOS 7.x | NXOS 9.x | JunOS 12.x | JunOS 18.x |
|--------|----------|----------|--------|----------|----------|------------|------------|
| Device Time | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Serial Number | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Critical Logs | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Interface Errors | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Environment | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| VLAN Audit | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

✅ = Supported with fallbacks

---

**Note:** Plugins gracefully degrade on unsupported platforms by returning "command not available" rather than crashing.
