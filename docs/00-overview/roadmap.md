# Network Swiss Tool Pro - Strategic Roadmap

| Metadata | Description |
| :--- | :--- |
| **Purpose** | High-priority feature pipeline and strategic product direction for the platform. |
| **Scope** | Short-term enhancements, long-term architectural shifts, and impact analysis. |
| **Related Documents** | [Project Overview](project-overview.md), [System Architecture](../01-architecture/system-architecture.md) |
| **Update Responsibility** | Product Owner / Lead Architect |
| **Version Awareness** | v6.9.26 |

---

### 1. Parallel Execution Engine (Concurrency)
*   **Rank:** 1 (Top Priority)
*   **Reasoning:** Currently, processing 100 devices takes ~5-10 minutes because each SSH connection happens sequentially. Implementing a thread pool will reduce this to seconds.
*   **Impact:** **CRITICAL**. Transformation from a "scripting tool" to an "enterprise engine".
*   **Complexity:** Medium. Requires modifying `adapters.py` to use `ThreadPoolExecutor`.
*   **Est. Build Time:** 8-10 hours.
*   **Verification:** Benchmarking execution time for a 50-device inventory.

---

### 2. Integrated Web SSH Terminal
*   **Rank:** 2
*   **Reasoning:** When a tool identifies an issue, engineers often need to jump into the CLI manually. An integrated xterm.js terminal using Paramiko WebSockets eliminates the need to open Putty/SecureCRT.
*   **Impact:** **HIGH**. Keeps the engineer within a single "Pane of Glass".
*   **Complexity:** High. Requires WebSocket backend (Flask-SocketIO) and TTY handling.
*   **Est. Build Time:** 16-20 hours.
*   **Verification:** Latency testing and terminal resizing validation.

---

### 3. Automatic Drift Rollback
*   **Rank:** 3
*   **Reasoning:** If a VLAN rename or add completes but the post-check fails (e.g., VLAN doesn't show up in `show vlan`), the tool should automatically offer an "Instant Revert" button using the `pre-change` backup.
*   **Impact:** **HIGH**. Significantly increases safety and trust in the tool.
*   **Complexity:** Medium. Logic exists in `config_backup_system.py`, needs UI integration.
*   **Est. Build Time:** 6-8 hours.
*   **Verification:** Simulated failure injection and verified automated revert.

---

### 4. Modern Glass-UI Dashboard (Next.js/React Conversion)
*   **Rank:** 4
*   **Reasoning:** The current Flask/Jinja2 setup is solid but limited in responsiveness. Moving to a modern frontend framework allows for real-time data streaming and a more "Premium" feel.
*   **Impact:** **MEDIUM**. Massive UX/Aesthetics improvement.
*   **Complexity:** High. Complete frontend rewrite.
*   **Est. Build Time:** 24-30 hours.
*   **Verification:** Responsive design audit and cross-browser testing.

---

### 5. Jinja2-Based Configuration Templating
*   **Rank:** 5
*   **Reasoning:** Hardcoding `vlan {vid}` commands is limiting. Using Jinja2 templates for full-device boilerplate (e.g., "Standard BGP Peer" or "New Access Port") allows for rapid network provisioning.
*   **Impact:** **MEDIUM**. Expands the tool into a full Deployment orchestrator.
*   **Complexity:** Medium. Requires a new `/templates/` folder and template engine logic.
*   **Est. Build Time:** 10-12 hours.
*   **Verification:** Correct variable interpolation across Cisco/Juniper syntaxes.

---

### 6. Live Config "Diff" Viewer
*   **Rank:** 6
*   **Reasoning:** Visualize precisely what changed on a device. Side-by-side highlighting of the current `running-config` vs the `pre-change` backup.
*   **Impact:** **MEDIUM**. Essential for auditing and change verification.
*   **Complexity:** Medium. Uses Python `difflib` and a split-pane UI.
*   **Est. Build Time:** 6-8 hours.
*   **Verification:** Accurate diff highlighting for multi-thousand line configs.

---

### 7. Searchable Topology & High-Resolution Export
*   **Rank:** 7
*   **Reasoning:** Large networks create "hairball" topology maps. Adding a search box to focus on a MAC or Hostname in the Vis.js diagram is essential for troubleshooting.
*   **Impact:** **MEDIUM**. Improves the utility of the topology mapper.
*   **Complexity:** Easy. JavaScript-side filtering of the Vis.js Dataset.
*   **Est. Build Time:** 4-6 hours.
*   **Verification:** Search lag testing with 200+ nodes.

---

### 8. RBAC (Role-Based Access Control)
*   **Rank:** 8
*   **Reasoning:** As more people use the tool, we need to separate "Auditors" (Read-only) from "Engineers" (VLAN management permissions).
*   **Impact:** **MEDIUM**. Required for production compliance.
*   **Complexity:** Medium. Flask-Login integration and permission decorators.
*   **Est. Build Time:** 8-10 hours.
*   **Verification:** Unauthorized access attempt validation.

---

### 9. Excel Inventory Two-Way Sync
*   **Rank:** 9
*   **Reasoning:** Engineers live in Excel. Allowing the tool to read/write directly to `.xlsx` files for inventory management reduces data entry errors.
*   **Impact:** **LOW**. Quality of Life improvement.
*   **Complexity:** Easy. Integration with `pandas` and `openpyxl`.
*   **Est. Build Time:** 4-6 hours.
*   **Verification:** Import/Export integrity check for special characters.

---

### 10. SNMP Interface Bandwidth Monitor
*   **Rank:** 10
*   **Reasoning:** While SSH is great for configuration, SNMP is better for real-time metrics. Adding a "Mini-Dashboard" per node to show current Mbps per port.
*   **Impact:** **LOW**. Niche monitoring feature.
*   **Complexity:** High. Requires `pysnmp` and MIB management.
*   **Est. Build Time:** 12-15 hours.
*   **Verification:** Metric accuracy verification against SNMP Walk.

---

## Council refresh — 2026-06-10 (v7.0.31)

**Source:** [`NEXT-STEPS-COUNCIL-2026-06-10.md`](../13-bug-reports/03-team-contributions/NEXT-STEPS-COUNCIL-2026-06-10.md) (W-NEXT-STEPS)

**State:** Bug backlog clear · pytest 155/155 · enterprise QA gate · offline EXE v7.0.31 shipped.

### Do now (Top 3)

| ID | Initiative | Est. |
|----|------------|------|
| **NEXT-001** | Live SSH lab profile (`NST_LIVE_SSH=1` integration tests) | 4–6h |
| **NEXT-002** | Bare EXE field smoke script (`scripts/exe_field_smoke.py`) | 3–4h |
| **NEXT-003** | Credential UX fixes (force overwrite, tab refresh, tests) | 2–3h |

### Next sprint

| ID | Initiative | Est. |
|----|------------|------|
| **NEXT-004** | Full `/ui-ux-audit` (Swiss Tools polish) | 6–8h |
| **NEXT-005** | Parallel device execution (`ThreadPoolExecutor` in adapters) | 8–12h |
| **NEXT-006** | Topology / discovery map search & focus | 4–6h |

### Backlog / defer

- **NEXT-007** Config drift rollback UI
- **NEXT-008** CODE_INVENTORY truth pass
- **NEXT-009** Command center registry sync (`REBUILD_CREDENTIALS`, enterprise QA)
- **NEXT-010** Legacy IOS encryption (defer until field sample)

### Supersedes note

Ranks 1–10 above remain historical context. **NEXT-005** aligns with old Rank 1 (parallel execution). **NEXT-004/006** align with UX/map items. React rewrite (old Rank 4) **deferred** per council — stay on offline Flask/Jinja2 stack.
