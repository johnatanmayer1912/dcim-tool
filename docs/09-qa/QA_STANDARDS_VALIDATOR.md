# QA Test Protocol: Standards Validator v2.0

## Overview
Validates the consolidated reporting and category-based filtering logic for the Standards Validator plugin.

## Test Cases

### 1. Dynamic UI Loading
*   [ ] Policy dropdown populates with all files in `/policies`.
*   [ ] Categories checkboxes appear dynamically upon policy selection.
*   [ ] "Select All" / "Select None" buttons toggle all categories.

### 2. Execution & Scope
*   [ ] Run on Single Device: Results table populates in UI.
*   [ ] Run on Bulk: Progress bar shows per-device status.
*   [ ] Consolidation: "⬇ Full Report (TXT)" button appears after bulk run.

### 3. Report Integrity
*   [ ] Consolidated TXT report contains all target devices.
*   [ ] Failed/Non-compliant devices are sorted to the top.
*   [ ] Remediation steps are included for every violation.
*   [ ] CSV export includes a "Summary" tab with compliant/non-compliant counts.

### 4. Regression
*   [ ] Verify large policy files (>100 rules) load without UI lag.
*   [ ] Verify "Check Config" logic handles both Cisco and Juniper syntax in the same run.

---
**Sign-off:** ___________________  **Date:** ___________
