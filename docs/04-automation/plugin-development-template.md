# Developer Guide: Creating a New Plugin (v6.0)

> **"Follow this template to add a new networking feature to the tool in under 5 minutes."**

---

## 1. Create the File
Create a new file in `modules/plugins/` (e.g., `modules/plugins/my_new_tool.py`).

---

## 2. Define your METADATA
Paste this block at the top. The UI uses this to draw your tool's settings.

```python
METADATA = {
    "plugin_id": "my_new_tool",
    "display_name": "My New Tool",
    "version": "1.0.0",
    "author": "Network Admin",
    "category": "Maintenance",
    "description": "Short description of what this tool does.",
    "required_params": {
        "text_field": {"type": "string", "label": "Description", "required": True},
        "number_field": {"type": "integer", "label": "VLAN ID", "default": 1},
        "toggle": {"type": "checkbox", "label": "Enable Debug", "default": False}
    }
}
```

---

## 3. Implement the Logic
Every plugin must have a `run()` function.

```python
from modules.network_base import connect_permissive, build_json

def run(device, credentials, params, config, log_func):
    host = device['host']
    log_func(f"[{host}] Starting task...")
    
    # Access your dynamic parameters
    desc = params.get('text_field')
    vlan = params.get('number_field')
    
    try:
        # 1. Connect
        conn = connect_permissive(device, **credentials)
        
        # 2. Do Work
        output = conn.send_command(f"show vlan id {vlan}")
        
        # 3. Disconnect
        conn.disconnect()
        
        # 4. Return Standard Result
        return build_json(host, "success", {"raw": output})
        
    except Exception as e:
        return build_json(host, "fail", {}, str(e))
```

---

## 4. Test it!
1.  Save the file.
2.  Refresh your browser.
3.  The "My New Tool" button will appear in the **Plugin Tools** tab.
4.  If it doesn't appear, check `logs/startup.log` for validation errors.
