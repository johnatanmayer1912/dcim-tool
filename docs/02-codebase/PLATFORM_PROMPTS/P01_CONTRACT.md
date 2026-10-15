# 🧩 Puzzle Piece 1: The Standardized Contract

> **[OBJECTIVE]**
> Define the precise "Code Contract" that all plugins must follow. This ensures the backend orchestrator and the frontend UI know exactly what to expect from any dropped-in file.

---

## 🛠️ Task 1: Implementation of `plugin_base.py` (Optional / Interface)
Create a reference file `modules/plugins/base_template.py` that serves as the "Golden Standard".

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

---

## 📋 Task 2: Metadata Schema
Every plugin MUST contain a `METADATA` dictionary at the top of the file. This allows the Frontend to "draw" the UI automatically.

```python
METADATA = {
    "plugin_id": "vlan_audit_advanced",         # Internal unique ID
    "display_name": "Advanced vLAN Audit",     # UI Button Label
    "version": "1.0.0",
    "author": "Network Swiss Tool",
    "category": "Audit",                       # Tab/Group in UI
    "description": "Performs deep audit including unused VLAN detection.",
    "required_params": {                       # Input boxes to generate in UI
        "vlan_id": {
            "type": "integer",
            "label": "Target VLAN ID",
            "placeholder": "e.g. 100",
            "required": True
        },
        "dry_run": {
            "type": "checkbox",
            "label": "Dry Run Mode",
            "default": False
        }
    }
}
```

---

## ✅ QA Validation for the Agent
1.  **Strict Typing**: Ensure the `run` function returns a `dict`. If it returns a string or list, the orchestrator MUST catch it and return a "Contract Violation" error.
2.  **Schema Check**: The Registry (Step 2) must be instructed to ignore any file that lacks this `METADATA` dictionary.
3.  **No Core Imports**: verify the template only imports from `modules.network_base` and core libraries.

---

**Next Action**: Once this contract is defined, move to [P02_REGISTRY.md](./P02_REGISTRY.md) to build the scanner.
