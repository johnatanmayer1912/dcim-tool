# Fix log — reality-loop device-fidelity (7.0.97)

All samples below are **fixture/device-like**, not live captures.

## P0 — CDP brief Platform + Port ID single-space merge

**Symptom:** `show cdp neighbors` last columns `C9300-48P Gig 1/0/48` (one space) parsed remote_port as `C9300-48P Gig 1/0/48`. Brief vs detail could not share a cable key.

**Root cause:** Split on `\s{2,}` only. Cisco often leaves one space between Platform and Port ID.

**Fix:** `_cdp_brief_split_platform_port` peels a trailing interface token.

## P0 — Wrapped Device ID dropped

**Symptom:** Long Device ID on its own line + columns on the next line: first neighbor missing when continuation had <5 `\s{2,}` fields.

**Root cause:** Continuation with 4 fields cleared `pending_host` and was skipped.

**Fix:** If `pending_host` is set and the line starts with a CDP interface abbreviation, emit a neighbor. Hostname-only with no continuation still yields **no** neighbor (no invented ports).

## P0 — IOS 12.x `Local Interface` orphaned from Chassis id

**Symptom:** LLDP detail with Local Interface **before** Chassis id became `incomplete` (no local_port).

**Root cause:** Split only on `(?=Chassis id)` left Local Interface in the previous fragment.

**Fix:** `_split_cisco_lldp_detail_blocks` — dash rulers, or merge local-only + chassis-only fragments. NX-OS chassis-first still works.

## P1 — Spaced CDP abbreviations vs detail names

**Symptom:** `Gig 1/0/1` (brief) ≠ `Gi1/0/1` (detail finalize of GigabitEthernet1/0/1). Duplicate map edges.

**Fix:** `_normalize_interface_name` accepts spaced Gig/Fas/Ten/Eth/Po forms. Graph `_normalize_edge_port` uses the same helper (lazy import).

## P1 — NX-OS `mac ` prefix used as identity

**Symptom:** `Chassis id: mac 00:1A:2B:3C:4D:5E` with System Name not advertised could yield hostname `mac`.

**Fix:** Optional `mac ` prefix on Chassis/Port id; `_is_mac_like` after strip; hyphen MACs accepted.

## P1 — `Local Port id` stolen as remote Port id

**Fix:** Remote `Port id` must be at line start (`(?:^|\n)\s*Port id`), not the tail of `Local Port id`.

## P1 — Graph normalize must not import the SSH plugin

**Symptom:** Phase 4 telemetry freeze failed when `_normalize_edge_port` imported `network_discovery` (paramiko).

**Fix:** `utils/cisco_iface.py` — no SSH. Parsers and graph share it.


**Symptom:** 5 columns with Chassis MAC in column 1 treated as Parent Interface; chassis became `507` (Port ID).

**Fix:** If column 1 is MAC-like, treat as Chassis Id; prefer ifName over numeric SNMP Port ID for remote_port.
