# Task T-001: System Audit

| Field | Value |
|-------|-------|
| **Task ID** | T-001 |
| **Task Name** | System Audit |
| **Frequency** | Weekly |
| **Owner** | Lead Developer (R-ENG) |
| **Executor** | Ongoing Task Executor (R-TASK) |
| **Status** | active |
| **Last Updated** | 2026-06-03 |
| **Version** | 1.0.0 |

---

## Purpose

Execute comprehensive system audit to identify gaps, issues, and improvement opportunities across code, documentation, and processes. This task ensures holistic review requiring examination by all team members.

---

## Scope

The system audit covers:
- Code quality and consistency
- Documentation completeness and accuracy
- Process compliance and efficiency
- Security vulnerabilities
- Performance bottlenecks
- Test coverage
- Cross-feature dependencies
- Rebuild roadmap validity

---

## Execution Procedure

### Step 1: Audit Initialization

**Executor:** R-TASK

1. **Gather Context**
   - Review recent changes since last audit
   - Identify modified files and components
   - Load relevant documentation
   - Check for new features or deprecations

2. **Define Audit Scope**
   - Identify all components to audit
   - Map dependencies between components
   - Determine team members required for review
   - Set audit criteria and thresholds

---

### Step 2: Code Audit

**Lead:** R-ENG  
**Reviewers:** R-ARCH, R-QA, R-RECON

1. **Code Quality Review**
   - Check code consistency and style
   - Review for potential bugs
   - Validate error handling
   - Check for deprecated patterns

2. **Dependency Analysis**
   - Map all code dependencies
   - Identify circular dependencies
   - Check for unused imports
   - Validate dependency versions

3. **Security Review**
   - Check for security vulnerabilities
   - Validate input sanitization
   - Review authentication/authorization
   - Check for hardcoded credentials

**Gap Fix Prompts:**

```markdown
## Code Gap Fix Prompt

**Gap ID:** [GAP_ID]  
**Type:** [Code Quality/Security/Performance]  
**Severity:** [Critical/High/Medium/Low]  
**Component:** [Component Name]

### Gap Description
[Detailed description of the gap]

### Impact Analysis
- **Affected Components:** [List of affected components]
- **Potential Risks:** [List of potential risks]
- **User Impact:** [Description of user impact]

### Fix Requirements
1. [Specific fix requirement 1]
2. [Specific fix requirement 2]
3. [Specific fix requirement 3]

### Team Review Requirements
- **R-ENG:** Review technical implementation
- **R-ARCH:** Review architectural impact
- **R-QA:** Review test coverage
- **R-SEC:** Review security implications
- **R-RECON:** Review rebuild roadmap impact

### Validation Criteria
- [ ] Fix implemented correctly
- [ ] No other features affected
- [ ] All team members approved
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Rebuild roadmap updated if needed

### Expected Output
- Fixed code
- Updated tests
- Updated documentation
- Team approval record
- Validation results
```

---

### Step 3: Documentation Audit

**Lead:** R-LIB  
**Reviewers:** R-ENG, R-ARCH, R-RECON

1. **Completeness Check**
   - Verify all documented features exist
   - Check for undocumented features
   - Validate API documentation
   - Review code comments

2. **Accuracy Validation**
   - Verify documentation matches code
   - Check for outdated information
   - Validate examples and code snippets
   - Review version information

3. **Cross-Reference Validation**
   - Check all links work
   - Validate role references
   - Validate policy references
   - Check for broken references

**Gap Fix Prompts:**

```markdown
## Documentation Gap Fix Prompt

**Gap ID:** [GAP_ID]  
**Type:** [Completeness/Accuracy/Cross-Reference]  
**Severity:** [Critical/High/Medium/Low]  
**Document:** [Document Name]

### Gap Description
[Detailed description of the gap]

### Impact Analysis
- **Affected Documents:** [List of affected documents]
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
- [ ] Documentation updated
- [ ] Cross-references validated
- [ ] All team members approved
- [ ] Rebuild roadmap updated if needed
- [ ] Visual guide updated if needed

### Expected Output
- Updated documentation
- Validated cross-references
- Team approval record
- Updated visual guide if needed
```

---

### Step 4: Process Audit

**Lead:** R-LIB  
**Reviewers:** R-ENG, R-QA

1. **Process Compliance**
   - Review adherence to policies
   - Check documentation update procedures
   - Validate code review process
   - Review testing procedures

2. **Efficiency Assessment**
   - Identify process bottlenecks
   - Review automation opportunities
   - Check for redundant steps
   - Assess workflow efficiency

**Gap Fix Prompts:**

```markdown
## Process Gap Fix Prompt

**Gap ID:** [GAP_ID]  
**Type:** [Compliance/Efficiency/Automation]  
**Severity:** [Critical/High/Medium/Low]  
**Process:** [Process Name]

### Gap Description
[Detailed description of the gap]

### Impact Analysis
- **Affected Processes:** [List of affected processes]
- **Team Impact:** [Description of team impact]
- **Efficiency Impact:** [Description of efficiency impact]

### Fix Requirements
1. [Specific fix requirement 1]
2. [Specific fix requirement 2]
3. [Specific fix requirement 3]

### Team Review Requirements
- **R-LIB:** Review process documentation
- **R-ENG:** Review technical feasibility
- **R-QA:** Review quality impact

### Validation Criteria
- [ ] Process updated
- [ ] Team trained on new process
- [ ] All team members approved
- [ ] Documentation updated
- [ ] Policy updated if needed

### Expected Output
- Updated process documentation
- Updated policies
- Team training materials
- Team approval record
```

---

### Step 5: Team Coordination and Review

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
   - Ensure no other features affected
   - Validate cross-feature dependencies
   - Check for unintended consequences
   - Validate rebuild capability

---

### Step 6: Fix Execution and Validation

**Executor:** R-TASK  
**Implementers:** R-ENG, R-LIB, R-ARCH

1. **Execute Fix Prompts**
   - Execute prompts in appropriate order
   - Monitor for unintended consequences
   - Validate each fix before proceeding
   - Document all changes

2. **Holistic Validation**
   - Validate no other features affected
   - Ensure all team members approve
   - Validate rebuild capability
   - Run comprehensive tests

---

### Step 7: Documentation and Logging

**Executor:** R-TASK

1. **Task Log**
   ```markdown
   ## System Audit Execution Log

   **Audit ID:** [AUDIT_ID]  
   **Date:** [Date]  
   **Executor:** R-TASK  
   **Status:** [Status]

   ### Scope
   [Audit scope description]

   ### Team Members Involved
   - R-ENG: [Name] - [Contribution]
   - R-LIB: [Name] - [Contribution]
   - R-ARCH: [Name] - [Contribution]
   - R-QA: [Name] - [Contribution]
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
   - R-ENG: [Approved/Rejected] - [Comments]
   - R-LIB: [Approved/Rejected] - [Comments]
   - R-ARCH: [Approved/Rejected] - [Comments]
   - R-QA: [Approved/Rejected] - [Comments]
   - R-RECON: [Approved/Rejected] - [Comments]
   ```

2. **Documentation Updates**
   - Update relevant documentation
   - Update task registry if needed
   - Update roles-by-command reference
   - Update visual guide if needed

---

## Output Format

### Audit Summary Report

```markdown
## System Audit Summary

**Audit ID:** [AUDIT_ID]  
**Date:** [Date]  
**Duration:** [Duration]  
**Status:** [Status]

### Executive Summary
[High-level summary of audit findings]

### Metrics
- **Code Gaps Found:** [Number]
- **Documentation Gaps Found:** [Number]
- **Process Gaps Found:** [Number]
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

### Cross-Feature Validation
- Every fix must be examined for impact on other features
- All team members must review from their perspective
- No fix can proceed without team approval

### Dependency Mapping
- Map all dependencies before making changes
- Identify all potentially affected components
- Validate changes across all dependencies

### Documentation Synchronization
- All code changes must have corresponding documentation updates
- Documentation must be reviewed by R-LIB
- Changes must be reflected in rebuild roadmap if applicable

### Rebuild Roadmap Updates
- If changes affect reconstruction, update relevant prompts
- R-RECON must validate rebuild capability
- Maintain 1:1 reconstruction capability

---

## References

- ROLE_ONGOING_TASK_EXECUTOR_USAGE_PROMPT.md (R-TASK)
- CODE_CHANGE_DOCUMENTATION_UPDATE_PROCEDURES.md (G-09)
- TEAM_DOCUMENTATION_GOVERNANCE_MEETING.md
