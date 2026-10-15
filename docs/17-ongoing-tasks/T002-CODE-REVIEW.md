# Task T-002: Code Review

| Field | Value |
|-------|-------|
| **Task ID** | T-002 |
| **Task Name** | Code Review |
| **Frequency** | Per Pull Request |
| **Owner** | Lead Developer (R-ENG) |
| **Executor** | Ongoing Task Executor (R-TASK) |
| **Status** | active |
| **Last Updated** | 2026-06-03 |
| **Version** | 1.0.0 |

---

## Purpose

Execute holistic code review requiring all team members to review from their perspective. Ensures no other features are affected and generates comprehensive fix prompts for identified issues.

---

## Scope

The code review covers:
- Code quality and style
- Architectural consistency
- Security implications
- Performance impact
- Test coverage
- Documentation updates
- Cross-feature dependencies
- Rebuild roadmap impact

---

## Execution Procedure

### Step 1: Review Initialization

**Executor:** R-TASK

1. **Gather Context**
   - Load pull request details
   - Review changed files
   - Identify affected components
   - Map dependencies

2. **Define Review Scope**
   - Identify all components affected
   - Determine team members required
   - Set review criteria
   - Establish approval requirements

---

### Step 2: Technical Review

**Lead:** R-ENG  
**Reviewers:** R-ARCH, R-QA, R-SEC, R-RECON

1. **Code Quality Assessment**
   - Review code style and consistency
   - Check for potential bugs
   - Validate error handling
   - Review for performance issues

2. **Architectural Review**
   - Validate design patterns
   - Check architectural consistency
   - Review module boundaries
   - Validate separation of concerns

3. **Security Review**
   - Check for security vulnerabilities
   - Validate input sanitization
   - Review authentication/authorization
   - Check for sensitive data exposure

**Gap Fix Prompts:**

```markdown
## Code Review Gap Fix Prompt

**Gap ID:** [GAP_ID]  
**PR ID:** [PR_ID]  
**Type:** [Code Quality/Architecture/Security/Performance]  
**Severity:** [Critical/High/Medium/Low]  
**Component:** [Component Name]

### Gap Description
[Detailed description of the gap found in code review]

### Impact Analysis
- **Affected Components:** [List of affected components]
- **Potential Risks:** [List of potential risks]
- **User Impact:** [Description of user impact]
- **Performance Impact:** [Description of performance impact]
- **Security Impact:** [Description of security impact]

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
- [ ] Performance validated
- [ ] Security validated

### Expected Output
- Fixed code
- Updated tests
- Updated documentation
- Team approval record
- Validation results
- Performance metrics
- Security assessment
```

---

### Step 3: Test Coverage Review

**Lead:** R-QA  
**Reviewers:** R-ENG, R-ARCH

1. **Coverage Assessment**
   - Review test coverage for changes
   - Identify untested code paths
   - Validate test quality
   - Check for integration tests

2. **Test Quality Review**
   - Review test assertions
   - Validate test isolation
   - Check for flaky tests
   - Review test performance

**Gap Fix Prompts:**

```markdown
## Test Coverage Gap Fix Prompt

**Gap ID:** [GAP_ID]  
**PR ID:** [PR_ID]  
**Type:** [Coverage/Quality/Integration]  
**Severity:** [Critical/High/Medium/Low]  
**Component:** [Component Name]

### Gap Description
[Detailed description of test coverage gap]

### Impact Analysis
- **Affected Components:** [List of affected components]
- **Risk of Regression:** [Description of regression risk]
- **Test Coverage Impact:** [Current coverage vs required coverage]

### Fix Requirements
1. [Specific fix requirement 1]
2. [Specific fix requirement 2]
3. [Specific fix requirement 3]

### Team Review Requirements
- **R-QA:** Review test implementation
- **R-ENG:** Review technical feasibility
- **R-ARCH:** Review architectural test coverage

### Validation Criteria
- [ ] Tests added/updated
- [ ] Coverage meets threshold (80%+)
- [ ] Tests are isolated and reliable
- [ ] All team members approved
- [ ] Integration tests added if needed

### Expected Output
- New/updated tests
- Coverage report
- Team approval record
```

---

### Step 4: Documentation Review

**Lead:** R-LIB  
**Reviewers:** R-ENG, R-RECON

1. **Documentation Assessment**
   - Review code documentation
   - Check for API documentation updates
   - Validate inline comments
   - Review architecture documentation

2. **Rebuild Roadmap Review**
   - Check if changes affect reconstruction
   - Validate prompt updates if needed
   - Review prompt dependencies
   - Validate execution order

**Gap Fix Prompts:**

```markdown
## Documentation Gap Fix Prompt

**Gap ID:** [GAP_ID]  
**PR ID:** [PR_ID]  
**Type:** [Code Documentation/API Documentation/Rebuild Roadmap]  
**Severity:** [Critical/High/Medium/Low]  
**Document:** [Document Name]

### Gap Description
[Detailed description of documentation gap]

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
- Updated rebuild roadmap if needed
```

---

### Step 5: Cross-Feature Impact Analysis

**Lead:** R-ARCH  
**Reviewers:** R-ENG, R-QA, R-RECON

1. **Dependency Mapping**
   - Map all dependencies of changes
   - Identify potentially affected features
   - Review integration points
   - Validate data flow

2. **Impact Assessment**
   - Assess impact on other features
   - Identify breaking changes
   - Review backward compatibility
   - Validate migration path if needed

**Gap Fix Prompts:**

```markdown
## Cross-Feature Impact Gap Fix Prompt

**Gap ID:** [GAP_ID]  
**PR ID:** [PR_ID]  
**Type:** [Dependency/Integration/Compatibility]  
**Severity:** [Critical/High/Medium/Low]  
**Affected Features:** [List of affected features]

### Gap Description
[Detailed description of cross-feature impact gap]

### Impact Analysis
- **Affected Components:** [List of affected components]
- **Breaking Changes:** [List of breaking changes]
- **Migration Required:** [Yes/No - details]
- **User Impact:** [Description of user impact]

### Fix Requirements
1. [Specific fix requirement 1]
2. [Specific fix requirement 2]
3. [Specific fix requirement 3]

### Team Review Requirements
- **R-ARCH:** Review architectural impact
- **R-ENG:** Review technical implementation
- **R-QA:** Review test coverage for affected features
- **R-RECON:** Review rebuild roadmap impact

### Validation Criteria
- [ ] Impact mitigated
- [ ] Migration path provided if needed
- [ ] All affected features tested
- [ ] All team members approved
- [ ] Documentation updated
- [ ] Rebuild roadmap updated if needed

### Expected Output
- Mitigated impact
- Migration guide if needed
- Updated tests for affected features
- Team approval record
```

---

### Step 6: Team Coordination and Approval

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

### Step 7: Fix Execution and Validation

**Executor:** R-TASK  
**Implementers:** R-ENG, R-LIB, R-ARCH, R-QA

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

### Step 8: Documentation and Logging

**Executor:** R-TASK

1. **Review Log**
   ```markdown
   ## Code Review Execution Log

   **Review ID:** [REVIEW_ID]  
   **PR ID:** [PR_ID]  
   **Date:** [Date]  
   **Executor:** R-TASK  
   **Status:** [Status]

   ### Scope
   [Review scope description]

   ### Changed Files
   [List of changed files]

   ### Team Members Involved
   - R-ENG: [Name] - [Contribution]
   - R-LIB: [Name] - [Contribution]
   - R-ARCH: [Name] - [Contribution]
   - R-QA: [Name] - [Contribution]
   - R-SEC: [Name] - [Contribution]
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
   - R-SEC: [Approved/Rejected] - [Comments]
   - R-RECON: [Approved/Rejected] - [Comments]

   ### PR Decision
   [Approved/Rejected/Request Changes]
   ```

2. **Documentation Updates**
   - Update relevant documentation
   - Update task registry if needed
   - Update roles-by-command reference
   - Update visual guide if needed

---

## Output Format

### Code Review Summary Report

```markdown
## Code Review Summary

**Review ID:** [REVIEW_ID]  
**PR ID:** [PR_ID]  
**Date:** [Date]  
**Duration:** [Duration]  
**Status:** [Status]

### Executive Summary
[High-level summary of review findings]

### Metrics
- **Files Changed:** [Number]
- **Lines Added:** [Number]
- **Lines Removed:** [Number]
- **Code Gaps Found:** [Number]
- **Test Coverage Gaps:** [Number]
- **Documentation Gaps:** [Number]
- **Cross-Feature Issues:** [Number]
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

### PR Decision
[Approved/Rejected/Request Changes with reasons]

### Next Steps
[Recommended next actions]
```

---

## Holistic Approach Requirements

### Cross-Feature Validation
- Every change must be examined for impact on other features
- All team members must review from their perspective
- No change can proceed without team approval

### Dependency Mapping
- Map all dependencies before approving changes
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
