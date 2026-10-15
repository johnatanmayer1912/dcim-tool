# Usability and accessibility report

**VERSION:** 7.2.2 · **Date:** 2026-08-23

## Operator usability (NOC lens)

| Question | Verdict | Evidence |
|---|---|---|
| Is the next action obvious? | **Mostly yes** | Inventory: Preview→Commit; Maps: run then inspect HTML; Change: dry-run then mutate; IM: enter single host |
| Are errors understandable? | **Yes for covered Playwright paths** | Missing credential_id, live SSH without map, inventory DNS reject |
| Are outputs easy to inspect? | **Yes** | Evidence jobs; map Connection Index; export JSON under `generated_outputs/` |
| Does it feel shippable into ops infra? | **Conditionally** | As loopback operator EXE/console — yes. As enterprise multi-user service — no |

## Accessibility (partial — not full axe)

| Check | Result |
|---|---|
| Playwright: Connect / credential selector accessible names | PASS (`cli_credential_id.spec.mjs`) |
| Playwright: visible focus on primary Connect | PASS |
| Keyboard focus credential selector | PASS |
| Full axe-core / WCAG AA automated sweep | **NOT RUN** this pass |
| Color-only status in tables | Residual risk — Status text present on inventory (accept/warn/reject) |
| Map dark UI contrast | Generally high; banner red on black is strong (good for HARD STOP) |
| Emoji in VLAN validation header | Low a11y noise |

## Usability defects remaining

1. Chrome meta density on small screens (Medium)  
2. Full keyboard map for every Change sub-tab not exhaustively proven (Low residual)  
3. Client-side parsed-hosts Status remains a hint; server Preview is authoritative (documented trust note)  

## Verdict

**Usability: PASS for trained network operators on localhost.**  
**Accessibility: PARTIAL PASS** — targeted Playwright a11y checks green; full enterprise a11y certification not claimed.
