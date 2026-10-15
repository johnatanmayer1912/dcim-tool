# Phase 4 — Zero Trust gate for future telemetry transport and persistence

| Field | Value |
|---|---|
| **Status** | Architecture / security **gate only** — not implemented |
| **Predecessor** | Phase 3 fixture-only telemetry (API frozen) |
| **Code freeze** | Do not implement live transport, auth, persistence, UI, or collectors under this document |
| **Related** | `tests/qa/PHASE3_TELEMETRY_ACCEPTANCE.md`, `utils/telemetry/`, `.cursor/docs/ZERO_TRUST_MATRIX.md`, `utils/api_security.py` |

This document defines **must-pass** Zero Trust requirements before any future live telemetry transport, authentication, ingestion, durable storage, or operator-facing exposure.

It is **not** a certification, production readiness claim, or implementation plan.

---

## 1. Trust boundaries

| Boundary | Trust posture | Notes |
|---|---|---|
| **Device** | Untrusted telemetry source | May be compromised, spoofed, or clock-skewed |
| **Collector / agent** | Semi-trusted; must authenticate | Separate identity from devices and operators |
| **Ingestion boundary** | Hostile until authenticated + validated | Default-deny; size/rate limited |
| **Normalization boundary** | Untrusted input → contract model | Reuse Phase 3 quarantine / secret rejection |
| **Catalog boundary** | Trusted config, untrusted path strings | Exact lookup; never execute paths |
| **Store (in-memory or future persistent)** | Trusted process memory today; future store is high-value | Isolation + encryption requirements below |
| **Operator / API client** | Untrusted network peer unless proven | Loopback today ≠ authn; future must not rely on bind alone |
| **Topology subsystem** | Separate trust domain | Telemetry must not write edges/trust/maps |
| **Audit / security subsystem** | Privileged sink | Append-only intent; no secret material |

Cross-boundary rule: **fail closed**. Ambiguous identity, authz, schema, or freshness → reject/quarantine, never accept-by-default.

---

## 2. Identity

### Device identity
- Stable device id must map to inventory / enrollment record before live accept.
- Unknown devices: quarantine or reject; never auto-promote to trusted topology nodes.
- Duplicate identities (same id, conflicting platform/keys): reject both streams until operator resolution; record audit event.

### Collector / agent identity
- Distinct cryptographic identity from devices and operators (mTLS client cert or equivalent).
- Bound to allowed device set / metric scopes at enrollment.
- Compromised collector → revoke identity; do not rely on shared static passwords.

### Operator / service identity
- Explicit operator or service principal for query/export/admin (not “anyone on localhost”).
- Service accounts least-privilege; no shared god-token across ingest + export + admin.

### Certificates / keys
- Ownership: device keys on device; collector keys on collector; server trust anchors operator-managed.
- Rotation: documented max lifetime; overlap window; revoke-before-replace on compromise.
- Bootstrap / re-enrollment: out-of-band approval; no silent re-key from telemetry alone.
- Trust anchors: pinned or explicitly managed; no opportunistic TOFU in production paths.

### Unknown / duplicate handling
- Unknown → fail closed (reject or quarantine with opaque error to client).
- Duplicate enrollment → fail closed until human/admin workflow clears conflict.

---

## 3. Authentication and authorization

### Authentication
- Mutual authentication required for live collector↔ingest and operator↔API (mTLS and/or vault-backed session equivalent).
- Bind address (e.g. `127.0.0.1`) is **deployment hygiene**, not authentication.
- Replay of auth material: short-lived tokens/certs; reject expired/revoked.

### Authorization (default-deny)
| Capability | Allowed roles (illustrative least-privilege) |
|---|---|
| Ingest observations | `telemetry_ingest` only |
| Query store / series | `telemetry_read` |
| Export snapshot / bulk | `telemetry_export` (audited) |
| Catalog / retention admin | `telemetry_admin` |
| Topology write | **never** via telemetry roles |

- Scope every grant by device set, tenant (if multi-tenant ever appears), and metric/path prefix.
- Administrative separation: catalog/retention changes ≠ ingest rights.
- Authz failure: uniform deny; **no** leakage of existence of devices, paths, or other tenants in error bodies.

---

## 4. Transport security

Before live transport is authorized:

| Control | Requirement |
|---|---|
| Encryption in transit | TLS 1.2+ (prefer 1.3); no plaintext ingest |
| Certificate validation | Full chain + hostname/SPIFFE/SAN as designed; reject weak/self-signed unless explicitly lab-flagged |
| Trust-anchor management | Explicit store; rotation procedure; no ambient OS trust alone for collectors |
| Downgrade prevention | Disable insecure renegotiation / cleartext fallback |
| Replay resistance | Nonces, sequence, or windowed timestamps at session/message layer |
| Freshness / sequence | Reject stale or out-of-window messages per policy; never invent `source_timestamp` |
| Size limits | Hard caps on message, batch, and connection concurrency |
| Malformed handling | Reject; quarantine optional; never partially apply |

Protocol choice (gRPC, HTTPS, dial-out, etc.) is **out of scope** here; any chosen protocol must meet the table.

---

## 5. Ingestion safety

Preserve and extend Phase 3 invariants:

1. **Schema validation** before accept (contract fields, types, bounds).
2. **Catalog lookup** — known / unknown / invalid / ambiguous; ambiguous never silent-pick.
3. **Secret-like** path/payload/field rejection; errors must not echo secrets.
4. **Quarantine** malformed or policy-violating observations; quarantined never enter durable accept path.
5. **Duplicates / idempotency** — first-wins or explicit idempotent replay policy; document which.
6. **Resource exhaustion** — max batch, max store, rate limits, parser time/memory bounds (no catastrophic regex).
7. **Raw payloads** — do not persist or return by default; if retained for forensics, encrypt + ACL + retention.
8. **Safe errors** — opaque to untrusted clients; detailed reasons only in audit with redaction.

---

## 6. Persistence requirements

**No persistence is implemented in this pass.** Future durable store must satisfy:

| Topic | Gate requirement |
|---|---|
| Encryption at rest | Strong AEAD; keys not in git / reports / HTML |
| Key management | Separate from SSH device vault where practical; rotation + revoke |
| Retention / deletion | Policy TTL; verified delete; legal hold explicit |
| Backup / recovery | Encrypted backups; restore drills; no plaintext export of secrets |
| Isolation | Per-device (and per-tenant if ever) logical isolation |
| Audit immutability | Append-oriented audit; integrity check |
| Migration / rollback | Versioned schema; reversible migrations; fail closed on migrate error |

In-memory `ObservationStore` remains fixture/local only until these gates pass.

---

## 7. Audit and observability

Must record (without secrets or raw sensitive payloads):

- Authentication success/failure (principal id, not credentials)
- Authorization denials (action, scope class — not full path if sensitive)
- Quarantine / rejection (reason code)
- Duplicate / replay detections
- Configuration / catalog / retention changes
- Export / snapshot generation (who, filter class, count — not full series values if sensitive policy says so)
- Operator access to telemetry APIs

**Prohibited in logs:** passwords, tokens, private keys, vault material, full `show running-config`, unredacted secret-bearing paths, raw payloads marked sensitive.

---

## 8. Topology boundary

### Hard prohibition
Telemetry **must not** directly create or modify:

- physical links or cable relationships
- topology edges
- ownership / authority claims
- trust scores or trust tiers
- map / vis.js state
- discovery graph nodes as “proven” from counters/optics alone

Phase 2 topology-truth and Phase 3 non-goals remain in force.

### Future telemetry → topology (if ever proposed)
Requires **separate authorization** plus:

1. Written threat analysis for topology poisoning
2. Explicit evidence model (telemetry is supporting signal only unless dual-sourced)
3. No automatic edge insert from metric series
4. Operator confirmation + audit for any inferred relationship
5. Security-reviewer + topology-architect sign-off
6. Regression: Phase 2 topology-truth pack must stay green with no new false links

---

## 9. Threat model (design gate)

| Threat | Trust assumption | Control | Detection / evidence | Fail-closed | Unresolved limitation |
|---|---|---|---|---|---|
| Stolen collector credentials | Collectors can be stolen | Short-lived mTLS; revoke; scope | Auth fail spikes; anomalous device set | Reject ingest | Physical theft window before revoke |
| Compromised device | Devices lie | Inventory bind; quality flags; no topology write | Conflicting series; quarantine rates | Quarantine / ignore for topology | Device can still emit false gauges |
| Forged telemetry | Network adversaries exist | mTLS + schema + catalog | Auth/schema rejects | Drop | Insider with valid cert |
| Replayed telemetry | Replay feasible | Nonce/seq/freshness window | Replay counters | Drop | Clock skew policy tradeoffs |
| Cross-device injection | Shared channels | Device-scoped authz + identity bind | Scope violation audits | Deny | Mis-enrollment |
| Cross-tenant access | Future multi-tenant | Default single-tenant; deny cross scope | Authz denies | Deny | Not implemented today |
| Secret leakage | Logs/UI leak | Phase 3 secret rejection; audit redaction | Secret-marker tests | Reject / redact | Operator clipboard risk |
| Parser / resource exhaustion | Hostile input | Size/time limits; bounded regex | Timeout / reject metrics | Drop connection | Shared-process DoS |
| Storage compromise | Disk theft | Encryption at rest + key separation | Integrity checks | Refuse start if keys missing | Key escrow process TBD |
| Malicious / malformed paths | Paths are data | Catalog statuses; secret segment reject | Invalid/ambiguous counts | Quarantine | Novel obfuscation |
| Time / order manipulation | Clocks lie | Preserve source_ts; don’t invent; freshness caps | Skew / reorder audits | Prefer quarantine | No global time authority |
| Unauthorized export | Export is sensitive | `telemetry_export` + audit | Export event log | Deny | Insider with export role |
| Topology poisoning | Maps are high impact | Hard topology boundary (§8) | Phase 2 regression | No edge write | Social-engineer operator later |

This table is a **design gate**, not production threat-model completeness or certification.

---

## 10. Decision gates (must pass before implementation)

### Gate A — Live transport
- [ ] Protocol + TLS/mTLS design reviewed
- [ ] Size/rate/replay/freshness limits specified and testable
- [ ] No plaintext production ingest path
- [ ] Lab flag explicit if any insecure mode exists (default off)

### Gate B — Authentication
- [ ] Collector and operator identities distinct
- [ ] Mutual auth design; rotation/revocation runbook
- [ ] Loopback not treated as authn
- [ ] Auth failure messages non-leaking

### Gate C — Persistence
- [ ] Encryption at rest + key management design
- [ ] Retention/deletion/backup/isolation specified
- [ ] No secrets in backups/logs by design
- [ ] Migration/rollback plan

### Gate D — Operator / API exposure
- [ ] Default-deny RBAC (or equivalent) for ingest/read/export/admin
- [ ] Localhost bind ≠ authorization
- [ ] Export audited; sensitive fields policy defined
- [ ] CSRF/XSS considerations if browser UI ever added (separate effort)

### Gate E — Telemetry → topology integration
- [ ] Explicit separate authorization
- [ ] §8 evidence + dual-control requirements met
- [ ] Phase 2 topology-truth regression green; no invented edges
- [ ] Security-reviewer + topology-architect approval recorded

**Rule:** Implementation PRs that add live collectors, gRPC/protobuf clients/servers, durable telemetry DBs, auth for telemetry APIs, or topology writes from telemetry **must cite passed gates A–E as applicable**. Until then, Phase 3 fixture-only surface remains the only supported telemetry API.

---

## Explicit non-goals (this document)

- Implementing transport, auth, persistence, UI, or collectors
- Claiming secure production deployment
- Live vendor / gRPC / protobuf interoperability readiness
- Authentication or persistence “ready” status
- Telemetry security certification
- Complete sensor or threat coverage

## Validation (architecture gate)

```bash
python3 -m pytest tests/test_phase4_telemetry_zero_trust_gate.py \
  tests/test_phase3_telemetry_api_freeze.py \
  tests/test_phase3_telemetry_regression_slice6.py -q --tb=short
python3 scripts/validate_mandatory_qa_manifest.py
```
