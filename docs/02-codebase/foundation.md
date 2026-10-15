# Network Swiss Tool Pro - Foundation Guide

| Metadata | Description |
| :--- | :--- |
| **Purpose** | Documentation of the core foundation layers and base utilities of the platform. |
| **Scope** | File IO, connectivity base, shared utilities, and entry point logic. |
| **Related Documents** | [System Architecture](../01-architecture/system-architecture.md), [Exact Rebuild Procedure](../15-rebuild-roadmap/README.md) |
| **Update Responsibility** | Core Platform Developer |
| **Version Awareness** | v6.9.1 (NOC Dashboard Edition) |

---

## Core Entry Points

### `main.py`
The unified router for the platform. It handles:
- **CLI Mode:** Executes headless tasks like backups and audits.
- **Web Mode:** Launches the Flask server and opens the browser.
- **Initialization:** Sets up logs, checks inventory, and validates environment.

### `vlan_checker_web.py`
The Flask backend for the web interface.
- **Socket.IO:** Manages real-time CLI terminal streaming.
- **REST API:** Handles UI requests for audits, mapping, and management.

## Base Modules

### `modules/network_base.py`
The connectivity engine for the platform.
- **Netmiko Integration:** Standardized connection handler for Cisco and Juniper.
- **Authentication:** Handles privilege escalation (Enable password).
- **Normalization:** `norm_int()` ensures interface names are consistent across vendors.

### `utils/report_formatter.py`
The output generation engine.
- **Text Reports:** Human-readable device summaries.
- **CSV Exports:** Structured data for spreadsheet analysis.
- **HTML Visualization:** The Vis.js-powered topology rendering engine.

## Directory Structure Foundation
- `modules/`: Feature-specific logic.
- `utils/`: Shared utilities and helpers.
- `inventory.txt`: The source of truth for device targets.
- `backups/`: Configuration snapshot storage.
- `logs/`: Operational and error tracing.
- `reports/`: Final output artifacts.
