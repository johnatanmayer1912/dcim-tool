# Plugin Prompt: vlan_audit

## Purpose

Create a plugin that audits VLAN configurations on network devices. This plugin replaces the legacy vlan_audit.py module with a v6.0 plugin-compatible version.

## Requirements

### Functional Requirements
1. Support Cisco IOS 12.x+
2. Support Cisco NXOS 7.x+
3. Support Juniper JunOS 12.x+
4. Retrieve VLAN database from devices
5. Report VLAN ID, name, and status
6. Configurable display limits

### Parameters Required

| Parameter | Type | Description | Validation |
|-----------|------|-------------|------------|
| include_details | checkbox | Include VLAN names | Default: True |
| max_vlans | integer | Max VLANs to show | Range: 1-1000, Default: 50 |

### Command Strategy

**Cisco IOS/NXOS:**
- Primary: `show vlan brief`
- Fallback: `show vlan`

**Juniper JunOS:**
- Primary: `show vlans`

### Return Data Structure
```json
{
  "status": "success",
  "data": {
    "true_host": "hostname",
    "vlan_count": 25,
    "vlans": [
      {"id": 1, "name": "default", "status": "active"}
    ]
  }
}
```

## Version History Prompts

### v1.0.0 Creation Prompt
```
Create vlan_audit_plugin.py that:
1. Replaces legacy vlan_audit.py
2. Implements v6.0 plugin contract
3. Supports IOS, NXOS, JunOS
4. Parameters: include_details (bool), max_vlans (int)
5. Returns parsed VLAN data
```

## Creation Checklist

- [x] Plugin file created
- [x] METADATA with required fields
- [x] run() function implemented
- [x] Multi-platform commands added
- [x] Error handling implemented
- [ ] Testing completed
- [ ] Documentation completed
- [ ] QA sign-off obtained

---

**Status:** Created - Awaiting Testing
