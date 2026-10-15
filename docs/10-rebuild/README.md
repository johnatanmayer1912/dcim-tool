# Build and Rebuild Documentation

| Field | Value |
|-------|-------|
| **Version** | 2.0.0 |
| **Status** | active |
| **Owner** | Release Manager (R-REL) + R-RECON |
| **Last Updated** | 2026-06-18 |
| **Application Version** | 7.0.51 |

## Purpose

Build, install, and recovery procedures for **normal** operations.

> **Code lost — only docs remain?** Use **[`../14-roadmap/`](../14-roadmap/README.md)** (P01–P42, `DISASTER_RECOVERY_COMMAND.md`). This folder covers day-to-day build; `14-roadmap` is full 1:1 reconstruction.

---

## Documents

| Document | Purpose |
|----------|---------|
| [BUILD_PROCESS.md](BUILD_PROCESS.md) | PyInstaller build |
| [exact-rebuild-procedure.md](exact-rebuild-procedure.md) | Step-by-step rebuild (dev) |
| [from-zero-installation.md](from-zero-installation.md) | Clean install |
| [cold-start-recovery.md](cold-start-recovery.md) | Cold start |
| [offline-recovery.md](offline-recovery.md) | Offline recovery |

---

## Validation

- `python _prebuild.py` → ALL CHECKS PASSED
- [exe-smoke-checklist.md](../07-operations/exe-smoke-checklist.md)
- Spec: `NetworkSwissToolPro_v7.0.51.spec`
- Artifact: `dist/NetworkSwissToolPro_v7.0.51_OFFLINE.exe`

---

## See also

- [PROMPT_COMMAND_CENTER.md](../12-master-prompts/PROMPT_COMMAND_CENTER.md) § `build exe` / `/release-vX.Y.Z`
- [14-roadmap/SYNC_PROTOCOL.md](../14-roadmap/SYNC_PROTOCOL.md)
