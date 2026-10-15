# External Inspirations & References

This document logs external projects and methodologies that have inspired or been integrated into the Network Management Tool cartography/mapping capabilities.

## 1. Secure Cartography
- **Repository**: [https://github.com/scottpeterman/secure_cartography](https://github.com/scottpeterman/secure_cartography)
- **Author**: Scott Peterman
- **Integration Context**: 
  - The offline multi-protocol (SSH + SNMP fallback) device parsing logic inspired the two-pass device discovery methodology in this tool.
  - The Layer 2 topology mapping (utilizing LLDP/CDP and MAC tracing) is heavily based on the graph strategies implemented here.
  - *Note: NIST comparative features from the original project were purposefully omitted based on project requirements.*

## 2. Netdisco
- **Repository**: [https://github.com/netdisco/netdisco](https://github.com/netdisco/netdisco)
- **Integration Context**:
  - Netdisco's approach to compiling comprehensive Layer 3 routing maps and ARP data inspired the advanced Layer 3 visualization capabilities in our offline UI.
  - The separation of inventory modeling (database-agnostic) from view rendering (UI maps) was adapted to allow Python to statically generate map models that run completely offline in our single-executable setup.

These repositories were referenced as part of the v7.x advanced cartography overhaul.

## Implementation (v7.0.64+)

| Feature | Module | Inspiration |
|---------|--------|-------------|
| L3 Routing Map | `modules/l3_topology_runner.py`, `utils/l3_map_shell.py` | Netdisco routing inventory |
| Network Flow Map | `build_flow_topology_bundle()` | Netdisco gateway/ARP flow model |
| Advanced L2 Map | `modules/discovery/advanced_mapper.py` | Secure Cartography L2 enrichment |
| Route parsing | `modules/routing_analyzer/` | Multi-vendor TextFSM + regex fallback |

Operator entry: **Swiss Tools → Advanced L2 / L3 / Network Flows** (web UI only).

Sources (future reference):

- https://github.com/scottpeterman/secure_cartography
- https://github.com/netdisco/netdisco
