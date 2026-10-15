# Network Swiss Tool Pro v7.0.1 — Discovery & Map Trustworthiness

**Release date:** 2026-05-24  
**Artifact:** `dist/NetworkSwissToolPro_v7.0.1_OFFLINE.exe`

## Highlights

- **BUG-0007 fixed:** Cisco Nexus CDP platform strings no longer classified as JunOS (`ex` inside `nexus` trap removed).
- **Canonical device merge:** One node per switch (IP + hostname aliases unified) before map and JSON export.
- **Map labels:** `hostname` + `NX-OS · model` (or IOS/JunOS) for scanned devices; `os_source` on nodes for diagnostics.
- **Swiss Tools maps:** Endpoint name normalization on topology edges (parity with Discovery).
- **Plugin** `network_discovery` **1.3.0** with graph validation warnings in crawl logs.

## Upgrade notes

- Re-run Discovery after upgrade; old HTML maps may still show duplicate nodes until regenerated.
- See [`docs/08-operations/discovery-trust-validation.md`](../08-operations/discovery-trust-validation.md).

## QA gate

Classifier, dedup, discovery parser tests, `_prebuild.py`, `_master_qa_test.py` — all required green before EXE deploy.
