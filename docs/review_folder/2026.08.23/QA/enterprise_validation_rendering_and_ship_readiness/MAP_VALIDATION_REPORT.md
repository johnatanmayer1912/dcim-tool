# Map validation report

**VERSION:** 7.2.2 · **Date:** 2026-08-23  
**Lab:** Offline unified E2E fixture (`demo_lab/`) — **not** live CDP/LLDP.

## Expected vs actual

Source: `generated_outputs/exports/expected_vs_actual.json`

| Metric | Expected | Actual | Match |
|---|---|---|---|
| device_count | 8 | 8 | ✓ |
| l2_edge_count | 7 | 7 | ✓ |
| non_cable_count | 2 | 2 | ✓ |
| standard_l2_vis_edges | 7 | 7 | ✓ |
| discovery_vis_edges | 9 | 9 | ✓ |
| overlay_painted | 1 | 1 | ✓ |
| discovery_evpn_unpainted | true | true | ✓ |
| fingerprint_unchanged | true | true | ✓ |

**Overall:** `match: true`  
**Honesty string:** Offline fixture lab. Not live vendor evidence. Not a certified cable plant.

## Variants validated

| Variant | Evidence |
|---|---|
| Standard L2 + overlay replay | HTML + `screenshots/maps/standard_l2.png` + Playwright offline_map_html |
| Standard L2 overlay off | `standard_l2_overlay_off.html` |
| Discovery Command Center | HTML + `screenshots/maps/discovery.png` |
| Utilization overlay JSON | `overlays/utilization_overlay_replay.json` |
| Diagnostics | `diagnostics/link_issues.json` |
| Enrichment samples (IOS / NX-OS / Junos) | `enrichment/*.txt` (fixture CLI samples, not live) |
| Topology graph export | `topology/graph.json` |

## Trust / honesty checks (Playwright)

- Replay is not a live poll  
- Live SSH is not SNMP  
- Overlay does not certify topology / mint cables  
- file:// Live SSH stays disabled  
- Discovery does not offer Live SSH start as a live poll  
- EVPN / STP-blocked edges not grayed as unsampled cables when overlay on  
- Map shells show Program Status HARD STOP / `release_gate` BLOCKED  

## Residual map risks (not cleared)

- Spoofed CDP/LLDP poisoning not live-tested  
- Duplicate hostname / serial merge edge cases beyond fixture set  
- No live truncated discovery evidence → gate stays BLOCKED  

## Verdict

**Maps: PASS (offline fixture + rendering honesty).** Unfit to claim live topology certification.
