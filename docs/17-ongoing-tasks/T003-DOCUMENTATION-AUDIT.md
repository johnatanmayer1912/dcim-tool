# Task T-003: Documentation Audit

| Field | Value |
|-------|-------|
| **Task ID** | T-003 |
| **Task Name** | Documentation Audit |
| **Frequency** | Weekly |
| **Owner** | Documentation Steward (R-LIB) |
| **Executor** | Ongoing Task Executor (R-TASK) |
| **Status** | active |
| **Last Updated** | 2026-06-03 |
| **Version** | 1.0.0 |

---

## Purpose

Audit documentation for completeness, accuracy, and governance compliance. Validates cross-references and links. Generates update prompts for identified gaps with holistic team review.

---

## Scope

The documentation audit covers:
- Documentation completeness
- Accuracy and currency
- Cross-reference validation
- Governance compliance
- Rebuild roadmap validity
- Visual guide accuracy
- Role prompt currency
- Policy compliance

---

## Execution Procedure

### Step 1: Audit Initialization

**Executor:** R-TASK

1. **Gather Context**
   - Review recent documentation changes
   - Identify modified documentation files
   - Load documentation governance policies
   - Check for new features requiring documentation

2. **Define Audit Scope**
   - Identify all documentation to audit
   - Map documentation dependencies
   - Determine team members required
   - Set audit criteria and thresholds

---

### Step 2: Completeness Audit

**Lead:** R-LIB  
**Reviewers:** R-ENG, R-ARCH, R-RECON

1. **Feature Coverage**
   - Verify all documented features exist in code
   - Check for undocumented features
   - Validate API documentation completeness
   - Review configuration documentation

2. **Component Coverage**
   - Verify all modules documented
   - Check for undocumented components
   - Validate plugin documentation
   - Review utility documentation

**Gap Fix Prompts:**

```markdown
## Documentation Completeness Gap Fix Prompt

**Gap ID:** [GAP_ID]  
**Type:** [Feature/Component/API/Configuration]  
**Severity:** [Critical/High/Medium/Low]  
**Document:** [Document Name]

### Gap Description
[Detailed description of completeness gap]

### Impact Analysis
- **Affected Documentation:** [List of affected documents]
- **User Impact:** [Description of user impact]
- **Reconstruction Impact:** [Impact on 1:1 reconstruction]

### Fix Requirements
1. [Specific fix requirement 1]
2. [Specific fix requirement 2]
3. [Specific fix requirement 3]

### Team Review Requirements
- **R-LIB:** Review documentation quality
- **R-ENG:** Review technical accuracy
- **R-ARCH:** Review architectural documentation
- **R-RECON:** Review rebuild roadmap impact

### Validation Criteria
- [ ] Documentation created/updated
- [ ] All features documented
- [ ] All team members approved
- [ ] Cross-references validated
- [ ] Rebuild roadmap updated if needed
- [ ] Visual guide updated if needed

### Expected Output
- New/updated documentation
- Validated cross-references
- Team approval record
- Updated rebuild roadmap if needed
- Updated visual guide if needed
```

---

### Step 3: Accuracy Audit

**Lead:** R-LIB  
**Reviewers:** R-ENG, R-ARCH

1. **Code-Documentation Alignment**
   - Verify documentation matches current code
   - Check for outdated information
   - Validate examples and code snippets
   - Review version information

2. **Technical Accuracy**
   - Validate technical descriptions
   - Check for correct terminology
   - Review architectural diagrams
   - Validate configuration examples

**Gap Fix Prompts:**

```markdown
## Documentation Accuracy Gap Fix Prompt

**Gap ID:** [GAP_ID]  
**Type:** [Code Alignment/Technical/Version/Examples]  
**Severity:** [Critical/High/Medium/Low]  
**Document:** [Document Name]

### Gap Description
[Detailed description of accuracy gap]

### Impact Analysis
- **Affected Documentation:** [List of affected documents]
- **User Impact:** [Description of user impact]
- **Reconstruction Impact:** [Impact on 1:1 reconstruction]

### Fix Requirements
1. [Specific fix requirement 1]
2. [Specific fix requirement 2]
3. [Specific fix requirement 3]

### Team Review Requirements
- **R-LIB:** Review documentation quality
- **R-ENG:** Review technical accuracy
- **R-ARCH:** Review architectural accuracy

### Validation Criteria
- [ ] Documentation updated
- [ ] Technical accuracy validated
- [ ] All team members approved
- [ ] Examples tested if applicable
- [ ] Rebuild roadmap updated if needed

### Expected Output
- Updated documentation
- Validated examples
- Team approval record
```

---

### Step 4: Cross-Reference Validation

**Lead:** R-LIB  
**Reviewers:** R-RECON

1. **Link Validation**
   - Check all internal links work
   - Validate external links
   - Check for broken references
   - Validate file paths

2. **Reference Validation**
   - Validate role references (R-*)
   - Validate policy references (G-*)
   - Validate prompt references (P-*)
   - Validate task references (T-*)

**Gap Fix Prompts:**

```markdown
## Cross-Reference Gap Fix Prompt

**Gap ID:** [GAP_ID]  
**Type:** [Link/Role/Policy/Prompt/Task]  
**Severity:** [Critical/High/Medium/Low]  
**Document:** [Document Name]

### Gap Description
[Detailed description of cross-reference gap]

### Impact Analysis
- **Affected Documentation:** [List of affected documents]
- **Broken References:** [List of broken references]
- **User Impact:** [Description of user impact]

### Fix Requirements
1. [Specific fix requirement 1]
2. [Specific fix requirement 2]
3. [Specific fix requirement 3]

### Team Review Requirements
- **R-LIB:** Review reference corrections
- **R-RECON:** Review rebuild roadmap references

### Validation Criteria
- [ ] All links validated
- [ ] All references corrected
- [ ] All team members approved
- [ ] No broken references remain

### Expected Output
- Fixed references
- Validated links
- Team approval record
```

---

### Step 5: Governance Compliance Audit

**Lead:** R-LIB  
**Reviewers:** R-ENG, R-ARCH

1. **Policy Compliance**
   - Verify compliance with DOCUMENTATION_POLICY.md (G-06)
   - Verify compliance with PROMPT_GOVERNANCE_POLICY.md (G-03)
   - Check for policy violations
   - Validate governance procedures

2. **Process Compliance**
   - Verify documentation update procedures followed
   - Check for proper approvals
   - Validate audit trail
   - Review documentation maintenance

**Gap Fix Prompts:**

```markdown
## Governance Compliance Gap Fix Prompt

**Gap ID:** [GAP_ID]  
**Type:** [Policy/Process/Approval/Audit]  
**Severity:** [Critical/High/Medium/Low]  
**Document:** [Document Name]

### Gap Description
[Detailed description of governance compliance gap]

### Impact Analysis
- **Affected Documentation:** [List of affected documents]
- **Policy Violation:** [Specific policy violated]
- **Governance Impact:** [Description of governance impact]

### Fix Requirements
1. [Specific fix requirement 1]
2. [Specific fix requirement 2]
3. [Specific fix requirement 3]

### Team Review Requirements
- **R-LIB:** Review governance compliance
- **R-ENG:** Review process compliance
- **R-ARCH:** Review architectural documentation governance

### Validation Criteria
- [ ] Policy compliance achieved
- [ ] Process compliance validated
- [ ] All team members approved
- [ ] Audit trail complete
- [ ] Procedures updated if needed

### Expected Output
- Compliant documentation
- Updated procedures
- Complete audit trail
- Team approval record
```

---

### Step 6: Rebuild Roadmap Validation

**Lead:** R-RECON  
**Reviewers:** R-ENG, R-ARCH, R-LIB

1. **Prompt Currency**
   - Verify prompts reflect current code
   - Check for outdated prompts
   - Validate prompt dependencies
   - Review execution order

2. **Reconstruction Capability**
   - Validate 1:1 reconstruction capability
   - Test prompt execution
   - Validate prompt completeness
   - Check for missing prompts

**Gap Fix Prompts:**

```markdown
## Rebuild Roadmap Gap Fix Prompt

**Gap ID:** [GAP_ID]  
**Type:** [Prompt Currency/Dependencies/Execution Order/Completeness]  
**Severity:** [Critical/High/Medium/Low]  
**Prompt:** [Prompt ID]

### Gap Description
[Detailed description of rebuild roadmap gap]

### Impact Analysis
- **Affected Prompts:** [List of affected prompts]
- **Reconstruction Impact:** [Impact on 1:1 reconstruction]
- **User Impact:** [Description of user impact]

### Fix Requirements
1. [Specific fix requirement 1]
2. [Specific fix requirement 2]
3. [Specific fix requirement 3]

### Team Review Requirements
- **R-RECON:** Review rebuild roadmap impact
- **R-ENG:** Review technical accuracy
- **R-ARCH:** Review architectural accuracy
- **R-LIB:** Review documentation quality

### Validation Criteria
- [ ] Prompt updated
- [ ] Dependencies validated
- [ ] Execution order validated
- [ ] All team members approved
- [ ] Reconstruction capability maintained
- [ ] Visual guide updated if needed

### Expected Output
- Updated prompt
- Validated dependencies
- Team approval record
- Updated visual guide if needed
```

---

### Step 7: Visual Guide Validation

**Lead:** R-LIB  
**Reviewers:** R-RECON, R-ENG

1. **Guide Accuracy**
   - Verify visual guide matches documentation
   - Check for outdated information
   - Validate links to documentation
   - Review feature descriptions

2. **Guide Completeness**
   - Verify all phases documented
   - Check for missing features
   - Validate flow diagrams
   - Review role commands

**Gap Fix Prompts:**

```markdown
## Visual Guide Gap Fix Prompt

**Gap ID:** [GAP_ID]  
**Type:** [Accuracy/Completeness/Links/Features]  
**Severity:** [Critical/High/Medium/Low]  
**Section:** [Visual Guide Section]

### Gap Description
[Detailed description of visual guide gap]

### Impact Analysis
- **Affected Sections:** [List of affected sections]
- **User Impact:** [Description of user impact]
- **Documentation Impact:** [Impact on documentation]

### Fix Requirements
1. [Specific fix requirement 1]
2. [Specific fix requirement 2]
3. [Specific fix requirement 3]

### Team Review Requirements
- **R-LIB:** Review guide quality
- **R-RECON:** Review roadmap accuracy
- **R-ENG:** Review technical accuracy

### Validation Criteria
- [ ] Visual guide updated
- [ ] Links validated
- [ ] All team members approved
- [ ] Guide matches documentation

### Expected Output
- Updated visual guide
- Validated links
- Team approval record
```

---

### Step 8: Team Coordination and Approval

**Executor:** R-TASK

1. **Assign Reviews**
   - Assign each gap to appropriate team members
   - Provide context and requirements
   - Set review deadlines
   - Specify approval criteria

2. **Collect Feedback**
   - Gather team member inputs
   - Document concerns and suggestions
   - Identify conflicting requirements
   - Facilitate resolution

3. **Holistic Validation**
   - Ensure documentation changes are consistent
   - Validate cross-document dependencies
   - Check for unintended consequences
   - Validate rebuild capability

---

### Step 9: Fix Execution and Validation

**Executor:** R-TASK  
**Implementers:** R-LIB, R-RECON, R-ENG

1. **Execute Fix Prompts**
   - Execute prompts in appropriate order
   - Monitor for unintended consequences
   - Validate each fix before proceeding
   - Document all changes

2. **Holistic Validation**
   - Validate consistency across documentation
   - Ensure all team members approve
   - Validate rebuild capability
   - Validate visual guide accuracy

---

### Step 10: Documentation and Logging

**Executor:** R-TASK

1. **Audit Log**
   ```markdown
   ## Documentation Audit Execution Log

   **Audit ID:** [AUDIT_ID]  
   **Date:** [Date]  
   **Executor:** R-TASK  
   **Status:** [Status]

   ### Scope
   [Audit scope description]

   ### Documents Audited
   [List of audited documents]

   ### Team Members Involved
   - R-LIB: [Name] - [Contribution]
   - R-ENG: [Name] - [Contribution]
   - R-ARCH: [Name] - [Contribution]
   - R-RECON: [Name] - [Contribution]

   ### Gaps Identified
   1. [Gap 1] - [Severity] - [Type]
   2. [Gap 2] - [Severity] - [Type]

   ### Fix Prompts Generated
   [List of fix prompts]

   ### Changes Made
   [Description of changes]

   ### Validation Results
   [Validation results]

   ### Team Approvals
   - R-LIB: [Approved/Rejected] - [Comments]
   - R-ENG: [Approved/Rejected] - [Comments]
   - R-ARCH: [Approved/Rejected] - [Comments]
   - R-RECON: [Approved/Rejected] - [Comments]
   ```

2. **Documentation Updates**
   - Update relevant documentation
   - Update task registry if needed
   - Update roles-by-command reference
   - Update visual guide if needed

---

## Output Format

### Documentation Audit Summary Report

```markdown
## Documentation Audit Summary

**Audit ID:** [AUDIT_ID]  
**Date:** [Date]  
**Duration:** [Duration]  
**Status:** [Status]

### Executive Summary
[High-level summary of audit findings]

### Metrics
- **Documents Audited:** [Number]
- **Completeness Gaps:** [Number]
- **Accuracy Gaps:** [Number]
- **Cross-Reference Issues:** [Number]
- **Governance Violations:** [Number]
- **Rebuild Roadmap Issues:** [Number]
- **Visual Guide Issues:** [Number]
- **Critical Issues:** [Number]
- **High Priority Issues:** [Number]
- **Medium Priority Issues:** [Number]
- **Low Priority Issues:** [Number]

### Gaps by Severity
- **Critical:** [List]
- **High:** [List]
- **Medium:** [List]
- **Low:** [List]

### Fix Prompts Generated
[Links to or include fix prompts]

### Team Approvals
[Summary of team approvals]

### Next Steps
[Recommended next actions]
```

---

## Holistic Approach Requirements

### Cross-Documentation Validation
- Every documentation change must be examined for impact on other documents
- All team members must review from their perspective
- No change can proceed without team approval

### Dependency Mapping
- Map all documentation dependencies before making changes
- Identify all potentially affected documents
- Validate changes across all dependencies

### Synchronization
- All documentation changes must be synchronized
- Visual guide must match documentation
- Rebuild roadmap must reflect documentation
- Role prompts must be current

### Rebuild Roadmap Updates
- If documentation changes affect reconstruction, update relevant prompts
- R-RECON must validate rebuild capability
- Maintain 1:1 reconstruction capability

---

## References

- ROLE_ONGOING_TASK_EXECUTOR_USAGE_PROMPT.md (R-TASK)
- CODE_CHANGE_DOCUMENTATION_UPDATE_PROCEDURES.md (G-09)
- DOCUMENTATION_POLICY.md (G-06)
- PROMPT_GOVERNANCE_POLICY.md (G-03)
