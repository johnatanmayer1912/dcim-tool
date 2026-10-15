# 🧩 Puzzle Piece 3: The Generic Orchestrator

> **[OBJECTIVE]**
> Refactor `modules/adapters.py` to remove hard-coded dependencies on specific feature scripts. Move to a "Dynamic Execution Loop" that can launch any plugin in the registry.

---

## 🛠️ Task 1: The `execute_task` Engine
In `modules/adapters.py`, implement a generic execution method:

```python
def run_generic_plugin(plugin_id, devices, user, pwd, enb_pwd, params, log_func):
    """
    The orchestrator for ALL plugins.
    1. Grabs the module from the Registry.
    2. Iterates over devices.
    3. Executes the plugin's run() method.
    4. Handles Threading/Parallelization (ThreadPoolExecutor).
    """
```

### Key Logic:
1.  **Registry Lookup**: Get the module object for the `plugin_id`.
2.  **Thread Pool**: Use `ThreadPoolExecutor(max_workers=10)` to run the plugin's `run()` function in parallel across `devices`.
3.  **Result Aggregation**: Collect the JSON results and ensure they match the standard format: `{"device": "...", "status": "...", "data": {...}}`.
4.  **Logging Proxy**: Ensure that when a plugin calls `log_func("Hello")`, it is properly routed to the `vlan_checker_web.py` log queue.

---

## 🛠️ Task 2: Dispatch Refactor (vlan_checker_web.py)
In the `api_execute()` route, update the logic to check both internal methods AND the plugin registry:

```python
if action in INTERNAL_MAPPING:
    # ... call legacy threads ...
elif plugin_registry.exists(action):
    # Call run_generic_plugin(...) in a background thread
```

## 🛠️ Task 3: Migratory Testing (The "VLAN Audit" Test)
To verify the engine, refactor the existing `vlan_audit.py` into the new plugin format as `modules/plugins/vlan_audit_plugin.py`.
- **Validation**: Ensure that the results from the new plugin-based audit are identical to the legacy method.
- **Cleanup**: Once verified, the AI should provide instructions on how to disable/remove the legacy code paths to prevent duplication.
1.  **Parallel Execution**: Verify that if 5 devices are selected, the plugin `run()` calls happen concurrently (measure time to confirm).
2.  **State Isolation**: Ensure that parameters specifically for "Device A" in the plugin don't leak into the execution for "Device B".
3.  **Graceful Catch**: If a plugin's `run()` function raises an unhandled `Exception`, the Orchestrator MUST catch it, log the traceback, and report `status: fail` for that specific device ONLY.

---

**Next Action**: Once the backend can execute dynamic tasks, move to [P04_UI_DYNAMO.md](./P04_UI_DYNAMO.md) to build the frontend.
