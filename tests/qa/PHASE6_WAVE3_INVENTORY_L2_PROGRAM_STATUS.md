# QA — Phase 6 Wave 3 (inventory L2 Program Status)

## Scope

Swiss Tools inventory Standard L2 map header reuses Program Status. Not exhaustive QA.

## Commands

```bash
python -m pytest tests/test_phase6_wave3_inventory_l2_program_status.py -q
```

Expect: `nst-program-status-banner`, `HARD STOP — not advisory`, inventory ≠ crawl labeling.

## Do not report as

- Inventory map Program Status = crawl graph equivalence
- Map complete = enterprise ready / live truncated validation
- Inventory device/link counts clear the release gate
