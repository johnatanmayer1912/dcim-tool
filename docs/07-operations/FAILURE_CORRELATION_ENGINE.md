# Failure Correlation Engine

**Version:** 7.4.33+  
**Action:** `failure_correlation` via `/api/execute`  
**UI:** Inventory → Inventory Utilities → **Failure correlation**

## What it is

An offline **engineer explanation engine** — not a SIEM. For each inventory device it:

1. Collects `show logging` / `show logging logfile` (bounded)
2. Collects interface brief/status + NX-OS `show vpc`
3. Classifies lines with a rule catalog (interface, vPC, protocol, security, hardware…)
4. Drops noise (periodic CDP/LLDP, debug)
5. Clusters evidence by object (interface / vPC / protocol)
6. Ranks **hypotheses** with confidence + evidence quotes + next check

## Honesty

- No hypothesis without evidence (or explicit **incomplete observation** when CLI shows down but logs are empty).
- Does not invent topology or dual-active events.
- Complements LibreNMS/Loki/SuzieQ for long-term retention.

## Outputs

Under `outputs/failure_correlation/<date>/<run>/`:

| File | Purpose |
|---|---|
| `failure_correlation.html` | Operator report |
| `failure_correlation.json` | Machine-readable bundle |
| `report.txt` | Compact engineer notes |

## APIs

- `POST /api/execute` `{ "action": "failure_correlation", "credential_id": "..." }`
- `GET /api/failure-correlation/status`
- `GET /api/failure-correlation/open`

## Lab

Docker SSH fabric includes intentional log stories (link failure, vPC keepalive fail, BPDU guard err-disable, OSPF down) so the engine can be validated offline.
