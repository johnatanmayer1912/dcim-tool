# Security Documentation

## Purpose

This folder contains documentation related to security, compliance, and auditing for the Network Management Tool.

## Scope

Security documentation covers:
- Security policies
- Security procedures
- Compliance requirements
- Security audits
- Vulnerability management
- Security best practices
- Authentication and authorization
- Data protection

## File Inventory

This folder contains security-related documentation files.

## Related Documentation

- `01-architecture/` - System architecture documentation
- `03-infrastructure/` - Infrastructure security documentation
- `07-operations/` - Security operations documentation
- `09-qa/` - Security testing documentation

## Usage Guidelines

### Session credential cache (v7.0.58+)

Sidebar credentials entered for tasks are stored **in process memory only** (not on disk). They survive browser tab reload while the EXE/server is running and are cleared on **Stop** (`/api/shutdown`) or normal process exit. The vault (Fernet) remains separate for saved credential profiles.

## Related Documentation

Use this documentation to:
- Understand security requirements
- Implement security measures
- Conduct security audits
- Manage vulnerabilities
- Ensure compliance
- Handle security incidents

## Maintenance

Security documentation should be updated when:
- Security policies change
- New security threats emerge
- Compliance requirements change
- Security procedures are updated
- Security audits are conducted

## Related Documentation

- `docs/COMPREHENSIVE_DOCS_ORGANIZATION_PLAN.md` - Documentation organization plan
- `docs/DOCUMENTATION_MASTER_INDEX.md` - Documentation master index
