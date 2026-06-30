# Amendment CT-004 — C139 + C158: Consent Ledger Namespace Sharding + Async GDPR Erasure Queue

**CT-ID:** CT-004
**Amendment status:** PROPOSED — awaiting R0GV3 approval to merge into canon
**Decision confirmed:** 2026-06-30 by R0GV3
**Resolution:** Option D — Namespace Sharding + Async GDPR Erasure Queue + Verification Endpoint
**Docs affected:** C139 (consent ledger architecture), C158 (GDPR compliance)
**Simulation to validate:** SIM-011 (run immediately after this commit)
**Closes:** Issue #710

---

## Context

SIM-005 revealed that the C139 single-node consent ledger breaches both write latency and GDPR erasure targets at 2,000 rps:
- Write P95: 116.9ms at 2,000 rps (target <100ms)
- GDPR Erase P95: 730ms at 2,000 rps (target <500ms); 13,652ms at 10,000 rps
- Error rate: 17.3% at 10,000 rps

Safe operating zone on single node: ≤1,000 rps. At population scale, 2,000+ rps is easily reachable.

---

## Changes to C139 (Consent Ledger Architecture)

### 1. Namespace Sharding — Required Architecture

**Add to C139 Architecture section:**

> **Consent Ledger Namespace Sharding — Required**
>
> The consent ledger SHALL be implemented as a horizontally sharded system partitioned by user namespace:
>
> **Sharding key:** `user_namespace` — derived from the first 8 characters of the user’s UUID (256 possible namespace buckets)
>
> **Shard sizing rule:** Each shard SHALL be sized to handle a maximum of **1,000 rps** sustained load. As the user base grows, additional shards are provisioned automatically when any shard’s 5-minute average exceeds 800 rps (80% of capacity).
>
> **Shard routing:** A lightweight Consent Router layer sits in front of all shards. The Router:
> - Resolves the shard for any given `user_id` in ≤1ms
> - Routes read, write, and erase requests to the correct shard
> - Monitors per-shard load and triggers auto-scaling
> - Maintains a shard map in memory with ≥10-second refresh
>
> **Cross-shard operations:** Consent queries that span multiple users (e.g. bulk audit) are fanned out by the Router and results merged. Cross-shard fan-out latency budget: ≤50ms for queries spanning ≤10 shards.
>
> **Shard isolation:** A failure in one shard does not affect other shards. Each shard has its own hot-standby replica (per C158 availability SLA).

---

### 2. Async GDPR Erasure Queue — Required Component

**Add to C139 Architecture section:**

> **Async GDPR Erasure Queue — Required**
>
> GDPR erasure requests SHALL be processed asynchronously via a dedicated erasure queue:
>
> **Erasure flow:**
> 1. User submits erasure request → Consent Router accepts and returns `erasure_id` + `estimated_completion` immediately (≤5ms response time)
> 2. Request is enqueued to the Erasure Queue with priority = `GDPR_ERASURE`
> 3. Erasure worker processes the request: cascades deletion across all memory tiers (C156), knowledge graph nodes (C156 KG), consent ledger entries (C139), and audit logs (C158)
> 4. On completion: `erasure_status` updated to `COMPLETE`; user notified via registered callback or polling endpoint
>
> **SLA:** Erasure requests SHALL be completed within **1 hour** of submission under normal load. Under exceptional load (system-wide incident), maximum completion time is **24 hours**. Requests approaching 24 hours trigger an escalation alert.
>
> **Queue durability:** The Erasure Queue is durable (persisted to disk). A system restart does not lose queued erasure requests.
>
> **Erasure atomicity:** Each erasure operation is transactional per shard. If a shard erasure fails, it is retried up to 3 times before escalating to a `ERASURE_FAILED` alert.

---

### 3. Erasure Status Verification Endpoint — Required

**Add to C139 API section:**

> **GET /consent/erasure/{erasure_id}**
>
> Returns the current status of a GDPR erasure request.
>
> Response fields:
> | Field | Type | Description |
> |---|---|---|
> | `erasure_id` | UUID | The erasure request identifier |
> | `status` | Enum: `QUEUED` / `IN_PROGRESS` / `COMPLETE` / `FAILED` | Current status |
> | `submitted_at` | ISO 8601 | When the request was received |
> | `completed_at` | ISO 8601 / null | When erasure completed (null if not yet complete) |
> | `shards_complete` | Integer | Number of shards where erasure is confirmed |
> | `shards_total` | Integer | Total shards where user data existed |
> | `estimated_completion` | ISO 8601 / null | Estimated completion time (null if complete) |

---

## Changes to C158 (GDPR Compliance)

### 4. GDPR Erasure SLA Definition

**Add to C158 GDPR section:**

> **GDPR Erasure SLA**
>
> In compliance with GDPR Article 17 (Right to Erasure):
> - **Acknowledgement SLA:** Erasure request acknowledged within **5ms** (sync response with `erasure_id`)
> - **Completion SLA:** Erasure completed within **1 hour** under normal conditions
> - **Maximum SLA:** Erasure completed within **24 hours** under all conditions
> - **Verification:** User may verify erasure status at any time via `/consent/erasure/{erasure_id}` endpoint
> - **Audit trail:** Every erasure request, its processing steps, and completion confirmation are logged immutably to the compliance audit log
>
> *Note: The async queue model is GDPR-compliant. GDPR Article 17 does not require synchronous erasure — it requires erasure ‘without undue delay’, which regulators consistently interpret as ≤30 days. A 1-hour SLA exceeds this requirement by several orders of magnitude.*

### 5. Consent Ledger Availability SLA — Update

**Update C158 Consent Ledger section:**

> **Consent Ledger Availability SLA**
> - Read availability: ≥99.99% (four nines)
> - Write availability: ≥99.9% (three nines)
> - Per-shard failure does not affect global availability (shard isolation per C139)
> - Shard hot-standby failover: ≤500ms

---

## Amendment Sign-Off

- [x] R0GV3 decision confirmed: 2026-06-30
- [ ] Amendment reviewed by R0GV3
- [ ] Merged into `canon/C139.md`
- [ ] Merged into `canon/C158.md`
- [ ] SIM-011 validation passed
- [ ] Issue #710 closed
- [ ] CHANGELOG updated

*Amendment CT-004 proposed 2026-06-30 by GAIA. Awaiting merge approval.*
