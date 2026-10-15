# /api/execute Action Contract

Release gate: `tests/test_api_execute_mac_alias.py` must pass before ship.

## Core actions (`vlan_checker_web.api_execute`)

| `action` value | Thread | Notes |
|----------------|--------|-------|
| `connectivity` | connectivity check | |
| `vlan_check` | VLAN audit | |
| `find_missing_vlan` | missing VLAN scan | requires `vlan_id` |
| **`mac_check`** | MAC trace | requires `mac_address` |
| `description_search` | description search | requires `desc_search` |
| `add_vlan` / `rename_vlan` / `delete_vlan` | VLAN mutations | validate API first |
| `interfaces` | interface check | |
| `vlan_compare` | compare | |
| `node_analyze` | node analysis | |
| `node_interface_topology` | port map | |
| `topology` | L2 / vPC map | `map_mode` |
| `audit` | OS audit | |
| `backup` / `save_config` | config ops | |
| `reachability_matrix` | fleet reachability HTML/CSV | |
| `l3_topology` / `flow_map` / `advanced_l2_map` | map builders | |
| `failure_correlation` | Failure Correlation Engine | logs → ranked hypotheses |

## Aliases (v7.0.61+)

| Alias | Resolves to | Why |
|-------|-------------|-----|
| `mac_trace` | `mac_check` | Search-it progress category is `mac_trace`; Swiss Tools must not dispatch invalid action |

## UI rules

1. Swiss Tools and Search tab buttons call **`runAction('mac_check')`**, not `mac_trace`.
2. `runAction()` normalizes `mac_trace` → `mac_check` before POST.
3. Empty `mac_address` is rejected in the browser before dispatch.

## Search-it progress keys (not execute actions)

| Progress key | Execute action |
|--------------|----------------|
| `mac_trace` | `mac_check` |
| `description_search` | `description_search` |
| `ping_scan` | `/api/ping_scan` (separate route) |

## Mandatory tests

```bash
python -m pytest tests/test_api_execute_mac_alias.py -q
python -m pytest tests/qa/test_00_implemented_mandatory.py -q -k mac
```

Evolution: any new Swiss Tools shortcut must use a registered `action` or documented alias — add test in `test_api_execute_mac_alias.py`.
