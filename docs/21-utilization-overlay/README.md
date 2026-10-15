# Utilization overlay — documentation index

| Field | Value |
|-------|--------|
| **Status** | Implemented in product code (M1–M5). Not live-lab proven. |
| **As of** | 2026-08-23 |
| **App VERSION** | 7.0.99 |
| **Schema** | `nst.utilization_overlay.v1` |
| **Live collector** | SSH CLI counters (not SNMP) |

This folder is the **authoritative contract** for painting utilization on existing L2 map edges.

| Document | Role |
|----------|------|
| [FEATURE_CONTRACT.md](FEATURE_CONTRACT.md) | Product, UX, data, join, modes |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Phased delivery |
| [RISKS_AND_NON_GOALS.md](RISKS_AND_NON_GOALS.md) | Risks, never-do, freeze boundaries |
| [ACCEPTANCE.md](ACCEPTANCE.md) | QA / exit checks |
| [overlay-contract.schema.json](overlay-contract.schema.json) | Machine-readable overlay document |
| [overlay-contract.ts](overlay-contract.ts) | TypeScript draft matching the schema |
| [HANDOFF_NEXT_PROMPT.md](HANDOFF_NEXT_PROMPT.md) | **Stop record** — no further overlay implementation until signed named-lab evidence |

UX visual reference (mock only): `docs/11-ux/demos/07-maps-utilization.html`.
