# P0 remediation validation — 2026-08-24

## Summary

| P0 ID | Issue | Status | Evidence |
|-------|--------|--------|----------|
| **ZT-007** | Plugin AST sandbox / HTTP upload | **CLOSED** | `plugin_upload_is_enabled()` permanently `False`; RB-ZT-01 tests pass |
| **ZT-008** | `/api/execute` no operator identity | **CLOSED** | credential_id mandatory; plaintext secrets rejected; execute audit log |
| **B-01** | `release_gate` BLOCKED | **OPEN (by design)** | Honesty register requires live evidence; checker emits BLOCKED + hard_stop |
| **B-02** | No live truncated CDP/LLDP SSH evidence | **OPEN (environment)** | Live harness exit 2 against lab IPs; replay contract proven |
| **B-03** | Windows PE EXE not built on Darwin | **OPEN (environment)** | `_prebuild.py` PASS; EXE build requires Windows host |

## Code changes (fixable P0)

### ZT-008 — execute credential_id-only

- `utils/vault_credentials.py` — `credential_id_required` mode; rejects client secret fields
- `utils/api_security.py` — `audit_execute_dispatch()`
- `vlan_checker_web.py` — `/api/execute` requires vault credential_id
- `modules/web/templates/index.html` — runAction/VLAN/plugin/IM payloads send credential_id only
- `tests/execute_test_helpers.py`, `tests/test_rb_zt_execute_credential_id_only.py`
- Updated execute-related tests + `tests/conftest.py` isolation fixture

### ZT-007 — verified closed

No code change required; upload route returns 403 with install model metadata.

### Collateral fixes

- `UPDATE_DATE` aligned to v7.2.3
- `utils/standard_map_shell.py` — map tooltip copy (no `credential_id` in HTML)
- `tests/test_phase3_telemetry_api_freeze.py` — import isolation (paramiko from other tests)
- `scripts/run_playwright_e2e.py` — mkdir for html report index

## Test results

| Gate | Result |
|------|--------|
| `pytest` (full) | **1919 passed**, 1 skipped |
| `mandatory_release_qa.py --phase every_code_change` | **PASS** |
| `run_playwright_e2e.py` (6 specs) | **PASS** |
| `_prebuild.py` | **READY TO BUILD** |
| `phase5_discovery_readiness_check.py` | **ok=true**, **release_gate=BLOCKED** |

## Honest verdict

**Fixable security P0s (ZT-007, ZT-008) are closed** with automated proof.

**Evidence/environment P0s (B-01, B-02, B-03) remain open** — clearing `release_gate` without live SSH vendor evidence would violate product honesty and fail the readiness register checker.

Product posture: **improved localhost security**; **not** enterprise-operational-ready until live lab + Windows EXE evidence exists.
