# Network Swiss Tool Pro - Exact Rebuild Procedure

| Metadata | Description |
| :--- | :--- |
| **Purpose** | Mandatory step-by-step instructions for recreating the production environment and executable. |
| **Scope** | Development environment setup, dependency management, and layered construction logic. |
| **Related Documents** | [Build Process](build-process.md), [System Architecture](../01-architecture/system-architecture.md) |
| **Update Responsibility** | DevOps Lead / Release Manager |
| **Version Awareness** | v7.0.29 |

> **Full code loss / docs-only rebuild:** Use **[`../15-rebuild-roadmap/DISASTER_RECOVERY_COMMAND.md`](../15-rebuild-roadmap/DISASTER_RECOVERY_COMMAND.md)** (P01–P42). This file is the **developer** rebuild summary; legacy `prompts/P0x` links below are superseded by `15-rebuild-roadmap/`.

---

## 🏗️ Phase 0: Environment Setup

Before executing any construction prompts, ensure your base environment is ready.

1.  **Python Version**: 3.12, 3.13, or 3.14 (3.13+ requires `telnetlib_compat.py`).
2.  **Dependencies**:
    ```bash
    pip install netmiko flask flask-socketio pandas openpyxl paramiko cryptography
    ```
3.  **Directory Structure**:
    ```bash
    mkdir modules, utils, backups, logs, reports, build_scripts, legacy
    ```

---

## 🧱 Phase 1: Layered Construction (The Prompt Sequence)

Follow these prompts exactly in the specified order. Each layer MUST be tested before moving to the next.

| Step | Prompt File | Purpose | Validation |
|:---:|:---|:---|:---|
| **All** | [DISASTER_RECOVERY_COMMAND.md](../15-rebuild-roadmap/DISASTER_RECOVERY_COMMAND.md) | P01–P42 batch rebuild | `pytest` + `_prebuild.py` PASS |
| **Index** | [00-RECONSTRUCTION_INDEX.md](../15-rebuild-roadmap/00-RECONSTRUCTION_INDEX.md) | Full roadmap map | Phase folders present |

---

## 🛠️ Phase 2: Critical v6.6.0 Synchronizations

After Phase 1, ensure the following v6.6.0 specific patches are applied:

### 1. Web Handshake Fix (127.0.0.1 / Port 5051)
In `vlan_checker_web.py`, ensure the Flask server binds to `127.0.0.1` and uses Port `5051`. The frontend `index.html` must use `127.0.0.1` for WebSocket/API calls to avoid IPv6 resolution lag.

### 2. vPC Topology Premium Rendering
Verify `modules/adapters.py` includes the `vpc_domain_{id}` grouping logic for node clustering and the orange/purple glow styles for member/peer links.

### 3. Hardened CLI Handshake
Ensure `handle_cli_connect` in `vlan_checker_web.py` uses room-based emits (`to=session_id`) and avoids redundant SID-direct emits to prevent character doubling.

### 4. Glassmorphism UI
Confirm `utils/report_formatter.py` and `cli_terminal.html` use the Inter font family and backdrop-blur styling for side panels.

---

## 🧪 Phase 3: Validation Protocol

1.  **Smoke Test**: `python main.py test --category infrastructure`
2.  **Connectivity Audit**: Run Ping + SSH check on `inventory.txt`.
3.  **VLAN Idempotency**:
    *   Test adding a VLAN that already exists (Should report SKIP).
    *   Test renaming a VLAN (Should show pre-change backup).
4.  **Topology Export**: Generate a map and verify it loads without internet access.

---

## 🚀 Rebuild Logic (Dummy-Proof Rules)

-   **RULE #1**: NEVER skip a prompt. The order is strict.
-   **RULE #2**: If `import modules.adapters` fails, DO NOT proceed to the Web UI.
-   **RULE #3**: Check the `logs/` folder immediately if the UI shows "Server Offline".
-   **RULE #4**: Always use `inventory.txt` as the source of truth for device IPs.

---

**Next Steps:**
- → Start with [Foundation Guide](../02-codebase/foundation.md)
- → If stuck: Consult [Troubleshooting Index](../08-operations/TS_ERROR_INDEX.md)
