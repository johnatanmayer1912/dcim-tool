# Reality-loop device-fidelity / fix-until-stable pass

**Date:** 2026-08-22  
**VERSION:** 7.0.97  
**Review folder:** `docs/review_folder/2026.08.22/QA/reality_loop_device_fidelity_pass/`  
**Evidence class:** fixture / replay / device-like. **Not live. Not enterprise clearance.**

## A. Active roles

parser-engineer · topology-architect · security-reviewer · map/product-ux-reviewer · test-engineer · telemetry-architect · packaging/release-engineer · browser-e2e-engineer · legacy-device-compatibility-reviewer · fixture-fidelity-engineer · release-board-auditor

## B. Loop cycles executed

1. Inspected god-mode report, readiness register, parsers, fixtures, Playwright, spec/prebuild. Probed legacy IOS/NX-OS/Junos formats against current parsers.
2. Found real parse bugs (CDP brief merge/wrap, LLDP local-first split, spaced abbrev, `mac ` prefix, Junos 11 brief). Fixed at root; added fixtures; retested.
3. Graph port normalize aligned with parser finalize (lazy import). Retested Phase 2 + graph dedup.
4. Expanded Playwright (hash, About, jobs, 404 report, reload) + API contracts. Screenshot on reload.
5. VERSION 7.0.97 spec/changelog/manifest/UPDATE_DATE. Collector + review folder. Hard-stop still BLOCKED.

Stopped when remaining blockers were live-lab absence and Windows-host EXE, not unfixed parser defects in scope.

## C. Folder created for this pass

`docs/review_folder/2026.08.22/QA/reality_loop_device_fidelity_pass/` — README, FIXLOG, maps, fixtures, pytest logs, readiness, packaging, browser screenshot.

## D. Tests / fixtures created or updated

**Fixtures (labeled device-like, not live):**
- `legacy_ios12_cdp_brief_wrapped_device_id.txt`
- `legacy_ios12_lldp_detail_local_interface.txt`
- `legacy_nxos_lldp_detail_mac_prefix.txt`
- `legacy_junos11_lldp_brief_no_parent.txt`
- `device_like_nxos_lldp_brief_device_id_first.txt`
- `legacy_ios_cdp_detail_ipv4_and_blank_ip.txt`

**Tests:** `tests/test_reality_loop_device_fidelity.py`, `tests/test_reality_loop_api_contracts.py`  
**Playwright:** `tests/browser/operator_program_status.spec.mjs` (18 → 29 checks)  
**Manifest:** `pytest_reality_loop_device_fidelity` (40 suites)  
**Scripts:** `scripts/reality_loop_collect_evidence.py`

## E. Issues found and fixes made

See `FIXLOG.md`. Summary: CDP brief wrap + single-space Platform/Port ID; IOS LLDP Local Interface+Chassis merge; spaced Gig/Fas normalize; NX-OS `mac ` prefix; Local Port id vs Port id; Junos 11 no-parent brief.

## F. Realism/device-fidelity improvements

Closest simulated coverage: IOS 12.x CDP wrap and LLDP local-first; NX-OS mac-prefix + Device-ID-first brief; Junos 11.x 5-column brief without Parent Interface; IPv4 Address / blank IP CDP detail; CRLF vs LF. **Not** “validated on real devices.”

## G. Maps / outputs / files validated

| Artifact | Check |
|----------|--------|
| `maps/incomplete_observation_no_edges.html` | incomplete present; no `"from": "EDGE-01"` edge |
| `maps/legacy_ios12_wrapped_cdp_brief.html` | wrap neighbors present; `Gi1/0/1`; fixture edges only |
| Traffic/Shumoku | absent — not generated |
| Cable certification | not claimed; wrap edges are CDP brief finalize, not cable-truth |

## H. Playwright / API / code / packaging results

- Playwright: **29/29 PASS** (mocked loopback)
- Reality-loop pytest + API: **PASS** (40 tests with packaging alignment)
- Phase 2 + graph + parser regression: **153 passed**
- Phase 3+4 isolated: **164 passed** (combined session with discovery imports can pollute freeze `sys.modules` — not a product regression)
- Phase 5+6 previously 112; re-run in collector/reality_loop file PASS
- Prebuild + every_code_change: **PASS**
- `--require-release-pass`: exit **1** (expected)

## I. Exact commands and results

```
python3 -m pytest tests/test_reality_loop_device_fidelity.py tests/test_reality_loop_api_contracts.py -q
# PASS (included in 40 with packaging)

python3 -m pytest tests/test_phase2_topology_truth_*.py tests/test_discovery_graph_dedup.py \
  tests/test_parser_regression.py tests/test_network_discovery.py -q
# 153 passed

python3 -m pytest tests/test_phase3_telemetry_*.py tests/test_phase4_*.py -q
# 164 passed

NST_REVIEW_DIR=docs/review_folder/2026.08.22/QA/reality_loop_device_fidelity_pass \
  python3 scripts/run_operator_browser_qa.py
# 29/29 PASS

python3 _prebuild.py && python3 scripts/mandatory_release_qa.py --phase every_code_change
# MANDATORY RELEASE QA: PASS (40 suites)

python3 scripts/phase5_discovery_readiness_check.py --require-release-pass
# exit 1  (BLOCKED)

python3 scripts/reality_loop_collect_evidence.py
# sample_maps ok; wrap_edge_count 2
```

## J. Readiness evidence summary

| Signal | Value |
|--------|-------|
| Register `ok` | true (honesty only) |
| `release_gate` | BLOCKED |
| `hard_stop` | true |
| `may_claim_enterprise_ready` | false |
| `may_claim_live_vendor_validated` | false |
| `live_evidence_artifact` | null |
| Device-like parser coverage | improved, fixture-only |

## K. Final verdict

**Blocked** for enterprise / live-vendor claims.

**Conditionally ready** for offline loopback operator use with honest BLOCKED Program Status, plus stronger device-like parser contracts.

Not awarded: Operationally ready but not enterprise ready — live truncated CDP/LLDP still not_executed; operational field use of truncated discovery remains unproven.

## L. Remaining blockers

1. No retained live_ssh PASS-eligible artifact
2. Windows EXE requires a Windows + PyInstaller host
3. No Shumoku/SNMP utilization maps (scope)
4. CDP spoofing / no SSO unchanged

## M. Next required step

Authorized live_ssh lab against reachable IOS/XE, NX-OS, and Junos devices; retain truncated CDP/LLDP artifact; wire `live_evidence_artifact`. Build EXE on Windows via `python build.py`.
