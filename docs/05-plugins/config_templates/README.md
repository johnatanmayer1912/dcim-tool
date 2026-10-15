# Template-Based Configuration Generator Plugin

# Purpose
The **Template-Based Configuration Generator Plugin** allows network administrators to generate standard, verified network device configurations using standard **Jinja2** templates in a completely safe, read-only preview mode. It automatically parses variables from custom templates and generates dynamic web forms for user input.

# Scope
- **Engine**: Jinja2 Template Compiler.
- **Templates**: Any standard `.j2` or `.txt` configuration snippets stored under the `templates/` program directory.
- **Remediation**: Outputs formatted configuration previews. Safe execution — does not write or push commands to devices directly.

# Dependencies
- **jinja2**: Python Jinja2 compiler engine (falls back to regex placeholder compiler if jinja2 is missing).
- **modules/network_base.py**: Host resolution and reporting dependencies.
- **utils/report_formatter.py**: Consolidated master reporting.

# Related Documents
- [Plugin System Mandate](../../05-plugins/ui-philosophy.md)
- [LIBRARIAN Prime Directive](../../00-overview/LIBRARIAN_MANDATE.md)

# Operational Impact
- **NOC-Compliant**: 100% read-only. Avoids dangerous automated script pushes by requiring configuration review before copy-paste execution.
- **Central Library**: Centralizes team configurations under a single, writeable `templates/` folder in the program directory.

# Failure Conditions
- **Syntax Errors**: Caught gracefully with diagnostic stack-traces presented directly in the web UI.

# Template catalog (v6.9.28)

| File | Use case |
|------|----------|
| `cisco_nxos_trunk.j2` | NX-OS trunk interface |
| `cisco_nxos_port_channel.j2` | NX-OS LACP port-channel + members |
| `cisco_nxos_trunk_vpc.j2` | NX-OS trunk with `vpc` binding |
| `cisco_ios_trunk.j2` | IOS/XE trunk |
| `cisco_ios_port_channel.j2` | IOS port-channel |
| `cisco_ios_ntp.j2` / `cisco_ios_syslog.j2` | Baseline services |

**Quick builder:** Templates tab → preset dropdown → **Generate into editor** (`GET /api/templates/presets`).

# Last Synchronization Timestamp
- **Date**: 2026-05-31 (app v6.9.28)
- **Maintainer**: Network Swiss Tool UI/UX & Automation Engineering Team
