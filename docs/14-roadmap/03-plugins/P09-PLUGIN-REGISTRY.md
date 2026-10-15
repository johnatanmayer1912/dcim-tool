# P09: Plugin Registry

| Field | Value |
|-------|-------|
| **Prompt ID** | P09 |
| **Phase** | 03-plugins |
| **Dependency Level** | 2 (Depends on Phase 2) |
| **Estimated Time** | 15 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct the plugin registry for plugin management. This module handles plugin discovery, loading, and execution.

---

## Prerequisites

- Phase 2 (Core Modules) completed
- network_base module functional
- adapters module functional
- connectivity module functional

---

## Instructions

### Step 1: Create plugin_registry Module Structure

```bash
cd modules
```

---

### Step 2: Create plugin_registry.py

```python
"""
Plugin Registry

Plugin discovery, loading, and execution management.
"""

import importlib
import inspect
import os
from typing import Dict, List, Any

class PluginRegistry:
    """Registry for managing plugins"""
    
    def __init__(self):
        self.plugins: Dict[str, Any] = {}
        self.plugin_metadata: Dict[str, Dict] = {}
        self.plugin_directory = 'modules/plugins'
    
    def discover_plugins(self):
        """
        Discover all plugins in the plugin directory
        
        Returns:
            int: Number of plugins discovered
        """
        plugin_count = 0
        
        # Get all plugin directories
        if not os.path.exists(self.plugin_directory):
            os.makedirs(self.plugin_directory)
            return 0
        
        for plugin_name in os.listdir(self.plugin_directory):
            plugin_path = os.path.join(self.plugin_directory, plugin_name)
            
            # Skip if not a directory
            if not os.path.isdir(plugin_path):
                continue
            
            # Skip if no __init__.py
            if not os.path.exists(os.path.join(plugin_path, '__init__.py')):
                continue
            
            # Load plugin
            try:
                module = importlib.import_module(f'modules.plugins.{plugin_name}')
                
                # Check for METADATA
                if hasattr(module, 'METADATA'):
                    metadata = module.METADATA
                    plugin_id = metadata.get('plugin_id', plugin_name)
                    
                    self.plugins[plugin_id] = module
                    self.plugin_metadata[plugin_id] = metadata
                    plugin_count += 1
                    
            except Exception as e:
                print(f"Error loading plugin {plugin_name}: {e}")
        
        return plugin_count
    
    def get_plugin(self, plugin_id: str):
        """
        Get plugin by ID
        
        Args:
            plugin_id: Plugin identifier
        
        Returns:
            Plugin module or None
        """
        return self.plugins.get(plugin_id)
    
    def get_plugin_metadata(self, plugin_id: str) -> Dict:
        """
        Get plugin metadata
        
        Args:
            plugin_id: Plugin identifier
        
        Returns:
            Plugin metadata dictionary
        """
        return self.plugin_metadata.get(plugin_id, {})
    
    def execute_plugin(self, plugin_id: str, device: Dict, credentials: Dict, params: Dict, log_func):
        """
        Execute plugin
        
        Args:
            plugin_id: Plugin identifier
            device: Device dictionary
            credentials: Credentials dictionary
            params: Plugin parameters
            log_func: Logging function
        
        Returns:
            dict: Plugin execution result
        """
        plugin = self.get_plugin(plugin_id)
        
        if not plugin:
            return {
                'status': 'error',
                'error': f'Plugin {plugin_id} not found'
            }
        
        try:
            # Check for run function
            if hasattr(plugin, 'run'):
                result = plugin.run(device, credentials, params, log_func)
                return result
            else:
                return {
                    'status': 'error',
                    'error': f'Plugin {plugin_id} has no run function'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Plugin execution error: {e}'
            }
    
    def list_plugins(self) -> List[Dict]:
        """
        List all plugins with metadata
        
        Returns:
            List of plugin dictionaries
        """
        plugin_list = []
        
        for plugin_id, metadata in self.plugin_metadata.items():
            plugin_info = {
                'plugin_id': plugin_id,
                'display_name': metadata.get('display_name', plugin_id),
                'version': metadata.get('version', '1.0.0'),
                'category': metadata.get('category', 'general'),
                'description': metadata.get('description', '')
            }
            plugin_list.append(plugin_info)
        
        return plugin_list
    
    def reload_plugins(self):
        """
        Reload all plugins
        
        Returns:
            int: Number of plugins reloaded
        """
        self.plugins.clear()
        self.plugin_metadata.clear()
        return self.discover_plugins()
```

---

### Step 3: Validate Module

```python
# Test plugin registry
from modules.plugin_registry import PluginRegistry

# Create registry
registry = PluginRegistry()

# Discover plugins
plugin_count = registry.discover_plugins()
print(f"Discovered {plugin_count} plugins")

# List plugins
plugins = registry.list_plugins()
print(f"Available plugins: {len(plugins)}")

print("Plugin registry validation successful")
```

---

## Validation Checklist

- [ ] plugin_registry.py created
- [ ] PluginRegistry class implemented
- [ ] discover_plugins implemented
- [ ] get_plugin implemented
- [ ] get_plugin_metadata implemented
- [ ] execute_plugin implemented
- [ ] list_plugins implemented
- [ ] reload_plugins implemented
- [ ] Module validation successful
- [ ] Ready for plugin templates reconstruction

---

## Troubleshooting

### Issue: Plugin discovery fails

**Solution:**
- Verify plugin directory exists
- Check plugin __init__.py files
- Verify METADATA in plugins

### Issue: Plugin execution fails

**Solution:**
- Check plugin run function
- Verify plugin dependencies
- Check plugin parameters

---

## Next Steps

After completing this prompt, proceed to P10: Plugin Templates

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- MODULE_ARCHITECTURE.md: ../../01-architecture/MODULE_ARCHITECTURE.md
- plugins/: ../../plugins/
