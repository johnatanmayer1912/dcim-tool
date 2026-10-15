# Parser, regex, and fallback report

**VERSION:** 7.2.2 · **Date:** 2026-08-23  
**Honesty:** Fixture CLI / JSON only — **not** live IOS / NX-OS / Junos proof.

## Vendor surfaces covered (offline)

| Vendor | Fixture / enrichment | Tests |
|---|---|---|
| Cisco IOS | `enrichment/cisco_ios_show_interfaces.txt` | `test_parser_regression`, `test_vendor_matrix`, QA vendor ops |
| Cisco NX-OS | `enrichment/cisco_nxos_show_interface.txt` | same |
| Juniper Junos | `enrichment/juniper_show_interfaces_statistics.txt` | same; VLAN rename blocked notice in UI |

## Pytest results (this pass)

| Suite | Result | Log |
|---|---|---|
| Core trust/parser/UI/security battery | **309 passed** | `pytest/core_battery.txt` |
| Parser regression + vendor matrix + QA vendor ops | **57 passed** | `pytest/parser_vendor.txt` |
| Broader parser+topology slice set (earlier in pass) | **127 passed** | same log lineage / phase5 slices |

## JSON / overlay edge behavior

From `generated_outputs/edge_cases/edge_case_results.json`:

| Input | Result |
|---|---|
| `malformed_not_json.txt` | **PASS** — rejected by `json.loads` |
| `empty_object.json` | LOADED — edges=0; must not mint topology |
| `partial_overlay.json` | LOADED — schema `utilization_overlay_v1`, edges=1 |
| `wrong_version_overlay.json` | LOADED — schema `utilization_overlay_v999` (version drift visible; join must not mint topology) |
| `duplicate_edge_ids.json` | LOADED — edges=2; join must not invent cables |
| `valid_minimal_overlay.json` | LOADED — edges=0 |

## Inventory normalization edge behavior

| Case | accept | warn | reject |
|---|---|---|---|
| empty | 0 | 0 | 0 |
| DNS hostname | 0 | 0 | 1 |
| duplicate | 1 | 1 | 0 |
| bad device_type | 0 | 0 | 1 |
| IPv6 | 1 | 0 | 0 |

Aligns with Preview/Commit/execute IP gate (7.2.2).

## Fallback / resilience notes

- Phase5 parser topology resilience slices exist; not all re-run in the final minute of this pass — core regression + vendor matrix green.  
- Overlay wrong-version does not auto-upgrade silently into a certified plant.  
- Map overlay paints existing L2 only; gray dashed = no sample (honesty).  

## Verdict

**Parsers/fixtures: PASS for offline regression scope.** Do not cite as live multi-vendor certification.
