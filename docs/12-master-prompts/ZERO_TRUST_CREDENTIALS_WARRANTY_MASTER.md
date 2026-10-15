# MASTER PROMPT — Credential Fallback + Asset Warranty Zero-Trust Validation

| Field | Value |
|-------|-------|
| **Version** | 2.0.0 |
| **Product** | Network Swiss Tool Pro |
| **Target build** | VERSION file (must match UI `/api/version`) |
| **Mindset** | Zero Trust — never trust logs alone; assert API payloads, vault resolution, SSH attempt order, report artifacts, and UI state |

## Mission

Prove end-to-end that:

1. **Multi-credential fallback** (Primary → Secondary → Third) works for Tools, Plugins, Discovery, Interface Manager, STP, Standards, Settings, and session restore.
2. **Cisco Asset & Warranty** reports are honest for Cisco devices and label **non-Cisco** (Juniper / other) as `not a cisco device` (never vague `unknown` for platform identity).
3. **Consolidated reports** merge multiple HTML + CSV files into non-empty mutual HTML **and** CSV with correct serials/PIDs.
4. **Mock SSH** simulates several vault users; Playwright drives GUI/Settings; API tests prove payloads; regex contracts lock report text.

## Non-negotiable gates (Zero Trust)

| Gate | Pass criteria |
|------|----------------|
| G1 API payload | Every execute/discovery/IM/STP/VLAN request that can SSH includes `credential_id` and, when selected, `secondary_credential_id` / `third_credential_id` |
| G2 Vault resolve | `resolve_execute_credentials` returns `fallback_credentials` length matching selected Secondary/Third |
| G3 SSH order | Mock/connect mocks: Primary fails → Secondary succeeds (or all fail with labeled attempts) |
| G4 Session | POST `/api/session/credentials` persists secondary/third IDs; GET restores without secrets |
| G5 UI Settings | Sidebar Primary/2nd/3rd dropdowns sync hidden fields; Use Primary/2nd/3rd buttons work |
| G6 Reports | Per-device HTML/CSV exist; non-Cisco rows use `not a cisco device` |
| G7 Consolidate | ≥2 HTML + ≥2 CSV → `total_devices > 0`, HTML+CSV outputs, serials present |
| G8 Secrets | Logs/API public views never emit plaintext passwords |
| G9 Version | UI and VERSION agree |

## Scenarios (must all pass)

### A — Credentials / Mock SSH
- A1 Primary only succeeds
- A2 Primary fails, Secondary succeeds
- A3 Primary+Secondary fail, Third succeeds
- A4 All fail — error surfaces; no silent success
- A5 Empty secondary/third — no spurious fallback attempts
- A6 Session reload restores credential IDs (not passwords)
- A7 Plugin execute + Tools `runAction` both send secondary/third
- A8 Discovery / IM / STP / VLAN payloads include secondary/third

### B — Asset Warranty reports
- B1 Cisco mock/lab asset → PID/serial populated; status not platform-unknown
- B2 `juniper_junos` / non-cisco device_type → report fields say `not a cisco device`
- B3 Multi-host mixed inventory → Cisco rows enriched; Juniper rows labeled honestly
- B4 Regex contract: `\bnot a cisco device\b` present; forbid platform labeled only as bare `unknown` for non-Cisco

### C — Consolidated Reports
- C1 Pretty HTML with newlines in `<td>` → devices extracted
- C2 Title-Case plugin CSV → devices extracted
- C3 Multi-file mix (2 CSV + 2 HTML) → mutual report non-empty; combined CSV on disk
- C4 Modal/script tables do not create fake devices
- C5 Dedupe by serial keeps richer row
- C6 API consolidate returns `output_csv` + `summary.total_devices`

### D — Playwright GUI
- D1 Unlock/use vault credentials; set Primary/Secondary/Third in Settings sidebar
- D2 Intercept `/api/execute` and assert JSON body IDs
- D3 Open Reports workspace; list input files; consolidate; assert status shows device count + CSV
- D4 Credential buttons Use Primary / Use 2nd / Use 3rd update hidden fields
- D5 After session POST, reload page → dropdowns restore

## Execution order

1. Implement/fix non-Cisco report labeling + any gaps found
2. Unit + mock-SSH pytest (A, B)
3. Consolidator zero-trust pytest (C)
4. Playwright extensive scenarios (D)
5. Fail-fix any gate; re-run full matrix
6. Bump VERSION / spec only if product code changed

## Forbidden shortcuts

- Trusting log substring `"Has fallback_credentials: True"` without asserting SSH attempt order
- Consolidator “success” with `total_devices == 0`
- Marking Juniper/other as warranty `unknown` when the real issue is **platform not Cisco**
- Skipping Playwright because API unit tests passed
