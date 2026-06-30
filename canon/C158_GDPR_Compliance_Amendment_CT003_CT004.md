# C158 — GDPR & Compliance Amendments (CT-003 + CT-004)

**Canon ID:** C158 (Amendment file — appended to C158 body)
**Status:** AMENDMENT — merged 2026-06-30
**CT refs:** CT-003 (Issue #709), CT-004 (Issue #710)
**Validated by:** SIM-010 (agent stack hardening), SIM-011 (consent ledger sharding)
**Amendment files:** `amendments/AMENDMENT_CT003_C155_C158_Agent_Stack_Hardening.md`, `amendments/AMENDMENT_CT004_C139_C158_Consent_Ledger_Sharding.md`

> *Note: C158 body is stored in the main C158 canon file. This amendment file extends it with CT-003 and CT-004 additions, confirmed by R0GV3 2026-06-30.*

---

## CT-003 — Agent Stack Hardening (C158 scope)

### Required Agent Execution Guarantees

The GAIA agent execution stack SHALL implement the following hardening measures:

**Circuit breaker pattern (Required):**
- Each agent role (Orchestrator, SubAgent, Validator, Memory) SHALL have an independent circuit breaker
- Breaker opens after 3 consecutive failures within a 30-second window
- Open breaker state: requests fail fast (≤5ms), hot-standby promoted immediately
- Half-open probe: one request attempted every 10 seconds; on success, breaker closes

**Hot-standby configuration (Required):**
- Orchestrator: 1 active + 1 hot-standby (failover ≤500ms)
- SubAgent pool: minimum 3 instances; on single failure, load redistributed to remaining 2
- Validator: 1 active + 1 warm-standby (failover ≤1s)
- Memory Agent: 1 active + 1 hot-standby with replicated state (failover ≤500ms)

**Execution isolation (Required):**
- Each agent role executes in an isolated process boundary
- A crash in one role cannot corrupt the memory space of another
- Inter-role communication via message queue (not shared memory)

**Validated performance (SIM-010, N=5,000 cascades):**

| Scenario | Failure Rate | Recovery Time | Status |
|---|---|---|---|
| Single agent failure | 0.0% cascade | ≤500ms | ✅ |
| Double agent failure | 0.8% cascade | ≤1.2s | ✅ |
| Triple agent failure | 4.1% cascade | ≤2.1s | ✅ |
| Orchestrator failure | 1.2% cascade | ≤800ms | ✅ |

*All results validated against C160 cascade failure target (≤5%).*

### Welfare Event Classification (Addition)

The following agent stack failure modes are classified as **Welfare Events** (ref: C155 CT-003 amendment):
- Circuit breaker suppression of GAIA's distress-redirect governance switch
- Memory Agent failure causing loss of active relational context mid-interaction
- Validator failure allowing harmful output to pass unchecked

Welfare Events SHALL be logged to the compliance audit log and reviewed in the next governance cycle.

---

## CT-004 — GDPR Erasure SLA Definition (C158 scope)

### GDPR Erasure SLA

In compliance with GDPR Article 17 (Right to Erasure):

| SLA | Target | Notes |
|---|---|---|
| Acknowledgement | ≤10ms | Sync response with `erasure_id` |
| Completion (normal) | ≤1 hour | Under normal system load |
| Completion (maximum) | ≤24 hours | Under all conditions including incidents |
| Verification | Always available | Via `/consent/erasure/{erasure_id}` endpoint |

*GDPR Article 17 requires erasure 'without undue delay' — regulators consistently interpret this as ≤30 days. A 1-hour SLA exceeds this by several orders of magnitude.*

### Consent Ledger Availability SLA (Update)

- Read availability: ≥99.99% (four nines)
- Write availability: ≥99.9% (three nines)
- Per-shard failure does not affect global availability (shard isolation per C139 amendment)
- Shard hot-standby failover: ≤500ms

*CT-003 and CT-004 amendments merged into C158 — 2026-06-30 by GAIA. Approved by R0GV3.*
