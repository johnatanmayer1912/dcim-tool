"""Shared enterprise theme for offline map HTML shells (v7.4.22).

All map shells (L2 / L3 / vPC / discovery / topo) should prepend
``enterprise_map_css()`` so chrome, type, and accents stay consistent —
graphite + system blue, SF Pro stack, no purple brand gradients.
"""
from __future__ import annotations


def enterprise_map_css() -> str:
    return """
/* NST map shell theme v7.4.22 */
:root {
  --nst-map-bg0: #0b0b0d;
  --nst-map-bg1: #161618;
  --nst-map-bg2: #1c1c1e;
  --nst-map-bg3: #2c2c2e;
  --nst-map-tx1: #f5f5f7;
  --nst-map-tx2: #a1a1a6;
  --nst-map-tx3: #8e8e93;
  --nst-map-bdr: rgba(255,255,255,0.08);
  --nst-map-acc: #0a84ff;
  --nst-map-acc2: #64d2ff;
  --nst-map-ok: #30d158;
  --nst-map-warn: #ffd60a;
  --nst-map-danger: #ff453a;
  --nst-map-font: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Helvetica Neue", system-ui, sans-serif;
  --nst-map-mono: "SF Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
body.nst-map-enterprise,
body.l3-routing-map,
body.nst-standard-map,
body.vpc-command-center,
body.discovery-map,
body.topo-map {
  font-family: var(--nst-map-font) !important;
  -webkit-font-smoothing: antialiased;
  letter-spacing: -0.01em;
}
.nst-map-brand-mark {
  width: 32px; height: 32px;
  border-radius: 10px;
  background: linear-gradient(145deg, #0a84ff 0%, #0040dd 100%);
  box-shadow: 0 4px 14px rgba(10, 132, 255, 0.35);
  display: inline-flex; align-items: center; justify-content: center;
  color: #fff; font-size: 11px; font-weight: 700; letter-spacing: 0.04em;
}
.nst-map-toolbar button,
.l3-toolbar button,
.topo-toolbar button,
.vpc-map-toolbar button {
  border-radius: 10px !important;
  font-family: var(--nst-map-font) !important;
  font-weight: 600 !important;
  transition: background 160ms ease, border-color 160ms ease, color 160ms ease;
}
.nst-map-toolbar button:hover,
.l3-toolbar button:hover,
.topo-toolbar button:hover,
.vpc-map-toolbar button:hover {
  border-color: rgba(10, 132, 255, 0.55) !important;
}
.nst-map-honesty,
.overlay-honesty {
  font-size: 11px !important;
  color: var(--nst-map-tx3) !important;
  line-height: 1.4 !important;
}
"""


def brand_mark_html(label: str = "NST") -> str:
    safe = (label or "NST")[:4]
    return f'<span class="nst-map-brand-mark" aria-hidden="true">{safe}</span>'
