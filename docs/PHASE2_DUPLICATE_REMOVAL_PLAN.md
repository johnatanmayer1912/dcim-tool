# Phase 2: Duplicate Removal Plan for docs/ Folder

## Purpose

This plan defines the systematic approach to remove duplicate information from all 600+ markdown files in the docs/ folder and establish single source of truth principles.

## Current State

- **Total Folders**: 21 (00-20 + rebuilt-1-1)
- **Total Files**: 600+ markdown files
- **Phase 1 Completed**: Folder structure reorganized, README files created

## Challenge

The scale of this task (600+ files) requires a systematic, prioritized approach rather than attempting to process all files at once.

## Strategy: Prioritized Batch Processing

### Priority 1: Core Documentation Files (Meta Files)
These files define the documentation structure and should be processed first:

1. `docs/README.md` - Main docs entry point
2. `docs/DOCUMENTATION_MASTER_INDEX.md` - Master index
3. `docs/DOCUMENTATION_MAINTENANCE_GUIDE.md` - Maintenance guide
4. `docs/DOCS_CANONICAL_MAP.md` - Canonical mapping
5. `docs/DOCUMENTATION_TRUTH_AUDIT_2026-06-10.md` - Truth audit
6. `docs/DOCUMENTATION_VALIDATION_CHECKLIST.md` - Validation checklist
7. `docs/COMPREHENSIVE_DOCS_ORGANIZATION_PLAN.md` - Organization plan
8. `docs/skill-improvement-process.md` - Skill improvement process

### Priority 2: Folder-Level README Files
Each folder's README should be the single source of truth for that folder's overview:

- `docs/00-overview/README.md`
- `docs/01-architecture/README.md`
- `docs/02-codebase/README.md`
- `docs/03-infrastructure/README.md`
- `docs/04-automation/README.md`
- `docs/05-plugins/README.md`
- `docs/06-ui-ux/README.md`
- `docs/07-operations/README.md`
- `docs/08-security/README.md`
- `docs/09-qa/README.md`
- `docs/10-rebuild/README.md`
- `docs/11-reference/README.md`
- `docs/12-master-prompts/README.md`
- `docs/13-bug-reports/README.md`
- `docs/14-roadmap/README.md`
- `docs/15-visual-guide/README.md`
- `docs/16-roles-by-command/README.md`
- `docs/17-ongoing-tasks/README.md`
- `docs/18-interface-management/README.md`
- `docs/19-recovery/README.md`
- `docs/20-release-management/README.md`
- `docs/rebuilt-1-1/README.md`

### Priority 3: High-Value Individual Files
Files that contain critical information and are frequently referenced:

**00-overview/**
- `project-overview.md`
- `roadmap.md`

**01-architecture/**
- `system-architecture.md`
- `MODULE_ARCHITECTURE.md`

**02-codebase/**
- `CODE_INVENTORY.md`
- `API_DOCUMENTATION.md`

**12-master-prompts/**
- `INDEX_PROMPT.md`
- `GLOBAL_MASTER_PROMPT_RULES.md`

### Priority 4: Remaining Files
Process remaining files systematically by folder, starting with smaller folders and moving to larger ones.

## Single Source of Truth Principles for docs/

### Information Ownership by Category

#### Program Overview
- **Primary Source**: `docs/00-overview/README.md`
- **Secondary**: `docs/00-overview/project-overview.md` (detailed)

#### Architecture
- **Primary Source**: `docs/01-architecture/system-architecture.md`
- **Secondary**: `docs/01-architecture/MODULE_ARCHITECTURE.md` (detailed)

#### Codebase
- **Primary Source**: `docs/02-codebase/CODE_INVENTORY.md`
- **Secondary**: `docs/02-codebase/API_DOCUMENTATION.md` (detailed)

#### Infrastructure
- **Primary Source**: `docs/03-infrastructure/README.md`
- **Secondary**: Individual infrastructure files

#### Automation
- **Primary Source**: `docs/04-automation/README.md`
- **Secondary**: `.devin/workflows/` (detailed)

#### Plugins
- **Primary Source**: `docs/05-plugins/README.md`
- **Secondary**: Individual plugin READMEs

#### UI/UX
- **Primary Source**: `docs/06-ui-ux/README.md`
- **Secondary**: Individual UI/UX files

#### Operations
- **Primary Source**: `docs/07-operations/README.md`
- **Secondary**: Individual operations files

#### Security
- **Primary Source**: `docs/08-security/README.md`
- **Secondary**: Individual security files

#### QA
- **Primary Source**: `docs/09-qa/README.md`
- **Secondary**: Individual QA files

#### Rebuild
- **Primary Source**: `docs/10-rebuild/README.md`
- **Secondary**: `docs/rebuilt-1-1/automatic-processes.md` (context)

#### Reference
- **Primary Source**: `docs/11-reference/README.md`
- **Secondary**: Individual reference files

#### Master Prompts
- **Primary Source**: `docs/12-master-prompts/INDEX_PROMPT.md`
- **Secondary**: Individual role prompts

#### Bug Reports
- **Primary Source**: `docs/13-bug-reports/README.md`
- **Secondary**: Individual bug reports

#### Roadmap
- **Primary Source**: `docs/14-roadmap/README.md`
- **Secondary**: Individual roadmap files

#### Visual Guide
- **Primary Source**: `docs/15-visual-guide/README.md`
- **Secondary**: Individual visual files

#### Roles by Command
- **Primary Source**: `docs/16-roles-by-command/README.md`
- **Secondary**: Individual role files

#### Ongoing Tasks
- **Primary Source**: `docs/17-ongoing-tasks/README.md`
- **Secondary**: Individual task files

#### Interface Management
- **Primary Source**: `docs/18-interface-management/README.md`
- **Secondary**: Individual interface files

#### Recovery
- **Primary Source**: `docs/19-recovery/README.md`
- **Secondary**: Individual recovery files

#### Release Management
- **Primary Source**: `docs/20-release-management/README.md`
- **Secondary**: Individual release files

## Implementation Steps

### Step 1: Process Priority 1 (Meta Files)
- Review each meta file
- Identify duplicates with other meta files
- Establish single source of truth
- Add cross-references
- Update related documentation sections

### Step 2: Process Priority 2 (Folder READMEs)
- Review each folder README
- Ensure no duplicates with other folder READMEs
- Establish single source of truth for folder overview
- Add cross-references to related folders
- Update related documentation sections

### Step 3: Process Priority 3 (High-Value Files)
- Review each high-value file
- Identify duplicates with other files
- Establish single source of truth
- Add cross-references
- Update related documentation sections

### Step 4: Process Priority 4 (Remaining Files)
- Process remaining files systematically by folder
- Start with smaller folders (fewer files)
- Move to larger folders (more files)
- Apply single-source-of-truth principles
- Add cross-references

## Cross-Reference Guidelines

### When to Reference vs. Duplicate

**Reference (Link) when:**
- Information is detailed in another file
- Information is the authoritative source
- Information is implementation detail

**Duplicate when:**
- Information is a high-level summary needed for context
- Information is essential for understanding the current file
- Information is a brief overview (not detailed)

### Reference Format

```markdown
See `[DOCUMENT_PATH]` for details
```

## Validation

After each batch of files is processed, validate:
- No duplicate detailed information
- Each piece of information has one primary source
- Cross-references are accurate
- Related documentation sections are updated

## Success Criteria

- **Canonical Numbering**: All folders use consistent numbering (00-20)
- **Single Source of Truth**: Each piece of information has one primary source
- **No Duplicates**: Duplicate information removed or consolidated
- **Cross-References**: All files have proper cross-references
- **README Files**: Each folder has comprehensive README
- **Enterprise Quality**: Documentation meets enterprise standards

## Related Documentation

- `docs/COMPREHENSIVE_DOCS_ORGANIZATION_PLAN.md` - Overall organization plan
- `.devin/DOCUMENTATION_STRUCTURE.md` - .devin documentation structure
- `docs/DOCUMENTATION_MASTER_INDEX.md` - Documentation master index
