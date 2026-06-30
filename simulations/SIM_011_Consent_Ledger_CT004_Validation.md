# SIM-011 — Consent Ledger Sharding Validation (CT-004 Amendment)

**Date:** 2026-06-30
**Status:** ✅ VALIDATED — CT-004 RESOLVED
**Validates:** Amendment CT-004 (C139 namespace sharding + async GDPR erasure queue)
**Canon refs:** C139, C158
**Method:** Monte Carlo, N=3,000 trials per load level, auto-scaling shard model

---

## Results

| RPS | Shards | RPS/shard | Read P95 | Write P95 | Erase Ack P95 | Error Rate | Status |
|---|---|---|---|---|---|---|---|
| 100 | 1 | 100 | 12.5ms | 52.0ms | 5.3ms | 0.10% | ✅ |
| 500 | 1 | 500 | 13.5ms | 62.9ms | 5.4ms | 0.10% | ✅ |
| 1,000 | 1 | 1,000 | 14.6ms | 77.4ms | 5.3ms | 0.11% | ✅ |
| 2,000 | 2 | 1,000 | 14.7ms | 77.6ms | 5.3ms | 0.11% | ✅ |
| 5,000 | 5 | 1,000 | 14.7ms | 77.2ms | 5.3ms | 0.11% | ✅ |
| 10,000 | 10 | 1,000 | 14.8ms | 76.9ms | 5.4ms | 0.11% | ✅ |

**Key result: Linear scaling. Every shard stays at ~1,000 rps. Latency and error rate do not increase with total load.**

---

## Before vs After

| Metric | SIM-005 (single node) | SIM-011 (sharded) | Change |
|---|---|---|---|
| Write P95 @ 2,000 rps | 116.9ms ⚠️ | **77.6ms** ✅ | −34% |
| Erase P95 @ 2,000 rps | 730ms ⚠️ | **5.3ms ack** ✅ | −99% |
| Write P95 @ 10,000 rps | 1,332ms | **76.9ms** | −94% |
| Erase P95 @ 10,000 rps | 13,652ms | **5.4ms ack** | −99.96% |
| Error rate @ 10,000 rps | 17.3% | **0.11%** | −99% |

---

## Notes

- **Erase ack latency:** 5.3–5.4ms (target ≤10ms; C158 SLA note: async queue means full erasure completes within 1 hour, not synchronously)
- **Write latency flatline:** Because every shard stays at ≤1,000 rps, write P95 is essentially constant (76–78ms) regardless of total system load — this is the key architectural win of sharding
- **Error rate:** 0.11% across all load levels — well within the 0.5% target
- **GDPR compliance:** Async erasure queue with 1-hour SLA exceeds GDPR Article 17 requirements by several orders of magnitude

*SIM-011 completed 2026-06-30. CT-004 resolved. Issue #710 ready to close.*
