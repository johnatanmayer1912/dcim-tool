# P27: Deployment

| Field | Value |
|-------|-------|
| **Prompt ID** | P27 |
| **Phase** | 08-deployment |
| **Dependency Level** | 9 (Depends on P26) |
| **Estimated Time** | 10 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Reconstruct deployment procedures for production. This provides the deployment configuration and procedures for production environments.

---

## Prerequisites

- P26: Packaging completed
- Distribution package created
- Python environment set up

---

## Instructions

### Step 1: Create deploy.py

```python
"""
Deployment Script

Deploy application to production environment.
"""

import os
import shutil
import subprocess
from datetime import datetime

def deploy_to_production(target_dir):
    """
    Deploy to production directory
    
    Args:
        target_dir: Target deployment directory
    """
    version = "7.0.10"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create backup of current deployment
    if os.path.exists(target_dir):
        backup_dir = f"{target_dir}_backup_{timestamp}"
        print(f"Creating backup: {backup_dir}")
        shutil.copytree(target_dir, backup_dir)
    
    # Create deployment directory
    os.makedirs(target_dir, exist_ok=True)
    
    # Copy executable
    print("Copying executable...")
    shutil.copy("dist/NetworkSwissToolPro.exe", f"{target_dir}/NetworkSwissToolPro.exe")
    
    # Copy documentation
    print("Copying documentation...")
    if os.path.exists(f"{target_dir}/docs"):
        shutil.rmtree(f"{target_dir}/docs")
    shutil.copytree("docs", f"{target_dir}/docs")
    
    # Copy configuration files
    print("Copying configuration files...")
    shutil.copy("config.yaml", f"{target_dir}/config.yaml")
    shutil.copy("config_logging.yaml", f"{target_dir}/config_logging.yaml")
    
    # Create logs directory
    os.makedirs(f"{target_dir}/logs", exist_ok=True)
    os.makedirs(f"{target_dir}/logs/jobs", exist_ok=True)
    os.makedirs(f"{target_dir}/logs/plugins", exist_ok=True)
    os.makedirs(f"{target_dir}/logs/errors", exist_ok=True)
    
    # Create deployment marker
    with open(f"{target_dir}/DEPLOYMENT_INFO.txt", "w") as f:
        f.write(f"Version: {version}\n")
        f.write(f"Deployed: {datetime.now().isoformat()}\n")
        f.write(f"Deployment ID: {timestamp}\n")
    
    print(f"Deployment complete: {target_dir}")
    return True

def rollback_deployment(target_dir):
    """
    Rollback to previous deployment
    
    Args:
        target_dir: Target deployment directory
    """
    # Find most recent backup
    backups = sorted([d for d in os.listdir(os.path.dirname(target_dir)) 
                     if d.startswith(os.path.basename(target_dir) + "_backup")])
    
    if backups:
        latest_backup = os.path.join(os.path.dirname(target_dir), backups[-1])
        print(f"Rolling back to: {latest_backup}")
        
        # Remove current deployment
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        
        # Restore from backup
        shutil.copytree(latest_backup, target_dir)
        print("Rollback complete")
        return True
    else:
        print("No backup found for rollback")
        return False

def verify_deployment(target_dir):
    """
    Verify deployment
    
    Args:
        target_dir: Target deployment directory
    """
    required_files = [
        "NetworkSwissToolPro.exe",
        "config.yaml",
        "config_logging.yaml",
        "DEPLOYMENT_INFO.txt"
    ]
    
    required_dirs = [
        "docs",
        "logs",
        "logs/jobs",
        "logs/plugins",
        "logs/errors"
    ]
    
    print("Verifying deployment...")
    
    # Check files
    for file in required_files:
        file_path = os.path.join(target_dir, file)
        if os.path.exists(file_path):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} - MISSING")
            return False
    
    # Check directories
    for dir in required_dirs:
        dir_path = os.path.join(target_dir, dir)
        if os.path.exists(dir_path):
            print(f"  ✓ {dir}/")
        else:
            print(f"  ✗ {dir}/ - MISSING")
            return False
    
    print("Deployment verification passed")
    return True

if __name__ == '__main__':
    import sys
    
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "C:\\Program Files\\NetworkSwissToolPro"
    
    if sys.argv[2] == 'rollback' if len(sys.argv) > 2 else False:
        success = rollback_deployment(target_dir)
    else:
        success = deploy_to_production(target_dir)
        if success:
            verify_deployment(target_dir)
    
    sys.exit(0 if success else 1)
```

---

### Step 2: Create production_config.yaml

```bash
cat > production_config.yaml << 'EOF'
# Production Configuration

app:
  name: Network Swiss Tool Pro
  version: 7.0.10
  debug: false

server:
  host: 0.0.0.0
  port: 5000
  workers: 4

logging:
  level: WARNING
  file: logs/application.log
  max_bytes: 52428800
  backup_count: 10

plugins:
  directory: modules/plugins
  enabled:
    - network_discovery
    - standards_validator
    - stp_topology_visualizer
    - vpc_domain
    - vlan_audit_plugin
    - unused_trunk_pruner
    - critical_logs_plugin
    - device_time_plugin
    - environment_status_plugin
    - interface_errors_plugin
    - serial_number_plugin
    - config_templates
EOF
```

---

### Step 3: Validate Deployment

```bash
# Test deployment to test directory
python deploy.py "C:\\test_deployment"

# Verify deployment
python deploy.py "C:\\test_deployment" verify

# Test rollback
python deploy.py "C:\\test_deployment" rollback
```

---

## Validation Checklist

- [ ] deploy.py created
- [ ] Deployment procedures functional
- [ ] Backup procedures functional
- [ ] Rollback procedures functional
- [ ] Verification procedures functional
- [ ] production_config.yaml created
- [ ] Deployment validation successful
- [ ] Deployment phase complete
- [ ] Ready for validation reconstruction

---

## Troubleshooting

### Issue: Deployment fails

**Solution:**
- Check target directory permissions
- Verify disk space
- Validate file paths

### Issue: Rollback fails

**Solution:**
- Verify backup exists
- Check backup integrity
- Test backup restoration

---

## Next Steps

After completing this prompt, Phase 8 (Deployment) is complete. Proceed to Phase 9: Validation (can run in parallel with Phases 10-11)

---

## References

- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- BUILD_PROCESS.md: ../../10-rebuild/BUILD_PROCESS.md
