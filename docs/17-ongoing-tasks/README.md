# Ongoing Tasks

## Overview

This directory contains ongoing task prompts for systematic program maintenance and improvement. Each task prompt defines a structured procedure for conducting specific types of reviews, audits, or planning activities.

## Task Prompts

| Task ID | Task Name | Frequency | Owner | Status | Last Updated |
|---------|-----------|-----------|-------|--------|--------------|
| T-001 | System Audit | Weekly | R-ENG | Active | 2026-06-03 |
| T-002 | Code Review | Per Pull Request | R-ENG | Active | 2026-06-03 |
| T-003 | Documentation Audit | Weekly | R-LIB | Active | 2026-06-03 |
| T-004 | UI/UX Overview | Monthly | R-UX | Active | 2026-06-03 |
| T-005 | Improvement and Next Steps Planning | Monthly | R-ENG | Active | 2026-06-04 |

## Task Descriptions

### T-001: System Audit
Comprehensive system audit to identify gaps, issues, and improvement opportunities across code, documentation, and processes. Ensures holistic review requiring examination by all team members.

**Scope:**
- Code quality and consistency
- Documentation completeness and accuracy
- Process compliance and efficiency
- Security vulnerabilities
- Performance bottlenecks
- Test coverage
- Cross-feature dependencies
- Rebuild roadmap validity

**Executor:** R-TASK (Ongoing Task Executor)

### T-002: Code Review
Holistic code review requiring all team members to review from their perspective. Ensures no other features are affected and generates comprehensive fix prompts for identified issues.

**Scope:**
- Code quality and style
- Architectural consistency
- Security implications
- Performance impact
- Test coverage
- Documentation updates
- Cross-feature dependencies
- Rebuild roadmap impact

**Executor:** R-TASK (Ongoing Task Executor)

### T-003: Documentation Audit
Audit documentation for completeness, accuracy, and governance compliance. Validates cross-references and links. Generates update prompts for identified gaps with holistic team review.

**Scope:**
- Documentation completeness
- Accuracy and currency
- Cross-reference validation
- Governance compliance
- Rebuild roadmap validity
- Visual guide accuracy
- Role prompt currency
- Policy compliance

**Executor:** R-TASK (Ongoing Task Executor)

### T-004: UI/UX Overview
Comprehensive UI/UX assessment focusing on usability, accessibility, and design consistency. Generates improvement prompts with holistic team review requirements.

**Scope:**
- Usability assessment
- Accessibility compliance
- Design consistency
- User experience flows
- Responsive design
- Performance perception
- Visual hierarchy
- Error handling UX
- Feedback mechanisms

**Executor:** R-TASK (Ongoing Task Executor)

### T-005: Improvement and Next Steps Planning
Conduct comprehensive team meeting for continuous improvement and next steps planning. Each role in their professional field analyzes current state, researches industry best practices via internet, and proposes prioritized improvements across all program aspects.

**Scope:**
- UI/UX enhancements and modernization
- Feature development and prioritization
- Code structure and architecture improvements
- Documentation completeness and quality
- Role and prompt optimization
- Process efficiency and automation
- Technology stack evaluation
- Security enhancements
- Performance optimization
- Testing strategy improvements
- DevOps and deployment improvements
- User feedback integration
- Industry best practices adoption

**Executor:** R-TASK (Ongoing Task Executor)

**Key Feature:** Each role must conduct internet research to become more professional in their field and identify industry best practices.

## Execution Model

All ongoing tasks follow a consistent execution model:

1. **Initialization** - Gather context and define scope
2. **Assessment/Review** - Conduct specific review or analysis
3. **Gap Identification** - Identify issues and improvement opportunities
4. **Team Coordination** - Assign reviews and collect feedback
5. **Fix/Improvement Execution** - Execute prompts in appropriate order
6. **Validation** - Holistic validation with team approval
7. **Documentation and Logging** - Log execution and update documentation

## Holistic Approach

All ongoing tasks require:
- **Cross-feature validation** - Every change examined for impact on other features
- **Team perspective review** - All team members review from their professional perspective
- **Team approval required** - No change proceeds without team consensus
- **Dependency mapping** - Map all dependencies before making changes
- **Documentation synchronization** - All changes have corresponding documentation updates
- **Rebuild roadmap maintenance** - Maintain 1:1 reconstruction capability

## References

- ROLE_ONGOING_TASK_EXECUTOR_USAGE_PROMPT.md (R-TASK) - Executor role prompt
- CODE_CHANGE_DOCUMENTATION_UPDATE_PROCEDURES.md (G-09) - Documentation update procedures
- TEAM_DOCUMENTATION_GOVERNANCE_MEETING.md - Team meeting governance
- DOCUMENTATION_MASTER_INDEX.md - Documentation navigation index

## Task Execution Order

For comprehensive program maintenance, execute tasks in this order:

1. **Weekly:** T-001 (System Audit) → T-003 (Documentation Audit)
2. **Per Pull Request:** T-002 (Code Review)
3. **Monthly:** T-004 (UI/UX Overview) → T-005 (Improvement and Next Steps Planning)

## Output Location

All task execution logs and outputs should be stored in:
- `.cursor/audits/` — living agent logs + current GAP / product registers (see that folder README)
- `docs/12-master-prompts/action-logs/` - Role invocation logs

## Version Control

- All task prompts are versioned
- Changes to task prompts require team approval
- Task prompt versions tracked in changelog
- Archive old versions in `docs/12-master-prompts/archive/`
