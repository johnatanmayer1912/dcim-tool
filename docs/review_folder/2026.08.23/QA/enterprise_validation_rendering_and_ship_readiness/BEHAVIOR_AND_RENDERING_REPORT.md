# Behavior and rendering report

**VERSION:** 7.2.2 · **Date:** 2026-08-23  
**Honesty:** Fixtures and generated HTML ≠ live vendor proof.

## Operator shell (localhost `:5051`)

| Workspace | Screenshot | Behavior notes |
|---|---|---|
| Inventory | `screenshots/operator/01_inventory.png` | IPv4/IPv6-only lede; parsed hosts Status; Preview/Commit/execute IP gate aligned (7.2.2 trust contract) |
| Maps | `screenshots/operator/02_maps.png` | Replay ≠ live poll; Live SSH ≠ SNMP honesty retained |
| Find | `screenshots/operator/03_find.png` | White card panels; CTAs coherent |
| Change · VLAN | `screenshots/operator/04_change_vlan.png` | Dry-run checkbox; **Delete VLAN** (not Destroy); Validate ≠ Apply copy |
| Change · IM | `screenshots/operator/04_change_im.png` | Single-host warning; calm KPI strip (white cards); no bulk deploy lie |
| Evidence | `screenshots/operator/05_evidence.png` | Jobs table; Note vs Open wording |
| Settings / About | `06_settings.png`, `07_about.png` | Release notes parse `### 7.2.x`; VERSION surface |

## Generated map / report HTML

| Artifact | Path | Content check |
|---|---|---|
| Standard L2 (overlay replay) | `generated_outputs/maps/standard_l2_overlay_replay.html` | 8 devices · 7 links; HARD STOP Program Status; overlay honesty |
| Standard L2 (overlay off) | `generated_outputs/maps/standard_l2_overlay_off.html` | Exists; fingerprint contract |
| Discovery Command Center | `generated_outputs/maps/discovery_command_center.html` | 9 vis edges; EVPN non-cable not grayed as unsampled cable |
| Overlay JSON | `generated_outputs/overlays/utilization_overlay_replay.json` | Replay paint; not topology mint |
| Expected vs actual | `generated_outputs/exports/expected_vs_actual.json` | **`match: true`** |
| vPC demo map (API) | `screenshots/reports/vpc_demo_map.png` | Health demo render |

## Workflow / import-export (offline)

| Path | Result |
|---|---|
| Inventory Preview/Commit IP gate | DNS rejected; IPv6 accepted (edge_case_results) |
| Execute `filter_inventory` | Same allow-list as Preview (trust contract tests) |
| Map generate (`generate_unified_e2e_demo`) | Logs in `logs/generate_maps.txt` |
| Export counts | `generated_outputs/exports/actual_counts.json` |
| Overlay edge fixtures | See `json_fixtures/` + `edge_cases/edge_case_results.json` |

## Non-happy paths exercised

Empty inventory · DNS host · duplicate · bad device_type · malformed JSON · wrong overlay schema version · partial overlay · empty object — see `PARSER_REGEX_FALLBACK_REPORT.md` and edge_case results.

## Outcome

**Behavior and rendering: PASS for offline/operator scope.** Important HTML pages render with honesty banners and expected topology counts. Not a live production plant certification.
