# Cisco Asset & Warranty — Pilot Runbook

Network Swiss Tool Pro **7.3.0+**. Local operator console only (`127.0.0.1:5051` by default).

## Scope

Collect chassis/module serials, PID/VID, software version, and optional warranty enrichment for Cisco IOS, IOS-XE, NX-OS, and ACI APIC targets. Outputs consolidated HTML + CSV under `outputs/plugins/<date>/`.

## Prerequisites

1. Unlock the credential vault (Settings → Credentials).
2. Store at least one **SSH-capable** vault profile (`credential_id`).
3. For SNMP fallback, either:
   - SNMP fields on the same profile (`ssh_and_snmp`), or
   - A separate **SNMP-only** profile selected with **Use SNMP** in Settings.
4. Inventory lines: `IP,device_type[,group]` — supported types include `cisco_ios`, `cisco_xe`, `cisco_nxos`, `cisco_aci`.

## Operator steps (production pilot)

1. Start the web console: `python main.py web`
2. Settings → Credentials → **Use** (SSH profile) and optionally **Use SNMP** (SNMP profile).
3. Maps → Swiss Tools → **Cisco asset & warranty**
4. Parameters:
   - **Collection policy**: `ssh_first_snmp_fallback` (default) or `snmp_only` / `ssh_only`
   - **SNMP fallback**: enabled when policy allows
   - **Include modules**: slower; includes line-card inventory
5. Select inventory scope and run. Open the generated HTML report from the task log link.

## Offline QA lab (no live devices)

### In-process mock (fastest)

```bash
export NST_MOCK_ASSET_LAB=1
python main.py web
```

Use inventory file `tests/fixtures/asset/mock_lab_inventory.txt` (hosts `10.99.1.1`–`10.99.1.4`).

### TCP/UDP simulators (optional)

Terminal A — SSH sim (one device per port):

```bash
python lab/ssh_sim/server.py --port 2201 --device ios12
python lab/ssh_sim/server.py --port 2203 --device nxos7
```

Terminal B — SNMP sim:

```bash
python lab/snmp_sim/responder.py --port 1161 --community public-lab
```

Inventory example (custom port via group field is not supported — use standard SSH port mapping in netmiko device settings or mock lab):

| Host | Type | Notes |
|------|------|-------|
| `127.0.0.1` | `cisco_ios` | Point netmiko to port 2201 in lab harness only |

For automated pytest, prefer `NST_MOCK_ASSET_LAB=1` — no external services required.

## Security notes

- SNMP communities and v3 keys stay in the Fernet vault; API responses never echo secrets.
- `snmp_only` profiles cannot be used as primary `credential_id` on `/api/execute` (SSH tasks require SSH-capable profile).
- Binding beyond localhost expands blast radius — not recommended without additional controls.

## Rollback

1. Disable plugin runs from Swiss Tools.
2. Remove SNMP profiles from vault if no longer needed.
3. Revert to VERSION 7.2.x if collection regressions occur; mock lab env var is safe to unset.

## Success criteria (pilot)

- [ ] ≥1 IOS and ≥1 NX-OS device return serial + PID via SSH
- [ ] At least one SSH-failure path succeeds via SNMP fallback when separate SNMP profile is selected
- [ ] HTML report opens locally; CSV importable to asset tracker
- [ ] No secrets in `/api/logs`, browser DOM, or report HTML

## Known limitations

- Warranty API enrichment depends on external Cisco support APIs / credentials not bundled in NST.
- `release_gate` / Program Status **BLOCKED** is independent — asset collection does not certify topology readiness.
- Serial Number plugin remains SSH-only; dual SNMP applies to asset/warranty collection policy.
