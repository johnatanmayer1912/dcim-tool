# Mandatory sync footer (embed in every implementation role)

**Copy this block into R-ENG, R-ARCH, R-QA, R-REL, R-SEC, R-OBS, R-PROD, R-RECON, R-LIB, R-GOV-LIB prompts.**

---

## Mandatory documentation + rebuild sync (non-negotiable)

Every task that **changes code, behavior, prompts, or VERSION** MUST complete this before the task is marked done — **without waiting for the user to request doc sync**.

| # | Action | Owner |
|---|--------|-------|
| 1 | Update `CHANGELOG.md` (what / why / impact) | R-ENG + R-LIB |
| 2 | Update affected docs per `docs/15-rebuild-roadmap/SYNC_PROTOCOL.md` | R-LIB |
| 3 | Update `docs/02-codebase/CODE_INVENTORY.md` + `UTILITIES_DOCUMENTATION.md` / `API_DOCUMENTATION.md` if modules/APIs touched | R-LIB |
| 4 | Update feature/ops guides under `docs/05-plugins/`, `docs/08-operations/` | R-LIB |
| 5 | Update matching `docs/15-rebuild-roadmap/**/P*.md` reconstruction prompts | R-RECON |
| 6 | Bump `docs/README.md` version awareness if `VERSION` changed | R-LIB |
| 7 | `action-logs/YYYY-MM-DD_<slug>.md` | Invoking role |

**Hub:** `PROMPT_COMMAND_CENTER.md` · **Procedure:** `CODE_CHANGE_DOCUMENTATION_UPDATE_PROCEDURES.md`

**Skipping doc sync = incomplete work** (G-06, G-18 rule 14).
