# C160 — System Metrics Amendment (CT-002)

**Canon ID:** C160 (Amendment file — appended to C160 body)
**Status:** AMENDMENT — merged 2026-06-30
**CT ref:** CT-002 (Issue #708)
**Validated by:** SIM-009 (memory tiering, N=5,000)
**Amendment file:** `amendments/AMENDMENT_CT002_C156_C160_Memory_Tiering.md`

> *Note: C160 body is stored in the main C160 canon file. This amendment file updates Metric 6, confirmed by R0GV3 2026-06-30.*

---

## CT-002 — Metric 6 Revision (Memory Retention Rate)

### Metric 6 — Memory Retention Rate (Updated)

**Target: ≥85% retention at 30 days** (measured across HOT + WARM tiers only)

**Measurement window:** Rolling 30-day window.

**Tier scope:** HOT and WARM tier memories only. COLD tier memories are compressed and excluded from the retention rate calculation by design — they represent infrequently accessed content where compression is the intended behaviour.

**Retention definition:** A memory is 'retained' if its `relevance_score` is ≥0.50 and it is retrievable without decompression.

**Methodology note (added 2026-06-30, ref SIM-003, SIM-009):**

Under the original flat-decay model (no tiering), the ≥85% target was breached at days 16–18 for all memory types. With tiered storage and access-pattern boosting:
- HOT tier memories sustain ≥85% retention through day 60+
- WARM tier memories sustain ≥85% retention through approximately day 28
- HOT+WARM combined: **90.8% at day 30 ✅**

| Metric | SIM-003 (flat decay) | SIM-009 (tiered) |
|---|---|---|
| Retention at day 18 | ~83% ⚠️ | 98.0% ✅ |
| Retention at day 30 | ~61% ⚠️ | **90.8% ✅** |
| Metric 6 target met | No | **Yes** |

Canon tension CT-002 (Issue #708) documents the full analysis. Issue #708 closed.

*CT-002 amendment merged into C160 — 2026-06-30 by GAIA. Approved by R0GV3.*
