# Phase 4 — Gate D: Operator/API exposure design

| Field | Value |
|---|---|
| **Status** | Architecture / security **design gate only** — **not implemented** |
| **Predecessor** | `PHASE4_ZERO_TRUST_GATE.md` Gate D; lab ingest + `LabAuditSink`; Gate C |
| **Code freeze** | No HTTP/HTTPS/mTLS/gRPC listener, sockets, UI, persistence, live collectors, alerting, or topology integration in this pass |
| **Related** | Phase 3 API freeze (`utils.telemetry.__all__`); `lab_ingest.py` permissions; `lab_audit.py` redaction |

**Question this gate answers:**  
What read-only telemetry and audit information may be exposed to which principal, under which scope, with what redaction, and with what fail-closed behavior?

This document does **not** authorize a listener and does **not** change the frozen Phase 3 public telemetry API.

---

## 1. Exposure principles

- **Read-only by default** — no mutation surfaces for observations, catalog, topology, or maps.
- **Default deny** — missing/unknown permission → deny.
- **Least privilege** — separate ingest, read, export, audit-read, admin.
- **No implicit export** — on-screen/API read ≠ export permission.
- **No raw payload exposure** — ever, including error bodies.
- **No secret or token exposure** — credentials, stub tokens, keys, Authorization headers.
- **No topology mutation** — and no cable/ownership/trust inference from telemetry.
- **No persistence assumption** — exposure design works over in-memory store; disk needs Gate C implementation-pass.
- **Loopback ≠ authentication** — bind address is not a principal.
- **No device ownership or physical-link inference** from telemetry reads.

---

## 2. Principal classes

| Principal | Intended use | Default permissions (illustrative) | Hard limits |
|---|---|---|---|
| **Collector** | Ingest fixtures/live later | `telemetry_ingest` (+ device scope) | No snapshot/audit/export/topology |
| **Operator** | Read series / export snapshots | `telemetry_read`, optionally `telemetry_export` | No ingest; no audit-read unless also granted |
| **Auditor** | Security evidence | `telemetry_audit_read` | No ingest; snapshot not implied; no raw payload |
| **Administrator** | Catalog/retention/policy (future) | `telemetry_admin` (+ explicit others) | Still no topology_write; no raw_payload_read |
| **Service account** | Automated read/export | Explicit least-privilege set | No shared god-token across ingest+export+admin |
| **Unauthenticated** | None | *(empty)* | All surfaces denied |

No role-management product is implied — labels only for future authz.

---

## 3. Endpoint / surface inventory (logical — not routes)

| Surface | Principal | Permission | Scope | Export? | Safe fields (summary) | Forbidden | Fail-closed | Audit |
|---|---|---|---|---|---|---|---|---|
| Health / readiness | Authenticated any lab principal | *(authn only)* or public **lab** probe with no data | N/A | No | `status`, `lab_mode`, schema version | store contents, secrets | Deny data on authz fail | Optional health hit |
| Normalized observation read | Operator | `telemetry_read` | device/metric | No | Contract fields sans raw/secret | `raw_*`, tokens, passwords | Deny | observation_read |
| Series snapshot read | Operator | `telemetry_read` + `telemetry_export` for export-shaped responses | device filters | If export perm | Phase 3 snapshot shape | raw payloads, topology | Deny / audit_failed | snapshot_read |
| Delta read | Operator | `telemetry_read` | series scope | No (unless export) | delta status, values, direction | raw obs bodies | Deny | delta_read |
| Catalog metadata read | Operator / Admin | `telemetry_read` or `telemetry_admin` | path/platform | No | status, kind, unit, warnings | secret path strings | Deny | catalog_read |
| Quarantine summary read | Operator / Auditor | `telemetry_read` and/or `telemetry_audit_read` | device | Export needs export+audit policy | reason_code, ids, catalog_status | raw payload, secret values | Deny | quarantine_read |
| Audit-event read | Auditor | `telemetry_audit_read` | N/A (redacted events) | Separate audit export | LabAuditSink allowlist keys | tokens, paths secret-like, payloads | Deny | audit_read |
| Schema / version read | Authenticated | authn | N/A | No | `schema_version`, freeze note | internals | Deny if unauthenticated | schema_read |

---

## 4. Permission matrix

| Permission | Collector | Operator | Auditor | Admin | Unauth |
|---|---|---|---|---|---|
| `telemetry_ingest` | **Yes** (scoped) | No | No | Only if explicit | No |
| `telemetry_read` | No | **Yes** | Optional | Optional | No |
| `telemetry_export` | No | Explicit | No* | Optional | No |
| `telemetry_audit_read` | No | No (unless explicit) | **Yes** | Optional | No |
| `telemetry_admin` | No | No | No | **Yes** | No |
| `topology_read` | No via telemetry API | No via telemetry API | No | No | No |
| `topology_write` | **Unavailable** | **Unavailable** | **Unavailable** | **Unavailable** | No |
| `raw_payload_read` | **Denied** | **Denied** | **Denied** | **Denied** | No |

\*Auditor export of audit events requires an explicit future `telemetry_audit_export` (or dual `telemetry_export`+`telemetry_audit_read`) — never implied by audit read alone.

**Hard rules**

- Unknown / absent permissions → **denied**.
- Operator cannot ingest; collector cannot read snapshots by default.
- Snapshot read does **not** imply audit read.
- Audit read does **not** imply raw payload read or snapshot export.
- Telemetry permissions do **not** grant topology permissions.
- `topology_write` remains unavailable on all telemetry surfaces.

---

## 5. Response contracts (future — do not alter Phase 3 now)

### Observation (read)
Stable fields aligned with Phase 3 contract: `observation_id`, `device_id`, `platform`, `metric_name`, `metric_path`, `entity_path`, `value`, `value_type`, `unit`, `metric_kind`, `catalog_status`, `source_timestamp`, `received_at`, `quality`, `quarantined`, `warnings`, `notes` (redacted).  
Nullable/`unknown` per Phase 3. No `raw_payload`, credentials, tokens.

### Series snapshot
Match `export_series_snapshot` shape: `schema_version`, `generated_at` (caller-supplied or `unknown`), `series_count`, `observation_count`, `series[]`, `export_notes`/`warnings`. Deterministic `series_key` order. No topology/trust/raw.

### Delta
`delta_status`, `absolute_delta`, `direction`, `reset_detected`, observation ids, `comparison_basis`, warnings/notes. No nested raw observations.

### Catalog result
`status` (`known`/`unknown`/`invalid`/`ambiguous`), match ids, metric_kind, unit, warnings — never silent pick on ambiguous; secret-like paths → invalid without echoing path.

### Quarantine summary
`observation_id` (if any), `reason_code`, `catalog_status`, `device_id_safe`, counts — no payload body.

### Audit event
Exactly LabAuditSink allowlist: `event_id`, `event_type`, `outcome`, `actor_kind`, `actor_id_safe`, `device_scope_safe`, `operation`, `observation_id`, `catalog_status`, `reason_code`, `sequence`, `lab_only`, `redaction_version`.

### Error
`ok: false`, `status` (stable category), `reason` (generic), optional `request_id`. No tokens, secrets, raw paths, payloads, or stack traces.

**Ordering:** deterministic by documented keys. **Pagination (future):** cursor/limit required before large sets. **Correlation:** opaque `request_id` in audit + response; not a secret.

---

## 6. Export rules

| Export class | Permission | Controls |
|---|---|---|
| On-screen / API read | `telemetry_read` | Bounded size; redaction; no disk assumption |
| Structured snapshot export | `telemetry_read` + `telemetry_export` | Deterministic; redaction before serialize; export audit event; fail-closed on redaction/audit failure |
| Audit export | `telemetry_audit_read` + explicit export grant | Same; still no secrets |
| Quarantine export | read/audit + export policy | reason codes only |
| Bulk export | export + admin policy | Hard max records/bytes; rate limit |

**Require:** explicit export permission; bounded size; deterministic order; redaction before serialization; export event recorded; **no** raw payload / secret-like paths; **no** topology mutation via import/export; fail-closed on redaction or audit failure.

---

## 7. Query controls (future requirements)

| Control | Requirement |
|---|---|
| Device / tenant / metric scope | Mandatory filter enforcement; cross-scope deny |
| Time range | Optional; never invent timestamps |
| Max records / response size | Hard caps; reject if exceeded |
| Timeout / rate limit | Per principal; fail-closed |
| Pagination / sorting | Documented; default series_key / sequence order |
| Stale/fresh indicators | Optional labels; not topology trust |
| Catalog unknown/ambiguous | Visible statuses; never silent resolve |
| Quarantine visibility | Permission-gated; summary only |

No performance infrastructure in this pass.

---

## 8. Error behavior

| Category | Client `status` (illustrative) | Echo rule |
|---|---|---|
| Authentication failure | `authn_failed` | Generic |
| Authorization failure | `authz_denied` | Generic |
| Invalid scope | `invalid_scope` | No device enumeration |
| Invalid query | `invalid_query` | No raw filter echo if sensitive |
| Unsupported surface | `unsupported` | Generic |
| Malformed identifier | `invalid_id` | Generic |
| Rate / size limit | `limit_exceeded` | Generic |
| Unavailable data | `unavailable` | Generic |
| Audit failure | `audit_failed` | Deny success claim |
| Redaction failure | `redaction_failed` | Deny response body |
| Topology access denied | `authz_denied` | Same as lab deny |

Never echo: tokens, secrets, raw paths, raw payloads, stack traces.

---

## 9. Audit requirements

Record (LabAuditSink philosophy — in-memory lab today; durable only after Gate C implementation):

- Authn success/failure; authz allow/deny  
- Observation / snapshot / delta / catalog / quarantine / audit reads  
- All exports  
- Denied raw-payload and topology requests  
- Invalid or excessive queries  
- Redaction failures  

Reuse stable **reason codes**; no durable audit storage in this pass.

---

## 10. Listener boundary

**Prerequisites before any future listener**

1. Gate D documented-pass (this artifact) **and** implementation review  
2. Approved authentication (Gate B / mutual-auth design)  
3. Approved authorization implementing this matrix  
4. Gate C implementation-pass **if** any persistence  
5. Request/response validation + rate/size controls  
6. Audit integration (fail-closed on security-relevant success paths)  
7. Loopback or explicitly approved bind policy (default refuse `0.0.0.0`)  
8. Security + Phase 2/3/4 regression tests  
9. Separate production-readiness review  

**Prohibit:** public/wildcard bind by default; implicit startup; unauthenticated data reads; query-driven topology changes; raw payload endpoints; credential-bearing responses.

---

## 11. Topology boundary

All future operator/API surfaces:

- are **telemetry read-only**;
- **cannot** create/update/delete topology edges;
- **cannot** infer cables, ownership, or trust;
- **cannot** alter maps;
- **cannot** treat telemetry as topology evidence without **Gate E** + separate authorization.

---

## 12. Gate D decision checklist

Gate D is **documented-pass** when all are true here; **implementation-pass** requires a later authorized effort:

- [x] Principal classes explicit (§2)
- [x] Permission matrix complete (§4)
- [x] Read and export separate (§4, §6)
- [x] Audit read separate from snapshot read (§4)
- [x] Raw payload access denied (§4)
- [x] Topology writes denied (§4, §11)
- [x] Response and error schemas defined (§5, §8)
- [x] Redaction behavior explicit (§5–§6, §9)
- [x] Query/resource controls specified (§7)
- [x] Listener prerequisites explicit (§10)
- [x] **No listener or API implementation added by this effort**

---

## Explicit non-goals

Operator/API exposure exists · HTTP/HTTPS/mTLS readiness · production authz/rate limits/performance · persistence readiness · compliance certification · live telemetry · topology integration.

## Validation

```bash
python3 -m pytest tests/test_phase4_gate_d_operator_api_exposure.py \
  tests/test_phase4_telemetry_lab_audit.py \
  tests/test_phase4_telemetry_lab_ingest.py -q --tb=short
python3 scripts/validate_mandatory_qa_manifest.py
```
