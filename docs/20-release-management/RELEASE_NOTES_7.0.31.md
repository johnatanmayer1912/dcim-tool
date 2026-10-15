# Release Notes — v7.0.31

**Date:** 2026-06-10  
**Artifact:** `dist/NetworkSwissToolPro_v7.0.31_OFFLINE.exe`

## Highlights

- **Enterprise QA gate:** `python scripts/enterprise_qa_gate.py` — 155 pytest, prebuild, doc links, frozen plugin sim.
- **Offline lab smoke:** IOS-XE MAC (colon → dotted CAM) and QFX5100 Junos LLDP/MAC fixtures with mock SSH.
- **Topology:** Port-aware `_topology_edge_link_key` keeps parallel links on distinct ports.
- **Documentation:** 0 broken internal markdown links under `docs/`.

## Platform support (offline + live)

| Vendor | Families | Notes |
|--------|----------|-------|
| Cisco | IOS, IOS-XE, NX-OS | CDP/LLDP, MAC dotted format, vPC |
| Juniper | Junos (EX, QFX, SRX) | LLDP brief-first, `xe-`/`ge-`/`ae`, Junos 14+ MAC table layouts |

## Validation

```
python scripts/enterprise_qa_gate.py
```

Expected: **ENTERPRISE QA GATE: PASS**
