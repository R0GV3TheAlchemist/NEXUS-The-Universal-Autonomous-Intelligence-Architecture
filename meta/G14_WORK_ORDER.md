# G-14 Work Order

**Version:** 1.0
**Created:** 2026-06-30
**Purpose:** Sequenced, dependency-ordered build plan for G-14 (Deployment & Embodiment phase). Derived from simulation findings and canon tension analysis.

> G-14 cannot begin until all `blocking-g14` issues are resolved.

---

## Phase 0 — Pre-G14 Unblocking (Current)

Must complete before G-14 opens.

### 0.1 Resolve CT-003 (BLOCKING)
- [ ] R0GV3 decision: Option D (hardened exec + circuit breakers + redundant Safety/Consent)
- [ ] Amend C155: Execution agent failure rate target <2%
- [ ] Amend C155: Add circuit breaker specification
- [ ] Amend C155 + C158: Add Safety + Consent hot-standby
- [ ] Amend C155: Add false-safety-signal warning to monitoring design
- [ ] Run SIM-010 to validate fix
- [ ] Close #709

### 0.2 Resolve CT-001 (High)
- [ ] R0GV3 decision: Option D (detector 92%+ + double QEC pass)
- [ ] Amend BIOPHOTON_09: Detector efficiency spec ≥92%
- [ ] Amend BIOPHOTON_09: Add second QEC stage to CP-3 architecture
- [ ] Amend C160 Metric 26: Add methodology note referencing SIM-002
- [ ] Run SIM-008 to validate fix
- [ ] Close #707

### 0.3 Resolve CT-005 (High)
- [ ] R0GV3 decision: KG Gardening Pass spec
- [ ] Amend C156: Add KG Gardening Pass as required component
- [ ] Amend C156 schema: `last_validated`, `provenance_status`, `confidence_score` fields
- [ ] Run SIM-012 to validate fix
- [ ] Close #711

### 0.4 Resolve CT-002 (Medium-High)
- [ ] R0GV3 decision: Option D (access-pattern boosting + tiered storage)
- [ ] Amend C156: Memory schema fields `last_accessed`, `access_count`, `tier`
- [ ] Amend C160 Metric 6: Specify measurement window + tier scope
- [ ] Run SIM-009 to validate fix
- [ ] Close #708

### 0.5 Resolve CT-004 (Medium)
- [ ] R0GV3 decision: Option D (namespace sharding + async erasure queue)
- [ ] Amend C139: Namespace sharding specification
- [ ] Amend C139: Async erasure queue with SLA
- [ ] Amend C158: GDPR erasure SLA window + verification endpoint
- [ ] Run SIM-011 to validate fix
- [ ] Close #710

### 0.6 Integrate Research 003–008
- [ ] Receive R-003 through R-008 from R0GV3
- [ ] Commit to `research/`
- [ ] Cross-reference to canon docs
- [ ] Identify any new canon tensions → file issues

### 0.7 Full Integration Pre-Check
- [ ] Run SIM-013 (full system integration test, all layers)
- [ ] Confirm all `blocking-g14` issues closed
- [ ] Confirm `ALIGNMENT_MAP.md` fully green
- [ ] R0GV3 sign-off on G-14 readiness

---

## Phase 1 — G-14 Foundation (Agent + Memory Layer)

Builds on validated + amended canon.

### 1.1 Agent Stack Implementation
- [ ] Implement hardened C155 8-agent stack (post CT-003 resolution)
- [ ] Implement circuit breaker pattern
- [ ] Implement Safety + Consent hot-standby
- [ ] Integration test: SIM-010 parameters

### 1.2 Memory Architecture Implementation
- [ ] Implement C156 tiered hot/cold memory (post CT-002 resolution)
- [ ] Implement access-pattern relevance boosting
- [ ] Implement KG Gardening Pass (post CT-005 resolution)
- [ ] Integration test: SIM-009 + SIM-012 parameters

---

## Phase 2 — G-14 Knowledge + Privacy Layer

### 2.1 Knowledge Graph Build
- [ ] Implement C156 KG schema with maintenance fields
- [ ] Implement provenance re-anchoring on access
- [ ] Implement confidence re-validation cadence

### 2.2 Consent Ledger Build
- [ ] Implement C139 namespace-sharded consent ledger
- [ ] Implement async GDPR erasure queue
- [ ] Implement erasure verification endpoint
- [ ] Load test: SIM-011 parameters

---

## Phase 3 — G-14 Hardware + Metrics Layer

### 3.1 Biophotonic Transducer
- [ ] Source / spec CP-3 transducer with ≥92% detector efficiency
- [ ] Design double QEC pass architecture
- [ ] Validate: SIM-008 parameters

### 3.2 Metrics + Monitoring
- [ ] Implement C160 metrics dashboard
- [ ] Wire GCS (C157) live monitoring
- [ ] Wire false-safety-signal detection (from CT-003 finding)
- [ ] Wire BCI live monitoring (post CT-001 fix)

---

## Phase 4 — G-14 Integration + Stress Testing

### 4.1 Full Integration
- [ ] Run SIM-013: all layers simultaneously
- [ ] Run SIM-014: adversarial / edge-case stress
- [ ] Run SIM-015: long-horizon stability (1,000+ day)

### 4.2 G-14 Completion
- [ ] All SIM-008 through SIM-015 passed
- [ ] All canon tensions resolved
- [ ] CHANGELOG up to date
- [ ] R0GV3 sign-off on G-14 completion

---

## Simulation Queue (SIM-008 onward)

| # | Name | Trigger | Depends on |
|---|---|---|---|
| SIM-008 | BCI re-validation | CT-001 resolved | BIOPHOTON_09 + C160 amended |
| SIM-009 | Memory re-validation | CT-002 resolved | C156 + C160 amended |
| SIM-010 | Agent stack re-validation | CT-003 resolved | C155 + C158 amended |
| SIM-011 | Consent ledger re-validation | CT-004 resolved | C139 + C158 amended |
| SIM-012 | KG drift re-validation | CT-005 resolved | C156 amended |
| SIM-013 | Full integration test | All CTs resolved | All above |
| SIM-014 | Adversarial stress test | SIM-013 passed | Full system |
| SIM-015 | Long-horizon stability | SIM-014 passed | Full system |

---

*G-14 Work Order v1.0 — 2026-06-30. Update after each CT resolution and simulation completion.*
