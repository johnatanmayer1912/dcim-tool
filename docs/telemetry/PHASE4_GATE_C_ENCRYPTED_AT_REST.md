# Phase 4 — Gate C: Encrypted-at-rest design and persistence boundary

| Field | Value |
|---|---|
| **Status** | Architecture / security **design gate only** — **not implemented** |
| **Predecessor** | `PHASE4_ZERO_TRUST_GATE.md` §6 / Gate C; lab ingest (`lab_ingest.py`) in-process only |
| **Code freeze** | No durable store, DB, file persistence, encryption library wiring, HTTP, mTLS, gRPC, UI, alerting, or topology integration in this pass |
| **Related** | Phase 3 API freeze; `modules/credential_manager.py` (Fernet vault pattern — **analogy only**); `utils/output_paths.get_data_root()` |

**Question this gate answers:**  
What must be true before normalized telemetry, metadata, audit events, or snapshots may be written beyond process memory?

This document is **not** encrypted persistence, production KMS, compliance certification, or recovery readiness.

---

## 1. Persistence scope

| Data type | Persist? | Sensitivity | Retention class | Scope | Raw payloads |
|---|---|---|---|---|---|
| Normalized observation fields (contract) | **Optional** (future) | Medium–High (ops intel) | `obs_hot` / `obs_warm` | device (+ tenant if ever) | **Forbidden** |
| `source_timestamp` / `received_at` | With observation | Medium | Same as observation | device | N/A |
| Catalog metadata (status, kind, unit) | Optional denormalized copy | Low–Medium | `obs_*` or `config` | global catalog + per-obs | Forbidden |
| Delta metadata (computed) | Optional / derived | Medium | Prefer recompute; short `derived` if cached | device/series | Forbidden |
| Snapshot summaries | Optional export artifact | Medium–High | `snapshot_export` | operator export ACL | **Forbidden** |
| Quarantine records (reason codes, ids) | **Required** if live ingest persists | Medium | `quarantine` | device | Forbidden (no raw body) |
| Authentication events | **Required** if auth exists | Medium | `audit_long` | principal | No secrets/tokens |
| Authorization events | **Required** | Medium | `audit_long` | principal + action class | No path secret echo |
| Rejection / duplicate events | Recommended | Low–Medium | `audit_short` / with quarantine | device | Forbidden |
| Configuration / key **metadata** (ids, versions, not material) | **Required** with keys | High (meta) | `config` | system | Key **material** never in DB rows |

**Raw payloads:** prohibited from durable telemetry stores, backups, snapshots, and default exports. Forensic retention (if ever) needs a **separate** encrypted vault, ACL, and TTL — out of Gate C implementation scope.

**Today:** only in-memory `ObservationStore` is authorized. Any disk write of the above is **Gate C blocked** until checklist §11 passes and a separate implementation effort is authorized.

---

## 2. Encryption at rest

Future durable telemetry storage must provide:

| Control | Requirement |
|---|---|
| Storage encryption | All observation, quarantine, snapshot-on-disk, and audit blobs encrypted at rest |
| Authenticated encryption | AEAD (encrypt-then-MAC / integrated AEAD); ciphertext alone insufficient |
| Nonce / IV uniqueness | Never reuse (key, nonce) pairs; fail closed on reuse detection |
| Integrity verification | Decrypt/verify before trust; mismatch → reject record |
| Key separation | Telemetry DEKs ≠ SSH/device vault keys where practical |
| Key hierarchy | KEK wraps DEKs; DEKs encrypt data partitions (e.g. per-device or per-epoch) |
| Data-encryption keys (DEK) | Scoped; rotatable; never logged |
| Key-encryption keys (KEK) | Higher privilege; operator/KMS-backed; not in application data files |
| Key rotation | Re-wrap or re-encrypt plan; dual-key read window; documented max lifetime |
| Revoked / expired keys | Cannot decrypt new writes; reads of old epochs only if policy allows + audited |
| Backup encryption | Backups encrypted with backup-specific wrapping; no plaintext dumps |
| Temporary files | Encrypt or avoid; scrub on success/failure; no plaintext crash dumps of observations |
| Crash / recovery artifacts | WAL/journal ciphertext only; incomplete records discarded or quarantined |
| Cache / export | Memory caches cleared on lock; exports need `telemetry_export` + encrypted transit/at-rest if written |

**Library choice:** deferred. NST already uses Fernet for credentials — telemetry persistence **may** follow a similar local pattern or a stronger KMS later, but **must not** hard-code keys or reuse `.credential_key` bytes for telemetry DEKs without an explicit security design addendum.

---

## 3. Key management

| Topic | Gate requirement |
|---|---|
| Ownership | Operator/org owns KEKs; process holds unwrapped DEKs only while unlocked |
| Source | Derived from operator secret and/or OS/KMS; never embedded in repo or EXE resources |
| Bootstrap | Out-of-band; lab keys ≠ production keys; distinct key namespaces |
| Rotation cadence | Documented maximum; emergency rotate on suspicion |
| Revocation | Immediate deny for new encrypt; audit event |
| Destruction | Crypto-shred DEKs where feasible; verify unavailability |
| Recovery | Split knowledge / escrow policy explicit; no single sticky note |
| Separation of duties | Key admin ≠ routine ingest; key admin ≠ unaudited export |
| Test vs production | Separate key material and storage roots (`get_data_root()` isolation in tests) |
| Hard-coded keys | **Prohibited** |
| Env / log exposure | **Prohibited** — no DEK/KEK/password in logs, HTML, snapshots, `/api/logs` |
| Missing / stale / revoked / unavailable keys | **Fail closed**: refuse start of persist path; refuse decrypt; refuse export that needs keys |

Fail-closed examples: missing key provider → do not fall back to plaintext; invalid key → abort operation; revoked key → deny write and sensitive read.

---

## 4. Access control

Default-deny permissions (extend lab stub names; not implemented here):

| Operation | Permission (illustrative) |
|---|---|
| Ingest → memory / future persist | `telemetry_ingest` |
| Persist flush / durable write | `telemetry_persist` (distinct from ingest if separated) |
| Query | `telemetry_read` |
| Snapshot export | `telemetry_export` |
| Deletion | `telemetry_delete` |
| Retention admin | `telemetry_admin` |
| Backup / restore | `telemetry_backup` / `telemetry_restore` |
| Key administration | `telemetry_key_admin` |
| Audit access | `telemetry_audit_read` |

Require: least privilege; device/tenant scoping on ingest/query/delete; operator vs collector vs key-admin separation; explicit export permission; **no raw-payload export** capability.

Localhost bind remains **not** authentication (see Gates A/B).

---

## 5. Integrity and replay

| Topic | Requirement |
|---|---|
| Record integrity | AEAD tag / HMAC over canonical serialization |
| Record identity | Stable `observation_id` (Phase 3 rules) |
| Uniqueness | Durable first-wins or explicit idempotent upsert policy — document one; default **first-wins** aligned with store |
| Append / update | Prefer append-only observation log; updates only for retention tombstones |
| Freshness metadata | Preserve `source_timestamp` / `received_at`; **never invent** timestamps |
| Replay detection | Reject duplicate ids / replayed ciphertext with same id different body |
| Tamper detection | Integrity fail → quarantine or discard; audit |
| Clock uncertainty | Treat source clocks as untrusted; ordering rules stay Phase 3 (source → received → insert); no global time authority claimed |
| Restore / replay safety | Restored data must not silently re-ingest as “new” without idempotency checks |

---

## 6. Retention and deletion

| Class | Guidance (policy knobs; not shipped) |
|---|---|
| Observations | Configurable TTL; default short for lab; production TBD by ops policy |
| Quarantine | ≥ observation TTL or fixed floor for forensics of rejects |
| Audit | Longer than observations; immutable intent |
| Snapshots on disk | Short TTL unless export archive policy |
| Backups | Tied to recovery RPO; encrypted; separate TTL |
| Deletion auth | `telemetry_delete` + audit |
| Legal / operational hold | Explicit hold flag blocks delete; audited |
| Secure deletion | Overwrite or crypto-shred DEK where feasible; OS limits acknowledged |
| Tombstones | Deletion evidence retained in audit; observation body gone |
| Partial deletion | Fail closed or transactional; never leave plaintext residue in temp |

---

## 7. Backup and recovery

- Backups **must** be encrypted; plaintext telemetry dumps prohibited.
- Restore requires key availability **and** `telemetry_restore` authorization.
- Post-restore: re-apply device/tenant ACLs; refuse cross-scope leakage.
- Rollback: versioned schema; refuse load of unsupported/corrupt sets.
- Corruption: detect via integrity checks; isolate bad records.
- Every restore: audit who/when/what scope/counts (not payloads).
- Prevent stale/replayed re-entry via observation_id idempotency and backup generation markers.

---

## 8. Failure modes (fail-closed)

| Failure | Behavior | Client error |
|---|---|---|
| Unavailable key provider | Refuse persist/decrypt/export | Generic unavailable |
| Invalid key | Abort | Generic auth/crypto failure |
| Revoked key | Deny | Generic denied |
| Corrupted record / integrity mismatch | Quarantine or drop; audit | Generic rejected |
| Unsupported schema | Refuse migrate/load | Generic unsupported |
| Unauthorized query / export | Deny | Generic authorization denied |
| Retention / deletion failure | Do not claim success; retry or alert ops via audit | Generic failure |
| Backup / restore failure | Leave store unchanged if possible | Generic failure |
| Disk / resource exhaustion | Stop accepts; fail closed | Generic unavailable |

**Never** in errors: secrets, raw payloads, key material, full sensitive paths.

---

## 9. Topology boundary

Hard rules (unchanged from Phase 2/3/4 ZT):

- Persistence **cannot** create topology edges or cable relationships.
- Snapshots **cannot** create trust, ownership, or map state.
- Restore **cannot** mutate topology modules or discovery graphs.
- No telemetry record is topology evidence by itself.
- Future telemetry→topology requires **Gate E** + separate authorization (see `PHASE4_ZERO_TRUST_GATE.md`).

---

## 10. Migration path (future only — not this effort)

Ordered phases; each preserves Phase 3 frozen API and lab in-process boundaries until explicitly re-authorized:

1. **Persistence interface** — abstract repository over memory vs future encrypted backend  
2. **Encrypted repository** — AEAD blobs under `get_data_root()` isolation  
3. **Key-provider adapter** — lab stub vs production KEK source  
4. **Migration / versioning** — schema epoch; rollback tests  
5. **Audit integration** — redacted event sink  
6. **Recovery tests** — fixture-only encrypt/decrypt round-trip (still no live collectors)  
7. **Operator / API authorization** — Gate D alignment  
8. **Production readiness review** — separate release gate; no claim from this doc  

Lab ingest must continue to refuse `enable_persistence=True` until an authorized implementation cites this Gate C checklist as passed **and** ships tests proving fail-closed key behavior.

---

## 11. Decision checklist — Gate C pass criteria

Gate C is **documented-pass** (design) when all are true in this artifact; **implementation-pass** requires a later effort:

- [x] Data classification complete (§1)
- [x] Raw payload policy explicit (forbidden in default durable paths)
- [x] Encryption and integrity controls defined (§2, §5)
- [x] Key lifecycle defined with fail-closed (§3, §8)
- [x] Access controls default-deny (§4)
- [x] Replay / duplicate behavior explicit (§5)
- [x] Retention / deletion explicit (§6)
- [x] Backup / recovery explicit (§7)
- [x] Failure behavior fail-closed (§8)
- [x] Topology boundaries hard (§9)
- [x] **No persistence code introduced by this effort**

**Implementation remains blocked** until a separately authorized change set implements the above with tests — this document alone does **not** authorize disk writes.

---

## Explicit non-goals

Encrypted persistence exists today · production key management · storage/compliance certification · production recovery readiness · live telemetry · mTLS/gRPC · topology integration · security certification.

## Validation

```bash
python3 -m pytest tests/test_phase4_gate_c_encrypted_at_rest.py \
  tests/test_phase4_telemetry_lab_ingest.py \
  tests/test_phase4_telemetry_zero_trust_gate.py -q --tb=short
python3 scripts/validate_mandatory_qa_manifest.py
```
