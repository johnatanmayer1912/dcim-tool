# QA — Phase 6 Wave 4 (Program Status overview strip)

## Scope

Cross-surface overview strip / linkage. Not exhaustive end-program QA.

## Commands

```bash
python -m pytest tests/test_phase6_wave4_program_status_overview.py -q
```

Expect: three surfaces, shared readiness BLOCKED + hard_stop, inventory ≠ crawl labeling, no parallel truth.

## Do not report as

- Overview strip = enterprise clearance or live validation
- Three surfaces = one topology artifact
- Program Status = map edges / confirmed links
