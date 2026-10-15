# Integration Phase Prompt Index

| Field | Value |
|-------|-------|
| **Phase** | 06-integration |
| **Phase Number** | 6 |
| **Dependency Level** | 5 (Depends on Phases 2, 3, 4, 5) |
| **Total Steps** | 3 |
| **Estimated Time** | 30 minutes |
| **Parallel Execution** | No (Sequential Required) |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

This phase reconstructs integration modules that connect all components together. This includes module integration, API integration, and database integration.

---

## Prompt Sequence

### P19: Module Integration
**File:** P19-MODULE-INTEGRATION.md
**Purpose:** Reconstruct module integration for connecting all modules
**Dependencies:** P05-P08, P09-P11, P12-P15, P16-P18
**Estimated Time:** 10 minutes
**Validation:** Module integration functional, all modules connected

### P20: API Integration
**File:** P20-API-INTEGRATION.md
**Purpose:** Reconstruct API integration for REST and WebSocket APIs
**Dependencies:** P12-P15
**Estimated Time:** 10 minutes
**Validation:** API integration functional, all endpoints working

### P21: Database Integration
**File:** P21-DATABASE-INTEGRATION.md
**Purpose:** Reconstruct database integration for data persistence
**Dependencies:** P01-P04
**Estimated Time:** 10 minutes
**Validation:** Database integration functional, CRUD operations working

---

## Execution Order

**Sequential Execution Required:**
1. P19 → P20 → P21

**Wait Time Between Prompts:** 30 seconds

---

## Validation Criteria

### Phase-Level Validation

- [ ] Module integration created
- [ ] All modules connected
- [ ] Data flow functional
- [ ] API integration created
- [ ] All endpoints functional
- [ ] WebSocket integration functional
- [ ] Database integration created
- [ ] CRUD operations functional
- [ ] Data persistence working
- [ ] Ready for testing reconstruction

---

## Failure Recovery

### P19 Failure
**Recovery:** Re-run P19, validate module connections
**Estimated Time:** 10 minutes

### P20 Failure
**Recovery:** Re-run P20, validate API endpoints
**Estimated Time:** 10 minutes

### P21 Failure
**Recovery:** Re-run P21, validate database operations
**Estimated Time:** 10 minutes

---

## References

- RECONSTRUCTION_INDEX.md: ../00-RECONSTRUCTION_INDEX.md
- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- MODULE_ARCHITECTURE.md: ../../01-architecture/MODULE_ARCHITECTURE.md
- API_DOCUMENTATION.md: ../../02-codebase/API_DOCUMENTATION.md
