# Engineering Prompt: Transitioning to the "Dynamic Plugin Platform" (v6.0)

> **[INSTRUCTIONS FOR THE AI AGENT]**
> You are acting as the Lead System Architect and Senior Network Automation Engineer. Your mission is to evolve the **Network Swiss Tool Pro v5.5.0** from a monolithic application into a **Dynamic Plugin-Based Platform**. This is a non-breaking architectural shift that will enable the user to add new features by simply dropping a `.py` file into a directory, without rebuilding the entire application or executable.

---

## 🎯 Primary Objective
Rewrite the orchestration layer (`modules/adapters.py`) and the Web UI dispatch logic (`vlan_checker_web.py`) to support **"Drop-in Modules"**. The goal is that a new file in `modules/plugins/` should automatically appear as an operable action in the UI.

---

## 🛠️ Technical Requirements

### 1. The Plugin Contract (Standard API)
Define and enforce a strict signature for all future modules. Every script in the `modules/plugins/` directory must implement a standard entry point:
```python
def run(device, credentials, params, log_func):
    # device: dict (host, type, group)
    # credentials: dict (user, pwd, secret)
    # params: dict (extra inputs like vlan_id, etc.)
    # log_func: function for real-time trace
    return {"status": "success/fail", "data": {}, "error": ""}
```

*Note on v6.7.0 Schema Updates:* For plugins that generate topology output, the return payload MUST include `description` and `vpc_domain_id` metadata fields to enable the new vPC mapping abstractions and interface tooltips.

### 2. The Dynamic Loader (`modules/adapters.py`)
Implement a `ModuleLoader` class that:
- Uses `importlib` and `pkgutil` to scan the `modules/plugins/` directory.
- Extracts metadata from the plugin (e.g., `DISPLAY_NAME`, `CATEGORY`, `REQUIRED_INPUTS`).
- Maps these plugins to a central `PLUGIN_REGISTRY`.

### 3. UI Synchronization (`vlan_checker_web.py`)
Update the Flask backend to:
- Expose a `/api/plugins` endpoint that returns the list of discovered modules.
- Update the `api_execute()` router to dynamically dispatch to any registered plugin based on the `action` ID.
- (Advanced) Update `index.html` to dynamically render buttons/forms for these discovered plugins.

### 4. UI Management Dashboard
Update the frontend with a "Plugin Manager" tab that allows the user to:
- **Upload**: Drag-and-drop a `.py` file to a temporary "Staging" area.
- **Enable/Disable**: Toggle plugins without deleting files.
- **Version History**: See a list of previous versions for a specific plugin.

### 5. Pre-Installation QA (The "Validator")
Implement a "Gatekeeper" service in `adapters.py` that:
- Attempts a `restricted_import` of an uploaded plugin to check for syntax errors.
- Validates the presence of the `run()` function and required Metadata headers (`VERSION`, `AUTHOR`, `MIN_SYSTEM_VERSION`).
- ONLY moves the file from `scratch/uploads/` to `modules/plugins/` if all checks pass.

### 6. Rollback Engine
- Whenever a plugin is updated, the system must move the old version to `backups/plugins/{plugin_name}/{timestamp}_v{n}.py`.
- Provide an "Instant Rollback" API that restores the latest backup if the new version causes runtime errors.

---

## 📚 Documentation & Governance

### 1. Updated Architectures
Modify `docs/01_ARCHITECTURE/01-ARCHITECTURE.md` to reflect the transition from "Hard-coded Adapters" to "Dynamic Plugin Loading". Define the "Plugin Lifecycle" (Discover → Register → Dispatch → Report).

### 2. Developer Onboarding
Create a new guide: `docs/05_PROCEDURES/DEVELOPING_PLUGINS.md`. This must be a **"dummy-proof"** template for a developer to write their first plugin.

### 3. Master Brain Update
Update `docs/00_MASTER/00-MASTER-BRAIN.md` to reflect that the system is now a modular platform.

---

## 🧪 QA & Verification Suite

1.  **Idempotency Test**: Create a dummy plugin `test_plugin.py` and verify it appears in the Web UI without a server restart.
2.  **Contract Validation**: Ensure the system handles "Broken" plugins (e.g., missing `run()` function) without crashing the main Flask process.
3.  **Traceability**: Verify that `log_func` calls from the plugin reach the browser's real-time console correctly.

---

### 4. Uploader Instructions
Document the "Golden Path" for an uploader (user or AI):
1.  **Develop**: Write the plugin locally.
2.  **QA**: Use the `/api/validate_plugin` endpoint to check for signature matches.
3.  **Upload**: Submit via the UI.
4.  **Confirm**: System performs logic check and moves to live production.

---

## 🚀 Execution Paradigm (How to work)

1.  **Librarian Mindset**: Before touching code, audit `modules/adapters.py` to identify all hard-coded operations (`vlan_mgmt`, `mac_trace`, etc.) that need to be "migrated" to the new plugin structure.
2.  **Senior Developer Mindset**: Write clean, PEP8 compliant code. Use type hinting. Ensure backward compatibility (keep the old methods working while phasing in the plugins).
3.  **QA Mindset**: Do not consider a file "Done" until you have verified the internal links and confirmed the logic handles "Device Unreachable" errors gracefully.
4.  **Packaging Mindset**: The AI should create plugins as standalone `.py` files containing all logic. No external proprietary dependencies outside of the core `netmiko/flask` stack.

---

**[FINAL INSTRUCTION]**
Do not just "write code." Document the **WHY** behind the architectural decisions in the `01_ARCHITECTURE.md` while you work. The final result should be a codebase that is essentially "Future-Proof."
