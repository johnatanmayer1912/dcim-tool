# Network Swiss Tool Pro - Parsing Workflows

| Metadata | Description |
| :--- | :--- |
| **Purpose** | Detailed documentation of regex-based and structured parsing logic for network CLI output. |
| **Scope** | VLAN parsing, neighbor discovery (CDP/LLDP), vPC telemetry, and interface status extraction. |
| **Related Documents** | [Backend Architecture](../01-architecture/backend-architecture.md), [Cisco Automation](cisco-automation.md) |
| **Update Responsibility** | Network Automation Engineer / Regex Specialist |
| **Version Awareness** | v6.9.5 |

---

## Overview

The platform relies on a sophisticated multi-stage parsing engine to transform raw CLI text into structured JSON data. This document outlines the primary regex patterns and logic flows used across different modules.

## 1. VLAN Parsing Logic

### Cisco IOS/NXOS Standard
Matches standard `show vlan brief` output.
- **Pattern:** `^(\d+)\s+([\w-]+)\s+([\w-]+)`
- **Example:** `100   VLAN0100   active`

### Juniper ELS (Enhanced Layer 2 Software)
Matches `show vlans` output on modern Junos devices.
- **Pattern:** `^\S+\s+([\w-]+)\s+(\d+)`
- **Example:** `default   VLAN-Name   100`

### Juniper Legacy
Matches `show vlans` on older Junos devices.
- **Pattern:** `^([\w-]+)\s+(\d+)`
- **Example:** `VLAN-Name   100`

## 2. Neighbor Discovery (Topology)

### CDP Detail Parsing (Cisco)
The `topology_mapper.py` uses a state-machine parser to extract:
- **Local Interface:** `^Device ID: (.*)` triggers a new block.
- **Remote Hostname:** Extracted from `Device ID`.
- **Remote Interface:** `^Interface: (.*),  Port ID \(outgoing port\): (.*)`

### LLDP Detail Parsing (Juniper/Multi-vendor)
- **Local Port:** `^Local Interface: (.*)`
- **Remote System:** `^System Name: (.*)`
- **Remote Port:** `^Port ID: (.*)`

## 3. vPC Telemetry (NX-OS)

Structured parsers in `modules/topology_mapper.py`:

| Function | CLI source | Output |
|----------|------------|--------|
| `_parse_vpc_full` | `show vpc`, `show vpc brief`, `show vpc peer-link` | `vpc_structured` with `vpc_table[]`, role, keepalive, peer-link Po |
| `_parse_vpc_brief_table` | `show vpc brief` (fallback) | Rows when main `show vpc` table is empty |
| `_parse_port_channel_summary_nxos` | `show port-channel summary` | `port_channel_detail` with physical `members[]` |
| `_parse_lacp_neighbors_nxos` | `show lacp neighbor` | LACP partner map per Po |

Post-collection merge in `modules/adapters.py`:

- `_build_vpc_member_interfaces(member, meta)` — per-switch list of vPC IDs, port-channels, and physical member interfaces for the HTML sidebar and diagnostic JSON.
- `_build_html_presentation_payload(nodes, edges, map_mode)` — flattened structure matching the UI (`member_interfaces_by_switch`, `consistency_tables`, `graph_edges`).

## 4. Description Search (search_it — v6.9.5)

Module: `modules/description_search.py`  
Action: `description_search`

- Runs `show interfaces description` on each target device
- NX-OS also scans `show port-channel summary` for Po descriptions
- Match rule: **case-insensitive substring** (any position in description text)
- Output: `description_search_{term}_{timestamp}.txt`

## 5. Interface Status & Descriptions

### Multi-Strategy Parser
To handle variations in `show interfaces description` output, the system uses a fallback chain:
1. **Full Regex:** Matches standard tabular headers.
2. **Simplified Regex:** Matches if headers are missing.
3. **Tab-Split Fallback:** Splitting by whitespace if regex fails.

## Best Practices for Parser Maintenance
1. **Test with Raw Output:** Always keep raw CLI samples in the `tests/` directory for regression testing.
2. **Handle Case Sensitivity:** Use `.lower()` on interface names before comparison.
3. **Normalization:** Always use `utils.network_base.norm_int()` to ensure `GigabitEthernet0/1` matches `Gi0/1`.
