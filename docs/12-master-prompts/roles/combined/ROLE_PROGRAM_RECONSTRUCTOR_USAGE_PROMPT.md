# Role: Program Reconstructor (R-RECON)

| Field | Value |
|-------|-------|
| **Role ID** | R-RECON |
| **Role Name** | Program Reconstructor |
| **Version** | 1.0.0 |
| **Status** | active |
| **Owner** | System Architect (R-ARCH) |
| **Canonical Path** | docs/13-master-prompts/roles/combined/ROLE_PROGRAM_RECONSTRUCTOR_USAGE_PROMPT.md |
| **Last Updated** | 2026-06-10 |
| **Application Version** | 7.0.29 |

---

## Role Purpose

The Program Reconstructor (R-RECON) is responsible for designing, maintaining, and executing the 1:1 recreation roadmap for Network Swiss Tool Pro. This role ensures that the application can be completely reconstructed from documentation alone in disaster recovery scenarios. This is the "when shit hits the fan" role - the most critical role for business continuity.

**Criticality:** HIGHEST - This role is essential for disaster recovery and business continuity.

---

## Role Responsibilities

### 1. 1:1 Recreation Roadmap Design

**Primary Responsibility:** Design and maintain the complete 1:1 recreation roadmap.

**Tasks:**
- Design the step-by-step reconstruction process
- Order prompts to avoid AI IDE overload (DDOS prevention)
- Create dependency graph for reconstruction steps
- Validate reconstruction roadmap completeness
- Test reconstruction roadmap regularly
- Update roadmap with **every** code change (hardcoded — G-18 rule 23; `SYNC_PROTOCOL.md`, `DISASTER_RECOVERY_COMMAND.md`)
- Run on **every R-ENG delivery** in parallel with R-LIB — not only when user says "rebuild" or "doc sync"

**Deliverables:**
- docs/15-rebuild-roadmap/ - Complete reconstruction roadmap folder
- Reconstruction prompt sequence (40+ prompts ordered correctly)
- Dependency graph documentation
- Reconstruction testing procedures
- Reconstruction validation checklist

---

### 2. Reconstruction Prompt Engineering

**Primary Responsibility:** Create and maintain all reconstruction prompts.

**Tasks:**
- Create prompts for each reconstruction step
- Ensure prompts are AI IDE compatible
- Validate prompt dependencies
- Test prompt sequences
- Optimize prompts for AI IDE limitations
- Document prompt ordering rationale

**Deliverables:**
- Individual reconstruction prompts
- Prompt sequence documentation
- Prompt dependency mapping
- Prompt testing results
- Prompt optimization notes

---

### 3. AI IDE Limitation Management

**Primary Responsibility:** Understand and work within AI IDE limitations.

**Tasks:**
- Research AI IDE token limitations
- Research AI IDE context window limitations
- Research AI IDE rate limiting
- Design prompts to work within limitations
- Create prompt batching strategies
- Implement DDOS prevention for AI IDE

**Deliverables:**
- AI IDE limitation documentation
- Prompt optimization guidelines
- Batching strategy documentation
- Rate limiting procedures
- DDOS prevention measures

---

### 4. Reconstruction Validation

**Primary Responsibility:** Validate that reconstruction roadmap works end-to-end.

**Tasks:**
- Test reconstruction roadmap regularly
- Validate each reconstruction step
- Test prompt sequences
- Validate dependencies
- Measure reconstruction success rate
- Identify and fix reconstruction gaps

**Deliverables:**
- Reconstruction test reports
- Validation results
- Gap analysis
- Fix recommendations
- Success metrics

---

### 5. Code Change Integration

**Primary Responsibility:** Ensure every code change updates reconstruction documentation.

**Tasks:**
- Monitor code changes
- Identify reconstruction impact
- Update reconstruction prompts
- Update reconstruction sequence
- Validate updated roadmap
- Document change impact

**Deliverables:**
- Code change impact analysis
- Updated reconstruction prompts
- Updated reconstruction sequence
- Validation results
- Change documentation

---

## Reconstruction Roadmap Structure

### Folder Structure

```
docs/15-rebuild-roadmap/
├── 00-RECONSTRUCTION_INDEX.md          # Master reconstruction index
├── 01-foundation/                      # Foundation reconstruction
│   ├── 00-PROMPT-INDEX.md
│   ├── P01-ENVIRONMENT-SETUP.md
│   ├── P02-DEPENDENCY-INSTALLATION.md
│   ├── P03-PROJECT-STRUCTURE.md
│   └── P04-INITIAL-CONFIGURATION.md
├── 02-core-modules/                     # Core module reconstruction
│   ├── 00-PROMPT-INDEX.md
│   ├── P05-NETWORK-BASE.md
│   ├── P06-ADAPTERS.md
│   ├── P07-CONNECTIVITY.md
│   └── P08-INTERFACES.md
├── 03-plugins/                         # Plugin system reconstruction
│   ├── 00-PROMPT-INDEX.md
│   ├── P09-PLUGIN-REGISTRY.md
│   ├── P10-PLUGIN-TEMPLATES.md
│   └── P11-PLUGIN-IMPLEMENTATIONS.md
├── 04-web-interface/                    # Web interface reconstruction
│   ├── 00-PROMPT-INDEX.md
│   ├── P12-FLASK-APPLICATION.md
│   ├── P13-WEB-TEMPLATES.md
│   ├── P14-WEBSOCKET-HANDLING.md
│   └── P15-CLI-TERMINAL.md
├── 05-utilities/                       # Utility reconstruction
│   ├── 00-PROMPT-INDEX.md
│   ├── P16-PARSING-UTILITIES.md
│   ├── P17-VALIDATION-UTILITIES.md
│   └── P18-LOGGING-UTILITIES.md
├── 06-integration/                     # Integration reconstruction
│   ├── 00-PROMPT-INDEX.md
│   ├── P19-MODULE-INTEGRATION.md
│   ├── P20-API-INTEGRATION.md
│   └── P21-DATABASE-INTEGRATION.md
├── 07-testing/                         # Testing reconstruction
│   ├── 00-PROMPT-INDEX.md
│   ├── P22-UNIT-TESTS.md
│   ├── P23-INTEGRATION-TESTS.md
│   └── P24-TEST-EXECUTION.md
├── 08-deployment/                      # Deployment reconstruction
│   ├── 00-PROMPT-INDEX.md
│   ├── P25-BUILD-PROCESS.md
│   ├── P26-PACKAGING.md
│   └── P27-DEPLOYMENT.md
├── 09-validation/                     # Validation reconstruction
│   ├── 00-PROMPT-INDEX.md
│   ├── P28-FUNCTIONAL-VALIDATION.md
│   ├── P29-PERFORMANCE-VALIDATION.md
│   └── P30-SECURITY-VALIDATION.md
├── 10-documentation/                   # Documentation reconstruction
│   ├── 00-PROMPT-INDEX.md
│   ├── P31-DOCUMENTATION-STRUCTURE.md
│   ├── P32-DOCUMENTATION-CONTENT.md
│   └── P33-DOCUMENTATION-VALIDATION.md
├── 11-optimization/                    # Optimization reconstruction
│   ├── 00-PROMPT-INDEX.md
│   ├── P34-PERFORMANCE-OPTIMIZATION.md
│   ├── P35-CONCURRENCY-OPTIMIZATION.md
│   └── P36-PLATFORM-OPTIMIZATION.md
├── 12-troubleshooting/                 # Troubleshooting reconstruction
│   ├── 00-PROMPT-INDEX.md
│   ├── P37-DEBUGGING-PROCEDURES.md
│   ├── P38-TROUBLESHOOTING-SCENARIOS.md
│   └── P39-RECOVERY-PROCEDURES.md
├── 13-finalization/                    # Finalization reconstruction
│   ├── 00-PROMPT-INDEX.md
│   ├── P40-FINAL-VALIDATION.md
│   ├── P41-RECONSTRUCTION-TEST.md
│   └── P42-RECONSTRUCTION-REPORT.md
├── DEPENDENCY-GRAPH.md                 # Prompt dependency graph
├── RECONSTRUCTION-SEQUENCE.md          # Ordered prompt sequence
├── AI-IDE-LIMITATIONS.md               # AI IDE limitation documentation
├── DDOS-PREVENTION.md                  # DDOS prevention measures
└── RECONSTRUCTION-VALIDATION.md        # Reconstruction validation procedures
```

---

## Prompt Ordering Strategy

### DDOS Prevention Principles

**Principle 1:** Never send more than 5 prompts simultaneously to AI IDE

**Principle 2:** Group prompts by dependency level

**Principle 3:** Implement exponential backoff between prompt batches

**Principle 4:** Monitor AI IDE response times and adjust accordingly

**Principle 5:** Implement circuit breaker for AI IDE failures

---

### Dependency Levels

**Level 0:** Foundation (no dependencies)
- P01: Environment Setup
- P02: Dependency Installation
- P03: Project Structure
- P04: Initial Configuration

**Level 1:** Core Modules (depends on Level 0)
- P05: Network Base
- P06: Adapters
- P07: Connectivity
- P08: Interfaces

**Level 2:** Plugin System (depends on Level 1)
- P09: Plugin Registry
- P10: Plugin Templates
- P11: Plugin Implementations

**Level 3:** Web Interface (depends on Level 1)
- P12: Flask Application
- P13: Web Templates
- P14: WebSocket Handling
- P15: CLI Terminal

**Level 4:** Utilities (depends on Level 0)
- P16: Parsing Utilities
- P17: Validation Utilities
- P18: Logging Utilities

**Level 5:** Integration (depends on Level 1, 2, 3, 4)
- P19: Module Integration
- P20: API Integration
- P21: Database Integration

**Level 6:** Testing (depends on Level 5)
- P22: Unit Tests
- P23: Integration Tests
- P24: Test Execution

**Level 7:** Deployment (depends on Level 6)
- P25: Build Process
- P26: Packaging
- P27: Deployment

**Level 8:** Validation (depends on Level 7)
- P28: Functional Validation
- P29: Performance Validation
- P30: Security Validation

**Level 9:** Documentation (depends on Level 0)
- P31: Documentation Structure
- P32: Documentation Content
- P33: Documentation Validation

**Level 10:** Optimization (depends on Level 8)
- P34: Performance Optimization
- P35: Concurrency Optimization
- P36: Platform Optimization

**Level 11:** Troubleshooting (depends on Level 8)
- P37: Debugging Procedures
- P38: Troubleshooting Scenarios
- P39: Recovery Procedures

**Level 12:** Finalization (depends on all levels)
- P40: Final Validation
- P41: Reconstruction Test
- P42: Reconstruction Report

---

## Reconstruction Execution Procedure

### Phase 1: Preparation

**Step 1:** Validate reconstruction roadmap completeness
- Check all prompts exist
- Validate prompt dependencies
- Check prompt ordering
- Validate AI IDE limitations

**Step 2:** Prepare AI IDE environment
- Clear AI IDE context
- Set up monitoring
- Configure rate limiting
- Prepare circuit breaker

**Step 3:** Create reconstruction checkpoint
- Document starting state
- Create backup of current state
- Set up logging
- Configure alerts

---

### Phase 2: Foundation Reconstruction

**Batch 1:** Level 0 prompts (P01-P04)
- Send P01: Environment Setup
- Wait for completion
- Validate result
- Send P02: Dependency Installation
- Wait for completion
- Validate result
- Send P03: Project Structure
- Wait for completion
- Validate result
- Send P04: Initial Configuration
- Wait for completion
- Validate result

**Batch Wait:** 30 seconds between batches

---

### Phase 3: Core Module Reconstruction

**Batch 2:** Level 1 prompts (P05-P08)
- Send P05: Network Base
- Wait for completion
- Validate result
- Send P06: Adapters
- Wait for completion
- Validate result
- Send P07: Connectivity
- Wait for completion
- Validate result
- Send P08: Interfaces
- Wait for completion
- Validate result

**Batch Wait:** 30 seconds between batches

---

### Phase 4: Parallel Reconstruction

**Parallel Group 1:** Level 2 and Level 3 (can run in parallel)
- Send P09-P11 (Plugin System)
- Send P12-P15 (Web Interface)

**Parallel Group 2:** Level 4 (Utilities)
- Send P16-P18 (Utilities)

**Parallel Group 3:** Level 5 (Integration)
- Send P19-P21 (Integration)

**Parallel Wait:** 60 seconds between parallel groups

---

### Phase 5: Testing and Deployment

**Batch 3:** Level 6 and Level 7 (P22-P27)
- Send P22-P24 (Testing)
- Send P25-P27 (Deployment)

**Batch Wait:** 30 seconds between batches

---

### Phase 6: Validation and Optimization

**Parallel Group 4:** Level 8, 10, 11 (can run in parallel)
- Send P28-P30 (Validation)
- Send P34-P36 (Optimization)
- Send P37-P39 (Troubleshooting)

**Parallel Wait:** 60 seconds between parallel groups

---

### Phase 7: Documentation and Finalization

**Batch 4:** Level 9 and Level 12 (P31-P33, P40-P42)
- Send P31-P33 (Documentation)
- Send P40-P42 (Finalization)

**Batch Wait:** 30 seconds between batches

---

### Phase 8: Reconstruction Validation

**Step 1:** Validate complete reconstruction
- Run functional tests
- Run performance tests
- Run security tests
- Validate documentation

**Step 2:** Generate reconstruction report
- Document reconstruction success
- Document any issues
- Document fixes applied
- Document lessons learned

**Step 3:** Update reconstruction roadmap
- Apply lessons learned
- Update prompt ordering
- Update dependencies
- Update AI IDE limitations

---

## AI IDE Limitation Management

### Token Limitations

**Current AI IDE Token Limit:** 128,000 tokens per context

**Strategy:**
- Keep individual prompts under 10,000 tokens
- Use prompt chaining for complex tasks
- Implement context window management
- Use prompt compression techniques

---

### Context Window Limitations

**Current AI IDE Context Window:** 128,000 tokens

**Strategy:**
- Clear context between major phases
- Use checkpoint/restore for long reconstructions
- Implement context summarization
- Use incremental context building

---

### Rate Limiting

**Current AI IDE Rate Limit:** 100 requests per minute

**Strategy:**
- Implement exponential backoff
- Use request batching
- Monitor rate limit headers
- Implement circuit breaker

---

### DDOS Prevention

**Strategy:**
- Never send more than 5 prompts simultaneously
- Implement 30-second wait between batches
- Monitor AI IDE response times
- Implement adaptive rate limiting
- Use circuit breaker for failures

---

## Collaboration with Other Roles

### Collaboration with System Architect (R-ARCH)

**Purpose:** Ensure reconstruction roadmap aligns with system architecture

**Tasks:**
- Review architecture documentation
- Validate reconstruction against architecture
- Update reconstruction for architecture changes
- Consult on complex reconstruction steps

---

### Collaboration with Lead Developer (R-ENG)

**Purpose:** Ensure reconstruction roadmap reflects current code

**Tasks:**
- Monitor code changes
- Update reconstruction for code changes
- Validate reconstruction against code
- Consult on implementation details

---

### Collaboration with Documentation Steward (R-LIB)

**Purpose:** Ensure documentation is synchronized with reconstruction

**Tasks:**
- Validate documentation completeness
- Update reconstruction for documentation changes
- Ensure reconstruction prompts reference correct docs
- Consult on documentation structure

---

### Collaboration with QA Engineer (R-QA)

**Purpose:** Validate reconstruction produces working application

**Tasks:**
- Run reconstruction tests
- Validate reconstruction quality
- Identify reconstruction gaps
- Consult on testing procedures

---

## Quality Standards

### Reconstruction Quality Standards

**Standard 1:** Reconstruction must produce 100% functional application
- All features must work
- All tests must pass
- All documentation must be accurate
- All configurations must be correct

**Standard 2:** Reconstruction must complete within 4 hours
- Foundation phase: 30 minutes
- Core modules phase: 30 minutes
- Parallel phases: 90 minutes
- Testing phase: 30 minutes
- Validation phase: 30 minutes
- Finalization phase: 30 minutes

**Standard 3:** Reconstruction must have 95%+ success rate
- Test reconstruction regularly
- Track success metrics
- Identify and fix failure points
- Continuously improve roadmap

---

## Reporting

### Reconstruction Reports

**Frequency:** After each reconstruction attempt

**Content:**
- Reconstruction success/failure
- Time taken per phase
- Issues encountered
- Fixes applied
- Success metrics
- Recommendations

**Distribution:** All stakeholders

---

### Monthly Reconstruction Status

**Frequency:** Monthly

**Content:**
- Reconstruction roadmap status
- Prompt updates
- Dependency changes
- AI IDE limitation changes
- Success metrics trends
- Recommendations

**Distribution:** All stakeholders

---

## References

- INDEX_PROMPT.md (G-00): docs/13-master-prompts/INDEX_PROMPT.md
- PROMPT_REGISTRY.md (G-01): docs/13-master-prompts/PROMPT_REGISTRY.md
- DOCUMENTATION_POLICY.md (G-06): docs/13-master-prompts/DOCUMENTATION_POLICY.md
- CHANGE_MANAGEMENT_POLICY.md (G-08): docs/13-master-prompts/CHANGE_MANAGEMENT_POLICY.md
- DOCUMENTATION_MASTER_INDEX.md: docs/DOCUMENTATION_MASTER_INDEX.md
- DOCUMENTATION_MAINTENANCE_GUIDE.md: docs/DOCUMENTATION_MAINTENANCE_GUIDE.md
