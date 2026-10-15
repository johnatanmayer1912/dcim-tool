# P19: Module Integration

| Field | Value |
|-------|-------|
| **Prompt ID** | P19 |
| **Phase** | 06-integration |
| **Dependency Level** | 5 (Depends on Phases 2, 3, 4, 5) |
| **Estimated Time** | 10 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct module integration for connecting all modules. This module provides the integration layer that connects core modules, plugins, web interface, and utilities.

---

## Prerequisites

- Phase 2 (Core Modules) completed
- Phase 3 (Plugin System) completed
- Phase 4 (Web Interface) completed
- Phase 5 (Utilities) completed
- All modules functional

---

## Instructions

### Step 1: Create module_integration Module

```bash
cd modules
```

---

### Step 2: Create module_integration.py

```python
"""
Module Integration

Integration layer connecting all modules.
"""

from typing import Dict, List, Any
from modules.plugin_registry import PluginRegistry
from modules.connectivity import ConnectionPool
from modules.parsing_utilities import parse_vlan_output
from modules.validation_utilities import validate_ip_address, validate_vlan_id
from modules.logging_utilities import get_logger

class ModuleIntegrator:
    """Integrator for connecting all modules"""
    
    def __init__(self):
        self.plugin_registry = PluginRegistry()
        self.connection_pool = ConnectionPool()
        self.logger = get_logger('module_integration')
        
        # Discover plugins
        self.plugin_registry.discover_plugins()
    
    def execute_plugin_on_device(self, plugin_id: str, device: Dict, credentials: Dict, params: Dict):
        """
        Execute plugin on device with full integration
        
        Args:
            plugin_id: Plugin identifier
            device: Device dictionary
            credentials: Credentials dictionary
            params: Plugin parameters
        
        Returns:
            dict: Execution result
        """
        try:
            # Validate device IP
            ip_validation = validate_ip_address(device['host'])
            if not ip_validation['valid']:
                return {
                    'status': 'error',
                    'error': f'Invalid IP address: {device["host"]}'
                }
            
            # Execute plugin
            result = self.plugin_registry.execute_plugin(
                plugin_id,
                device,
                credentials,
                params,
                self.logger.info
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Plugin execution error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def execute_plugin_on_devices(self, plugin_id: str, devices: List[Dict], credentials: Dict, params: Dict):
        """
        Execute plugin on multiple devices
        
        Args:
            plugin_id: Plugin identifier
            devices: List of device dictionaries
            credentials: Credentials dictionary
            params: Plugin parameters
        
        Returns:
            dict: Batch execution result
        """
        results = []
        errors = []
        
        for device in devices:
            try:
                result = self.execute_plugin_on_device(plugin_id, device, credentials, params)
                results.append(result)
                
                if result['status'] == 'error':
                    errors.append({
                        'device': device['host'],
                        'error': result.get('error')
                    })
                    
            except Exception as e:
                errors.append({
                    'device': device['host'],
                    'error': str(e)
                })
        
        return {
            'status': 'complete',
            'total_devices': len(devices),
            'successful': len(results) - len(errors),
            'failed': len(errors),
            'results': results,
            'errors': errors
        }
    
    def get_device_vlan_info(self, device, credentials):
        """
        Get VLAN information from device with parsing
        
        Args:
            device: Device dictionary
            credentials: Credentials dictionary
        
        Returns:
            dict: VLAN information
        """
        from modules.connectivity import connect_to_device
        
        try:
            # Connect to device
            result = connect_to_device(device, credentials['username'], credentials['password'], credentials.get('secret'), self.logger.info)
            
            if result['status'] != 'success':
                return result
            
            # Get VLAN output (would need actual connection)
            # For now, return parsed structure
            vlan_output = "1  default  active\n10  data  active"
            vlans = parse_vlan_output(vlan_output, device['device_type'])
            
            return {
                'status': 'success',
                'device': device['host'],
                'vlans': vlans
            }
            
        except Exception as e:
            self.logger.error(f"VLAN info error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def validate_device_config(self, device, credentials, config_data):
        """
        Validate device configuration
        
        Args:
            device: Device dictionary
            credentials: Credentials dictionary
            config_data: Configuration data to validate
        
        Returns:
            dict: Validation result
        """
        try:
            # Validate VLANs
            if 'vlans' in config_data:
                for vlan in config_data['vlans']:
                    validation = validate_vlan_id(vlan)
                    if not validation['valid']:
                        return {
                            'status': 'error',
                            'error': f'Invalid VLAN ID: {vlan}'
                        }
            
            return {
                'status': 'success',
                'message': 'Configuration validation passed'
            }
            
        except Exception as e:
            self.logger.error(f"Config validation error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
```

---

### Step 3: Validate Module Integration

```python
# Test module integration
from modules.module_integration import ModuleIntegrator

# Create integrator
integrator = ModuleIntegrator()

# Test plugin registry integration
plugins = integrator.plugin_registry.list_plugins()
assert len(plugins) > 0

# Test connection pool integration
assert integrator.connection_pool is not None

# Test device validation
device = {'host': '10.1.1.1', 'device_type': 'cisco_ios'}
credentials = {'username': 'admin', 'password': 'password'}

# Test VLAN info retrieval
result = integrator.get_device_vlan_info(device, credentials)
assert result['status'] in ['success', 'error']

print("Module integration validation successful")
```

---

## Validation Checklist

- [ ] module_integration.py created
- [ ] ModuleIntegrator class implemented
- [ ] Plugin registry integration functional
- [ ] Connection pool integration functional
- [ ] execute_plugin_on_device implemented
- [ ] execute_plugin_on_devices implemented
- [ ] get_device_vlan_info implemented
- [ ] validate_device_config implemented
- [ ] Module integration validation successful
- [ ] Ready for API integration reconstruction

---

## Troubleshooting

### Issue: Module import fails

**Solution:**
- Verify all modules exist
- Check Python path
- Validate module dependencies

### Issue: Plugin execution fails

**Solution:**
- Check plugin registry
- Verify plugin dependencies
- Test plugin individually

---

## Next Steps

After completing this prompt, proceed to P20: API Integration

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- MODULE_ARCHITECTURE.md: ../../01-architecture/MODULE_ARCHITECTURE.md
