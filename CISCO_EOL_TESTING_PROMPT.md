# COMPREHENSIVE TESTING PROMPT: Cisco EOL/EOS Database Feature v7.4.2

## OBJECTIVE
Execute end-to-end testing of the Cisco EOL/EOS database feature for Network Swiss Tool Pro v7.4.2, including API validation, result verification, Playwright E2E tests, and CSV output validation. Only proceed to version update, documentation update, and EXE build after ALL tests pass with zero errors.

## ROLES TO INVOKE
- **Senior Architect**: Validate overall architecture, EXE bundling strategy, database integrity
- **Backend Developer**: Validate database queries, enrichment logic, API responses
- **Frontend Developer**: Validate HTML rendering, modal functionality, JavaScript interactions
- **QA Engineer**: Execute all test suites, validate test coverage, error handling
- **Python Skill**: Validate Python code quality, type safety, error handling
- **Code Reviewer Skill**: Systematic code review, identify bugs, validate fixes
- **UI/UX Skill**: Validate responsive design, accessibility, user interactions

## TESTING PHASES

### PHASE 1: UNIT TESTS (Database Module)
**File**: `tests/test_cisco_eol_database.py`

**Test Execution**:
```bash
cd "c:\Users\bbb12\OneDrive\Desktop\Antigravity Projects Folder\NEW_PROJECTS\03092026\nmg\net-mng-tool\net-mng-tool"
python -m pytest tests/test_cisco_eol_database.py -v --cov=modules/cisco_eol_database --cov-report=html
```

**Success Criteria**:
- [ ] All 14 unit tests pass (100% pass rate)
- [ ] Code coverage ≥ 90% for `modules/cisco_eol_database.py`
- [ ] No warnings or errors in test output
- [ ] Database initialization succeeds
- [ ] PID lookup works with valid/invalid PIDs
- [ ] Asset enrichment adds EOL/EOS data correctly
- [ ] Warranty status calculation is accurate
- [ ] Demo mode fallback activates correctly

**Error Handling**:
- If any test fails: Identify root cause, fix code, re-run until all pass
- If coverage < 90%: Add missing test cases for uncovered code paths
- Log all failures with stack traces for debugging

### PHASE 2: INTEGRATION TESTS (Enrichment & Formatting)
**File**: `tests/test_asset_warranty_eol_integration.py`

**Test Execution**:
```bash
python -m pytest tests/test_asset_warranty_eol_integration.py -v --cov=utils/report_formatter --cov-report=html
```

**Success Criteria**:
- [ ] All 10 integration tests pass (100% pass rate)
- [ ] CSV generation includes all 4 new EOL/EOS columns
- [ ] CSV column order is correct
- [ ] CSV warranty status values are accurate (Active/Expired/Expiring Soon/Unknown)
- [ ] HTML generation includes clickable PIDs
- [ ] HTML modal structure is correct
- [ ] HTML status badges display correctly
- [ ] HTML JavaScript functions are present
- [ ] Demo data is included in HTML
- [ ] Empty assets handled gracefully

**Error Handling**:
- If CSV columns missing: Verify `format_asset_warranty_csv()` implementation
- If HTML structure wrong: Verify `format_asset_warranty_html()` implementation
- If demo data missing: Verify `seed_demo_data()` is called in HTML formatter

### PHASE 3: PLAYWRIGHT E2E TESTS (UI Interactions)
**File**: `tests/cisco_eol_catalog.spec.js`

**Playwright Setup Instructions**:
```bash
# Install Playwright (if not already installed)
npm install -D @playwright/test

# Install browsers
npx playwright install chromium

# Run tests in headed mode for debugging
npx playwright test tests/cisco_eol_catalog.spec.js --headed

# Run tests in headless mode for CI
npx playwright test tests/cisco_eol_catalog.spec.js
```

**Test Execution**:
```bash
cd "c:\Users\bbb12\OneDrive\Desktop\Antigravity Projects Folder\NEW_PROJECTS\03092026\nmg\net-mng-tool\net-mng-tool"
npx playwright test tests/cisco_eol_catalog.spec.js --reporter=html
```

**Success Criteria**:
- [ ] All 15 Playwright tests pass (100% pass rate)
- [ ] Test 1: CSV output has new EOL/EOS columns
- [ ] Test 2: HTML report has clickable PIDs
- [ ] Test 3: Clicking PID opens model catalog modal
- [ ] Test 4: Catalog search functionality works
- [ ] Test 5: Catalog filter by status works
- [ ] Test 6: Catalog clear search works
- [ ] Test 7: Modal close (X button) works
- [ ] Test 8: Modal close (Escape key) works
- [ ] Test 9: Modal close (click outside) works
- [ ] Test 10: Modal highlights clicked model
- [ ] Test 11: Status badges display correctly
- [ ] Test 12: Filter buttons toggle correctly
- [ ] Test 13: Modal is responsive (mobile viewport)
- [ ] Test 14: Demo mode without database works
- [ ] Test 15: Warranty status calculation is correct

**Playwright Error Handling Strategies**:
1. **Element Not Found**: Use `waitForSelector()` with timeout
   ```javascript
   await page.waitForSelector('.nst-clickable-pid', { timeout: 5000 });
   ```

2. **Button Not Clickable**: Use `waitForElementState()` to ensure ready
   ```javascript
   await page.waitForElementState('button', 'visible');
   await page.click('button');
   ```

3. **Modal Not Opening**: Add retry logic with exponential backoff
   ```javascript
   await page.click('.nst-clickable-pid');
   await page.waitForSelector('#catalogModal', { timeout: 3000 });
   ```

4. **Search Not Filtering**: Add delay for JavaScript execution
   ```javascript
   await page.fill('#searchInput', 'N9K-C93180YC-EX');
   await page.waitForTimeout(100); // Wait for filter to apply
   ```

5. **Responsive Test Failing**: Verify viewport size before test
   ```javascript
   await page.setViewportSize({ width: 375, height: 667 });
   ```

**Demo File Compatibility**:
- Tests use `demo_cisco_eol_catalog.html` as test fixture
- Verify demo file exists at project root
- If demo file structure differs from production HTML, update selectors accordingly
- Current demo file uses: `#catalogModal`, `#searchInput`, `#catalogBody`, `.status-active`

### PHASE 4: CSV OUTPUT VALIDATION
**Manual CSV Validation Steps**:

1. **Generate Test CSV**:
   - Run the Cisco Asset & Warranty plugin on a test device
   - Verify CSV file is created in run folder
   - Open CSV in spreadsheet application

2. **Validate CSV Structure**:
   ```csv
   Host,Hostname,Collection Method,PID,VID,Serial Number,Software Version,Device Type,Model Name,End of Life Date,End of Support Date,End of Service Date,Warranty Status,Warranty End,Contract Status,Severity,Error,Collection Timestamp
   ```

3. **Validate CSV Data**:
   - [ ] All 18 columns present
   - [ ] Column headers match expected order
   - [ ] Model Name column populated for known PIDs
   - [ ] End of Life Date populated for known PIDs
   - [ ] End of Support Date populated for known PIDs
   - [ ] End of Service Date populated for known PIDs
   - [ ] Warranty Status calculated correctly (Active/Expired/Expiring Soon/Unknown)
   - [ ] Unknown PIDs show empty EOL/EOS dates
   - [ ] Unknown PIDs show "Unknown" warranty status
   - [ ] No empty rows (except header)
   - [ ] No duplicate rows
   - [ ] Timestamp format is ISO 8601

4. **Validate CSV Encoding**:
   - [ ] UTF-8 encoding
   - [ ] Proper CSV escaping for special characters
   - [ ] No line breaks within fields

### PHASE 5: DATABASE INTEGRITY VALIDATION
**Database Validation Steps**:

1. **Verify Database Exists**:
   ```bash
   ls config/cisco_eol_database.db
   ```

2. **Verify Database Schema**:
   ```bash
   sqlite3 config/cisco_eol_database.db ".schema cisco_models"
   ```
   Expected schema:
   ```sql
   CREATE TABLE cisco_models (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       pid TEXT UNIQUE NOT NULL,
       model_name TEXT,
       end_of_life DATE,
       end_of_support DATE,
       end_of_service DATE,
       last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

3. **Verify Data Count**:
   ```bash
   sqlite3 config/cisco_eol_database.db "SELECT COUNT(*) FROM cisco_models;"
   ```
   Expected: 82 models (Nexus 9000, Catalyst 9000, ISR/ASR, Catalyst 29XX, Catalyst 38XX)

4. **Verify Data Quality**:
   ```bash
   sqlite3 config/cisco_eol_database.db "SELECT pid, model_name FROM cisco_models WHERE model_name IS NULL OR model_name = '';"
   ```
   Expected: 0 rows (all models should have names)

5. **Verify Index Exists**:
   ```bash
   sqlite3 config/cisco_eol_database.db ".indexes"
   ```
   Expected: `idx_pid` on `cisco_models(pid)`

### PHASE 6: API VALIDATION (If Applicable)
**API Endpoint Testing**:

If the application exposes API endpoints for EOL/EOS data:

1. **Test GET /api/cisco-eol/models**:
   - [ ] Returns 200 OK
   - [ ] Returns JSON array of all models
   - [ ] Each model has: pid, model_name, end_of_life, end_of_support, end_of_service
   - [ ] Response time < 500ms

2. **Test GET /api/cisco-eol/models/:pid**:
   - [ ] Returns 200 OK for valid PID
   - [ ] Returns 404 for invalid PID
   - [ ] Returns model data in correct format
   - [ ] Case-insensitive PID lookup works

3. **Test POST /api/cisco-eol/enrich**:
   - [ ] Accepts asset data in request body
   - [ ] Returns enriched asset with EOL/EOS data
   - [ ] Handles missing PID gracefully
   - [ ] Returns 400 for invalid input

### PHASE 7: OFFLINE/DEMO MODE VALIDATION
**Demo Mode Testing**:

1. **Test Without Database**:
   ```bash
   mv config/cisco_eol_database.db config/cisco_eol_database.db.backup
   # Run plugin
   # Verify demo mode activates
   mv config/cisco_eol_database.db.backup config/cisco_eol_database.db
   ```

2. **Validate Demo Mode Behavior**:
   - [ ] Plugin runs without database
   - [ ] Demo data is used for enrichment
   - [ ] HTML catalog shows demo models
   - [ ] No errors or crashes
   - [ ] Warning logged about demo mode activation

### PHASE 8: CODE QUALITY VALIDATION
**Static Analysis**:

1. **Run Pylint**:
   ```bash
   pylint modules/cisco_eol_database.py --max-line-length=120
   ```
   Expected: Score ≥ 8.0/10

2. **Run Flake8**:
   ```bash
   flake8 modules/cisco_eol_database.py --max-line-length=120
   ```
   Expected: 0 errors, 0 warnings

3. **Run MyPy** (Type Checking):
   ```bash
   mypy modules/cisco_eol_database.py --ignore-missing-imports
   ```
   Expected: 0 type errors

### PHASE 9: DOCUMENTATION VALIDATION
**Documentation Review**:

1. **Verify README.md Updated**:
   - [ ] `docs/05-plugins/cisco_asset_warranty_plugin/README.md` updated
   - [ ] New CSV columns documented
   - [ ] Clickable PID feature documented
   - [ ] Model catalog functionality documented
   - [ ] Demo mode documented
   - [ ] Version history updated to v7.4.2

2. **Verify Code Comments**:
   - [ ] `modules/cisco_eol_database.py` has docstrings
   - [ ] All functions have type hints
   - [ ] Complex logic has inline comments

### PHASE 10: EXE BUNDLING VALIDATION
**EXE Testing**:

1. **Build EXE**:
   ```bash
   python -m PyInstaller --clean --noconfirm NetworkSwissToolPro_v7.4.2.spec
   ```

2. **Verify EXE Created**:
   ```bash
   ls dist/NetworkSwissToolPro_v7.4.2_OFFLINE.exe
   ```
   Expected: File exists, size ~66 MB

3. **Verify Database Bundled**:
   - Extract EXE (temporarily) or run EXE and check internal structure
   - Verify `config/cisco_eol_database.db` is bundled
   - Verify database has 82 models

4. **Test EXE Functionality**:
   - Run EXE on clean machine (if possible)
   - Launch application
   - Run Cisco Asset & Warranty plugin
   - Verify CSV output has EOL/EOS columns
   - Verify HTML report has clickable PIDs
   - Verify modal opens and functions correctly

## SUCCESS CRITERIA SUMMARY

**ALL of the following must be TRUE before proceeding to version update**:

- [ ] Unit tests: 14/14 passing (100%)
- [ ] Integration tests: 10/10 passing (100%)
- [ ] Playwright E2E tests: 15/15 passing (100%)
- [ ] CSV output validation: All checks pass
- [ ] Database integrity: All checks pass
- [ ] Demo mode: Functions correctly
- [ ] Code quality: Pylint ≥ 8.0, Flake8 0 errors, MyPy 0 errors
- [ ] Documentation: All sections updated
- [ ] EXE build: Successful, database bundled
- [ ] Zero errors in any test suite
- [ ] Zero warnings that indicate bugs
- [ ] Manual CSV validation passes
- [ ] Manual HTML validation passes

## POST-TESTING ACTIONS (Only if ALL tests pass)

### Step 1: Update Version
**File**: `vlan_checker_web.py`
```python
VERSION = _read_version()
UPDATE_DATE = "2026-09-06 — v7.4.2: Cisco EOL/EOS database integration with interactive model catalog (82 models including Catalyst 29XX/38XX)"
```

### Step 2: Update Documentation
**File**: `docs/05-plugins/cisco_asset_warranty_plugin/README.md`
- Add note about Catalyst 29XX/38XX models
- Update model count to 82
- Update version history

### Step 3: Rebuild EXE
```bash
python -m PyInstaller --clean --noconfirm NetworkSwissToolPro_v7.4.2.spec
```

### Step 4: Final Validation
- Run EXE one more time
- Verify all functionality works offline
- Verify database is bundled correctly

### Step 5: Create Release Notes
Document:
- 82 Cisco models added (Nexus 9000, Catalyst 9000, ISR/ASR, Catalyst 29XX, Catalyst 38XX)
- Official Cisco EoX data sources
- Interactive model catalog with search/filter
- CSV enrichment with 4 new columns
- Demo mode fallback
- 100% test pass rate (39 tests total)

## FAILURE HANDLING

**If ANY test fails**:
1. Stop immediately
2. Identify root cause
3. Fix the issue
4. Re-run the failed test suite
5. Only proceed when ALL tests pass
6. DO NOT proceed to version update until all tests pass

**Common Failure Scenarios**:
- Database not found: Verify `config/cisco_eol_database.db` exists
- PID lookup fails: Verify database has the PID being tested
- HTML modal not opening: Verify JavaScript is not blocked
- Playwright timeout: Increase timeout or verify element exists
- CSV columns missing: Verify formatter implementation
- EXE build fails: Verify spec file syntax and dependencies

## TEST EXECUTION ORDER

Execute phases in this exact order:
1. Phase 1: Unit Tests
2. Phase 2: Integration Tests
3. Phase 3: Playwright E2E Tests
4. Phase 4: CSV Output Validation
5. Phase 5: Database Integrity Validation
6. Phase 6: API Validation (if applicable)
7. Phase 7: Offline/Demo Mode Validation
8. Phase 8: Code Quality Validation
9. Phase 9: Documentation Validation
10. Phase 10: EXE Bundling Validation

Only after ALL phases pass, execute Post-Testing Actions.

## REPORTING

After each phase, report:
- Phase name
- Tests run / passed
- Any failures with stack traces
- Any warnings
- Next action (proceed or fix)

After all phases pass, report:
- Final test summary (39/39 tests passing)
- CSV validation results
- Database validation results
- EXE build status
- Ready for version update confirmation
