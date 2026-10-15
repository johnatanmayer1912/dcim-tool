# Phase 5 live-lab evidence attempts

**Closeout (2026-08-21):** The authorized live-lab attempt **failed** to produce PASS-eligible evidence. Files below are **attempt-only**. Register `live_evidence_artifact` remains **null**. See `reports/LIVE_LAB_EVIDENCE_FAILURE_CLOSEOUT_2026-08-21.md`.

| File | Mode | `live_vendor_validated` | Eligible for `evidence_paths.live_evidence_artifact`? |
|---|---|---|---|
| `phase5_live_lab_prereq_skip_2026-08-21.json` | `live_ssh_prereq_skip` | false | **No** — attempt-only |
| `phase5_live_ssh_probe_2026-08-21.json` | `live_ssh_not_executed` | false | **No** — attempt-only |

Wiring any of these into the register while `live_vendor_truncated_cdp_lldp_validated=false` **fails** the readiness checker (by design).

A PASS-eligible artifact requires `mode=live_ssh` and `live_vendor_validated=true` from reachable lab SSH with truncated CDP/LLDP contract held — no passwords in the file. **That artifact was not obtained.**
