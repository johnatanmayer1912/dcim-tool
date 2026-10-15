# Jinja2 Templates Documentation

## Overview

Network Swiss Tool Pro uses Jinja2 templates for configuration generation. This document provides comprehensive documentation for all Jinja2 templates.

**Generated:** 2026-06-02  
**Purpose:** Template documentation for configuration generation  
**Templates Location:** templates/

---

## Template Overview

| Template | Platform | Purpose | Variables |
|----------|----------|---------|-----------|
| cisco_ios_ntp.j2 | Cisco IOS | NTP configuration | ntp_servers, timezone, source_interface |
| cisco_ios_port_channel.j2 | Cisco IOS | Port-Channel configuration | port_channel_id, mode, members, description |
| cisco_ios_syslog.j2 | Cisco IOS | Syslog configuration | syslog_servers, logging_level, source_interface |
| cisco_ios_trunk.j2 | Cisco IOS | Trunk configuration | interface, allowed_vlans, native_vlan |
| cisco_nxos_port_channel.j2 | Cisco NX-OS | Port-Channel configuration | port_channel_id, mode, members, description, vpc |
| cisco_nxos_trunk.j2 | Cisco NX-OS | Trunk configuration | interface, allowed_vlans, native_vlan |
| cisco_nxos_trunk_vpc.j2 | Cisco NX-OS | vPC Trunk configuration | interface, allowed_vlans, native_vlan, vpc_id |
| juniper_junos_ntp.j2 | Juniper JunOS | NTP configuration | ntp_servers, timezone, source_interface |

---

## cisco_ios_ntp.j2

### Purpose
Generate NTP configuration for Cisco IOS devices.

### File Location
`templates/cisco_ios_ntp.j2`

### File Size
~277 bytes

### Variables

#### ntp_servers
**Type:** List of strings  
**Description:** List of NTP server IP addresses  
**Example:** `["10.1.1.1", "10.1.1.2"]`

#### timezone
**Type:** String  
**Description:** Timezone configuration  
**Example:** `"PST8PDT,M3.2.0,M11.1.0"`

#### source_interface
**Type:** String  
**Description:** Source interface for NTP packets  
**Example:** `"GigabitEthernet0/0"`

### Template Content
```jinja2
{% if ntp_servers %}
{% for server in ntp_servers %}
ntp server {{ server }}
{% endfor %}
{% endif %}
{% if timezone %}
clock timezone {{ timezone }}
{% endif %}
{% if source_interface %}
ntp source {{ source_interface }}
{% endif %}
```

### Usage Example
```python
from jinja2 import Template

template = Template(open('templates/cisco_ios_ntp.j2').read())
config = template.render(
    ntp_servers=["10.1.1.1", "10.1.1.2"],
    timezone="PST8PDT,M3.2.0,M11.1.0",
    source_interface="GigabitEthernet0/0"
)
```

### Generated Output
```
ntp server 10.1.1.1
ntp server 10.1.1.2
clock timezone PST8PDT,M3.2.0,M11.1.0
ntp source GigabitEthernet0/0
```

### Platform-Specific Notes
- Cisco IOS NTP configuration syntax
- Supports multiple NTP servers
- Timezone format: `timezone_name,offset,dst_offset,dst_start,dst_end`

---

## cisco_ios_port_channel.j2

### Purpose
Generate Port-Channel configuration for Cisco IOS devices.

### File Location
`templates/cisco_ios_port_channel.j2`

### File Size
~484 bytes

### Variables

#### port_channel_id
**Type:** Integer  
**Description:** Port-Channel interface number  
**Example:** `1`

#### mode
**Type:** String  
**Description:** Port-Channel mode (active or on)  
**Example:** `"active"`

#### members
**Type:** List of strings  
**Description:** List of member interfaces  
**Example:** `["GigabitEthernet0/1", "GigabitEthernet0/2"]`

#### description
**Type:** String  
**Description:** Port-Channel description  
**Example:** `"Uplink to Core"`

### Template Content
```jinja2
interface Port-channel{{ port_channel_id }}
{% if description %}
 description {{ description }}
{% endif %}
{% if mode %}
 channel-group {{ port_channel_id }} mode {{ mode }}
{% endif %}
{% for member in members %}
interface {{ member }}
 channel-group {{ port_channel_id }} mode {{ mode }}
{% endfor %}
```

### Usage Example
```python
from jinja2 import Template

template = Template(open('templates/cisco_ios_port_channel.j2').read())
config = template.render(
    port_channel_id=1,
    mode="active",
    members=["GigabitEthernet0/1", "GigabitEthernet0/2"],
    description="Uplink to Core"
)
```

### Generated Output
```
interface Port-channel1
 description Uplink to Core
 channel-group 1 mode active
interface GigabitEthernet0/1
 channel-group 1 mode active
interface GigabitEthernet0/2
 channel-group 1 mode active
```

### Platform-Specific Notes
- Cisco IOS Port-Channel configuration syntax
- Supports LACP (active) or static (on) mode
- Member interfaces configured individually

---

## cisco_ios_syslog.j2

### Purpose
Generate Syslog configuration for Cisco IOS devices.

### File Location
`templates/cisco_ios_syslog.j2`

### File Size
~247 bytes

### Variables

#### syslog_servers
**Type:** List of strings  
**Description:** List of Syslog server IP addresses  
**Example:** `["10.1.1.10", "10.1.1.11"]`

#### logging_level
**Type:** String  
**Description:** Logging level (debugging, informational, notification, warning, error, critical, alert, emergency)  
**Example:** `"informational"`

#### source_interface
**Type:** String  
**Description:** Source interface for Syslog packets  
**Example:** `"GigabitEthernet0/0"`

### Template Content
```jinja2
{% if logging_level %}
logging {{ logging_level }}
{% endif %}
{% if syslog_servers %}
{% for server in syslog_servers %}
logging host {{ server }}
{% endfor %}
{% endif %}
{% if source_interface %}
logging source-interface {{ source_interface }}
{% endif %}
```

### Usage Example
```python
from jinja2 import Template

template = Template(open('templates/cisco_ios_syslog.j2').read())
config = template.render(
    syslog_servers=["10.1.1.10", "10.1.1.11"],
    logging_level="informational",
    source_interface="GigabitEthernet0/0"
)
```

### Generated Output
```
logging informational
logging host 10.1.1.10
logging host 10.1.1.11
logging source-interface GigabitEthernet0/0
```

### Platform-Specific Notes
- Cisco IOS Syslog configuration syntax
- Supports multiple Syslog servers
- Logging levels follow standard syslog severity levels

---

## cisco_ios_trunk.j2

### Purpose
Generate Trunk configuration for Cisco IOS devices.

### File Location
`templates/cisco_ios_trunk.j2`

### File Size
~333 bytes

### Variables

#### interface
**Type:** String  
**Description:** Interface name  
**Example:** `"GigabitEthernet0/1"`

#### allowed_vlans
**Type:** String  
**Description:** Allowed VLAN list (range or specific)  
**Example:** `"10,20,30"` or `"10-20"`

#### native_vlan
**Type:** Integer  
**Description:** Native VLAN ID  
**Example:** `1`

### Template Content
```jinja2
interface {{ interface }}
 switchport mode trunk
{% if native_vlan %}
 switchport trunk native vlan {{ native_vlan }}
{% endif %}
{% if allowed_vlans %}
 switchport trunk allowed vlan {{ allowed_vlans }}
{% endif %}
```

### Usage Example
```python
from jinja2 import Template

template = Template(open('templates/cisco_ios_trunk.j2').read())
config = template.render(
    interface="GigabitEthernet0/1",
    allowed_vlans="10,20,30",
    native_vlan=1
)
```

### Generated Output
```
interface GigabitEthernet0/1
 switchport mode trunk
 switchport trunk native vlan 1
 switchport trunk allowed vlan 10,20,30
```

### Platform-Specific Notes
- Cisco IOS Trunk configuration syntax
- Supports VLAN ranges (e.g., "10-20")
- Supports specific VLANs (e.g., "10,20,30")
- Native VLAN defaults to VLAN 1

---

## cisco_nxos_port_channel.j2

### Purpose
Generate Port-Channel configuration for Cisco NX-OS devices.

### File Location
`templates/cisco_nxos_port_channel.j2`

### File Size
~528 bytes

### Variables

#### port_channel_id
**Type:** Integer  
**Description:** Port-Channel interface number  
**Example:** `1`

#### mode
**Type:** String  
**Description:** Port-Channel mode (active or on)  
**Example:** `"active"`

#### members
**Type:** List of strings  
**Description:** List of member interfaces  
**Example:** `["Ethernet1/1", "Ethernet1/2"]`

#### description
**Type:** String  
**Description:** Port-Channel description  
**Example:** `"Uplink to Core"`

#### vpc
**Type:** Integer  
**Description:** vPC ID (optional)  
**Example:** `1`

### Template Content
```jinja2
interface port-channel{{ port_channel_id }}
{% if description %}
 description {{ description }}
{% endif %}
{% if vpc %}
 vpc {{ vpc }}
{% endif %}
{% for member in members %}
interface {{ member }}
 channel-group {{ port_channel_id }} mode {{ mode }}
{% endfor %}
```

### Usage Example
```python
from jinja2 import Template

template = Template(open('templates/cisco_nxos_port_channel.j2').read())
config = template.render(
    port_channel_id=1,
    mode="active",
    members=["Ethernet1/1", "Ethernet1/2"],
    description="Uplink to Core",
    vpc=1
)
```

### Generated Output
```
interface port-channel1
 description Uplink to Core
 vpc 1
interface Ethernet1/1
 channel-group 1 mode active
interface Ethernet1/2
 channel-group 1 mode active
```

### Platform-Specific Notes
- Cisco NX-OS Port-Channel configuration syntax
- Supports vPC integration
- Interface naming convention: EthernetX/Y
- vPC configuration on Port-Channel interface only

---

## cisco_nxos_trunk.j2

### Purpose
Generate Trunk configuration for Cisco NX-OS devices.

### File Location
`templates/cisco_nxos_trunk.j2`

### File Size
~321 bytes

### Variables

#### interface
**Type:** String  
**Description:** Interface name  
**Example:** `"Ethernet1/1"`

#### allowed_vlans
**Type:** String  
**Description:** Allowed VLAN list (range or specific)  
**Example:** `"10,20,30"` or `"10-20"`

#### native_vlan
**Type:** Integer  
**Description:** Native VLAN ID  
**Example:** `1`

### Template Content
```jinja2
interface {{ interface }}
 switchport mode trunk
{% if native_vlan %}
 switchport trunk native vlan {{ native_vlan }}
{% endif %}
{% if allowed_vlans %}
 switchport trunk allowed vlan {{ allowed_vlans }}
{% endif %}
```

### Usage Example
```python
from jinja2 import Template

template = Template(open('templates/cisco_nxos_trunk.j2').read())
config = template.render(
    interface="Ethernet1/1",
    allowed_vlans="10,20,30",
    native_vlan=1
)
```

### Generated Output
```
interface Ethernet1/1
 switchport mode trunk
 switchport trunk native vlan 1
 switchport trunk allowed vlan 10,20,30
```

### Platform-Specific Notes
- Cisco NX-OS Trunk configuration syntax
- Similar to IOS but with NX-OS interface naming
- Supports VLAN ranges and specific VLANs
- Native VLAN defaults to VLAN 1

---

## cisco_nxos_trunk_vpc.j2

### Purpose
Generate vPC Trunk configuration for Cisco NX-OS devices.

### File Location
`templates/cisco_nxos_trunk_vpc.j2`

### File Size
~337 bytes

### Variables

#### interface
**Type:** String  
**Description:** Interface name  
**Example:** `"Ethernet1/1"`

#### allowed_vlans
**Type:** String  
**Description:** Allowed VLAN list (range or specific)  
**Example:** `"10,20,30"` or `"10-20"`

#### native_vlan
**Type:** Integer  
**Description:** Native VLAN ID  
**Example:** `1`

#### vpc_id
**Type:** Integer  
**Description:** vPC ID  
**Example:** `1`

### Template Content
```jinja2
interface {{ interface }}
 switchport mode trunk
{% if native_vlan %}
 switchport trunk native vlan {{ native_vlan }}
{% endif %}
{% if allowed_vlans %}
 switchport trunk allowed vlan {{ allowed_vlans }}
{% endif %}
 vpc {{ vpc_id }}
```

### Usage Example
```python
from jinja2 import Template

template = Template(open('templates/cisco_nxos_trunk_vpc.j2').read())
config = template.render(
    interface="Ethernet1/1",
    allowed_vlans="10,20,30",
    native_vlan=1,
    vpc_id=1
)
```

### Generated Output
```
interface Ethernet1/1
 switchport mode trunk
 switchport trunk native vlan 1
 switchport trunk allowed vlan 10,20,30
 vpc 1
```

### Platform-Specific Notes
- Cisco NX-OS vPC Trunk configuration syntax
- vPC configuration on member interface
- Used for vPC peer-link and member links
- vPC ID must match vPC domain configuration

---

## juniper_junos_ntp.j2

### Purpose
Generate NTP configuration for Juniper JunOS devices.

### File Location
`templates/juniper_junos_ntp.j2`

### File Size
~242 bytes

### Variables

#### ntp_servers
**Type:** List of strings  
**Description:** List of NTP server IP addresses  
**Example:** `["10.1.1.1", "10.1.1.2"]`

#### timezone
**Type:** String  
**Description:** Timezone configuration  
**Example:** `"America/Los_Angeles"`

#### source_interface
**Type:** String  
**Description:** Source interface for NTP packets  
**Example:** `"ge-0/0/0"`

### Template Content
```jinja2
set system ntp servers {% for server in ntp_servers %}{{ server }} {% endfor %}
{% if timezone %}
set system time-zone {{ timezone }}
{% endif %}
{% if source_interface %}
set system ntp source-address {{ source_interface }}
{% endif %}
```

### Usage Example
```python
from jinja2 import Template

template = Template(open('templates/juniper_junos_ntp.j2').read())
config = template.render(
    ntp_servers=["10.1.1.1", "10.1.1.2"],
    timezone="America/Los_Angeles",
    source_interface="ge-0/0/0"
)
```

### Generated Output
```
set system ntp servers 10.1.1.1 10.1.1.2 
set system time-zone America/Los_Angeles
set system ntp source-address ge-0/0/0
```

### Platform-Specific Notes
- Juniper JunOS configuration syntax (set commands)
- Timezone format: IANA timezone database format
- Interface naming convention: ge-X/Y/Z
- Configuration format differs from Cisco (set commands)

---

## Template Usage in Application

### Config Templates Plugin
The config_templates plugin uses these templates to generate device configurations.

**Plugin Location:** `modules/plugins/config_templates.py`

**Template Loading:**
```python
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('templates/'))
template = env.get_template('cisco_ios_ntp.j2')
config = template.render(variables)
```

**Template Selection:**
Based on device type and configuration type:
- Cisco IOS: cisco_ios_*.j2 templates
- Cisco NX-OS: cisco_nxos_*.j2 templates
- Juniper JunOS: juniper_junos_*.j2 templates

---

## Template Variables Reference

### Common Variables

#### ntp_servers
**Type:** List of strings  
**Platforms:** Cisco IOS, Juniper JunOS  
**Description:** NTP server IP addresses  
**Validation:** Must be valid IP addresses

#### timezone
**Type:** String  
**Platforms:** Cisco IOS, Juniper JunOS  
**Description:** Timezone configuration  
**Validation:** Platform-specific format

#### source_interface
**Type:** String  
**Platforms:** Cisco IOS, Juniper JunOS  
**Description:** Source interface for NTP/Syslog packets  
**Validation:** Must be valid interface name

#### interface
**Type:** String  
**Platforms:** Cisco IOS, Cisco NX-OS  
**Description:** Interface name  
**Validation:** Must be valid interface name for platform

#### allowed_vlans
**Type:** String  
**Platforms:** Cisco IOS, Cisco NX-OS  
**Description:** Allowed VLAN list  
**Validation:** VLAN range or specific VLANs

#### native_vlan
**Type:** Integer  
**Platforms:** Cisco IOS, Cisco NX-OS  
**Description:** Native VLAN ID  
**Validation:** Valid VLAN ID (1-4094)

#### port_channel_id
**Type:** Integer  
**Platforms:** Cisco IOS, Cisco NX-OS  
**Description:** Port-Channel interface number  
**Validation:** Valid Port-Channel number

#### mode
**Type:** String  
**Platforms:** Cisco IOS, Cisco NX-OS  
**Description:** Port-Channel mode  
**Validation:** "active" or "on"

#### members
**Type:** List of strings  
**Platforms:** Cisco IOS, Cisco NX-OS  
**Description:** Member interfaces  
**Validation:** Must be valid interface names for platform

#### description
**Type:** String  
**Platforms:** Cisco IOS, Cisco NX-OS  
**Description:** Interface description  
**Validation:** Free-form text

#### vpc / vpc_id
**Type:** Integer  
**Platforms:** Cisco NX-OS  
**Description:** vPC ID  
**Validation:** Valid vPC ID

#### syslog_servers
**Type:** List of strings  
**Platforms:** Cisco IOS  
**Description:** Syslog server IP addresses  
**Validation:** Must be valid IP addresses

#### logging_level
**Type:** String  
**Platforms:** Cisco IOS  
**Description:** Logging level  
**Validation:** Valid syslog severity level

---

## Platform-Specific Differences

### Cisco IOS vs Cisco NX-OS

#### Interface Naming
- **IOS:** `GigabitEthernet0/1`, `FastEthernet0/1`
- **NX-OS:** `Ethernet1/1`, `Ethernet1/2`

#### Port-Channel Naming
- **IOS:** `Port-channel1`
- **NX-OS:** `port-channel1`

#### vPC Support
- **IOS:** Not supported
- **NX-OS:** Supported (vPC configuration)

#### Configuration Syntax
- **IOS:** Standard IOS syntax
- **NX-OS:** Similar to IOS with NX-OS extensions

### Cisco vs Juniper

#### Configuration Format
- **Cisco:** Hierarchical configuration (interface, subcommands)
- **Juniper:** Set commands (set system ntp servers)

#### Timezone Format
- **Cisco:** `timezone_name,offset,dst_offset,dst_start,dst_end`
- **Juniper:** IANA timezone database format (e.g., `America/Los_Angeles`)

#### Interface Naming
- **Cisco:** `GigabitEthernet0/1`, `Ethernet1/1`
- **Juniper:** `ge-0/0/0`, `xe-0/0/0`

---

## Template Testing

### Unit Testing
Test each template with valid variables:
```python
def test_cisco_ios_ntp_template():
    template = env.get_template('cisco_ios_ntp.j2')
    config = template.render(
        ntp_servers=["10.1.1.1"],
        timezone="PST8PDT,M3.2.0,M11.1.0",
        source_interface="GigabitEthernet0/0"
    )
    assert "ntp server 10.1.1.1" in config
    assert "clock timezone" in config
```

### Integration Testing
Test template integration with config_templates plugin:
```python
def test_config_templates_plugin():
    plugin = load_plugin('config_templates')
    result = plugin.run(device, credentials, params, config, log_func)
    assert result['status'] == 'success'
```

---

## Template Maintenance

### Adding New Templates
1. Create new .j2 file in templates/ directory
2. Document template in this file
3. Add template to config_templates plugin
4. Test template with valid variables
5. Update CHANGELOG.md

### Updating Existing Templates
1. Update template file
2. Update documentation in this file
3. Test updated template
4. Update CHANGELOG.md

### Deprecating Templates
1. Mark template as deprecated in documentation
2. Add deprecation notice in template comments
3. Update CHANGELOG.md
4. Remove from config_templates plugin (if applicable)

---

## Troubleshooting

### Common Issues

#### Template Rendering Error
**Symptom:** Jinja2 template rendering fails  
**Solution:** Check variable names match template, check variable types

#### Invalid Configuration Generated
**Symptom:** Generated configuration is invalid for platform  
**Solution:** Check platform-specific syntax, validate variables

#### Missing Variable Error
**Symptom:** Template rendering fails due to missing variable  
**Solution:** Provide all required variables, use default values in template

---

## Best Practices

### Template Design
- Use clear variable names
- Add comments for complex logic
- Use conditional blocks for optional features
- Use loops for repeated elements
- Validate variable types

### Variable Naming
- Use descriptive names
- Use snake_case for variable names
- Use consistent naming across templates
- Document variable types and constraints

### Platform Compatibility
- Test templates on actual devices
- Validate platform-specific syntax
- Document platform differences
- Handle edge cases

---

## References

- Jinja2 Documentation: https://jinja.palletsprojects.com/
- Cisco IOS Configuration Guide: https://www.cisco.com/c/en/us/support/docs/ip/routing-information-protocol-rip/
- Cisco NX-OS Configuration Guide: https://www.cisco.com/c/en/us/support/docs/nexus-9000-series-switches/
- Juniper JunOS Configuration Guide: https://www.juniper.net/documentation/
