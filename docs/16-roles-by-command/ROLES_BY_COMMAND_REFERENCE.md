# Roles by Command Reference

| Field | Value |
|-------|-------|
| **Document ID** | CMD-REF |
| **Owner** | R-LIB + R-GOV-LIB |
| **Status** | active |
| **Last Updated** | 2026-06-10 |
| **Version** | 3.0.0 |
| **Application Version** | 7.0.29 |
| **HTML Manual** | [COMMAND_MANUAL.html](COMMAND_MANUAL.html) — offline command book |

## Purpose

Authoritative **what to type** reference. Each command activates **all listed roles** automatically.

**Detail:** [`PROMPT_COMMAND_CENTER.md`](../13-master-prompts/PROMPT_COMMAND_CENTER.md) · **Workflow files:** `docs/13-master-prompts/roles/`

---

## How to use

1. Type the command in Cursor chat (natural language or `/slash` form).
2. AI loads workflow file + all roles in **Activates** column.
3. Wait for deliverables; use **Copy prompt** blocks from output or HTML manual.

---

## Tier 1 — Mega-commands (holistic / council)

| Command | Workflow | Roles | Output |
|---------|----------|-------|--------|
| **`/full-docs-sync`** · `full docs sync` | [FULL_DOCS_SYNC.md](../13-master-prompts/roles/FULL_DOCS_SYNC.md) | GOV-LIB, LIB, RECON, ARCH, QA, REL | Complete doc + rebuild + registry parity; link validation |
| **`/find-all-bugs-and-fix`** · `find all bugs and fix` | [FIND_ALL_BUGS_AND_FIX.md](../13-master-prompts/roles/FIND_ALL_BUGS_AND_FIX.md) | **All council** | Sweep report + severity table + per-bug fix prompts + **FIX-ALL-CONSOLIDATED-PROMPT.md** |
| **`/ui-ux-audit`** · `ui ux check` | [UI_UX_AUDIT.md](../13-master-prompts/roles/UI_UX_AUDIT.md) | PROD, ENG, QA, ARCH, LIB, OBS, COUNCIL | PC/offline UX report + fix prompts (1024px+, no mobile) |
| **`/next-steps`** · `what are the next steps` | [NEXT_STEPS_COUNCIL.md](../13-master-prompts/roles/NEXT_STEPS_COUNCIL.md) | **All council** | NEXT-* roadmap: decision, why, complexity, **implementation prompts** |
| **`/find-all-bugs-and-fix` auto** | Same + "auto proceed" | All → ENG chain | Finds + fixes in priority order until green tests |

---

## Tier 2 — Quality & ship

| Command | Roles | Output |
|---------|-------|--------|
| `check system for bugs` / `/check-system-bugs` | All council | [CHECK_SYSTEM_FOR_BUGS.md](../13-master-prompts/roles/CHECK_SYSTEM_FOR_BUGS.md) — find only |
| `/code-review-doc-sync` | ARCH→ENG→QA→LIB | Review + architecture + tests + docs |
| `/full-fix-and-ship [desc]` | ARCH→ENG→QA→LIB→RECON→REL | Implement + test + doc + optional release |
| `/release-vX.Y.Z` | REL, QA, LIB, RECON, ENG | VERSION, CHANGELOG, EXE |
| `execute fix all from latest bug sweep` | ENG→QA→LIB | Runs `04-fix-workflow/FIX-ALL-CONSOLIDATED-PROMPT.md` |

---

## Tier 3 — Development

| Command | Roles | Output |
|---------|-------|--------|
| `implement [feature]` | ARCH, ENG, QA, LIB, RECON | Code + mandatory doc sync |
| `fix bug [ID]` | ENG, QA, LIB, RECON | fix-prompt + validation |
| `validate fix [ID]` | QA, LIB | validation-prompt evidence |
| `implement NEXT-NNN` | Per NEXT_STEPS prompt | Council-approved feature |

---

## Tier 4 — Documentation & governance

| Command | Roles | Output |
|---------|-------|--------|
| `sync documentation` | LIB, GOV-LIB, RECON | Partial sync (use `/full-docs-sync` for complete) |
| `/doc-audit` | GOV-LIB, LIB, RECON | Gap analysis |
| `govern prompts` | GOV-LIB, LIB | Registry + INDEX |

---

## Tier 5 — Architecture & security

| Command | Roles | Output |
|---------|-------|--------|
| `review architecture` | ARCH, LIB | Compliance report |
| `security review` | SEC, ENG, LIB | Security findings |

---

## Tier 6 — Build & disaster recovery

| Command | Roles | Output |
|---------|-------|--------|
| `build exe` | ENG, QA, REL | `_prebuild.py` + dist EXE |
| `prepare release` | REL, QA, LIB, RECON | Release package |
| `rebuild from docs — Batch N` | RECON, ENG | [DISASTER_RECOVERY_COMMAND.md](../15-rebuild-roadmap/DISASTER_RECOVERY_COMMAND.md) |

---

## Role activation order (default)

```
RESYNC → PROD (scope) → ARCH → ENG → QA → SEC* → OBS* → LIB + RECON → GOV-LIB* → REL* → COUNCIL*
```
\* when applicable

---

## Copy-paste quick blocks

### Full docs sync
```
/full-docs-sync
Execute docs/13-master-prompts/roles/FULL_DOCS_SYNC.md — all phases, action log required.
```

### Find all bugs and fix
```
/find-all-bugs-and-fix
Execute docs/13-master-prompts/roles/FIND_ALL_BUGS_AND_FIX.md — Phase A+B+C, generate FIX-ALL-CONSOLIDATED-PROMPT.md
```

### UI/UX audit (PC offline)
```
/ui-ux-audit
Execute docs/13-master-prompts/roles/UI_UX_AUDIT.md — desktop 1024px+, offline EXE, no mobile
```

### Next steps council
```
/next-steps
Execute docs/13-master-prompts/roles/NEXT_STEPS_COUNCIL.md — 360 council, implementation prompts per NEXT-* item
```

---

## Related

- [COMMAND_MANUAL.html](COMMAND_MANUAL.html) — offline HTML manual
- [PROMPT_COMMAND_CENTER.md](../13-master-prompts/PROMPT_COMMAND_CENTER.md)
- [FINAL_OPERATING_INSTRUCTION.md](../13-master-prompts/FINAL_OPERATING_INSTRUCTION.md)
