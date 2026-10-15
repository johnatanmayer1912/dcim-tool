"""L2 utilization overlay — paint existing Standard L2 edges only.

Replay/fixture and bounded live SSH (two samples). Never mutates topology,
trust_tier, or release_gate. Not SNMP. Do not import this package from
utils.telemetry (Phase 3/4 freeze).
"""
from utils.utilization_overlay.join import (
    OverlayBindResult,
    bind_overlay_to_standard_l2,
    bind_replay_to_standard_l2,
    join_observations_to_l2,
    l2_cable_key,
    topology_fingerprint,
)
from utils.utilization_overlay.discovery_host import (
    bind_overlay_to_discovery,
    discovery_embed_payload,
)
from utils.utilization_overlay.model import (
    OverlayValidationError,
    load_overlay_document,
    load_replay_overlay,
    resolve_replay_overlay_source,
    validate_overlay_document,
)
from utils.utilization_overlay.paint import stroke_for_paint, ui_paint_view

__all__ = [
    'OverlayBindResult',
    'OverlayValidationError',
    'bind_overlay_to_discovery',
    'bind_overlay_to_standard_l2',
    'bind_replay_to_standard_l2',
    'discovery_embed_payload',
    'join_observations_to_l2',
    'l2_cable_key',
    'load_overlay_document',
    'load_replay_overlay',
    'resolve_replay_overlay_source',
    'stroke_for_paint',
    'topology_fingerprint',
    'ui_paint_view',
    'validate_overlay_document',
]
