# Phase 5 Slice 1 — Parser / Topology Resilience Baseline (fixture-only)

**Status:** baseline established (2026-08-21)  
**Scope:** Cisco IOS / IOS-XE, Cisco NX-OS, Juniper Junos discovery parsers + topology honesty  
**Out of scope:** live SSH, Arista, telemetry transport, topology writes from telemetry

## Purpose

Prove deterministic fixture behavior for malformed and drifting discovery CLI:

- where parsers already preserve Phase 2 truth rules;
- where behavior fails or is incomplete (queued for Slice 2+).

## Fixture matrix

Under `tests/fixtures/discovery/` (existing + `phase5_*`):

| Case | IOS/IOS-XE | NX-OS | Junos |
|---|---|---|---|
| Valid baseline | `ios_cdp_detail.txt`, `iosxe_lldp_brief.txt` | `nxos_cdp_detail.txt`, `nxos_lldp_brief.txt` | `junos_lldp_brief.txt` |
| Missing remote port | `phase5_ios_cdp_detail_missing_remote_port.txt`, `phase5_iosxe_lldp_brief_missing_port_id.txt` | (shared Cisco CDP/LLDP parsers) | `phase5_junos_lldp_brief_incomplete_neighbor.txt` |
| Truncated CDP | `phase5_ios_cdp_detail_truncated_no_interface.txt` | shared CDP detail | n/a (LLDP) |
| Garbage injection | `phase5_ios_cdp_detail_garbage_injected.txt`, `phase5_iosxe_lldp_brief_garbage_injected.txt` | `phase5_nxos_cdp_detail_garbage_injected.txt` | `phase5_junos_lldp_brief_garbage.txt` |
| Duplicate blocks | `phase5_ios_cdp_detail_duplicate_blocks.txt` | — | — |
| Empty / comment | `phase5_empty_show_output.txt`, `''` | same | same |
| CDP disabled | — | `nxos_cdp_disabled.txt` | — |
| Chassis-only LLDP | — | `nxos_lldp_chassis_only.txt` | — |
| IRB / L3 | — | — | `junos_lldp_brief_irb.txt` |

## Test module

`tests/test_phase5_parser_topology_resilience_slice1.py`

## Commands

```bash
python3 -m pytest tests/test_phase5_parser_topology_resilience_slice1.py -q --tb=short
```

## Claims

This baseline does **not** claim live vendor compatibility, physical cable truth in production, complete parser coverage, Arista support, or telemetry transport readiness.

Slice chronology reports under `reports/PHASE5_SLICE*` were removed as superseded; this file is the living baseline.
