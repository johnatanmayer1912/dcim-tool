# Documentation Maintenance Guide

| Field | Value |
|-------|-------|
| **Version** | 2.0.0 |
| **Status** | active |
| **Owner** | Documentation Steward (R-LIB) |
| **Last Updated** | 2026-06-18 |
| **Application Version** | 7.0.51 |

---

## Purpose

This guide establishes the standards, procedures, and best practices for maintaining the documentation system for Network Swiss Tool Pro. It serves as the authoritative reference for how documentation must be built, maintained, synced, and validated for current and future usage.

---

## Documentation Philosophy

### Core Principles

1. **Intentionality:** Every document must serve a clear, specific purpose. No orphan or redundant documentation.
2. **Accuracy:** All documentation must be accurate, up-to-date, and validated against the codebase.
3. **Traceability:** All documentation must be traceable to code components, policies, and roles.
4. **Discoverability:** Documentation must be easy to find through logical organization and comprehensive indexing.
5. **Maintainability:** Documentation must be easy to update, version, and maintain over time.
6. **Professionalism:** Documentation must meet enterprise-level standards for quality and presentation.
7. **Synchronization:** All cross-references, links, and role references must be accurate and synchronized.

### Enterprise-Level Standards

- **Completeness:** All code components must have corresponding documentation
- **Consistency:** All documentation must follow consistent formatting and structure
- **Clarity:** Documentation must be clear, concise, and unambiguous
- **Validation:** All documentation must be validated before publication
- **Versioning:** All documentation must be versioned with change tracking
- **Review:** All documentation changes must undergo review process

---

## Documentation Structure

### Canonical Folder Structure

```
docs/
├── 00-overview/              # High-level project overview and introduction
├── 01-architecture/          # System and module architecture documentation
├── 02-codebase/              # Code inventory, API docs, and technical details
├── 03-infrastructure/        # Infrastructure and deployment documentation
├── 04-automation/            # Automation, CI/CD, and workflows
├── 05-plugins/               # Plugin system and individual plugins
├── 06-ui-ux/                 # UI/UX documentation (web templates, Jinja2)
├── 07-operations/            # Operational guides, runbooks, troubleshooting
├── 08-security/              # Security documentation (auth, authz, threat model)
├── 09-qa/                    # QA standards, testing, production readiness
├── 10-rebuild/               # Build process, installation, recovery
├── 11-reference/             # Reference materials, standards, archives
├── 12-master-prompts/        # Prompt governance framework (G-00 through G-18)
├── 13-bug-reports/           # Bug tracking and fix workflow
├── 14-roadmap/               # Roadmap and reconstruction prompts
├── 15-visual-guide/          # Visual guide for program reconstruction
├── 16-roles-by-command/      # Command reference (→ PROMPT_COMMAND_CENTER)
├── 17-ongoing-tasks/         # T-001–T-005 recurring tasks
├── 18-interface-management/  # Interface management feature documentation
├── 19-recovery/              # Recovery procedures and disaster recovery
├── 20-release-management/    # Release notes, changelog, compatibility
├── rebuilt-1-1/              # 1:1 rebuild context documentation
├── DOCS_CANONICAL_MAP.md     # Folder canonical vs legacy guide
├── DOCUMENTATION_MASTER_INDEX.md  # Master navigation index
├── DOCUMENTATION_MAINTENANCE_GUIDE.md  # This guide
├── DOCUMENTATION_VALIDATION_CHECKLIST.md  # Validation checklist
├── README.md                 # Project README
└── [Historical audit files]  # Archive historical documentation
```

### Folder Naming Conventions

- Use two-digit prefixes for logical ordering (00-20)
- Use lowercase with hyphens for folder names
- Use descriptive names that clearly indicate folder purpose
- Maintain consistent depth (max 3 levels deep)

### File Naming Conventions

- Use uppercase with underscores for policy files (e.g., PROMPT_GOVERNANCE_POLICY.md)
- Use lowercase with hyphens for documentation files (e.g., module-architecture.md)
- Use uppercase with underscores for role files (e.g., ROLE_SYSTEM_ARCHITECT_USAGE_PROMPT.md)
- Use version suffixes for release notes (e.g., RELEASE_NOTES_7.0.10.md)
- Use date prefixes for action logs (e.g., 2026-06-02_team-meeting-audit.md)

---

## Document Standards

### Required Document Header

Every documentation file must include:

```markdown
# Document Title

| Field | Value |
|-------|-------|
| **Version** | X.Y.Z |
| **Status** | active | archive | deprecated | retired |
| **Owner** | [Role or Person] |
| **Last Updated** | YYYY-MM-DD |
| **Application Version** | X.Y.Z (if applicable) |
```

### Document Structure

Every documentation file should follow this structure:

1. **Header** - Version, status, owner, last updated
2. **Purpose** - Clear statement of document purpose
3. **Scope** - What is and isn't covered
4. **Audience** - Who should read this document
5. **Prerequisites** - What knowledge is required
6. **Content** - Main documentation content
7. **Cross-References** - Links to related documents
8. **References** - External references
9. **Change History** - Version history (if applicable)

### Content Standards

- **Clarity:** Use clear, concise language
- **Completeness:** Cover all relevant aspects of the topic
- **Accuracy:** Ensure all information is correct and up-to-date
- **Examples:** Provide examples where helpful
- **Diagrams:** Use diagrams for complex concepts
- **Code Snippets:** Include code snippets with syntax highlighting
- **Tables:** Use tables for structured data
- **Lists:** Use lists for sequential or grouped information

---

## Cross-Reference Standards

### Internal References

All internal references must use relative paths from the docs/ directory:

```markdown
# Correct (from docs/02-codebase/)
See: ../01-architecture/MODULE_ARCHITECTURE.md

# Correct (from docs/ root)
See: 01-architecture/MODULE_ARCHITECTURE.md

# Incorrect (absolute paths)
See: c:\Users\...\docs\01-architecture\MODULE_ARCHITECTURE.md
```

### Policy References

All policy references must point to canonical locations:

```markdown
# Governance Policy
See: 12-master-prompts/PROMPT_GOVERNANCE_POLICY.md (G-03)

# Documentation Policy
See: 12-master-prompts/DOCUMENTATION_POLICY.md (G-06)

# Quality Gate Policy
See: 12-master-prompts/QUALITY_GATE_POLICY.md (G-07)
```

### Role References

All role references must point to canonical combined files:

```markdown
# Prompt Librarian
See: 12-master-prompts/roles/combined/ROLE_PROMPT_LIBRARIAN_USAGE_PROMPT.md (R-GOV-LIB)

# System Architect
See: 12-master-prompts/roles/combined/ROLE_SYSTEM_ARCHITECT_USAGE_PROMPT.md (R-ARCH)

# Documentation Steward
See: 12-master-prompts/roles/combined/ROLE_DOCUMENTATION_STEWARD_USAGE_PROMPT.md (R-LIB)
```

### Code References

All code references must point to canonical locations:

```markdown
# Module reference
See: modules/plugin_registry.py

# Plugin reference
See: modules/plugins/network_discovery.py

# Utility reference
See: utils/discovery_graph.py
```

---

## Version Control

### Version Numbering

Use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR:** Structure, responsibility, or behavior changes
- **MINOR:** Expanded scope or important clarification
- **PATCH:** Wording or formatting only

### Version Update Workflow

1. Determine change type (major/minor/patch)
2. Update version number in document header
3. Update last_updated date
4. Add change to change history section
5. Update DOCUMENTATION_MASTER_INDEX.md if applicable
6. Update PROMPT_REGISTRY.md if applicable
7. Create action log entry if significant change

### Change History Format

```markdown
## Change History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2026-06-02 | Initial version | Documentation Steward |
| 1.1.0 | 2026-06-15 | Added section on cross-references | Documentation Steward |
```

---

## Documentation Update Workflow

### When to Update Documentation

Documentation must be updated when:

1. **Code Changes:** Any code change that affects documented behavior
2. **Feature Addition:** New features are added
3. **Bug Fix:** Bugs are fixed that affect documented behavior
4. **Deprecation:** Features or components are deprecated
5. **Policy Change:** Governance policies change
6. **Role Change:** Role responsibilities change
7. **Architecture Change:** System architecture changes
8. **API Change:** API endpoints change
9. **Configuration Change:** Configuration parameters change
10. **Process Change:** Operational processes change

### Update Procedure

1. **Identify Affected Documentation**
   - Search for references to changed code/component
   - Identify all documents that need updates
   - Prioritize by impact (critical/high/medium/low)

2. **Update Documentation**
   - Update content to reflect changes
   - Update version number
   - Update last_updated date
   - Add change to change history

3. **Validate Cross-References**
   - Verify all internal links are valid
   - Verify all policy references are correct
   - Verify all role references are correct
   - Verify all code references are correct

4. **Review and Approve**
   - Self-review for accuracy
   - Peer review if significant change
   - Approve and commit

5. **Update Index**
   - Update DOCUMENTATION_MASTER_INDEX.md
   - Update PROMPT_REGISTRY.md if applicable
   - Create action log entry if significant

### Update Checklist

- [ ] Content updated to reflect changes
- [ ] Version number updated
- [ ] Last_updated date updated
- [ ] Change history updated
- [ ] Cross-references validated
- [ ] Policy references validated
- [ ] Role references validated
- [ ] Code references validated
- [ ] DOCUMENTATION_MASTER_INDEX.md updated
- [ ] PROMPT_REGISTRY.md updated (if applicable)
- [ ] Action log entry created (if significant)

---

## Documentation Validation

### Validation Criteria

Documentation must be validated against:

1. **Code Accuracy:** Documentation matches actual code behavior
2. **Completeness:** All relevant aspects are documented
3. **Clarity:** Documentation is clear and understandable
4. **Consistency:** Documentation follows established standards
5. **Accuracy:** All information is correct
6. **Currency:** Documentation is up-to-date
7. **Traceability:** Documentation is traceable to code
8. **Discoverability:** Documentation is easy to find

### Validation Process

1. **Self-Validation**
   - Review against validation criteria
   - Check cross-references
   - Verify version info
   - Check formatting

2. **Peer Validation** (for significant changes)
   - Request peer review
   - Incorporate feedback
   - Re-validate

3. **Automated Validation** (where applicable)
   - Run automated checks
   - Fix any issues
   - Re-validate

### Validation Tools

- **DOCUMENTATION_VALIDATION_CHECKLIST.md** - Comprehensive validation checklist
- **DOCUMENTATION_MASTER_INDEX.md** - Cross-reference validation
- **PROMPT_REGISTRY.md** - Registry validation
- **CODE_INVENTORY.md** - Code-to-documentation mapping validation

---

## Duplicate Documentation Prevention

### Duplicate Detection

1. **Regular Audits**
   - Quarterly documentation audits
   - Check for duplicate content
   - Consolidate or remove duplicates

2. **Canonical Locations**
   - Establish canonical locations for each type of documentation
   - Redirect non-canonical locations to canonical
   - Maintain redirect notes

3. **Content Review**
   - Review new documentation for duplicates before publication
   - Check for overlapping content
   - Consolidate or clarify scope

### Consolidation Procedure

1. **Identify Duplicates**
   - Search for similar content
   - Identify canonical location
   - Identify non-canonical locations

2. **Consolidate**
   - Merge content into canonical document
   - Add redirect note to non-canonical
   - Update cross-references

3. **Remove**
   - Remove duplicate content
   - Update DOCUMENTATION_MASTER_INDEX.md
   - Update PROMPT_REGISTRY.md if applicable

### Canonical Locations

| Documentation Type | Canonical Location |
|-------------------|-------------------|
| Plugin Documentation | docs/plugins/ |
| API Documentation | docs/02-codebase/API_DOCUMENTATION.md |
| Module Architecture | docs/01-architecture/MODULE_ARCHITECTURE.md |
| Utilities Documentation | docs/02-codebase/UTILITIES_DOCUMENTATION.md |
| Build Process | docs/10-rebuild/BUILD_PROCESS.md |
| Code Inventory | docs/02-codebase/CODE_INVENTORY.md |
| Documentation Gap Analysis | docs/02-codebase/DOCUMENTATION_GAP_ANALYSIS.md |
| Consolidation Log | docs/02-codebase/CONSOLIDATION_LOG.md |
| Recreation Test Report | docs/02-codebase/RECREATION_TEST_REPORT.md |

---

## Documentation Quality Gates

### Quality Gate Criteria

Documentation must pass these quality gates before publication:

1. **Completeness Gate:** All required sections present
2. **Accuracy Gate:** All information verified against code
3. **Clarity Gate:** Content is clear and understandable
4. **Consistency Gate:** Follows established standards
5. **Cross-Reference Gate:** All cross-references valid
6. **Version Gate:** Version info present and correct
7. **Review Gate:** Reviewed and approved

### Quality Gate Process

1. **Self-Check**
   - Run through quality gate criteria
   - Fix any issues
   - Re-check

2. **Peer Review** (for significant changes)
   - Submit for peer review
   - Address feedback
   - Re-check

3. **Final Approval**
   - Approve for publication
   - Commit to repository
   - Update indices

### Quality Gate Failure

If documentation fails quality gate:

1. **Identify Failure**
   - Determine which gate failed
   - Understand why it failed

2. **Fix Issues**
   - Address the failure
   - Re-validate

3. **Re-Submit**
   - Re-run quality gates
   - Approve if passes

---

## Documentation Roles and Responsibilities

### Documentation Steward (R-LIB)

**Responsibilities:**
- Maintain documentation standards
- Review documentation changes
- Validate documentation quality
- Update documentation indices
- Coordinate with other roles

**Authority:**
- Approve documentation changes
- Require documentation updates
- Block non-compliant documentation
- Request documentation audits

### Prompt Librarian (R-GOV-LIB)

**Responsibilities:**
- Maintain prompt governance documentation
- Validate prompt documentation
- Update prompt registry
- Conduct documentation audits
- Track documentation coverage

**Authority:**
- Update prompt documentation
- Validate prompt registry
- Conduct documentation audits
- Require documentation compliance

### All Roles

**Responsibilities:**
- Update documentation for their domain
- Validate documentation accuracy
- Follow documentation standards
- Report documentation issues
- Participate in documentation reviews

---

## Documentation Metrics

### Coverage Metrics

- **Code Coverage:** Percentage of code components with documentation
- **Feature Coverage:** Percentage of features with documentation
- **API Coverage:** Percentage of API endpoints with documentation
- **Plugin Coverage:** Percentage of plugins with documentation

### Quality Metrics

- **Accuracy:** Percentage of documentation verified against code
- **Completeness:** Percentage of required sections present
- **Currency:** Percentage of documentation updated within 30 days
- **Validation:** Percentage of documentation passing quality gates

### Maintenance Metrics

- **Update Frequency:** Average time between documentation updates
- **Review Frequency:** Average time between documentation reviews
- **Audit Frequency:** Time between documentation audits
- **Issue Resolution:** Average time to resolve documentation issues

---

## Documentation Tools

### Indexing

- **DOCUMENTATION_MASTER_INDEX.md** - Master navigation index
- **PROMPT_REGISTRY.md** - Prompt registry
- **CODE_INVENTORY.md** - Code inventory

### Validation

- **DOCUMENTATION_VALIDATION_CHECKLIST.md** - Validation checklist
- **DOCUMENTATION_MAINTENANCE_GUIDE.md** - This guide
- **DOCUMENTATION_GAP_ANALYSIS.md** - Gap analysis

### Tracking

- **CONSOLIDATION_LOG.md** - Consolidation tracking
- **RECREATION_TEST_REPORT.md** - Recreation capability validation
- **Action Logs** - Role invocation logs

---

## Documentation Best Practices

### Writing

1. **Be Clear:** Use clear, concise language
2. **Be Complete:** Cover all relevant aspects
3. **Be Accurate:** Verify all information
4. **Be Consistent:** Follow established standards
5. **Be Professional:** Use professional tone

### Organization

1. **Logical Structure:** Organize content logically
2. **Clear Headings:** Use clear, descriptive headings
3. **Consistent Formatting:** Use consistent formatting
4. **Visual Aids:** Use diagrams and tables where helpful
5. **Examples:** Provide examples where helpful

### Maintenance

1. **Regular Updates:** Update documentation regularly
2. **Version Control:** Use version control for all changes
3. **Change Tracking:** Track all changes
4. **Review Process:** Follow review process
5. **Quality Gates:** Pass quality gates

### Collaboration

1. **Peer Review:** Request peer reviews
2. **Feedback:** Incorporate feedback
3. **Communication:** Communicate changes
4. **Coordination:** Coordinate with other roles
5. **Documentation:** Document the process

---

## Documentation Lifecycle

### Creation

1. **Identify Need:** Determine documentation need
2. **Plan Content:** Plan content structure
3. **Draft Content:** Draft initial content
4. **Review:** Review and refine
5. **Validate:** Validate against code
6. **Approve:** Approve for publication
7. **Publish:** Publish to repository
8. **Index:** Update indices

### Update

1. **Identify Change:** Determine need for update
2. **Update Content:** Update content
3. **Update Version:** Update version number
4. **Validate:** Validate changes
5. **Review:** Review if significant
6. **Approve:** Approve changes
7. **Publish:** Publish to repository
8. **Index:** Update indices

### Deprecation

1. **Identify Need:** Determine need for deprecation
2. **Mark Deprecated:** Mark document as deprecated
3. **Redirect:** Add redirect to replacement
4. **Archive:** Archive after grace period
5. **Remove:** Remove from active index
6. **Retain:** Retain in archive

---

## Documentation Governance

### Policies

All documentation must comply with:

- **PROMPT_GOVERNANCE_POLICY.md (G-03)** - Governance policy
- **DOCUMENTATION_POLICY.md (G-06)** - Documentation policy
- **QUALITY_GATE_POLICY.md (G-07)** - Quality gate policy
- **CHANGE_MANAGEMENT_POLICY.md (G-08)** - Change management policy

### Standards

All documentation must follow:

- **ROLE_USAGE_STANDARD.md (G-14)** - Role usage standard
- **PROMPT_EXECUTION_RULES.md (G-15)** - Prompt execution rules
- **GLOBAL_MASTER_PROMPT_RULES.md (G-18)** - Absolute rules

### Processes

All documentation must follow:

- **PROMPT_MIGRATION_SYNC.md (G-16)** - Migration and sync
- **TEAM_MEETING.md (G-11)** - Team meeting escalation
- **FINAL_OPERATING_INSTRUCTION.md (G-17)** - Operating instruction

---

## Documentation Troubleshooting

### Common Issues

#### Broken Cross-References

**Symptom:** Links to other documents don't work

**Solution:**
1. Verify target document exists
2. Verify path is correct
3. Update cross-reference
4. Validate all cross-references

#### Outdated Information

**Symptom:** Documentation doesn't match current code

**Solution:**
1. Identify outdated sections
2. Update content
3. Verify against code
4. Update version number

#### Duplicate Content

**Symptom:** Same content in multiple documents

**Solution:**
1. Identify canonical location
2. Consolidate content
3. Add redirect notes
4. Update cross-references

#### Missing Documentation

**Symptom:** Code component lacks documentation

**Solution:**
1. Identify missing documentation
2. Create documentation
3. Validate against code
4. Update indices

#### Quality Gate Failure

**Symptom:** Documentation fails quality gate

**Solution:**
1. Identify failed gate
2. Fix issues
3. Re-validate
4. Re-submit

---

## Documentation Future Improvements

### Planned Improvements

1. **Automated Validation:** Implement automated documentation validation
2. **Documentation Generation:** Generate documentation from code comments
3. **Documentation Testing:** Test documentation against code
4. **Documentation Metrics:** Implement comprehensive metrics tracking
5. **Documentation Reviews:** Regular documentation review process

### Future Considerations

1. **Documentation as Code:** Treat documentation as code
2. **Documentation CI/CD:** Integrate documentation into CI/CD
3. **Documentation Monitoring:** Monitor documentation health
4. **Documentation Analytics:** Analyze documentation usage
5. **Documentation AI:** Use AI for documentation assistance

---

## References

- DOCUMENTATION_MASTER_INDEX.md: docs/DOCUMENTATION_MASTER_INDEX.md
- DOCUMENTATION_VALIDATION_CHECKLIST.md: docs/DOCUMENTATION_VALIDATION_CHECKLIST.md
- INDEX_PROMPT.md: docs/12-master-prompts/INDEX_PROMPT.md
- PROMPT_REGISTRY.md: docs/12-master-prompts/PROMPT_REGISTRY.md
- DOCUMENTATION_POLICY.md: docs/12-master-prompts/DOCUMENTATION_POLICY.md
- QUALITY_GATE_POLICY.md: docs/12-master-prompts/QUALITY_GATE_POLICY.md
- CODE_INVENTORY.md: docs/02-codebase/CODE_INVENTORY.md
