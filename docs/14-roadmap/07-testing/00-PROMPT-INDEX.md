# Testing Phase Prompt Index

| Field | Value |
|-------|-------|
| **Phase** | 07-testing |
| **Phase Number** | 7 |
| **Dependency Level** | 6 (Depends on Phase 6) |
| **Total Steps** | 3 |
| **Estimated Time** | 30 minutes |
| **Parallel Execution** | No (Sequential Required) |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

This phase reconstructs the test suite for automated testing. This includes unit tests, integration tests, and test execution procedures.

---

## Prompt Sequence

### P22: Unit Tests
**File:** P22-UNIT-TESTS.md
**Purpose:** Reconstruct unit tests for individual modules
**Dependencies:** P05-P08, P16-P18
**Estimated Time:** 10 minutes
**Validation:** Unit tests created, test coverage adequate

### P23: Integration Tests
**File:** P23-INTEGRATION-TESTS.md
**Purpose:** Reconstruct integration tests for module interactions
**Dependencies:** P19-P21
**Estimated Time:** 10 minutes
**Validation:** Integration tests created, module interactions tested

### P24: Test Execution
**File:** P24-TEST-EXECUTION.md
**Purpose:** Reconstruct test execution procedures and CI/CD integration
**Dependencies:** P22-P23
**Estimated Time:** 10 minutes
**Validation:** Test execution functional, CI/CD integration working

---

## Execution Order

**Sequential Execution Required:**
1. P22 → P23 → P24

**Wait Time Between Prompts:** 30 seconds

---

## Validation Criteria

### Phase-Level Validation

- [ ] Unit tests created
- [ ] Test coverage >= 80%
- [ ] All unit tests passing
- [ ] Integration tests created
- [ ] Module interactions tested
- [ ] All integration tests passing
- [ ] Test execution procedures created
- [ ] CI/CD integration functional
- [ ] Test reporting functional
- [ ] Ready for deployment reconstruction

---

## Failure Recovery

### P22 Failure
**Recovery:** Re-run P22, validate test structure
**Estimated Time:** 10 minutes

### P23 Failure
**Recovery:** Re-run P23, validate integration tests
**Estimated Time:** 10 minutes

### P24 Failure
**Recovery:** Re-run P24, validate test execution
**Estimated Time:** 10 minutes

---

## References

- RECONSTRUCTION_INDEX.md: ../00-RECONSTRUCTION_INDEX.md
- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- AUTOMATED_TESTING_DOCUMENTATION.md: ../../02-codebase/AUTOMATED_TESTING_DOCUMENTATION.md
- COMPREHENSIVE_TESTING_COVERAGE.md: ../../02-codebase/COMPREHENSIVE_TESTING_COVERAGE.md
