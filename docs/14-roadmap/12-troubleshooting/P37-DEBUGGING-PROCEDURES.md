# P37: Debugging Procedures

| Field | Value |
|-------|-------|
| **Prompt ID** | P37 |
| **Phase** | 12-troubleshooting |
| **Dependency Level** | 10 (Depends on Phases 1-8) |
| **Estimated Time** | 10 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct debugging procedures for troubleshooting. This provides debugging procedures and diagnostic tools for the reconstructed application.

---

## Prerequisites

- Phases 1-8 completed
- Application built and deployed
- Python environment set up

---

## Instructions

### Step 1: Create debugging_procedures.py

```python
"""
Debugging Procedures

Debugging and diagnostic procedures for the reconstructed application.
"""

import sys
import traceback
from modules.logging_utilities import get_logger

class DebuggingProcedures:
    """Procedures for debugging and diagnostics"""
    
    def __init__(self):
        self.logger = get_logger('debugging')
    
    def enable_debug_logging(self):
        """Enable debug-level logging"""
        try:
            from modules.logging_utilities import setup_logging
            logger = setup_logging(log_level='DEBUG')
            self.logger.info("Debug logging enabled")
            return True
        except Exception as e:
            self.logger.error(f"Failed to enable debug logging: {e}")
            return False
    
    def get_system_info(self):
        """Get system information for diagnostics"""
        try:
            import platform
            import psutil
            
            info = {
                'platform': platform.system(),
                'platform_version': platform.version(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available
            }
            
            self.logger.info(f"System info: {info}")
            return info
        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return None
    
    def get_application_status(self):
        """Get application status"""
        try:
            from vlan_checker_web import app
            from modules.plugin_registry import PluginRegistry
            
            registry = PluginRegistry()
            plugin_count = len(registry.list_plugins())
            
            status = {
                'app_status': 'running',
                'plugin_count': plugin_count,
                'flask_config': dict(app.config)
            }
            
            self.logger.info(f"Application status: {status}")
            return status
        except Exception as e:
            self.logger.error(f"Failed to get application status: {e}")
            return None
    
    def diagnose_connection_issues(self, device):
        """Diagnose connection issues for a device"""
        try:
            from modules.validation_utilities import validate_ip_address
            
            ip_validation = validate_ip_address(device['host'])
            
            diagnosis = {
                'device': device['host'],
                'ip_valid': ip_validation['valid'],
                'device_type': device.get('device_type'),
                'recommendation': 'Check network connectivity and credentials' if not ip_validation['valid'] else 'Proceed with connection'
            }
            
            self.logger.info(f"Connection diagnosis: {diagnosis}")
            return diagnosis
        except Exception as e:
            self.logger.error(f"Failed to diagnose connection issues: {e}")
            return None
    
    def generate_debug_report(self):
        """Generate comprehensive debug report"""
        try:
            report = {
                'system_info': self.get_system_info(),
                'application_status': self.get_application_status(),
                'timestamp': str(datetime.datetime.now())
            }
            
            self.logger.info("Debug report generated")
            return report
        except Exception as e:
            self.logger.error(f"Failed to generate debug report: {e}")
            return None

if __name__ == '__main__':
    import datetime
    debugger = DebuggingProcedures()
    
    # Enable debug logging
    debugger.enable_debug_logging()
    
    # Get system info
    system_info = debugger.get_system_info()
    print(f"System Info: {system_info}")
    
    # Get application status
    app_status = debugger.get_application_status()
    print(f"Application Status: {app_status}")
    
    # Generate debug report
    report = debugger.generate_debug_report()
    print(f"Debug Report: {report}")
```

---

### Step 2: Validate Debugging Procedures

```bash
# Run debugging procedures
python debugging_procedures.py
```

---

## Validation Checklist

- [ ] debugging_procedures.py created
- [ ] Debug logging implemented
- [ ] System info retrieval implemented
- [ ] Application status retrieval implemented
- [ ] Connection diagnosis implemented
- [ ] Debug report generation implemented
- [ ] All debugging procedures functional
- [ ] Ready for troubleshooting scenarios reconstruction

---

## Troubleshooting

### Issue: Debugging procedures fail

**Solution:**
- Check module imports
- Verify logging configuration
- Test individual procedures

---

## Next Steps

After completing this prompt, proceed to P38: Troubleshooting Scenarios

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- ADVANCED_DEBUGGING_GUIDE.md: ../../02-codebase/ADVANCED_DEBUGGING_GUIDE.md
