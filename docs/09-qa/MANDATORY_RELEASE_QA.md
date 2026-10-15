# Mandatory Release QA Workflow

Network Swiss Tool Pro ships only after **mandatory QA phases** pass. The manifest is the single source of truth: `tests/qa/MANDATORY_MANIFEST.yaml`.

## Phases

| Phase | When | Command | Blocking |
|-------|------|---------|----------|
| **every_code_change** | After any product code edit | `python scripts/mandatory_release_qa.py --phase every_code_change` | prebuild + manifest validate |
| **pre_release** | Before VERSION bump / EXE | `python scripts/mandatory_release_qa.py --phase pre_release` | core pytest + frozen sim + CLI browser QA |
| **all** | Full gate | `python scripts/mandatory_release_qa.py --phase all` | both phases |
| **scaffold full** | Implementing `tests/qa/` bodies | `set NST_MANDATORY_QA_FULL=1` then `pre_release` | scaffold tests execute |

## Persona ownership

Each suite in the manifest has an **owner** persona (see manifest `personas:`). Before release, mentally sign off per seat:

- **network_engineer_council** — vendor CLI, mutations, maps
- **product_architect** — one control plane, outputs, plugins
- **software_engineer** — API contracts, threading, errors
- **noc_operator** — operator workflows, progress, reports folder
- **product_simplicity** — delete steps, obvious primary path (Steve Jobs lens)
- **ui_ux_professional** — tables, highlights, HTML contracts

## Council (code-only, not pytest)

Before **major** releases, run **nst-network-engineer-council**:

1. Work through `.cursor/skills/nst-network-engineer-council/QUESTIONNAIRE.md`
2. Write `.cursor/audits/TEAM_VALIDATION_REGISTER_<date>.md`
3. Feed P0/P1 gaps into `nst-gap-remediation-workflow`

Complement with **nst-zero-trust-network-council** → `GAP_REGISTER_*.md` when time allows.

## Integration points

| Entry | Behavior |
|-------|----------|
| `_prebuild.py` | Section `[8]` validates manifest integrity |
| `scripts/enterprise_qa_gate.py` | Delegates to `mandatory_release_qa.py --phase pre_release` |
| `scripts/run_cli_browser_qa.py` | Node Playwright `/cli_terminal` credential_id QA (mocked SSH; not Python Playwright) |
| Agents | Rule `05-nst-mandatory-qa.mdc` — extend tests on feature/bug |
| CI / release engineer | Run `all` before EXE build |

## Environment flags

| Flag | Meaning |
|------|---------|
| `NST_QA_ON_CHANGE` | Documented trigger for on-change phase |
| `NST_QA_PRE_RELEASE` | Documented trigger for pre-release |
| `NST_MANDATORY_QA_FULL=1` | Run scaffold test bodies (default: skip) |
| `NST_CLI_BROWSER_QA_PORT` | Override loopback port for CLI browser QA server |
| `NST_CLI_BROWSER_QA_SKIP_INSTALL=1` | Skip `npm ci` / Chromium install (deps must already exist) |

## Do not

- Bump VERSION or build EXE without `pre_release` pass
- Add features without manifest + questionnaire updates
- Run full scaffold suite in every agent turn (expensive; use when implementing tests)

## References

- `tests/qa/README.md`
- `docs/09-qa/QA_EVOLUTION_POLICY.md`
- `.cursor/skills/nst-network-engineer-council/SKILL.md`
- `.cursor/skills/nst-release-engineer/SKILL.md`
