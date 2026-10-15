"""Two-sample counter math for live utilization. No smoothing, no invention."""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

COUNTER_32 = 2 ** 32
COUNTER_64 = 2 ** 64
# If a wrap-corrected delta implies more than 2x ifSpeed, treat as reset/invalid.
HEADROOM = 2.0


def clamp_delta_seconds(value: Any, default: float = 10.0) -> float:
    try:
        dt = float(value)
    except (TypeError, ValueError):
        dt = default
    if dt < 5.0:
        return 5.0
    if dt > 60.0:
        return 60.0
    return dt


def _as_int(value: Any) -> Optional[int]:
    if value is None or value is False:
        return None
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    if n < 0:
        return None
    return n


def prefer_octets(sample: Dict[str, Any], direction: str) -> Tuple[Optional[int], str]:
    """Prefer 64-bit counter fields when present."""
    if direction not in ('in', 'out'):
        return None, 'invalid'
    key64 = f'{direction}_octets_64'
    key = f'{direction}_octets'
    v64 = _as_int(sample.get(key64))
    if v64 is not None:
        return v64, '64'
    v = _as_int(sample.get(key))
    if v is not None:
        width = '64' if v >= COUNTER_32 else str(sample.get('counter_width') or '64')
        return v, width
    return None, 'missing'


def delta_octets(t0: Optional[int], t1: Optional[int], width: str) -> Tuple[Optional[int], Optional[str]]:
    """Return (delta, error_reason). error_reason set when the delta is not usable."""
    if t0 is None or t1 is None:
        return None, 'counter_invalid'
    if t1 >= t0:
        return t1 - t0, None
    # Negative: try wrap, else reset
    for modulus in (COUNTER_32, COUNTER_64):
        if width == '32' and modulus == COUNTER_64:
            continue
        wrapped = t1 + modulus - t0
        if wrapped >= 0:
            return wrapped, None
    return None, 'counter_invalid'


def compute_bps(delta: Optional[int], dt_seconds: float) -> Optional[float]:
    if delta is None or dt_seconds is None:
        return None
    try:
        dt = float(dt_seconds)
    except (TypeError, ValueError):
        return None
    if dt <= 0:
        return None
    return (float(delta) * 8.0) / dt


def compute_pct(bps: Optional[float], if_speed_bps: Optional[float]) -> Optional[float]:
    if bps is None:
        return None
    try:
        speed = float(if_speed_bps) if if_speed_bps is not None else 0.0
    except (TypeError, ValueError):
        return None
    if speed <= 0:
        return None
    return (float(bps) / speed) * 100.0


def rate_implausible(bps: Optional[float], if_speed_bps: Optional[float]) -> bool:
    if bps is None:
        return False
    try:
        speed = float(if_speed_bps) if if_speed_bps is not None else 0.0
    except (TypeError, ValueError):
        return False
    if speed <= 0:
        return False
    return float(bps) > speed * HEADROOM


def pair_interface_samples(
    t0: Dict[str, Any],
    t1: Dict[str, Any],
    dt_seconds: float,
) -> Dict[str, Any]:
    """Build one observation from two counter snapshots. Never guesses rates."""
    in0, in_w = prefer_octets(t0, 'in')
    in1, _ = prefer_octets(t1, 'in')
    out0, out_w = prefer_octets(t0, 'out')
    out1, _ = prefer_octets(t1, 'out')
    din, in_err = delta_octets(in0, in1, in_w)
    dout, out_err = delta_octets(out0, out1, out_w)
    speed = t1.get('if_speed_bps')
    if speed is None:
        speed = t0.get('if_speed_bps')
    try:
        speed_f = float(speed) if speed is not None else None
        if speed_f is not None and speed_f <= 0:
            speed_f = None
    except (TypeError, ValueError):
        speed_f = None

    in_bps = compute_bps(din, dt_seconds) if not in_err else None
    out_bps = compute_bps(dout, dt_seconds) if not out_err else None
    if rate_implausible(in_bps, speed_f) or rate_implausible(out_bps, speed_f):
        return {
            'ok': False,
            'reason': 'counter_invalid',
            'in_bps': None,
            'out_bps': None,
            'in_pct': None,
            'out_pct': None,
            'pct': None,
            'if_speed_bps': speed_f,
            'pct_gt_100': False,
        }
    if in_err and out_err:
        return {
            'ok': False,
            'reason': 'counter_invalid',
            'in_bps': None,
            'out_bps': None,
            'in_pct': None,
            'out_pct': None,
            'pct': None,
            'if_speed_bps': speed_f,
            'pct_gt_100': False,
        }
    in_pct = compute_pct(in_bps, speed_f)
    out_pct = compute_pct(out_bps, speed_f)
    pcts = [p for p in (in_pct, out_pct) if p is not None]
    pct = max(pcts) if pcts else None
    pct_gt_100 = bool(pct is not None and pct > 100.0)
    if speed_f is None and in_bps is None and out_bps is None:
        return {
            'ok': False,
            'reason': 'no_speed' if speed_f is None else 'counter_invalid',
            'in_bps': in_bps,
            'out_bps': out_bps,
            'in_pct': None,
            'out_pct': None,
            'pct': None,
            'if_speed_bps': speed_f,
            'pct_gt_100': False,
        }
    return {
        'ok': True,
        'reason': None if (in_bps is not None or out_bps is not None) else 'counter_invalid',
        'in_bps': in_bps,
        'out_bps': out_bps,
        'in_pct': in_pct,
        'out_pct': out_pct,
        'pct': pct,
        'if_speed_bps': speed_f,
        'pct_gt_100': pct_gt_100,
    }
