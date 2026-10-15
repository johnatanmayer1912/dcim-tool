# COMPETITIVE_ADVANTAGE_POLICY

| Field | Value |
|-------|-------|
| **Version** | 3.0.0 |
| **Status** | active |
| **Owner** | Prompt Governance Framework |
| **Registry ID** | G-10 |
| **last_updated** | 2026-05-31 |

**Role:** Product / Platform Strategist (R-PROD / U-PROD) · **Lifecycle:** `CHANGE_MANAGEMENT_POLICY.md` phase 1 (Problem/scope) · **Escalation:** `ESCALATION_MATRIX.md` — Strategic opportunity row

## Purpose

Keep the platform strategically ahead in the network management market.

---

## Review domains

Periodically evaluate competitors and adjacent tools across:

- network automation platforms
- network observability platforms
- network mapping tools
- NMS platforms
- NOC tools
- Cisco ecosystem tools
- automation frameworks
- enterprise monitoring solutions

Reviews should inform roadmap and **scope decisions** before large engineering investment (U-PROD → U-ARCH).

---

## Rules

1. **Periodically evaluate** competitors and adjacent tools (at least when planning major features or quarterly roadmap reviews).
2. **Identify** gaps, differentiation opportunities, and strategic risks.
3. **Translate** market insight into roadmap recommendations (`CHANGELOG` themes, `docs/00-overview/`, action logs).
4. **Balance** innovation with maintainability and operational safety (`QUALITY_GATE_POLICY.md`, offline/reliability constraints).
5. **Record** strategic recommendations and ownership (Product Strategist + Architect; Team Meeting for forks).

---

## Strategic focus (Network Swiss Tool Pro)

Differentiate on **capabilities that compound**, not feature count alone:

| Pillar | Examples in this codebase |
|--------|---------------------------|
| **Reliability** | Fewer false-empty UI panels; validated VPC/topology pipeline |
| **Offline operations** | Embedded Vis.js maps, offline EXE, air-gapped workflows |
| **Topology + vPC intelligence** | Member interfaces, diagnostics exports, vPC Domain plugin |
| **Extensibility** | Plugin registry, orchestrator workflows |
| **Governed engineering quality** | Master prompts, tests (`_prebuild`, VPC validation), LIBRARIAN docs |

### Invest when

- Capability reduces **NOC time-to-diagnose** (topology diagnostics, search_it, VPC domain).
- Output works **air-gapped** (no CDN-only critical path for offline SKU).
- Behavior is **testable** and documented.
- Knowledge **compounds** (docs + prompts preserve intent).

### Avoid

- Fragile CDN-only critical paths for offline SKU.
- Undocumented parser heuristics.
- UI churn without operational workflow docs.
- Feature sprawl without QA/governance gates.

### Measurement (examples)

- Fewer false-empty panels (e.g. VPC member interfaces).
- Faster mean time to export diagnostics.
- Documented release notes for every shipped version.
- Plugin load errors = 0 at release.

---

## Required outputs

Each strategic review or major feature proposal SHOULD produce:

| Output | Description |
|--------|-------------|
| **competitive landscape notes** | Who competes, how they position, relevant domains above |
| **platform gaps** | Where Network Swiss Tool Pro is weak vs needs |
| **strategic opportunities** | Differentiation bets aligned with pillars |
| **priority recommendations** | Ranked initiatives with rationale |
| **implementation candidates** | Concrete features/plugins/docs tied to U-ARCH / U-ENG |
| **risks and tradeoffs** | Maintainability, security, offline, scope creep |

Store in `action-logs/YYYY-MM-DD_strategy-<topic>.md` or `docs/00-overview/` when durable.

---

## Required strategic action log

For Product Strategist–led reviews, log:

| Field | Content |
|-------|---------|
| **review date / trigger** | Roadmap, feature request, competitive event |
| **domains reviewed** | Subset of review domains list |
| **outputs produced** | Which required outputs above are attached |
| **owner** | U-PROD + handoff to U-ARCH |
| **next decision** | Proceed / defer / Team Meeting |

Link to G-08 change summary when moving to implementation.

---

## Integration with governance

| Policy | Use |
|--------|-----|
| G-08 Change management | Scope and expected outcome before build |
| G-07 Quality gates | Do not trade safety for speed without waiver |
| G-09 Release | Ship only with validation + docs |
| G-06 Documentation | Strategic decisions that affect users must be documented |

---

## Success criteria

- [ ] Competitive/adjacent landscape considered for major initiatives
- [ ] All six required outputs addressed or explicitly N/A
- [ ] Recommendations recorded with owner
- [ ] Tradeoffs balance innovation vs maintainability and safety

---

## Index linkage

`INDEX_PROMPT.md` Phase A §7 (policy set).
