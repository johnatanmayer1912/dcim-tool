# P03: Project Structure

| Field | Value |
|-------|-------|
| **Prompt ID** | P03 |
| **Phase** | 01-foundation |
| **Dependency Level** | 2 (Depends on P01, P02) |
| **Estimated Time** | 10 minutes |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

Create the complete project directory structure for Network Swiss Tool Pro. This includes all source code directories, configuration directories, and documentation directories.

---

## Prerequisites

- P01: Environment Setup completed
- P02: Dependency Installation completed
- Virtual environment activated

---

## Instructions

### Step 1: Create Root-Level Directories

```bash
# Source code directories
mkdir modules
mkdir templates
mkdir static

# Configuration directories
mkdir policies
mkdir logs

# Documentation directories
mkdir docs
mkdir docs/00-overview
mkdir docs/01-architecture
mkdir docs/02-codebase
mkdir docs/03-infrastructure
mkdir docs/04-automation
mkdir docs/05-plugins
mkdir docs/06-ui-ux
mkdir docs/07-security
mkdir docs/08-operations
mkdir docs/09-qa
mkdir docs/10-rebuild
mkdir docs/11-release-management
mkdir docs/12-reference
mkdir docs/13-master-prompts
mkdir docs/14-bug-reports
mkdir docs/15-rebuild-roadmap
mkdir docs/plugins
mkdir docs/ui-mockups

# Plugin directories
mkdir modules/plugins
mkdir modules/plugins/base_template
mkdir modules/plugins/config_templates
mkdir modules/plugins/critical_logs_plugin
mkdir modules/plugins/device_time_plugin
mkdir modules/plugins/environment_status_plugin
mkdir modules/plugins/interface_errors_plugin
mkdir modules/plugins/network_discovery
mkdir modules/plugins/serial_number_plugin
mkdir modules/plugins/standards_validator
mkdir modules/plugins/stp_topology_visualizer
mkdir modules/plugins/unused_trunk_pruner
mkdir modules/plugins/vlan_audit_plugin
mkdir modules/plugins/vpc_domain

# Template directories
mkdir templates
mkdir static/css
mkdir static/js
mkdir static/images

# Log directories
mkdir logs
mkdir logs/jobs
mkdir logs/plugins
mkdir logs/errors
```

---

### Step 2: Create Module Subdirectories

```bash
# Core modules
mkdir modules/adapters
mkdir modules/network_base
mkdir modules/topology_mapper
mkdir modules/node_analyze
mkdir modules/node_interface_topology
mkdir modules/stp_swiss_runner
mkdir modules/mac_trace
mkdir modules/description_search
mkdir modules/config_backup
mkdir modules/network_audit
mkdir modules/vlan_compare
mkdir modules/save_config
mkdir modules/vlan_mgmt_production
mkdir modules/cli_manager
```

---

### Step 3: Create Documentation Subdirectories

```bash
# Master prompts subdirectories
mkdir docs/13-master-prompts/action-logs
mkdir docs/13-master-prompts/archive
mkdir docs/13-master-prompts/bugs
mkdir docs/13-master-prompts/roles
mkdir docs/13-master-prompts/roles/combined

# Rebuild roadmap subdirectories
mkdir docs/15-rebuild-roadmap/01-foundation
mkdir docs/15-rebuild-roadmap/02-core-modules
mkdir docs/15-rebuild-roadmap/03-plugins
mkdir docs/15-rebuild-roadmap/04-web-interface
mkdir docs/15-rebuild-roadmap/05-utilities
mkdir docs/15-rebuild-roadmap/06-integration
mkdir docs/15-rebuild-roadmap/07-testing
mkdir docs/15-rebuild-roadmap/08-deployment
mkdir docs/15-rebuild-roadmap/09-validation
mkdir docs/15-rebuild-roadmap/10-documentation
mkdir docs/15-rebuild-roadmap/11-optimization
mkdir docs/15-rebuild-roadmap/12-troubleshooting
mkdir docs/15-rebuild-roadmap/13-finalization
```

---

### Step 4: Create __init__.py Files

```bash
# Create __init__.py for all Python packages
touch modules/__init__.py
touch modules/plugins/__init__.py
touch modules/adapters/__init__.py
touch modules/network_base/__init__.py
touch modules/topology_mapper/__init__.py
touch modules/node_analyze/__init__.py
touch modules/node_interface_topology/__init__.py
touch modules/stp_swiss_runner/__init__.py
touch modules/mac_trace/__init__.py
touch modules/description_search/__init__.py
touch modules/config_backup/__init__.py
touch modules/network_audit/__init__.py
touch modules/vlan_compare/__init__.py
touch modules/save_config/__init__.py
touch modules/vlan_mgmt_production/__init__.py
touch modules/cli_manager/__init__.py
```

---

### Step 5: Verify Structure

```bash
# Verify directory structure
tree -L 3 -d
```

**Expected Structure:**
```
Net_mngmnt_tool/
├── modules/
│   ├── __init__.py
│   ├── plugins/
│   ├── adapters/
│   ├── network_base/
│   ├── topology_mapper/
│   ├── node_analyze/
│   ├── node_interface_topology/
│   ├── stp_swiss_runner/
│   ├── mac_trace/
│   ├── description_search/
│   ├── config_backup/
│   ├── network_audit/
│   ├── vlan_compare/
│   ├── save_config/
│   ├── vlan_mgmt_production/
│   └── cli_manager/
├── templates/
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── policies/
├── logs/
│   ├── jobs/
│   ├── plugins/
│   └── errors/
├── docs/
│   ├── 00-overview/
│   ├── 01-architecture/
│   ├── 02-codebase/
│   ├── 03-infrastructure/
│   ├── 04-automation/
│   ├── 05-plugins/
│   ├── 06-ui-ux/
│   ├── 07-security/
│   ├── 08-operations/
│   ├── 09-qa/
│   ├── 10-rebuild/
│   ├── 11-release-management/
│   ├── 12-reference/
│   ├── 13-master-prompts/
│   ├── 14-bug-reports/
│   ├── 15-rebuild-roadmap/
│   ├── plugins/
│   └── ui-mockups/
└── venv/
```

---

## Validation Checklist

- [ ] All root-level directories created
- [ ] All module subdirectories created
- [ ] All documentation subdirectories created
- [ ] All __init__.py files created
- [ ] Directory structure verified
- [ ] Structure matches expected layout
- [ ] Ready for initial configuration

---

## Troubleshooting

### Issue: Directory creation fails

**Solution:**
- Check write permissions
- Check disk space
- Verify parent directories exist

### Issue: __init__.py creation fails

**Solution:**
- Use: `touch __init__.py` (Linux/macOS)
- Use: `type nul > __init__.py` (Windows)
- Verify Python package structure

---

## Next Steps

After completing this prompt, proceed to P04: Initial Configuration

---

## References

- PROJECT_STRUCTURE.md: ../../02-codebase/repository-structure.md
- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
