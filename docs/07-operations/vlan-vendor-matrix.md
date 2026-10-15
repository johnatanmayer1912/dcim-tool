# VLAN operations — vendor matrix

| Field | Value |
|-------|-------|
| **Version** | v7.0.48+ |
| **Scope** | Web UI VLAN add / rename / delete / validate |
| **Owner** | NetOps / R-NET |

---

## Supported `device_type` values

| Platform | Inventory `device_type` | Show VLAN | Config apply | Persist |
|----------|----------------------|-----------|--------------|---------|
| Cisco IOS / IOS-XE | `cisco_ios`, `cisco_iosxe`, `cisco_xe` | `show vlan brief` | `send_config_set` | `write memory` |
| Cisco NX-OS | `cisco_nxos` | `show vlan` | `send_config_set` | `copy run start` |
| Cisco IOS-XR | `cisco_xr`, `ios_xr`, `iosxr` | `show vlan` | `send_config_set` + **commit** | commit (no wr mem) |
| Juniper Junos | `juniper_junos`, `junos` | `show vlans` | set/delete + **commit** | commit |

---

## IOS-XR specifics (G-006, v7.0.48)

1. Set inventory line: `10.0.0.1,cisco_xr,CoreRouters`
2. Validation pipeline accepts XR in `utils/vlan_validate.py` with platform note: commit-based VLAN.
3. Commands: `vlan <id>` + `name <name>` (same CLI shape as classic IOS VLAN config).
4. Changes are committed inside `_apply_vlan_config()` — do not expect `write memory`.
5. Post-check uses `show vlan` (not `show vlan brief`).
6. VLAN audit plugin uses the same `_vlan_show_cmd()` helper as production VLAN mgmt.

---

## Not supported on IOS-XR (by design)

- **Interface Manager** — use IOS/NX-OS/Junos only until G-015 Arista/XR IM work (IM fails closed on unknown types).
- **Juniper-style rename** — XR supports rename via `vlan <id>` / `name <new>` like IOS.

---

## Operator checklist (XR VLAN add)

1. Sidebar credentials + scope includes XR device with `device_type=cisco_xr`.
2. VLAN tab → Validate → confirm platform note mentions IOS-XR commit.
3. Dry-run if unsure → review command preview.
4. Live add → verify bucket shows **Changed+Verified** or **Verify failed** (honest status).
5. Pre-change backup path logged — manual restore only (no auto-rollback).

---

## Code references

| Module | Role |
|--------|------|
| `modules/vlan_mgmt_production.py` | `_is_ios_xr()`, add/rename/delete, commit apply |
| `utils/vlan_validate.py` | Pre-flight validation API |
| `modules/vlan_audit.py` | Audit show command via `_vlan_show_cmd` |
| `modules/network_base.py` | `parse_vlan_output()` Cisco-family parser |

See also: [backend-architecture.md](../01-architecture/backend-architecture.md) § VLAN Management.
