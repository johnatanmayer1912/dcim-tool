# Phase 4 — Fixture/lab-only telemetry acceptance (closeout freeze)

**Status:** Phase 4 **closed** (fixture + lab-only).  
**Scope:** Phase 3 frozen contract + Phase 4 Zero Trust gate + Gate C / Gate D designs + in-process lab surfaces (`lab_ingest`, `lab_audit`, `lab_facade`).  
**Not:** HTTP/HTTPS/mTLS/gRPC listeners, durable storage, UI, alerting, live collectors, production auth, or topology integration.

## Supported fixture families (unchanged from Phase 3)

- Cisco IOS-XE
- Cisco NX-OS
- Juniper Junos

Arista remains unsupported.

---

## 1. Gate A/B — lab ingest

- Explicit `lab_mode=True` required (`LabTelemetryIngestor`).
- In-process only: validate → normalize → catalog → `ObservationStore` → snapshot.
- No sockets, threads, auto-start, or persistence.
- Loopback-only bind configuration (`127.0.0.1` / `::1` / `localhost`).
- Public / wildcard bind (`0.0.0.0`, `::`, `*`) rejected.
- `start_network_listener` hard-fails.

## 2. Authentication and authorization

- Test-only `LabStubPrincipal` / `LabAuthContext` (not production mTLS).
- Missing / unknown / expired / revoked / mismatched principals rejected.
- Default-deny; separate `telemetry_ingest`, `telemetry_read`, `telemetry_export`, `telemetry_audit_read`.
- Raw payload and topology operations denied.
- Operator cannot ingest; collector cannot snapshot/audit by default; snapshot read ≠ audit read.

## 3. Gate C — encrypted-at-rest (design only)

Documented in `docs/telemetry/PHASE4_GATE_C_ENCRYPTED_AT_REST.md`:

- AEAD / key hierarchy (KEK/DEK), rotation, revocation, fail-closed key failures.
- Retention, deletion, backup, restore requirements.
- **No durable telemetry store or encryption implementation exists.**

## 4. Gate D — operator/API exposure (design + lab facade)

Documented in `docs/telemetry/PHASE4_GATE_D_OPERATOR_API_EXPOSURE.md`:

- Read-only surfaces designed; **no HTTP routes or listeners**.
- Allowlisted responses/errors; export separate from read; audit-read separate from snapshot-read.
- Query/resource bounds defined; listener prerequisites explicit before any future network exposure.
- Lab implementation: `LabGateDFacade` (in-process only).

## 5. Lab audit sink

- `LabAuditSink`: in-memory, bounded, oldest-first eviction, overflow counter.
- Redacted allowlisted event fields; no tokens, secrets, raw payloads, or unsafe paths.
- Audit write failure → fail-closed on acceptance paths (`audit_failed`, no silent success).
- Retrieval permission-gated (`telemetry_audit_read`) and copy-on-read.

## 6. Lab facade

- Health / schema / observation / snapshot / delta / catalog / quarantine reads.
- Snapshot export and audit export (permission-separated).
- Bounded, deterministic, allowlisted responses; authn/authz per protected operation.
- Redaction and audit failures fail closed.
- **No ingestion through facade** (ingest remains `LabTelemetryIngestor` only).
- No topology read/write.

## 7. Frozen boundaries

| Boundary | Rule |
|---|---|
| Scope | Fixture and lab only |
| Phase 3 API | `utils.telemetry.__all__` unchanged; lab modules **not** package-exported |
| Live vendors | No compatibility claim |
| gRPC / protobuf | Not present; no interoperability claim |
| mTLS / production auth | Stubs only; no production claim |
| Durable storage | None |
| UI / alerting | None |
| Topology | No mutation, edges, trust, maps, or cable inference |
| Performance / compliance / security certification | Not claimed |
| Arista | Unsupported |

## 8. Design artifacts

- `docs/telemetry/PHASE4_ZERO_TRUST_GATE.md` — Zero Trust gate (Gates A–E)
- `docs/telemetry/PHASE4_GATE_C_ENCRYPTED_AT_REST.md` — Gate C
- `docs/telemetry/PHASE4_GATE_D_OPERATOR_API_EXPOSURE.md` — Gate D
- `tests/qa/PHASE3_TELEMETRY_ACCEPTANCE.md` — Phase 3 freeze (still in force)

## 9. Validation commands

```bash
python3 -m pytest \
  tests/test_phase4_telemetry_closeout.py \
  tests/test_phase4_telemetry_lab_facade.py \
  tests/test_phase4_telemetry_lab_audit.py \
  tests/test_phase4_telemetry_lab_ingest.py \
  tests/test_phase4_gate_d_operator_api_exposure.py \
  tests/test_phase4_gate_c_encrypted_at_rest.py \
  tests/test_phase4_telemetry_zero_trust_gate.py \
  tests/test_phase3_telemetry_api_freeze.py \
  tests/test_phase3_telemetry_regression_slice6.py \
  tests/test_phase3_telemetry_snapshot_slice5.py \
  tests/test_phase3_telemetry_delta_slice4.py \
  tests/test_phase3_telemetry_store_slice3.py \
  tests/test_phase3_telemetry_catalog_slice2.py \
  tests/test_phase3_telemetry_contract_slice1.py \
  -q --tb=short

python3 -m pytest tests/test_phase2_topology_truth_regression.py -q --tb=short

python3 scripts/validate_mandatory_qa_manifest.py
```

Optional full pre_release orchestrator (includes this suite when run):

```bash
python3 scripts/mandatory_release_qa.py --phase pre_release
```

## 10. Regression anchors

| Anchor | Role |
|---|---|
| `tests/test_phase4_telemetry_closeout.py` | Acceptance + manifest freeze |
| `tests/test_phase4_telemetry_lab_facade.py` | Gate D lab facade |
| `tests/test_phase4_telemetry_lab_audit.py` | Audit sink |
| `tests/test_phase4_telemetry_lab_ingest.py` | Lab ingest |
| `tests/test_phase4_gate_*` / `zero_trust_gate` | Design gates |
| `tests/test_phase3_telemetry_*` | Phase 3 freeze + slices |
| Manifest suite | `pytest_phase4_telemetry_lab` (pre_release, blocking) |
