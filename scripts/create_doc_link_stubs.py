#!/usr/bin/env python3
"""Create redirect stub markdown files to resolve broken internal doc links."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "docs"

STUBS = {
    "01-architecture/plugin-architecture.md": (
        "# Plugin Architecture\n\n"
        "> **Canonical:** [MODULE_ARCHITECTURE.md](MODULE_ARCHITECTURE.md)\n\n"
        "Plugin system design, registry, and lifecycle are documented in `MODULE_ARCHITECTURE.md`.\n"
    ),
    "02-codebase/module-breakdown.md": (
        "# Module Breakdown\n\n"
        "> **Canonical:** [CODE_INVENTORY.md](CODE_INVENTORY.md) · [MODULE_ARCHITECTURE.md](../01-architecture/MODULE_ARCHITECTURE.md)\n"
    ),
    "03-infrastructure/cisco-automation.md": (
        "# Cisco Automation\n\n"
        "> **Canonical:** [parsing-workflows.md](parsing-workflows.md) · [MODULE_ARCHITECTURE.md](../01-architecture/MODULE_ARCHITECTURE.md)\n"
    ),
    "01-architecture/JUNOS_COMPATIBILITY.md": (
        "# Junos Compatibility\n\n"
        "> **Canonical:** [network_discovery README](../05-plugins/network_discovery/README.md) · [mac-trace-howto](../08-operations/mac-trace-howto.md)\n\n"
        "Junos / QFX / EX platforms: LLDP brief-first, `xe-`/`ge-`/`ae` interfaces, colon MAC format.\n"
    ),
    "07-security/credential-management.md": (
        "# Credential Management\n\n"
        "> **Implementation:** `modules/credential_manager.py` · [authentication.md](authentication.md)\n\n"
        "Fernet-encrypted credential sets for offline EXE deployments.\n"
    ),
    "09-qa/qa-strategy.md": (
        "# QA Strategy\n\n"
        "> **See also:** [ST_MASTER_QA_SUITE.md](ST_MASTER_QA_SUITE.md) · [production-readiness.md](production-readiness.md)\n\n"
        "## Gates\n\n1. `python -m pytest tests/ -q`\n2. `python _prebuild.py`\n3. `python scripts/enterprise_qa_gate.py`\n4. `python scripts/validate_docs_links.py`\n"
    ),
    "08-operations/CONNECTION_ISSUES.md": (
        "# Connection Troubleshooting\n\n"
        "> **Index:** [TS_ERROR_INDEX.md](TS_ERROR_INDEX.md) · [operational-workflows.md](operational-workflows.md)\n\n"
        "Ping target, verify port 22, check inventory IP, firewall, and `connect_permissive` encryption fallback.\n"
    ),
    "08-operations/AUTH_ISSUES.md": (
        "# Authentication Troubleshooting\n\n"
        "> **Index:** [TS_ERROR_INDEX.md](TS_ERROR_INDEX.md)\n\n"
        "Verify username/password, enable secret, Juniper root if required, and credential manager entries.\n"
    ),
    "08-operations/TOPOLOGY_ISSUES.md": (
        "# Topology Troubleshooting\n\n"
        "> **Index:** [TS_ERROR_INDEX.md](TS_ERROR_INDEX.md) · [discovery-trust-validation.md](discovery-trust-validation.md)\n"
    ),
    "08-operations/WEB_INTERFACE_ISSUES.md": (
        "# Web Interface Troubleshooting\n\n"
        "> **Index:** [TS_ERROR_INDEX.md](TS_ERROR_INDEX.md) · port **5051**\n"
    ),
    "08-operations/CLI_TERMINAL_ISSUES.md": (
        "# CLI Terminal Troubleshooting\n\n"
        "> **Index:** [TS_ERROR_INDEX.md](TS_ERROR_INDEX.md) · CLI smoke in `_prebuild.py`\n"
    ),
    "08-operations/device_specific/README.md": (
        "# Device-Specific Troubleshooting\n\n"
        "> **Junos:** [JUNOS_COMPATIBILITY.md](../01-architecture/JUNOS_COMPATIBILITY.md)\n"
    ),
    "08-operations/recovery/README.md": (
        "# Recovery Procedures\n\n"
        "> **Canonical:** [BUILD_PROCEDURES.md](BUILD_PROCEDURES.md) · [../15-rebuild-roadmap/DISASTER_RECOVERY_COMMAND.md](../15-rebuild-roadmap/DISASTER_RECOVERY_COMMAND.md)\n"
    ),
    "08-operations/recovery/BUILD_PROCEDURES.md": (
        "# Build Procedures\n\n"
        "> **Canonical:** [BUILD_GUIDE.md](../../BUILD_GUIDE.md) (repo root)\n"
    ),
    "08-operations/qa_testing/README.md": (
        "# QA Testing Index\n\n"
        "> **Canonical:** [../09-qa/ST_MASTER_QA_SUITE.md](../09-qa/ST_MASTER_QA_SUITE.md)\n"
    ),
    "11-release-management/release-history.md": (
        "# Release History\n\n"
        "> **Canonical:** [CHANGELOG.md](../../CHANGELOG.md) · per-version notes in this folder\n"
    ),
    "10-rebuild/dependency-restoration.md": (
        "# Dependency Restoration\n\n"
        "> **Canonical:** [../15-rebuild-roadmap/01-foundation/P02-DEPENDENCY-INSTALLATION.md](../15-rebuild-roadmap/01-foundation/P02-DEPENDENCY-INSTALLATION.md)\n"
    ),
    "05-ui-ux/ui-philosophy.md": (
        "# UI Philosophy\n\n"
        "> **Canonical:** Swiss Tools dark theme in `modules/web/templates/index.html`\n"
    ),
    "10-reference/prompts/00-PROMPT-INDEX.md": (
        "# Prompt Index (legacy)\n\n"
        "> **Canonical:** [../../15-rebuild-roadmap/00-RECONSTRUCTION_INDEX.md](../../15-rebuild-roadmap/00-RECONSTRUCTION_INDEX.md) · [../../13-master-prompts/PROMPT_COMMAND_CENTER.md](../../13-master-prompts/PROMPT_COMMAND_CENTER.md)\n"
    ),
    "04-plugins/plugin-development-guide.md": (
        "# Plugin Development (legacy path)\n\n"
        "> **Canonical:** [../04-automation/plugin-development-guide.md](../04-automation/plugin-development-guide.md)\n"
    ),
}

for rel, body in STUBS.items():
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(body, encoding="utf-8")
        print(f"created {rel}")
    else:
        print(f"exists  {rel}")
