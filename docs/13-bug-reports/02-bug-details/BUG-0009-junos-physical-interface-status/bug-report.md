# Bug report — BUG-0009

| Field | Value |
|-------|-------|
| **ID** | BUG-0009 |
| **Title** | Junos `Physical interface:` same-line status not parsed |
| **Severity** | High |
| **Priority** | P1 |
| **Owner** | Lead Developer |
| **Status** | **closed** v7.0.29 |
| **Found** | 2026-06-10 (W-BUG-SWEEP-2026-06-10-v7028) |

## Description

When Junos `show interfaces` returns status on the same line as the physical interface header — e.g. `Physical interface: xe-0/0/0, Enabled, Physical link is Up` — Interface Manager reports `status: unknown` instead of `up`.

## Root cause

`_parse_junos_interfaces()` in `interface_manager.py` matches the `Physical interface:` line for the name only. `Physical link is Up/Down` detection runs on subsequent lines under `current_interface`, not on the header line itself.

## Impact

- Interface map shows wrong status on Junos (including QFX5100 / Junos 14)
- 3+ parser regression tests fail
- Undermines v7.0.28 interface-map improvements for Juniper

## Reproduction

1. Parse fixture in `tests/test_parser_regression.py::test_junos_interfaces_xe_format`
2. Or SSH to Junos device, run discover via Interface Manager
3. Observe `xe-0/0/0` card shows `unknown` despite link up

## Role findings

| Role | Finding |
|------|---------|
| QA | 3 parser tests fail; prebuild does not run full pytest |
| Lead Developer | One-line fix in header match branch |
| System Architect | Same pattern may affect `topology_mapper` if duplicated |
