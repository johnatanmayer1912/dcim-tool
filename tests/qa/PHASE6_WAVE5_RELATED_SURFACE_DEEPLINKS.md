# QA — Phase 6 Wave 5 (related-surface deep-links)

## Scope

Navigation polish only. Not exhaustive end-program QA.

## Commands

```bash
python3 -m pytest tests/test_phase6_wave5_related_surface_deeplinks.py -q
```

Expect: jump metadata, UI helpers, map console links, gate still BLOCKED + hard_stop. Does not freeze or clear release_gate. HARD STOP — not advisory.

## Do not report as

- Deep-links = enterprise clearance or live validation
- Jump to Inventory L2 = auto topology truth or crawl equivalence
- Navigation = readiness progress
