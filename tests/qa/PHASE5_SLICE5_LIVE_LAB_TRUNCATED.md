# Phase 5 Slice 5 — Live-lab truncated CDP/LLDP (authorized path)

**Status:** closed for this checkout with **honest skip of live SSH**  
**Date:** 2026-08-21

## Authorization

This slice was authorized to exercise the live-lab truncated CDP/LLDP path.  
Vault / `.credential_key` was **not** read.

## Live SSH attempt

| Host (from `inventory.txt`) | Reachability |
|---|---|
| 10.1.1.1 | DOWN |
| 10.1.1.2 | DOWN |
| 10.2.1.1 | DOWN |
| 10.2.1.2 | DOWN |
| 10.3.1.1 | DOWN |
| SSH :22 on 10.1.1.1 | closed/filtered |

**Verdict:** Live SSH **not executed** (no reachable lab hosts). Do not claim live vendor truncated CDP/LLDP validation.

## Executable substitute (authorized harness)

`scripts/phase5_live_lab_truncated_discovery.py`

- Gate: `NST_PHASE5_LIVE_LAB=1`
- Replay: `NST_PHASE5_LIVE_LAB_REPLAY=tests/fixtures/discovery/phase5_live_lab_capture_replay.json`
- Live SSH: `NST_LAB_HOSTS` + `NST_LAB_USER` + `NST_LAB_PASSWORD` (env only)
- Contract: incomplete → not edge-eligible; no `unknown`/`n/a` ports

Replay result this checkout: **ok** (2 incomplete + 1 complete; 0 failures).

## Operator live run (when lab is up)

```bash
export NST_PHASE5_LIVE_LAB=1
export NST_LAB_HOSTS=...
export NST_LAB_USER=...
export NST_LAB_PASSWORD=...
# optional: NST_LAB_DEVICE_TYPE=cisco_ios|cisco_xe|cisco_nxos|juniper_junos
python3 scripts/phase5_live_lab_truncated_discovery.py --json-out /tmp/phase5_live.json
```

## Tests

`tests/test_phase5_parser_topology_resilience_slice5.py`  
Manifest suite includes Slice 5.
