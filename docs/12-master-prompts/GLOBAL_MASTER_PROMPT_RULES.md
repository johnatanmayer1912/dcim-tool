# GLOBAL MASTER PROMPT RULES

| Field | Value |
|-------|-------|
| **Version** | 4.0.0 |
| **Status** | active |
| **Owner** | Prompt Governance Framework |
| **Registry ID** | G-18 |
| **last_updated** | 2026-06-10 |

**Entry:** `INDEX_PROMPT.md` (G-00) · **Registry:** `PROMPT_REGISTRY.md` (G-01) · **Operations:** `FINAL_OPERATING_INSTRUCTION.md` (G-17) · **Sequence:** `PROMPT_EXECUTION_RULES.md` (G-15) · **Council roles:** `roles/combined/ROLE_*_USAGE_PROMPT.md`

These **24 absolute rules** bind every AI session in this repository. They do not replace role prompts or policies; they **govern** them.

---

## Absolute rules (mandatory)

1. **NEVER** delete original prompts in `docs/02-codebase/PLATFORM_PROMPTS/`.
2. **ALWAYS** copy prompts into `docs/12-master-prompts/` before enhancing.
3. **PRESERVE** original intent and historical meaning.
4. **ENHANCE** by elaborating professionally, not removing behavior.
5. **SYNC** changes forward, never replace history.
6. **KEEP** previous versions for traceability and rollback.
7. **EVERY** role prompt **MUST** have a matching usage guide (G-14).
8. **EVERY** role **MUST** include mandatory action log (`roles/_ACTION_LOG_SNIPPET.md`).
9. **EVERY** role **MUST** know dependencies (upstream and downstream) — see `ROLE_MATRIX.md` (G-04).
10. **EVERY** change **MUST** be logged (`action-logs/`, registry change log).
11. **NO** work begins before reading `INDEX_PROMPT.md` and `PROMPT_REGISTRY.md`.
12. **NO** prompt may bypass required policy reviews (documentation, QA, security, architecture, observability, release, performance) — `QUALITY_GATE_POLICY.md` (G-07).
13. **EVERY** role **MUST** resync before acting (latest docs, prompts, code, release notes, bug fixes, policies).
14. **NO** undocumented changes permitted (`DOCUMENTATION_POLICY.md`, G-06).
15. **THE AI MUST** automatically activate **ALL** relevant roles even if the user doesn't name them (G-13, G-17).
16. **IF** a role's mission is relevant, it **MUST** be loaded, read, and applied.
17. **IF** multiple roles are relevant, coordinate in **dependency order** and escalate conflicts to **Team Meeting** (R-COUNCIL / G-11).
18. **THE PROGRAM** takes only updated information from prompts and elaborates professionally on each.
19. **NEW** roles **MAY** be added, but usage instructions **MUST** update accordingly (registry, combined files, G-04).
20. **ALL** prompts **MUST** be professional, enterprise-grade, aligned with mission.
21. **EVERY** code or behavior change **MUST** update ongoing documentation **and** the rebuild roadmap (`14-roadmap/SYNC_PROTOCOL.md`) — **without** waiting for a separate doc-sync command (see `PROMPT_COMMAND_CENTER.md`, `roles/_MANDATORY_SYNC_FOOTER.md`).
22. **EVERY** implementation role (R-ENG, R-ARCH, R-QA, R-REL, etc.) **MUST** treat documentation sync as part of **done**, not a follow-up task.
23. **THE** `docs/14-roadmap/` folder **MUST** stay current with code — R-RECON + R-LIB on every meaningful merge; disaster recovery is invalid if prompts drift.
24. **USE** `PROMPT_COMMAND_CENTER.md` (G-CC) for all-in-one commands, role activation, and batch rebuild — do not invent ad-hoc orchestration.

---

## Mission

Build the most capable, maintainable, extensible, reliable, and professionally engineered **network management platform in the world**.

---

## Vision

Create an **enterprise-grade AI-assisted engineering operating system** that manages network complexity at scale, improves quality, and creates durable competitive advantage.

---

## Engineering principles

- Clarity over ambiguity
- Traceability over hidden action
- Compatibility over reckless change
- Documentation over institutional memory
- Quality over speed
- Resilience over convenience
- Collaboration over isolated execution

---

## Policy and gate map (rule 12)

| Review | Policy | Role |
|--------|--------|------|
| Documentation | G-06 | U-LIB (R-LIB) |
| QA | G-07 | U-QA (R-QA) |
| Security | G-07, G-08 | U-SEC (R-SEC) |
| Architecture | G-07, G-08 | U-ARCH (R-ARCH) |
| Observability | G-07, G-09 | U-OBS (R-OBS) |
| Release | G-09 | U-REL (R-REL) |
| Performance | G-07, G-10 | U-ENG, U-TOPO, U-ARCH |
| Product / strategy | G-10 | U-PROD (R-PROD) |

No bypass without **Team Meeting** record (G-11).

---

## Role invoke shortcuts

| Need | Combined file (`roles/combined/`) |
|------|-----------------------------------|
| Single-file role + usage | `ROLE_*_USAGE_PROMPT.md` |
| Full council list | `FINAL_OPERATING_INSTRUCTION.md` § Council roles |

---

## Version lineage

| Version | Scope |
|---------|--------|
| 3.x | Per-policy and per-role prompts (G-00–G-17, R-*, U-*) |
| **4.0** | This document — consolidated **absolute rules** for the whole hub |

When G-18 and another file conflict on an **absolute rule**, G-18 wins. For **procedure detail**, follow G-15, G-17, and role prompts.
