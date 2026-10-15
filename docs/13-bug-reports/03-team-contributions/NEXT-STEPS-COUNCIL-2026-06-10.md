# Next Steps Council — 2026-06-10

| Field | Value |
|-------|-------|
| **Workflow** | W-NEXT-STEPS (`NEXT_STEPS_COUNCIL.md`) |
| **Application** | Network Swiss Tool Pro **v7.0.31** |
| **Council** | R-COUNCIL + all 10 roles |
| **Inputs** | Bug list (clear), CHANGELOG, enterprise QA PASS, G-10 pillars |

## Council snapshot

| Area | Status |
|------|--------|
| Open bugs (P1–P3) | **0** — medium backlog closed v7.0.30–7.0.31 |
| pytest | **155/155** |
| Doc links | **0** broken |
| EXE | `NetworkSwissToolPro_v7.0.31_OFFLINE.exe` built |
| Offline lab smoke | Mock-SSH IOS-XE + QFX5100 in CI |
| Live SSH lab | **Not automated** — field validation still required |
| Strategic debt | Old `roadmap.md` ranks pre-v7; parallel execution not shipped |

### Role one-liners

| Role | Recommendation theme |
|------|---------------------|
| **R-PROD** | Parallel device ops + clearer progress UX = biggest NOC time win |
| **R-ARCH** | Keep credential vault decoupled from plugins; extend sidebar contract for Junos root |
| **R-ENG** | Small credential JS fixes; then adapters thread pool behind existing progress hooks |
| **R-QA** | Live SSH profile file + bare EXE smoke script in enterprise gate |
| **R-SEC** | Credential GET returns secrets — add session unlock TTL doc; no API auth yet (offline PC) |
| **R-OBS** | STP/discovery job progress already good; add EXE startup diagnostic bundle export |
| **R-LIB** | Register `REBUILD_CREDENTIALS_FEATURE.md` in command center; CODE_INVENTORY body audit |
| **R-REL** | Field smoke checklist → scripted verifier beside enterprise QA |
| **R-RECON** | Add P43 credential rebuild pointer in `15-rebuild-roadmap` if porting feature elsewhere |
| **R-GOV-LIB** | Wire `/next-steps` + `/rebuild-credentials` into `PROMPT_REGISTRY` |

---

## Top 3 — Do now

| Rank | ID | Title | Hours |
|------|-----|-------|-------|
| 1 | **NEXT-001** | Live SSH lab profile + optional integration tests | 4–6h |
| 2 | **NEXT-002** | Bare EXE field smoke automation | 3–4h |
| 3 | **NEXT-003** | Credential manager UX + test hardening | 2–3h |

---

## Full recommendation table

| ID | Title | Decision | Why (engineer value) | Complexity |
|----|-------|----------|----------------------|------------|
| **NEXT-001** | Live SSH lab profile | **Do now** | Validates IOS-XE MAC + QFX5100 on real gear; closes trust gap mock tests cannot | S (4–6h) |
| **NEXT-002** | Bare EXE smoke script | **Do now** | Operators deploy single EXE offline; automates checklist in `exe-smoke-checklist.md` | S (3–4h) |
| **NEXT-003** | Credential UX fixes | **Do now** | Fix overwrite `force` bug; `become_password` → sidebar; refresh on tab open | S (2–3h) |
| **NEXT-004** | Full UI/UX audit | **Next sprint** | Swiss Tools tab density, progress consistency, mobile/small screen | M (6–8h) |
| **NEXT-005** | Parallel device execution | **Next sprint** | 50–100 device jobs: minutes → seconds (G-10 reliability + time) | L (8–12h) |
| **NEXT-006** | Discovery search-in-map | **Next sprint** | Focus hostname/MAC on Vis.js map (roadmap #7) | S (4–6h) |
| **NEXT-007** | Config drift rollback UI | **Backlog** | Post-change VLAN fail → one-click revert from backup | M (6–8h) |
| **NEXT-008** | CODE_INVENTORY truth pass | **Backlog** | Rebuild/disaster recovery accuracy | M (8h) |
| **NEXT-009** | Command center registry sync | **Backlog** | `REBUILD_CREDENTIALS`, `W-NEXT-STEPS`, enterprise QA in manual | S (1–2h) |
| **NEXT-010** | Legacy IOS encryption monitor | **Defer** | Field reports only; add parser fixture when sample output available | S (2h) |

---

## Per-item detail + implementation prompts

### NEXT-001: Live SSH lab profile

| Field | Value |
|-------|-------|
| **Decision** | Do now |
| **What it adds** | `lab_profile.yaml` + `tests/integration/test_live_ssh_lab.py` skipped unless `NST_LIVE_SSH=1` |
| **Roles** | R-QA, R-ENG |
| **Dependencies** | Lab: IOS-XE L3 switch, QFX5100 Junos 14+ |
| **Risks** | Shipping without live validation → field MAC/LLDP regressions undetected |
| **Success metric** | CI optional job green on lab; checklist signed in action log |

#### Implement NEXT-001: Live SSH lab profile

```
ACTIVATE: R-QA → R-ENG → R-REL

SCOPE:
- Files: config/lab_profile.yaml.example, tests/integration/test_live_ssh_lab.py
- Tests: IOS-XE MAC colon input; QFX5100 LLDP neighbor count ≥1
- Docs: docs/08-operations/live-ssh-lab.md, audit-test-gaps.md update

STEPS:
1. Create lab_profile.yaml.example (hosts, device_type, creds via env vars NST_LAB_USER/PASS)
2. Add integration tests that read profile; pytest.skip unless NST_LIVE_SSH=1
3. Document manual run: set env, pytest tests/integration/test_live_ssh_lab.py -v
4. Add optional [6i] block in _prebuild.py: skip if env unset, run if set

VALIDATE:
- Mock path: existing test_lab_smoke_offline.py still passes
- Lab path: engineer runs with NST_LIVE_SSH=1 on two devices

DOCUMENT:
- CHANGELOG, RELEASE_NOTES, SYNC_PROTOCOL row for lab_profile

COMMAND AFTER MERGE: /full-docs-sync
```

---

### NEXT-002: Bare EXE field smoke automation

| Field | Value |
|-------|-------|
| **Decision** | Do now |
| **What it adds** | `scripts/exe_field_smoke.py` — spawn EXE, HTTP health, plugin count API, exit |
| **Roles** | R-REL, R-QA |
| **Dependencies** | Built `dist/NetworkSwissToolPro_v7.0.31_OFFLINE.exe` |
| **Risks** | Bare-folder deploy fails silently (NEW-C1 class issues) |
| **Success metric** | Script PASS on clean temp dir with only EXE + inventory.txt |

#### Implement NEXT-002: Bare EXE field smoke

```
ACTIVATE: R-REL → R-QA → R-ENG

SCOPE:
- Files: scripts/exe_field_smoke.py, docs/08-operations/exe-smoke-checklist.md
- Wire into scripts/enterprise_qa_gate.py as optional --exe path

STEPS:
1. Copy EXE to temp dir; add minimal inventory.txt
2. subprocess.Popen EXE; poll http://127.0.0.1:5051/health (timeout 60s)
3. GET /api/health-check/run POST quick=true; assert plugins check ok
4. Terminate process; return exit code 0/1

VALIDATE:
- python scripts/exe_field_smoke.py --exe dist/NetworkSwissToolPro_v7.0.31_OFFLINE.exe

DOCUMENT:
- BUILD_GUIDE.md post-build step; action log

COMMAND AFTER MERGE: /full-docs-sync
```

---

### NEXT-003: Credential manager UX + tests

| Field | Value |
|-------|-------|
| **Decision** | Do now |
| **What it adds** | Fix duplicate overwrite; Juniper `become_password` field; tab refresh |
| **Roles** | R-ENG, R-QA |
| **Dependencies** | `REBUILD_CREDENTIALS_FEATURE.md` spec |
| **Risks** | Engineers cannot overwrite creds; Junos root not applied from vault |
| **Success metric** | `tests/test_credential_manager.py` ≥8 cases; manual Use → enable/become filled |

#### Implement NEXT-003: Credential UX fixes

```
ACTIVATE: R-ENG → R-QA

SCOPE:
- Files: modules/web/templates/index.html (addCredential force param, switchTab credentials)
- Optional: #become_password sidebar field; useCredential maps become_password
- tests/test_credential_manager.py (new)

STEPS:
1. Fix addCredential(username,..., force=false) — pass force in JSON body on overwrite
2. switchTab: if tabId==='credentials' loadCredentials()
3. Add tests/test_credential_manager.py per REBUILD_CREDENTIALS_FEATURE.md Phase 6
4. Optional: become_password → new sidebar field wired to plugins expecting root

VALIDATE:
- pytest tests/test_credential_manager.py
- python scripts/enterprise_qa_gate.py

DOCUMENT:
- REBUILD_CREDENTIALS_FEATURE.md known-quirks section → mark fixed
- CHANGELOG v7.0.32

COMMAND AFTER MERGE: /full-docs-sync
```

---

### NEXT-004: Full UI/UX audit

| Field | Value |
|-------|-------|
| **Decision** | Next sprint |
| **What it adds** | W-UI-UX report: tab order, progress bars, error recovery, credentials modal vs prompt() |
| **Roles** | R-PROD, R-ENG, R-LIB |
| **Dependencies** | Run `UI_UX_AUDIT.md` workflow |
| **Risks** | Swiss Tools feels “engineer-unfriendly” vs single-purpose CLI scripts |
| **Success metric** | `W-UI-UX-YYYY-MM-DD.md` with ≥10 prioritized fixes |

#### Implement NEXT-004: UI/UX audit

```
ACTIVATE: R-PROD → R-ENG → R-LIB (run UI_UX_AUDIT.md)

SCOPE:
- Deliverable: docs/14-bug-reports/W-UI-UX-2026-MM-DD.md
- Focus: sidebar credential flow, discovery command center, search-it progress

STEPS:
1. Execute /ui-ux-audit per roles/UI_UX_AUDIT.md
2. Council ranks top 5 quick wins (S) vs structural (L)
3. Implement top 3 quick wins in following sprint

VALIDATE:
- Peer review + engineer walkthrough checklist

COMMAND AFTER MERGE: /full-docs-sync
```

---

### NEXT-005: Parallel device execution

| Field | Value |
|-------|-------|
| **Decision** | Next sprint |
| **What it adds** | `ThreadPoolExecutor` in `adapters.py` multi-device loops with max_workers config |
| **Roles** | R-ARCH, R-ENG, R-QA |
| **Dependencies** | Thread-safe log_queue; plugin registry already supports parallel metadata |
| **Risks** | Sequential SSH remains #1 complaint for 50+ device inventories |
| **Success metric** | 50-device connectivity check ≤30s on lab; no log interleaving corruption |

#### Implement NEXT-005: Parallel execution

```
ACTIVATE: R-ARCH → R-ENG → R-QA

SCOPE:
- Files: modules/adapters.py (run_* thread pools), config default max_workers=10
- Tests: mock devices timing test; thread safety on log_queue

STEPS:
1. Extract _run_devices_parallel(devices, fn, max_workers) helper
2. Migrate connectivity, vlan_check, mac_check first (highest use)
3. Preserve per-device log prefixes; cap workers for fragile networks
4. Add config/env NST_MAX_WORKERS

VALIDATE:
- pytest + manual 20-device inventory timing
- _prebuild.py unchanged gates PASS

DOCUMENT:
- MODULE_ARCHITECTURE.md concurrency section, CHANGELOG

COMMAND AFTER MERGE: /full-docs-sync
```

---

### NEXT-006: Topology map search / focus

| Field | Value |
|-------|-------|
| **Decision** | Next sprint |
| **What it adds** | Search box on topology + discovery HTML maps; highlight node + neighbors |
| **Roles** | R-ENG, R-PROD |
| **Dependencies** | vis-network datasets in report_formatter / discovery_map_formatter |
| **Risks** | Large maps unusable without focus |
| **Success metric** | 200-node demo map: search <200ms to focus |

#### Implement NEXT-006: Map search

```
ACTIVATE: R-ENG → R-QA

SCOPE:
- Files: utils/topo_map_shell.py, utils/discovery_map_formatter.py, index.html topology tab

STEPS:
1. Add search input + JS filter on nodes Dataset
2. Highlight match + 1-hop neighbors; dim others
3. Contract test: discovery HTML contains search input id

VALIDATE:
- tests/test_discovery_map_html_contract.py extended

COMMAND AFTER MERGE: /full-docs-sync
```

---

### NEXT-007: Config drift rollback UI

| Field | Value |
|-------|-------|
| **Decision** | Backlog |
| **What it adds** | After failed VLAN post-check, offer revert from `config_backup_system` snapshot |
| **Roles** | R-ENG, R-PROD |
| **Dependencies** | `utils/config_backup_system.py` |
| **Success metric** | Simulated failed rename → revert restores prior VLAN name |

---

### NEXT-008: CODE_INVENTORY truth pass

| Field | Value |
|-------|-------|
| **Decision** | Backlog |
| **What it adds** | Line-accurate `docs/02-codebase/CODE_INVENTORY.md` for disaster recovery |
| **Roles** | R-LIB, R-RECON |
| **Success metric** | DISASTER_RECOVERY_COMMAND batch audit PASS |

---

### NEXT-009: Command center registry sync

| Field | Value |
|-------|-------|
| **Decision** | Backlog |
| **What it adds** | `REBUILD_CREDENTIALS_FEATURE`, `enterprise_qa_gate`, `/next-steps` in PROMPT_REGISTRY + COMMAND_MANUAL.html |
| **Roles** | R-GOV-LIB |
| **Success metric** | All W-* workflows listed in `ROLES_BY_COMMAND_REFERENCE.md` |

---

### NEXT-010: Legacy IOS encryption fallback

| Field | Value |
|-------|-------|
| **Decision** | Defer |
| **What it adds** | Fixture when field provides `show version` from legacy IOS SSH |
| **Roles** | R-ENG |
| **Trigger** | First field report of handshake failure |

---

## Conflicts resolved

| Tension | Council ruling |
|---------|----------------|
| Parallel execution vs UI polish | **Parallel first** (NEXT-005) for time savings; UI audit (NEXT-004) same sprint if capacity |
| React rewrite (old roadmap #4) | **Defer** — violates offline simplicity; improve Jinja2 Swiss Tools instead |
| RBAC (old roadmap #8) | **Backlog** — single-engineer offline PC deployment model; document in threat model |

---

## Follow-up commands

| User says | Action |
|-----------|--------|
| `implement NEXT-001` | Run NEXT-001 prompt block |
| `/full-fix-and-ship NEXT-003` | Credential fixes + v7.0.32 |
| `/ui-ux-audit` | NEXT-004 deliverable |
| `/full-docs-sync` | After any NEXT item ships |

**Cross-link:** [`team-meeting-synthesis.md`](team-meeting-synthesis.md) · [`docs/00-overview/roadmap.md`](../../00-overview/roadmap.md)
