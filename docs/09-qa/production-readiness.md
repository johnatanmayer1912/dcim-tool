# Production Readiness & Doc-Sync Checklist

| Metadata | Description |
| :--- | :--- |
| **Purpose** | Mandatory verification protocol for ensuring code, documentation, and QA alignment before release. |
| **Scope** | All code changes, feature enhancements, and bug fixes impacting the production environment. |
| **Related Documents** | [LIBRARIAN Mandate](../00-overview/LIBRARIAN_MANDATE.md), [QA Strategy](qa-strategy.md) |
| **Update Responsibility** | QA Lead / LIBRARIAN |
| **Version Awareness** | v6.9.1 (NOC Dashboard Edition) |

---

## 📋 The Golden Rule

```
NO CODE CHANGE IS COMPLETE WITHOUT CORRESPONDING DOCUMENTATION UPDATES
```

Every feature, bugfix, or enhancement must update:
1. **Code** (obviously)
2. **Feature Documentation** (in `02_FEATURES/`)
3. **QA Tests** (in `03_QA_TESTING/`)
4. **Troubleshooting** (if applicable)
5. **This Checklist** (✓ each item)

---

## 🔍 Pre-Flight Checklist

### 1. Feature Identification
- [ ] Feature name: _________________________________
- [ ] Related modules: ____________________________
- [ ] Related files: ______________________________
- [ ] Breaking changes? ☐ Yes ☐ No
- [ ] New dependencies? ☐ Yes ☐ No

### 2. Code Changes
- [ ] Code implemented and tested locally
- [ ] No syntax errors (verified with `python -m py_compile`)
- [ ] Code follows project conventions
- [ ] Docstrings added/updated
- [ ] Comments explain complex logic
- [ ] No hardcoded credentials or secrets

### 3. Feature Documentation (MANDATORY)

#### If NEW Feature:
- [ ] Created relevant documentation in `00-overview/` to `05-ui-ux/`
- [ ] Created `README.md` in plugin folder (if plugin)
- [ ] Documented:
  - [ ] Feature description
  - [ ] User guide
  - [ ] Technical implementation details
  - [ ] API reference (if applicable)
  - [ ] Screenshots/diagrams (if UI feature)
- [ ] Created `changelog.md` entry template
- [ ] Updated `00-overview/project-overview.md`

#### If EXISTING Feature Update:
- [ ] Updated relevant documentation across all affected categories
- [ ] Documented changes in "Version History" section
- [ ] Updated any screenshots/diagrams
- [ ] Marked deprecated features (if applicable)

### 4. QA Testing Documentation (MANDATORY)

#### Test Prompt Creation:
- [ ] Updated `08-qa/regression-testing.md` or created new test in `08-qa/`
- [ ] Tests cover:
  - [ ] Happy path (normal operation)
  - [ ] Edge cases (empty input, large data, etc.)
  - [ ] Error handling (invalid input, network failures)
  - [ ] UI/UX (if applicable)
  - [ ] Integration with other features
- [ ] Tests include:
  - [ ] Step-by-step procedures
  - [ ] Expected results
  - [ ] Verification criteria
  - [ ] Device/platform coverage

#### Test Execution:
- [ ] All tests executed locally
- [ ] All tests passed ☐ Yes ☐ No (explain failures)
- [ ] Screenshots captured (if UI changes)
- [ ] Performance metrics recorded (if relevant)

### 5. Troubleshooting Updates (if applicable)
- [ ] New error scenarios documented in `07-operations/diagnostics.md`
- [ ] Updated `07-operations/TS_ERROR_INDEX.md` with new error codes
- [ ] Added solutions to known issues
- [ ] Updated FAQ (if user-facing)

### 6. Architecture Documentation (if applicable)
- [ ] Updated `01-architecture/system-architecture.md` (if major change)
- [ ] Updated `02-codebase/module-breakdown.md` (if module changes)
- [ ] Updated `10-reference/api-reference.md` (if API changes)
- [ ] Updated diagrams (if structural changes)

### 7. Rebuild Procedures (if applicable)
- [ ] Updated `06-build-rebuild/build-process.md` (if build process changes)
- [ ] Updated `10-reference/dependency-reference.md` (if new dependencies)
- [ ] Updated `06-build-rebuild/exact-rebuild-procedure.md` (if recovery steps change)
- [ ] Tested rebuild procedure from scratch

### 8. Release Documentation (if version change)
- [ ] Updated root `CHANGELOG.md` and `09-release-notes/changelog.md`
- [ ] Updated `VERSION` file
- [ ] Created `09-release-notes/release-history.md` entry
- [ ] Updated `README.md` (if major features)

### 9. Cross-References
- [ ] Added links between related documents
- [ ] Updated `docs/README.md` index (if new sections)
- [ ] Checked for broken links
- [ ] Verified all internal references

### 10. Final Review
- [ ] Read all updated docs aloud (catches awkward phrasing)
- [ ] Spell check performed
- [ ] Formatting consistent
- [ ] Code blocks tested (copy-paste and run)
- [ ] No placeholder text ("TODO", "FIXME", "XXX")

---

## 📝 Quick Reference: What to Update

### By Change Type

| Change Type | Must Update |
|-------------|-------------|
| **New Feature** | Feature doc, QA tests, Architecture index, Changelog |
| **Bug Fix** | Feature doc (note fix), Troubleshooting (if user-visible), Changelog |
| **UI Change** | Feature doc, QA tests (screenshots), User guide |
| **API Change** | API reference, Feature doc, Architecture doc |
| **Device Support** | Device matrix, Feature docs, QA tests |
| **Dependency** | Recovery docs, Build procedures, Architecture |
| **Performance** | Feature doc (benchmarks), QA tests |
| **Security** | Feature doc, Troubleshooting, Recovery |

### By Module

| Module | Primary Doc Location | Secondary Updates |
|--------|---------------------|-------------------|
| `vlan_audit.py` | `02_FEATURES/VLAN_AUDIT/` | QA tests, API ref |
| `vlan_mgmt.py` | `02_FEATURES/VLAN_MANAGEMENT/` | QA tests, Recovery |
| `mac_trace.py` | `02_FEATURES/MAC_TRACE/` | QA tests, Troubleshooting |
| `topology_mapper.py` | `02_FEATURES/TOPOLOGY/` | QA tests, Screenshots |
| `cli_manager.py` | `02_FEATURES/CLI_TERMINAL/` | QA tests, Security |
| `vlan_checker_web.py` | `02_FEATURES/WEB_INTERFACE/` | QA tests, UI/UX |

---

## 🔄 Documentation Update Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Code Change │────→│ Doc Update  │────→│ QA Prompts  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       ↓                   ↓                   ↓
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Review    │←────│  Cross-ref  │←────│   Review    │
└─────────────┘     └─────────────┘     └─────────────┘
       │
       ↓
┌─────────────┐
│   Submit    │
│     PR      │
└─────────────┘
```

---

## ✅ Sign-Off Section

**Developer:** _________________________________  **Date:** ___________

**Changes Summary:**
```
[Write 2-3 sentences describing what changed and why]
```

**Documentation Impact:**
- [ ] No documentation changes needed (explain why)
- [ ] Minor documentation updates only
- [ ] Significant documentation updates required
- [ ] New feature documentation created

**QA Test Results:**
- Tests written: ☐ Yes ☐ No
- Tests executed: ☐ Yes ☐ N/A
- Pass rate: _____/_____ (_____%)

**Checklist Completed:**
- [ ] I have verified all documentation is accurate
- [ ] I have tested all code examples in documentation
- [ ] I have cross-referenced all related documents
- [ ] I understand that incomplete docs = rejected PR

**Signature:** _________________________________

---

## 🚨 Common Mistakes (AVOID THESE)

### ❌ Common Failures
1. **"The code is self-documenting"** - No, it's not. Write docs.
2. **"I'll update docs later"** - No, you won't. Do it now.
3. **"Only changed one line"** - Still needs doc update if behavior changed.
4. **"Tests passed, so it's fine"** - Passing tests ≠ documented feature.
5. **"Copy-pasted from old version"** - Update version numbers and dates.

### ✅ Success Patterns
1. **Write docs first** - TDD for documentation
2. **Use templates** - Copy from `02_FEATURES/TEMPLATE.md`
3. **Include examples** - Show, don't just tell
4. **Test your examples** - Copy-paste and verify
5. **Reviewer's perspective** - Will they understand this?

---

## 🎯 Quick Checks (Before Submitting)

Run these commands:

```bash
# 1. Syntax check all Python files
python -m py_compile modules/*.py utils/*.py *.py

# 2. Check for TODO/FIXME in docs
grep -r "TODO\|FIXME\|XXX" docs/

# 3. Verify all internal links
grep -r "\.md)" docs/ | grep -v "http"

# 4. Check version consistency
grep -r "5\.0" docs/ | head -20
```

---

## 📞 Need Help?

**Documentation Questions:**
- Check `02_FEATURES/TEMPLATE.md` for structure
- Check existing feature docs for examples
- Ask in #documentation Slack channel

**QA Test Questions:**
- Check `03_QA_TESTING/TEMPLATE.md`
- Review `MASTER_QA_SUITE.md` for patterns
- Ask QA Lead for review

**Emergency:** If you're stuck, document what you tried and why it didn't work. Better to have incomplete docs with context than no docs at all.

---

**Remember:** Documentation debt compounds faster than technical debt. Update docs NOW.

---

*Version: 5.0.0*  
*Last Review: 2026-04-19*  
*Next Review: 2026-05-19*
