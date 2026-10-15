# Network Swiss Tool Pro — Quick Walkthrough

| Field | Value |
|-------|-------|
| **Purpose** | Fast orientation for Web Edition and plugin platform |
| **Version Awareness** | **v7.0.51** |
| **Last Updated** | 2026-06-18 |
| **Last Updated** | 2026-06-10 |

---

## Deployment (offline)

1. **Artifact:** `dist/NetworkSwissToolPro_v7.0.51_OFFLINE.exe`
2. **Inventory:** `inventory.txt` beside the EXE
3. **Launch:** Double-click EXE → browser opens `http://127.0.0.1:5051`

---

## Initial setup

### Inventory
```text
[CoreSwitches]
10.1.1.1,cisco_nxos,CoreSwitches

[AccessLayer]
10.2.1.1,cisco_ios,AccessLayer
```

### Credentials (sidebar)
- SSH user/password, enable password (Cisco), port 22

---

## Feature navigation

| Area | Tab / action |
|------|----------------|
| Connectivity | Sidebar targets + ping/connect |
| Network Search | MAC trace, description search, ping scan |
| Discovery | Crawl + [Discovery Command Center](../07-operations/discovery-command-center-guide.md) |
| Topology / vPC | Maps + [VPC Command Center](../07-operations/vpc-command-center-guide.md) |
| Plugins | Plugin Tools → reload registry → run |
| CLI | Terminal tab (WebSocket SSH) |

---

## Troubleshooting

- **Server offline:** Check console / logs beside EXE
- **Plugins empty:** See [exe-smoke-checklist.md](../07-operations/exe-smoke-checklist.md) (NEW-C1 bundled path)
- **Errors:** [TS_ERROR_INDEX.md](../07-operations/TS_ERROR_INDEX.md)

---

## Next steps

- [network-search-workflow.md](../07-operations/network-search-workflow.md)
- [mac-trace-howto.md](../07-operations/mac-trace-howto.md)
- [docs/README.md](../README.md)
