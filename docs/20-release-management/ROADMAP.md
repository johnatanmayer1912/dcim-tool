# Network Swiss Tool Pro - Future Features Roadmap

## Overview
As part of the `v5.2.0` codebase audit and transition into an enterprise-grade operational status, the following 5 features have been formally proposed to vastly improve functionality, visibility, and the overarching UX of the network devices.

### 1. Interactive Visual Config Diff Engine (UX & Functionality)
**Feature description:** 
An overarching "Diff View" alongside the Config Backup logic. When comparing the current running configuration against yesterday's backup (or standard templates), the Web UI will display a side-by-side, visually-colored output highlighting additions (`+` Green) and deletions (`-` Red).
**Benefit:** 
Provides immediate visual compliance tracking without having to leave the interface, imitating Git diffing workflows.

### 2. Real-Time Node Metrics Polling (Visibility & Monitoring)
**Feature description:** 
Use SNMP or headless CLI interactions to actively ping back real-time parameters from the switches upon dashboard load. Displays visual bars containing "CPU %" and "Interface Utilization".
**Benefit:** 
Evolves the platform from a static interaction suite to a 'live monitoring' tier zero dashboard for operators.

### 3. IP-Range Sweep / Subnet Mapper (Functionality)
**Feature description:** 
A subnet mapping tab allowing users to define a `/24` Subnet CIDR block. The system will inherently ping-sweep the range, scrape the device's ARP cache via CLI, and dynamically chart which IP assignments are "Active", "Unassigned", or "Blocked/Filtered".
**Benefit:** 
Significantly simplifies IPAM workflows and gives rapid visibility into endpoint populations on isolated networks.

### 4. Mandatory Access Control Audits (Security Compliance & UX)
**Feature description:** 
An automated "Compliance Core" scanning logic taking the running config and cross-referencing it with approximately 10 standard InfoSec hardening rules:
*   e.g. `transport input ssh` (no telnet allowed)
*   e.g. `service password-encryption`
*   e.g. `no ip http server`
Devices failing the check will be flagged visually with a distinct warning icon on the application interface.
**Benefit:** 
Fully automates security compliance reporting and prevents audit findings.

### 5. Config Backup Daemon (Functionality)
**Feature description:** 
Introduce `APScheduler` or native `Threading` daemon into the existing backend to enable hands-free execution. Network Swiss Tool will routinely execute the `config_backup` logic automatically across all devices every single night (e.g. 02:00 AM) while the server is running.
**Benefit:** 
Brings the platform closer to enterprise configuration authorities such as SolarWinds or Cisco NSO, establishing a reliable archival state.
