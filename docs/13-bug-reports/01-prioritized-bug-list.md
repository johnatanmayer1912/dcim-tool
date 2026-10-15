# Prioritized bug list



## Closed — v6.9.26 / v6.9.28 / v7.0.x



**Resolution:** BUG-0001–0005 fixed in **v6.9.26**; BUG-0006 in **v6.9.28**; BUG-0007 in **v7.0.1**; health wizard in **v7.0.2**.



| Priority | BUG-ID | Title | Status |

|----------|--------|-------|--------|

| P1 | BUG-0002 | Discovery job always `complete` even on plugin error | **closed** v6.9.26 |

| P2 | BUG-0001 | Documentation version drift | **closed** v6.9.26 |

| P3 | BUG-0004 | Hardcoded VERSION in vPC validation script | **closed** v6.9.26 |

| P3 | BUG-0003 | Unclosed test fixture files (ResourceWarning) | **closed** v6.9.26 |

| P3 | BUG-0005 | Unbounded `_discovery_jobs` in-memory store | **closed** v6.9.26 |

| P2 | BUG-0006 | NX-OS hostname from `show version` banner | **closed** v6.9.28 |

| P1 | BUG-0007 | Discovery platform misclassification + duplicate nodes | **closed** v7.0.1 |



---



## Closed — v7.0.3 / v7.0.28 (verified 2026-06-10 sweep)



| ID | Title | Status |

|----|-------|--------|

| **NEW-H1** | `visited.add()` before SSH | **closed** v7.0.3+ (`network_discovery.py` L630–641) |

| **NEW-H2** | `dry_run` hardcoded false | **closed** v7.0.3+ |

| **NEW-H3** | CLI connect TOCTOU | **closed** v7.0.3+ (`cli_manager.py` lock during connect) |

| **NEW-H6** | Junos MAC trace Cisco column parsing | **closed** v7.0.28 |



## Closed — v7.0.29 (verified 2026-06-10 code review)



| ID | Title | Status |

|----|-------|--------|

| **BUG-0009** | Junos `Physical interface:` same-line status → `unknown` | **closed** v7.0.29 |

| **BUG-0010** | pytest 10 failures (parser + HTML contracts) | **closed** v7.0.29 |

| **NEW-C1** | Frozen EXE plugin path (read-only → bundled) | **closed** v7.0.29 |

| **NEW-H5** | Junos LLDP colon fallback captures `:` | **closed** v7.0.29 |

| **NEW-M2** | `merge_nodes` short-hostname collision | **closed** v7.0.29 (serial merge) |



## Closed — v7.0.30 (`/find-all-bugs-and-fix` 2026-06-10)



Repro: [`W-BUG-SWEEP-2026-06-10-v7030.md`](W-BUG-SWEEP-2026-06-10-v7030.md)



| ID | Title | Status |

|----|-------|--------|

| **NEW-M1** | Edge dedup drops parallel links | **closed** v7.0.30 — port-aware graph + regression test |

| **NEW-M3** | `validate_graph` case-sensitive orphan detection | **closed** v7.0.30 — verified + test |

| **NEW-M4** | `discovered_inventory.json` global path — job overwrite | **closed** v7.0.30 — `reports/discovery/` + timestamp |

| **NEW-M5** | `adapters.run_mac_trace` expects dict matches | **closed** v7.0.30 — verified dict/string handling |

| **NEW-M6** | `/api/execute` missing JSON guard | **closed** v7.0.30 |

| **NEW-M7** | STP tab actions hidden on error | **closed** v7.0.30 — retry button on failure |

| **NEW-M8** | Health `ok` ignores full-mode demo failures | **closed** v7.0.30 — UI + backend verified |

| **NEW-M9** | `classify_os_family` broad Cisco→IOS fallback | **closed** v7.0.30 |

| — | Duplicate standards JS (`runStandardsValidation` vs V2) | **closed** v7.0.30 — V2 alias |

| — | Health wizard mixed localStorage keys | **closed** v7.0.30 — `nst_health_ok` |

| — | Verbose `[DEBUG]` map pipeline logs | **closed** v7.0.30 — `NST_DEBUG` gate |

| **BUG-0008** | Bug registry / executive summary drift vs `VERSION` | **closed** v7.0.30 sweep |



---



## Closed — v7.0.33 (`/find-all-bugs-and-fix` 2026-06-10)

Repro: [`W-BUG-SWEEP-2026-06-10-v7033.md`](W-BUG-SWEEP-2026-06-10-v7033.md)

| ID | Title | Status |
|----|-------|--------|
| **NEW-S1** | Master password change wipes vault when locked | **closed** v7.0.33 |
| **NEW-S2** | Plugin upload path traversal | **closed** v7.0.33 |
| **NEW-S3** | Discovery job reads without lock | **closed** v7.0.33 |
| **NEW-S4** | POST JSON guards missing | **closed** v7.0.33 |
| **NEW-S5** | Uncaught `int()` on API params | **closed** v7.0.33 |
| **NEW-S6** | Credential table stored XSS | **closed** v7.0.33 |
| **NEW-S7** | Clear label leaves sidebar secrets | **closed** v7.0.33 |
| **NEW-S9** | Stale `UPDATE_DATE` in web entry | **closed** v7.0.33 |

---

## Deferred / watch



| Topic | Notes |

|-------|-------|

| Live SSH discovery on legacy IOS | Encryption fallback in `network_base`; monitor field reports. |

| `DEMO_VPC_TOPOLOGY_v7.0.html` label | Header may show older version — cosmetic. |

| Bare EXE deploy | **NEW-C1 closed** v7.0.29 — field smoke recommended. |

| Swiss Tools topology parallel links | Port-aware dedup in `adapters.py`; monitor if CDP+LLDP duplicates reported. |

| `description_search` DEBUG verbosity | Intentional for operator diagnostics. |



---



## Test gaps



See [`docs/08-operations/audit-test-gaps.md`](../08-operations/audit-test-gaps.md).

