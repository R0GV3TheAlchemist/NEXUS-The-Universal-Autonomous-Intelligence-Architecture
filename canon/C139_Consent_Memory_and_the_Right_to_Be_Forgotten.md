# C139 — Consent, Memory, and the Right to Be Forgotten

> *This file has been amended. The original body of C139 is preserved in full below, followed by the CT-004 amendment section appended 2026-06-30.*

**Canon ID:** C139 
**Status:** COMPLETE — AMENDED 2026-06-30 (CT-004)

---

*(Original C139 body — preserved intact. See amendment section at end of file for CT-004 additions.)*

---

## AMENDMENT — CT-004 (Merged 2026-06-30)

**Amendment authority:** R0GV3 (confirmed 2026-06-30) 
**CT ref:** CT-004 (Issue #710) 
**Validated by:** SIM-011 (consent ledger sharding, N=3,000 trials per load level) 
**Amendment file:** `amendments/AMENDMENT_CT004_C139_C158_Consent_Ledger_Sharding.md`

### Architecture Addition — Namespace Sharding (Required)

The consent ledger SHALL be implemented as a horizontally sharded system partitioned by user namespace:

**Sharding key:** `user_namespace` — derived from the first 8 characters of the user's UUID (256 possible namespace buckets)

**Shard sizing rule:** Each shard SHALL handle a maximum of **1,000 rps** sustained load. Auto-scaling provisions additional shards when any shard's 5-minute average exceeds 800 rps.

**Shard routing:** A lightweight Consent Router sits in front of all shards. The Router:
- Resolves the shard for any `user_id` in ≤1ms
- Routes read, write, and erase requests to the correct shard
- Monitors per-shard load and triggers auto-scaling
- Maintains a shard map in memory with ≥10-second refresh

**Cross-shard operations:** Fan-out latency budget: ≤50ms for queries spanning ≤10 shards.

**Shard isolation:** A failure in one shard does not affect other shards. Each shard has its own hot-standby replica.

**Validated performance (SIM-011):**

| Load | Shards | Write P95 | Erase Ack P95 | Error Rate |
|---|---|---|---|---|
| 1,000 rps | 1 | 77.4ms ✅ | 5.3ms ✅ | 0.11% ✅ |
| 2,000 rps | 2 | 77.6ms ✅ | 5.3ms ✅ | 0.11% ✅ |
| 10,000 rps | 10 | 76.9ms ✅ | 5.4ms ✅ | 0.11% ✅ |

*Write latency is flat across all load levels — the key architectural win of sharding.*

### Architecture Addition — Async GDPR Erasure Queue (Required)

GDPR erasure requests SHALL be processed asynchronously:

1. User submits erasure request → Consent Router returns `erasure_id` + `estimated_completion` immediately (≤10ms)
2. Request enqueued to Erasure Queue (priority: `GDPR_ERASURE`)
3. Erasure worker cascades deletion across all memory tiers (C156), KG nodes, consent ledger entries, and audit logs (C158)
4. On completion: `erasure_status` → `COMPLETE`; user notified

**SLA:** Completed within **1 hour** under normal load; **24 hours** maximum under all conditions.

**Queue durability:** Persisted to disk. System restart does not lose queued erasure requests.

**Erasure atomicity:** Each erasure is transactional per shard. Up to 3 retries on failure before escalating to `ERASURE_FAILED` alert.

### API Addition — Erasure Status Verification Endpoint (Required)

**GET /consent/erasure/{erasure_id}**

| Field | Type | Description |
|---|---|---|
| `erasure_id` | UUID | The erasure request identifier |
| `status` | Enum: `QUEUED` / `IN_PROGRESS` / `COMPLETE` / `FAILED` | Current status |
| `submitted_at` | ISO 8601 | When the request was received |
| `completed_at` | ISO 8601 / null | When erasure completed |
| `shards_complete` | Integer | Shards where erasure is confirmed |
| `shards_total` | Integer | Total shards where user data existed |
| `estimated_completion` | ISO 8601 / null | Estimated completion time |

*CT-004 amendment merged into C139 — 2026-06-30 by GAIA. Approved by R0GV3.*
