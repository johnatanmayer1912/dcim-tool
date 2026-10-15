# BUG-0008 — Bug registry / executive summary drift

| Field | Value |
|-------|-------|
| **ID** | BUG-0008 |
| **Title** | Bug registry and executive summary out of sync with application `VERSION` |
| **Severity** | Low (documentation) |
| **Priority** | P3 |
| **Owner** | Documentation Steward |
| **Status** | **open** (process) |
| **Found** | 2026-05-31 (sweep W-BUG-SWEEP-2026-05-31-v702) |

## Description

After v7.0.x releases, `docs/14-bug-reports/00-executive-summary.md` and individual `bug-report.md` files (e.g. BUG-0001, BUG-0002) still showed **open** status and app version **6.9.28**. Operators and agents reading detail folders saw false open bugs.

## Impact

Wrong prioritization; duplicate fix attempts; loss of trust in bug registry.

## Resolution (partial — this audit pass)

- Refreshed [`00-executive-summary.md`](../../00-executive-summary.md) to **7.0.2**
- Closed BUG-0001/0002 detail `bug-report.md` headers
- Added [`W-BUG-SWEEP-2026-05-31-v702.md`](../../W-BUG-SWEEP-2026-05-31-v702.md) and updated [`01-prioritized-bug-list.md`](../../01-prioritized-bug-list.md)

## Ongoing process

On each release bump `VERSION`:

1. Update executive summary version and sweep reference
2. Ensure new findings use NEW-* or BUG-00xx folders
3. Close detail files when fixed; do not leave `Status: open` for shipped fixes

## Related

- Sweep: W-BUG-SWEEP-2026-05-31-v702
- Not a runtime defect
