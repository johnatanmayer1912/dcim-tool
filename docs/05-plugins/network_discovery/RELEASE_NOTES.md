# Release Notes — Network Discovery & Crawl Plugin

# Purpose
Documents the release history, key capabilities, fixed issues, and production readiness checklist for the Network Discovery & Crawl plugin.

# Scope
Covers all plugin versions, starting from v1.0.0.

# Related Documents
- [README.md](README.md)
- [CHANGELOG.md](CHANGELOG.md)

---

## v1.0.0 (2026-05-26)
### New Features
- **BFS Crawl Engine**: Implemented multi-platform neighbor crawling across Cisco IOS/NX-OS and Juniper Junos using CDP and LLDP.
- **Visual Mapping**: Automated Vis.js graph mapping, highlighting scanned nodes (blue) and discovered-only boundary nodes (slate gray).
- **Duplicate Detection**: Robust duplicate prevention matching hostname FQDNs and collected IPs.
- **Offline Mode**: Bundles raw JS payloads to allow graph execution in air-gapped systems.

### Production Readiness
- **Safety Status**: Approved for safe NOC read-only usage.
- **QA Verification**: Confirmed zero impact on running system VLAN check and compliance subsystems.
