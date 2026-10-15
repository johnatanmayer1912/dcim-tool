# Fix prompt — BUG-0001 (copy into AI IDE)

Synchronize documentation to **v6.9.25** per LIBRARIAN mandate:

1. Update **Version Awareness** footers in `docs/README.md`, `docs/00-overview/walkthrough.md`, `docs/00-overview/roadmap.md`, `docs/08-operations/search-it-workflow.md` to v6.9.25.
2. Walkthrough: point to `dist/NetworkSwissToolPro_v6.9.25_OFFLINE.exe` and `http://127.0.0.1:5051`.
3. `docs/13-master-prompts/PROMPT_REGISTRY.md`: set Application sync to 6.9.25.
4. `docs/11-release-management/README.md` Quick Start Web row: align port **5051** and current OFFLINE exe name.
5. Do not edit archived `dist_package_*` trees unless user requests.

Run grep: `6\.9\.(1[0-9]|2[0-4])\b` under `docs/` (exclude `CHANGELOG.md` history and `14-bug-reports/`).
