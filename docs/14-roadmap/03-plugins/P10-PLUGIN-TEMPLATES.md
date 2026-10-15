# P10: Plugin Templates

| Field | Value |
|-------|-------|
| **Prompt ID** | P10 |
| **Phase** | 03-plugins |
| **Dependency Level** | 3 (Depends on P09) |
| **Estimated Time** | 15 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct plugin templates for plugin development. This provides the base template structure for creating new plugins.

---

## Prerequisites

- P09: Plugin Registry completed
- plugin_registry module functional
- Plugin directory structure created

---

## Instructions

### Step 1: Create base_template Plugin Structure

```bash
cd modules/plugins/base_template
```

---

### Step 2: Create __init__.py

```python
"""
Base Plugin Template

Template for creating new plugins.
"""

METADATA = {
    'plugin_id': 'base_template',
    'display_name': 'Base Plugin Template',
    'version': '1.0.0',
    'category': 'template',
    'description': 'Base template for plugin development',
    'author': 'Network Swiss Tool Pro',
    'dependencies': [],
    'supported_platforms': ['cisco_ios', 'cisco_nxos', 'juniper_junos']
}

def run(device, credentials, params, log_func):
    """
    Run plugin
    
    Args:
        device: Device dictionary
        credentials: Credentials dictionary
        params: Plugin parameters
        log_func: Logging function
    
    Returns:
        dict: Plugin execution result
    """
    try:
        log_func(f"Running base_template plugin on {device['host']}")
        
        # Plugin logic goes here
        result = {
            'status': 'success',
            'data': {},
            'message': 'Plugin executed successfully'
        }
        
        return result
        
    except Exception as e:
        log_func(f"Error in base_template plugin: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
```

---

### Step 3: Create config_templates Plugin Structure

```bash
cd modules/plugins/config_templates
```

---

### Step 4: Create __init__.py

```python
"""
Config Templates Plugin

Plugin for configuration template management.
"""

METADATA = {
    'plugin_id': 'config_templates',
    'display_name': 'Configuration Templates',
    'version': '1.0.0',
    'category': 'configuration',
    'description': 'Manage configuration templates',
    'author': 'Network Swiss Tool Pro',
    'dependencies': [],
    'supported_platforms': ['cisco_ios', 'cisco_nxos', 'juniper_junos']
}

def run(device, credentials, params, log_func):
    """
    Run plugin
    
    Args:
        device: Device dictionary
        credentials: Credentials dictionary
        params: Plugin parameters
        log_func: Logging function
    
    Returns:
        dict: Plugin execution result
    """
    try:
        log_func(f"Running config_templates plugin on {device['host']}")
        
        # Plugin logic for configuration templates
        result = {
            'status': 'success',
            'data': {'templates': []},
            'message': 'Configuration templates retrieved'
        }
        
        return result
        
    except Exception as e:
        log_func(f"Error in config_templates plugin: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
```

---

### Step 5: Validate Plugin Templates

```python
# Test plugin template import
from modules.plugins.base_template import METADATA as base_metadata
from modules.plugins.config_templates import METADATA as config_metadata

# Validate metadata
assert base_metadata['plugin_id'] == 'base_template'
assert config_metadata['plugin_id'] == 'config_templates'

# Validate run function exists
from modules.plugins.base_template import run as base_run
from modules.plugins.config_templates import run as config_run

assert callable(base_run)
assert callable(config_run)

print("Plugin templates validation successful")
```

---

## Validation Checklist

- [ ] base_template plugin structure created
- [ ] base_template __init__.py created
- [ ] base_template METADATA defined
- [ ] base_template run function implemented
- [ ] config_templates plugin structure created
- [ ] config_templates __init__.py created
- [ ] config_templates METADATA defined
- [ ] config_templates run function implemented
- [ ] Plugin templates validation successful
- [ ] Ready for plugin implementations reconstruction

---

## Troubleshooting

### Issue: Plugin template import fails

**Solution:**
- Verify plugin directory structure
- Check __init__.py exists
- Verify Python path

### Issue: METADATA validation fails

**Solution:**
- Check METADATA structure
- Verify required fields
- Validate data types

---

## Next Steps

After completing this prompt, proceed to P11: Plugin Implementations

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- MODULE_ARCHITECTURE.md: ../../01-architecture/MODULE_ARCHITECTURE.md
- plugins/base_template/: ../../plugins/base_template/
- plugins/config_templates/: ../../plugins/config_templates/
