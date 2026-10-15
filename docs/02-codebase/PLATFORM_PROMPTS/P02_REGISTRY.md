# 🧩 Puzzle Piece 2: The Discovery Engine

> **[OBJECTIVE]**
> Build the "Registry" logic that scans the file system, identifies valid plugins, and caches their metadata. This engine is the bridge between the disk and the UI.

---

## 🛠️ Task 1: Create `modules/plugin_registry.py`
Implement a `PluginRegistry` singleton class.

### Key Logic:
1.  **Scanning**: Use `os.listdir` or `pkgutil` to find all `.py` files in `modules/plugins/`.
2.  **Validation**: For each file, attempt to read the `METADATA` dictionary WITHOUT executing the whole file (use `ast.parse` or `importlib.util` dynamic loading).
3.  **Registration**: Store a map of `plugin_id -> {file_path, metadata, module_object}`.
4.  **Refresh Mechanism**: Implement a `registry.reload()` method that re-scans the folder. This enables "Hot Reloading" of features without restarting the server.

---

## 🛠️ Task 2: Discovery API (vlan_checker_web.py)
Create a new Flask route to serve the plugin list to the UI:

```python
@app.route('/api/plugins/list')
def api_list_plugins():
    # Call registry.get_all_metadata()
    # Return JSON: {"plugins": [...metadata hashes...]}
```

---

## ✅ QA Validation for the Agent
1.  **Duplicate Detection**: If two plugins have the same `plugin_id`, the registry MUST log an error and only load the first one.
2.  **Silent Failure**: If a file in `modules/plugins/` is not a valid Python file (e.g., `README.txt`), the registry must ignore it silently without crashing.
3.  **Import Isolation**: Ensure that loading one plugin does not accidentally execute global code in another plugin (Task orchestration should only happen inside `run()`).

---

**Next Action**: Once the registry can "see" the plugins, move to [P03_ORCHESTRATOR.md](./P03_ORCHESTRATOR.md) to refactor the execution loop.
