# 14-Roadmap — Disaster Recovery

| Field | Value |
|-------|-------|
| **Version** | 2.0.0 |
| **Status** | active |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-10 |
| **Application Version** | 7.0.51 |

## When to use this folder

**Scenario:** All source code is lost. Only the `docs/` folder (and optionally `VERSION`, `CHANGELOG.md`) survives.

**Goal:** Rebuild Network Swiss Tool Pro **1:1** using AI IDE prompts in controlled batches — **without overloading the IDE** (no 42-prompt DDOS).

---

## Start here (read order)

| # | Document | Purpose |
|---|----------|---------|
| 1 | [`00-RECONSTRUCTION_INDEX.md`](00-RECONSTRUCTION_INDEX.md) | Phases, dependencies, success criteria |
| 2 | [`DISASTER_RECOVERY_COMMAND.md`](DISASTER_RECOVERY_COMMAND.md) | **Copy-paste batch commands** for IDE |
| 3 | [`SYNC_PROTOCOL.md`](SYNC_PROTOCOL.md) | Code path → doc + prompt mapping (keep updated on every code change) |
| 4 | Phase `00-PROMPT-INDEX.md` files | Prompts within each phase |

**Role:** `docs/12-master-prompts/roles/combined/ROLE_PROGRAM_RECONSTRUCTOR_USAGE_PROMPT.md` (R-RECON)

---

## Quick command (IDE)

Type in chat:

```
rebuild from docs — execute docs/14-roadmap/DISASTER_RECOVERY_COMMAND.md Batch 1 only
```

Then Batch 2, 3, … after validating each batch. **Never send all batches at once.**

---

## Maintenance rule (hardcoded)

**Every code change** MUST update this folder per `SYNC_PROTOCOL.md`. This is integrated into:

- `PROMPT_COMMAND_CENTER.md` (G-CC)
- `CODE_CHANGE_DOCUMENTATION_UPDATE_PROCEDURES.md` (PROC-CCDU)
- `GLOBAL_MASTER_PROMPT_RULES.md` (G-18 rules 21–23)
- `roles/_MANDATORY_SYNC_FOOTER.md`

Responsible: **R-RECON** (prompts) + **R-LIB** (ongoing docs) on every R-ENG delivery.

---

## Phase overview (42 prompts)

| Phase | Folder | Prompts | Time (est.) |
|-------|--------|---------|-------------|
| 1 Foundation | `01-foundation/` | P01–P04 | 30 min |
| 2 Core modules | `02-core-modules/` | P05–P08 | 30 min |
| 3 Plugins | `03-plugins/` | P09–P11 | 45 min |
| 4 Web UI | `04-web-interface/` | P12–P15 | 45 min |
| 5 Utilities | `05-utilities/` | P16–P18 | 30 min |
| 6 Integration | `06-integration/` | P19–P21 | 30 min |
| 7 Testing | `07-testing/` | P22–P24 | 30 min |
| 8 Deployment | `08-deployment/` | P25–P27 | 30 min |
| 9 Validation | `09-validation/` | P28–P30 | 30 min |
| 10 Documentation | `10-documentation/` | P31–P33 | 30 min |
| 11 Optimization | `11-optimization/` | P34–P36 | 30 min |
| 12 Troubleshooting | `12-troubleshooting/` | P37–P39 | 30 min |
| 13 Finalization | `13-finalization/` | P40–P42 | 30 min |

**Supporting truth (not prompts):** `docs/02-codebase/CODE_INVENTORY.md`, `MODULE_ARCHITECTURE.md`, `API_DOCUMENTATION.md`
