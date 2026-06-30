# SIM-010 Pass 2 — Agent Stack Hardening Refinement

**Pass Classification:** Pass 2 — Refinement  
**Simulation number:** SIM-010  
**Date filed:** 2026-06-30  
**Phase:** G-15 — The Rhythm Phase  
**Resolves:** CT-003 (#709)  
**Protocol:** SIMULATION_VALIDATION_PROTOCOL.md

---

## Pass Context

**What Pass 1 (SIM-004) revealed:**
- Cascade failure rate 7.0% at baseline load (target: <5%) — sovereignty safety issue
- Sovereignty conflict rate 2.8% at baseline (barely within 3% limit)
- False safety signal: sovereignty conflicts *decline* at extreme load because Execution fails so completely it never runs — standard monitoring shows "improving" compliance during catastrophic failure
- Root cause: Execution agent 5% base failure rate at end of 4-node dependency chain; cascade propagation

**How the design was adjusted (Option D — accepted, Canon Amendment CT-003 #712):**
- Execution agent hardened to <2% base failure rate
- Circuit Breaker pattern on Orchestrator (CLOSED/OPEN/HALF-OPEN; trips at 3 failures in 30s)
- Safety + Consent hot-standby redundant pairs (≤500ms failover)
- False-safety-signal monitoring: `SOVEREIGNTY_MONITORING_DEGRADED` alert when Execution health <98% AND sovereignty conflicts = 0%

---

## Refinement Hypotheses

1. With Option D hardening, cascade failure rate ≤4% at baseline load (target <5%)
2. Sovereignty conflict rate stays <3% at baseline and x1.5 load
3. `SOVEREIGNTY_MONITORING_DEGRADED` alert fires correctly when Execution fails silently at x5.0+ load
4. Circuit breaker prevents cascade propagation — failure isolation confirmed
5. Hot-standby failover ≤500ms — no sovereignty gap during failover window
6. P95 latency stays ≤200ms at x1.5 load

---

## Parameters

| Parameter | Value |
|---|---|
| Execution agent base failure rate | 2% (hardened from 5%) |
| Circuit breaker trip threshold | 3 consecutive failures in 30s |
| Circuit breaker states | CLOSED / OPEN / HALF-OPEN |
| Hot-standby failover target | ≤500ms |
| False-safety-signal threshold | Execution health <98% AND sovereignty conflicts = 0% |
| Load levels tested | x1.0, x1.5, x2.0, x5.0, x10.0 |
| N trials per load level | 10,000 |

---

## Success Conditions

- Cascade failure ≤4% at x1.0 baseline
- Sovereignty conflicts <3% at x1.0 and x1.5
- `SOVEREIGNTY_MONITORING_DEGRADED` fires at x5.0+ load
- Circuit breaker isolates failure — cascade does not propagate beyond tripped agent
- Failover ≤500ms confirmed
- P95 latency ≤200ms at x1.5

## Failure Conditions

- Cascade failure >4% at baseline → Execution hardening insufficient; review agent architecture
- Sovereignty conflicts breach 3% at baseline → hot-standby not covering gap; review failover logic
- False-safety-signal alert does NOT fire at x5.0 → monitoring logic error; halt and review
- Circuit breaker does not isolate → architecture review required before Pass 3

---

## Output Artefacts

- `simulations/SIM_010_Pass2_agent_stack_hardening.py`
- `simulations/SIM_010_Pass2_agent_stack_hardening_results.md`
- `simulations/agent_stack_hardening_stress.png`

## Canon Gate

Pass 2 success → proceed to Pass 3 verification at x3.0 and x7.0 load stress.  
Pass 3 success → merge Canon Amendment CT-003 into C155 + C158 + close CT-003 (#709).

---

*Filed 2026-06-30. CT-003 Option D. Three-Pass Protocol. 🌿*
