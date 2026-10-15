# AI Prompt Index - Rebuild Network Swiss Tool Pro

> **Step-by-step prompts for rebuilding the entire application**

---

## ⚡ Quick Start: Rebuild Sequence

Execute these prompts **in order**. Each prompt builds on the previous:

| Order | Prompt File | Purpose | Est. Time |
|-------|-------------|---------|-----------|
| 1 | `P01-FOUNDATION.md` | Project structure & core utilities | 10 min |
| 2 | `P02-NETWORK-BASE.md` | Connection handling & base functions | 15 min |
| 3 | `P03-VLAN-MODULES.md` | VLAN audit & management | 20 min |
| 4 | `P04-MAC-TRACE.md` | MAC address tracing | 15 min |
| 5 | `P05-TOPOLOGY.md` | Topology mapping | 25 min |
| 6 | `P06-ADAPTERS.md` | Adapter orchestration layer | 20 min |
| 7 | `P07-WEB-INTERFACE.md` | Flask web UI | 25 min |
| 8 | `P08-REPORTING.md` | Report formatting | 15 min |
| 9 | `P09-LOGGING.md` | Structured logging | 15 min |
| 10 | `P10-BUILD.md` | PyInstaller packaging | 10 min |
| 11 | `P11-QA-TESTING.md` | QA validation | 20 min |

**Total Estimated Time:** ~3 hours (if done sequentially)

---

## 📋 Prompt Dependencies

```
P01-FOUNDATION
    │
    ├───► P02-NETWORK-BASE
    │       │
    │       ├───► P03-VLAN-MODULES
    │       │       │
    │       │       └───► P06-ADAPTERS
    │       │               │
    │       ├───► P04-MAC-TRACE ────────┤
    │       │                           │
    │       ├───► P05-TOPOLOGY ─────────┤
    │       │                           │
    │       └───► (Other modules) ──────┤
    │                                   │
    ├───► P08-REPORTING ────────────────┤
    │                                   │
    ├───► P09-LOGGING ──────────────────┤
    │                                   ▼
    └───► P07-WEB-INTERFACE ◄───────────┘
                │
                ▼
           P10-BUILD
                │
                ▼
           P11-QA-TESTING
```

---

## 🎯 Execution Rules

### Before Running Any Prompt:

1. **Backup First**
   ```bash
   git add .
   git commit -m "Before prompt execution"
   # OR manual backup:
   Copy-Item -Recurse . ../backup-$(Get-Date -Format "yyyyMMdd-HHmmss")
   ```

2. **Check Prerequisites**
   - Python 3.12+ installed
   - Netmiko available: `pip show netmiko`
   - Flask available: `pip show flask`

3. **Verify Previous Prompt Success**
   - Files created exist
   - Imports work: `python -c "import modules.network_base"`

### After Running Each Prompt:

1. **Test the Component**
   ```bash
   python -c "from modules import X; print('OK')"
   ```

2. **Review Changes**
   - Files match expected structure
   - No syntax errors

3. **Commit Checkpoint**
   ```bash
   git add .
   git commit -m "P0X: Completed [feature]"
   ```

---

## 🔧 Prompt Categories

### Foundation Prompts (P01-P02)
**Goal:** Establish project structure and core utilities

| Prompt | Output |
|--------|--------|
| P01 | `utils/report_formatter.py`, `VERSION`, `README.md`, folder structure |
| P02 | `modules/network_base.py` - Connection handling, VLAN parsing |

### Module Prompts (P03-P05)
**Goal:** Build core network operation modules

| Prompt | Output |
|--------|--------|
| P03 | `modules/vlan_audit.py`, `modules/vlan_mgmt_production.py` |
| P04 | `modules/mac_trace.py` |
| P05 | `modules/topology_mapper.py`, `modules/node_interface_topology.py` |

### Integration Prompts (P06-P07)
**Goal:** Connect modules together and create UI

| Prompt | Output |
|--------|--------|
| P06 | `modules/adapters.py` - Orchestration layer |
| P07 | `vlan_checker_web.py`, `modules/web/templates/index.html` |

### Utility Prompts (P08-P09)
**Goal:** Supporting systems

| Prompt | Output |
|--------|--------|
| P08 | Enhanced `utils/report_formatter.py` with HTML generation |
| P09 | `utils/structured_logger.py`, `utils/config_backup_system.py` |

### Deployment Prompts (P10-P11)
**Goal:** Package and validate

| Prompt | Output |
|--------|--------|
| P10 | `NetworkSwissToolPro_v6_6_0.spec`, build scripts |
| P11 | QA checklist validation, smoke tests |

---

## 🆘 Recovery Procedures

### If a Prompt Fails:

1. **Don't panic**
   - Read the error message
   - Check if it's a missing import or syntax error

2. **Rollback Option**
   ```bash
   # If you committed before the prompt
   git reset --hard HEAD~1
   
   # If you have a backup folder
   Remove-Item -Recurse .
   Copy-Item -Recurse ../backup-xxxx .
   ```

3. **Manual Fix Template**
   ```python
   # Add this to debug
   import traceback
   print(traceback.format_exc())
   ```

### Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError` | Missing dependency | `pip install X` |
| `IndentationError` | Mixed tabs/spaces | Convert to 4 spaces |
| `NameError` | Variable not defined | Check variable scope |
| `ImportError` | Circular import | Reorder imports |

---

## 📝 Before/After State

### Before Prompt P01:
```
(empty workspace)
```

### After Prompt P11 (Complete):
```
NetworkSwissToolPro/
├── vlan_checker_web.py          ✓
├── modules/
│   ├── adapters.py              ✓
│   ├── network_base.py          ✓
│   ├── vlan_audit.py            ✓
│   ├── vlan_mgmt_production.py  ✓
│   ├── mac_trace.py             ✓
│   ├── topology_mapper.py       ✓
│   └── ...                      ✓
├── utils/
│   ├── report_formatter.py      ✓
│   ├── structured_logger.py     ✓
│   └── config_backup_system.py  ✓
├── modules/web/templates/
│   └── index.html               ✓
├── dist/                        ✓
│   └── NetworkSwissToolPro_v6_6_0.exe ✓
└── docs/                        ✓
```

---

## 🎓 AI Behavior Guide

When executing these prompts, the AI should:

### DO:
- ✅ Follow the exact file structure specified
- ✅ Include all error handling shown in examples
- ✅ Add docstrings to all functions
- ✅ Test imports after creating files
- ✅ Use existing patterns from previous prompts

### DON'T:
- ❌ Skip error handling for "simplicity"
- ❌ Change function signatures without reason
- ❌ Add unnecessary dependencies
- ❌ Skip the verification steps
- ❌ Assume "it should work" without testing

---

## 📚 Additional Resources

| Doc | Purpose |
|-----|---------|
| `AI-BEHAVIOR-GUIDE.md` | Detailed AI coding standards |
| `BACKUP-RECOVERY.md` | How to backup before changes |
| `TESTING-STRATEGY.md` | Unit and integration testing |
| `P12-BUGFIX-TEMPLATE.md` | Template for fixing bugs |
| `P13-FEATURE-TEMPLATE.md` | Template for adding features |

---

## 🚀 Next Step

**Ready to start?**
→ Open `P01-FOUNDATION.md` and follow the instructions exactly.

**Need to understand the architecture first?**
→ Read `../01-ARCHITECTURE.md`

**Want to see all features first?**
→ Read `../features/FEATURE-ROADMAP.md`
