# ORCHESTRATOR — Usage Guide

**Registry ID:** U-ORCH · **Source:** `docs/02-codebase/PLATFORM_PROMPTS/P03_ORCHESTRATOR.md`  
**Quality gate:** Automation Review

## Role purpose

Coordinate multi-device workflows, plugin execution chains, and batch operations across the plugin registry.

## When to use

- Plugin runs, batch jobs, multi-step device automation.
- New plugin registration and execution paths.

## When not to use

- Single-file UI tweak with no orchestration.

## Best practices

- Read plugin doc in `docs/04-plugins/` before coding.
- Fail gracefully per device; document sequence.
- Keep plugin IDs stable (`P02_REGISTRY.md`).

## Required inputs

- `P03_ORCHESTRATOR.md`, `P02_REGISTRY.md`
- Plugin module + registry metadata
- Feature doc (e.g. vpc-domain-plugin, network-discovery)

## Expected outputs

- Documented step sequence; error handling per device
- Plugin load 0 errors in registry list

## Related roles

Lead Developer; System Architect; QA Engineer; Documentation Steward.

## Related policies

G-07, G-08

## Common mistakes

- New plugin without `docs/04-plugins/` page.
- Breaking execute API contract.

## Example scenarios

1. vPC Domain plugin → parse `show vpc` / brief, report domain/role.
2. Network Discovery crawl → depth limits + duplicate MAC handling.

## Resync procedure

INDEX, registry, plugin docs, `modules/plugins/`, CHANGELOG plugin entries, smoke `/api/plugins/list`.
