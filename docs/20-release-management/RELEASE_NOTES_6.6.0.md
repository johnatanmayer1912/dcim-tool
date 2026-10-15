# Release Notes - v6.6.0 (2026-04-30)

## Overview
v6.6.0 is a "Stabilization and Aesthetics" release focused on finalizing the vPC Topology UX and resolving persistent CLI connectivity issues for air-gapped data center environments.

## Major Enhancements

### 1. vPC Topology "Premium Pass"
*   **Logical Clustering:** Implemented `vis.Network` node grouping by vPC domain ID. This forces peer-pairs to align side-by-side on the map automatically.
*   **Architectural Edge Styling:**
    *   **Member Links:** Rendered with a high-intensity orange glow (`rgba(255,127,80,0.4)` shadow) and increased width (8px).
    *   **Peer-Links:** Maximum visibility purple lines (10px) with deeper shadow styling to emphasize the most critical link in the domain.
*   **Intelligence Dashboard:** Overhauled the vPC summary side-panel using a modern slate-based glassmorphism theme.
    *   Backdrop-blur: 8px
    *   Font: Inter / Segoe UI
    *   Structured Table: Clear separation of Device, ID, PC, and Status columns.

### 2. CLI Terminal Hardening
*   **WebSocket Optimization:** Eliminated redundant `sid`-based emits. All communication now flows strictly through the `session_id` room, preventing race conditions and duplicate character rendering.
*   **Connection Lifecycle:** Improved SSH handshake reliability with better error reporting during PTY initialization.
*   **Air-Gapped Diagnostics:** Added immediate server-side console logging for `cli_connect` events, providing instant visibility into handshake progress without checking log files.

## Technical Fixes
*   **[FIX]** Resolved "Stuck on Connecting" state by ensuring the `join_room` operation completes before the background SSH task begins.
*   **[FIX]** Standardized version reporting across all API endpoints and frontend headers.
*   **[FIX]** Hardened `adapters.py` logic to prevent attribute errors when processing partially discovered topology nodes.

## Build Information
*   **Executable:** `NetworkSwissToolPro_v6_6_0.exe`
*   **Build Script:** `build_scripts/build_v6_6_0.bat`
*   **Spec File:** `build_scripts/NetworkSwissToolPro_v6_6_0.spec`
*   **Dependencies:** Bundled (Air-Gapped Ready)
