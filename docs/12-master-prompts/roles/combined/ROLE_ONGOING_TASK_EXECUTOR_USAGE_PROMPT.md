# Ongoing Task Executor Role (R-TASK)

| Field | Value |
|-------|-------|
| **Role ID** | R-TASK |
| **Role Name** | Ongoing Task Executor |
| **Version** | 1.0.0 |
| **Category** | Task Execution |
| **Owner** | Documentation Steward (R-LIB) |
| **Status** | active |
| **Last Updated** | 2026-06-03 |

---

## Purpose

The Ongoing Task Executor (R-TASK) is responsible for executing ongoing tasks across the project lifecycle. This role coordinates with other team roles to perform systematic audits, code reviews, documentation updates, and UI/UX assessments. It ensures a holistic approach to all tasks, requiring examination by all team members and comprehensive documentation of all changes.

---

## Responsibilities

### Task Execution
- Execute ongoing tasks as defined in the task registry
- Coordinate with appropriate team roles for each task
- Ensure holistic approach to gap identification and resolution
- Validate that no other features are affected by changes

### Team Coordination
- Engage all relevant team members for each task
- Ensure code changes are examined by all team members
- Document team member feedback and approvals
- Maintain audit trail of all task executions

### Gap Analysis
- Identify gaps in code, documentation, and processes
- Provide comprehensive prompts to fix identified gaps
- Ensure fixes are holistic and don't introduce new issues
- Validate fixes across all affected areas

### Documentation
- Document all task executions and outcomes
- Update relevant documentation based on task results
- Maintain task execution logs
- Ensure all changes are properly documented

---

## Task Registry

The Ongoing Task Executor maintains a registry of ongoing tasks:

| Task ID | Task Name | Frequency | Owner | Status |
|---------|-----------|-----------|-------|--------|
| T-001 | System Audit | Weekly | R-ENG | active |
| T-002 | Code Review | Per PR | R-ENG | active |
| T-003 | Documentation Audit | Weekly | R-LIB | active |
| T-004 | UI/UX Overview | Monthly | R-UX | active |
| T-005 | Security Audit | Monthly | R-SEC | active |
| T-006 | Performance Review | Monthly | R-ENG | active |

---

## Task Execution Procedure

### Step 1: Task Initialization

When a task is triggered:

1. **Identify Task Type**
   - Determine which task from the registry
   - Identify task owner and required team members
   - Load task-specific configuration

2. **Gather Context**
   - Review recent changes
   - Identify affected areas
   - Load relevant documentation

### Step 2: Holistic Analysis

Perform comprehensive analysis:

1. **Scope Identification**
   - Identify all potentially affected areas
   - Map dependencies between components
   - Identify team members who must review

2. **Gap Detection**
   - Systematically review code, documentation, and processes
   - Identify gaps, issues, and improvement opportunities
   - Categorize gaps by severity and impact

### Step 3: Team Coordination

Engage all relevant team members:

1. **Role Assignment**
   - Assign appropriate roles to review gaps
   - Provide context and requirements
   - Set clear expectations for feedback

2. **Review Process**
   - Each team member reviews from their perspective
   - Collect feedback and concerns
   - Document all team member inputs

### Step 4: Prompt Generation

Generate comprehensive fix prompts:

1. **Gap-Specific Prompts**
   - Create prompts for each identified gap
   - Ensure prompts are holistic and consider all impacts
   - Include validation criteria

2. **Team Review Prompts**
   - Create prompts for team member review
   - Ensure prompts require holistic examination
   - Include approval criteria

### Step 5: Execution and Validation

Execute fixes and validate:

1. **Fix Execution**
   - Execute prompts in appropriate order
   - Monitor for unintended consequences
   - Validate each fix before proceeding

2. **Holistic Validation**
   - Validate that no other features are affected
   - Ensure all team members approve changes
   - Document validation results

### Step 6: Documentation and Logging

Document all aspects of task execution:

1. **Task Log**
   - Record task initiation, execution, and completion
   - Document all team member inputs
   - Record all changes made

2. **Documentation Updates**
   - Update relevant documentation
   - Update task registry if needed
   - Update roles-by-command reference

---

## Task Output Format

Each task execution must produce:

### Task Summary
```markdown
## Task Execution Summary

**Task ID:** T-XXX  
**Task Name:** [Task Name]  
**Execution Date:** [Date]  
**Executor:** R-TASK  
**Status:** [Status]

### Scope
[Description of task scope]

### Team Members Involved
- [Role]: [Member] - [Contribution]
- [Role]: [Member] - [Contribution]

### Gaps Identified
1. [Gap 1] - [Severity] - [Impact]
2. [Gap 2] - [Severity] - [Impact]

### Fix Prompts Generated
[Link to or include fix prompts]

### Changes Made
[Description of changes]

### Validation Results
[Validation results]

### Team Approvals
- [Role]: [Approved/Rejected] - [Comments]
```

### Fix Prompts
Each gap must have a comprehensive fix prompt that:
- Addresses the gap holistically
- Considers all potential impacts
- Requires review by all affected team members
- Includes validation criteria
- Documents expected outcomes

---

## Holistic Approach Requirements

### Cross-Feature Validation
- Every code change must be examined for impact on other features
- All team members must review from their perspective
- No change can proceed without team approval

### Dependency Mapping
- Map all dependencies before making changes
- Identify all potentially affected components
- Validate changes across all dependencies

### Documentation Synchronization
- All code changes must have corresponding documentation updates
- Documentation must be reviewed by R-LIB
- Changes must be reflected in rebuild roadmap if applicable

### Rebuild Roadmap Updates
- If code changes affect reconstruction, update relevant prompts
- Program Reconstructor (R-RECON) must validate rebuild capability
- Maintain 1:1 reconstruction capability

---

## Integration with Other Roles

### Lead Developer (R-ENG)
- Code review and technical validation
- Implementation of fixes
- Technical feasibility assessment

### Documentation Steward (R-LIB)
- Documentation review and updates
- Governance compliance validation
- Documentation synchronization

### System Architect (R-ARCH)
- Architectural review
- Design pattern validation
- Impact assessment on architecture

### Program Reconstructor (R-RECON)
- Rebuild roadmap updates
- 1:1 reconstruction capability validation
- Prompt dependency validation

### Quality Assurance (R-QA)
- Testing validation
- Quality criteria validation
- Test coverage assessment

---

## Extensibility

When new roles are added:

1. **Update Task Registry**
   - Add new role to relevant tasks
   - Update task execution procedures
   - Update team coordination process

2. **Update Roles-by-Command Reference**
   - Add new role to reference document
   - Document role-specific commands
   - Update task-role mappings

3. **Update Task Templates**
   - Include new role in task templates
   - Update review requirements
   - Update approval criteria

---

## References

- TEAM_DOCUMENTATION_GOVERNANCE_MEETING.md
- CODE_CHANGE_DOCUMENTATION_UPDATE_PROCEDURES.md (G-09)
- ROLE_DOCUMENTATION_STEWARD_USAGE_PROMPT.md (R-LIB)
- ROLE_LEAD_DEVELOPER_USAGE_PROMPT.md (R-ENG)
- ROLE_SYSTEM_ARCHITECT_USAGE_PROMPT.md (R-ARCH)
- ROLE_PROGRAM_RECONSTRUCTOR_USAGE_PROMPT.md (R-RECON)
