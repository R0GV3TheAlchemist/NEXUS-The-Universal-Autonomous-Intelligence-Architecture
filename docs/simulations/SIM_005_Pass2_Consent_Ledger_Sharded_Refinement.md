# SIM-005 Pass 2 — Consent Ledger Sharded Architecture Refinement

**Pass Classification:** Pass 2 — Refinement  
**Simulation number:** SIM-005  
**Date filed:** 2026-06-30  
**Phase:** G-15 — The Rhythm Phase  
**Resolves:** CT-004 (#710)  
**Protocol:** SIMULATION_VALIDATION_PROTOCOL.md

---

## Pass Context

**What Pass 1 (SIM-005) revealed:**
- Consent ledger performs within targets at ≤1,000 rps
- GDPR erasure breaches compliance at 2,000+ rps (730ms at 2k, 13,652ms at 10k)
- Root cause: single-node implicit assumption in C139 — no sharding, no async erasure
- Error rate acceptable at ≤2,000 rps; catastrophic at 5,000+

**How the design was adjusted (Option D — accepted 2026-06-30):**
- Namespace sharding: each shard handles ≤1,000 rps
- Async GDPR erasure queue with guaranteed SLA completion window
- Erasure status endpoint for user verification

---

## Refinement Hypotheses

1. With namespace sharding (each shard ≤1,000 rps), write P95 stays ≤100ms at aggregate 10,000 rps
2. Async erasure queue brings GDPR erase P95 within a 1-hour SLA at all load levels
3. Error rate stays ≤0.5% at 10,000 rps aggregate with sharding
4. Shard routing overhead does not add >10ms to write P95 at baseline

---

## Parameters

| Parameter | Value |
|---|---|
| Shard count | 10 (one per 1,000 rps at peak load) |
| Aggregate load levels | 1k, 2k, 5k, 10k, 20k rps |
| Erasure queue SLA window | 1 hour |
| Erasure queue throughput | Async; batch processing every 60s |
| Shard routing overhead model | Consistent hash; ≤10ms added latency |
| N trials per load level | 5,000 |

---

## Success Conditions

- Write P95 ≤100ms at ≤10,000 rps aggregate
- GDPR erasure completes within 1-hour SLA at all load levels
- Error rate ≤0.5% at 10,000 rps
- Shard routing overhead ≤10ms at baseline

## Failure Conditions

- Write P95 breaches 100ms below 10,000 rps → shard count insufficient; increase shards or review routing
- Erasure queue backlog exceeds 1-hour SLA → async batch interval too long; review queue throughput
- Error rate breaches 0.5% → shard consistency issue; review hash distribution

---

## Output Artefacts

- `simulations/SIM_005_Pass2_consent_ledger_sharded.py`
- `simulations/SIM_005_Pass2_consent_ledger_sharded_results.md`
- `simulations/consent_ledger_sharded_throughput.png`

## Canon Gate

Pass 2 success → proceed to Pass 3 verification with expanded load range and SLA stress test.  
Pass 3 success → amend C139 (sharding spec) + C158 (GDPR SLA) + close CT-004 (#710).

---

*Filed 2026-06-30. CT-004 Option D. Three-Pass Protocol. 🌿*
