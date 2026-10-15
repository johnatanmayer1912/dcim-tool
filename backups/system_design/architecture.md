# System Architecture Snapshot

## Overview
The Network Swiss Tool Pro has evolved from a series of monolithic scripts into a modular, decoupled architecture. This design pattern separates the User Interface (UI), Business Logic, and Network Interaction layers.

## Component Responsibilities

### 1. User Interface (UI)
- **Files**: `vlan_checker_gui.py` (Desktop), `vlan_checker_web.py` (Web).
- **Responsibility**: Capture user parameters (auth, target items), manage session state, and display real-time logs/results.
- **Dependency**: Must only interact with the `Adapter Layer`.

### 2. Adapter Layer (Orchestration)
- **File**: `modules/adapters.py`.
- **Responsibility**: Centralized task workflow management. It receives high-level requests from the UI (e.g., "Run VLAN Audit on these 50 switches") and coordinates the loop, calling feature modules and delegating file I/O to the `Report Formatter`.

### 3. Feature Modules (Networking Logic)
- **Directory**: `modules/`.
- **Files**: `connectivity.py`, `vlan_audit.py`, `mac_trace.py`, `topology_mapper.py`, `network_audit.py`, etc.
- **Responsibility**: Pure network interaction. They accept a single device dictionary and credentials, execute vendor-specific CLI commands (Cisco/Juniper), parse the results, and return a standardized JSON object.

### 4. Core Essentials (Foundational Logic)
- **File**: `modules/network_base.py`.
- **Responsibility**: Connection management (`connect_permissive`), shared parsing utilities (`parse_vlan_output`), and data structure builders (`build_json`).

### 5. Utility Layer (Side Effects)
- **Directory**: `utils/`.
- **Files**: `report_formatter.py` (File I/O), `backup_util.py` (Project Zipping).
- **Responsibility**: Writing reports to disk, creating HTML/CSV files, and handling data persistence.

## Execution Flow
1. **Trigger**: User initiates an action in the UI.
2. **Routing**: UI logic calls a function in `modules/adapters.py` within a background thread.
3. **Looping**: The Adapter iterates through the target device list.
4. **Execution**: For each device, the corresponding `modules/*.py` is called.
5. **Collection**: Results are aggregated into structured JSON.
6. **Persistence**: `utils/report_formatter.py` writes the final report.
7. **Feedback**: Completion status is pushed back to the UI log area.
