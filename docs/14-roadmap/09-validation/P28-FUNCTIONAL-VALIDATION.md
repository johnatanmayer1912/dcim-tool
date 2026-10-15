# P28: Functional Validation

| Field | Value |
|-------|-------|
| **Prompt ID** | P28 |
| **Phase** | 09-validation |
| **Dependency Level** | 8 (Depends on Phases 1-8) |
| **Estimated Time** | 10 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct functional validation procedures. This provides validation procedures to ensure all features work correctly after reconstruction.

---

## Prerequisites

- Phases 1-8 completed
- Application built and deployed
- Python environment set up

---

## Instructions

### Step 1: Create functional_validation.py

```python
"""
Functional Validation

Validate all features of the reconstructed application.
"""

from modules.module_integration import ModuleIntegrator
from modules.plugin_registry import PluginRegistry
from modules.database_integration import DatabaseManager
from flask import Flask
import sys

class FunctionalValidator:
    """Validator for functional testing"""
    
    def __init__(self):
        self.results = []
        self.errors = []
    
    def validate_plugin_registry(self):
        """Validate plugin registry"""
        try:
            registry = PluginRegistry()
            count = registry.discover_plugins()
            
            if count > 0:
                self.results.append("Plugin registry: PASS (discovered {} plugins)".format(count))
                return True
            else:
                self.errors.append("Plugin registry: FAIL (no plugins discovered)")
                return False
        except Exception as e:
            self.errors.append(f"Plugin registry: FAIL ({e})")
            return False
    
    def validate_module_integration(self):
        """Validate module integration"""
        try:
            integrator = ModuleIntegrator()
            
            if integrator.plugin_registry and integrator.connection_pool:
                self.results.append("Module integration: PASS")
                return True
            else:
                self.errors.append("Module integration: FAIL")
                return False
        except Exception as e:
            self.errors.append(f"Module integration: FAIL ({e})")
            return False
    
    def validate_database(self):
        """Validate database operations"""
        try:
            db = DatabaseManager('test_validation.db')
            device = {'host': '10.1.1.1', 'device_type': 'cisco_ios'}
            device_id = db.add_device(device)
            
            if device_id > 0:
                retrieved = db.get_device('10.1.1.1')
                if retrieved:
                    self.results.append("Database: PASS")
                    return True
            
            self.errors.append("Database: FAIL")
            return False
        except Exception as e:
            self.errors.append(f"Database: FAIL ({e})")
            return False
    
    def validate_flask_app(self):
        """Validate Flask application"""
        try:
            from vlan_checker_web import app
            
            with app.test_client() as client:
                response = client.get('/')
                if response.status_code == 200:
                    self.results.append("Flask app: PASS")
                    return True
            
            self.errors.append("Flask app: FAIL")
            return False
        except Exception as e:
            self.errors.append(f"Flask app: FAIL ({e})")
            return False
    
    def validate_api_endpoints(self):
        """Validate API endpoints"""
        try:
            from vlan_checker_web import app
            
            with app.test_client() as client:
                # Test plugins endpoint
                response = client.get('/api/plugins/list')
                if response.status_code == 200:
                    self.results.append("API endpoints: PASS")
                    return True
            
            self.errors.append("API endpoints: FAIL")
            return False
        except Exception as e:
            self.errors.append(f"API endpoints: FAIL ({e})")
            return False
    
    def run_all_validations(self):
        """Run all functional validations"""
        print("Running functional validations...")
        
        self.validate_plugin_registry()
        self.validate_module_integration()
        self.validate_database()
        self.validate_flask_app()
        self.validate_api_endpoints()
        
        return len(self.errors) == 0
    
    def print_results(self):
        """Print validation results"""
        print("\n=== Functional Validation Results ===")
        print("\nPassed:")
        for result in self.results:
            print(f"  ✓ {result}")
        
        print("\nFailed:")
        for error in self.errors:
            print(f"  ✗ {error}")
        
        print(f"\nTotal: {len(self.results)} passed, {len(self.errors)} failed")

if __name__ == '__main__':
    validator = FunctionalValidator()
    success = validator.run_all_validations()
    validator.print_results()
    sys.exit(0 if success else 1)
```

---

### Step 2: Validate Functional Validation

```bash
# Run functional validation
python functional_validation.py
```

---

## Validation Checklist

- [ ] functional_validation.py created
- [ ] Plugin registry validation implemented
- [ ] Module integration validation implemented
- [ ] Database validation implemented
- [ ] Flask app validation implemented
- [ ] API endpoints validation implemented
- [ ] All validations passing
- [ ] Ready for performance validation reconstruction

---

## Troubleshooting

### Issue: Validation fails

**Solution:**
- Check module imports
- Verify application built correctly
- Test individual components

---

## Next Steps

After completing this prompt, proceed to P29: Performance Validation

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- ADVANCED_TROUBLESHOOTING_SCENARIOS.md: ../../02-codebase/ADVANCED_TROUBLESHOOTING_SCENARIOS.md
