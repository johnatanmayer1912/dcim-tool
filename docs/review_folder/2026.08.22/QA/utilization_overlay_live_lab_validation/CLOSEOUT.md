# Utilization overlay — final closeout

Date: 2026-08-22  
Product: Network Swiss Tool Pro **7.0.97**  
Authority: latest live-lab validation + Phase 5 readiness register + named-lab kit

## Decision

**STOP.** No further utilization-overlay implementation prompt until retained live evidence exists from a signed named lab.

This closeout does not ship a VERSION bump, does not clear `release_gate`, and does not claim enterprise ready.

## Proven (not live-vendor)

| Item | Class |
|---|---|
| M1–M3 replay overlay on Standard L2 (join/paint/HTML) | fixture-only |
| M4 live overlay **contract** + mocked two-sample collector + CLI goldens | mocked rehearsal |
| M5 Discovery host as viewer (`live_controls=false`) | fixture-only |
| No SNMP collector; `utils.telemetry` does not import overlay | static / isolated freeze tests |
| Overlay jobs do not mint edges or mutate `trust_tier` | fixture/unit |
| Phase 5 `live_evidence_artifact` remains `null` | register (unchanged) |

## Not proven

- Live SSH two-sample collection against a signed named lab
- Vault `credential_id` resolve on a running console against lab devices
- Eligibility against a real Standard L2 bind table
- Live bps / percent / stale / cancel / degrade on real CLI
- Any retained `utilization_overlay.json` with `evidence_class=live_ssh` from devices
- Enterprise operational ready
- Live-vendor topology certification (utilization never certifies cables)

## Evidence classification

| Bucket | Path / artifact | Class |
|---|---|---|
| M1–M3 replay tests + HTML | `tests/test_utilization_overlay_*.py`, M1–M3 review folder | fixture-only |
| M4 live fixture JSON + mocked SSH tests | `tests/fixtures/utilization/live_standard_l2.json`, M4 `maps/*.html` | fixture-only / mocked rehearsal — **not a live poll** |
| M5 Discovery sample HTML | M5 review folder | fixture-only viewer |
| 2026-08-22 live-lab validation | `docs/review_folder/2026.08.22/QA/utilization_overlay_live_lab_validation/` | **non-evidence / prereq skip** (`mode=live_ssh_prereq_skip`) |
| Named lab signoff / matrix | `.cursor/docs/named-lab/LAB_SIGNOFF.md`, `LAB_DEVICE_MATRIX.md` | incomplete — **not evidence** |
| Placeholder `inventory.txt` TCP/22 | prereq probe | unreachable — **not retained live** |
| Retained live `utilization_overlay.json` | (absent) | **none** |

Fixture or mocked pytest **does not** count as live-vendor proof.

## Release gate

`tests/qa/PHASE5_DISCOVERY_READINESS.json`:

- `release_gate_when_not_ready`: **BLOCKED** (hard stop, not advisory)
- `enterprise_operational_ready`: **false**
- `live_vendor_truncated_cdp_lldp_validated`: **false**
- `evidence_paths.live_evidence_artifact`: **null**

Utilization live SSH is a **different evidence class** from truncated CDP/LLDP. Running (or failing to run) utilization does **not** clear this gate. This closeout does not re-label BLOCKED as conditional. **Not enterprise ready.**

## Required before any later live-SSH overlay prompt is valid

All of the following, human-owned:

1. Signed `.cursor/docs/named-lab/LAB_SIGNOFF.md`
2. Filled reachable rows in `.cursor/docs/named-lab/LAB_DEVICE_MATRIX.md`
3. Lab inventory files matching those rows (not placeholder `10.1.1.x` / `192.168.1.x` unless those hosts actually answer SSH)
4. Unlocked vault `credential_id` used for the run (secrets never in git/chat)
5. Operator console on `127.0.0.1:5051` if execute is started from Swiss Tools
6. Completed Inventory Standard L2 map (`map_mode=all`) with diag folder + `utilization_ssh_targets.json`
7. Retained live artifact: `utilization_overlay.json` with `mode=live`, `evidence_class=live_ssh`, `collector.kind=ssh_cli`, secrets-free, plus regenerated Standard L2 HTML whose edge set is unchanged

Until every item exists, do not generate another overlay implementation or live-lab validation prompt.

## Thread status

Closed. M1–M5 code remains as shipped. No collector expansion. No Discovery change. No replay change. No SNMP. No telemetry thaw. No new QA loop.
