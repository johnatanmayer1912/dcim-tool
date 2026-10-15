# Network Swiss Tool Pro - Operational Workflows

| Metadata | Description |
| :--- | :--- |
| **Purpose** | Guide for navigating documentation and executing common operational tasks by role. |
| **Scope** | Role-based navigation paths, common workflows (feature add, bug fix, recovery), and maintenance tasks. |
| **Related Documents** | [Project Overview](../00-overview/project-overview.md), [Troubleshooting Index](TS_ERROR_INDEX.md) |
| **Update Responsibility** | Tech Lead / Documentation Librarian |
| **Version Awareness** | v6.9.1 (NOC Dashboard Edition) |

---

## 🗺️ Documentation Map by Role

### 🆕 New Team Member
**Goal:** Get up to speed quickly

**Path:**
1. Start: `production-guidelines.md` ← You are here
2. Context: `../01-architecture/system-architecture.md`
3. Practice: `../03-automation/parsing-workflows.md`
4. Hands-on: Run local application
5. Deep dive: Pick learning path below

**Time:** 2-4 hours

---

### 👨‍💻 Feature Developer
**Goal:** Add new feature or modify existing

**Path:**
1. Start: `../09-qa/production-readiness.md` ← **MUST READ**
2. Template: `../04-plugins/plugin-development-template.md`
3. Example: `../03-automation/parsing-workflows.md` ← Reference
4. Tests: `../09-qa/ST_MASTER_QA_SUITE.md` ← Write tests
5. Recovery: `../06-build-rebuild/build-process.md` ← Test build

**Key Rule:** Every code change needs synchronized docs + tests

**Time:** 4-8 hours (including docs)

---

### 🧪 QA Engineer
**Goal:** Test features and ensure quality

**Path:**
1. Start: `../09-qa/qa-strategy.md` ← Testing guide
2. Master: `../09-qa/ST_MASTER_QA_SUITE.md` ← Test suite
3. Feature: `../09-qa/regression-testing.md` ← Specific tests
4. Readiness: `../09-qa/production-readiness.md`

**Key Rule:** No release without QA sign-off

**Time:** 2-3 hours (full suite)

---

### 🚨 DevOps / Emergency Recovery
**Goal:** Rebuild system from scratch

**Path:**
1. **URGENT:** `../06-build-rebuild/exact-rebuild-procedure.md` ← Start here
2. Setup: `../06-build-rebuild/environment-setup.md`
3. Build: `../06-build-rebuild/build-process.md`
4. Verify: `../09-qa/ST_MASTER_QA_SUITE.md`

**Target:** 90 minutes from zero to working system

**Time:** 90 minutes (if following procedure exactly)

---

### 📊 Release Manager
**Goal:** Prepare and ship new version

**Path:**
1. Start: `../09-release-notes/changelog.md`
2. Checklist: `../09-qa/production-readiness.md`
3. History: `../09-release-notes/release-history.md`
4. QA: `../09-qa/ST_MASTER_QA_SUITE.md`

**Deliverables:**
- Updated VERSION file
- Release notes document
- Updated changelog
- QA sign-off
- Build artifacts

**Time:** 2-4 hours

---

### 🔧 Support Engineer
**Goal:** Resolve user issues

**Path:**
1. Start: `TS_ERROR_INDEX.md` ← Search by error
2. Common: `troubleshooting.md`
3. Diagnostics: `diagnostics.md`
4. Architecture: `../01-architecture/system-architecture.md`

**Time:** 15-30 minutes per issue

---

## 🔄 Common Workflows

### Workflow 1: Adding a New Feature

```
Week 1: Planning
├── Read: SYSTEM_OVERVIEW.md
├── Read: TEMPLATE.md (copy for your feature)
├── Design: Architecture approval
└── Plan: QA test strategy

Week 2: Development
├── Code: Implement feature
├── Test: Local testing
├── Write: Feature documentation
├── Write: QA test prompts
└── Update: Architecture docs if needed

Week 3: Integration
├── Review: DOC_SYNC_CHECKLIST.md
├── Test: Full QA suite
├── Fix: Issues found
├── Build: Create executable
└── Deploy: Test environment

Week 4: Release
├── Write: Release notes
├── Update: Changelog
├── Final: QA sign-off
└── Ship: Production release
```

**Key Documents:**
- `DOC_SYNC_CHECKLIST.md` (check daily)
- `../02_FEATURES/TEMPLATE.md` (starting point)
- `../03_QA_TESTING/TEMPLATE.md` (testing)
- `../05_RECOVERY/BUILD_PROCEDURES.md` (build)

---

### Workflow 2: Fixing a Bug

```
Hour 1: Investigation
├── Reproduce: Confirm bug exists
├── Document: Error messages, logs
├── Search: error_index.md
└── Read: Feature documentation

Hour 2: Fix
├── Code: Implement fix
├── Test: Verify fix works
└── Test: Regression tests

Hour 3: Documentation
├── Update: Feature doc (note fix)
├── Update: Troubleshooting (if user-facing)
├── Write: QA test for this bug (prevent regression)
└── Complete: DOC_SYNC_CHECKLIST.md

Hour 4: Release
├── Build: Create patch version
├── Test: Quick smoke test
└── Deploy: Hotfix release
```

**Key Documents:**
- `../04_TROUBLESHOOTING/error_index.md`
- `DOC_SYNC_CHECKLIST.md`
- `../03_QA_TESTING/REGRESSION_TEST_PROMPTS.md`

---

### Workflow 3: Emergency Recovery

```
Minute 0-15: Environment
├── Follow: MASTER_RECOVERY.md Phase 1
├── Install: Python, dependencies
└── Verify: Environment ready

Minute 15-30: Source Code
├── Restore: From backup or git
├── Verify: All files present
└── Check: No syntax errors

Minute 30-45: Configuration
├── Create: VERSION, README
├── Test: Basic imports
└── Verify: Configuration complete

Minute 45-75: Build
├── Clean: Previous builds
├── Execute: PyInstaller
└── Verify: EXE created

Minute 75-90: Verification
├── Test: Launch application
├── Test: Core features
├── Test: QA smoke tests
└── Sign-off: Recovery complete
```

**Key Documents:**
- `../05_RECOVERY/MASTER_RECOVERY.md` (follow exactly)
- `../05_RECOVERY/BUILD_PROCEDURES.md`
- `../03_QA_TESTING/MASTER_QA_SUITE.md` (smoke tests)

**⚠️ CRITICAL:** Do not skip steps. Each checkpoint validates progress.

---

### Workflow 4: Version Release

```
Pre-Release (1 week before):
├── Review: All feature docs current
├── Execute: Full QA suite
├── Verify: All critical tests pass
├── Update: VERSION file
├── Write: RELEASE_NOTES_X.X.X.md
└── Update: CHANGELOG.md

Release Day:
├── Final: QA sign-off
├── Build: Production executable
├── Test: Smoke tests on build
├── Package: Distribution files
├── Tag: Git version tag
└── Deploy: Release to users

Post-Release:
├── Monitor: Error reports
├── Support: User questions
├── Document: Lessons learned
└── Plan: Next version features
```

**Key Documents:**
- `../06_RELEASES/RELEASE_NOTES_TEMPLATE.md`
- `DOC_SYNC_CHECKLIST.md` (version section)
- `../03_QA_TESTING/MASTER_QA_SUITE.md`
- `../05_RECOVERY/BUILD_PROCEDURES.md`

---

## 🔍 Finding Information Quickly

### By Error Message
1. Check `../04_TROUBLESHOOTING/error_index.md`
2. Search for error code or message
3. Follow linked troubleshooting guide

### By Feature Name
1. Go to `../02_FEATURES/`
2. Find folder matching feature
3. Read `README.md` in that folder

### By Device Type
1. Check `../01_ARCHITECTURE/DEVICE_SUPPORT.md`
2. Find your device platform
3. Follow links to platform-specific docs

### By Task Type
| Task | Start Here |
|------|-----------|
| Learn the system | `../00_START_HERE/ONBOARDING.md` |
| Fix a bug | `../04_TROUBLESHOOTING/error_index.md` |
| Add feature | `DOC_SYNC_CHECKLIST.md` + `../02_FEATURES/TEMPLATE.md` |
| Test application | `../03_QA_TESTING/MASTER_QA_SUITE.md` |
| Build release | `../05_RECOVERY/BUILD_PROCEDURES.md` |
| Emergency recovery | `../05_RECOVERY/MASTER_RECOVERY.md` |
| Understand architecture | `../01_ARCHITECTURE/SYSTEM_OVERVIEW.md` |

---

## 📋 Daily Development Checklist

### Morning (Planning)
- [ ] Review `DOC_SYNC_CHECKLIST.md` for today's work
- [ ] Check `../06_RELEASES/` for version context
- [ ] Read relevant `../02_FEATURES/` docs

### During Development
- [ ] Follow feature template structure
- [ ] Write code comments referencing docs
- [ ] Test incrementally

### Before Commit
- [ ] Run syntax checks
- [ ] Update feature documentation
- [ ] Add/update QA tests
- [ ] Complete checklist sign-off

### End of Day
- [ ] Update troubleshooting if issues found
- [ ] Log test results
- [ ] Plan tomorrow's work

---

## 🎓 Learning Paths

### Path A: New Developer (Week 1-4)

**Week 1: Orientation**
- Day 1: Read `ONBOARDING.md` + `SYSTEM_OVERVIEW.md`
- Day 2: Set up environment, run application
- Day 3: Explore all UI features
- Day 4: Read one complete feature doc
- Day 5: Make first documentation contribution

**Week 2: Deep Dive**
- Choose focus: Network automation / Full-stack / QA
- Study relevant modules
- Shadow experienced developer
- Fix documentation typo or small bug

**Week 3: First Feature**
- Take small feature or improvement
- Follow complete workflow
- Write docs + tests
- Get code review

**Week 4: Integration**
- Participate in QA testing
- Handle support question
- Mentor next new hire

---

### Path B: QA Engineer (Week 1-2)

**Week 1: Foundation**
- Day 1: Read `../03_QA_TESTING/README.md`
- Day 2: Study `MASTER_QA_SUITE.md` structure
- Day 3: Run existing tests manually
- Day 4: Write test for existing feature
- Day 5: Review test with QA Lead

**Week 2: Execution**
- Execute full test suite
- Document results
- Find and report bugs
- Improve test procedures

---

### Path C: DevOps (Week 1-2)

**Week 1: Build System**
- Day 1: Read `MASTER_RECOVERY.md`
- Day 2: Practice recovery procedure
- Day 3: Study `BUILD_PROCEDURES.md`
- Day 4: Create build from scratch
- Day 5: Optimize build process

**Week 2: Automation**
- Set up CI/CD pipeline
- Automate QA smoke tests
- Create deployment scripts
- Document infrastructure

---

## 🚨 Emergency Procedures

### Scenario: Documentation is Missing
1. Check `../08_HISTORY/` for archived docs
2. Check git history for deleted docs
3. Check `../05_RECOVERY/` for procedure docs
4. If completely missing: Follow MASTER_RECOVERY.md to reconstruct

### Scenario: Tests are Outdated
1. Check version in test file header
2. Compare with current feature code
3. Update test procedures
4. Re-run and validate
5. Update version history

### Scenario: Can't Find Information
1. Check this WORKFLOWS.md for path
2. Search error_index.md by keyword
3. Check MASTER-BRAIN.md for high-level overview
4. Ask in team Slack with specific question

---

## 📝 Documentation Maintenance

### Monthly Tasks
- [ ] Review `MASTER_RECOVERY.md` (test procedure)
- [ ] Update `CHANGELOG.md` with recent changes
- [ ] Archive old release notes to `../08_HISTORY/`
- [ ] Check for broken internal links

### Quarterly Tasks
- [ ] Review all feature docs for accuracy
- [ ] Update architecture diagrams
- [ ] Refresh troubleshooting guides
- [ ] Validate all QA tests still work

### Annual Tasks
- [ ] Complete documentation audit
- [ ] Reorganize if needed
- [ ] Update templates
- [ ] Train team on any changes

---

## 🎯 Success Metrics

**Good documentation usage:**
- ✅ New hire productive in < 2 days
- ✅ Bug fixes include doc updates
- ✅ QA tests pass > 95%
- ✅ Recovery completed in < 90 minutes
- ✅ Zero "where is X documented?" questions

**Bad signs:**
- ❌ People asking "where is..."
- ❌ Docs outdated compared to code
- ❌ Tests failing due to outdated procedures
- ❌ Recovery taking > 2 hours
- ❌ Onboarding taking > 1 week

---

## 💡 Tips for Efficient Navigation

### Use Search
- Use `grep` or IDE search for keywords
- Search file names for feature names
- Search error messages in troubleshooting

### Follow Cross-References
- Every doc has "Related Documentation" section
- Follow those links
- Build mental map of relationships

### Check Version History
- See when doc was last updated
- Check if it matches current code version
- Look for deprecation notices

### When in Doubt
1. Start with `../00_START_HERE/`
2. Follow role-based path
3. Check `../docs/README.md` for structure
4. Ask team with specific question

---

## 📞 Getting Help

**Quick Questions:**
- Check this WORKFLOWS.md for path
- Check `../docs/README.md` for structure

**Documentation Issues:**
- Outdated docs → Report to doc owner
- Missing docs → Create using template
- Broken links → Fix and PR

**Process Questions:**
- Development workflow → Tech Lead
- QA procedures → QA Lead
- Release process → DevOps Lead

**Emergencies:**
- System down → Follow `../05_RECOVERY/`
- Data loss → Follow `../05_RECOVERY/`
- Security issue → Escalate immediately

---

**Document Owner:** Tech Lead  
**Last Review:** 2026-04-19  
**Next Review:** 2026-05-19

---

*This guide is your map. Use it to navigate efficiently and contribute effectively.*
