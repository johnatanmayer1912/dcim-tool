# Bug reports (system check output)

**Created by:** `docs/12-master-prompts/roles/CHECK_SYSTEM_FOR_BUGS.md` (W-BUG-SWEEP)  
**Trigger:** User says **check system for bugs**

This folder is populated when you run the bug-sweep prompt. Do not hand-edit the tree before a run unless archiving a prior sweep.

**Latest sweep:** 2026-05-31 — **W-BUG-SWEEP-2026-05-31-v702** (app **v7.0.2**, audit-only) — start at [`00-executive-summary.md`](00-executive-summary.md) · full report [`W-BUG-SWEEP-2026-05-31-v702.md`](W-BUG-SWEEP-2026-05-31-v702.md)

## Layout

```text
docs/13-bug-reports/
├── README.md
├── 00-executive-summary.md
├── 01-prioritized-bug-list.md
├── 02-bug-details/BUG-NNNN-[short-description]/  (per bug)
├── 03-team-contributions/                        (per role)
├── 04-fix-workflow/
├── 05-validation-reports/
├── 06-documentation-updates/
├── 07-version-history/
└── _SCAFFOLD/                                    (templates — copy per bug)
```

## Quick start

1. In AI IDE: open `docs/12-master-prompts/roles/CHECK_SYSTEM_FOR_BUGS.md` or type **check system for bugs**
2. After run: start at `00-executive-summary.md`
3. Fix bugs using `02-bug-details/*/fix-prompt.md` (copy-paste into IDE)

## Legacy

Older single-bug templates: `docs/12-master-prompts/bugs/_TEMPLATE/` (superseded by `_SCAFFOLD/` here for full sweeps).
