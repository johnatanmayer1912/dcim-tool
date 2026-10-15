# QA Test Protocol: vPC Topology (v6.6.0 Premium Pass)

## Overview
This protocol validates the high-fidelity vPC topology visualization introduced in v6.6.0, focusing on peer-clustering, edge styling, and the intelligence dashboard.

## Test Environment
*   **Inventory:** At least 2 Nexus switches configured in a vPC domain.
*   **Connectivity:** Both switches reachable via SSH.

## Section 1: Data Acquisition
1.  **Run Topology Mapper:** Select "vPC Mode" and run discovery.
2.  **Verify Backend Extraction:**
    *   Check `logs/operations.log` for successful `show vpc` execution.
    *   Confirm `vpc_domain_id` is parsed correctly for both peers.

## Section 2: Visual Layout (The Premium Pass)
1.  **Node Clustering:**
    *   [ ] Do peer switches appear side-by-side automatically?
    *   [ ] Verify `vis.Network` groups match the vPC domain ID.
2.  **Peer-Link Styling:**
    *   [ ] Is the peer-link deep purple (`#a55eea`)?
    *   [ ] Is the width set to 10px?
    *   [ ] Is the shadow/glow effect visible?
3.  **Member Link Styling:**
    *   [ ] Are links from vPC peers to downstream devices orange (`#ff7f50`)?
    *   [ ] Is the width set to 8px?
    *   [ ] Does the glow effect appear when hovering?

## Section 3: Diagnostic Export (v6.9.4+)
1.  **Folder Creation:**
    *   [ ] After vPC map generation, `topology_diagnostics_*` folder exists in the app working directory.
    *   [ ] `00_README.txt` explains each file.
2.  **Member Interface Data:**
    *   [ ] `01_raw_node_metadata.json` → each NX-OS peer has `vpc_member_interfaces` with `entries[]`.
    *   [ ] `06_pre_render_presentation.json` → `member_interfaces_by_switch` is populated.
3.  **HTML Sidebar:**
    *   [ ] Click `VPC_Domain_*` → "Member Interfaces & vPCs" lists local ports per switch (not empty when vPCs exist).
    *   [ ] Consistency table shows rows when `vpc_structured` was collected.

## Section 4: Intelligence Dashboard (Side-Panel)
1.  **Aesthetics:**
    *   [ ] Does the panel use the Slate theme (`#1e293b` background)?
    *   [ ] Is `backdrop-blur: 8px` active?
    *   [ ] Is the Inter font applied to all text?
2.  **Data Integrity:**
    *   [ ] Does the vPC summary table list all member Port-Channels?
    *   [ ] Are "Up" statuses highlighted in green and "Down" in red?
    *   [ ] Does the summary correctly identify the Peer-Link status?

## Section 5: Automated Validation (v6.9.4+)

```powershell
python tests/validate_vpc_member_interfaces.py
```

Expected: `RESULT: ALL CHECKS PASSED` (exit code 0).

## Section 6: Engineering Board (v6.9.27+)

1.  **Default tab:**
    *   [ ] HTML opens on **Engineering Board** (not the graph).
    *   [ ] `window.__VPC_BOARD__` present in page source.
2.  **Board content (no graph click required):**
    *   [ ] Domain dropdown lists all `VPC_Domain_*` IDs.
    *   [ ] Peer strip shows hostname, role, peer-link Po, peer status, keepalive.
    *   [ ] vPC table lists Port-Channels with members when collected.
    *   [ ] **Global Consistency Parameters** shows CLI excerpt when `show vpc consistency-parameters global` was captured.
3.  **Simplified Map tab:**
    *   [ ] Physics off — no stabilization jitter on load.
    *   [ ] Non-vPC links hidden by default; toolbar toggle shows them.
    *   [ ] Peers + domain readable at 1280×768.
4.  **Offline / print:**
    *   [ ] Open saved HTML with no internet; board renders.
    *   [ ] Print preview shows tables (Board tab).

## Section 7: Regression
1.  **Standard Mode:** Switch to "Standard" mode; verify vPC styling is removed but connectivity remains.
2.  **Missing Data:** Run on a non-vPC environment; verify the dashboard handles empty vPC data gracefully (no crashes).

---
**Sign-off:** ___________________  **Date:** ___________
