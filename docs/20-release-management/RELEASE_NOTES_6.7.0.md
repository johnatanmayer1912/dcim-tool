# Release Notes - v6.7.0 (Premium Edition)

**Release Date:** 2026-05-04
**Type:** Feature Update & Major Architectural Fixes

## 🚀 Executive Summary
Version 6.7.0 delivers a complete overhaul of the vPC and logical topology visualization engine, transforming complex switch pairs into unified logical domains. It also introduces dynamic interface description integration natively within the graph, allowing engineers to visualize exactly what is physically connected over an edge without performing secondary queries.

## ✨ New Features
*   **vPC Topology Consolidation:** The network graph now intelligently identifies vPC peer nodes via `vpc_domain_id` attributes. These members are visually grouped and abstracted into a singular `VPC_Domain` node for clarity.
*   **Redundancy Path Visualization:** Shared links going to dual-homed downstream devices are cleanly merged into a single thick blue `vpc_shared` line, while single-homed links are aggressively flagged as dashed red `vpc_orphan` links to easily identify non-redundant paths.
*   **Interface Description Native Mapping:** The topology generator now intercepts and renders port descriptions inside edge tooltips. A dedicated "Show Descriptions" button has been added to toggle descriptions natively across all physical edge labels.

## 🛠️ Enhancements & Fixes
*   **CLI WebSocket State Machine:** Fixed a race condition where the CLI terminal UI would get permanently stuck on "Connecting" due to duplicate SID/Room emissions.
*   **Legacy vPC Pair De-cluttering:** Removed the older "domain-matched" peer connection logic which polluted maps with redundant crossover links.
*   **Orphan Node Data Models:** Ensured that consolidated vPC domain nodes possess aggregated node_metadata, preventing frontend UI crashes during hover interactions.

## ⚠️ Breaking Changes
*   **Plugin Topology Payloads:** Plugins generating CDP/LLDP topology output must now ensure `desc` (interface description) and `vpc_domain_id` are included in the metadata payloads to correctly interface with the v6.7.0 parsing abstractions.

## 🔄 Upgrade Path
There are no database migration steps as the platform uses stateless JSON execution files. Simply replace the previous executable with `NetworkSwissToolPro_v6_7_0.exe`. Ensure you copy over any persistent `inventory.txt` files if upgrading a standalone bundle.
