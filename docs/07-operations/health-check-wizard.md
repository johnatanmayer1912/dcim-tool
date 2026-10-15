# First-launch health check wizard (v7.0.0)

On first load, the web UI runs an optional **health check** unless the user chose **Don't show again** (`localStorage.nst_health_v7_ok`).

## API

- `GET|POST /api/health-check/run` — runs all checks, returns `{ ok, checks[], ran_at }`
- `GET /api/health-check/status` — last result cached in memory
- `GET /api/health-check/demo-map/discovery` — offline discovery demo HTML
- `GET /api/health-check/demo-map/vpc` — vPC Engineering Board demo (`DEMO_VPC_TOPOLOGY_v7.0.html`)

## Checks

| Step | Validates |
|------|-----------|
| Inventory | `inventory.txt` readable with at least one device line |
| Port | `127.0.0.1:5051` status |
| Plugins | Registry loads ≥11 plugins, zero load errors |
| Discovery demo | `NetworkDiscoveryPlugin` demo_mode + topology HTML path |
| vPC demo | `DEMO_VPC_TOPOLOGY_v7.0.html` contains `__VPC_BOARD__` |
| CLI smoke | `tests/test_cli_smoke.run_cli_smoke_test()` pass/fail |

## UI

Modal: **Run checks**, **Skip for this session**, **Don't show again**, plus links to open demo maps.
