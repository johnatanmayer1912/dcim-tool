# Bug report — BUG-0001

| Field | Value |
|-------|-------|
| **ID** | BUG-0001 |
| **Title** | Documentation version-awareness drift vs 6.9.25 |
| **Severity** | Medium |
| **Priority** | P2 |
| **Owner** | Documentation Steward |
| **Status** | **closed** (v6.9.26) |
| **Found** | 2026-05-31 |
| **Closed** | 2026-05-31 |

## Description

Several hub documents still reference older releases (v6.9.1, v6.9.10, v6.9.22) or old EXE names while `VERSION` is **6.9.25**.

## Examples

| File | Stale reference |
|------|-----------------|
| `docs/README.md` footer | Synchronized (v6.9.22) |
| `docs/00-overview/walkthrough.md` | v6.9.1, `dist_package_v6.9.1/`, `NetworkSwissToolPro_v6.9.1.exe` |
| `docs/00-overview/roadmap.md` | v6.9.1 |
| `docs/08-operations/search-it-workflow.md` | v6.9.10 |
| `docs/13-master-prompts/PROMPT_REGISTRY.md` | Application sync 6.9.22 |
| `docs/11-release-management/README.md` (Web row) | Port 5000 / old exe name in places |

## Impact

Wrong deployment instructions; operators may run outdated EXE; AI agents resync to stale version.

## Reproduction

Grep `docs/` for `6.9.1`, `6.9.22`, `v6.9.10` and compare to `VERSION`.
