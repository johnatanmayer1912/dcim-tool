# Polish residuals closed — 7.2.3

Closed items from enterprise validation list (excluding Windows EXE + SSO):

| # | Item | Change |
|---|---|---|
| 3 | Calm VLAN/Settings chrome | White validation panels; credential KPI/export/master/danger panels flat; STP + L2 hero flattened; IM CTAs → `btn-mac` |
| 4 | Find CTA consistency | Find Missing VLAN → `btn-mac-primary`; Port map → neutral `btn-mac` |
| 5 | Chrome meta narrow width | ≤1100px: brand column stack; hide `·` separators; freshness full width |
| 6 | Discovery DNS vs inventory | Seed hint + Inventory lede: seeds may be DNS; `inventory.txt` IP-only |
| 7 | Flask `__version__` | `/debug_status` → `importlib.metadata.version` |
| 9 | Sidebar brand | Quiet “About” text link; logo/version hidden |

**VERSION:** 7.2.3 · Tests: `tests/test_polish_7_2_3.py` · Does not clear `release_gate`.
