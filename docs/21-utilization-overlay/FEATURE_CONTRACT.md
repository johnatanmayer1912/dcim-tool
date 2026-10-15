# L2 utilization overlay — canonical feature contract

| Field | Value |
|-------|--------|
| **ID** | NST-UTIL-OVERLAY-v1 |
| **Status** | Authoritative spec — M1–M5 implemented in product code (Standard L2 replay + live SSH collector + Discovery viewer). Live SSH is **not** live-lab proven. `release_gate` stays BLOCKED. |
| **Date** | 2026-08-23 |
| **App VERSION at authoring** | 7.0.99 |
| **Cite this file** | Future implementation prompts must treat this as product law |

---

## 1. What this feature is

A **paint overlay** on an existing Layer-2 topology graph. Utilization is computed from interface counters (replay snapshot or live SSH) and applied **only** to edges that already exist in the map’s L2 dataset.

One graph. One topology. Two operating modes (`replay` | `live`) sharing one renderer and one join layer.

## 2. What this feature is not

- Not a second topology.
- Not cable certification, LACP proof, or a trust-tier upgrade.
- Not SNMP / ifXTable / Shumoku NMS polling (explicitly out of product law for this slice; live = SSH).
- Not overlay/EVPN/NVE paint (those edges are already “not cables”).
- Not Phase 3/4 `utils.telemetry` (that API is frozen; this is a new package).
- Not a path, forwarding, QoS, or “hot potato” traffic-engineering view.
- Not a down/up interface status map (gray ≠ down).

## 3. Graph invariants

1. **Topology source of truth** is the L2 edge list already produced by the map job (`from`, `to`, `f_port`, `t_port`, plus existing trust/evidence fields).
2. Overlay **may not** insert, delete, split, merge, or reclassify edges or nodes.
3. Overlay **may not** change `trust_tier`, `confidence`, `one_sided`, `not_physical`, `layer`, or `sources[]`.
4. Incomplete observations (`edge_eligible=false`) remain non-edges. Counters must not promote them.
5. Unmapped counter rows stay in `unmapped[]`. They never become vis.js edges.
6. Paint is a **property of an existing edge id/key**, not a new relation type.

## 4. Trust and source-of-truth boundaries

| Concern | Authority | Overlay role |
|---------|-----------|--------------|
| Who is linked to whom | CDP/LLDP (+ inventory Standard Map finalize) | Read-only |
| Cable / spoof honesty | `utils/topology_trust.py` | Must not upgrade “High” to Verified because a port is busy |
| Port name identity | `utils/cisco_iface.py`, `utils/juniper_iface.py`, graph `_normalize_edge_port` | Join uses the same normalize |
| Utilization numbers | Overlay document (`nst.utilization_overlay.v1`) | Only after join |
| Program Status / live-vendor gate | Phase 5 register | Overlay jobs do **not** clear `release_gate` |

**Paint-eligible edges (decision):** L2 vis edges where `not_physical` is false, `layer` is not `overlay`, protocol is not EVPN/OSPF/BGP/ISIS, and both endpoint hosts exist. One-sided L2 edges **may** receive **partial** paint (one endpoint sampled). Inferred/synthetic edges that **already exist** on the map (e.g. vPC peer-link finalize in `adapters._finalize_standard_map_edges`) may be painted; overlay still cannot create them.

**Not paint-eligible:** overlay/EVPN, IRB/L3 SVI, STP-blocked as “utilization of a forwarding path,” incomplete observations, edges missing both ports.

## 5. Operator-facing truth statements (must appear in UI)

Use this wording or a strict paraphrase:

- **Banner:** `Utilization paints existing L2 links only. It is not topology. Gray dashed = no sample — not down. Overlay never creates cables.`
- **Mode replay:** `Replay snapshot — not a live poll.`
- **Mode live:** `Live SSH counters — not SNMP.`
- **Stale:** `STALE — last sample older than policy. Colors kept; do not treat as current load.`
- **Partial:** `One side sampled — not a full duplex measurement.`
- **Unmapped table title:** `Unmapped interfaces (not drawn)`
- **Panel “must not imply”:** `Not a forwarding path, QoS class, or cable certification. Gray edges are not down.`

## 6. Anti-misinterpretation rules

| Operator might think | Product must show |
|---------------------|-------------------|
| Gray = down | Gray = no sample / no ifSpeed / not joined |
| Red = link failure | Red = % of ifSpeed above 90% on a **mapped** edge |
| Overlay found a new neighbor | Unmapped table + zero new vis edges |
| Replay is live | Mode chip + `evidence_class` |
| Busy port = verified cable | Trust pills unchanged |
| Member counter = Po cable | Exact ifName join only (see join) |

## 7. Never-do rules

1. Never mint vis edges from ifName, ifIndex, or hostname-only matches.
2. Never use SNMP in v1 live (SSH only). Do not add a silent SNMP fallback.
3. Never write utilization into `utils.telemetry` public API.
4. Never treat missing overlay document as “all links idle at 0%.”
5. Never hide L2 edges when overlay is on and unsampled.
6. Never join `mgmt0` / `irb.*` / `Vlan*` SVI counters onto physical cables.
7. Never use array index as edge identity (`e0`, `e1` in vis is display-only). Join via `topology_relation_key` / undirected cable key.
8. Never log passwords, community strings, or full `show running-config`.
9. Never claim live-vendor utilization validation because replay fixtures passed.

## 8. UX model

### 8.1 Host surface (decision)

**Slice 1 host:** Inventory Standard L2 (`map_mode=all`) — `utils/standard_map_shell.py` + `utils/report_formatter.py` `generate_topology_html()`, launched from Swiss Tools **Map all** (`#btn-map-all`).

**Slice 2 host:** Discovery Command Center (`utils/discovery_map_shell.py`) using the same overlay JSON + join. Do not fork visuals.

**Out of slice 1:** L3 maps, vPC board, STP-only maps, overlay/EVPN layer.

### 8.2 Overlay off

Unchanged current L2 coloring (protocol/trust/one-sided dashes as today). No utilization legend. Freshness line keeps `SNMP: no sample this release` **until** overlay ships; then replace with overlay status (see copy).

### 8.3 Overlay on

- Checkbox/toggle: `Utilization overlay`
- Mode control: `Replay` | `Live SSH` (disabled Live until collector ships)
- Legend (fixed): no sample / &lt;70% / 70–90% / &gt;90%
- Existing L2 edges remain; sampled ones change **stroke color and width only**
- Unsampled stay **gray dashed**, width 2 — still clickable as L2

### 8.4 Color and width (decision — matches demo 07)

| `paint_state` | Stroke | Width | Dash |
|---------------|--------|-------|------|
| `no_sample` / `unmapped_endpoint` / overlay off for that edge | `#64748b` | 2 | `5 4` |
| `ok` (`pct` &lt; 70) | `#22c55e` | 3 | solid |
| `warn` (70–90 inclusive of 70, exclusive of 90 at upper bound: `70 ≤ pct < 90`) | `#eab308` | 3 | solid |
| `hot` (`pct ≥ 90`) | `#ef4444` | 4 | solid |
| `stale` + had a pct | keep last color | keep last width | solid; **STALE** in title + banner |
| `partial` | color by available pct | 3 | `4 3` (distinct from no-sample gray dash) |
| `invalid` / `no_speed` | `#64748b` | 2 | `5 4` | listed in unmapped or panel reason |

`pct` for color = `max(in_pct, out_pct)` when both exist.

**Stale + overlay on:** keep paint, do not gray-out the whole map (demo “stale poll” behavior). Banner must include STALE.

### 8.5 Click / inspector

Selecting an edge shows **existing** L2 identity (hosts, ports, protocol, trust) **plus** utilization block:

- Mode, evidence_class, job id
- in/out bps and % of ifSpeed
- ifSpeed / oper_speed
- sample timestamps and age
- join_confidence (`mapped` \| `partial` \| `ambiguous` — ambiguous never paints)
- Must-not-imply sentence

If no overlay sample: `No utilization sample for this link.` + L2 fields unchanged.

### 8.6 Freshness line (Maps hub + map HTML)

Pattern: `Last L2: {l2_age} · Overlay: {mode} {overlay_age_or_none} · sampled {n}/{total} L2 edges`

Examples:

- `Last L2: 14m · Overlay: replay 8m (3/9 edges sampled) — not live`
- `Last L2: 14m · Overlay: live SSH 2m (3/9) · STALE policy 15m`
- `Last L2: 14m · Overlay: none — topology unchanged`

### 8.7 Empty / degraded

| State | UX |
|-------|-----|
| No overlay document | Overlay toggle off or on-with-all-gray; banner `No utilization document loaded` |
| Overlay on, 0 mapped | All L2 gray dash; unmapped table may be full; not an error if collector ran |
| Live poll cancel | Partial document allowed; `degraded: true`; do not invent remaining samples |
| Join file device_ids ≠ map node ids | Load fails closed: no paint; error `device identity mismatch — refusing to paint` |
| Parse failure per interface | that row unmapped; rest of job continues |

### 8.8 Unmapped table

Columns: Host (map id), ifName (raw), ifName_normalized, reason code, collector command (no secrets).

Reasons (closed set): `no_matching_edge`, `ambiguous_edges`, `mgmt_or_l3_svi`, `bundle_member_not_on_graph`, `subinterface_no_parent_edge`, `no_speed`, `counter_invalid`, `identity_mismatch`, `not_paint_eligible_layer`.

## 9. Canonical data contract

See also `overlay-contract.schema.json`.

### 9.1 Document

Top-level overlay document (one per map job or explicit load):

| Field | Semantics |
|-------|-----------|
| `schema` | `nst.utilization_overlay.v1` |
| `mode` | `replay` \| `live` |
| `evidence_class` | `fixture` \| `replay_snapshot` \| `live_ssh` |
| `topology_job_id` | Map/crawl job this overlay binds to (required for live; required for replay when painting a generated HTML) |
| `topology_relation_keys_ref` | Optional hash/count of L2 keys at bind time |
| `generated_at` | ISO-8601 UTC |
| `collector` | `{kind: "ssh_cli", vendors: [...]}` |
| `stale_after_seconds` | Live default **900**; replay uses `null` (no live-stale) but still shows snapshot age |
| `degraded` | bool |
| `paints[]` | 0..n paint records keyed to existing L2 |
| `unmapped[]` | 0..n |
| `summary` | counts only |

**Honesty:** `mode=live` requires `evidence_class=live_ssh`. `mode=replay` forbids `evidence_class=live_ssh`.

### 9.2 Edge identity (join key)

Reuse undirected identity already in code:

- Graph: `utils.discovery_graph._undirected_cable_key` → `(host_a, port_a, host_b, port_b)` lowercased, ports via `normalize_cisco_iface` / Junos helpers.
- Maps: `utils.evidence_inspector.topology_relation_key` → `host_a|port_a|host_b|port_b|kind` with `kind=l2`.

**Overlay `cable_key` (decision):** `topology_relation_key` with `kind=l2` (or empty kind coerced to l2). Vis `id` (`e0`) is **not** a join key.

### 9.3 Sample (pre-join)

One observation per device interface per poll:

- `device_id` (must equal map node `id`)
- `if_name_raw`, `if_name_normalized`
- `octets_in`, `octets_out` (64-bit if present)
- `if_speed_bps` (operational if known, else configured)
- `sample_ts` ISO-8601
- `command` (e.g. `show interfaces`)
- `vendor` / `device_type`

Two samples (`t0`, `t1`) required to compute bps. Single sample ⇒ `counter_invalid` / unmapped, never 0%.

### 9.4 Paint record (post-join)

- `cable_key`
- `paint_state`
- `in_bps`, `out_bps`, `in_pct`, `out_pct`, `pct` (max)
- `if_speed_bps`
- `join`: `{status, sides: ["a"|"b"|...], t0, t1}`
- `provenance`: mode, evidence_class, job_id, commands
- `freshness`: `{sampled_at, age_seconds, stale}`

### 9.5 Computed UI fields

Renderer must not recompute topology. It may compute `stale` from `sampled_at` + policy. It must not infer pct from a single counter.

### 9.6 Validation rules

- Reject document if any `paints[].cable_key` is absent from bound L2 key set.
- Reject `live_ssh` without two sample timestamps per painted edge (partial allowed only with `paint_state=partial` and `degraded`).
- `pct` outside 0–100+headroom: clamp display at 100 for color `hot`, keep raw in panel; do not create edges.
- Empty `paints` is valid.

## 10. Join strategy

### 10.1 Inputs

| Input | Source |
|-------|--------|
| L2 keys | Map edges after canonicalize / Standard Map finalize |
| Counter rows | Replay JSON or live parser |
| Normalize | `normalize_cisco_iface`, `split_junos_unit` / `is_junos_irb_or_l3_svi` |

### 10.2 Stages (strict order)

1. **Drop L3/mgmt:** `mgmt0`, `irb.*`, `vlan.*` L3, `Vlan*` SVI, `lo*`, `Loopback*` → unmapped `mgmt_or_l3_svi`.
2. **Normalize ifName** on the collector row.
3. **Index L2 endpoints:** map `(device_id.lower(), port_normalized.lower())` → list of `cable_key`.
4. **Exact join:** row `(device, ifName_norm)` → endpoint index.
5. **Junos unit fallback:** if no hit, try physical base (`ge-0/0/0.0` → `ge-0/0/0`) **only if** exactly one L2 edge endpoint matches that device+base.
6. **Cisco subinterface:** no parent fallback in v1 (unmapped `subinterface_no_parent_edge`) — too easy to paint a bundle/SVI wrongly.
7. **Ambiguity:** 2+ distinct `cable_key` for the same endpoint → unmapped `ambiguous_edges` (do not pick).
8. **Bundle members:** `Gi1/0/1` does **not** paint `Po10` even if LACP says membership. `Po10` paints `Po10` edge only. Member without member-edge on graph → unmapped `bundle_member_not_on_graph`.
9. **One side only:** if exactly one endpoint of a cable_key is sampled, `paint_state=partial`; still no new edge.
10. **No hit:** `no_matching_edge`.

### 10.3 Confidence

| Join status | Paint? |
|-------------|--------|
| `mapped` (both sides or unique one-side on a one-sided L2 edge) | Yes |
| `partial` (one of two sides on a bidirectional L2 edge) | Yes, dashed partial |
| `ambiguous` | No |
| `unmapped` | No |

Hostname-only (ignore port) is **forbidden**. IP-only join is **forbidden**. ifIndex-only without ifName map is **forbidden** in v1 (SSH parsers emit names).

### 10.4 Why join never creates topology

Join is a **lookup** into a frozen key set copied from the map at bind time. Inserting a key is a spec violation and must fail tests that count vis edges before vs after overlay apply.

## 11. Mode strategy

### 11.1 Replay / static (MVP)

**Artifact:** JSON file matching `overlay-contract.schema.json` (or a `samples[]` + join run that **emits** that document). Fixtures live under `tests/fixtures/utilization/` labeled `evidence_class: fixture`.

**Bind:** Operator (or test) selects overlay JSON + existing map HTML/job. Device ids in samples must match map node ids.

**Labeling:** UI chip `Replay` + banner not-live. File metadata `mode=replay`.

**Minimum first release:** Join + paint on Standard L2 HTML (or equivalent vis payload) from fixture; no SSH.

### 11.2 Live (later slice)

**Collector abstraction:** `UtilizationCollector.collect(device, creds, t0_wait) -> InterfaceSamplePair` via existing Netmiko path (`modules/network_base.py`). No new bind address. Localhost + vault unlock same as other mutating/sensitive jobs (`utils/api_security.py`).

**Lifecycle:** Job on control plane → SSH each in-scope inventory device that appears as a map node → sample t0 → wait Δt (default 10s, min 5s, max 60s) → sample t1 → parse → join → write overlay JSON beside map outputs (`utils/output_paths.py`) → optional regenerate HTML **without** changing edge set.

**Rate:** `(Δoctets * 8) / Δt / if_speed_bps`. Missing Δt or Δoctets reset → unmapped.

**ifSpeed:** operational speed from CLI if present; else configured BW; else `no_speed`.

**Timeouts:** per-device timeout; skip device; `degraded=true`; do not paint guessed values.

**Cancel:** stop SSH; emit partial overlay; topology unchanged.

**Suggested commands (adapter-owned; fixtures required):**

| `device_type` | Command intent |
|---------------|----------------|
| `cisco_ios`, `cisco_xe` | Counters + speed (`show interfaces` / status) |
| `cisco_nxos` | `show interface counters` + `show interface status` |
| `juniper_junos` | Interface statistics / extensive subset |

Exact regexes are **not** frozen in this spec; they are an implementation deliverable with golden CLI fixtures (old + new majors), same as discovery parsers.

**Security:** reuse vault `credential_id`; no SNMP community; do not log full interface dumps in `/api/logs`.

## 12. Package and freeze

New code: `utils/utilization_overlay/` (`join.py`, `model.py`, `paint.py`, later `ssh_collector.py`).

**Forbidden:** adding symbols to `utils.telemetry.__all__`; SNMP libraries; creating edges in `canonicalize_discovery_graph`.

## 13. Open decisions (repo does not settle)

1. Exact IOS/XE/NX-OS/Junos command strings and parser regexes — require fixtures.
2. Whether Discovery Command Center ships in the same VERSION as Standard L2 or the next.
3. Δt default 10s vs operator-configurable in v1 (recommendation: fixed 10s in v1, no extra UI).
4. Whether `pct > 100` (counter wrap or speed mismatch) is `hot` or `invalid` (recommendation: `hot` + panel warning `pct_gt_100`).

Everything else in this file is **decided**.
