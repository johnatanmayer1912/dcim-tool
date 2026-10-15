# Remaining gaps after P1 a11y (2026-08-24)

## Intentionally out of scope (user)

- SSO / RBAC / multi-user sessions
- Zero Trust identity items beyond the local operator console
- Plugin AST sandbox as a security boundary

## Axe incomplete (not a green certification)

- `aria-prohibited-attr` — 1–2 nodes on most workspaces (axe incomplete, not a violation). Hidden confirm dialogs still receive `aria-hidden` from JS when closed after open.
- `color-contrast` incomplete — 0–1 nodes on some pages (complex/hidden tab paint).

## Product / environment (unchanged)

| Item | Status |
|------|--------|
| `release_gate` | **BLOCKED** — needs live truncated CDP/LLDP evidence |
| WCAG / VPAT | Not claimed |
| Windows PE EXE E2E | Not run (Darwin) |
| Screen-reader pass | Not run |

## P2 leftovers (not this pass)

- `report_formatter.py` decorative gradients on some diagnostic HTML
- Enhanced L3 shell dark hero (if that shell is enabled)
- vis.js canvas is not a text alternative for the map graph (connection table + search remain the keyboard path)
