# UI_UX_AUDIT

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | active |
| **Registry ID** | W-UI-UX |
| **Trigger** | `ui ux check` · `/ui-ux-audit` · `ui ux audit` |
| **Owner** | R-PROD + R-ENG + R-QA |
| **last_updated** | 2026-06-10 |

**Invoke:** Say **`ui ux check`** or paste this file.

---

## Mission

Holistic UI/UX audit for **offline desktop PC** use by **network engineers**. Professional, neat, tech-oriented, aligned — **no glitches**. Must work on **older displays** (1024×768, 1366×768). **No mobile** — do not optimize for phone; flag mobile-only patterns as defects.

---

## Roles (mandatory)

| Role | Focus |
|------|-------|
| R-PROD | Engineer workflows, time-to-task, clarity, simplicity |
| R-ENG | `index.html`, CSS, JS, tab logic, WebSocket CLI |
| R-QA | Visual regression, HTML contracts, broken tabs |
| R-ARCH | UI ↔ API contract, plugin form generation |
| R-LIB | Ops guides match UI labels |
| R-OBS | Error toasts, progress UX, log readability |
| R-SEC | Credential sidebar, no secret leakage in UI |
| R-COUNCIL | Synthesize priorities |

---

## Scope — audit every surface

| Surface | Path / check |
|---------|----------------|
| Main web UI | `modules/web/templates/index.html` |
| Tabs | Connectivity, Network Search, Discovery, Topology, Plugins, CLI, Health, Standards |
| Offline maps | `utils/discovery_map_shell.py`, `vpc_map_shell.py`, `topo_map_shell.py` |
| Command centers | Discovery + vPC offline HTML |
| vis.js | Bundled local — **no CDN** in offline EXE |
| Forms | Plugin dynamic forms, credential sidebar |
| Progress | MAC trace, discovery crawl, search-it badges |
| Typography | Readability at 1024px width |
| Dark/light | Consistency across tabs |
| Keyboard | Tab order, focus visible (PC) |

---

## PC / offline constraints (pass/fail)

| Rule | Pass when |
|------|-----------|
| Offline EXE | All assets from bundle; no broken external URLs |
| Min width 1024px | No horizontal scroll on primary tabs at 1024×768 |
| No mobile-first | No required touch gestures; no hidden-critical actions on “mobile menu” |
| Engineer speed | Core tasks ≤ 3 clicks from landing (connect → action) |
| Status clarity | Running/complete/error visible for long operations |
| Label alignment | Tab names match docs (`08-operations/` guides) |

---

## Execution sequence

### 1. Static review (R-ENG + R-PROD)

- Read `index.html` structure: tabs, IDs, duplicate init scripts
- Grep: `http://`, `https://`, `cdn.`, `unpkg` — flag externals
- Check vis.js load retry patterns (vPC, discovery maps)
- Interface map: ae bundles, member badges (v7.0.28+)

### 2. Contract tests (R-QA)

```bash
python -m pytest tests/test_discovery_map_html_contract.py tests/test_vpc_map_html_contract.py -q
python _prebuild.py
```

### 3. Heuristic checklist (R-PROD)

For each tab, answer:

- What is the engineer trying to do?
- Is the primary action obvious?
- Is feedback immediate?
- What fails silently today?

### 4. Council synthesis (R-COUNCIL)

Write `docs/14-bug-reports/03-team-contributions/ui-ux-audit-YYYY-MM-DD.md`:

| ID | Severity | Area | Issue | Fix prompt path |
|----|----------|------|-------|-----------------|
| UX-001 | … | Network Search | … | `02-bug-details/.../fix-prompt.md` or inline |

Generate **fix prompts** for Critical/High UX issues.

---

## Deliverables

| Artifact | Location |
|----------|----------|
| Audit report | `docs/14-bug-reports/W-UI-UX-AUDIT-YYYY-MM-DD.md` |
| Team contributions | `03-team-contributions/ui-ux-audit-*.md` |
| Prioritized UX backlog | Section in audit or `01-prioritized-bug-list.md` |
| Fix prompts | Per issue in `02-bug-details/UX-*` or BUG-* |
| Doc updates | `06-ui-ux/` notes if patterns change |

---

## Success criteria

- [ ] All tabs reviewed
- [ ] Offline/CDN rule verified
- [ ] 1024px layout considered
- [ ] HTML contract tests noted
- [ ] Council prioritized list with fix prompts
- [ ] No mobile-only recommendations unless explicitly rejected
