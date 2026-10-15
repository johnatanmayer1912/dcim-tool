# 🧩 The Dynamic Plugin Platform: Puzzle Master Guide

This directory contains a series of **Engineering Prompts** designed to transition the Network Swiss Tool Pro v5.5.0 into a modular v6.0 platform. 

### 🚀 Execution Order
The puzzle pieces MUST be executed in the following sequence to maintain system integrity.

| Step | File | Purpose | Critical Goal |
|:---:|:---|:---|:---|
| **1** | [P01_CONTRACT.md](./P01_CONTRACT.md) | **The Contract** | Define the standardized Python interface for all future features. |
| **2** | [P02_REGISTRY.md](./P02_REGISTRY.md) | **The Discovery Engine** | Build the backend "scanner" that founds files in `modules/plugins/`. |
| **3** | [P03_ORCHESTRATOR.md](./P03_ORCHESTRATOR.md) | **Generic Refactor** | Move `adapters.py` away from hard-coded logic to dynamic dispatching. |
| **4** | [P04_UI_DYNAMO.md](./P04_UI_DYNAMO.md) | **Dynamic UI** | Implement the "Feature List" and "Input Gating" in the browser UI. |
| **5** | [P05_LIFECYCLE.md](./P05_LIFECYCLE.md) | **Gatekeeper & Rollbacks** | Build the safety system for uploads, validation, and emergency rollbacks. |
| **6** | [P06_ALIGNMENT.md](./P06_ALIGNMENT.md) | **Final Alignment** | Ensure Master Brain, Architecture, and QA docs are fully updated for v6.0. |
| **7** | [P07-DOCUMENTATION-LIBRARIAN.md](./P07-DOCUMENTATION-LIBRARIAN.md) | **Documentation Sync** | Systematic synchronization of all documentation with current application state. |

### 🛑 Master Rules for the AI Agent
1.  **Dependency Safety**: Always verify that `modules/network_base.py` remains the primary library for all plugins.
2.  **No Monoliths**: A plugin must be a single file (or a folder if complex). It should never touch the core `vlan_checker_web.py`.
3.  **The "Live-Reload" Rule**: Adding a plugin should NOT require a server restart. The Registry must be refreshable.

### Required Function Signature
Every plugin MUST contain a `run` function with this exact signature:
```python
def run(device, credentials, params, config, log_func):
    """
    Main entry point for the plugin task.
    :param device: dict containing {'host': '...', 'device_type': '...', 'group': '...'}
    :param credentials: dict containing {'username': '...', 'password': '...', 'secret': '...'}
    :param params: dict of dynamic user inputs (validated against METADATA)
    :param config: dict of global application settings (timeouts, logs, etc.)
    :param log_func: callable log(msg) for real-time trace to UI
    :return: dict {'status': 'success/fail', 'data': {...}, 'error': 'message or None'}
    """
```
**Security**: Disallow plugins from using `os.popen` or `subprocess` for system-level destructive commands. Use `netmiko` only.

---

**Next Action**: Proceed to [P01_CONTRACT.md](./P01_CONTRACT.md)
