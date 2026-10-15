# Combined Role + Usage Prompts

**Canonical invoke** for council roles. One file = **Part 1** (R-* master role) + **Part 2** (ROLE USAGE).

**Command hub:** [`../../PROMPT_COMMAND_CENTER.md`](../../PROMPT_COMMAND_CENTER.md) (G-CC) — all-in-one commands, mandatory doc/rebuild sync.

**Every implementation role** must honor [`../_MANDATORY_SYNC_FOOTER.md`](../_MANDATORY_SYNC_FOOTER.md) before marking work done.

Edit these files directly when changing role behavior. Registry: `PROMPT_REGISTRY.md`.

## Council roles

| Combined file | Registry ID | Role |
|---------------|-------------|------|
| [ROLE_PROMPT_LIBRARIAN_USAGE_PROMPT.md](ROLE_PROMPT_LIBRARIAN_USAGE_PROMPT.md) | R-GOV-LIB | Prompt Librarian |
| [ROLE_SYSTEM_ARCHITECT_USAGE_PROMPT.md](ROLE_SYSTEM_ARCHITECT_USAGE_PROMPT.md) | R-ARCH | System Architect |
| [ROLE_LEAD_DEVELOPER_USAGE_PROMPT.md](ROLE_LEAD_DEVELOPER_USAGE_PROMPT.md) | R-ENG | Lead Developer |
| [ROLE_QA_ENGINEER_USAGE_PROMPT.md](ROLE_QA_ENGINEER_USAGE_PROMPT.md) | R-QA | QA Engineer |
| [ROLE_SECURITY_REVIEWER_USAGE_PROMPT.md](ROLE_SECURITY_REVIEWER_USAGE_PROMPT.md) | R-SEC | Security Reviewer |
| [ROLE_OBSERVABILITY_ENGINEER_USAGE_PROMPT.md](ROLE_OBSERVABILITY_ENGINEER_USAGE_PROMPT.md) | R-OBS | Observability Engineer |
| [ROLE_DOCUMENTATION_STEWARD_USAGE_PROMPT.md](ROLE_DOCUMENTATION_STEWARD_USAGE_PROMPT.md) | R-LIB | Documentation Steward |
| [ROLE_RELEASE_MANAGER_USAGE_PROMPT.md](ROLE_RELEASE_MANAGER_USAGE_PROMPT.md) | R-REL | Release / Change Manager |
| [ROLE_PRODUCT_STRATEGIST_USAGE_PROMPT.md](ROLE_PRODUCT_STRATEGIST_USAGE_PROMPT.md) | R-PROD | Product / Platform Strategist |
| [ROLE_TEAM_MEETING_COUNCIL_USAGE_PROMPT.md](ROLE_TEAM_MEETING_COUNCIL_USAGE_PROMPT.md) | R-COUNCIL | Team Meeting Council |
| [ROLE_PROGRAM_RECONSTRUCTOR_USAGE_PROMPT.md](ROLE_PROGRAM_RECONSTRUCTOR_USAGE_PROMPT.md) | R-RECON | Program Reconstructor (disaster recovery) |

## Usage

Paste or `@`-reference one combined file. The AI must read **Part 1** (authority, gates, deliverables) then **Part 2** (activation signals, practices, handoffs).

Domain-only guides remain in `../` (`RESYNC_USAGE.md`, `TOPOLOGY_USAGE.md`, etc.).
