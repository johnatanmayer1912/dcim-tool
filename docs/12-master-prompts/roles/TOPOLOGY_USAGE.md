# TOPOLOGY — Usage Guide

**Registry ID:** U-TOPO · **Source:** `docs/02-codebase/PLATFORM_PROMPTS/P05-TOPOLOGY.md`  
**Quality gate:** Network Engineering Review

## Role purpose

Own topology collection, VPC parsing, HTML map rendering, diagnostics exports, and Vis.js performance behavior.

## When to use

- Topology maps, vPC/member interfaces, keepalive panels, CDP/LLDP.
- `topology_diagnostics_*` folder behavior.
- `report_formatter.py` / `adapters.py` / `topology_mapper.py` changes.

## When not to use

- Non-network UI tabs with no map pipeline.

## Best practices

- Validate with `tests/validate_vpc_member_interfaces.py`.
- Keep `bundled_links` / `edge_data` contract consistent.
- Prefer physics off after stabilize for large maps.

## Required inputs

- `QA_VPC_MAP.md`, demo HTML or live diagnostics JSON
- Parser samples (`show vpc brief`, etc.)

## Expected outputs

- Data path documented; tests pass
- Diagnostics README + JSON templates when applicable

## Related roles

Lead Developer; QA Engineer; Observability Engineer; System Architect.

## Related policies

G-07, G-10

## Common mistakes

- JS reading `bundled_links` only at edge top level.
- Omitting `show vpc brief` fallback on NX-OS.

## Example scenarios

1. Empty Member Interfaces panel → trace adapters → edges_json → JS.
2. Keepalive “not healthy” strings → telemetry parser in formatter.

## Resync procedure

Manual resync + `QA_VPC_MAP.md` + latest VPC-related CHANGELOG entries + validation script status.
