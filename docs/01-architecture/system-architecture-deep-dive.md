# Network Swiss Tool Pro - Master Brain Documentation

> **ARCHIVE / HISTORICAL** — Contains v6.x paths and external `file://` links.  
> **Canonical disaster recovery (2026+):** [14-roadmap/README.md](../14-roadmap/README.md)  
> **Canonical architecture:** [MODULE_ARCHITECTURE.md](MODULE_ARCHITECTURE.md) · [CODE_INVENTORY.md](../02-codebase/CODE_INVENTORY.md)

# Network Swiss Tool Pro - Master Brain Documentation (legacy)

> **"Shit Hits The Fan" Recovery Guide**  
> **Version:** 6.7.0 - Premium Edition (historical)  
> **Last Updated:** 2026-05-04
> 
> ⚠️ **v6.7.0 Release:** Advanced vPC Topology Visualization and Interface Description injection.
>
> 🔌 **New in v6.0:** Plugin Registry, Dynamic UI Generation, Gatekeeper Upload System, and Rollback Management.

---

## 🚨 EMERGENCY REBUILD - START HERE

If you need to rebuild this application from scratch, follow this exact order:

### 5-Minute Quick Rebuild
```bash
# 1. Clone/copy this docs folder
# 2. Read: docs/REBUILD_MASTER_GUIDE.md (FOOLPROOF INSTRUCTIONS)
# 3. Follow the Layered Construction workflow
# 4. Execute prompts P01 through P11 in order
# 5. Run: python vlan_checker_web.py
```

---

## 📋 What This Application Does

**Network Swiss Tool Pro** is a multi-mode enterprise network toolkit for Cisco (IOS/NXOS), Juniper (Junos), and F5 (BigIP) devices:

| Mode | Purpose | Entry Point |
|------|---------|-------------|
| **Web Edition** | Modern Browser-based GUI with real-time logs | `vlan_checker_web.py` |
| **GUI Edition** | Lightweight Desktop Tkinter application | `vlan_checker_gui.py` |
| **CLI Edition** | Headless automation & scripting engine | `main.py --mode cli` |

### Core Capabilities

**v6.0 Plugin Platform:**
1. **🔌 Dynamic Plugin System** - Hot-load modular network tools without server restart.
2. **🛡️ Gatekeeper Sandbox** - Upload validation with security scanning and syntax checking.
3. **📦 Plugin Registry** - Automatic discovery with metadata extraction and contract validation.
4. **↩️ Rollback Manager** - Version vault with one-click restore for any plugin.
5. **🎨 Dynamic UI Generation** - Auto-generate input forms from plugin METADATA.

**Core Network Tools:**
6. **Connectivity & Auth** - Rapid Ping + SSH validation with log trace.
7. **Interactive CLI Terminal** - High-performance, real-time SSH shell in the browser (xterm.js + SocketIO).
8. **VLAN Audit** - Automated discovery, parsing, and CSV reporting.
9. **VLAN Management** - Idempotent Add/Rename/Delete with auto-backup & verify.
10. **MAC Address Trace** - Cross-switch MAC table lookup and port identification.
11. **Topology Mapping** - Dynamic CDP/LLDP visualization. **(v6.7.0: Advanced vPC clustering with `vpc_shared` link mapping and interactive Interface Description tooltips)**.
12. **Config Backup** - Automated diff-aware configuration repository.
13. **Network Audit** - Hardware/Software/OS version inventory (CSV/JSON).
14. **VLAN Compliance** - Compare VLAN database against an environment baseline.

---

## 🏗️ Architecture Overview (v6.0 Plugin Platform)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE LAYER                          │
├──────────────┬──────────────┬───────────────────────────────────────┤
│  Web (Flask) │ GUI (Tkinter)│    CLI (Argparse)                     │
│  vlan_checker│  vlan_checker│    main.py                            │
│  _web.py     │  _gui.py     │                                       │
└──────┬───────┴──────┬───────┴───────────────────┬───────────────────┘
       │              │                         │
       └──────────────┴───────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │     ADAPTERS LAYER        │
                    │   modules/adapters.py     │
                    │  • Legacy orchestration   │
                    │  • Generic plugin runner  │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │   PLUGIN PLATFORM v6.0   │
                    │  modules/plugin_registry │
                    │  • Discovery Engine      │
                    │  • Contract Validator    │
                    │  • Sandbox Gatekeeper    │
                    │  • Rollback Manager      │
                    └─────────────┬─────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────▼────────┐  ┌──────────────▼────────┐  ┌───────────▼────────┐
│ LEGACY MODULES │  │   PLUGIN MODULES      │  │   UTILITY LAYER    │
│ • vlan_audit   │  │  modules/plugins/     │  │ • network_base     │
│ • mac_trace    │  │  • vlan_audit_plugin   │  │ • structured_logger│
│ • topology_    │  │  • base_template       │  │ • config_backup    │
│   mapper       │  │  • [Your Plugins Here] │  │   _system          │
└────────────────┘  └───────────────────────┘  └────────────────────┘
```

**v6.0 Key Components:**
- **PluginRegistry** (`modules/plugin_registry.py`): Singleton discovery and management
- **Base Template** (`modules/plugins/base_template.py`): Reference implementation
- **Sandbox** (`scratch/uploads/`): Staging area for new plugins
- **Version Vault** (`backups/plugins/`): Rollback storage for plugin versions

---

## 📦 Hierarchical File Structure (v6.0)

```
Net_mngmnt_tool/
├── vlan_checker_web.py          # Primary Web entry point (v6.0)
├── main.py                      # CLI entry point (v6.0)
├── modules/                     # Core Business Logic
│   ├── adapters.py              # Orchestration + Generic Plugin Runner
│   ├── plugin_registry.py       # v6.0: Plugin Discovery & Management
│   ├── cli_manager.py           # Interactive SSH Shell Engine
│   ├── plugins/                 # v6.0: Plugin Directory
│   │   ├── base_template.py     # Reference plugin implementation
│   │   ├── vlan_audit_plugin.py # Plugin-based VLAN audit
│   │   └── [your_plugins].py    # Custom plugins go here
│   └── ...                      # Legacy feature modules
├── scratch/                     # v6.0: Staging area
│   └── uploads/                 # Plugin upload sandbox
├── backups/                     # Snapshots & Plugin Versions
│   └── plugins/                 # Rollback storage per plugin
├── static/                      # Web Assets (CSS, JS, xterm.js)
└── build_scripts/               # PyInstaller Assets
```

**v6.0 Plugin Development (HARDCODED REQUIREMENTS):**

⚠️ **MANDATORY:** ALL plugins MUST comply with:
- `PLUGIN_DOCUMENTATION_REQUIREMENTS.md` - Documentation standards
- `PLUGIN_BUNDLING_POLICY.md` - Build inclusion requirements

### 1. Plugin Bundling Policy (HARDCODED)

**ALL PLUGINS MUST BE INCLUDED IN EVERY BUILD - NO EXCEPTIONS**

- ✅ Build script validates all plugins are present
- ✅ ALL plugins copied to `dist_package/plugins/` folder
- ✅ ALL plugin docs copied to `dist_package/docs/plugins/`
- ✅ Users receive complete set - they decide what to upload
- ✅ `PLUGINS_INCLUDED.txt` manifest lists all bundled plugins
- ✅ See `docs/00_MASTER/PLUGIN_BUNDLING_POLICY.md`

### 2. Version Requirements:
   - MUST use Semantic Versioning (MAJOR.MINOR.PATCH)
   - MUST maintain version history in docstring
   - MUST update changelog on EVERY change

### 3. Documentation Requirements (6 files REQUIRED):
   - `docs/plugins/{plugin_id}/README.md` - Current documentation
   - `docs/plugins/{plugin_id}/RELEASE_NOTES.md` - All releases
   - `docs/plugins/{plugin_id}/PROMPT.md` - Creation instructions
   - `docs/plugins/{plugin_id}/CHANGELOG.md` - Detailed changelog
   - `docs/plugins/{plugin_id}/TEST_RESULTS.md` - QA results
   - `docs/plugins/{plugin_id}/COMPATIBILITY.md` - Platform matrix

### 4. Version Archive (REQUIRED):
   - `docs/plugins/{plugin_id}/versions/vX.Y.Z/` folder
   - Archived plugin file, README, release notes, test results
   - `manifest.json` with checksums and metadata

### 5. METADATA Requirements:
   - MUST include `"version"` field (SemVer)
   - MUST include `"changelog"` array
   - MUST include `"documentation"` dict with file paths
   - MUST include `"version_archive"` info

### 6. Tools:
   - **Wizard:** `python create_plugin.py` enforces all requirements
   - **Template:** `modules/plugins/base_template.py`
   - **Policy:** `docs/00_MASTER/PLUGIN_BUNDLING_POLICY.md`

---

## 🔑 Senior Developer Standards

### 1. Adapter Pattern
NEVER add business logic to the UI files. All workflows must be implemented in `modules/adapters.py` so they are shared across Web, GUI, and CLI.

### 2. The Return Contract
All modules MUST return:
```python
{
    "status": "success" | "fail",
    "data": { ... },   # The payload
    "error": "..."    # Detailed error if status is fail
}
```

### 3. Safety First
- **Dry-Run**: Always implement a `--dry-run` flag for mutable operations.
- **Auto-Backup**: Take a config snapshot BEFORE pushing any change.
- **Post-Check**: Verify the change was successful (e.g., `show vlan` after `set vlan`).

---

## 🛠️ Build & Deployment

### Packaging
File: `build_scripts/NetworkSwissToolPro_v5_5_0_Offline.spec`
- Command: `pyinstaller --clean build_scripts/NetworkSwissToolPro_v5_5_0_Offline.spec`
- Handled via: `build_scripts/build_web_production_exe.bat`

### Compatibility
- Designed for **Python 3.12+**.
- Includes `telnetlib_compat.py` for Python 3.13+ (where telnetlib was removed).
- Hardened for **offline/air-gapped** environments.

---

## 📚 Documentation Index

| Category | Primary Documents |
|----------|-------------------|
| **00 MASTER** | [REBUILD_MASTER_GUIDE.md](file:///c:/Users/bbb12/OneDrive/Desktop/Antigravity%20Projects%20Folder/Net_mngmnt_tool%20-%20V5.5%20-%20Operational/docs/00_MASTER/REBUILD_MASTER_GUIDE.md), [STRATEGIC_ROADMAP.md](file:///c:/Users/bbb12/OneDrive/Desktop/Antigravity%20Projects%20Folder/Net_mngmnt_tool%20-%20V5.5%20-%20Operational/docs/00_MASTER/STRATEGIC_ROADMAP.md) |
| **01 ARCHITECTURE** | [01-ARCHITECTURE.md](file:///c:/Users/bbb12/OneDrive/Desktop/Antigravity%20Projects%20Folder/Net_mngmnt_tool%20-%20V5.5%20-%20Operational/docs/01_ARCHITECTURE/01-ARCHITECTURE.md), [02-APP-LOGIC.md](file:///c:/Users/bbb12/OneDrive/Desktop/Antigravity%20Projects%20Folder/Net_mngmnt_tool%20-%20V5.5%20-%20Operational/docs/01_ARCHITECTURE/02-APP-LOGIC.md) |
| **02 RELEASES** | [CHANGELOG.md](file:///c:/Users/bbb12/OneDrive/Desktop/Antigravity%20Projects%20Folder/Net_mngmnt_tool%20-%20V5.5%20-%20Operational/docs/02_RELEASES/CHANGELOG.md), [ROADMAP_FEATURES.md](file:///c:/Users/bbb12/OneDrive/Desktop/Antigravity%20Projects%20Folder/Net_mngmnt_tool%20-%20V5.5%20-%20Operational/docs/02_RELEASES/ROADMAP_FEATURES.md) |
| **03 QA** | [QA_TESTING_CHECKLIST.txt](file:///c:/Users/bbb12/OneDrive/Desktop/Antigravity%20Projects%20Folder/Net_mngmnt_tool%20-%20V5.5%20-%20Operational/docs/03_QA/QA_TESTING_CHECKLIST.txt), [ST_MASTER_QA_SUITE.md](file:///c:/Users/bbb12/OneDrive/Desktop/Antigravity%20Projects%20Folder/Net_mngmnt_tool%20-%20V5.5%20-%20Operational/docs/03_QA/ST_MASTER_QA_SUITE.md) |
| **04 TROUBLESHOOTING**| [06-TROUBLESHOOTING.md](file:///c:/Users/bbb12/OneDrive/Desktop/Antigravity%20Projects%20Folder/Net_mngmnt_tool%20-%20V5.5%20-%20Operational/docs/04_TROUBLESHOOTING/06-TROUBLESHOOTING.md), [TS_ERROR_INDEX.md](file:///c:/Users/bbb12/OneDrive/Desktop/Antigravity%20Projects%20Folder/Net_mngmnt_tool%20-%20V5.5%20-%20Operational/docs/04_TROUBLESHOOTING/TS_ERROR_INDEX.md) |
| **05 PROCEDURES** | [WORKFLOWS.md](file:///c:/Users/bbb12/OneDrive/Desktop/Antigravity%20Projects%20Folder/Net_mngmnt_tool%20-%20V5.5%20-%20Operational/docs/05_PROCEDURES/WORKFLOWS.md), [ONBOARDING.md](file:///c:/Users/bbb12/OneDrive/Desktop/Antigravity%20Projects%20Folder/Net_mngmnt_tool%20-%20V5.5%20-%20Operational/docs/05_PROCEDURES/ONBOARDING.md) |
| **06 RECOVERY** | [RECOVERY_MASTER.md](file:///c:/Users/bbb12/OneDrive/Desktop/Antigravity%20Projects%20Folder/Net_mngmnt_tool%20-%20V5.5%20-%20Operational/docs/06_RECOVERY/RECOVERY_MASTER.md) |

---

## 🆘 Need Help?

1.  **Check the Master Guide**: `docs/00_MASTER/REBUILD_MASTER_GUIDE.md`
2.  **Verify Setup**: Run `python main.py test --category infrastructure`
3.  **Review Logs**: Open `logs/operations.log` for execution trace.
