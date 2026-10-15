# Remaining blockers

**VERSION:** 7.2.2 · **Date:** 2026-08-23  
Strict enterprise bar: anything that would fail a real ops acceptance review.

## P0 — blocks “enterprise operational ready” / live ship claims

| ID | Blocker | Why it matters |
|---|---|---|
| B-01 | `release_gate` **BLOCKED** / HARD STOP | Product correctly refuses enterprise-ready claim; cannot clear from fixtures |
| B-02 | No live truncated CDP/LLDP / SSH lab evidence in this pass | Fixtures ≠ live plant |
| B-03 | Windows PE EXE not produced / not E2E’d on this Darwin host | Offline EXE is the typical ops deliverable |

## P1 — blocks broad enterprise infrastructure adoption

| ID | Blocker | Why it matters |
|---|---|---|
| B-04 | No SSO/RBAC / multi-user authz | Loopback ≠ identity control; external bind expands blast radius |
| B-05 | Full axe / WCAG certification not run | Accessibility residual for regulated enterprises |

## P2 — polish / residual (not ship-stoppers for localhost NOC console)

| ID | Item | Status |
|---|---|---|
| B-06 | Remaining decorative gradients (VLAN validation panel, some Settings surfaces) | **Closed in 7.2.3** |
| B-07 | Find accent color inconsistency (purple outline) | **Closed in 7.2.3** |
| B-08 | Chrome meta density on narrow viewports | **Closed in 7.2.3** |
| B-09 | Discovery seed may allow DNS (intentional ≠ inventory.txt) — document for operators | **Closed in 7.2.3** |
| B-10 | Flask `__version__` deprecation warning | **Closed in 7.2.3** |
| B-11 | Sidebar brand still slightly loud | **Closed in 7.2.3** (quiet About link) |

Still open after exclusions (Windows / SSO ignored by operator request): live lab for B-01/B-02; optional full axe (B-05).

## Explicit non-blockers (honest)

- Offline map expected_vs_actual MATCH  
- Playwright CI-browser PASS  
- Pytest batteries green for executed sets  
- Prebuild READY TO BUILD  
- IM KPI rainbow and Destroy wording fixed this pass  

## Clearance rule

Do **not** mark release_gate clear, live-validated, or enterprise-operational-ready until B-01–B-03 are closed with live + Windows EXE evidence.
