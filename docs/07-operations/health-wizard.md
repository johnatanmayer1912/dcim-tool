# First-launch health wizard (v7.0.2)

## Behavior

On first launch, a **Welcome — readiness check** modal appears. **No checks run automatically** — use **Continue to program** to dismiss immediately.

| Button | What runs |
|--------|-----------|
| **Continue to program** | Closes modal; no checks |
| **Run quick check** | Inventory file, port 5051, plugin registry (&lt; 1 s) |
| **Run full check (demos)** | Quick + offline discovery HTML + vPC demo file |
| **Run CLI smoke (slow)** | Quick + mock SSH CLI smoke test |

## Plugin check (false positives)

v7.0.1 required ≥11 plugins with zero load errors using private registry fields — often failed in partial installs.

v7.0.2 uses `get_all_metadata()`, threshold **≥10** plugins, lists loaded plugin IDs in the UI, and tolerates one load warning if count is still sufficient.

## Persistence

- **Don't show again** → `localStorage.nst_health_v72_ok`
- **Skip for this session** → `sessionStorage.nst_health_v72_skip`

## API

`POST /api/health-check/run` with JSON:

```json
{ "quick": true, "full": false, "include_cli": false }
```

Default when body omitted: quick mode only.
