# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 7.4.33 — Full-program validation harden + governance restore

- **Zero Trust** — Demo discovery skips vault overlay; interface validate surfaces missing `proposed_config` before credential resolve; adapter tests use vault `credential_id`.
- **A11y / Apex** — Operator contrast tokens (`--text-muted` / `--text-secondary` / success / chrome pills); `aria-label="Operator jobs"` on command strip.
- **Packaging** — Semver-aware latest `.spec` picker; `NetworkSwissToolPro_v7.4.33.spec` with `modules/plugins` + Failure Correlation hiddenimports.
- **Governance** — Restored `.cursor/docs/` (baseline, pilot, offline, live-lab, airgap); added native `zero-trust-audit-360` skill + questionnaire.
- **Contract** — `failure_correlation` registered in execute UI contract + EXECUTE_ACTION_CONTRACT.
- **Lab / QA** — Lab exhaustive 33/33 on Docker SSH fabric; pytest ~3525+; Playwright correlation + credential/L3 suites; TEAM_VALIDATION_REGISTER for this train.
- **VERSION** — `7.4.33`.

### 7.4.32 — Failure Correlation Engine + wide competitive review

- **Competitive review** — Wide peer map (Netdisco, Oxidized, LibreNMS, SuzieQ, NAPALM, Batfish, SIEM, commercial) → `.cursor/audits/COMPETITIVE_REVIEW_WIDE_2026-10-10.md`.
- **Feature** — Failure Correlation Engine: SSH logs + interface/vPC context → ranked “why” hypotheses with evidence (`modules/failure_correlation/`, execute `failure_correlation`, UI tile, `/api/failure-correlation/*`).
- **Lab** — Logging + degraded vPC fixtures for NX-OS leaves / IOS access.
- **Docs** — `docs/07-operations/FAILURE_CORRELATION_ENGINE.md`.
- **QA** — `tests/test_failure_correlation_engine_v7432.py` (600+), Playwright `tests/browser/failure_correlation.spec.mjs`.
- **VERSION** — `7.4.32`.

### 7.4.31 — L3 empty-map root cause + enterprise validation matrix

- **Root cause** — L3 map showed 0/0/0/0 because lab SSH returned `% Invalid input` for `show ip route` (no fixtures); HTML shell still rendered → false “success”.
- **Lab** — Added IOS/NX-OS `show ip route` fixtures for the 3-node fabric; handler serves them.
- **Honesty** — L3 HTML empty-state banner; bundle injects SSH-OK device markers when routes=0; observation field.
- **QA** — `tests/test_enterprise_zero_trust_matrix_v7431.py` (500+ cases); exhaustive validator requires `route_count >= 1`.
- **VERSION** — `7.4.31`.

### 7.4.30 — Lab SSH echo fix + map honesty + fail-closed credential_id

- **Lab** — SSH sim echoes CLI commands (Netmiko `terminal width 511` / length); expanded fixtures (VLAN/MAC/vPC empty-honest). Rebuild: `lab/docker`.
- **Bug** — Topology jobs no longer report `complete` when no HTML is produced.
- **Bug** — `/api/execute` no longer silently reuses session `credential_id` when the body omits it (hidden-credentials class).
- **Maps** — Standard L2 drops legacy side-panel DOM; Program Status is a collapsed honesty strip (not a red HARD STOP wall); title `Standard L2 Map`.
- **QA** — Exhaustive validator checks map HTML artifacts + reject-without-credential_id; fabric tests updated.
- **VERSION** — `7.4.30`.

### 7.4.29 — Docker lab fabric + credential UX + Standard L2 polish

- **Lab** — Docker SSH fabric: 1× IOS C9300 + 2× NX-OS **N9K-C93180YC-EX** with CDP fixtures (`lab/docker/`, `lab/fixtures/`). Exhaustive API validator: `scripts/lab_exhaustive_validate.py`.
- **Credentials** — Settings password fields are draft-only (never sent); sync hidden `credential_id` from sidebar Primary; clearer alert when vault not selected / vault locked.
- **Maps** — Standard L2 shell uses Apex cyan accents; removed DEBUG noise from topology HTML generation.
- **VERSION** — `7.4.29`.

### 7.4.28 — Inventory utilities tile layout (Apex)

- **GUI** — Inventory Utilities (OS audit / Cisco asset & warranty / Port interface map) no longer overlap: multi-line `btn-mac` tiles use column flex + wrap (`nst-tile-btn`), same pattern as map tiles; Apex pill override does not force row/`nowrap` on tiles.
- **QA** — `tests/test_inventory_utilities_tiles_v7428.py`.
- **VERSION** — `7.4.28`.

### 7.4.27 — Asset Warranty Consolidated Report (go-live harden)

- **Consolidator** — After serial/UUID dedup across CSV/HTML/JSON/TXT/XLSX inputs, re-enrich every device from bundled `config/cisco_eol_database.db` (authoritative EOL/EOS/EOSe + lifecycle status).
- **Field honesty** — `End of Life` maps to `end_of_life` (not contract `warranty_end`); exports (HTML/CSV/JSON/XLSX) emit DB-backed lifecycle dates.
- **EOL DB** — Reseeded 114 Cisco models with refreshed `last_updated` (`seed_cisco_eol_database.py`).
- **QA** — Warranty/EOL suites updated for demo-aligned CSV columns + DB enrich expectations (81 tests).
- **VERSION** — `7.4.27`.

### 7.4.26 — Credentials without daily master password

- **Vault model** — Daily credential use relies on the local machine key (`.credential_key`). No master password required to list, select, or resolve credentials.
- **Legacy unlock** — Existing master-password vaults unlock once, then auto-migrate to the machine key (gate cleared).
- **API** — `POST /api/credentials/master-password/set` retired (400 + guidance). Status exposes `ready` / `mode=machine_key`. New `POST .../clear` for open vaults.
- **GUI** — Settings “Credential vault” panel; vault pill “Vault ready”; no blocking prompt on credential load; export-with-password remains for portable backups.
- **QA** — `tests/test_vault_no_master_password_v7426.py` + credential manager migration cases; mandatory security gate updated.
- **VERSION** — `7.4.26`.

### 7.4.25 — Apex Fusion shell parity (live ≡ mock layout)

- **Shell rebuild** — Live console now uses the Option 4 stage: atmospheric glass HUD, icon rail (INV/MAP/FIND/…), glass drawer, glass main, instrument console, command strip — matching `04_team_apex_fusion.html` structure (trusted metrics only; no invented fleet KPIs).
- **CSS** — Apex overrides win over legacy Apple inline chrome; cyan/teal pill CTAs; soft danger Cancel/Stop; Outfit-like offline font stack (no CDN).
- **QA** — `tests/test_apex_fusion_v7424.py` shell contract expanded (rail/drawer/main/console/hero).
- **VERSION** — `7.4.25`.

### 7.4.24 — Apex Fusion GUI (Northglass × OpsRail)

- **Option 4 mock** — `mocks/gui_external_audit_2026-10-07/04_team_apex_fusion.html` (council wow concept for operators + managers).
- **Live shell** — `nst-enterprise.css` Apex Fusion tokens (cyan/teal signal, glass atmosphere, command strip, brand hero); body `nst-apex-fusion`.
- **Trusted HUD** — session Vault / Credential / Scope / Live job mirrors real chrome + control-plane state (no invented fleet metrics).
- **Docs** — `.cursor/audits/APEX_FUSION_GUI_2026-10-07.md`; index updated.
- **QA** — `tests/test_apex_fusion_v7424.py` + mandatory `every_code_change`.
- **VERSION** — `7.4.24`.

### 7.4.23 — God-mode multi-expert perfection (no new features)

- **Audit** — `.cursor/audits/GODMODE_AUDIT_REGISTER_v7423.md` + `.cursor/audits/GODMODE_RESULTS_v7423.md` (backend/security, frontend/UI, Cisco/Juniper/Netmiko council).
- **Security** — `contained_run_dir` realpath containment; IM/L3/topology open-report path gates; credential export/import confined to exports dir; vault save fail-closed; overlay APIs require vault `credential_id`; credential list requires unlock; secondary vault resolve fail-closed; unified `resolve_web_port()`.
- **Vendor** — Discovery multi-driver SSH fallback (no silent IOS for Juniper peers); IM vendor-specific list fallbacks + `send_config_set` deploy; Junos LACP/`inet6.0`/chassis SN; path_trace Junos port normalize; honest Junos persist logging.
- **UI** — IM/Standards XSS escaping; health wizard a11y via `nstSetDialogOpen`; emoji-strip copy repair; Inter→`--font-ui`; console collapse CSS; VLAN step reset; IM label `for=`.
- **VERSION** — `7.4.23`.

### 7.4.22 — Full UI closeout (plan → checklist → green)

- **Plan** — `.cursor/audits/CLOSEOUT_PLAN_v7422.md` (implementation + validation IDs). Results: `.cursor/audits/CLOSEOUT_RESULTS_v7422.md` via `scripts/run_closeout_checklist_v7422.py`.
- **Design system extraction** — `modules/web/static/nst-enterprise.css` served at `/static/nst-enterprise.css`; linked from operator console.
- **Emoji-free operator chrome** — IM / Standards / Discovery / Templates / Plugins decorative glyphs removed; empty states are text-only.
- **Map shells** — `utils/map_shell_theme.py` wired into L3, Standard L2, vPC, Discovery, Topo; chrome accent `#0a84ff` (peer-link legend colors remain semantic).
- **Dead ends** — onclick inventory + IM Refresh/Export/Clear/Download + Evidence/credentials/path/plugins/SNMP/health APIs validated by checklist.
- **VERSION** — `7.4.22`.

### 7.4.21 — Outside UI audit + enterprise shell

- **Outside audit** — Independent UX review (`.cursor/audits/OUTSIDE_UI_AUDIT_2026-10-06.md`): dull flat shell, gutted sidebar brand, mixed button languages, purple Tools card, emoji credential labels, stale chrome date.
- **Enterprise shell** — Frosted dark chrome, pill workspace nav, restored sidebar brand tile, elevated cards/forms, calm graphite+system-blue system (no purple novelty).
- **Control honesty** — Credential labels cleaned; CLI connect uses primary mac button; Config backup panel neutralized; chrome Stop styled consistently.
- **Verification** — `tests/test_outside_ui_audit_v7421.py` (onclick inventory + API smoke for credentials/jobs/maps/plugins/backups/health). Mandatory `every_code_change` green.
- **VERSION** — `7.4.21`.

### Gap closeout — NOC daily + Apple console (this pass)

- **Backup health advice** — stale/missing backup messages point to Tools → Config backup & save (not legacy “Run Config Backup”); age check also sees `outputs/config_backup`.
- **Path reconstruct gate** — requires real L2 edges from `04_final_map_data.json` (`edge_count` / `/api/topology/edges-status`); HTML/status alone no longer enables the button.
- **Plugin history UI** — Version history panel + optional localhost rollback (`POST /api/plugins/rollback`).
- **L3 Animate LPM flow** — toolbar button animates last Trace Flow path (or protocol-evidenced edges); no random traffic fake.
- **First-launch health wizard** — glass Apple-style dialog, clearer copy.
- **ntc-templates / NAPALM-style / SNMP graphs** — `modules/ntc_parse.py`, `modules/napalm_style.py`, `modules/snmp_interface_graphs.py` + Tools SNMP graphs panel + `/api/capabilities/parsers`.
- **UI** — Apple-inspired glass sidebar/cards, SF Pro stack, electric-blue accent, atmospheric background.
- **Tests** — `tests/test_gap_closeout_noc.py`.

### Functional gap closeout (daily NOC dead-ends)

- **Tools Backup → Compare catalog** — successful Tools backups also register into `ConfigBackupSystem`; compare list also includes `outputs/config_backup` run files.
- **Evidence Open / Reveal / Pack / Re-run** — `GET .../open`, `POST .../reveal`, Pack ZIP, `POST .../rerun` (current vault session; no stored passwords).
- **Edit Credential** — Settings Edit opens modal → `POST /api/credentials/update`.
- **Keyboard** — `6` Reports, `7` Settings.
- Audit: `.cursor/audits/FUNCTIONAL_GAP_CLOSEOUT_2026-10-06.md`.

### OSS competitive wow slice (NOC daily + manager share)

- **Evidence pack ZIP** — `GET /api/jobs/<task_id>/pack` packs contained `outputs/` run folders (`utils/evidence_pack.py`); Evidence workspace Download button (skips `.credential_key`).
- **Config backup list + unified diff** — `GET /api/backups`, `POST /api/backups/diff` with path containment under `data_root/backups` (`utils/backup_api.py`); Tools UI compare panel.
- **Fleet reachability matrix** — execute action `reachability_matrix` builds HTML/CSV host×ping×SSH cards (`utils/reachability_matrix.py`); Open last matrix.
- **Skill** — `.cursor/skills/nst-oss-competitive-excellence/SKILL.md` + audit `.cursor/audits/OSS_COMPETITIVE_EXCELLENCE_2026-10-06.md`.
- **Tests** — `tests/test_oss_wow_noc_features.py`.

### 7.4.20 — Cisco Asset & Warranty Hardware UUID Deduplication, Attribute Merging & Duplicates Audit

- **Hardware UUID Deduplication (`utils/asset_warranty_consolidator.py`)** — Ingested multi-file reports (CSV, HTML, JSON, TXT) now normalize device serial numbers as authoritative hardware UUIDs (`SN:<SERIAL>`). Identical devices across files are validated and deduplicated rather than duplicated in inventory totals.
- **Intelligent Attribute Merging & Enrichment** — When identical hardware UUIDs are detected across separate files, attributes are non-destructively merged (e.g. Hostname/IP from file 1 combined with Model/PID and EOL dates from file 2). Discrepancies and conflicts (such as differing hostnames or differing IPs across files) are detected and recorded.
- **Statistical Integrity Protection** — Summary metrics (`model_counts` and `warranty_status_counts`) are now calculated strictly on the deduplicated master devices, preventing double-counting and hardware count inflation.
- **Dedicated Duplicates Audit Across All Outputs**:
  - **Master HTML**: Added summary cards for "Raw Rows" and "Duplicates Merged", plus an amber "⚠️ Duplicate Hardware Audit" table detailing each duplicate UUID, occurrence multiplier badge, source files, and conflict notes.
  - **Master XLSX**: Added a dedicated second tab `"Duplicates Audit"` with custom styling, auto-fitted columns, and freeze panes alongside `"Master Inventory"`.
  - **Master JSON**: Ingests `duplicates_summary` (raw counts, unique counts, duplicates removed) and an array of `duplicates_audit` records.
  - **Operator Web UI**: Enhanced `#asset-warranty-consolidate-status` with a yellow badge displaying the number of unique devices and duplicates merged across files.
- **Prebuild & Offline Packaging** — Updated `tests/qa/MANDATORY_MANIFEST.yaml` (`minimum_app_version: 7.4.20`), verified `_prebuild.py` passes 100%, and generated `NetworkSwissToolPro_v7.4.20.spec`.

### 7.4.19 — L3 Path Tracer + Unified Canvas (STP layer) + Quad Consolidated Inventory Export

- **L3 Path Tracer & Hop-by-Hop Flow Simulation (`modules/routing_analyzer/path_tracer.py`)** — Interactive Longest Prefix Match (LPM) path simulation over multi-vendor routing tables. Resolves ingress device, hop-by-hop forwarding interfaces, gateway transit, and destination arrival. Integrated with Vis.js canvas animation and REST endpoint `POST /api/l3/trace-path`.
- **Unified Multi-Layer Canvas (`utils/topo_map_shell.py`)** — Added dedicated `STP` (Spanning-Tree Protocol) layer switch button. Highlights root bridges, green forwarding ports, and red dashed blocking ports alongside Physical, L2, L3, and Overlay views.
- **Quad Consolidated Inventory Export (`utils/asset_warranty_consolidator.py`)** — Consolidator now emits synchronized **HTML, CSV, JSON, and XLSX** master reports. Uses `openpyxl` with styled headers, auto-fitted columns, frozen panes, and colorized warranty statuses. In-browser UI displays direct download badges for all 4 formats.
- **Architectural Navigation Breadcrumbs** — Structured `AI_NAVIGATION_BREADCRUMBS` headers added to core and utility modules to document purpose, connections, invariants, and future developer guidelines.
- **PyInstaller Offline Spec (`NetworkSwissToolPro_v7.4.19.spec`)** — Added `openpyxl` metadata and datas to ensure offline Excel generation in packaged executable.

### 7.4.18 — Credential fallback operational certification

- Full mock-device matrix: every SSH plugin + legacy Tools `connect_device` + `/api/execute` plugins assert Primary→Secondary attempt order (`tests/test_credential_fallback_full_matrix.py`).
- Playwright all-Tools-buttons payload matrix (`tests/browser/credential_fallback_all_buttons.spec.mjs`).
- Master prompt v3: `docs/12-master-prompts/CREDENTIAL_FALLBACK_OPERATIONAL_CERTIFICATION_v3.md`.

### 7.4.17 — Credential sidebar fallback enabled + non-Cisco report honesty + zero-trust QA

- **Fix: Secondary/Third sidebar dropdowns were hard-`disabled` in HTML** — operators could not select fallback vault profiles in the UI (root cause of prior "fallback not working" reports). Dropdowns restored as optional Primary→Secondary→Third selectors.
- **Non-Cisco Asset & Warranty labeling** — Juniper/Arista/other platforms report `not a cisco device` (HTML/CSV/logs) instead of vague `unknown` / demo EOL.
- **Zero-trust test pack** — `tests/test_zero_trust_credentials_warranty.py`, Playwright `tests/browser/zero_trust_credentials_warranty.spec.mjs`, master prompt `docs/12-master-prompts/ZERO_TRUST_CREDENTIALS_WARRANTY_MASTER.md`.

### 7.4.16 — Multi-credential fallback everywhere + Asset Warranty consolidator fix

- **Multi-credential (Primary → Secondary → Third) wired program-wide** — New `connect_device()` / `safe_connection_from_credentials()` / `attach_fallback_to_devices()` in `modules/network_base.py`. All plugins that SSH, legacy Tools modules (topology, VLAN, backup, connectivity, …), Discovery / Interface Manager / STP / Standards APIs, and UI `runAction` / VLAN / IM payloads now propagate vault Secondary/Third profiles. Session `/api/session/credentials` persists secondary/third IDs.
- **Cisco Asset Warranty consolidator** — Fixed empty mutual report on HTML upload: cell regex uses `DOTALL`, header-aware column mapping for real NST Title-Case CSV/HTML, modal/script noise stripped, 2-cell rows accepted. Consolidate now emits **HTML + CSV**. Multi-file merge + dedupe by serial.
- **Tests** — `test_multi_credential_wiring.py`, `test_asset_warranty_consolidator_real_formats.py`; existing mock-SSH / fallback / ZT credential suites green.

### 7.4.0 — Multi-Credential Connection Fallback (Primary, Secondary, Third)
- **Feature: Multi-Credential Device Connection Fallback** — Added support across all network operations (`modules/network_base.py`) for Primary (mandatory), Secondary (optional retry), and Third (optional retry) credentials.
- **Connection Retry Engine (`safe_connection`)** — When connecting to any network device, `safe_connection` attempts connection with Primary credentials first. If authentication or connection fails, it logs the failure and automatically retries using Secondary credentials, followed by Third credentials.
- **Vault & Session Resolution (`utils/vault_credentials.py` & `utils/session_cred_cache.py`)** — Updated `resolve_execute_credentials` and in-memory session cache to resolve and maintain Primary (`credential_id`), Secondary (`secondary_credential_id`), and Third (`third_credential_id`) profiles.
- **Left Sidebar UI & Settings Integration (`modules/web/templates/index.html`)** — Added dedicated "Device Credentials (Fallback)" panel in the left sidebar below Target Scope with Primary, Secondary, and Third dropdown selectors. Updated Credentials Management table with "Use Primary", "Use 2nd", and "Use 3rd" quick actions.

### 7.3.2 — Fix: all topology maps rendered empty in offline HTML output

**Root cause:** Three map shells (`l3_map_shell.py`, `combined_l2l3_shell.py`, `l3_map_shell_enhanced.py`) used `<body style="display:flex; flex-direction:column; height:100vh">` but the `<main>` wrapper element inside had no CSS rule. The vis.js canvas container (`#l3-network`, `#combined-network`) used `height:100%` which resolved to 0px because `main` had no declared height in the flex chain. vis.js drew to a zero-pixel container and produced an empty map. The app reported "completed" correctly — the data was always present; only rendering was broken.

- **Fix: `utils/l3_map_shell.py`** — Added `main.l3-map-main { display:flex; flex-direction:column; flex:1 1 0%; overflow:hidden; min-height:0; }`. Changed `.l3-layout` and `#l3-network` to use `flex:1 1 0%` (no `height:100%`).
- **Fix: `utils/combined_l2l3_shell.py`** — Added `main.combined-map-main { display:flex; flex-direction:column; flex:1 1 0%; overflow:hidden; min-height:0; }`. Same pattern for `.combined-layout` and `#combined-network`.
- **Fix: `utils/l3_map_shell_enhanced.py`** — Added `main { display:flex; flex-direction:column; flex:1 1 0%; overflow:hidden; min-height:0; }` inside the `<style>` block. Also added `html, body { height:100%; }`.
- **Safety net (all three):** Added JS guard at vis.Network init: if `container.offsetHeight < 10` at render time, set `minHeight:600px` and log a warning. Ensures maps are never invisible even if the CSS chain is later broken again.
- **Not affected:** L2 Discovery (`utils/discovery_map_shell.py`), Standard map (`utils/standard_map_shell.py`), vPC map (`utils/vpc_map_shell.py`) — these use `max-height:calc(100vh - Npx)` which does not depend on the parent flex chain, and `standard_map_shell.py` has an additional JS `nstEnsureMapSize()` fallback.
- **Offline integrity confirmed:** vis.js (`modules/web/vis-network.min.js`, v9.1.6, 701 KB) remains fully bundled. No CDN references introduced. `test_map_acceptance.py` 11/11 pass. 594 topology/map tests pass.

### 7.3.1 — Bug-fix: cisco_asset_warranty dispatch, Discovery status 500, DOM warnings, console 404 noise
- **Fix: `Python EX invalid API Action cisco_asset_warranty`** — `_resolve_frozen_plugins_dir` in `modules/plugin_registry.py` now always syncs missing bundled plugins (from `_MEIPASS/modules/plugins`) into the writable sidecar regardless of sidecar count. `cisco_asset_warranty_plugin.py` copied to `dist/plugins/`. `build.py` updated to always copy all plugins and `tests/qa/PHASE5_DISCOVERY_READINESS.json` to `dist/`.
- **Fix: Single-device warranty scan (0 targets)** — `runAction()` now guards against dispatching when `target_mode === 'single'` and `single_combo` is empty; alerts operator to load inventory and pick a host. `updateGroups()` now falls back to `nstCommittedText` when textarea is empty so single_combo populates from committed inventory.
- **Fix: 500 on `/api/discovery/program-status`** — `load_readiness_register()` in `utils/discovery_program_status.py` now tries multiple candidate paths (`_MEIPASS`, exe dir, `DEFAULT_REGISTER`) and falls back to embedded authoritative BLOCKED register dictionary instead of raising `FileNotFoundError`. `NetworkSwissToolPro_v7.3.1.spec` bundles `tests/qa/PHASE5_DISCOVERY_READINESS.json` in `datas`.
- **Fix: `[DOM] Password field is not contained in a form`** — All 6 password inputs (`#password`, `#enable_password`, `#become_password`, `#export-password`, `#import-password`, `#master-password-input`) wrapped in semantic `<form>` elements with correct `autocomplete` attributes and `onsubmit="return false;"`.
- **Fix: 404 console noise on startup** — `/api/mac-trace/last`, `/api/description-search/last`, `/api/ping-scan/last` now return HTTP 200 with `{status: "idle", empty: true}` when no run has occurred yet instead of HTTP 404. Frontend loaders check `d.empty` and silently exit.
- Does not clear `release_gate`. Does not certify live CDP/LLDP vendor validation.

### 7.3.0 — Cisco asset & warranty + dual SNMP credentials + offline lab
- **Cisco asset & warranty** Swiss Tools plugin: SSH-first collection, SNMP fallback, ACI REST, consolidated HTML/CSV reports (Print → PDF).
- **Dual vault profiles**: `profile_type` (`ssh_only`, `snmp_only`, `ssh_and_snmp`); optional `snmp_credential_id` overlays SNMP from a second profile on execute.
- **Settings UI**: separate **Use SNMP** action; session cache restores SSH + SNMP profile ids without exposing secrets.
- **Offline lab**: in-process mock (`NST_MOCK_ASSET_LAB=1`) plus optional TCP simulators under `lab/ssh_sim/` (ports 2201–2204) and `lab/snmp_sim/` (UDP 1161).
- **Dependencies**: `pysnmp-lextudio`, `pyasn1`, `pysnmpcrypto` for SNMP collection.
- Does not clear `release_gate`. Does not certify live CDP/LLDP vendor validation. SNMP lab sim is QA-only.

### P1 operator accessibility (maps + console) — not a WCAG certification
- Operator console: muted/body text `#475569`, primary buttons `#1d4ed8`, success `#047857`; tab sections use `h2`/`h3` (no `h5`/`h6` skip after workspace `h1`).
- Hidden legacy tab strip is `hidden inert` only (not `tabindex` / `aria-hidden` stacked). Confirm modals closed state is `hidden inert` without first-paint `tabindex`.
- Discovery Command Center light shell: freshness and layer-switch tokens meet AA on white; maps keep `lang`, `<main>`, and keyboard-focusable connection tables.
- Does not add SSO/RBAC. Does not certify WCAG. Does not clear `release_gate`.

### 7.2.3 — Operator chrome polish (enterprise validation residuals)
- VLAN / IM validation panels and Settings credential cards: calm white panels (no rainbow gradients / emoji status headers).
- Find Missing VLAN + Port interface map CTAs use design-system `btn-mac` / `btn-mac-primary` (no purple accents).
- Chrome meta stacks under brand at ≤1100px; meta separators hidden on narrow widths.
- Discovery seeds documented as DNS-allowed crawl entry; inventory.txt remains IPv4/IPv6-only (Inventory lede + Discovery seed hint).
- Sidebar brand demoted to quiet “About” link (product identity stays in chrome).
- `/debug_status` uses `importlib.metadata.version` (no Flask `__version__` deprecation).
- Not live-vendor. Does not clear `release_gate`.

### 7.2.2 — Operator trust contracts
- Execute/scope (`filter_inventory`) skips DNS hostnames — same IPv4/IPv6 gate as Preview/Commit.
- About release notes parse `### 7.2.x` CHANGELOG sections; heading follows VERSION (no stale v7.0.0).
- L3 map sidebar + failed-host list HTML-escaped; Standard L2 node detail uses `nstUtilEsc`.
- Inventory lede + parsed-host Status column; Find panels calmed to white cards.
- Not live-vendor. Does not clear `release_gate`.

### 7.2.1 — Final master QA residuals
- Inventory preview/commit reject non-IP hosts (IPv4/IPv6 only; DNS names rejected).
- Program Status overview: one-line HARD STOP + Details disclosure (honesty strings retained).
- Sidebar brand demoted (logo + version); chrome remains product identity.
- Find primary CTAs use design-system `btn-mac-primary` (no rainbow inline colors).
- QA: mandatory suite accepts Operator shortcuts label and any 7.x VERSION string.
- Not a topology change. Does not clear `release_gate`. Not live-vendor proof.

### 7.2.0 — Enterprise operator shell redesign
- First-launch health wizard demoted: primary Continue / Quick check / Don't show again; demos under disclosure.
- Operator chrome: quiet meta status (vault · credential · scope) instead of candy pills; underline workspace nav; demoted task-log rail.
- Inventory canvas (editor + parsed hosts) remains the primary work surface. Maps hub copy shortened; Program Status / shortcuts visually restrained. Honesty strings retained (replay ≠ live poll; Live SSH ≠ SNMP).
- Not a topology change. Does not clear `release_gate`. Not live-vendor proof.

### Operator console layout (folded into 7.2.0)
- Inventory workspace hosts the inventory editor and parsed-host table. Task log sanitizes trusted color spans. Task log starts collapsed.

### 7.1.0 — 8-vendor UX lab demo; Live SSH discoverable; overlay demos are SSH not SNMP
- `docs/11-ux/demos/09-offline-8vendor-lab.html` is the operator-console freeze of the offline 8-device lab (3 NX-OS, 2 IOS, 1 IOS-XE, 2 Junos): overlay on/off, replay, Live SSH gated on vault `credential_id` and Standard L2 host, Discovery viewer disables live start, EVPN/STP stay non-cables.
- Swiss Tools shows Live SSH utilization **before** a map completes (disabled + honesty hint). It enables only after Standard L2. Not SNMP. Does not clear `release_gate`.
- UX demos 00/02/06/07/08 no longer teach SNMP as the overlay collector. Gallery keys 7–9.
- Playwright: `ux_demo_09_8vendor.spec.mjs` (file://). Not live-vendor. Not EXE E2E.

### 7.0.99 — CI-browser Playwright overlay/map HTML; overlay docs match shipped M1–M5
- Operator Playwright covers Swiss Tools overlay honesty: Live SSH without `credential_id` fails closed and does not POST `utilization_live`; overlay status poll does not clear `release_gate`.
- Fixture Standard L2 + Discovery Command Center HTML is exercised over `file://` (overlay toggle, EVPN/STP not grayed as unsampled cables).
- Overlay contract docs no longer claim live SSH is unimplemented. Playwright is documented as CI-browser, never EXE E2E.
- Not live-vendor evidence. Chromium is not bundled in the offline EXE.

### 7.0.98 — STP-blocked not utilization paint; offline 8-vendor demo lab
- STP-blocked / protocol STP edges are not paint-eligible for the utilization overlay (contract: not a forwarding-path utilization). Discovery overlay JS does not gray those edges as unsampled cables.
- Offline 8-device demo lab (3 NX-OS, 2 IOS, 1 IOS-XE, 2 Junos) generates Standard L2 + Discovery maps and replay overlay from fixtures. Not live-vendor evidence.

### Utilization overlay M5 (Discovery Command Center host)
- Discovery Command Center can **view** the existing utilization overlay JSON on crawl maps. Join/paint semantics are unchanged. Only existing trusted L2 cable keys are painted.
- EVPN, overlay, and incomplete observations stay non-cables and are never utilization-colored. Unmapped interfaces remain listed, not graphed. Live SSH start stays Standard L2 only.
- Standard L2 replay + live SSH paths are unchanged. Overlay does not clear `release_gate` or mutate `trust_tier`.

### Utilization overlay M4 (live SSH, Standard L2)
- Inventory Standard L2 can run a **bounded Live SSH** two-sample collector on map nodes only (`/api/execute` action `utilization_live`). Requires vault `credential_id`. Not SNMP. Does not certify topology and does not clear `release_gate`.
- Rates are `(Δoctets × 8) / Δt`. Missing/zero ifSpeed suppresses percent. Cancel and per-device SSH errors degrade honestly; replay overlay remains available.
- Map UI labels Live SSH vs Replay by provenance. `file://` maps cannot start live collection (no secrets on the map page).

### Utilization overlay M1–M3 (replay, Standard L2)
- Inventory Standard L2 can paint a **replay/fixture** utilization overlay on existing L2 edges only. Join is `cable_key` / topology relation key — never vis `e0` ids.
- Overlay off leaves today’s L2 coloring unchanged. Overlay on changes stroke only. Gray dashed = no sample, not down. Replay is not a live poll.
- Invalid or mismatched fixtures fail closed; the base map stays usable. Topology, `trust_tier`, and `release_gate` are not modified.

### Reality-loop device-fidelity (7.0.97)
- CDP brief: wrapped Device ID continuation; Platform/Port ID split when a single space separates them; spaced abbreviations (`Gig 1/0/1`) normalize with detail (`GigabitEthernet1/0/1`).
- IOS LLDP detail: `Local Interface` kept with `Chassis id` (12.x local-first blocks); `mac ` chassis/port prefix is not a hostname.
- Junos 11.x brief without Parent Interface: Chassis Id column is not treated as a parent port.
- Graph `_normalize_edge_port` uses `utils.cisco_iface` (not the discovery plugin) so Phase 4 telemetry freeze does not load paramiko.

### Migration — CLI Socket.IO credential_id only (breaking for plaintext CLI)

**Breaking:** Interactive CLI no longer accepts username/password over Socket.IO. The temporary `NST_CLI_PLAINTEXT_COMPAT` environment variable has been **removed** and is ignored if set.

**Operator steps:**
1. Create or verify a vault credential in the main console.
2. Unlock the vault if required.
3. In `/cli_terminal`, select the stored credential (`credential_id`).
4. Connect — the password stays on the server.
5. Do not type or transmit a password through Socket.IO.

See `docs/08-security/credential-management.md`.

### Phase 1 closure (2026-08-20)
- Origin/CSRF: mutating requests require a loopback UI origin **or** empty Origin/Referer (local pytest/curl). Prefix-lookalike origins are denied. Loopback is not identity.
- Plugins: Reload Registry POSTs `/api/plugins/reload` after confirm. Load refuses `os.system`/`eval`/`exec` AST calls. HTTP upload stays disabled. Plugins still run in-process.
- Vault: `credential_id` is the stored username. Execute fails closed on unknown, deleted, invalid, locked, or mismatched ids. Lists omit passwords.
- Credentials GET: `/api/credentials/get/<username>` returns metadata only. Use selects `credential_id`; the server resolves vault secrets in memory. Compatibility: the route remains; secret JSON fields are gone. Loopback is not identity.
- CLI Socket.IO: `cli_connect` **requires** vault `credential_id`. Plaintext Socket.IO passwords and `NST_CLI_PLAINTEXT_COMPAT` are **removed**. CLI UI selects metadata-only credentials; no password fields on the connect form.
- IM/VLAN confirm dialogs trap focus, close on Escape/Cancel, restore trigger focus, and stay inert when closed (HTML contract; Playwright not installed).

### Confirm dialogs first paint (RB-ZT-04)
- IM deploy and VLAN confirm overlays are `hidden`+`inert`+`aria-hidden` until opened via `nstSetDialogOpen`.

### Operator log pane (RB-ZT-03)
- `GET /api/logs` is a bounded cursor snapshot (`since`, `limit`). It does not drain, clear, or delete logs.
- Query parameters cannot select files. POST/DELETE on `/api/logs` are not allowed.
- The UI poller follows `next_cursor` so lines are not duplicated.

### Plugin runtime upload disabled (RB-ZT-01)
- `POST /api/plugins/upload` always returns 403 and never writes files. Env vars cannot re-enable HTTP install.
- Operator install model is `offline_local_directory`: copy trusted `.py` into `modules/plugins` (or EXE sidecar) then Reload or restart.
- `promote_plugin` refuses copies into the plugins directory. `BANNED_IMPORTS` is unchanged (still not a sandbox).

### L3 routing-analyzer contract (RB-L3-01–03)
- `RoutingParser.template_dir` is public; `_tdir` is an alias to the same path. Cisco/Junos TextFSM templates parse as valid TextFSM.
- `RoutingCollector` records transport errors without secrets; IPv6 CLI stays in `routing_v6`; unit tests inject Mock transport (no live SSH).
- L3 graph device nodes require at least one usable unicast (or default) prefix; multicast-only routes no longer fabricate a device.

### Phase 1 shell a11y / Evidence copy (7.0.96)
- Inactive workspaces and the legacy tab-view hold are `hidden` + `inert` + `aria-hidden` in first-paint HTML so Maps/Find/Change headings are not exposed before JS.
- Evidence empty and artifact-unavailable copy is explicit; Open/Reveal/Zip remain unimplemented (no file reader).
- Chrome actions stay sticky at ~720px; 900px chrome stacks to one column.

### Six-workspace shell (7.0.95)
- Operator chrome: version, vault pill, credential label (no secrets), scope, freshness, Cancel, Stop EXE.
- Six workspaces: Inventory, Maps, Find, Change, Evidence, Settings. Keys 1–6. Legacy `tab-segment-*` + `goTo*Tab()` remain as a compatibility bridge.
- Evidence reads `GET /api/jobs`. Path reconstruct stays disabled until MAC last + L2 status exist.

### Phase 0 cleanup (7.0.94)
- Standards stays a synchronous POST (UI still receives `results` in the same response) and now writes a SQLite job-index row. Cancellation is **not** supported (`cancel_scope=none`); in-flight SSH is not interrupted.
- Plugin `/api/execute` start JSON sets `artifacts_expected` to null until a plugin actually writes an `outputs/` folder.
- STP status JSON no longer includes absolute `html_path` / `output_folder`. Reports stay on localhost GET `/api/stp/report/<id>` after path containment checks.
- `/api/version` date string tracks 7.0.94.

### Host-job source model (7.0.93)
- Ping Scan `target_source=cidr_scan` (omitted source is `legacy_body` CIDR of `network` only). Not inventory. Max 256 hosts. Path-like and huge prefixes rejected. Indexed; cancellable via the control plane; reports stay under `outputs/`.
- STP uses `inventory_source=committed|unsaved`, `target_source=explicit_host_list`, `demo_mode`, or legacy `devices[]` (`legacy_body`). The textarea is not a silent STP target list.
- Job index JSON adds `artifacts_available` (true only when a contained `outputs/` folder exists). Connectivity still completes without a run folder — that is honest, not a fake pack.
- `mandatory_release_qa.py` runs manifest `python` commands with `sys.executable`.

### Inventory source chip after commit (7.0.92)
- Commit/restore now assign `nstCommittedText` before filling the textarea so the sidebar chip does not stay on “no committed file” after a successful write.
- Discovery launch errors now write the failure into the status line instead of leaving “Launching discovery crawl…”.

### Discovery / IM target source (7.0.91)
- Discovery seeds are not bulk inventory. `target_source` is `discovery_seeds`, `committed_inventory` (explicit seed list from inventory.txt, not a census), or `unsaved_inventory` (explicit). Inventory body without a source is rejected.
- Interface Manager is one host: `single_host`, or the host must exist in committed/unsaved inventory when those sources are chosen. The unsaved box no longer silently supplies the first line.
- Both job types register in the SQLite catalog. Discovery cancelled/partial is never stored as complete. Export/report still available for partial/cancelled artifacts.
- Hop bound remains 1–3. Discovered neighbors are not written to inventory.txt.

### Job index / Evidence catalog (7.0.90)
- SQLite catalog at `{data_root}/index/jobs.sqlite` (same `get_data_root()` as reports). Index only — run folders remain the artifact store.
- Rows: task_id, timestamps, action, status (`running` / `complete` / `failed` / `cancelled` / `partial`), inventory_source, device_count, contained `outputs/` run_dir, sanitized error summary.
- GET `/api/jobs` and GET `/api/jobs/<task_id>` are localhost-only. Limit 1–200, newest first. No file open, no inventory body, no passwords.
- Index writes are fail-open (job result is unchanged if SQLite fails). Cancelled is never rewritten as complete; cancel-with-run-dir is `partial`.
- See `docs/02-codebase/JOB_INDEX.md`.

### Execute inventory source (7.0.89)
- Live UI sends `inventory_source=committed` by default. Jobs use `inventory.txt`, not a silently edited textarea.
- Sidebar chip states committed / unsaved / none / box-differs. Checkbox **Run unsaved box** is required to execute the draft; VLAN/save-config also need `acknowledge_unsaved=true` when the box differs.
- Omitted `inventory_source` keeps the old API contract (request body wins) so pytest and old clients do not break.
- POST `/api/inventory/source` returns compare state. Execute start JSON includes `inventory_source` / `inventory_state` / `device_count` — not the inventory body. Logs are counts and source labels only.

### Inventory preview / commit / bak (7.0.88)
- POST `/api/inventory/preview` parses v1 text into accept / warn (duplicate host+port) / reject (parse error, unknown device_type). Unknown types are not silently dropped.
- POST `/api/inventory/commit` (`replace` or `merge`) requires `confirm=true`, writes `inventory.txt` v1, keeps last 10 `inventory.txt.bak.*` files beside it. Commit logs counts, not the file body.
- POST `/api/inventory/restore` restores a bak by basename only (no path traversal).
- GET `/api/inventory` still returns `{inventory}` for Import; also returns `counts` and `baks`.
- Sidebar: Preview, Commit replace/merge, Restore bak. SSH jobs still use the textarea; commit refreshes it so the box matches the file.

### Cable witnesses / path / golden-config (7.0.87)
- Inventory L2 edges stamp description-vs-neighbor, speed/duplex mismatch, and DOM/optics alarms when CLI collected. Overlay/L3/`not_physical` edges are skipped. Never labeled a verified cable.
- `link_issues.json` + GET `/api/topology/issues` (localhost) list mismatch / DOM / LACP / one-sided rows for the last Standard L2 map.
- POST `/api/path-trace` reconstructs a MAC path from last MAC-table hits and existing CDP/LLDP edges only. Missing edges stop the walk; hops are not invented. Not DNA Path Trace and not a forwarding path.
- VLAN validate/apply and Interface Manager validate/deploy add a golden-config step (`policies/golden_gate.yaml`). Reserved VLANs 1002–1005, bad names, `default interface`, and access-VLAN-without-description fail closed before SSH apply.

### Overlay / LACP / cancel (7.0.86)
- Discovery and inventory topology collect overlay from `show nve peers` / `show nve vni` (NX-OS/IOS-XE) and Junos EVPN/VTEP CLI. Overlay edges are VTEP peers (`not_physical`), never hostname leaf/spine guesses.
- Schema allows `overlay_collected=true` only with a list of not-physical overlay links.
- Cancel force-closes registered Netmiko sockets (`disconnect` + `remote_conn.close`) so in-flight `send_command` unblocks.
- LAG/LACP stamps oper-state from `show lacp neighbor` / port-channel summary. A down member does not delete the bundle edge (T-L2-11). ifName-only stays labeled heuristic.

### Discovery operator console
- Console CSS is local (no Bootstrap or Google Fonts CDN). Maps still fail closed if vis.js is missing.
- Physical vs L2: same CDP/LLDP collection; Physical view hides one-sided/mismatch (not verified cables). Hash `#nst-layer=` opens that view.
- Discovery crawl map is Command Center; inventory L2 is explicitly “not this crawl.”
- Discovery JSON schema (`utils/discovery_schema.py`) rejects cancelled-as-complete and dishonest overlay_collected=true.
- Duplicate chassis IDs flag `chassis_conflict` (no silent merge).
- IOS-XE classified separately; unknown platforms stay `unknown`.
- Cancel is checked between CLI commands **and** disconnects in-flight SSH.
- Inventory L2/vPC collection (`topology_mapper`) also checks cancel between CLI commands and disconnects live sockets.
- VLAN validate does not open SSH when Juniper rename is already forbidden (or VLAN ID is invalid).
- L3 map edges carry a VRF label; same next-hop in two VRFs is not collapsed. This is **not** a hard VRF graph cut.
- Swiss Tools splits Standard/vPC (L2) from Advanced L2/L3/Flow (SSH routing — not overlay).
- Plugin upload copy states in-process execution; disable with `NST_DISABLE_PLUGIN_UPLOAD`.
- Operator log pane no longer receives Python stack traces (structured logger only).
- Interface VLAN reporter HTML escapes hostnames and CLI fields.
- vis.js SHA-256 pin (`modules/web/vis-network.min.js.sha256`) is checked by offline verification (SBOM-lite, not a full SBOM).
- Port-interface map HTML escapes hostnames.
- Current operator docs (README, release README) no longer advertise Tk as a supported UI.
- Overlay layer shows NVE/EVPN peers when CLI ran; empty-after-collection is not an empty fabric.
- Map STALE badge re-checks against the browser clock every 60s.
- Results table adds an Evidence column (`neighbor_evidence`, `identity_conflict`) and escapes hostname/IP/OS cells.
- Scan-state filter includes Auth denied and Timeout (not only Failed SSH).
- Link CSV includes `confidence`, `one_sided`, and `bundle_kind`.
- JSON export fallback and inventory dump include `links`, `collection_status`, `partial`, and `cancelled` (not devices-only).
- `identity_conflict` is passed through on discovery `devices[]`.
- “Standard L2 Map (inventory)” confirms it starts sidebar inventory topology, not the crawl job graph.
- Swiss Tools Physical and L2 status text states they start the same inventory CDP/LLDP job; layer switch is in the generated HTML.
- Empty-state and Wide profile copy no longer imply L3 census.

### Security
- Loopback-only guards on `/debug_status`, `/api/shutdown`, `/api/plugins/upload`, `/api/plugins/reload`, `/api/plugins/debug`, and `/api/execute`.
- Empty `remote_addr` is no longer treated as localhost (`utils/api_security.py`).
- Root `.gitignore` excludes credential vault files (`.credential_key`, `.credentials.enc`, salt/hash/meta).
- GET `/api/session/credentials` no longer returns password fields; execute falls back to the in-process cache.
- Socket.IO CORS limited to `http://127.0.0.1:5051` and `http://localhost:5051`.
- Flask `secret_key` is a process-local random (not persisted).
- Loopback-only decorator on remaining mutation APIs: VLAN validate, Interface Manager, discovery, ping scan, STP, standards, health-check, templates, extract_docs, control-plane cancel.
- Bind host defaults to `127.0.0.1`; any non-loopback bind requires `NST_ALLOW_NONLOCAL_BIND=1`.
- Operator console is loopback-gated (`before_request`); `/health` remains a probe.
- Cross-origin POSTs (evil `Origin`) are rejected even from loopback.
- Plugin upload can be disabled with `NST_DISABLE_PLUGIN_UPLOAD=1`; AST denylist expanded (still not a sandbox).
- Map HTML JSON is script-safe; device names in link tables are escaped; log pane uses textContent.

### Topology
- Discovery edge trust scores now match confidence labels (bidirectional = High/80; one-sided = Medium; incomplete = Low) and retain protocol `sources`.
- CDP and LLDP evidence for the same cable merge into one edge with provenance (`sources[]`); distinct ports stay parallel.
- L3 graph edges are typed (`bgp-neighbor`, `ospf-neighbor`, …) with `layer=l3` and `not_physical`; tooltips say they are not cables.
- Link inventory shows an Evidence column; trust pills render High/Low instead of mislabeling High as Inferred.
- NX-OS LLDP/CDP disabled / `% Invalid command` yields zero neighbors (no invented links).
- STP blocked-port parser keeps Blocking/BLK distinct from Forwarding/FWD.
- L3 maps still do not draw EVPN (routing collection only). Discovery/inventory Overlay layer uses NVE/EVPN CLI.
- Physical / L2 / L3 / Overlay layer switch on maps and Swiss Tools.
- Freshness badge: STALE when collected_at is older than 24 hours.
- One-sided CDP/LLDP edges are labeled spoof-risk (Medium); not treated as verified cables.
- Map blast radius (1-hop) and “why this link” evidence live region on L2/L3/discovery maps.
- Contradictory remote ports on the same local interface are Mismatch (not silently merged).
- Duplicate hostnames with different IP/serial stay two nodes (`identity_conflict`); vis ids do not collide.
- Discovery Stop cancels the crawl and returns a partial graph (not complete truth).
- Junos LLDP brief table (older Junos) and IOS-XE `show lldp neighbors` brief parse system name / Port ID instead of parent `-` or hold-time.
- Overlay empty panel splits “CLI not collected” vs “CLI ran, zero peers” (no hostname guessing).
- Blast radius: 1-hop default and optional 2-hop neighborhood (explicitly not a forwarding path).
- LAG/AE: Po/ae ifName classified as bundle vs member; LACP CLI stamps oper-state when collected. Degraded member does not remove the bundle edge.
- Discovery scan profiles: conservative / standard / wide. Job `collection_status` + operator_truth on status API. Auth denied vs timeout scan states.
- Empty CDP/LLDP neighbor lists are labeled lack of evidence (`neighbor_evidence`), not isolation.
- Map HTML never fetches vis.js from a CDN if the bundle is missing (offline fail-closed).

### Offline / governance
- Acceptance criteria, baseline assertions, AI navigation, and Playwright-alternative (Flask HTML contracts, Chromium not in EXE).
- Controlled-pilot package, readiness traceability, live-lab prep pack, EXE signing documented as a Ready blocker.
- Named-lab and air-gap **execution kits** (procedures; not executed). Discovery complete copy is hop-bounded, not a census.

### AI IDE
- Restored native `.cursor` operating system (rules, skills, commands, governance docs) so agents no longer depend on missing `.devin` / `skillss` junctions.

## [v7.0.76] - 2026-07-02

### Enhanced — Swiss Tools Button UX

- **Modern button design:** Enhanced button styling with gradient backgrounds and subtle shadows
- **Hover effects:** Added smooth lift animation (translateY -1px) on hover for tactile feedback
- **Ripple effect:** Added ripple animation on button click for visual feedback
- **Focus states:** Added focus outline for keyboard accessibility
- **Loading state:** Added loading spinner animation for async operations
- **Improved spacing:** Increased padding and font weight for better touch targets
- **Color gradients:** Primary buttons use blue gradient, secondary use subtle gray gradient
- **Shadow depth:** Added dynamic shadows that intensify on hover
- **Smooth transitions:** Cubic-bezier easing for professional feel
- **Legacy compatibility:** Updated btn-mac classes with same UX enhancements

### Tests

- All 80 tests passing

### Build

- `NetworkSwissToolPro_v7.0.76_OFFLINE.exe` — enhanced button UX across Swiss Tools interface

## [v7.0.75] - 2026-07-02

### Enhanced — Device Icons and Hierarchical Layout

- **Device icons:** Added SVG icons for device types (switch-blue, router-orange, firewall-red, server-purple, default-gray)
- **Icon detection:** Auto-detects device type from platform string (switch, router, firewall, server)
- **Hierarchical layout:** Changed to hierarchical layout (Up-Down) for better network structure visualization
- **Engineer-friendly:** Hierarchical view shows network topology in tree structure ideal for engineering teams
- **Icon integration:** Icons embedded as data URIs for offline compatibility
- **Layout tuning:** Adjusted level separation, node spacing, and tree spacing for clear visualization

### Tests

- All 80 tests passing

### Build

- `NetworkSwissToolPro_v7.0.75_OFFLINE.exe` — enhanced with device icons and hierarchical layout

## [v7.0.74] - 2026-07-02

### Enhanced — L3 Map UX and Detail Information

- **Map stability:** Disabled physics after stabilization to prevent continuous movement
- **Short labels:** Truncated long hostnames/IPs to first 15 chars for cleaner display (full info in tooltip)
- **Interface details:** Added interface information display in device detail panel (up to 10 interfaces)
- **Default routes:** Added dedicated default route section showing 0.0.0.0/0 routes with next-hop and protocol
- **Routing table:** Enhanced routing table display grouped by protocol with route counts
- **Route details:** Added metric and interface information to route entries
- **Better organization:** Routes grouped by protocol (Connected, Static, OSPF, BGP, etc.) with badges

### Tests

- All 80 tests passing

### Build

- `NetworkSwissToolPro_v7.0.74_OFFLINE.exe` — enhanced L3 map with better UX and detailed information

## [v7.0.73] - 2026-07-02

### Debug — L3 Map Blank Despite Successful Initialization

- **Node logging:** Added console logging for each node's color, shape, and size
- **Camera logging:** Added logging for camera position and scale after network.fit()
- **Node positions:** Added logging of node positions after stabilization
- **Canvas CSS:** Added explicit CSS for canvas element (display: block, position: absolute)
- **Container CSS:** Added min-height and min-width to container
- **Force redraw:** Added network.redraw() call after fit

### Tests

- All 80 tests passing

### Build

- `NetworkSwissToolPro_v7.0.73_OFFLINE.exe` — debugging build to diagnose blank map issue

## [v7.0.72] - 2026-07-01

### Fixed — L3 Map Visibility in Enhanced Shell

- **Node visibility:** Doubled node size in enhanced shell for better visibility
- **Edge visibility:** Increased edge width from 1px to 2px and opacity from 0.6 to 0.8
- **Physics tuning:** Improved Barnes-Hut parameters (stronger gravity, more iterations, better damping)
- **Auto-fit:** Added network.fit() after stabilization to ensure nodes are visible on load
- **Console logging:** Added extensive console logging for debugging (RAW_NODES, RAW_EDGES, container dimensions, network errors)
- **DOMContentLoaded:** Changed from window.onload to DOMContentLoaded for more reliable initialization
- **Error handling:** Added container existence check and network error handler

### Tests

- All 80 tests passing

### Build

- `NetworkSwissToolPro_v7.0.72_OFFLINE.exe` — bundles enhanced shell with visibility fixes

## [v7.0.71] - 2026-07-01

### Fixed — Vis.js Loading Error (404)

- **Inline embedding:** Fixed vis.js loading by embedding vis-network.min.js inline in HTML instead of loading from external files
- **load_vis_script() function:** Added proper function to load vis.js from bundled location in PyInstaller
- **Removed dynamic loading:** Removed JavaScript-based dynamic loading that was causing 404 errors in offline environment
- **Root cause:** Web adapter was trying to load vis.js from file paths that don't exist in the browser context

### Tests

- All 80 tests passing

### Build

- `NetworkSwissToolPro_v7.0.71_OFFLINE.exe` — bundles vis.js inline for offline compatibility

## [v7.0.70] - 2026-07-01

### Fixed — L3 Map Visibility and Script Execution

- **Node visibility:** Changed device node color from dark gray to bright blue (#00bceb) for better visibility against dark background
- **Node size:** Increased node size from default to 35px for better visibility
- **Edge width:** Increased edge width from 1.5px to 2px for better visibility
- **Script execution:** Added DOMContentLoaded wrapper to ensure vis.js initializes after DOM is ready
- **Console logging:** Added extensive console logging for debugging (RAW_NODES, RAW_EDGES, container dimensions, network errors)
- **Physics tuning:** Improved Barnes-Hut physics parameters (stronger gravity, longer spring length, more iterations)
- **Error handling:** Added container existence check and error handler for network errors

### Tests

- All 80 tests passing
- Test HTML generated with console logging for debugging

### Build

- `NetworkSwissToolPro_v7.0.70_OFFLINE.exe` — bundles visibility and execution fixes

## [v7.0.69] - 2026-07-01

### Fixed — L3 Map Empty Display Issue (Final Fix)

- **Vis.js layout configuration:** Disabled hierarchical layout, enabled physics-based Barnes-Hut layout
- **Container sizing:** Added explicit height, width, and position to network container for proper rendering
- **Auto-fit:** Added network.fit() after stabilization to ensure nodes are visible on load
- **Syntax fix:** Removed extra closing brace that was breaking JavaScript initialization
- **Root cause:** Hierarchical layout with disabled physics + improper container sizing caused nodes to not display

### Tests

- Verified data embedding in HTML (RAW_NODES, RAW_EDGES contain actual data)
- Confirmed vis.js initialization with proper node/edge datasets
- All 80 tests passing (38 comprehensive + 20 network engineer + 16 edge cases + 6 end-to-end rendering)

### Build

- `NetworkSwissToolPro_v7.0.69_OFFLINE.exe` — bundles fixed L3 map with proper vis.js layout and container sizing

## [v7.0.68] - 2026-07-01

### Fixed — L3 Map Empty Display Issue

- **Vis.js layout configuration:** Fixed empty map display by disabling hierarchical layout and enabling physics-based layout
- **Physics engine:** Enabled Barnes-Hut physics algorithm with optimized parameters for proper node positioning
- **Stabilization:** Added stabilization settings to ensure nodes render correctly on load
- **Root cause:** Hierarchical layout with disabled physics was causing nodes to not display in the browser despite data being correctly embedded

### Tests

- Verified data embedding in HTML (RAW_NODES, RAW_EDGES contain actual data)
- Confirmed vis.js initialization with proper node/edge datasets
- All 80 tests passing (38 comprehensive + 20 network engineer + 16 edge cases + 6 end-to-end rendering)

### Build

- `NetworkSwissToolPro_v7.0.68_OFFLINE.exe` — bundles fixed L3 map with proper vis.js layout

## [v7.0.67] - 2026-07-01

### Fixed — L3 Map Data Rendering Verification

- **End-to-end data flow verification:** Added comprehensive tests to verify that collected routing data is actually rendered in the HTML output
- **Single device rendering:** Confirmed that single device scans display correctly in the map with nodes, edges, and metadata
- **Group device rendering:** Confirmed that bulk/group scans (multiple devices) display correctly with all devices shown
- **Data structure validation:** Verified that the vis.js payload structure is correctly embedded in the HTML (RAW_NODES, RAW_EDGES, DEVICES_META, etc.)
- **Failed device handling:** Confirmed that failed devices don't prevent successful devices from being rendered
- **Empty route handling:** Verified that even with no routes, HTML is still generated (empty map)

### Tests

- `tests/test_l3_end_to_end_rendering.py` — 6 new end-to-end rendering tests covering:
  - Single device data rendering in HTML
  - Multiple devices (group) data rendering in HTML
  - Empty routes still render HTML
  - Failed devices don't prevent successful ones from showing
  - vis.js payload structure in HTML
  - Duplicate gateway shows once in HTML
- All 80 tests passing (38 comprehensive + 20 network engineer + 16 edge cases + 6 end-to-end rendering)

### Build

- `NetworkSwissToolPro_v7.0.67_OFFLINE.exe` — bundles verified L3 map with end-to-end data rendering validation

## [v7.0.66] - 2026-07-01

### Fixed — L3 Map Edge Cases and Bulk Scanning

- **Duplicate gateway resolution:** Verified and confirmed that 1 gateway + 4 switches correctly shows as 1 gateway node with 4 connections (not 5 duplicate gateway nodes)
- **Bulk scanning:** Verified support for scanning up to 150 devices in parallel with automatic truncation and warning for larger sets
- **Network crawling:** Tested hub-and-spoke, mesh, and multi-layer topologies to ensure proper visualization
- **Edge case handling:** Added comprehensive tests for self-referential routes, loopback filtering, multicast filtering, /32 host route filtering, and empty next-hop handling
- **Gateway device upgrade:** Confirmed that gateways which are also devices are correctly upgraded to gateway type instead of creating duplicate nodes

### Tests

- `tests/test_l3_edge_cases.py` — 16 new edge case tests covering:
  - Duplicate gateway resolution (single gateway with multiple switches)
  - Gateway that is also a device
  - Multiple gateways with same IP in different contexts
  - Large device count handling (200 devices)
  - Device groups and mixed device types
  - Hub-and-spoke, mesh, and multi-layer topologies
  - Self-referential routes, loopback addresses, multicast routes
  - Host route filtering and empty next-hop handling
  - Mixed protocols and VRF-specific routes
- All 74 tests passing (38 comprehensive + 20 network engineer + 16 edge cases)

### Build

- `NetworkSwissToolPro_v7.0.66_OFFLINE.exe` — bundles verified L3 map with edge case handling

## [v7.0.65] - 2026-07-01

### Enhanced — L3 Map UI/UX (Secure Cartography-inspired)

- **Vendor-specific styling:** Cisco (blue #00bceb), Juniper (orange #f97316), Arista (green #22c55e) color coding for devices
- **Network flow animation:** Toggle button to animate edge widths for visualizing traffic flow
- **Focus mode:** 1-hop neighborhood view for troubleshooting - click a node then "Focus Mode" to see only connected devices
- **PNG export:** Export map to PNG for documentation and sharing
- **Enhanced legend:** Vendor-specific legend with Cisco, Juniper, Arista, Gateway, Default GW, and Subnet indicators
- **Improved vendor badges:** Added Arista detection and updated Cisco badge to "Cisco" instead of "IOS"
- **Enhanced metadata display:** VRF names and route count by protocol now shown in device detail panels

### Tests

- `tests/test_l3_network_engineer_validation.py` — 20 network engineer-focused validation tests covering:
  - Default gateway identification
  - Routing protocol distribution
  - VRF-aware routing
  - Connected subnet identification
  - Interface-to-subnet mapping
  - Routing troubleshooting (loops, asymmetric routing, multi-path)
  - Network change validation (new gateway detection, subnet changes)
  - Vendor-specific features (Cisco IOS route codes, Juniper protocol names)
  - Operational readiness (failed host reporting, route counts, HTML export)
  - Performance at scale (150+ devices, 1000+ routes)
  - Security and compliance (credential exposure prevention)
- All 38 comprehensive L3 pipeline tests passing
- All 20 network engineer validation tests passing

### Build

- `NetworkSwissToolPro_v7.0.65_OFFLINE.exe` — bundles enhanced L3 map shell with Secure Cartography-inspired UI

## [v7.0.64] - 2026-06-30

### Added — L3 / Flow network cartography (Netdisco + Secure Cartography inspired)

- **L3 Routing Map:** SSH `show ip route` / `show route` collection from sidebar inventory; multi-vendor parsing (Cisco IOS/XE/NX-OS, Juniper Junos) with TextFSM + regex fallback; offline Vis.js HTML map with gateways, subnets, and device routing graph.
- **Network Flow Map:** Gateway-centric logical flow view derived from routing tables (default gateways, inter-subnet paths).
- **Advanced L2 Map:** CDP/LLDP enriched adjacency map (Secure Cartography style) — separate from Standard L2 Map.
- **Web UI:** Swiss Tools buttons now run real jobs via `/api/execute` (`l3_topology`, `flow_map`, `advanced_l2_map`) with status polling (`/api/l3-map/status`) and HTML open (`/api/l3-map/open`) — no raw JSON endpoints.
- **Modules:** `modules/l3_topology_runner.py`, `utils/l3_map_shell.py`, `utils/l3_map_formatter.py`; wired `modules/routing_analyzer/*` into production adapters pipeline.

### Tests

- `tests/test_l3_map_html_contract.py` — parser regex, L3/Flow pipeline, UI/API contracts.
- `tests/routing_analyzer/test_multi_vendor.py` + `test_graph_builder.py` added to mandatory pre-release manifest.
- QA scaffold: L3 status API + UI contract tests in `tests/qa/test_12_topology_maps.py`.

### Build

- `NetworkSwissToolPro_v7.0.64_OFFLINE.exe` — bundles `networkx`, `modules.routing_analyzer`, TextFSM templates, offline L3 map shell.

### References

- [secure_cartography](https://github.com/scottpeterman/secure_cartography) — L2 enrichment methodology (NIST comparison omitted by design).
- [netdisco](https://github.com/netdisco/netdisco) — L3 routing inventory / gateway flow model (SNMP walk not used; SSH-only for offline EXE).

## [v7.0.62] - 2026-06-22

### Fixed — P1 gap remediation

- **G-UX-001/002/003 (UI tab navigation):** Replaced all dead `querySelector('[data-tab=…]')` calls with proper `goToSearchTab()`, `goToToolsTab()`, `goToDiscoveryTab()` helper functions. Swiss Tools "Start here" buttons and Discovery cross-link now reliably activate the target tab.
- **G-UX-004 (desc_search empty guard):** `runAction('description_search')` now checks `desc_search_input` client-side before dispatch — alerts and focuses the empty field exactly like the existing MAC trace guard.

### Fixed — P2 gap remediation

- **G-011b (IM legacy syntax hard block):** `switchport trunk encapsulation` on `cisco_nxos` and any other platform-specific legacy command is now promoted from warning-only to a blocking error (`"passed": false`, `"blocking": true`). Operators can no longer accidentally deploy unsupported syntax.
- **G-SCAFFOLD (30 scaffold tests implemented):** Converted 30+ persona scaffold tests across `test_01`, `test_03`, `test_04`, `test_06`, `test_09`, `test_11`, `test_12`, `test_15` from `@SCAFFOLD_SKIP` placeholders to real assertions covering source-code contracts, API presence, UI structure, and pure-function behaviour.
- **G-CONTRACT (runAction→execute contract):** `tests/test_ui_execute_contract.py` — asserts every `runAction(…)` call in `index.html` maps to a registered `/api/execute` action or alias; also verifies no dead `[data-tab=…]` selectors and `goTo*Tab()` helpers.
- **G-008b (IM HTML report E2E test):** `TestImHtmlReportRoute` in `test_ui_execute_contract.py` covers missing-path 400, path-traversal block, and the route source presence check.

### Tests

- `tests/test_ui_execute_contract.py` — UI/execute action contract + dead selector guard + IM report route (new).
- `tests/plugins/test_interface_manager.py::test_nxos_legacy_syntax` — updated to expect blocking failure not pass.
- `tests/qa/` — 30 scaffold bodies implemented across 7 modules.
- Manifest v3 updated; `minimum_app_version` 7.0.62; `tests/test_ui_execute_contract.py` added to core pre-release suite.

### Build

- `NetworkSwissToolPro_v7.0.62_OFFLINE.exe` — **corrected offline rebuild** (use this one, not the first 26.8 MB build from 17:50).
- **Root cause of undersized first EXE:** built with system Python 3.14 instead of project `.venv` Python 3.12; ~8,500 fewer bundled files, half the netmiko drivers.
- **Fix:** spec now uses `collect_all()` for `netmiko`, `ntc_templates`, `textfsm`, `invoke` + explicit vendor driver hiddenimports; rebuild command: `.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm NetworkSwissToolPro_v7.0.62.spec`
- **Verified:** 36,900 bundle entries (vs 26,563 in v7.0.60), 1,723 netmiko + 3,787 ntc_templates paths, python312.dll, 14/14 plugins, prebuild PASS.

## [v7.0.61] - 2026-06-22

### Fixed

- **Swiss Tools MAC trace:** "Start here" button dispatched `mac_trace` but `/api/execute` only accepts `mac_check` → `Invalid API Action mac_trace`. UI now uses `mac_check`; API accepts `mac_trace` as alias; `runAction()` normalizes client-side; empty MAC blocked before dispatch.

### Tests (mandatory before release)

- `tests/test_api_execute_mac_alias.py` — API alias, UI contract, action registry guardrail.
- `tests/qa/test_00_implemented_mandatory.py` — Swiss Tools + alias static checks.

### Docs

- `docs/09-qa/EXECUTE_ACTION_CONTRACT.md` — `/api/execute` action names vs Search-it progress keys.

**No new EXE** in this patch — use v7.0.60 offline build or run from source until next EXE ship.

## [v7.0.60] - 2026-06-22

### Council remediation (P0 / P1 / P2)

- **Mandatory QA implemented:** `tests/qa/test_00_implemented_mandatory.py` — 22+ real council tests (questionnaire linkage).
- **Live SSH warranty:** `docs/09-qa/LIVE_SSH_WARRANTY.md` — offline gate + optional `NST_LIVE_SSH=1` probe.
- **Topology truncate (G-004):** `devices_skipped_hosts` in manifest; Swiss Tools panel lists hosts beyond 150-device cap.
- **Junos VLAN rename (G-007):** Explicit UI notice; validation blocks rename before SSH.
- **IM safety (G-011):** Blocks `shutdown`, `default interface`, `no switchport` in validation pipeline.
- **IM HTML reports (G-008):** Open report button + `/api/interface/open-report` (path validated under output root).
- **Swiss Tools (N-001):** "Start here" strip — MAC trace, description search, Standard L2 map.
- **IM execution_time (N-002):** Measured on deploy path.
- **MAC trace (G-012):** NX-OS `| include` lines parsed as MAC VLAN PORT (partial single-match resolves correctly).

### Tests

- `tests/test_release_7_0_60.py` — IM blocking validation, topology skipped hosts.
- Manifest v2 updated; `minimum_app_version` 7.0.60.

### Build

- `NetworkSwissToolPro_v7.0.60_OFFLINE.exe`

## [v7.0.59] - 2026-06-21

### Fixed (P0)

- **Search-it stuck progress:** Empty MAC trace and invalid ping CIDR now call `progress_done(error=…)`; API validates before pre-arm (400 response).
- **Interface map manifest:** Removed duplicate `write_run_manifest` call that caused NameError after successful HTML generation.
- **Partial MAC trace:** Full resolved MAC shown in UI + HTML with highlighted search term (single-match and ambiguous paths).

### Fixed (P1)

- **`become_password` dispatch:** Sent on all `/api/execute` payloads; thread-local `utils/task_credentials.py` + Junos `secret` fallback in `connect_permissive`.
- **Search-it XSS hardening:** `escapeHtml()` for MAC trace, description search, and node-analyze summary tables.
- **Progress flicker:** `progress_start_if_needed()` skips counter reset when API already pre-armed the same total.
- **Highlight enrichment:** Failures log a warning and fall back to escaped plain text.

### Fixed (P2)

- **Discovery manifest:** Single `write_run_manifest` after all artifacts are written.
- **VLAN mgmt HTML failure:** Logged as WARNING instead of silent pass.
- **Port map index:** Hostnames escaped in offline index HTML.
- **Import consistency:** VLAN management uses `utils.output_paths.write_run_manifest`.

### Added

- **Session cache lifecycle:** `atexit` clears in-memory credentials on normal process exit (in addition to Stop).

### Tests

- Extended `tests/test_description_search_progress.py`; `tests/test_mac_trace_formatter.py`.

### Build

- `NetworkSwissToolPro_v7.0.59_OFFLINE.exe`

## [v7.0.58] - 2026-06-21

### Fixed

- **Search-it progress (MAC trace, description search, ping scan):** Persistent 1.5s background heartbeat poll (no longer stops when idle); control-plane task completion hooks `searchItOnComplete`; log triggers aligned with backend messages; report open validates last API; `searchItInit()` on page load restores state without tab switch.

### Added

- **Session credential cache:** In-memory sidebar credentials survive browser reload for the process lifetime; cleared only on Stop (`/api/shutdown`). `GET/POST /api/session/credentials` (localhost-only).
- **Partial match highlighting:** Shared `utils/match_highlight.py` with `.nst-match` styling in web UI and HTML reports for description search and MAC trace partial matches.

### Tests

- `tests/test_session_cred_cache.py`, `tests/test_match_highlight.py`; updated description search progress tests.

### Build

- `NetworkSwissToolPro_v7.0.58_OFFLINE.exe`

## [v7.0.57] - 2026-06-21

### Fixed

- **Description Search progress stuck on "Starting…":** UI polling stopped before the worker thread called `progress_start` (idle race). Progress is now pre-armed in `/api/execute`, polling uses a 120s grace window, and completion refreshes the bar + report panel.
- **Description Search HTML:** "View report (HTML)" validates `/api/description-search/last` before opening; report-ready banner shows on complete like MAC trace / ping scan.

### Artifact

- `NetworkSwissToolPro_v7.0.57_OFFLINE.exe`

## [v7.0.56] - 2026-06-21

### Added

- **`utils/output_chrome.py`** — Shared offline report chrome for all txt/html outputs: headers, operator hints, KPI cards, high-contrast light theme, plugin-specific guidance.
- **`00_README.txt`** auto-written in run folders (manifest + plugin runs) explaining report.txt vs report.html offline usage.

### Improved (program-wide UX)

- **Swiss plugin reports:** Rich HTML (not bare `<pre>`), txt headers with how-to-read sections.
- **Ping scan, description search, VLAN mgmt, missing VLAN, MAC trace, Interface Manager:** Unified offline HTML shell with hints and KPIs.
- **Consolidated plugin reports:** Standard NST header/footer and run README.

### Artifact

- `NetworkSwissToolPro_v7.0.56_OFFLINE.exe`

## [v7.0.55] - 2026-06-21

### Fixed

- **Link Inventory unreadable (tab 2):** Light VPC/Discovery Command Center inherited dark body text on dark `#topo-link-inventory` background — fixed with light-theme overrides, white table rows, and sticky dark headers.
- **Link Inventory UX:** Trust tier pills, monospace port badges, sortable Trust column, and operator hint banner.

### Improved

- **vPC map graphics:** On-map “how to read” hint, larger legend pills, thicker selectable edges, white-backed edge labels for readability on light map canvas.

### Artifact

- `NetworkSwissToolPro_v7.0.55_OFFLINE.exe`

## [v7.0.54] - 2026-06-21

### Added

- **Program-wide topology trust:** Bidirectional CDP/LLDP scoring, vPC member cross-check, LACP witness, and interface trust chains on topology mapper, Standard Map connection index, Discovery crawl, and VPC Engineering Board.
- **Trust tiers on map edges:** Verified (green), Medium/unidir (yellow), Inferred (dashed grey), Mismatch (red).
- **Discovery trust pass:** `canonicalize_discovery_graph` assigns confidence/trust on every BFS link.

### Fixed

- **Standard Map briefing:** Restored role KPI counts after trust stats addition.
- **Chrome scroll (v7.0.53 carry-forward):** Bounded map pane; no infinite page expansion.

### Tests

- `tests/test_topology_trust.py`, `tests/test_program_wide_trust.py`, `tests/test_nxos_vpc_parse.py` in prebuild gate.

### Artifact

- `NetworkSwissToolPro_v7.0.54_OFFLINE.exe`

## [v7.0.53] - 2026-06-21

### Fixed

- **VPC Command Center / topology HTML infinite page growth (Chrome):** Bounded `#mynetwork.vpc-map-pane` height (`clamp` + max-height) instead of `height: 100%` in auto-height flex/grid parents; debounced `vpcFitTopology` and resize handlers; single initial fit guard to stop Vis.js fit/redraw loops that prevented scrolling to page bottom.

### Tests

- `tests/test_vpc_map_html_contract.py` — asserts bounded map pane CSS (no unbounded `height: 100%` on vpc-map-pane).

## [v7.0.53] - 2026-06-18

### Added

- **Topology trust layer** (`utils/topology_trust.py`): bidirectional CDP/LLDP validation, vPC member ↔ CDP cross-check, LACP witness, edge trust scoring (Verified/High/Medium/Low/Inferred), MAC dual-homed hints, domain completeness (unscanned peer warnings).

### Changed

- Map pipeline applies trust pass after collection; edges carry `trust_score`, `trust_tier`, `bidirectional`.
- VPC Engineering Board: Interface Trust Chains table, trust column on downstream links, unscanned-peer banners, NX-OS version on peer cards.
- VPC map legend: Verified CDP + Inferred link tiers; edge colors follow trust tier.
- NX-OS parser: classic 7.x table rows, `extract_nxos_version`, expanded peer/keepalive text patterns.

### Tests

- `tests/test_topology_trust.py` — bidirectional, verified scoring, cross-check, domain completeness.
- Extended `tests/test_nxos_vpc_parse.py` — classic 7.x table, NX-OS version extract.

### Artifact

- `NetworkSwissToolPro_v7.0.53_OFFLINE.exe`

## [v7.0.52] - 2026-06-18

### Fixed

- **NX-OS 9.x vPC collection empty:** Shared parser (`utils/nxos_vpc_parse.py`) handles multi-line table headers and Identifier column rows; peer status text like “peer adjacency formed ok” normalizes to `up`.
- **vPC map shows nothing with active domain:** Phase 1 resync fills `vpc_domain_id` and `vpc_details` from `vpc_structured`; single scanned peer with vPC data now forms a domain; CDP can infer unscanned peer.
- **VPC Command Center page clipped:** `body.vpc-command-center` and split overview allow vertical scroll instead of fixed `100vh` overflow hidden.

### Changed

- `topology_mapper`, `vpc_domain_plugin`, and map pipeline use shared NX-OS vPC / port-channel parsing.

### Tests

- `tests/test_nxos_vpc_parse.py` — NX-OS 9.x fixture regression (domain id, table rows, peer status).

### Artifact

- `NetworkSwissToolPro_v7.0.52_OFFLINE.exe`

## [v7.0.51] - 2026-06-18

### Fixed

- **Missing vPC peer-link on Standard Map:** Upgrade existing inter-peer edges to `vpc-peer-link`; synthesize peer-link when a two-member domain has no dedicated edge.
- **Text overlap on map:** Edge descriptions removed from canvas by default; full detail in tooltips and connection index. Optional “Show port labels” toggle for short port names only.
- **Black-on-black legend:** Unified top chrome with high-contrast legend pills (`nst-legend-pill`); legacy header/toolbar/legend hidden in Standard Map mode.
- **Legacy header duplicate:** Standard Map no longer renders old toolbar + legend alongside new chrome.

### Changed

- **Standard Map UX:** Professional unified header (search, KPI stats, legend, port-label toggle); peer-link rows highlighted in connection index; unified search syncs map + table.
- Node labels on canvas show hostname only; port badges in tooltip.

### Tests

- `tests/test_standard_map_v7049.py` — peer-link finalize, top-chrome HTML contract, empty canvas labels.

### Artifact

- `NetworkSwissToolPro_v7.0.51_OFFLINE.exe`

## [v7.0.50] - 2026-06-21

### Fixed

- **Standard Map blank/white canvas (offline / older Chrome):** Explicit map container sizing, dark background (no undefined CSS vars), fallback kept until Vis.js succeeds, retry boot (`nstBootStandardMap`), resize refit.
- **Tiny map in corner:** Schematic/Radial use larger coordinates; `network.fit()` with padding after every layout change.
- **Layout clutter:** Hide floating side panels in Standard Map mode; node/link detail in connection panel.

### Artifact

- `NetworkSwissToolPro_v7.0.50_OFFLINE.exe`

## [v7.0.49] - 2026-06-18

### Added

- **Standard Map NOC/NetEng redesign:** Split-pane layout — connection map always visible alongside enriched connection index (WHO/HOW/WHAT: VLAN, speed, status, platform, confidence).
- **Map style selector:** Tier (default hierarchical), Radial (core-centric), Focus (1–2 hop neighborhood), Schematic (orthogonal tier bands). No matrix view.
- **Briefing KPIs** in exported HTML: devices, links, Po/vPC, unidirectional, mismatch, failed hosts, truncation cap.
- `utils/standard_map_shell.py` — offline shell CSS/JS for Standard L2 Map.
- `tests/test_standard_map_v7049.py` — Cisco edge cases (trunk, Po/vPC, asymmetric CDP, access VLAN, role heuristics, HTML contract).

### Changed

- `link_rows_from_edges` enriched with speed, status, description, confidence, roles, remote platform.
- Standard Map export replaces tab-only link inventory with permanent side panel synced to map selection.

### Artifact

- `NetworkSwissToolPro_v7.0.49_OFFLINE.exe`

## [v7.0.48] - 2026-06-18

### Fixed

- **G-006 IOS-XR VLAN first-class:** `_is_ios_xr()` for `cisco_xr` / `ios_xr` / `iosxr` / `ios-xr`; correct `show vlan` (not brief), `show running-config vlan`, commit apply/save, validation platform notes, VLAN audit show command, and Cisco-family VLAN parse for post-check.

### Added

- `tests/test_g006_ios_xr_v7048.py` — XR detection, show commands, validate, parse.
- `docs/07-operations/vlan-vendor-matrix.md` — operator runbook; linked from backend-architecture and ops README.

### Artifact

- `NetworkSwissToolPro_v7.0.48_OFFLINE.exe`

## [v7.0.47] - 2026-06-18

### Added (Swiss Tools P0/P1)

- **Port Interface Map:** Multi-device parallel collection; per-switch HTML + index when scope >1; `/api/port-map/status` + `/api/port-map/open`.
- **Node Analyze:** Inline results panel, progress polling, `/api/node-analyze/status`; log_func wired to SSH steps.
- **Failed-host drill-down:** Clickable failed-host list in topology status; `failed_hosts.txt` in diag folder; `/api/topology/failed-hosts`.
- **Parallel SSH extended:** VLAN audit/management, network audit, config backup, interface inventory, ping sweep (bounded IP pool).
- **Standard Map infographic:** Report header in HTML (timestamp, device counts, truncation/failed banners); link inventory VLAN column; color-blind-safe legend; A4 landscape print CSS; `/api/topology/export-bundle` ZIP.
- **Discovery ↔ Swiss Tools:** “Standard L2 Map (inventory)” button after BFS discovery completes.

### Fixed

- **G-005:** Interface Manager blocks unknown `device_type` (no silent Cisco IOS default).

### Tests

- `tests/test_swiss_tools_p7047.py` — G-005, header, link VLAN, port map index, API smoke.

### Artifact

- `NetworkSwissToolPro_v7.0.47_OFFLINE.exe`

## [v7.0.46] - 2026-06-18

### Added

- **Parallel SSH pool** (`utils/parallel_device_pool.py`): bounded concurrency (default 5, max 20 via `NST_SSH_MAX_WORKERS`) for topology Phase 1, MAC trace, and description search; respects control-plane cancel between completions.
- **Swiss Tools UX:** L2 Standard Map hero card, mode-specific vPC legend, topology Stop button, truncation/failed-host/worker count in status, auto-open map preference restored.

### Fixed

- **G-001 IM cancel mid-SSH:** Interface Manager checks control-plane abort after backup, between config lines, and before commit/save (Cisco line-by-line deploy).
- **G-004 (partial):** Topology manifest exposes `devices_requested`, `devices_truncated`, `failed_hosts`, `parallel_workers` in API and web status.
- **Web JS:** Removed duplicate `DOMContentLoaded` closing brace in Swiss Tools handlers.

### Docs

- `.cursor/audits/SWISS_TOOLS_ROADMAP.md` — NetOps roadmap for Standard Map infographic quality and P0/P1/P2 backlog.

### Artifact

- `NetworkSwissToolPro_v7.0.46_OFFLINE.exe`

## [v7.0.45] - 2026-06-18

### Fixed (gap remediation G-003–G-014, G-016)

- **G-003 Description search:** Matches ranked in `description_search.run()` with `match_score` (exact > prefix > partial); API/HTML/GUI aligned.
- **G-006 IOS-XR VLAN:** Validation accepts `cisco_xr`; commit-based config apply and save path.
- **G-008 IM HTML reports:** `utils/interface_manager_formatter.py` — structured HTML per discover/validate/deploy.
- **G-009 Task progress:** `devices_done` / `devices_total` on control-plane task registry.
- **G-011 IM conflicts:** VLAN removal and config-fetch failures hard-fail validation (not warnings only).
- **G-012 MAC ambiguity:** Partial MAC matching multiple distinct addresses flagged in log, TXT, HTML, web, and GUI with user-friendly guidance.
- **G-013 Docs gate:** Markdown link validator resolves legacy folder renames + basename fallback.
- **G-014 GUI parity:** Description search in Tools tab; MAC ambiguity dialogs; HTML report prompt.
- **G-016 Live SSH CI:** `tests/test_live_ssh_matrix.py` — offline vendor matrix always; live probe when `NST_LIVE_SSH=1`.

### Artifact

- `NetworkSwissToolPro_v7.0.45_OFFLINE.exe`

## [v7.0.44] - 2026-06-18

### Fixed (P0/P1 — network trust)

- **Verification truth:** VLAN ops return `verification_failed` when post-check fails; summaries use Changed / Skipped / Verify failed / Failed buckets.
- **Rollback honesty:** Removed unsafe auto-rollback messaging; `utils/restore_guide.py` + `/api/interface/restore-guide` for manual restore steps only.
- **Credential security:** Vault APIs restricted to localhost; password GET requires unlocked vault; audit logging on access.
- **Vendor matrix tests:** `tests/test_vendor_matrix.py` + STP NX-OS/IOS fixtures; stale rollback QA assertions removed.
- **Cisco VLAN collision:** Add blocked when VLAN ID exists with different name (parity with Juniper).
- **GUI/web VLAN parity:** GUI runs validation pipeline + `save_config` default aligned with web.
- **IM dry-run:** Junos `commit check` on validate; Cisco syntax validation with explicit warning.
- **IM scope:** Bulk-mode banner — single-host only; backup path + manual restore button in UI.
- **STP reports:** DEMO vs LIVE label in HTML subtitle.

### Artifact

- `NetworkSwissToolPro_v7.0.44_OFFLINE.exe`

## [v7.0.43] - 2026-06-18

### Fixed

- **Interface Manager (Junos):** Discovery uses `| display set` for deployable config; conflict validation supports `set`/`delete` lines and Junos VLAN/mode checks; deploy success count no longer inflated by line count; `im_device_type` syncs from inventory and discover response.
- **VLAN delete (Cisco):** Pre-check blocks delete when VLAN still has active switchports.
- **parse_vlan_output (Junos):** Header skip uses exact matches — no longer drops valid VLAN names containing "Name".
- **Output paths parity:** Credential exports → data root; demo vPC topology → `{data_root}/demos/`; GUI MAC trace writes TXT+HTML; VLAN mgmt HTML report; topology/STP TXT summaries; discovery TXT in same folder as HTML (no duplicate plugin folder); plugin reports include HTML; standards consolidated HTML report.
- **Control plane:** Cooperative cancel in MAC trace (web + adapter), topology mapper, and description search loops.
- **Description search (adapter path):** Writes HTML report when not invoked via web thread.

### Artifact

- `NetworkSwissToolPro_v7.0.43_OFFLINE.exe`

## [v7.0.42] - 2026-06-18

### Fixed

- **Juniper VLAN delete:** `vlan_name` forwarded through `/api/execute`; auto-resolve name from VLAN ID; ELS vs non-ELS syntax restored.
- **Juniper IM deploy:** `commit()` before exiting configure mode (was committing in exec mode).
- **Juniper IM validation:** Accepts `set`/`delete` lines and bracket-style discovered config.
- **VLAN validation gate:** Confirm button disabled until pipeline passes; confirm path forces live run (ignores dry-run checkbox).
- **IM deploy gate:** Requires successful validate in-session before deploy modal.
- **Credentials & startup logs:** Stored under data root (`get_data_root()/credentials`, `get_logs_dir()`).
- **VLAN management outputs:** TXT summary + `manifest.json` per run folder.
- **Config save logging:** Reflects actual `save_result` from device operations.
- **Junos rename guard:** Fails fast when Juniper devices are in rename scope.
- **Interface template:** Junos default config uses `set interfaces` format.

### Artifact

- `NetworkSwissToolPro_v7.0.42_OFFLINE.exe`

## [v7.0.41] - 2026-06-18

### Fixed

- **VLAN Confirm and Execute:** Modal close no longer clears pending action before execution; add/rename/delete now dispatch to `/api/execute` correctly.
- **VLAN validation pipeline:** Dry-run validation panel mirrors Interface Manager (5-step progress) via `POST /api/vlan/validate`.

### Added

- **Control plane:** Task registry with live sidebar panel, stop requests, and cooperative cancel between devices (`utils/task_control_plane.py`).
- **Find Missing VLAN HTML:** Rich audit report (`missing_vlan_report.html`) alongside TXT output.
- **Cursor integration:** `AGENTS.md`, `.cursor/rules/` (auto skill activation), `scripts/sync_devin_to_cursor.ps1` (junction to `.devin/skills` without modifying `.devin/`).

### Changed

- **Interface Manager:** Natural sort order for interfaces; table layout when >50 interfaces; VLAN detail table when >50 VLANs on a port.
- **Search UX:** Description search results ranked by relevance with highlighted partial matches in HTML reports.
- **IM filter:** Relevance scoring for port/description/MAC partial search.

### Artifact

- `NetworkSwissToolPro_v7.0.41_OFFLINE.exe`

## [v7.0.36] - 2026-06-18

### Fixed

- **CRITICAL — VLAN Provisioning (Add/Rename/Delete):** Eliminated `ImportError: attempted relative import beyond top-level package` that aborted every VLAN write operation. Root cause: `utils/config_backup_system.py` used `from ..modules.network_base import connect_permissive` (relative import going two levels up) inside a directory that has no `__init__.py`, making `..` invalid. Fixed by replacing with an absolute import (`from modules.network_base import connect_permissive`) and adding a `sys.path` project-root guard at module load time — identical to the guard already used in `modules/vlan_mgmt_production.py`.
- **Impact scope:** All calls to `add_vlan`, `rename_vlan`, and `delete_vlan` that use `auto_backup=True` (the default) were affected. The import is lazy (inside `auto_backup_pre_change`), so the module loaded fine but crashed at runtime when the first VLAN operation was attempted.
- **Structured logger import:** Changed top-level `from .structured_logger import …` (relative, broken without `__init__.py`) to `from utils.structured_logger import …` (absolute, always safe).

### Technical Details

- **File changed:** `utils/config_backup_system.py`
- **Lines changed:** top-of-file imports + line 368 (lazy import inside `auto_backup_pre_change`)
- **QA result:** 89/90 tests PASS (the 1 failure is a pre-existing missing `RELEASE_NOTES_7.0.4.md` file, unrelated)

### Artifact

- `NetworkSwissToolPro_v7.0.36_OFFLINE.exe`

## [v7.0.35] - 2026-06-11

### Changed

- **Organized output paths:** All logs, reports, maps, compliance, discovery, VLAN, MAC trace, topology, STP, and plugin artifacts write under a dedicated data root (`Documents/NetworkSwissToolPro` or `NST_DATA_DIR`) — never the install/CWD folder.
- **Per-run folders:** Each feature run creates `outputs/<category>/<YYYYMMDD>/<HHMMSS>_<slug>/` with `manifest.json` (two MAC searches => two folders).
- **API:** `/api/version` returns `data_root` and `outputs_root` for operators.

### Artifact

- `NetworkSwissToolPro_v7.0.35_OFFLINE.exe`

## [v7.0.34] - 2026-06-10

### Fixed

- **Interface map MAC search:** Format-agnostic partial/full MAC filter on node interface HTML maps (IOS/NX-OS/Junos).
- **Interface Manager:** Discover enriches `learned_macs` from CAM table; filter box searches MAC addresses.
- **Topology search:** `searchNodes()` matches MAC across colon/dash/dot notations.

### Artifact

- `NetworkSwissToolPro_v7.0.34_OFFLINE.exe`

## [v7.0.33] - 2026-06-10

### Fixed

- **NEW-S1:** `set_master_password` refuses when vault locked (prevents credential wipe).
- **NEW-S2:** Plugin upload uses `secure_filename` + path boundary check.
- **NEW-S3:** Discovery job reads use `_job_store_lock` snapshot.
- **NEW-S4/S5:** Shared `_require_json_body()` + bounded int parsing on discovery/STP/ping/interface routes.
- **NEW-S6/S7:** Credential table DOM-safe rendering; clear label wipes sidebar secrets.

### Artifact

- `NetworkSwissToolPro_v7.0.33_OFFLINE.exe` (~25 MB)

## [v7.0.32] - 2026-06-10

### Added

- **Credential tests:** `tests/test_credential_manager.py` (8 cases: add/force, export/import, master password).
- **Discovery map search:** `disc-map-search-input` on overview map; link inventory filter bar.

### Fixed

- **Credential UX (NEXT-003):** `addCredential(..., force)` passes overwrite flag; Credentials tab refreshes on open; `become_password` sidebar field wired to Use.
- **Map search focus (NEXT-006):** Topology maps highlight match + 1-hop neighbors; dim non-matches instead of hiding.

### Artifact

- `NetworkSwissToolPro_v7.0.32_OFFLINE.exe` (~25 MB)

## [v7.0.31] - 2026-06-10

### Added

- **Offline lab smoke:** Mock-SSH tests for IOS-XE MAC trace and QFX5100 Junos LLDP (`tests/test_lab_smoke_offline.py`).
- **Enterprise QA gate:** `scripts/enterprise_qa_gate.py` (pytest + prebuild + doc links + frozen plugin sim).
- **Doc link integrity:** 0 broken internal markdown links; redirect stubs for legacy paths.

### Fixed

- **Swiss Tools topology:** Port-aware `_topology_edge_link_key` preserves parallel links on distinct ports.
- **Docs:** 54 legacy broken links resolved; `validate_docs_links.py` skips fenced code blocks.

### Artifact

- `NetworkSwissToolPro_v7.0.31_OFFLINE.exe`

## [v7.0.30] - 2026-06-10

### Fixed

- Medium bug backlog (NEW-M1, M3–M9): JSON guards, discovery inventory path, STP retry, platform classifier, health UI.
- Hygiene: `nst_health_ok`, standards V2 alias, `NST_DEBUG` map logs.

## [v7.0.29] - 2026-06-10

### Fixed

- **BUG-0009:** Junos `Physical interface:` same-line status (`Physical link is Up/Down`).
- **BUG-0010:** Full pytest suite green (146/146) — LLDP, interface parsers, graph merge, HTML contracts.
- **NEW-H5:** Junos LLDP local port colon fallback replaced with interface-aware header parse.
- **NEW-C1:** Read-only EXE directory loads plugins from `_MEIPASS` directly.
- **NEW-M2:** Device merge by shared serial number across different hostnames/IPs.

### Artifact

- `NetworkSwissToolPro_v7.0.29_OFFLINE.exe`

## [v7.0.28] - 2026-06-10

### Fixed

- **MAC Address Search (IOS-XE L3):** Normalize colon/dash MAC input to Cisco dotted format for `show mac address-table | include`.
- **MAC Address Search (Juniper):** Multi-command search with Junos 14/QFX syntax fallbacks; improved `xe-`/`ge-`/`ae0.0` parsing.
- **Juniper Interface Map:** LACP/AE bundle discovery links physical members to logical `ae` interfaces; MAC table `.0` unit correlation.

### Added

- `utils/mac_utils.py`, `utils/juniper_iface.py`, `tests/test_mac_trace_parsing.py`.

### Artifact

- `NetworkSwissToolPro_v7.0.28_OFFLINE.exe`

## [v7.0.10] - 2026-05-31

### Fixed

- **Discovery NX-OS LLDP links:** Parsers now handle `Local Port id` (not only `Local Intf`), `System Name: not advertised`, blocks without system name (chassis/MAC identity), and `Port id` carrying a MAC when `Port Description` has the real interface. Neighbor dedupe prefers detail over brief; link inventory shows `n/a` instead of JSON `null` for missing remote ports.

### Changed

- **network_discovery plugin** v1.4.0 — `_finalize_neighbor`, `_dedupe_neighbors`, improved `_parse_cisco_lldp_detail` / brief.

### Artifact

- `NetworkSwissToolPro_v7.0.10_OFFLINE.exe`

## [v7.0.9] - 2026-05-31

### Added

- **Sidebar branding (UX refined):** Logo, product name, version pill, short **Updated** date (full string in tooltip), **Made by AI IDE** — top of sidebar; click opens **About & Help**.
- **UI polish:** Chrome header bar, refined tab strip, accent content cards, monospace **SYS · Task Logs** console header.
- **Docs:** [network-search-workflow.md](docs/08-operations/network-search-workflow.md), [network-search-reports-guide.md](docs/08-operations/network-search-reports-guide.md); librarian audit [LIBRARIAN_AUDIT_v7.0.9.md](docs/00-overview/LIBRARIAN_AUDIT_v7.0.9.md).

### Changed

- **Network Search** tab (renamed from `search_it` in UI); internal APIs unchanged (`/api/search-it/progress`, pane id `diag`).
- **Header:** Title, version, date, and branding removed from top bar (moved to sidebar).
- **UPDATE_DATE** display: sidebar shows `YYYY-MM-DD` only; full release note in `title` attribute.

### Removed

- Mid-sidebar logo block (v7.0.8 placement between filters and Import).

### Artifact

- `NetworkSwissToolPro_v7.0.9_OFFLINE.exe`

## [v7.0.8] - 2026-05-31

### Added

- **Sidebar brand logo:** App icon shown in Target Scope (above Import/Browse) on a synced light card + dark icon plate. Updated favicon asset.

### Removed

- Center workspace watermark (replaced by sidebar logo placement).

### Fixed

- **Topology HTML map not rendering:** Container id was `mynetwork-legacy` while vis.js targeted `#mynetwork` — maps now attach correctly.
- **Topology default view:** Standard CDP/LLDP maps open on **Topology Map** (not hidden behind Link Inventory). vPC Command Center unchanged (Overview map pane).

### Artifact

- `NetworkSwissToolPro_v7.0.8_OFFLINE.exe`

## [v7.0.7] - 2026-05-24

### Added

- **search_it live progress bars:** Discovery-style indication bars for MAC trace, Description search, and Network ping scan (`utils/search_it_progress.py`, `GET /api/search-it/progress`).
- **search_it tab refresh:** Opening **search_it** (or page load) re-syncs progress, restores last-run summaries, resumes polling for in-flight scans, and shows **View report (HTML)** when a server-side last result exists.
- **search_it tab badge:** `● running` / `✓ ready` on the search_it segment when a scan is active or complete.

### Changed

- Background scans continue when switching tabs; returning to search_it no longer loses progress or report buttons.

### Artifact

- `NetworkSwissToolPro_v7.0.7_OFFLINE.exe`

## [v7.0.6] - 2026-05-24

### Added

- **search_it organized reports:** MAC trace, Description search, and Network ping scan write `report.txt`, `report.html`, and `manifest.json` under `reports/<category>/<YYYYMMDD>/<run_id>/` (`utils/search_report_output.py`).
- **search_it HTML + browser:** Description search and ping scan match MAC trace — summary panels and **View report (HTML)** buttons (`/api/description-search/report`, `/api/ping-scan/report`).
- Ops: [`search-it-reports-guide.md`](docs/08-operations/search-it-reports-guide.md).

### Changed

- MAC trace no longer drops `mac_trace_*.txt/html` in the application root; uses the same `reports/mac_trace/` layout.

### Artifact

- `NetworkSwissToolPro_v7.0.6_OFFLINE.exe`

## [v7.0.5] - 2026-05-24

### Fixed

- **MAC trace HTML hostnames:** Reject SSH login prompts (`Password:`, `Username:`, etc.) as device names; MAC trace uses `show version` / switchname resolution. Fixes wrong labels (e.g. `password`) on large multi-vendor inventories.

### Changed

- **VPC Command Center map:** Map-first Overview layout, reliable vis.js boot (pane sizing + retries), toolbar (fit / peers / L2 / reset), board↔map domain highlight, node deduplication before render, default hide of non-vPC L2 edges.

## [v7.0.4] - 2026-05-24

### Added

- **Discovery Command Center:** Light-theme offline HTML (`utils/discovery_map_shell.py`) — Overview (device table + map), Link inventory, Summary; hop/scan-state visuals in `discovery_map_formatter`.
- **Discovery in-app:** Live crawl progress (current host, hop, counts, log ring buffer), filters, scan-state badges, **Open Discovery Command Center** button.
- Ops guide: [`discovery-command-center-guide.md`](docs/08-operations/discovery-command-center-guide.md).

### Fixed

- **VPC topology map:** Universal fixed `x/y` via `_ensure_vpc_nodes_positioned`; when no vPC domain is detected, physical adjacency fallback with banner (edges no longer hidden); map empty-state guards and Swiss Tools status counts (`nodes` / `edges` / `vpc domains`).
- Demo: `DEMO_VPC_TOPOLOGY_v7.0.4.html`, `DEMO_DISCOVERY_COMMAND_CENTER_v7.0.4.html`.
- Artifact `NetworkSwissToolPro_v7.0.4_OFFLINE.exe`.

## [v7.0.3] - 2026-05-24

### Fixed (VPC Command Center hotfix)

- Legacy Engineering Board / Simplified Map tabs no longer break the Command Center (removed duplicate init, fixed board mount + vis.js boot retry).
- Domain dropdown and topology map render together on Overview.

### Added

- **VPC Command Center:** Offline light-theme shell (`utils/vpc_map_shell.py`) — Overview split (engineering board + simplified map), Link inventory, Collected data tab from `06_pre_render_presentation.json`, deferred vis.js init.
- Ops guide: [`vpc-command-center-guide.md`](docs/08-operations/vpc-command-center-guide.md).

### Fixed

- **Audit NEW-C1–NEW-M9:** Frozen EXE plugin bootstrap from `_MEIPASS`; discovery `visited`/`dry_run`; CLI session lock through connect; job-store locks + STP prune; Junos LLDP local port; MAC trace platform rows; edge dedup with ports; safer hostname merge; case-insensitive graph validation; per-job inventory files; MAC trace string matches; silent JSON parse; STP poll UI restore; health `ok` for full mode; tighter IOS classifier.
- Artifact `NetworkSwissToolPro_v7.0.3_OFFLINE.exe`.

## [v7.0.2] - 2026-05-24

### Fixed

- **Health wizard blocking startup:** Removed auto-run of discovery demo and CLI smoke on first launch; **Continue to program** dismisses immediately.
- **Plugin health false negative:** Uses `get_all_metadata()` (≥10 plugins), shows loaded plugin IDs; no reliance on private `_plugins` count ≥11 with zero errors.

### Changed

- `utils/health_check_runner.py`: quick / full / optional CLI smoke modes; default API quick-only.
- Diagnostics MAC copy clarifies inventory-wide trace vs CDP hop-by-hop.
- Ops: [`health-wizard.md`](docs/08-operations/health-wizard.md), [`mac-trace-howto.md`](docs/08-operations/mac-trace-howto.md).
- Artifact `NetworkSwissToolPro_v7.0.2_OFFLINE.exe`.

## [v7.0.1] - 2026-05-24

### Fixed

- **BUG-0007:** Discovery CDP platform `Nexus*` misclassified as JunOS (`'ex' in 'nexus'`); replaced with token-based `classify_os_family()` in [`utils/discovery_graph.py`](utils/discovery_graph.py).
- **Duplicate discovery nodes:** Canonical merge by IP/hostname before map/HTML; edges rewired to canonical ids.

### Changed

- Discovery map labels: OS family + model; sidebar shows `os_family` / `device_type`.
- Topology Swiss Tools: neighbor endpoint normalization on collected edges.
- Plugin `network_discovery` **1.3.0**; app artifact `NetworkSwissToolPro_v7.0.1_OFFLINE.exe`.

## [v7.0.0] - 2026-05-24

### Added

- **NOC Efficiency Bundle**: Centralized hostname resolution (`resolve_hostname_from_prompt` / `resolve_device_hostname`) across core modules and plugins.
- **Unified map shell** (`utils/topo_map_shell.py`): Link Inventory (default), static topology map, adjacency sidebar, and search — used by Discovery, standard/vPC maps, and STP reports.
- **First-launch health wizard**: `/api/health-check/run` validates inventory, port, plugins, offline discovery + vPC demos, and CLI smoke.
- **In-app release notes**: `/api/release-notes` and About tab “What’s new in v7.0.0”.
- **MAC trace path report**: Structured `path_hops`, HTML summary (`utils/mac_trace_formatter.py`), Diagnostics UI table + “View path report”.
- **STP Swiss Tools tab**: Background job API (`/api/stp/run`), demo lab, offline map via `modules/stp_swiss_runner.py`.

### Changed

- Standard and vPC simplified maps embed Link Inventory + enhanced search (hostname, IP, port, Po, vPC domain).
- `VERSION` bumped to **7.0.0**; artifact `NetworkSwissToolPro_v7.0.0_OFFLINE.exe`.

## [v6.9.28] - 2026-05-31

### Added

- **Discovery map UX**: Link Inventory tab (default) + static topology map; adjacency sidebar; offline (no Google Fonts).
- **Config template presets**: NX-OS/IOS trunk, port-channel, trunk+vPC `.j2` files + web preset builder (`/api/templates/presets`).

### Fixed

- **BUG-0006**: Network Discovery NX-OS hostname — no longer uses `show version` banner as device name (`resolve_device_hostname` in `network_base.py`).

## [v6.9.27] - 2026-05-31

### Added

- **vPC Engineering Board (offline-first)**: vPC map HTML opens on a fixed-layout **Engineering Board** tab — domain selector, peer strip, vPC Port-Channel table, downstream links, global consistency CLI, and alerts — no Vis.js physics required to read telemetry.
- **Simplified Map tab**: Static coordinates, physics off, short edge labels, non-vPC links hidden by default (toggle on map tab).

### Fixed

- **NX-OS vPC parsing**: `Peer status` / `vPC keep-alive status` labels in `show vpc` (topology mapper aligned with vpc_domain plugin).
- **Payload gaps**: `port_channels` embedded on topology nodes; peer-link Po and global consistency parameters shown in board and side panel.
- **Presentation**: Per-vPC vs global consistency sections separated in VPC detail panel.

## [v6.9.26] - 2026-05-31

### Fixed

- **Discovery job status (BUG-0002)**: API and UI no longer report success when the plugin returns `status: error`.
- **Discovery jobs memory (BUG-0005)**: Prune in-memory job store to the 50 most recent runs.
- **QA**: Discovery parser tests close fixture files; vPC validation reads `VERSION` dynamically (semver) instead of hardcoding.

### Documentation

- **BUG-0001**: Synced version-awareness fields and walkthrough to v6.9.26 / current OFFLINE EXE and port 5051.

## [v6.9.25] - 2026-05-31

### Fixed

- **Network Discovery (live crawl)**: Fixed `ValueError: not enough values to unpack (expected 3, got 2)` when running Discovery on one or more seed devices. Seed tuples are `(host, device_type)`; the initializer loop incorrectly expected a third depth field (queue-only).

### Added

- **Tests**: Regression coverage in `tests/test_network_discovery.py` for seed unpacking and mocked single-seed crawl entry.

## [v6.9.24] - 2026-05-31

### Added

- **Swiss Tools — topology UX**: Redesigned map panel with Standard vs vPC actions, color legend, live status polling (`/api/topology/status`), **Open Map in Browser** and **Open Diagnostics Folder** after completion.
- **Topology API**: `/api/topology/open` and `/api/topology/open-diagnostics` for the last completed map job; thread tracks `_last_topology` with device OK counts.
- **vPC infographic**: Domain summary header and engineer-oriented copy in `generate_topology_html`; `[TOPOLOGY_READY]` JSON log for console and UI poller.

### Fixed

- **Topology HTML CSS**: Removed stray `}}` in `report_formatter.py` that broke side-panel styles on vPC maps.

## [v6.9.23] - 2026-05-31

### Fixed

- **Discovery tab blank page**: Added missing `tab-discovery` HTML panel (navbar and JavaScript existed without content). Restored Config Templates `tab-templates` panel the same way.
- **Discovery API**: Implemented `NetworkDiscoveryPlugin` class (API previously imported a non-existent class). Multi-seed BFS, demo mode, and `/api/discovery/report/<job_id>` for topology HTML.

### Added

- **Network Discovery v1.1.0**: IOS/NX-OS/Junos device-type detection, serial extraction, CDP brief fallback for legacy IOS, endpoint filters for phones/APs, demo lab topology for offline validation.
- **Tests**: `tests/test_network_discovery.py` with CDP/LLDP/Junos parser fixtures and demo-mode plugin test.

## [v6.9.22] - 2026-05-31

### Documentation

- **Master Prompt Governance v3.0**: Added `docs/13-master-prompts/` hub (`INDEX_PROMPT.md`, `PROMPT_REGISTRY.md`, policies, role/escalation matrices, usage guides, action logs). Verbatim archive of `PLATFORM_PROMPTS` under `archive/platform-prompts-original/`. Root pointer: `INDEX_PROMPT.md`.
- **PROMPT_REGISTRY v3.1.0**: Full required-fields schema (prompt_id, source_prompt, dependencies, status, versioning); Quick Index; platform/archive/linked-doc entries; draft usage slots for eight platform roles.
- **PROMPT_USAGE_MANUAL v3.0**: Council role activation rules, resync/escalation/documentation/quality gates, example workflows, success criteria; nine council usage guides + standard template; ROLE_MATRIX v3.1.
- **PROMPT_ACTIVATION_POLICY v3.0** (`G-13`): Mandatory automatic role activation matrix, dependency chain, Team Meeting escalation, activation logging; INDEX read order §5.
- **ROLE_USAGE_STANDARD v3.0** (`G-14`): 12-section role prompt standard, 7-section usage guide standard, structured output format, action log template; INDEX §5.
- **PROMPT_EXECUTION_RULES v3.0** (`G-15`): Mandatory 15-step read/execute sequence, no-skip rules, logging requirements; INDEX Phase A/B reorganized.
- **PROMPT_GOVERNANCE_POLICY v3.0** (`G-03`): Managed-asset rules, traceability, change/retirement review, governance action log requirements; conflict precedence includes G-15.
- **ROLE_MATRIX v3.0** (`G-04`): Full coordination map (mission, domain, collaborators, reviews, escalation, output artifacts); council + domain specialist tables.
- **ESCALATION_MATRIX v3.0** (`G-05`): Issue-type escalation table (prompt drift, security, QA, conflicts, etc.); blocker conditions; L0–L4 severity retained.
- **DOCUMENTATION_POLICY v3.0** (`G-06`): Mandatory doc review triggers, ownership matrix, documentation action log fields; aligns with LIBRARIAN mandate.
- **QUALITY_GATE_POLICY v3.0** (`G-07`): Eleven review gates, risk-profile rules, no bypass without Team Meeting; quality-gate action log; project test hooks retained.
- **CHANGE_MANAGEMENT_POLICY v3.0** (`G-08`): Eight-phase lifecycle (problem through approval), required artifacts, change-management action log; council role mapping.
- **RELEASE_MANAGEMENT_POLICY v3.0** (`G-09`): Rollout rules, seven required checks, release action log (scope, approvals, rollback, validation, deployment, post-release watch).
- **COMPETITIVE_ADVANTAGE_POLICY v3.0** (`G-10`): Eight review domains, strategic rules, six required outputs, invest/avoid pillars for Network Swiss Tool Pro.
- **PROMPT_MIGRATION_SYNC v3.0** (`G-16`): Migration workflow (10 steps), sync versioning rules, six output requirements; archive-first traceability.
- **ROLE: Prompt Librarian v3.0** (`R-GOV-LIB`): Master-hub role prompt with full G-14 sections; `PROMPT_LIBRARIAN_USAGE.md` (ROLE USAGE) — invoke, best practices, scenarios, expected result.
- **ROLE: System Architect v3.0** (`R-ARCH`): Master-hub role prompt; `SYSTEM_ARCHITECT_USAGE.md` (ROLE USAGE); Architect Review gate alignment.
- **ROLE: Lead Developer v3.0** (`R-ENG`): Council master role; `ENGINEER_USAGE.md` (ROLE USAGE); linked to platform `ENGINEER.md` (P-ENG).
- **ROLE: QA Engineer v3.0** (`R-QA`): Validation, regression, compatibility; release block authority; `QA_ENGINEER_USAGE.md` (ROLE USAGE).
- **ROLE: Security Reviewer v3.0** (`R-SEC`): Trust boundaries, approve/block release; `SECURITY_REVIEWER_USAGE.md` (ROLE USAGE).
- **ROLE: Observability Engineer v3.0** (`R-OBS`): Diagnostics, telemetry gaps, block visibility regression; `OBSERVABILITY_ENGINEER_USAGE.md` (ROLE USAGE).
- **ROLE: Documentation Steward v3.0** (`R-LIB`): Doc/code/prompt parity, require updates before completion; `DOCUMENTATION_STEWARD_USAGE.md` (ROLE USAGE); `LIBRARIAN_USAGE.md` alias.
- **ROLE: Release / Change Manager v3.0** (`R-REL`): Readiness, rollback, block release; `RELEASE_MANAGER_USAGE.md` (ROLE USAGE); G-09 gate consolidation.
- **ROLE: Product / Platform Strategist v3.0** (`R-PROD`): Mission, competitive advantage, prioritization; `PRODUCT_STRATEGIST_USAGE.md` (ROLE USAGE); G-10 alignment.
- **ROLE: Team Meeting Council v3.0** (`R-COUNCIL`): Cross-functional review, required issue schema, exact AI prompts; `TEAM_MEETING_COUNCIL_USAGE.md`; G-11 template updated.
- **FINAL OPERATING INSTRUCTION v3.0** (`G-17`): Binding IDE contract — preserve/sync prompts, auto-activate roles, enforce policy chain and gates, success criteria; INDEX read order step 7.
- **Combined council prompts** (`roles/combined/`): One file per role merging R-* master + U-* usage (e.g. `ROLE_LIBRARIAN_USAGE_PROMPT.md`, `ROLE_PROMPT_LIBRARIAN_USAGE_PROMPT.md`); registry C-* entries v3.1.31.
- **GLOBAL MASTER PROMPT RULES v4.0** (`G-18`): 20 absolute rules, mission, vision, engineering principles; `INDEX_PROMPT` v4.0; G-03 precedence #1; read order step 3.
- **INDEX_PROMPT v4.0 (user spec):** Numbered read order `00`–`26`, simple commands table, mandatory rules 1–14; stubs `00_GLOBAL_RULES` through `25_ROLE_*`; `26_CHECK_SYSTEM_FOR_BUGS.md`; `bugs/_TEMPLATE/` fix and validation prompts.
- **Hub consolidation (registry 4.0.3):** Council roles canonical only in `roles/combined/ROLE_*_USAGE_PROMPT.md`; removed duplicate split R/U files, C-* registry rows, numbered hub stubs, and `bugs/_TEMPLATE/` (use `docs/14-bug-reports/_SCAFFOLD/`). INDEX, registry, activation policy, and role matrix aligned to canonical paths.
- **PROMPT_REGISTRY v4.0:** Preamble aligned to required fields, status values, rules, versioning, sync policy; G-01 document version 4.0.0 (entry data release 3.1.33 in change log).
- **CHECK_SYSTEM_FOR_BUGS v4.0** (`roles/CHECK_SYSTEM_FOR_BUGS.md`): Full-team bug sweep; `docs/14-bug-reports/` structure; copy-paste fix/validation/doc/version prompts; `_SCAFFOLD/` templates.
- **FINAL_OPERATING_INSTRUCTION v4.0** (`G-17`): Simple user commands table; IDE must list; success criteria including continuous development UX.

### Fixed

- **[P0] Jinja2 TemplateSyntaxError — Application Fail-to-Start**: Fixed a critical crash in `modules/web/templates/index.html` (line 2668) that caused every HTTP request to return `500 Internal Server Error`, rendering the entire web application completely non-functional.

  - **Root Cause**: The `tmplBuildVarForm()` JavaScript function (Config Templates tab, added in v6.9.21) contained the expression `{{ ${v} }}` inside an HTML attribute within a Jinja2 template. Jinja2 attempted to parse `{{ ${v} }}` as a server-side template expression and failed on the `$` character with `unexpected char '$' at 128744`.

  - **Fix**: Escaped the Jinja2 brace delimiters using Jinja2's string-literal syntax: `{{ '{{' }} ${v} {{ '}}' }}`. This outputs literal `{{ }}` braces to the browser while keeping the JavaScript `${v}` template literal interpolation fully functional at runtime.

  - **Impact**: Application could not serve any page. All users on v6.9.21 experienced complete web interface failure immediately after startup. No network operations were possible through the web interface.

  - **Location**: `modules/web/templates/index.html:2668`, function `tmplBuildVarForm()`

## [v6.9.21] - 2026-05-26

### Added
- **Network Discovery Plugin v1.0.0**: New plugin for recursive CDP/LLDP neighbor discovery starting from seed devices. Supports multi-platform parsing (Cisco IOS, IOS-XE, NXOS, Juniper JunOS), duplicate detection by MAC/UID, topology graph visualization using vis-network.js, and JSON inventory export. Includes root password support for Juniper devices and configurable crawl depth (1-3 hops).

- **Config Templates Plugin v1.0.0**: New Jinja2-based configuration template generator with safe read-only rendering. Bootstraps example templates on startup in program directory templates/ folder. Features variable extraction from templates, dynamic form generation for variable input, preview rendering (no automatic push), and template save/load functionality. Includes error indications for template syntax errors.

- **Discovery Tab**: New UI tab for Network Discovery with seed host input, crawl depth configuration, real-time job status polling, discovered devices table with hostname/IP/platform/serial/depth/reachability, topology visualization button, and JSON export functionality.

- **Templates Tab**: New UI tab for Configuration Templates with template list dropdown, template editor with syntax highlighting, automatic variable scanning and form generation, render preview panel, copy to clipboard, and save functionality.

### Fixed
- **Favicon Display**: Fixed favicon not displaying in HTML by adding Flask routes `/favicon.ico` and `/static/favicon_program.png` using `send_file` with `_get_resource_path()` for proper path resolution in both dev and EXE modes.

- **Standards Folder in EXE Mode**: Fixed standards folder creation to use program directory instead of home directory. On application startup, creates `standards/` folder in program directory with bundled standards.json and standards.yaml files, plus category subdirectories (Security, NTP, SNMP, Logging, Naming, Interface, AAA, Routing, QoS, Redundancy, Management, Health, Crypto, Compliance). Updated upload endpoint to save to this folder and plugin to check this folder for uploaded files.

- **Path Resolution**: Updated `_get_resource_path()` in both `vlan_checker_web.py` and `standards_validator.py` to check program directory for writable files (standards/, templates/) after checking bundled resources in EXE mode. Updated `list_available_policies()` to scan both bundled policies/ and program directory standards/ folders.

### Changed
- **Standards Validator Plugin v2.1.0**: Updated path resolution to check program directory standards folder for uploaded files in EXE mode. Enhanced policy file discovery to scan both bundled and custom policy locations.

## [v6.9.20] - 2026-05-26

### Fixed
- **Standards Validator Plugin v2.1.0**: Fixed critical file reading issue where uploaded policy files could not be found/read by the plugin, causing scan failures. Added `_get_resource_path()` helper function to plugin for PyInstaller EXE compatibility. Updated `_load_policies()` to use consistent path resolution. Updated upload endpoint to save files to writable location in EXE mode (user's home directory) instead of read-only _MEIPASS. Plugin now checks both bundled resources and home directory for uploaded files in EXE mode.

### Added
- **Favicon Integration**: Added favicon_program.png to HTML head for browser tab display. Added favicon to PyInstaller spec file datas and as window icon for EXE. Favicon is now mandatory and hardcoded in the application.

### Changed
- **Standards Validator**: Created standards.json file alongside standards.yaml for JSON policy support. Both YAML and JSON formats are now fully supported with 65+ policies covering security, NTP, SNMP, logging, naming, interface standards, AAA, routing, QoS, redundancy, interface hardening, management plane, health indicators, crypto, compliance, and Juniper-specific checks.

## [v6.9.19] - 2026-05-26

### Fixed
- **vPC Domain Plugin v2.3.1**: Added defensive programming fixes to prevent AttributeError and crashes when verification functions encounter None values or non-string inputs. Added isinstance() checks before all string operations (.lower(), .splitlines(), etc.). Added type validation for VLAN lists, members lists, and output strings. All verification functions now handle missing or malformed data gracefully without crashing.

## [v6.9.18] - 2026-05-26

### Changed
- **vPC Domain Plugin v2.3.0**: Major enhancement - executes actual verification commands for all 10 recommendations. Added verification logic for peer-link, keepalive, Type-1/Type-2 consistency, per-vlan consistency, VLAN consistency, CDP neighbors, port-channel members, and vPC statistics. Implemented human-readable verification results section with PASS/FAIL/WARN indicators, impact descriptions, and recommended actions for each verification. Added verification summary showing total checks, passed, failed, warnings, and unknown counts. Enhanced command set with show vpc peer-link, show vpc role, show interface brief, and show vpc legacy. Replaced static recommendations with dynamic verification results that show actual mismatches/errors. Added clear indication when vPC domain is healthy with no errors or mismatches detected.

## [v6.9.17] - 2026-05-25

### Fixed
- **vPC Domain Plugin v2.2.1**: Fixed critical parsing bug where vPC entries with "peer-link" in reason field (e.g., "Peer-link is down") caused premature termination of parsing. Changed section break detection to only break on section headers (lines starting with "peer-link" or "vpc peer-link") rather than containing the text. Added validation to skip error messages containing "error", "please", or "check". Added validation to ensure vPC ID is numeric, port-channel matches pattern, status and consistency are valid. Added validation in report formatting to only render valid vPC entries. Added warning message when vPC data is detected but cannot be parsed correctly.

## [v6.9.16] - 2026-05-25

### Changed
- **vPC Domain Plugin v2.2.0**: Comprehensive enhancement for network engineers. Fixed vPC entries parsing to handle NXOS table format correctly (now displays all vPCs with port-channels). Added consistency parameter parsing: Type-1 (global), Type-2 (interface), per-vlan consistency status. Added configuration inconsistency reason and type-2 inconsistency reason parsing. Enhanced command set with "show vpc consistency-parameters" and "show vpc statistics". Improved port-channel parsing to extract VLAN membership and member interfaces. Enhanced report formatting with dedicated consistency parameters section. Added vPC member details including port-channel, status, consistency, reason, and active VLANs. Added troubleshooting recommendations for consistency issues.

## [v6.9.15] - 2026-05-25

### Changed
- **MAC Address Search UI**: Updated search_it page MAC address search to match beautiful design pattern of other search options. Added gradient background (yellow/amber theme), descriptive text, styled button, and hint text showing example MAC formats.
- **Plugin Upload Error Handling**: Enhanced validate_upload() in plugin_registry.py to provide clearer error messages for indentation errors during plugin upload validation.
- **vPC Domain Plugin**: Fixed indentation error at line 142 in vpc_domain_plugin.py that was causing plugin upload failures.

## [v6.9.14] - 2026-05-25

### Fixed
- **Ping Scan CMD Popup**: Added Windows-specific subprocess flags (STARTUPINFO, CREATE_NO_WINDOW) to hide CMD popup during ping scan in vlan_checker_web.py.
- **Connectivity Ping CMD Popup**: Added Windows-specific subprocess flags to hide CMD popup during connectivity check ping in modules/connectivity.py.
- **Logout Logging - save_config.py**: Added explicit logout logging ("Logging out from device...", "Successfully logged out") with cleanup logging in finally block.
- **Logout Logging - description_search.py**: Added explicit logout logging with cleanup logging in finally block.
- **Logout Logging - vlan_compare.py**: Added explicit logout logging with cleanup logging in finally block.
- **Logout Logging - network_audit.py**: Added explicit logout logging with cleanup logging in finally block.
- **Logout Logging - node_analyze.py**: Added explicit logout logging with cleanup logging in finally block, and added log_func parameter.
- **Logout Logging - node_interface_topology.py**: Added explicit logout logging with cleanup logging in finally block, and added log_func parameter.

### Changed
- **Consistent Logout Pattern**: All device connection modules now follow the same logout logging pattern as connectivity check: "Logging out from device..." before disconnect, "Successfully logged out" after disconnect, and cleanup logging in finally block.

## [v6.9.13] - 2026-05-25

### Fixed
- **vPC Domain Plugin v2.1.0**: CRITICAL parsing fixes for NXOS command output formats.
- **Peer-link Status Parsing**: Fixed regex to match actual NXOS format "Peer status : peer link is down" instead of expecting "status" keyword on same line.
- **Keepalive Status Parsing**: Fixed regex to match actual NXOS format "vPC keep-alive status : Suspended (Destination IP not reachable)" instead of expecting "status" keyword on same line.
- **CDP Neighbor Parsing**: Completely rewrote CDP parser to use table-based parsing instead of keyword matching, preventing incorrect extraction of field labels as device names.
- **Status Normalization**: Added `_normalize_peer_status()` and `_normalize_keepalive_status()` functions to convert various NXOS status formats to standardized "up"/"down" values for health checks.
- **Health Check Accuracy**: vPC health check now correctly reports peer-link and keepalive status instead of "unknown".
- **Documentation**: Added comprehensive inline documentation with expected NXOS output formats and status normalization rules.

### Added
- **Comprehensive Plugin Documentation**: Added detailed docstrings explaining expected NXOS output formats for `show vpc` and `show cdp neighbors` commands.
- **Status Normalization Rules**: Documented all known NXOS status values and their normalized equivalents.
- **Corrected Demo Files**: Created demo files with realistic NXOS output format for healthy and unhealthy vPC scenarios.

## [v6.9.12] - 2026-05-25

### Added
- **vPC Domain Plugin v2.0.0**: Comprehensive vPC domain analysis with per-VPC interface details, CDP peer validation, and domain correlation.
- **Per-VPC Interface Enumeration**: Added parsing for individual vPC entries including port-channel, status, and consistency information.
- **CDP Neighbor Validation**: Implemented CDP neighbor parsing for peer switch validation and correlation.
- **Domain Correlation Logic**: Added global cache to correlate switches sharing the same vPC domain ID across the inventory.
- **Port-Channel Details**: Added parsing for port-channel interfaces including VLAN membership and member interfaces.
- **Enhanced vPC Report Formatting**: Comprehensive report with vPC member ports, port-channel details, CDP neighbors, and domain peer correlation.
- **Demo Output Files**: Created 4 demo files showing various vPC scenarios (no vPC, primary, secondary, unhealthy).
- **Network Ping Scan Feature**: Added ping scan functionality to search_it tab for offline network discovery.
- **Ping Scan UI**: Added green-themed ping scan section below Description Search in search_it tab with CIDR input examples.
- **Ping Scan Backend**: Implemented Python-based ping scanning using standard library (subprocess + ipaddress) for offline compatibility.
- **Ping Scan Report**: Human-readable report showing used vs unused IPs with progress indication during scan.

### Fixed
- **vPC Command Fallback**: Enhanced command execution with fallback mechanism for vPC commands (show vpc, show vpc brief, show vpc peer-keepalive, show cdp neighbors, show interface port-channel).
- **vPC Logging**: Added detailed logging for each vPC command attempt with success/failure status.

## [v6.9.11] - 2026-05-25

### Fixed
- **vPC Domain Plugin Enhancement**: Enhanced vpc_domain_plugin.py (v1.0.0 → v1.1.0) with vivid, human-readable output for vPC topology analysis.
- **Enhanced Report Formatting**: Added comprehensive vPC domain analysis report with role interpretation, health check indicators, and actionable recommendations.
- **Role Interpretation**: Added automatic interpretation of primary/secondary vPC roles with explanatory context.
- **Health Check Indicators**: Added visual health status indicators (✅/❌/⚠️) for peer-link and keepalive status.
- **Recommendations Section**: Added 5-point recommendations for vPC troubleshooting and monitoring.
- **Plugin Validation**: Reviewed all 11 plugins for command correctness and output formatting - all plugins use appropriate fallback mechanisms for NXOS, IOS, and JUNOS.

## [v6.9.10] - 2026-05-25

### Fixed
- **Critical NXOS command fix**: Fixed incorrect command for NXOS - changed from "show interfaces description" (plural) to "show interface description" (singular) which is the correct NXOS syntax.
- **Command fallback mechanism**: Implemented robust command fallback system that tries multiple commands in priority order until one succeeds. Prevents failures due to version differences or command variations.
- **Error detection**: Added comprehensive error detection to identify "Invalid command", "Unrecognized command", "syntax error", and other failure patterns.
- **Enhanced logging**: Added detailed logging for all command attempts including success/failure status, error reasons, and output samples. Diagnostic logs now show the complete command fallback chain.
- **Command priority lists by OS**:
  - NXOS: "show interface description" → "show interfaces description" → "show interface brief"
  - IOS: "show interfaces description" → "show interface description" → "show interface brief"
  - JUNOS: "show interfaces descriptions" → "show interfaces description" → "show interfaces terse"
- **Port-channel fallback**: Added fallback for NXOS port-channel commands: "show port-channel summary" → "show interface port-channel brief"
- **Production-grade reliability**: System now behaves like a network engineer's tool - tries alternatives before giving up, logs everything for troubleshooting, and handles edge cases gracefully.

## [v6.9.9] - 2026-05-25

### Fixed
- **Interface parsing critical fix**: Completely rewrote interface description parsing to capture ALL interfaces (both physical and logical) on NXOS, IOS, and JUNOS devices. Previously only captured 1 interface due to overly aggressive header skipping and rigid regex patterns.
- **Device-type-specific parsing**: Added separate parsing strategies for IOS, NXOS, and JUNOS with device-type detection to use the correct format for each OS.
- **Header detection improvement**: Made header skipping intelligent - only skips lines that are primarily header keywords (>50% of words), preventing valid interface lines from being skipped.
- **Interface pattern support**: Enhanced fallback strategy to support various interface naming patterns including subinterfaces (e.g., Se0/0/0.100, ge-0/0/0, lo0, Ethernet1/1, Gi1/0/1).
- **Status validation**: Added validation to ensure parsed lines contain valid status words before adding to results, preventing false positives.

## [v6.9.8] - 2026-05-25

### Fixed
- **Interface search regex support**: Added regex pattern matching capability to interface search. Now supports advanced patterns (e.g., "vpc.*", "eth[0-9]+", ".*server.*") with automatic fallback to substring matching for invalid regex patterns.
- **Interface search output**: Enhanced diagnostic logging to show full description, interface name, status, and source for each match. Critical for partial letter searches where seeing the complete description is essential.
- **Interface search diagnostics**: Added search method tracking (regex vs substring) in diagnostic logs for troubleshooting.

## [v6.9.7] - 2026-05-25

### Fixed
- **Interface search parsing**: Completely rewrote interface description parsing to support NXOS, IOS, and JUNOS with multiple fallback strategies. Previously failed with "0 interfaces scanned" due to rigid regex patterns.
- **Interface search diagnostics**: Added comprehensive diagnostic logging system that creates `interface_search_diagnostics/` folder with detailed reports including raw command output, parsing results, and search matches for troubleshooting.
- **Interface name search**: Enhanced search to include interface names (eth/vpc/port-channel/etc) in addition to descriptions with case-insensitive substring matching.

## [v6.9.6] - 2026-05-25

### Fixed
- **Interface search**: Enhanced search to now search both interface descriptions AND interface names (eth/vpc/port-channel/etc) with case-insensitive substring matching (not exact match). Previously only searched descriptions.
- **vPC Domain plugin**: Enhanced parsing with multiple regex patterns to handle various NX-OS output formats for domain ID, role, peer-link status, and keepalive status extraction. Improved human-readable output formatting.

## [v6.9.5] - 2026-05-24

### Added
- **search_it tab**: Renamed "Diagnostics & MAC" to `search_it` with a new **Description Search** (case-insensitive substring across all interface descriptions).
- **vPC Domain ID plugin** (`vpc_domain`): Reports vPC domain number, role, peer-link, and keepalive status from NX-OS `show vpc`.

### Changed
- **Topology map UI (v7.1)**: Smoother panel transitions, refined peer-link telemetry panel, per-peer keepalive/peer-link display with NX-OS-aware status parsing.

### Fixed
- **Keepalive display**: Recognizes NX-OS strings such as "peer is alive" (not only exact `alive`/`up`).

## [v6.9.4] - 2026-05-24

### Added
- **vPC Member Interfaces (per switch)**: Collects `show vpc` / `show vpc brief` table rows and expands port-channel physical members into `vpc_member_interfaces` for the HTML sidebar and diagnostics.
- **Topology diagnostic package**: Each map run creates `topology_diagnostics_YYYYMMDD_HHMMSS/` in the app working directory with `00_README.txt`, raw/pre/post JSON stages, `06_pre_render_presentation.json`, `07_post_render_manifest.json`, and `vpc_map_data_TEMPLATE.json` for lab data injection.
- **Editable data template**: `vpc_map_data_TEMPLATE.json` documents the schema used before HTML rendering so real network values can be merged for analysis.

### Fixed
- **Empty "Member Interfaces & vPCs" panel**: `bundled_links` are promoted to the Vis.js edge payload and read from `edge_data` when needed; structured `vpc_member_interfaces` is used as fallback.
- **`show vpc brief` parsing**: Used when the main `show vpc` table is empty (NX-OS variants).
- **HTML performance on older PCs**: Disabled continuous edge flow animation by default, reduced physics iterations, disabled node shadows, and use non-animated `network.fit()` after stabilization for stable offline viewing.
- **Edge type resolution in UI**: `extractVPCData` reads `edge.type` or `edge.edge_data.type` so shared/orphan links categorize correctly on older saved maps.

## [v6.9.3] - 2026-05-14

### Added
- **Hybrid vPC Observation System**: Revolutionized the vPC topology mapper to show both logical and physical layers simultaneously. Physical switches now remain visible while connected to a virtual `VPC_Domain` anchor, providing the requested "Physical-to-Logical" visibility.
- **VPC Shared Link Visualization**: Links from two separate switches to a single node are now preserved and styled as `vpc_shared`, enabling clear observability of dual-homed port-channels.

### Fixed
- **Blank Map Transition Bug**: Resolved the critical issue where the map would disappear or become blank when interacting with the side panel. Implemented a robust `network.fit()` and `network.setSize()` logic triggered after CSS transitions to ensure the canvas always recalibrates to the visible viewport.
- **JavaScript Resilience**: Hardened `hoverNode` and `selectNode` event handlers with `try-catch` blocks and explicit `Array.isArray` checks for `vpc_members`. This prevents UI crashes caused by missing or malformed metadata fields.
- **Interface Mapping Synchronization**: Updated the global `norm_int` function to support `TwentyFiveGigE` -> `Twe` mapping, ensuring consistent interface lookups across all topology and reporting modules.

## [v6.9.2] - 2026-05-14

### Fixed
- **Topology Mapper Crash**: Resolved a critical `'str' object has no attribute 'get'` error in `modules/adapters.py` by implementing defensive type-checking for vPC metadata dictionary parsing.
- **Data Model Hardening**: Refactored `modules/topology_mapper.py` to wrap raw CLI strings (consistency, brief, LACP) in dictionary objects, ensuring consistent API access.

## [v6.9.1] - 2026-05-14

### Added
- **Apple-Style UI Overhaul**: Transitioned the entire observability dashboard to a "Glassmorphism" / Hi-Tech NOC aesthetic (v8.5), featuring premium shadows, SF Pro typography, and Apple-inspired color palettes.
- **Human-Readable Link Enrichment**: Connection edges now display physical interface speed, operational status, and truncated descriptions directly on the graph for instant troubleshooting without clicking.
- **Enterprise Rebranding**: Standardized all UI headers and metadata to reflect the "Made by AI IDE" identity.

### Fixed
- **Offline Topology Viewer**: Resolved critical "Map Cannot Be Viewed" errors in air-gapped environments by natively embedding the `vis-network.min.js` dependency into the generated HTML reports.
- **Topology Mapper Hardening**: Fixed a critical `'str' object has no attribute 'get'` crash during vPC summary table generation by implementing defensive type-checking for internal metadata strings.
- **Demo Generator Stability**: Updated `create_demo_map.py` to correctly load local assets and support the new enriched data structures.

## [v6.9.0] - 2026-05-14


### Added
- **Structured Telemetry Enrichment**: Integrated deep network metadata collection for Port-Channels, vPCs, and LACP partners across NX-OS, IOS, and JunOS.
- **Cross-Platform Correlation**: Implemented CDP/LLDP cross-validation mechanisms and LACP partner verification to ensure high confidence network mapping.
- **Connection Intelligence Panel**: Added advanced frontend analytics detecting shared versus single-homed (orphan) VPC connections with risk validation badges.
- **LACP State Validation**: Edge info panels now display rich LACP partner system ID and port state for detailed troubleshooting.

### Enhanced
- **VPC Operational Summary**: Redesigned VPC Detail Panel natively supports real-time visibility into active VLANs, Keepalive status, Domain roles, and consistency checks per member.
- **Topology Parsing Architecture**: Replaced brittle regex patterns in Phase 1 (`topology_mapper.py`) with 6 new enterprise-grade structured parsers (`_parse_vpc_full`, `_parse_lacp_neighbors_nxos`, etc.).
- **Defensive Rendering Pipeline**: The UI now gracefully handles incomplete or inferred edge topology by leveraging the new `cdp_validation_map` for explicit confidence scores.

## [v6.8.1] - 2026-05-10

### Fixed
- **[CRITICAL] VPC Map Blank Issue**: Fixed blank map when scanning 2 devices in vPC domain.
  - **Root Cause**: VPC transformation removed internal peer-links but never created replacement edges.
  - **Fix**: Added placeholder edge creation between VPC domain node and members when no downstream links exist.
  - **Location**: `modules/adapters.py:1037-1088`
  - **Impact**: vPC maps now display correctly for 2-device scenarios.

- **HTML Fallback Content**: Added visible fallback content when JavaScript fails to render.
  - Users will see "Initializing visualization..." message instead of blank white canvas.
  - Message includes version and instructions to check browser console (F12).
  - Fallback is cleared automatically when Vis.js renders successfully.

### Enhanced
- **MAP-PIPELINE Logging**: Updated to v6.8.1 for consistent version tracking.
- **Console Diagnostics**: Added more detailed logging for edge creation events.

## [v6.8.0] - 2026-05-07

### Added
- **Architectural Hardening**: Implementation of a "Defensive Rendering Pipeline" for vPC topology.
- **Orphan Edge Filtering**: Runtime sanitization in the browser to prevent crashes caused by inconsistent graph data.
- **Physics Stabilization**: Explicit mass and gravity constants for vPC nodes to prevent "coordinate explosion" in large hierarchies.

### Fixed
- **[P1] Empty Map Syndrome**: Resolved edge-case silent script terminations that previously left the topology canvas blank despite successful data collection.
- **Event Handling**: Wrapped event listener management in try/catch blocks for improved resilience in restricted browser environments.

## [v6.7.7] - 2026-05-06

### Fixed

- **[P1] vPC Map Empty / Blank UI:** `modules/adapters.py`, `utils/report_formatter.py` — Resolved critical rendering issues where topology maps appeared blank.
  - **Deep ES5 Compatibility**: Performed a full audit and "De-ES6-ification" of all browser-side JavaScript. Replaced arrow functions (`=>`), template literals (backticks), and ES6 methods (`startsWith`) with ES5 equivalents to ensure compatibility with legacy browser engines.
  - **Asset Portability**: Improved `vis-network.min.js` embedding logic to ensure the library is bundled directly into the HTML for air-gapped/offline use.
  - **Self-Loop Removal**: Eliminated internal self-loop edges for vPC domains which caused hierarchical layout stabilization failures in Vis.js.
  - **HTML Structure**: Fixed a dangling `</div>` in the vPC summary template that broke browser rendering of the map container.
  - **JS Resilience**: Re-implemented `network.fit()` with a multi-stage approach (IterationsDone + Stabilized events) plus a 1-second safety fallback.
  - **Metadata Fix**: Added fallback description extraction in `toggleDescriptions` to prevent JS errors when edge metadata is partially nested.

## [v6.7.6] - 2026-05-04

### Fixed

- **[P1] vPC Map Empty After Generation:** `utils/report_formatter.py` — vPC layout uses `physics: { enabled: true }` with hierarchical repulsion. After stabilization, Vis.js positioned nodes off-screen and never auto-fitted the viewport. Added `network.once('stabilizationIterationsDone', network.fit)` and a 300ms fallback `setTimeout(network.fit)`.

- **[P1] Interface Map: No Descriptions in Popup:** `modules/node_interface_topology.py` — Description parser only matched lines where the second token was a status keyword. `show interfaces description` uses a tabular format where description is the 4th column. Added multi-strategy parser: full regex → simplified regex → tab-split fallback.

- **[P1] Interface Map: Missing MACs on Port-Channels:** `modules/node_interface_topology.py` — MAC matching used loose substring logic causing false matches and missed port-channel entries. Rewrote to use exact `norm_int()` match with proper skip logic for MAC addresses, VLAN numbers, and type keywords.

## [v6.7.5] - 2026-05-06

### Fixed
- **2-Device VPC Map Blank Issue**: Fixed blank map when scanning exactly 2 devices in vPC domain.
  - **Root Cause**: VPC transformation logic only created edges for shared downstream links, not internal peer-links.
  - **Fix**: Added explicit peer-link edge creation for 2-device vPC scenarios where no downstream shared links exist.
  - **Logging**: Added [MAP-PIPELINE] phase logging for better debugging.

- **Version String Synchronization**: Fixed hardcoded v6.2.4 version strings in CLI connectivity HTML template.
  - Updated `modules/web/templates/cli_terminal.html` to show v6.7.5.

### Enhanced
- **5-Phase Validation Pipeline**: Added structured logging for map generation:
  - Phase 1: Device Collection (validates successful connections)
  - Phase 2: Edge Processing (validates edge detection)
  - Phase 3: VPC Transformation (validates domain clustering)
  - Phase 4: Node Building (validates node metadata)
  - Phase 5: HTML Generation (validates file creation)

- **Interface Traffic Statistics**: Added upload/download rate display in Interface Map tooltips.
  - Collects `input_rate` and `output_rate` from `show interface` command for NXOS/IOS/JUNOS.
  - Displays formatted traffic rates (e.g., "↓1.5 Mbps ↑2.3 Mbps") in port tooltips.
  - Supports human-readable formatting (Kbps, Mbps, Gbps).

## [v6.7.4] - 2026-05-06

### Fixed
- **DEMO VPC Map Blank Issue**: Fixed critical issue where DEMO topology map failed to render.
  - **Root Cause**: DEMO file used external `<script src="modules/web/vis-network.min.js">` which fails when file opened directly in browser.
  - **Fix**: Embedded vis.js library inline in DEMO file (702KB) for standalone offline functionality.
  - **Error Handling**: Added JavaScript error handling with try-catch around network initialization and diagnostic console logging.
- **Generated Maps Error Handling**: Added defensive error handling in `utils/report_formatter.py` for network initialization failures.

### Enhanced
- **Interface Descriptions**: Enhanced interface description display in VPC detail panels and edge tooltips for better network documentation visibility.

## [v6.7.3] - 2026-05-04

### Fixed
- **Blank VPC Map Issue**: Resolved critical bug where VPC topology maps appeared blank/empty.
  - **Root Cause**: `vpc_members` field was only added to node metadata, not to the actual node objects passed to JavaScript frontend.
  - **Fix**: Added `vpc_members` field to node objects in `modules/adapters.py` (line 1182).
  - **JavaScript Hardening**: Added data validation and fallback member extraction in `utils/report_formatter.py` to handle edge cases.
  - **Diagnostics**: Added debug logging in both backend and frontend to trace VPC data flow.

## [v6.7.2] - 2026-05-04

### Added
- **VPC Visualization Layer v7.0**: Complete redesign of VPC topology visualization with 3-View Progressive Disclosure System.
  - **Global Topology View**: VPC domains displayed as large, prominent indigo nodes with drop shadows. Shared connections = thick blue edges, Orphan connections = dashed red edges.
  - **VPC Detail Panel**: Slide-out panel showing peer-link visualization, member device grid (Primary/Secondary), and interface listings.
  - **Connection Intelligence Panel**: Categorized view of shared (dual-homed) vs orphan (single-homed) connections with risk badges and export functionality.
- **Modern CSS Design System**: CSS custom properties for VPC colors, 8px spacing grid, card-based layouts, smooth 150-250ms transitions.
- **DEMO VPC Topology**: Standalone `DEMO_VPC_TOPOLOGY_v7.0.html` with sample 6-device network (2 VPC domains, 2 servers) for testing visualization without real devices.
- **Navigation History Stack**: Back/close buttons maintain view state for intuitive navigation between Global → Detail → Intelligence views.

### Changed
- **VPC Node Styling**: VPC domains now use indigo gradient (#6366f1 → #8b5cf6), larger size (60px), white text, prominent shadow for instant visual recognition.
- **Panel Architecture**: Replaced single side panel with dedicated VPC Detail and Connection Intelligence panels.

## [v6.7.1] - 2026-05-04

### Fixed
- **CLI Crash (AttributeError)**: Resolved a critical server-side crash in `Flask-SocketIO` when using Flask 3.1.x by disabling automatic session management.
- **Resilient CLI Routing**: Re-implemented robust Room + SID hybrid routing for CLI WebSocket traffic. Initial ACKs use SID for zero-latency feedback, while subsequent data streams use Room-based routing to ensure stability across browser reconnections.
- **Improved Background Handshake**: Standardized the background connection lifecycle with consistent progress reporting and definitive TCP/SSH error delivery.

## [v6.7.0] - 2026-05-04

### Added
- VPC logical topology rendering: Transforms vPC pairs into single logical domains on the map.
- Interface description visualization: Shows interface descriptions on link tooltips and optionally on labels.

### Fixed
- WebSocket CLI connectivity: Formalized state machine to prevent race conditions during SSH connection rendering.
- Missing interface descriptions: Handled extraction of `desc` from interface data into Vis.js tooltips.
- Incorrect VPC pairing logic: Replaced outdated domain mapping to now cleanly identify overlapping redundant links as single shared paths or orphan links.

### Improved
- Map clarity: Removed cluttered redundant links from vPC pairs to downstream devices.
- Data model: `VPCDomain` node restructuring allows standard Vis.js rendering without hacky node duplication.

## [6.6.0] - 2026-04-30

### Added
- **vPC Topology Premium Pass**: Enhanced peer-clustering via `vis.Network` groups, enabling logical side-by-side alignment for vPC domain members without manual coordinates.
- **Glow & Shadow Edge Styling**: Implemented high-visibility orange glows for vPC member links and purple shadows for peer-links to improve architectural clarity.
- **Glassmorphism Intelligence Dashboard**: Redesigned the vPC summary side-panel with a modern slate theme, backdrop-blur (8px), and Inter typography.
- **Hardened CLI Connectivity**: Resolved persistent "Stuck on Connecting" state by eliminating redundant WebSocket SID emits and implementing immediate backend-to-frontend diagnostics.
- **Immediate Console Diagnostics**: Added real-time print statements in `vlan_checker_web.py` for terminal connection handshakes to facilitate air-gapped troubleshooting.

### Fixed
- **CLI character doubling**: Removed double-emit logic (Room + SID) in `vlan_checker_web.py` that caused redundant output rendering in high-latency environments.
- **Stale vPC Summary styles**: Replaced inline white/orange table styles with a cohesive dark-mode glassmorphism palette.
- **Topology Font Scaling**: Standardized on the Inter font family across all Vis.js nodes for improved readability at high zoom levels.

## [6.5.5] - 2026-04-28

### Added
- **Standards Validator Plugin** (`modules/plugins/standards_validator.py`): Compares live device config against a user-editable YAML policy library. Reports violations with exact remediation commands. Read-only.
- **Expanded Policy Library** (`policies/standards.yaml`): 40+ policies across 10 categories — Security, NTP, SNMP, Logging, Banner, Naming, Routing, QoS, Redundancy, Interface, Management, Health, Crypto, Compliance, Juniper-specific.
- **`policies/` bundled in EXE**: Policy library is now included in the offline distribution package and PyInstaller spec. The EXE reads `policies/standards.yaml` from the folder next to the executable.
- **CLI Smoke Test** (`tests/test_cli_smoke.py`): Mandatory mock-SSH test that proves the CLI terminal connection flow works before every build. 11 steps covering connect, prompt receipt, write, disconnect.
- **`_prebuild.py` gate**: All builds now require syntax check + plugin load + CLI smoke test + safety checks to pass before PyInstaller runs.



### Fixed (CLI Terminal + MAPS Interface Data + M-Bugs)

- **[P0] CLI Terminal stuck on "Connecting":** `modules/cli_manager.py` completely rewritten with full inline documentation. Root causes: (1) `_do_connect()` never forwarded progress to `log_callback` — frontend saw nothing during the 10–45s SSH handshake. (2) `self.hostname` was never updated from the initial IP — stayed as IP forever. Fixed: every SSH handshake step now emits progress via `log_callback`; initial prompt is read after shell open to extract real hostname; buffered prompt bytes forwarded to frontend immediately so device prompt appears without delay.

- **[P0] MAPS side panel: no interfaces / speed / VLAN / MACs:** Four root causes fixed: (1) `topology_mapper.py` desc parser created `int_meta` entries without `speed`/`vlan`/`duplex`/`macs` keys — JS got `undefined`. Fixed: all four fields initialised to empty string/list in every code path. (2) MAC normalization mismatch — `_parse_mac_table` used `norm_int()` but `valid_interfaces` check was case-sensitive exact match. Fixed: added case-insensitive fallback. (3) Edge panel `f_int_data` lookup used raw CDP port name (`GigabitEthernet0/1`) but `int_meta` keys are normalized (`Gi0/1`) — always showed `unknown`. Fixed: `norm_int()` applied before lookup with raw-name fallback. (4) `adapters.py` MAC merge block didn't guarantee all fields exist. Fixed: `setdefault()` for all display fields before passing to frontend.

- **[P1] MAPS side panel: neighbor-only nodes show nothing:** Nodes discovered via CDP/LLDP but not directly scanned had empty `interfaces` dict — side panel was blank. Fixed: added "Interface Data Unavailable" message explaining the device needs to be in inventory to see interface details.

- **[P1] M-Bug: `network_audit.py` no `log_func`, no `finally` disconnect:** Added `log_func=None` parameter and `finally: conn.disconnect()` to prevent SSH session leaks on exception.

- **[P1] M-Bug: `config_backup.py` no `log_func`, no `finally` disconnect:** Same fix applied.

- **[P1] M-Bug: `save_config.py` no `log_func`, no `finally` disconnect:** Same fix applied.

- **[P1] M-Bug: `vlan_compare.py` no `log_func`, no `finally` disconnect:** Same fix applied.

- **[P1] Removed `restore_backup()`:** `utils/config_backup_system.py` — the experimental config restore method was unsafe (blind line-by-line paste corrupts NX-OS configs). Removed entirely along with `rollback_vlan_change()` in `vlan_mgmt_production.py` and the `/api/plugins/rollback` route in `vlan_checker_web.py`.

- **[P2] Added `utils/app_logger.py`:** Production-grade structured logging with rotating JSON files, audit trail, GUI callback support, and `export_logs()` for AI/support analysis.



### Fixed (Plugin System, VLAN Scope & Topology)

- **[P0] Plugin Registry Syntax Error:** `modules/plugin_registry.py` — `_validate_metadata()` had a double-colon `::` syntax error that prevented the entire module from importing. All 9 plugins were silently failing to load on every startup. Fixed to single colon.

- **[P0] Missing Plugin Report Functions:** `utils/report_formatter.py` — All 9 plugins import `save_plugin_report`, `append_to_master_report`, and plugin-specific `format_*_report` functions that did not exist in the file. Added all missing functions: `save_plugin_report`, `append_to_master_report`, `generate_consolidated_plugin_report`, `format_vlan_audit_report`, `format_serial_number_report`, `format_device_time_report`, `format_critical_logs_report`, `format_interface_errors_report`, `format_environment_status_report`. All 9 plugins now load with 0 errors.

- **[P1] Single Device VLAN Operations Return 0 Targets:** `vlan_checker_web.py` — `filter_inventory()` applied the group filter before the single-host match. When the group dropdown showed a non-matching group from a previous bulk session, the selected host was filtered out, returning 0 devices and the error "Filtered scope resulted in 0 target devices." Group filter is now skipped entirely in single mode.

- **[P1] vPC Topology Map Disorganized:** `modules/adapters.py`, `utils/report_formatter.py` — vPC map used `barnesHut` physics producing a chaotic, unreadable layout. Replaced with hierarchical `UD` layout (same as standard topology). vPC summary panel replaced with a structured table showing Device, vPC ID, Port-Channel, Status, and Peer-Link columns.

- **[P1] Topology Side Panel Missing Speed/VLAN/MAC:** `modules/topology_mapper.py` — `show interface status` was parsed for link state only; Speed, VLAN, and Duplex columns were never extracted. Added `_parse_status_line_fields()` helper. Interface data in the side panel now shows speed (1G/10G/etc.), VLAN assignment, duplex, and MAC addresses per interface.

## [6.4.0] - 2026-04-27

### Added
- **Intelligent Topology Mapping**: Complete re-engineering of the correlation engine and visualization.
- **Troubleshooting Side Panel**: Interactive panel for real-time device info, port stats, and MAC address correlation.
- **Link Confidence Scoring**: Visual indicators for bidirectional (Green), asymmetric (Yellow), and mismatch (Red) links.
- **vPC Styling**: Dedicated rendering for vPC Peer-Links and Member ports.
- **MAC Transparency**: Correlation of learned endpoint MAC addresses to inter-switch trunk links.

## [6.2.6] - 2026-04-26

### Fixed (Sprint 1 Audit Remediation — Production Hardening)

- **[P0] SSH Algorithm Mismatch:** `modules/network_base.py` — `connect_permissive()` completely
  rewritten with a two-pass strategy matching the proven approach in `cli_manager.py`.
  Pass 1 uses modern default Paramiko algorithms (works on IOS-XE 17.3+, NX-OS 9.3+, Juniper 21.x+).
  Pass 2 falls back to legacy `disabled_algorithms` for older hardware (IOS 12.x, NX-OS 7.x).
  Previously, ALL connections were forced to legacy mode, causing silent failures on modern devices.

- **[P0] Missing Plugins in PyInstaller Spec:** `build_scripts/NetworkSwissToolPro_v6_2_5_BETA.spec` —
  Added `modules.plugins.stp_topology_visualizer` and `modules.plugins.unused_trunk_pruner`
  to `hiddenimports`. These two plugins were copied to the dist folder but not declared,
  risking load failures in the compiled EXE.

- **[P0] Dependency Version Pinning:** `requirements.txt` — All 9 dependencies now have exact
  version pins (`==`). Previously only `netmiko` was pinned; all Flask/SocketIO deps used `>=`
  ranges, creating offline build reproducibility risk. Added `wsproto`, `bidict`, and `h11`
  which were already used in the spec but not declared in requirements.

- **[P1] Silent Report Failures:** `utils/report_formatter.py` — All file-writing functions
  (`write_text_file`, `write_csv_file`, `append_text_file`, etc.) now log errors to stderr
  instead of silently swallowing exceptions. Failed report writes are now visible in the
  operations log.

- **[P1] Version Single Source of Truth:** `main.py` and `vlan_checker_web.py` — Hardcoded
  `VERSION = "6.2.5-BETA"` strings replaced with `_read_version()` helpers that read the
  `VERSION` file at startup. Eliminates all future version drift across entry points.

- **[P1] MAC Address Input Validation:** `modules/mac_trace.py` — Added `_validate_mac()`
  with a strict safe-character regex before the MAC is concatenated into a device CLI command.
  Prevents potential command injection via malformed MAC strings.

- **[P1] Plugin Manifest Accuracy:** `PLUGINS_INCLUDED.txt` —
  - Updated header from `v6.0.0-BETA` to `v6.2.5-BETA`
  - Corrected "BUNDLED PLUGINS (7 TOTAL)" to "(9 TOTAL)"
  - Added full entries for `stp_topology_visualizer` (v1.0.1) and `unused_trunk_pruner` (v1.0.1)
  - Fixed stale `build_v6_0_0_beta.bat` reference to current spec file name
  - Updated validation instructions to reference 9 plugins
  - Updated MANIFEST DATE to 2026-04-26



### Added (Enhanced Plugin Reporting)

- **Improved:** Consolidated plugin reporting that aggregates results from multiple devices into a single, high-quality "human-readable" document.
- **Improved:** Visual formatting for plugin outputs (Serial Number, VLAN Audit, etc.) including status emojis (✅/❌) and aligned table layouts.
- **Improved:** Indicative report filenames that now include the device IP or hostname for single-device scans.
- **Hardened:** Centralized report orchestration in `report_formatter.py` to ensure all future plugins benefit from consistent, visual output formatting.

## [6.2.4] - 2026-04-23

### Fixed (CLI Terminal "Stuck on Connecting")

- **Fixed:** Critical race condition in CLI handshake where the frontend was stuck on "Connecting" despite a successful WebSocket link.
- **Fixed:** Implementation of "Handshake Delay" (100ms) and "Double-Emit Enforcement" to ensure the client PTY is fully ready before the session status is sent.
- **Improved:** Standardized versioning across `main.py`, `vlan_checker_web.py`, `cli_manager.py`, and the frontend.
- **Hardened:** Offline dependency bundling verified in the build spec for air-gapped production use.

## [5.5.0] - 2026-04-19

### Fixed (XHR Poll Error / Transport Error)

- **Fixed:** XHR poll errors and transport errors preventing CLI terminal from connecting to server.
- **Added:** Comprehensive startup logging to `logs/startup.log` for diagnosing EXE startup issues.
- **Added:** Server health check (`checkServerHealth()`) in CLI terminal before Socket.IO connection.
- **Added:** Enhanced error messages in terminal showing possible causes (firewall, antivirus, server not ready).
- **Improved:** Socket.IO configuration with longer timeouts (30s) for EXE cold start scenarios.
- **Improved:** Increased reconnection attempts (15) with exponential backoff for better reliability.
- **Improved:** Server startup with detailed logging of Socket.IO initialization and port availability.
- **Changed:** `initSocket()` is now async and performs health check before attempting Socket.IO connection.
- **Changed:** DOMContentLoaded event handler is now async to support await on `initSocket()`.

## [5.4.9] - 2026-04-19

### Fixed (CLI Terminal Connectivity)

- **Fixed:** Critical bug where CLI terminal was stuck in "Connecting" state because `initSocket()` was never called.
- **Fixed:** ImportError for missing `list_cli_sessions()` function in `cli_manager.py`.
- **Improved:** Socket.IO connection now initializes immediately on page load, ensuring reliable server communication.

## [5.4.8] - 2026-04-19

### Fixed (Connectivity Handshake Hardening)

- **Fixed:** Handshake failures caused by ambiguous `localhost`/IPv6 resolution by forcing `127.0.0.1` binding.
- **Added:** Technical Handshake Log UI (Debug toggle) for real-time frontend troubleshooting.
- **Added:** `/health` and `/debug_status` HTTP endpoints for definitive service isolation.
- **Improved:** Resilience in high-latency environments by increasing ping timeouts to 60s.

## [5.4.7] - 2026-04-19

### Fixed (Absolute Bundle & Crash Protection)

- **Fixed:** Startup crashes (Unhandled Exception) caused by unsafe imports in the diagnostic logger.
- **Fixed:** Missing root packages in the bundle by switching to `collect_all` PyInstaller hooks.
- **Improved:** Application resilience by implementing "Safe Imports" for all background components.

## [5.4.6] - 2026-04-19

### Fixed (Deep Dependency Bundling)

- **Fixed:** Missing `wsproto`, `bidict`, and `h11` libraries in standalone binaries by implementing deep collection hooks.
- **Improved:** Build system reliability by recursively collecting all sub-modules for the SocketIO stack.
- **Added:** Tracking for `wsproto` and `bidict` in the startup "Dependency Splash" log.

## [5.4.5] - 2026-04-19

### Changed (Port Diversification)

- **Changed:** Migration of all application network traffic from Port 5000 to Port 5051 to avoid system conflicts.
- **Fixed:** "Server Offline" issues caused by port occupation on common developer ports.
- **Improved:** Auto-launcher reliability by specifically targetting the new dedicated port range.

## [5.4.4] - 2026-04-19

### Fixed (Total Infrastructure Stabilization)

- **Added:** Diagnostic Splash at boot (Logs all library versions to `operations.log`).
- **Added:** Port Probe (Verifies Port 5000 is free before server start).
- **Added:** Frontend-visible error codes for SocketIO handshake failures.
- **Improved:** Protocol stability by hardening ping/pong timeouts and intervals.
- **Fixed:** Missing EngineIO hidden imports in the build spec for enhanced binary stability.

## [5.4.3] - 2026-04-19

### Fixed (Transport & "Server Offline" Issues)

- **Fixed:** "Server Offline" state by forcing Long Polling as a base transport layer.
- **Added:** UI feedback for the active transport method (Polling/WebSocket).
- **Added:** Deep diagnostics logging for Engine.IO/SocketIO in `logs/operations.log`.
- **Improved:** Server bootstrap stability with `allow_unsafe_werkzeug` for bundled EXEs.

## [5.4.2] - 2026-04-19

### Fixed (Handshake & Socket Stabilization)

- **Fixed:** Race condition in "Connecting..." state by moving WebSocket initialization to page-load.
- **Added:** "Server Status" visual indicator to verify backend health before allowing CLI operations.
- **Fixed:** Handshake message loss by implementing "Double-Emit" logic (Room + SID).
- **Improved:** UX by safety-locking the "Connect" button until the server is confirmed ready.

## [5.4.1] - 2026-04-19

### Fixed (Resilience & "Connecting" Hangs)

- **Fixed:** Eternal "Connecting..." state by implementing stable SocketIO Rooms based on `session_id`.
- **Added:** Pre-Flight TCP Probe with 2s timeout to catch host/firewall issues instantly.
- **Improved:** Handshake speed by explicitly disabling GSSAPI and DNS lookups in Paramiko.
- **Improved:** Connection resiliency across socket stutters/reconnects.

## [5.4.0] - 2026-04-19

### Changed (Major Architectural Overhaul — "Streaming Shell")

- **Replaced:** Netmiko Scripting Engine with raw Paramiko `invoke_shell()` for the CLI Terminal.
- **Added:** Bi-directional byte streaming for zero-latency interactivity (keystroke passthrough).
- **Added:** Background `ShellReader` thread per session to handle real-time terminal output.
- **Added:** Terminal resize synchronization (PTY resize) to match xterm.js dimensions.
- **Removed:** Synchronous "wait for prompt" logic that caused terminal hangs.

## [5.3.3] - 2026-04-19

### Fixed (Critical — "Infinite Spin" Resolved)

- **Fixed:** Resolved a `NameError` in the background connection task that caused the thread to die silently.
- **Added:** Background watchdog to intercept crashes and report them to the UI.
- **Added:** Real-time log streaming from Netmiko handshake to the terminal window.
- **Added:** Detailed SSH session logging to `logs/ssh_debug_[session_id].log` for deep troubleshooting.

## [5.3.2] - 2026-04-19

### Fixed (CLI Connection Hangs & Progress UX)

- **Fixed:** SSH connection "stuck on connecting" by wrapping the handshake in a hard 45-second wall-clock timeout via `ThreadPoolExecutor`.
- **Fixed:** Eliminated `find_prompt()` and `enable()` during initial connection to prevent infinite hangs on unusual banners or MOTDs.
- **Fixed:** Enabled `fast_cli=True` to reduce `netmiko` internal polling delays.
- **Fixed:** Removed invalid `read_timeout` from `send_command()` which was causing crashes in `netmiko 4.1.2`.
- **Added:** Real-time `cli_progress` status updates streamed to the terminal UI during the connection phase.

## [5.3.1] - 2026-04-19

### Fixed (Critical — CLI Terminal Fully Non-Functional)

- **Root cause #1:** `flask-socketio` was never installed. CLI WebSocket layer silently disabled on startup; terminal appeared to connect but no SSH was ever initiated.
- **Root cause #2:** `telnetlib_compat` shim not loaded before `netmiko` in `cli_manager.py` — caused silent `ImportError` on Python 3.13+.
- **Root cause #3:** `disabled_algorithms` override for Paramiko 4.x missing from `cli_manager.py` ConnectHandler — SSH rejected by legacy devices.
- **Root cause #4:** `socket.io.min.js` loaded from CDN — terminal broken in offline/air-gapped environments.
- **Root cause #5:** `initSocket()` called on every connect attempt — multiple stacked WS connections.
- **Fix:** `modules/cli_manager.py` fully rewritten with all corrections applied.
- **Fix:** `socket.io.min.js` now bundled locally in `static/js/`.
- **Fix:** `requirements.txt` updated with `flask-socketio`, `python-engineio`, `simple-websocket`.

## [5.3.0] - 2026-04-19

### Fixed

#### CLI Terminal Synchronization Fix
- **Fixed:** The "Phantom Disconnect" bug. Refactored the core Flask-SocketIO `cli_connect` and `cli_command` handlers to execute as strictly asynchronous background tasks (`socketio.start_background_task`). This decisively prevents the 30-second SSH negotiations from blocking the primary server event thread, ending the starvation of WebSocket heartbeat PINGs that forced the browser to incorrectly drop the connection early.
- **Fixed:** The stubborn `v5.1.0` web header label is resolved. The hardcoded version parameter deep in the `vlan_checker_web.py` render template has been unlinked from past builds.

## [5.2.0] - 2026-04-19

### Fixed

#### Deep CLI Terminal Stability
- **Fixed:** Instant crash caused by uninstantiated `self.device_type` when `cli_manager.py` spawns SSH processes. The CLI interface is now fully functional across all generic connections regardless of network platform type.
- **Fixed/Retained:** Legacy Paramiko backward compat overrides for offline switches.

### Internal & Cleanups
- **Removed:** Deep workspace cleanup. Cleared over 100MB of legacy specs (`v4.x` configs), duplicate `dist_backup` zips, and excessive QA log JSON dumps that littered the workspace.
- **Added:** Formal roadmap established in `docs/08_HISTORY/ROADMAP.md` covering subnets, monitoring, and compliance scanning for iteration v6.
- **Updated:** Compiled `NetworkSwissToolPro_v5_2_0_Offline.exe` build from SCRATCH.

## [5.1.0] - 2026-04-19

### Fixed

#### CLI Terminal Connection
- **Fixed:** Device type now correctly read from inventory file and passed to CLI connection
- **Fixed:** Connection dialog pre-populated with correct device type from inventory
- **Fixed:** Multi-platform support (NXOS, IOS, JUNOS) working correctly with platform-specific connection parameters
- **Fixed:** Encryption errors handled gracefully with automatic retry using legacy settings
- **Fixed:** Backwards compatibility for older OS versions (IOS 12.x, JUNOS 12.x, etc.)
- **Fixed:** Connection timeout and error handling improved

#### UI/UX
- **Fixed:** "Made by AI IDE" branding now properly visible in header with professional styling
- **Fixed:** Branding appears on all pages (main UI and CLI terminal)
- **Fixed:** Connection feedback messages added for better user experience

#### Metadata
- **Fixed:** Compile date updated to 2026-04-19
- **Updated:** Version to 5.1.0 across all files

### Added

#### API
- **Added:** `/api/get_device_type` endpoint to fetch device type from inventory
- **Added:** Inventory parsing function with support for section headers

#### Technical
- **Added:** Platform-specific connection parameters (NXOS, IOS, JUNOS)
- **Added:** Automatic encryption error detection and legacy mode retry
- **Added:** Connection logging and status feedback

**Full details in [RELEASE_NOTES_5.1.0.md](RELEASE_NOTES_5.1.0.md)**

## [5.0.0] - 2026-04-17

### Added

#### CLI Terminal Interface (Major Feature)
- **Web-based SSH terminal** for interactive device access
- **"Connect via CLI" button** in Single Device mode
- **Real-time terminal** using xterm.js via CDN
- **WebSocket communication** via Flask-SocketIO
- **Multiple concurrent sessions** - one per device
- **Privacy-first design** - terminal content NOT logged
- **Auto-disconnect** after 10 minutes idle
- **Session recovery** with reconnect option

**New Files:**
- `modules/cli_manager.py` - SSH session management
- `modules/web/templates/cli_terminal.html` - Terminal UI

**Modified Files:**
- `vlan_checker_web.py` - Added WebSocket routes and SocketIO
- `modules/web/templates/index.html` - Added CLI button
- `requirements.txt` - Added flask-socketio dependency

### Fixed

#### Syntax Error in vlan_mgmt.py
- **Fixed:** Unclosed parenthesis in JUNOS ELS detection (line 22)
- Changed nested double quotes to single quotes for command string

#### Topology Mapper HTML Generation
- **Fixed:** `generate_topology_html()` missing `extra_header` parameter
- Added `extra_header=""` default parameter and template usage

### Improved

#### JUNOS Compatibility
- **Enhanced:** ELS/Non-ELS VLAN syntax detection
- **Added:** SRX firewall MAC trace support (`show arp`)
- **Validated:** Full compatibility across EX, QFX, SRX, MX series
- **Documented:** Complete JUNOS compatibility matrix

## [4.5.8] - 2026-04-16

### Fixed

#### Topology Mapper JavaScript Bug
- **Fixed:** "dict object has no attribute 'upper'" error in Standard Map and vPC Map
- **Root Cause:** JavaScript in `index.html` was passing object `{map_mode: 'all'}` instead of string `'all'`
- **Fix:** Changed `onclick="runAction('topology', {map_mode: 'all'})"` to `onclick="runAction('topology', 'all')"`
- **Files Modified:** `modules/web/templates/index.html` (lines 477, 482)
- **Both buttons fixed:** Standard Map (`'all'`) and vPC Map (`'vpc'`)

## [4.5.7] - 2026-04-14

### Fixed

#### Thread Error Handling
- **Fixed:** Tasks getting stuck immediately (ping/SSH check, MAC search, maps)
- Added try-except wrappers around all thread functions in `vlan_checker_web.py`
- Added explicit "Starting..." and "Complete" logging for all operations
- Added critical error logging with full traceback for debugging

#### Connection Disconnect Logging
- **Added:** Explicit disconnect logging across all network operations
- New `safe_connection()` context manager in `network_base.py` for guaranteed cleanup
- All modules now log "Connecting to device...", "Successfully connected", "Logging out...", "Successfully logged out"
- `vlan_audit.py` - Added `log_func` parameter with full disconnect logging
- `mac_trace.py` - Added `log_func` parameter with full disconnect logging
- Proper try-finally blocks ensure disconnect always happens even on errors

### Added

#### Connection Context Manager
- **New:** `safe_connection()` context manager in `modules/network_base.py`
- Ensures connections are always properly closed
- Provides consistent logging for all connection lifecycle events

## [4.5.2] - 2026-04-14

### Added - Production Hardening Release

#### Structured Logging System
- **New Module**: `utils/structured_logger.py` - Production-grade JSON logging
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Operation tracing with device context and parameters
- Config state tracking (PENDING → PUSHED → VERIFIED → COMMITTED)
- Three log streams: operations.log, errors.log, audit.log
- Legacy-compatible adapter for GUI/Web integration

#### Configuration Backup System
- **New Module**: `utils/config_backup_system.py` - Automatic config backup management
- Per-device backup storage: `backups/devices/{hostname}/`
- Automatic pre-change backups for all VLAN mutations
- Backup manifest with metadata (hash, size, trigger reason)
- 24-hour backup health monitoring with CLI check
- Diff comparison and rollback capability
- Keeps last 50 backups per device (auto-cleanup)

#### Production VLAN Management
- **New Module**: `modules/vlan_mgmt_production.py` - Enterprise-grade VLAN operations
- Idempotent operations (skips if desired state already exists)
- VLAN ID validation (1-4094, reserved VLAN detection)
- Post-change verification (automatic validation)
- Enhanced dry-run mode with exact command preview
- Config state logging and backup tracking
- Rollback suggestion on failure

#### Smoke Test Framework
- **New Module**: `tests/smoke_tests.py` - Automated test suite
- 11 test categories: infrastructure, data, network, integration
- CLI test runner: `python main.py test`
- Category-based test selection
- Result validation and reporting

#### CLI Enhancements
- New command: `python main.py test` - Run smoke tests
- New command: `python main.py cli --task backup-check` - Check backup health
- Integrated startup logging initialization

#### Documentation Updates
- Updated `docs/MASTER_DOCUMENTATION.md` with new architecture
- Created `RELEASE_NOTES_4.5.2.md` with comprehensive release details

### Changed
- `modules/adapters.py` - Integrated structured logging and production VLAN module
- `main.py` - Added test mode and backup-check task, initialized structured logging
- `VERSION` - Updated to 4.5.2

### Backward Compatibility
- **100% backward compatible** - No breaking changes
- All existing CLI commands work unchanged
- Existing GUI/Web interfaces function identically
- Legacy logging continues to work alongside new structured logging

## [4.5.1] - 2026-04-13
### Fixed
- Added visible Save Device Config quick-access button directly in the GUI VLAN Management tab.
- Verified Web runtime version banner/API reports 4.5.1 and includes save_config action in UI payload.

## [4.5.0] - 2026-04-13
### Added
- **VLAN Dry-Run Mode**: Added dry-run execution for VLAN add/rename/delete in both GUI and Web UI to preview commands without sending configuration changes.
- **Pre-Change Snapshot**: VLAN mutating operations now automatically capture per-device pre-change VLAN configuration snapshots into timestamped directories.
- **Post-Change Verification**: VLAN mutating operations now validate expected state after execution (present after add/rename, absent after delete) and log explicit verification results.

### Changed
- **VLAN Adapter Pipeline**: Enhanced shared adapter workflow to log command plans, dry-run behavior, verification status, and snapshot output paths.
- **Version Update**: Bumped runtime and release version to `4.5.0`.

## [4.4.0] - 2026-04-13
### Added
- **Save Config Feature**: Added a dedicated `save_config` workflow to persist device config using the active scope model (Single/Bulk/Group) in both GUI and Web editions.
- **Config Persistence Module**: Added `modules/save_config.py` to centralize Cisco/NX-OS startup save and Juniper commit behavior under the standard JSON contract.

### Changed
- **VLAN Operational Logging**: VLAN add/rename/delete now clearly logs whether changes are already persisted (Junos commit) or still running-only (Cisco startup save pending).
- **Web Version Alignment**: Updated web backend runtime version metadata to `4.4.0`.
- **Template Path Reliability**: Updated web app and build script to use `modules/web/templates` for local runtime and PyInstaller bundling.

## [4.3.0] - 2026-04-12
### Added
- **Centralized Router (`main.py`)**: Introduced a unified entry point for the entire system supporting GUI, Web, and CLI modes.
- **Headless CLI Core**: Enabled non-interactive task execution (Backup, Audit, Connectivity) via `python main.py cli`.
- **System Environment Validation**: Added pre-boot checks to ensure critical inventory and directory structures exist.
- **Dependency Consolidation**: Centralized inventory parsing logic into `modules/network_base.py`.

### Changed
- **Refactored Entry Points**: `vlan_checker_gui.py` and `vlan_checker_web.py` are now modular and importable as libraries.
- **Updated Dependencies**: Added Flask to `requirements.txt` and pinned Netmiko for production stability.

## [4.2.0] - 2026-04-12
### Changed
- **Major Architectural Refactor**: Fully decoupled business logic from the GUI (`vlan_checker_gui.py`) and Web (`vlan_checker_web.py`) monoliths.
- **Adapter Layer Implementation**: Centralized all workflow orchestration into `modules/adapters.py`, eliminating ~1,000 lines of duplicated networking code.
- **Side Effect Isolation**: Moved all file I/O, report formatting, and HTML/CSV generation to `utils/report_formatter.py`.
- **Standardized JSON Contract**: Enforced strict adherence to JSON-based communication between the UI and the network modules.
- **Cleaned Codebase**: Removed all Netmiko/Paramiko imports and monolithic thread bodies from the main interface scripts.

## [4.1.1] - 2026-04-09
### Added
- **Operational Master Prompts (OPMP)**: Initialized core operations framework in `docs/OPERATIONAL_PROMPTS/` with `QA.md`, `BUILD.md`, and `BACKUP.md`.
- **System Governance**: Enforced strict production engineering lifecycle rules including mandatory backups, versioning, and changelog maintenance.

## [4.0.0] - 2026-04-09
### Internal
- Conducted full system code audit.
- Created `docs/MASTER_DOCUMENTATION.md` to serve as the single source of truth for architecture and usage.
- Enforced system lifecycle governance policies.

## [3.1.0] - 2026-02-26
### Added
- **Node Blacklist**: Automatically filters out non-hostname strings (e.g., `password`, `login`, `username`) from the topology map.
- **Premium Node Dashboards**: Redesigned infographic popups with status icons (✅/❌), connection summaries (Active/Total), and improved typography.
- **Multi-Link Grouping**: Improved table layout for nodes with multiple logical and physical connections.

### Fixed
- **Prompt Sanitization**: Hardened hostname extraction to strip trailing punctuation (`#`, `>`, `:`) ensuring clean node labels.

## [3.0.0] - 2026-02-26
### Changed
- Juniper & Cisco Command Refined
- Robust Interface Metadata Parsing
- Infographic Topology & Dual-View
- vPC & Enhanced Topology Mapping
- Topology & UX Overhaul

## [2.5.0] - 2026-02-26
### Changed
- Web Focused Enhancements

## [2.4.0] - 2026-02-26
### Added
- Code Audit & Documentation Release
- Created `QA_TESTING_CHECKLIST.txt` for manual testing
- Created `README.md` with architecture, features, and version history
### Removed
- Removed duplicate `import os` in web backend

## [2.3.0] - 2026-02-26
### Added
- Added Group dropdown filter to Web UI (parity with Desktop)
### Fixed
- Restored missing `connectivity`, `vlan_check`, `mac_check` in web thread router
- Fixed stale variable references (`enb`→`enb_pwd`, `d`→`data`) in web API handler
- Fixed `NameError: unique_nodes` in GUI topology mapper (should be `uniq_nodes`)
- Fixed web topology: `uniq_nodes` was overwritten with empty `set()` after population

## [2.2.0] - 2026-02-26
### Fixed
- Flask template routing for PyInstaller bundles (`sys._MEIPASS`)
- CSV audit now uses `conn.find_prompt()` for real hostname extraction
- Full regex parsing for OS Version, Serial Number, Model in web audit
- Topology mapper injects target node regardless of CDP/LLDP response

## [2.1.0] - 2026-02-25
### Changed
- Web UI Overhaul: MacOS-inspired glassmorphism design
- Complete feature parity: all 11 actions available in web edition
- Target Scope Engine with Bulk/Single/Group/Text filtering
- VLAN Compare, Interfaces tab, Config Backup added to web

## [2.0.0] - 2026-02-25
### Added
- Web Edition Created: Flask-based web application with HTML/JS frontend
- Separate PyInstaller build (`VlanCheckerWeb.exe`)
- Auto-launches browser on startup
- Session file logging

## [1.9.0] - 2026-02-08
### Added
- Topology Mapper with Vis.js interactive physics diagrams
- Network Audit exporting to CSV
- `safe_node_name()` for IP/hostname deduplication
- VLAN Compare Analysis with global baseline

## [1.8.0] - 2026-02-01
### Added
- VLAN Operations: Add/Rename/Delete VLAN with pre-check and confirmation dialogs
- Cisco config save and Juniper commit after changes
- Detailed per-device logging for all CRUD operations

## [1.7.0] - 2026-02-01
### Added
- Foundation: Connectivity & Authentication checker
- VLAN database audit with raw + parsed reports
- MAC Address tracer across network
- Group-based inventory filtering
- Enable Password support for Cisco IOS privilege escalation
- Thread-safe GUI with Queue-based logging
