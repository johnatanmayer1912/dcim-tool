# Code Change Documentation Update Procedures

| Field | Value |
|-------|-------|
| **Document ID** | PROC-CCDU |
| **Document Type** | Procedure |
| **Category** | Documentation Governance |
| **Owner** | Documentation Steward (R-LIB) |
| **Status** | active |
| **Last Updated** | 2026-06-10 |
| **Version** | 2.0.0 |
| **Application Version** | 7.0.29 |

---

## Purpose

This document defines the procedures for updating documentation when code changes are made. It ensures that all code changes trigger necessary documentation updates in both the rebuild roadmap and ongoing documentation, maintaining 100% 1:1 recreation capability.

**Hardcoded enforcement:** Integrated into `PROMPT_COMMAND_CENTER.md` (G-CC), `GLOBAL_MASTER_PROMPT_RULES.md` (rules 21–23), and `roles/_MANDATORY_SYNC_FOOTER.md`. **Every implementation task runs this procedure automatically** — not only when the user invokes "update documentation" or "doc sync".

---

## Scope

This procedure applies to:
- All code changes to the application
- All feature additions or modifications
- All bug fixes
- All configuration changes
- All dependency updates
- All refactoring efforts

---

## Roles and Responsibilities

### Lead Developer (R-ENG)
- Identify documentation impact of code changes
- Create or update relevant documentation
- Submit documentation updates for review

### Documentation Steward (R-LIB)
- Review documentation updates for completeness
- Validate cross-references and links
- Ensure documentation governance compliance
- Maintain documentation audit logs

### System Architect (R-ARCH)
- Review architectural documentation updates
- Validate architectural consistency
- Ensure design patterns are documented

### Program Reconstructor (R-RECON)
- Update rebuild roadmap prompts for code changes
- Ensure 1:1 reconstruction capability is maintained
- Validate prompt dependencies and execution order

---

## Procedure

### Step 1: Code Change Identification

When a code change is proposed or implemented:

1. **Lead Developer (R-ENG)** identifies the scope of the change:
   - Which modules are affected?
   - Which features are modified?
   - Which APIs are changed?
   - Which dependencies are updated?

2. **Lead Developer (R-ENG)** creates a code change ticket with:
   - Change description
   - Affected modules
   - Documentation impact assessment
   - Proposed documentation updates

---

### Step 2: Documentation Impact Assessment

**Lead Developer (R-ENG)** assesses documentation impact:

1. **Ongoing Documentation Updates:**
   - Update relevant codebase documentation in `docs/02-codebase/`
   - Update API documentation if APIs changed
   - Update module architecture if modules modified
   - Update troubleshooting scenarios if new issues introduced

2. **Rebuild Roadmap Updates:**
   - Identify which prompts need updating
   - Update prompt content to reflect code changes
   - Update prompt dependencies if needed
   - Update validation criteria if needed

3. **Cross-Reference Validation:**
   - Check for broken links
   - Validate role references
   - Validate policy references
   - Update master index if needed

---

### Step 3: Documentation Updates

**Lead Developer (R-ENG)** creates documentation updates:

1. **Ongoing Documentation:**
   - Update or create relevant markdown files
   - Update code examples if syntax changed
   - Update diagrams if architecture changed
   - Update configuration examples

2. **Rebuild Roadmap:**
   - Update relevant prompt files (PXX-*.md)
   - Update prompt index if prompts added/removed
   - Update reconstruction index if phases changed
   - Update validation criteria

3. **Documentation Metadata:**
   - Update version numbers
   - Update last updated dates
   - Update owner if responsibility changed
   - Update status if applicable

---

### Step 4: Documentation Review

**Documentation Steward (R-LIB)** reviews documentation updates:

1. **Completeness Check:**
   - All affected documentation updated
   - No missing sections
   - All examples accurate
   - All cross-references valid

2. **Quality Check:**
   - Grammar and spelling correct
   - Formatting consistent
   - Code examples valid
   - Diagrams clear

3. **Governance Check:**
   - Complies with DOCUMENTATION_POLICY.md (G-06)
   - Complies with PROMPT_GOVERNANCE_POLICY.md (G-03)
   - All role references correct
   - All policy references correct

---

### Step 5: Documentation Validation

**Program Reconstructor (R-RECON)** validates rebuild roadmap:

1. **Prompt Validation:**
   - All prompts updated correctly
   - Prompt dependencies valid
   - Execution order correct
   - Validation criteria accurate

2. **Reconstruction Test:**
   - Verify prompts can reconstruct the change
   - Test prompt execution order
   - Validate prompt dependencies
   - Ensure 1:1 reconstruction capability maintained

---

### Step 6: Documentation Approval

**Documentation Steward (R-LIB)** approves documentation updates:

1. **Approval Criteria:**
   - All documentation updates complete
   - All reviews passed
   - All validations passed
   - No broken links or references

2. **Approval Action:**
   - Mark documentation as approved
   - Update documentation audit log
   - Notify stakeholders
   - Merge documentation changes

---

### Step 7: Documentation Audit

**Documentation Steward (R-LIB)** conducts audit:

1. **Audit Log Entry:**
   - Record code change ID
   - Record documentation updates made
   - Record approval date
   - Record reviewer

2. **Audit Validation:**
   - Verify all updates logged
   - Verify audit trail complete
   - Verify governance compliance
   - Update action log

---

## Documentation Update Checklist

Before code change can be merged:

- [ ] Code change impact assessed
- [ ] Affected documentation identified
- [ ] Ongoing documentation updated
- [ ] Rebuild roadmap prompts updated
- [ ] Cross-references validated
- [ ] Documentation reviewed by R-LIB
- [ ] Rebuild roadmap validated by R-RECON
- [ ] Documentation approved
- [ ] Audit log updated
- [ ] 1:1 reconstruction capability maintained

---

## Failure Recovery

### Documentation Update Fails

**Recovery Procedure:**
1. Identify missing documentation updates
2. Lead Developer (R-ENG) creates missing updates
3. Re-submit for review
4. Re-validate rebuild roadmap

### Rebuild Roadmap Update Fails

**Recovery Procedure:**
1. Identify affected prompts
2. Program Reconstructor (R-RECON) updates prompts
3. Re-validate prompt dependencies
4. Re-test reconstruction capability

### Validation Fails

**Recovery Procedure:**
1. Identify validation failures
2. Fix documentation issues
3. Re-submit for review
4. Re-validate

---

## Documentation Update Templates

### Code Change Documentation Template

```markdown
## Code Change: [CHANGE_ID]

**Date:** [DATE]  
**Author:** [AUTHOR]  
**Affected Modules:** [MODULES]

### Description
[Brief description of change]

### Documentation Impact
- [ ] Codebase documentation
- [ ] API documentation
- [ ] Architecture documentation
- [ ] Troubleshooting documentation
- [ ] Rebuild roadmap prompts

### Documentation Updates
[List specific documentation files updated]

### Rebuild Roadmap Updates
[List specific prompts updated]

### Validation
- [ ] Cross-references validated
- [ ] Links validated
- [ ] Prompts validated
- [ ] 1:1 reconstruction capability maintained
```

---

## References

- DOCUMENTATION_POLICY.md (G-06)
- PROMPT_GOVERNANCE_POLICY.md (G-03)
- TEAM_DOCUMENTATION_GOVERNANCE_MEETING.md
- ROLE_DOCUMENTATION_STEWARD_USAGE_PROMPT.md (R-LIB)
- ROLE_PROGRAM_RECONSTRUCTOR_USAGE_PROMPT.md (R-RECON)
- ROLE_LEAD_DEVELOPER_USAGE_PROMPT.md (R-ENG)
- ROLE_SYSTEM_ARCHITECT_USAGE_PROMPT.md (R-ARCH)
