# PROMPT_MIGRATION_SYNC

| Field | Value |
|-------|-------|
| **Version** | 3.0.0 |
| **Status** | active |
| **Owner** | Prompt Governance Framework |
| **Registry ID** | G-16 |
| **last_updated** | 2026-05-31 |

**Owner role:** Prompt Librarian (U-GOV-LIB) · **Authority:** `PROMPT_GOVERNANCE_POLICY.md` (G-03) · **Archive:** `archive/platform-prompts-original/`

## Purpose

Define how prompts are migrated and synchronized without losing history.

---

## Rules

1. **Never delete** source prompts (`docs/02-codebase/PLATFORM_PROMPTS/`).
2. **Never overwrite** source prompts in place.
3. **Copy first, enhance second** (archive → master hub → optional forward sync only when approved).
4. **Preserve original intent** — forward sync; document deltas.
5. **Add** clarity, governance, and operational detail in master copies and usage guides.
6. **Keep older versions available** (archive folder + registry change log + prior registry version notes).
7. **Log every change** in `PROMPT_REGISTRY.md` (change log) and `action-logs/`.
8. **Keep source-to-master traceability** (`source_prompt` field, `prompt_id` linkage).

---

## Migration workflow

Use when introducing or formally adopting a platform prompt into the master hub.

| Step | Action | Artifact |
|------|--------|----------|
| 1 | Read original prompt | `docs/02-codebase/PLATFORM_PROMPTS/<file>.md` |
| 2 | Copy into master hub | `docs/13-master-prompts/archive/platform-prompts-original/<file>.md` (verbatim) |
| 3 | Create or update registry entry | `PROMPT_REGISTRY.md` — all 12 required fields |
| 4 | Create usage guide | `docs/13-master-prompts/roles/<ROLE>_USAGE.md` per `ROLE_USAGE_STANDARD.md` (G-14) |
| 5 | Enhance the prompt while preserving intent | Master copy in `roles/` or documented enhancement plan; **do not** replace archive |
| 6 | Add action log requirements | `action-logs/`, G-14 / G-15 logging fields |
| 7 | Add role dependencies | Registry `dependencies`, `used_with`; `ROLE_MATRIX.md` if new role |
| 8 | Validate against policies | G-03, G-06, G-07, G-13, G-14, G-15 as applicable |
| 9 | Mark version and status | Registry `version`, `status` (`draft` → `active`) |
| 10 | Preserve prior versions | Archive snapshot date in registry `notes`; registry change log row |

**Enhancement location:** Prefer usage guides + registry over editing `PLATFORM_PROMPTS/` unless explicitly approved for forward sync.

---

## Sync workflow

When a **source** prompt changes after initial migration:

| Situation | Action |
|-----------|--------|
| Source file edited | Copy new verbatim snapshot to archive (or dated subfolder if policy evolves); diff against prior archive |
| **Behavioral** change | Registry **major** or **minor** version; update usage guide; CHANGELOG; re-validate gates if runtime tied |
| **Clarifying** change | Registry **patch**; update `notes`; usage guide tweak |
| Deprecation | `status`: `deprecated` → `retired`; migration notes; successor `prompt_id` |

**Never:**

- Remove historical context from registry change log.
- Hide old behavior without explicit deprecation (`notes` + TEAM_MEETING if controversial).

**Forward sync to `PLATFORM_PROMPTS/`:** Only with explicit approval; still retain archive of pre-sync state.

---

## Output requirements

Every migration or sync event MUST record:

| Output | Location |
|--------|----------|
| **Source prompt referenced** | Registry `source_prompt`; action log path |
| **Master prompt updated** | Path under `docs/13-master-prompts/` (usage guide, policy, or enhancement doc) |
| **Usage guide updated** | `roles/*_USAGE.md` |
| **Registry updated** | `PROMPT_REGISTRY.md` entry + change log |
| **Compatibility impact recorded** | Action log + CHANGELOG if user-facing; G-08 artifact |
| **Rollback path noted** | Revert archive/registry row; restore prior usage guide from git |

### Governance action log (U-GOV-LIB)

Include from `PROMPT_GOVERNANCE_POLICY.md`:

- governance concern reviewed  
- prompt risk identified  
- policy affected (G-16, G-03, …)  
- decision made  
- remaining risk  

### Migration/sync action log template

`action-logs/YYYY-MM-DD_migrate-<prompt_id>.md`:

```markdown
# Migration/Sync — <prompt_id>

**Source:** docs/02-codebase/PLATFORM_PROMPTS/<file>
**Archive:** archive/platform-prompts-original/<file>
**Registry version:** X.Y.Z → X.Y.Z
**Sync type:** migration | forward-sync | patch

## Compatibility impact
-

## Rollback path
-

## Steps completed (1–10)
-
```

---

## Path reference (this repository)

| Layer | Path |
|-------|------|
| Source (immutable) | `docs/02-codebase/PLATFORM_PROMPTS/` |
| Archive | `docs/13-master-prompts/archive/platform-prompts-original/` |
| Usage guides | `docs/13-master-prompts/roles/` |
| Registry | `docs/13-master-prompts/PROMPT_REGISTRY.md` |

---

## Escalation

- Source vs master intent conflict → `ESCALATION_MATRIX.md` **Prompt drift** (U-GOV-LIB + U-LIB → Team Meeting).
- Behavioral sync affecting runtime → U-ARCH, U-QA, U-REL per change class.

---

## Success criteria

- [ ] Source prompt intact and referenced  
- [ ] Archive copy current or dated  
- [ ] Registry entry complete; change log updated  
- [ ] Usage guide exists or draft row tracked  
- [ ] All six output requirements documented in action log  
- [ ] No silent removal of historical behavior  

---

## Index linkage

`INDEX_PROMPT.md` Phase A §7 — read with `PROMPT_GOVERNANCE_POLICY.md` before prompt migration work.
