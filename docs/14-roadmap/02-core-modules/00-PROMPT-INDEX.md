# Core Modules Phase Prompt Index

| Field | Value |
|-------|-------|
| **Phase** | 02-core-modules |
| **Phase Number** | 2 |
| **Dependency Level** | 1 (Depends on Phase 1) |
| **Total Steps** | 4 |
| **Estimated Time** | 30 minutes |
| **Parallel Execution** | No (Sequential Required) |
| **Owner** | Program Reconstructor (R-RECON) |
| **Last Updated** | 2026-06-02 |

---

## Purpose

This phase reconstructs the core network modules that form the foundation of the application. These modules handle device connectivity, network operations, and data processing.

---

## Prompt Sequence

### P05: Network Base
**File:** P05-NETWORK-BASE.md
**Purpose:** Reconstruct network_base module with core network operations
**Dependencies:** P01-P04
**Estimated Time:** 8 minutes
**Validation:** Module structure created, core functions implemented

### P06: Adapters
**File:** P06-ADAPTERS.md
**Purpose:** Reconstruct adapters module for platform-specific operations
**Dependencies:** P05
**Estimated Time:** 7 minutes
**Validation:** Adapters created, platform-specific logic implemented

### P07: Connectivity
**File:** P07-CONNECTIVITY.md
**Purpose:** Reconstruct connectivity module for device connections
**Dependencies:** P05, P06
**Estimated Time:** 8 minutes
**Validation:** Connectivity functions implemented, connection handling validated

### P08: Interfaces
**File:** P08-INTERFACES.md
**Purpose:** Reconstruct interfaces module for interface operations
**Dependencies:** P05, P06
**Estimated Time:** 7 minutes
**Validation:** Interface operations implemented, validation functions created

---

## Execution Order

**Sequential Execution Required:**
1. P05 → P06 → P07 → P08

**Wait Time Between Prompts:** 30 seconds

---

## Validation Criteria

### Phase-Level Validation

- [ ] All core modules created
- [ ] Module structure matches CODE_INVENTORY.md
- [ ] All functions implemented
- [ ] All dependencies resolved
- [ ] Platform-specific adapters functional
- [ ] Connection handling validated
- [ ] Interface operations validated
- [ ] Ready for plugin system reconstruction

---

## Failure Recovery

### P05 Failure
**Recovery:** Re-run P05, validate module structure
**Estimated Time:** 8 minutes

### P06 Failure
**Recovery:** Re-run P06, validate adapter logic
**Estimated Time:** 7 minutes

### P07 Failure
**Recovery:** Re-run P07, validate connectivity functions
**Estimated Time:** 8 minutes

### P08 Failure
**Recovery:** Re-run P08, validate interface operations
**Estimated Time:** 7 minutes

---

## References

- RECONSTRUCTION_INDEX.md: ../00-RECONSTRUCTION_INDEX.md
- CODE_INVENTORY.md: ../../02-codebase/CODE_INVENTORY.md
- MODULE_ARCHITECTURE.md: ../../01-architecture/MODULE_ARCHITECTURE.md
