# Utilization overlay — risks and non-goals

| Field | Value |
|-------|--------|
| **Contract** | [FEATURE_CONTRACT.md](FEATURE_CONTRACT.md) |
| **Date** | 2026-08-22 |

## Non-goals (v1)

| Item | Why |
|------|-----|
| SNMP / ifXTable / Shumoku poller | Product is SSH/CLI; `F-SNMP-01` deferred; UI already says no SNMP sample |
| NetFlow / sFlow / IPFIX | Different truth model (flows ≠ L2 edge load) |
| Painting L3 / EVPN / IRB as “hot cables” | Overlay/L3 are not physical in NST domain model |
| Using utilization to raise `trust_tier` | Busy ≠ verified |
| Extending frozen `utils.telemetry` | Phase 3/4 freeze; SNMP needle even banned on that package |
| Auto-creating LAG member edges from counters | Join law |
| Clearing Phase 5 `release_gate` because live counters ran | Different evidence class (`live_ssh` utilization ≠ truncated CDP/LLDP lab) |
| Historical 24h heatmaps / capacity planning | New product |
| Tk GUI | Web-only |

## Risks

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| U-JOIN-01 | Wrong ifName → wrong cable | High | Exact join; ambiguous → unmapped; tests |
| U-JOIN-02 | Po vs member confusion | High | No member→bundle paint |
| U-JOIN-03 | Device id ≠ map node id | High | Fail closed, no paint |
| U-UX-01 | Gray read as down | High | Banner + legend + panel copy |
| U-UX-02 | Replay read as live | High | Mode chip + `evidence_class` |
| U-UX-03 | Utilization color fights protocol color | Med | Overlay-on replaces stroke; overlay-off restores |
| U-COL-01 | 32-bit counter wrap | Med | Prefer 64-bit; `pct_gt_100` warning |
| U-COL-02 | ifSpeed 0 / auto | Med | `no_speed` unmapped or gray |
| U-COL-03 | SSH scale / CPU | Med | Scope to map nodes only; cancel |
| U-SEC-01 | Counter dumps in logs | Med | Truncate; no passwords |
| U-ZT-01 | Importing collector into graph pulls paramiko into telemetry tests | Med | Keep overlay package out of `discovery_graph` import cycle; paint applied at render |
| U-GATE-01 | Marketing “live validated maps” | High | Copy forbids; tests on Program Status unchanged |

## Freeze / honesty interactions

- Topology freshness `NST_STALE_HOURS = 24` in `topo_map_shell.py` is **not** the utilization stale window (live default 900s).
- Discovery overlay layer (NVE/EVPN) is a **different** “overlay.” Utilization UI must say **utilization overlay** in full in first-run banner.
- `docs/11-ux/demos/07-maps-utilization.html` is a **mock** (mentions SNMP snapshot). Shipping copy is **SSH** for live.

## Residual product limits

CDP/LLDP remain spoofable. Utilization on a spoofed edge still paints that **existing** edge; it does not prove the cable. Panel must keep spoof/one-sided L2 warnings visible under paint.
