# MASTER PROMPT v3 — Operational Credential Fallback Certification

| Field | Value |
|-------|-------|
| **Version** | 3.0.0 |
| **Product** | Network Swiss Tool Pro (operational offline EXE) |
| **Mindset** | Zero Trust + Exhaustive Matrix — **never claim 100% without a green matrix row for every SSH entrypoint** |
| **Oracle** | One mock network device; Primary fails; Secondary succeeds; assert **attempt order** (not log presence alone) |

## Mission (pass/fail)

Certify that **every** code path that opens an SSH session to a device retries credentials in order:

**Primary → Secondary → Third**

Coverage required:

1. Every `modules/plugins/*.py` that SSH-connects
2. Every Tools `/api/execute` action that SSH-connects (connectivity, VLAN, topology, backup, …)
3. Discovery, Interface Manager, STP, Standards, Utilization live, L3 maps
4. GUI buttons that trigger those paths (payload must include secondary/third IDs)
5. Combinations: P-only success; P-fail/S-ok; P+S-fail/T-ok; all-fail; empty fallback (no extra attempts)

## Non-negotiable proof (per entrypoint)

| Proof | Requirement |
|-------|-------------|
| P1 Wire | Call uses `safe_connection`/`connect_device` **or** credentials dict with `fallback_credentials` reaching that call |
| P2 Stamp | Devices or credentials carry Secondary/Third from vault resolve |
| P3 Order | Mock `connect_permissive`: attempted usernames `== ['primary_user','secondary_user']` when S succeeds |
| P4 UI | Button/handler sends `secondary_credential_id` + `third_credential_id` when selected |
| P5 Fail | All-fail raises/surfaces error; no false success |

**Forbidden:** declaring success from `"Has fallback_credentials: True"` alone.

## Execution plan

1. Inventory all SSH call sites; fail if any `connect_permissive` remains outside `network_base`
2. Build `tests/test_credential_fallback_full_matrix.py` — one mock device, patch `connect_permissive`, run every plugin + every execute action
3. Static assert every plugin `safe_connection` block includes `fallback_credentials=`
4. Playwright: every major Tools button intercept `/api/execute` (or discovery/IM/STP) and assert IDs
5. Fix gaps; re-run matrix until **0 MISS rows**
6. Only then bump VERSION

## Verdict language

- **CERTIFIED** = matrix green for all SSH entrypoints + UI payload checks
- **NOT CERTIFIED** = any MISS / any order assertion fail — do not ship
