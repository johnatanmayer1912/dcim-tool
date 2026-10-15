# Utilization overlay — implementation plan

| Field | Value |
|-------|--------|
| **Contract** | [FEATURE_CONTRACT.md](FEATURE_CONTRACT.md) |
| **Date** | 2026-08-22 |
| **Live transport** | SSH CLI (not SNMP) |

## Complexity (honest)

| Slice | Effort | Why |
|-------|--------|-----|
| UX paint on existing vis edges + legend + banner | **M** (days–1 week) | Shells already color by protocol; overlay is stroke override + honesty copy |
| Replay/static join + fixture JSON | **M–H** (1–2 weeks) | Join/ifName is the hard part; identity already in `cisco_iface` / `topology_relation_key` |
| Live SSH two-sample collector | **H** (weeks–~2 months to a careful v1) | Vendor CLI drift, 64-bit counters, cancel, vault, scale |
| Live + replay in one VERSION | **H+** | Do not; replay must land first |
| SNMP/Shumoku | **Out** | Non-goal; see risks |

**Easiest win:** Fixture overlay JSON + join unit tests + Standard L2 stroke override, all-gray when document empty.

**Hardest risk:** Painting the wrong edge (Po vs member, `.0` unit, FQDN vs short hostname).

**Recommended order:** M0 mock already exists → M1 contract tests (this folder) → M2 join library → M3 Standard L2 replay paint → M4 live SSH collector → M5 Discovery CC host.

## Milestones

### M0 — Spec lock (this pass)

- **Purpose:** Freeze product law before code.
- **Scope:** This folder only.
- **Dependencies:** Existing L2 maps.
- **Risks:** None to runtime.
- **Tests:** None required.
- **Exit:** Contract cited by next prompt; schema validates conceptually.

### M1 — Overlay model + schema tests

- **Purpose:** `nst.utilization_overlay.v1` load/validate in Python.
- **Scope:** `utils/utilization_overlay/model.py`, JSON schema, reject live/replay mismatch, reject unknown cable_key.
- **Dependencies:** M0.
- **Risks:** Over-coupling to vis `e{i}` ids — forbidden.
- **Tests:** Unit: valid/invalid documents; refuse paint key not in L2 set.
- **Exit:** pytest green; no map HTML change required.

### M2 — Join library (replay samples → paints)

- **Purpose:** Conservative endpoint join.
- **Scope:** `join.py`; fixtures under `tests/fixtures/utilization/`; Junos unit fallback; no Po←member.
- **Dependencies:** M1, `utils/cisco_iface.py`, `utils/juniper_iface.py`.
- **Risks:** Ambiguous hostname aliases (inventory IP vs map id).
- **Tests:** Mapped / unmapped / ambiguous / partial / mgmt-irb / bundle member; vis edge count invariant helper.
- **Exit:** Golden fixtures; zero topology mutations.

### M3 — Standard L2 replay UX

- **Purpose:** Operator can toggle overlay on Inventory Standard L2 HTML.
- **Scope:** `standard_map_shell.py` + `report_formatter.py`; embed overlay JSON; legend; inspector; unmapped table; mode chip Replay.
- **Dependencies:** M2, existing `nstBootStandardMap`.
- **Risks:** XSS via ifName — must `topoEsc` / existing esc; color vs one-sided dash conflict (partial uses distinct dash).
- **Tests:** HTML contract: no new `from/to` pairs; banner copy; replay not labeled live; Playwright optional on fixture map.
- **Exit:** Fixture map screenshots in review folder; `#btn-map-all` path documented.

### M4 — Live SSH collector

- **Purpose:** Two-sample bps on inventory devices that are map nodes.
- **Scope:** Plugin or job action; Netmiko via `network_base`; control plane cancel; output JSON next to map; `api_security` localhost+vault.
- **Dependencies:** M3, credential_id, parsers+fixtures per vendor.
- **Risks:** Session load, parser drift, Phase 5 gate confusion (must not set live_vendor topology validation).
- **Tests:** Fixture CLI (not live lab); cancel/degraded; no secrets in overlay JSON; freeze test: `utils.telemetry` unchanged.
- **Exit:** Live toggle enabled; honesty `Live SSH — not SNMP`; still `release_gate BLOCKED` until unrelated live topology evidence exists.

### M5 — Discovery Command Center host

- **Purpose:** Same overlay document on crawl maps.
- **Scope:** `discovery_map_shell.py` consume same paint API.
- **Status:** Implemented 2026-08-22 (viewer host; Live SSH start remains Standard L2 only).
- **Dependencies:** M3.
- **Risks:** Mixing overlay EVPN purple with utilization red — mitigated by skipping non-cable vis ids on Discovery paint.
- **Tests:** EVPN edges never receive utilization color; incomplete observations never appear as painted cables.
- **Exit:** One overlay JSON can bind either host if `topology_job_id` matches.

## Milestone dependency graph

```
M0 spec → M1 model → M2 join → M3 Standard L2 replay → M4 live SSH
                                      ↘ M5 Discovery CC
```

Do not start M4 before M3 exit. Do not ship M4 without vendor CLI fixtures.

**Code status 2026-08-23:** M1–M5 are implemented in this repository. Fixture/CLI-parse tests exist. Named-lab live SSH has **not** been executed. Do not treat this plan as unfinished implementation work.

