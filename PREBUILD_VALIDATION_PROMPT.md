# Pre-Build Validation Protocol for Enterprise-Grade Software

## Purpose
This protocol ensures that all code changes are validated before building production executables. It prevents deployment of code with demo data placeholders, incomplete validations, or outdated implementations that would waste end-user time and compromise enterprise-grade quality.

## Roles

### Primary Validator (AI Assistant)
- **Responsibility**: Execute comprehensive validation of all code changes before build
- **Authority**: Block builds that fail validation criteria
- **Scope**: All source files, test files, configuration files, and build specifications

### Secondary Validator (Human Reviewer)
- **Responsibility**: Review validation findings and approve/deny build
- **Authority**: Override validation with documented justification
- **Scope**: Critical findings and edge cases

## Core Rules

### Rule 1: Zero Trust Principle
- **Never assume** code works based on previous validations
- **Never assume** tests cover production scenarios
- **Never assume** configuration is correct
- **Never assume** dependencies are compatible
- **Validate everything** that changed or could be affected

### Rule 2: Production-First Validation
- **Always validate** production code paths, not just test paths
- **Always verify** production uses real data sources, not demo data
- **Always check** production error handling, not just happy paths
- **Always test** with production-like data volumes

### Rule 3: Test-Reality Alignment
- **Tests must validate** actual production behavior, not mocked behavior
- **Tests must cover** the exact code paths that production uses
- **Tests must verify** data comes from correct sources (database vs hardcoded)
- **Tests must fail** if production code has demo placeholders

### Rule 4: Build Integrity
- **Source files in build** must match latest validated source
- **Dependencies in build** must be explicitly specified
- **Configuration in build** must match production requirements
- **Database files in build** must be current and complete

## Validation Workflows

### Workflow 1: Code Change Validation

#### Step 1: Identify Changed Files
- List all files modified since last successful build
- Include direct changes and indirect dependencies
- Mark files that affect data sources, formatters, or output generation

#### Step 2: Data Source Validation
For each file that handles data:
- **Check**: Does code use hardcoded demo data?
- **Check**: Does code load from database/API?
- **Check**: Is there a fallback to demo data?
- **Check**: Does the fallback path match production behavior?
- **Check**: Are database queries using correct schema?
- **Check**: Are API calls using correct endpoints?

**Critical Pattern to Detect**:
```python
# BAD: Hardcoded demo data in production code
const ciscoEolData = [
    {pid: 'N9K-C93180YC-EX', ...},  // Only 16 models
];

# GOOD: Load from database
models = get_all_models()  # 82 models from database
if not models:
    models = seed_demo_data()  # Fallback
```

#### Step 3: Output Format Validation
For each file that generates output (CSV, HTML, JSON, etc.):
- **Check**: Are all required columns/fields present?
- **Check**: Is data populated from correct source?
- **Check**: Are column names enterprise-grade (not abbreviated)?
- **Check**: Is data formatting consistent?
- **Check**: Are special characters properly escaped?

**Critical Pattern to Detect**:
```python
# BAD: Missing columns or wrong data source
csv_output = format_csv(data)  # Only 10 columns, missing EOL/EOS

# GOOD: Full enterprise format with all columns
csv_output = format_asset_warranty_csv(data)  # 18 columns with EOL/EOS
```

#### Step 4: Test Coverage Validation
For each changed file:
- **Check**: Do tests exist for the changed code?
- **Check**: Do tests validate production behavior (not mocked)?
- **Check**: Do tests verify data sources (database vs hardcoded)?
- **Check**: Do tests check output format (column count, data types)?
- **Check**: Do tests validate error conditions?

**Critical Pattern to Detect**:
```javascript
// BAD: Test only checks UI, not data source
test('modal opens', async ({ page }) => {
  await page.goto('demo.html');
  await expect(modal).toBeVisible();
});

// GOOD: Test validates data source
test('modal loads from database', async () => {
  const js = _get_cisco_eol_javascript();
  expect(js).toContain('Data loaded from Cisco EOL/EOS database');
  expect(js).not.toContain('Demo data - would come from backend');
});
```

### Workflow 2: Build Configuration Validation

#### Step 1: Source File Synchronization
- **Check**: Do files in `dist/` match files in source directories?
- **Check**: Are all changed files copied to build directories?
- **Check**: Are file permissions correct?
- **Check**: Are file paths in spec file correct?

**Critical Pattern to Detect**:
```python
# BAD: Source file not copied to build
# utils/report_formatter.py changed but dist/utils/report_formatter.py not updated

# GOOD: All source files synchronized
Copy-Item utils/report_formatter.py dist/utils/report_formatter.py -Force
```

#### Step 2: Dependency Validation
- **Check**: Are all new modules in `hiddenimports`?
- **Check**: Are data files in `datas` section?
- **Check**: Are database files bundled?
- **Check**: Are version numbers consistent?

**Critical Pattern to Detect**:
```python
# BAD: Module not in hiddenimports
hiddenimports=['module_a', 'module_b']  # Missing 'modules.cisco_eol_database'

# GOOD: All modules included
hiddenimports=['module_a', 'module_b', 'modules.cisco_eol_database']
```

#### Step 3: Database Validation
- **Check**: Is database file included in build?
- **Check**: Is database path correct for bundled EXE?
- **Check**: Does database have correct schema?
- **Check**: Does database have expected data count?
- **Check**: Are indexes present for performance?

**Critical Pattern to Detect**:
```python
# BAD: Database not bundled or wrong path
# config/cisco_eol_database.db not in datas section

# GOOD: Database bundled with correct path
datas=[('config/cisco_eol_database.db', 'config')]
```

### Workflow 3: Pre-Build Test Execution

#### Step 1: Unit Test Validation
- **Run**: All unit tests for changed modules
- **Verify**: 100% pass rate required
- **Check**: No skipped tests
- **Check**: No warnings about deprecated patterns

#### Step 2: Integration Test Validation
- **Run**: All integration tests
- **Verify**: 100% pass rate required
- **Check**: Tests use real database (not mocked)
- **Check**: Tests validate output formats

#### Step 3: E2E Test Validation
- **Run**: All Playwright tests
- **Verify**: 100% pass rate required
- **Check**: Tests validate production HTML (not demo HTML)
- **Check**: Tests validate CSV columns
- **Check**: Tests validate data sources

**Critical Pattern to Detect**:
```javascript
// BAD: Test only validates demo HTML
test('CSV columns', async ({ page }) => {
  await page.goto('demo.html');  // Wrong file
  const headers = await page.locator('th').allTextContents();
  expect(headers.length).toBe(10);  // Wrong count
});

// GOOD: Test validates production formatter
test('CSV has 18 columns', async () => {
  const csv = format_asset_warranty_csv(test_data);
  const headers = csv.split('\n')[0].split(',');
  expect(headers.length).toBe(18);
  expect(headers).toContain('End of Life Date');
});
```

### Workflow 4: Build Execution Validation

#### Step 1: Clean Build
- **Action**: Delete existing build directory
- **Action**: Delete existing dist directory
- **Action**: Run PyInstaller with `--clean --noconfirm`

#### Step 2: Build Verification
- **Check**: EXE file created
- **Check**: EXE file size reasonable (not suspiciously small)
- **Check**: No critical warnings in build log
- **Check**: All data files included

#### Step 3: Post-Build Validation
- **Check**: Can EXE be executed?
- **Check**: Does EXE load database correctly?
- **Check**: Does EXE generate correct output?
- **Check**: Does EXE handle errors gracefully?

## Common Failure Patterns

### Pattern 1: Demo Data in Production
**Symptoms**:
- HTML has hardcoded arrays with limited data
- CSV has missing columns or wrong data
- Tests pass but production has wrong output

**Detection**:
- Search for `const data = [` in production code
- Search for `demo data` comments
- Verify data source is database/API, not hardcoded

**Prevention**:
- Always use database loader functions
- Always have fallback to demo data with logging
- Always validate data count in tests

### Pattern 2: Test-Production Mismatch
**Symptoms**:
- Tests use demo HTML, production uses generated HTML
- Tests mock database, production uses real database
- Tests validate UI, not data sources

**Detection**:
- Check if test files reference `demo_*.html`
- Check if tests mock database functions
- Verify tests call actual formatter functions

**Prevention**:
- Tests must validate formatter functions directly
- Tests must check data source comments
- Tests must validate output structure

### Pattern 3: Build Source Mismatch
**Symptoms**:
- EXE has old code despite recent changes
- Source files not copied to build directories
- Spec file references wrong paths

**Detection**:
- Compare file modification times
- Verify dist/ files match source files
- Check spec file paths

**Prevention**:
- Always copy changed files to dist/ before build
- Always verify file synchronization
- Always use clean build

### Pattern 4: Missing Dependencies
**Symptoms**:
- EXE crashes on import
- Module not found errors
- Database not accessible

**Detection**:
- Check hiddenimports in spec file
- Check datas section in spec file
- Verify database file exists

**Prevention**:
- Add all new modules to hiddenimports
- Add all data files to datas section
- Test EXE execution after build

## Validation Checklist

### Before Build
- [ ] All changed files identified
- [ ] Data sources validated (no demo data in production)
- [ ] Output formats validated (all columns present)
- [ ] Test coverage validated (tests check production behavior)
- [ ] Source files synchronized with build directories
- [ ] Dependencies specified in spec file
- [ ] Database file included in build
- [ ] Unit tests pass (100%)
- [ ] Integration tests pass (100%)
- [ ] E2E tests pass (100%)

### After Build
- [ ] EXE file created
- [ ] EXE file size reasonable
- [ ] No critical build warnings
- [ ] EXE executes without errors
- [ ] Database loads correctly
- [ ] Output formats correct
- [ ] Error handling works

## Validation Report Template

```markdown
# Pre-Build Validation Report

## Build Information
- **Version**: X.Y.Z
- **Build Date**: YYYY-MM-DD
- **Validator**: [AI/Human]

## Changed Files
1. `path/to/file1.py` - Description
2. `path/to/file2.py` - Description

## Data Source Validation
- [ ] No hardcoded demo data in production
- [ ] Database loader functions used
- [ ] Fallback to demo data with logging
- [ ] Data count verified (expected: X, actual: Y)

## Output Format Validation
- [ ] CSV has all required columns (18)
- [ ] HTML loads from database (82 models)
- [ ] Column names enterprise-grade
- [ ] Data formatting consistent

## Test Coverage Validation
- [ ] Unit tests pass (14/14)
- [ ] Integration tests pass (10/10)
- [ ] E2E tests pass (17/17)
- [ ] Tests validate production behavior
- [ ] Tests check data sources

## Build Configuration Validation
- [ ] Source files synchronized
- [ ] Dependencies in spec file
- [ ] Database file bundled
- [ ] Version numbers consistent

## Build Execution
- [ ] Clean build completed
- [ ] EXE created successfully
- [ ] EXE size: XX MB
- [ ] No critical warnings

## Post-Build Validation
- [ ] EXE executes without errors
- [ ] Database loads правильно
- [ ] Output formats correct
- [ ] Error handling works

## Findings
- **Critical**: None
- **Warnings**: None
- **Info**: None

## Recommendation
- [ ] APPROVED for deployment
- [ ] DENIED - requires fixes

## Justification
[Detailed explanation if denied or with findings]
```

## Escalation Criteria

### Critical (Block Build)
- Production code uses demo data
- Tests don't validate production behavior
- Build source files not synchronized
- Database not included in build
- EXE fails to execute

### High (Review Required)
- Test coverage < 100%
- Output format missing columns
- Build warnings about missing dependencies
- Database data count incorrect

### Medium (Document)
- Minor formatting inconsistencies
- Non-critical build warnings
- Test timeouts (if flaky)

## Continuous Improvement

### Lessons Learned
- Document every validation failure
- Update patterns to detect new failure modes
- Refine validation workflows based on findings
- Share learnings across team

### Pattern Library
- Maintain library of common failure patterns
- Update detection rules regularly
- Add new patterns as discovered
- Share with AI training

## Conclusion

This protocol ensures enterprise-grade quality by:
1. Validating production code uses real data sources
2. Ensuring tests validate actual production behavior
3. Verifying build includes latest source files
4. Confirming EXE works as expected

**Zero Trust** - Validate everything, assume nothing.
**Production-First** - Always test production paths.
**Test-Reality** - Tests must match production behavior.
**Build Integrity** - Source must match build.

Following this protocol prevents deployment of code with demo placeholders, incomplete validations, or outdated implementations, saving valuable end-user time and maintaining enterprise-grade quality.
