# Audit test gap register (v7.0.2 sweep)

Gaps found during fresh system bug audit **W-BUG-SWEEP-2026-05-31-v702**. Add tests when implementing fixes (target v7.0.3+).

## Missing automated tests

| Gap | Relates to | Suggested test |
|-----|------------|----------------|
| Frozen plugin bootstrap | NEW-C1 | `test_plugin_registry_frozen_bootstrap.py`: mock `sys.frozen`, empty `exe_dir/plugins`, assert load from bundled path ≥10 |
| BFS visited before SSH | NEW-H1 | `test_discovery_crawl_retry.py`: mock `safe_connection` fail once then succeed; assert second attempt runs |
| `dry_run` parameter | NEW-H2 | `test_discovery_dry_run.py`: `crawl_network_multi_seed(..., dry_run=True)` must not call `safe_connection` |
| Junos LLDP local port | NEW-H5 | Extend `test_network_discovery.py` with fixture `junos_lldp_detail.txt`; assert `local_port == ge-0/0/0` |
| Parallel edge dedup | NEW-M1 | `test_discovery_parallel_edges.py`: two edges same pair different ports → both retained |
| Short-hostname merge collision | NEW-M2 | `test_discovery_graph_dedup.py`: `sw1.site-a` + `sw1.site-b` → two nodes |
| `validate_graph` case sensitivity | NEW-M3 | Nodes `SW1` / alias `sw1` after rewire → no false orphans |
| Concurrent discovery JSON | NEW-M4 | Integration: two job IDs write separate inventory paths (after fix) |
| `run_mac_trace` string matches | NEW-M5 | Adapter test with `matches: ["line1"]` logs FOUND |
| `/api/execute` empty body | NEW-M6 | Flask test client POST without JSON → 400 not 500 |
| STP UI error restore | NEW-M7 | Manual or Playwright: error status shows scan actions |
| Health full-mode `ok` | NEW-M8 | `run_health_checks(full=True)` with mocked failed vpc → `all_ok` false |
| CLI connect TOCTOU | NEW-H3 | Two threads `create_cli_session` same id → one connection |
| STP job prune | NEW-H4 | Stress test: N jobs → dict size capped |

## Covered today (do not duplicate)

- `tests/test_discovery_platform_classifier.py` — BUG-0007
- `tests/test_discovery_graph_dedup.py` — canonical merge
- `tests/test_health_check_runner.py` — quick health
- `tests/test_cli_smoke.py` — single connect path
- `_prebuild.py` sections 6b, 6c

## Prebuild hooks to add (when fixing)

| Fix | `_prebuild.py` section |
|-----|-------------------------|
| NEW-C1 | `[6d] Frozen plugin path contract` |
| NEW-H1/H2 | `[6e] Discovery crawl contract` |
| NEW-H5 | Parser fixture in existing 6b block |

## Manual-only (until lab available)

- Live legacy IOS SSH encryption fallback
- Full EXE GUI health wizard click-through on bare folder
- Multi-site hostname collision in production inventory
