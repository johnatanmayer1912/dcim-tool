# Repository Structure & Module Map

| Metadata | Description |
| :--- | :--- |
| **Purpose** | Definitive guide to the project's physical file layout and module organization. |
| **Scope** | Root directory, core modules, utilities, and static asset distribution. |
| **Related Documents** | [Module Breakdown](module-breakdown.md), [LIBRARIAN Mandate](../00-overview/LIBRARIAN_MANDATE.md) |
| **Update Responsibility** | LIBRARIAN / DevOps Engineer |
| **Version Awareness** | v6.9.1 (NOC Dashboard Edition) |

---

## 📂 Root Directory

The project follows a modular Python structure designed for both development flexibility and standalone packaging.

### Core Entry Points
- `vlan_checker_web.py`: Main Flask application server and WebSocket orchestrator.
- `main.py`: Unified CLI entry point for headless automation tasks.
- `vlan_checker_gui.py`: Legacy Tkinter-based desktop interface.

### Logical Directories
- `/modules`: Core business logic (Adapters, Parsers, Topology Engine).
- `/utils`: Common utility functions (Logging, Formatting, Configuration).
- `/docs`: Enterprise-grade documentation (LIBRARIAN Structure).
- `/static`: Frontend assets (JavaScript, CSS, Images).
- `/policies`: YAML-based configuration audit standards.
- `/plugins`: Dynamic automation extensions.

---

## 🧩 Module Breakdown

### 1. `/modules/`
The engine room of the platform.
- `adapters.py`: The orchestration layer. Handles threading, multi-device logic, and vPC transformation.
- `topology_mapper.py`: CDP/LLDP discovery engine with telemetry enrichment.
- `network_base.py`: Low-level SSH/Telnet connectivity (Netmiko wrappers).
- `mac_trace.py`: CAM table search logic across multiple platforms.
- `vlan_audit.py`: VLAN database collection and analysis.

### 2. `/utils/`
Cross-cutting concerns and helper functions.
- `report_formatter.py`: HTML/CSV generation logic for all reports.
- `structured_logger.py`: Thread-safe, colorized logging system.
- `config_backup_system.py`: Multi-threaded configuration retrieval and versioning.

### 3. `/static/` & `/modules/web/templates/`
The presentation layer.
- `index.html`: The NOC Dashboard frontend (Apple Hi-Tech design).
- `vis-network.min.js`: Locally embedded topology rendering engine (v6.9.1+).
- `xterm.js`: Browser-based CLI terminal emulator.

---

## 🔄 Data Lifecycle

1.  **Ingestion**: `inventory.txt` is parsed by `network_base`.
2.  **Execution**: `adapters.py` spawns threads to run tasks (e.g., `topology_mapper`).
3.  **Transformation**: Raw CLI output is converted to structured JSON by specialized parsers.
4.  **Presentation**: `report_formatter` converts JSON to interactive HTML/CSV.

---
**Status:** VALIDATED
**Last Updated:** 2026-05-14
