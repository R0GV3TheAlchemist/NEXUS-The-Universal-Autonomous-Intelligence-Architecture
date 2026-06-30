# C156 — Memory Architecture Amendments (CT-002 + CT-005)

**Canon ID:** C156 (Amendment file — appended to C156 body)
**Status:** AMENDMENT — merged 2026-06-30
**CT refs:** CT-002 (Issue #708), CT-005 (Issue #711)
**Validated by:** SIM-009 (memory tiering, N=5,000), SIM-012 (KG drift, N=2,000)
**Amendment files:** `amendments/AMENDMENT_CT002_C156_C160_Memory_Tiering.md`, `amendments/AMENDMENT_CT005_C156_KG_Gardening_Pass.md`

> *Note: C156 body is stored in the main C156 canon file. This amendment file extends it with CT-002 and CT-005 additions, confirmed by R0GV3 2026-06-30.*

---

## CT-002 — Memory Tiering + Access-Pattern Boosting

### Required Memory Record Fields (Addition to C156 Schema)

Every memory record SHALL carry the following required fields:

| Field | Type | Description |
|---|---|---|
| `memory_id` | UUID | Unique identifier (existing) |
| `created_at` | ISO 8601 | Creation timestamp (existing) |
| `content_hash` | SHA-256 | Content integrity check (existing) |
| `tier` | Enum: `HOT` / `WARM` / `COLD` | Current storage tier **(new)** |
| `last_accessed` | ISO 8601 | Most recent access timestamp **(new)** |
| `access_count` | Integer | Cumulative access count **(new)** |
| `relevance_score` | Float [0.0, 1.0] | Current computed relevance **(new)** |
| `decay_rate` | Float | Active tier-adjusted decay rate **(new)** |
| `tier_upgraded_at` | ISO 8601 / null | Timestamp of last tier upgrade **(new)** |

### Tiered Storage Architecture

| Tier | Retention window | Decay rate | Access threshold |
|---|---|---|---|
| `HOT` | 60 days full retention | λ = 0.01/day | ≥5 accesses in last 7 days |
| `WARM` | 30 days full retention | λ = 0.03/day | 1–4 accesses in last 7 days |
| `COLD` | Compressed after day 18 | λ = 0.07/day | 0 accesses in last 7 days |

**Tier assignment rules:**
- New memories start in `WARM` tier
- Tier re-evaluated every 7 days based on rolling access window
- Promotion: COLD → WARM → HOT on threshold met; demotion: HOT → WARM → COLD if threshold not met for 14 consecutive days
- Tier upgrade resets the decay clock for that tier's retention window

### Access-Pattern Relevance Boosting

On each memory access:
1. `last_accessed` → current timestamp
2. `access_count` → incremented by 1
3. `relevance_score` recalculated: `min(1.0, relevance_score + 0.05 × recency_weight)`
   - `recency_weight` = 1.0 (within 24h), 0.5 (1–7 days), 0.2 (7–30 days)
4. If `access_count` meets tier promotion threshold: schedule tier upgrade at next 7-day evaluation

**Validated retention (SIM-009, N=5,000):**

| Day | HOT | WARM | HOT+WARM | Status |
|---|---|---|---|---|
| 18 | 100.0% | 96.1% | 98.0% | ✅ |
| 30 | 100.0% | 81.5% | **90.8%** | ✅ C160 Metric 6 target met |
| 60 | 100.0% | 58.5% | 79.2% | Outside measurement window |

---

## CT-005 — Knowledge Graph Gardening Pass

### KG Gardening Pass — Required Maintenance Cycle

A **KG Gardening Pass** SHALL be executed every **50 reasoning cycles** (not every 100 as previously implied by omission of this requirement).

**Pass operations:**
1. **Orphan node detection:** Identify nodes with zero inbound + zero outbound edges → flag for review
2. **Weak edge pruning:** Remove edges with confidence score < 0.10 and not accessed in ≥30 days
3. **Duplicate consolidation:** Merge near-duplicate nodes (semantic similarity > 0.95) into canonical node, preserve provenance trail
4. **Provenance re-anchoring:** For any node whose provenance chain has become broken or circular, attempt re-anchoring from source canon; if unresolvable, flag as `PROVENANCE_UNCERTAIN`
5. **Cycle detection:** Identify reasoning cycles > 3 hops that have no resolution path → escalate to `KG_CYCLE_ALERT`

**Gardening Pass SLA:** Complete within 200ms for graphs up to 10,000 nodes; within 2s for graphs up to 100,000 nodes.

**Validated stability (SIM-012, N=2,000 reasoning cycles):**
- Without Gardening Pass: provenance collapse begins cycle 29, reaches 0% by cycle 85
- With 50-cycle Gardening Pass: provenance stability maintained >95% through cycle 2,000 ✅
- Orphan node rate held below 2% throughout ✅

*CT-002 and CT-005 amendments merged into C156 — 2026-06-30 by GAIA. Approved by R0GV3.*
