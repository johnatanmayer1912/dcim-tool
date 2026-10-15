# System Behavior Documentation

## Threading Model
The system uses a **Proactive Multithreading** model to ensure the User Interface remains responsive during long-running network operations.

1. **Main Thread**: Responsible for the Tkinter (GUI) or Flask (Web) event loop.
2. **Worker Thread**: Every network task (e.g., VLAN Audit) is spawned in a separate `threading.Thread(daemon=True)`.
3. **Synchronization**:
    - **GUI**: Uses a thread-safe `queue.Queue` to pipe log messages from the worker back to the main UI. The main thread polls this queue every 100ms.
    - **Web**: Uses a global list `log_queue` which is polled by the frontend via an AJAX call to `/api/logs`.

## Network Interaction (Netmiko)
The system leverages the `Netmiko` library for SSH orchestration.

- **Connection Layer**: Handled by `modules.network_base.connect_permissive()`.
- **Permissive Mode**: The system automatically attempts to find prompts, enters `enable` mode if necessary, and handles varied line endings across Cisco and Juniper.
- **Timeouts**: Global delay factors are set to `1.5` to accommodate slower devices or high-latency management networks.

## Result Flow & Data Contract
Every module must return data following the **Unified System Contract**:

```json
{
  "device": "10.1.1.1",
  "status": "success|fail",
  "data": {
    "true_host": "SWITCH-01",
    "feature_data": { ... }
  },
  "error": "Reason for failure (if any)"
}
```

## File Writing Strategy
- **Isolation**: Modules never write to files directly.
- **Delegation**: The Adapter layer collects results and passes them to `utils/report_formatter.py`.
- **Locking**: Since only one Adapter thread runs at a time per task, standard file `open('a')` is used. Reports are timestamped to avoid collisions.

## Error Handling Philosophy
1. **Per-Device Resilience**: A failure on one switch must NOT stop the execution on the rest of the inventory.
2. **Graceful Degradation**: If a command fails (e.g., `show cdp neighbors`), the module attempts a fallback (e.g., `show lldp neighbors`) before reporting a failure.
3. **Audit Trail**: Every error is logged to the persistent `app_session_log_*.txt` for post-run analysis.
