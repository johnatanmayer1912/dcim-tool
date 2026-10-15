# Developer Guide: Visual Interface Management System

## Extending the Platform
Developers can extend the parsing and validation engines in two main areas:

### 1. Adding Command Support
To support additional vendor platforms, edit the `VENDOR_COMMANDS` dictionary at the top of `modules/plugins/interface_manager.py`.

```python
VENDOR_COMMANDS = {
    "arista_eos": {
        "interfaces": "show interfaces",
        "config": "show running-config interface {interface}",
        "port_channel": "show port-channel",
        "vlan": "show vlan"
    }
}
```

### 2. Custom Syntax Validation Rules
Add regex validation patterns inside the `_validate_vendor_syntax` method in `interface_manager.py` within the `vendor_patterns` mapping definition.
