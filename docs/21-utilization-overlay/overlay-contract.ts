/**
 * NST utilization overlay v1 — draft types for map HTML/JS.
 * Authoritative validation: overlay-contract.schema.json
 * Paint is not topology. cable_key is topology_relation_key (kind=l2), never vis id e0.
 */
export type OverlayMode = 'replay' | 'live';
export type EvidenceClass = 'fixture' | 'replay_snapshot' | 'live_ssh';
export type PaintState =
  | 'ok'
  | 'warn'
  | 'hot'
  | 'partial'
  | 'stale'
  | 'no_sample'
  | 'no_speed'
  | 'invalid';
export type UnmappedReason =
  | 'no_matching_edge'
  | 'ambiguous_edges'
  | 'mgmt_or_l3_svi'
  | 'bundle_member_not_on_graph'
  | 'subinterface_no_parent_edge'
  | 'no_speed'
  | 'counter_invalid'
  | 'identity_mismatch'
  | 'not_paint_eligible_layer';

export interface UtilizationOverlayDocument {
  schema: 'nst.utilization_overlay.v1';
  mode: OverlayMode;
  evidence_class: EvidenceClass;
  topology_job_id?: string | null;
  topology_relation_keys_ref?: string | null;
  generated_at: string;
  stale_after_seconds?: number | null;
  degraded?: boolean;
  collector?: {
    kind: 'ssh_cli' | 'none';
    vendors?: Array<'cisco_ios' | 'cisco_xe' | 'cisco_nxos' | 'juniper_junos'>;
    delta_seconds_planned?: number | null;
  };
  paints: PaintRecord[];
  unmapped: UnmappedRecord[];
  summary: {
    l2_edge_count: number;
    painted_count: number;
    unmapped_count: number;
    partial_count?: number;
    stale_count?: number;
  };
}

export interface PaintRecord {
  cable_key: string;
  paint_state: PaintState;
  in_bps?: number | null;
  out_bps?: number | null;
  in_pct?: number | null;
  out_pct?: number | null;
  pct?: number | null;
  if_speed_bps?: number | null;
  pct_gt_100?: boolean;
  join: { status: 'mapped' | 'partial'; sides?: Array<'a' | 'b'> };
  provenance: {
    mode: OverlayMode;
    evidence_class: EvidenceClass;
    job_id?: string | null;
    commands?: string[];
  };
  freshness?: {
    sampled_at?: string | null;
    age_seconds?: number | null;
    stale?: boolean;
  };
}

export interface UnmappedRecord {
  device_id: string;
  if_name_raw: string;
  if_name_normalized?: string | null;
  reason: UnmappedReason;
  command?: string | null;
}
