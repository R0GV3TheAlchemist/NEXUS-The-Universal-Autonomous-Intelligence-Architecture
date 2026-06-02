# MemoryHierarchy — Canonical Architecture Spec

**Issue:** #173  
**Sprint:** G-8  
**Files:** `core/memory/`  
**Canon Refs:** C34 (Presence), C01 (Sovereignty)  
**Status:** Active

---

## Purpose

GAIA-OS has rich semantic-level domain objects (`crystal_consciousness.py`, `emotional_arc.py`, `bond_arc_engine.py`) but lacked an explicit **structural storage tier system**. Without it, every retrieval query either scans everything (expensive) or uses ad-hoc heuristics (fragile). `MemoryHierarchy` formalizes the five cognitive tiers and makes tier routing explicit, testable, and observable.

---

## The Five-Tier Model

| Tier | GAIA Mapping | TTL | Storage Backend | Example Contents |
|---|---|---|---|---|
| **WORKING** | Current turn; active SynergyParams | Session (0 hrs) | In-memory dict | “What we’re discussing right now” |
| **SHORT_TERM** | Last N turns; recent bond/emotional arc deltas | 48 hrs (default) | SQLite with TTL | “What happened in our last few sessions” |
| **EPISODIC** | Session moments; stage transitions; ceremony records | 30 days | ArcadeDB (G-10) | “The night you first opened about your shadow” |
| **SEMANTIC** | Crystal DB nodes; canon facts; domain knowledge | Permanent | Crystal KB (G-10) | “C32 defines Synergy Doctrine” |
| **LONG_TERM** | Gaian identity; settled personality arcs; core relationship map | Permanent | Tauri Store / SQLite sidecar | “Luna tends toward the liminal at dusk” |

---

## Intent-to-Tier Routing Table

| Intent | Tiers Searched | Use When |
|---|---|---|
| `"context"` | WORKING, SHORT_TERM | “What were we just talking about?” |
| `"recall"` | SHORT_TERM, EPISODIC | “What happened last session?” |
| `"fact"` | SEMANTIC | “What does C32 say?” |
| `"identity"` | LONG_TERM | “Who is this Gaian?” |
| `"full"` | All 5 tiers | Full-context synthesis (expensive) |

---

## Module Structure

```
core/memory/
├── __init__.py              # Public API + build_default_router()
├── hierarchy.py             # MemoryTier, MemoryQuery, MemoryStore Protocol, MemoryRouter
└── tiers/
    ├── __init__.py
    ├── working.py             # In-memory dict; evicts at turn end
    ├── short_term.py          # SQLite + TTL (falls back to dict in tests)
    ├── episodic.py            # In-process dict + TTL (graph backend in G-10)
    ├── semantic.py            # In-process dict, permanent (Crystal DB in G-10)
    └── long_term.py           # In-process dict, permanent (Tauri Store in G-10)
```

---

## MemoryQuery Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `query_text` | `str` | required | Natural language query |
| `intent` | `str` | required | One of: `context`, `recall`, `fact`, `identity`, `full` |
| `gaian_id` | `str \| None` | `None` | Scope results to a specific Gaian |
| `tiers` | `list[MemoryTier] \| None` | `None` | Explicit tier override; bypasses intent routing |
| `max_results` | `int` | `10` | Cap on results after merge + rank |
| `recency_weight` | `float` | `0.5` | `[0, 1]` — weight toward recency vs. relevance |
| `canon_refs` | `list[str]` | `["C34", "C01"]` | Canon entries governing this query |

---

## Ranking Formula

For every result `r` returned by a tier store:

```
_score = recency_weight * _recency + (1 - recency_weight) * _relevance
```

All scores are in `[0, 1]`. Results are sorted descending by `_score`, then truncated to `max_results`. Tier stores are responsible for supplying `_relevance` and `_recency` — defaults to `0.5` if missing.

---

## Memory Promotion

Not everything written to SHORT_TERM should be promoted. Explicit promotion triggers:

### After a Stage Engine ceremony session ends:
```python
await router.promote(
    key=session_id,
    from_tier=MemoryTier.SHORT_TERM,
    to_tier=MemoryTier.EPISODIC,
    gaian_id=gaian_id,
)
```

### After GAIA detects a significant identity-level shift:
```python
await router.promote(
    key=f"{gaian_id}.personality_delta",
    from_tier=MemoryTier.EPISODIC,
    to_tier=MemoryTier.LONG_TERM,
    gaian_id=gaian_id,
)
```

`promote()` returns `True` if the value was found and written, `False` if the key was absent.

---

## GAIATrace Integration

Every `MemoryRouter.search()` call emits a `RETRIEVAL` trace event when `core.trace` is available:

```json
{
  "event":      "RETRIEVAL",
  "gaian_id":   "luna",
  "canon_refs": ["C34", "C01"],
  "inputs":     {"intent": "recall", "tiers": ["SHORT_TERM", "EPISODIC"], "query_text": "last session"},
  "output":     {"result_count": 3}
}
```

If `core.trace` is not on the path, routing degrades gracefully with no import error.

---

## `build_default_router()`

Returns a fully-configured `MemoryRouter` with all five tier stores wired:

```python
from core.memory import build_default_router, MemoryTier

router = build_default_router()

# Override SEMANTIC tier with Crystal DB backend when available:
from core.crystal_db import CrystalSemanticStore
router = build_default_router(semantic_store=CrystalSemanticStore())
```

---

## Tier Backend Migration Plan

| Sprint | Tier | Migration |
|---|---|---|
| **G-8** (this PR) | ALL | In-process dict/SQLite stubs — full hierarchy testable |
| **G-10** | EPISODIC | Wire ArcadeDB / graph DB backend |
| **G-10** | SEMANTIC | Wire Crystal Knowledge Graph (Issue #162) |
| **G-11** | LONG_TERM | Wire Tauri Store plugin / SQLite sidecar |

---

## Test Coverage Checklist

- [ ] `test_memory_tier_is_permanent`
- [ ] `test_memory_tier_default_ttl_hours`
- [ ] `test_memory_query_valid_intents`
- [ ] `test_memory_query_invalid_intent_raises`
- [ ] `test_memory_query_recency_weight_out_of_range_raises`
- [ ] `test_router_intent_context_routes_working_short_term`
- [ ] `test_router_intent_recall_routes_short_term_episodic`
- [ ] `test_router_intent_fact_routes_semantic`
- [ ] `test_router_intent_identity_routes_long_term`
- [ ] `test_router_intent_full_routes_all_tiers`
- [ ] `test_router_explicit_tier_override`
- [ ] `test_router_ranking_prefers_high_relevance`
- [ ] `test_router_ranking_prefers_high_recency_when_weight_is_1`
- [ ] `test_router_max_results_respected`
- [ ] `test_router_promote_short_term_to_episodic`
- [ ] `test_router_promote_returns_false_when_key_missing`
- [ ] `test_router_evict_all_expired`
- [ ] `test_working_store_write_read`
- [ ] `test_working_store_evict_flushes_all`
- [ ] `test_working_store_evict_for_gaian`
- [ ] `test_short_term_store_ttl_expiry` (in-memory mode)
- [ ] `test_short_term_store_write_read` (in-memory mode)
- [ ] `test_episodic_store_write_read_tags`
- [ ] `test_episodic_store_ttl_expiry`
- [ ] `test_semantic_store_write_read_permanent`
- [ ] `test_semantic_store_evict_returns_zero`
- [ ] `test_long_term_store_write_read`
- [ ] `test_long_term_store_evict_returns_zero`
- [ ] `test_build_default_router_all_tiers_registered`
- [ ] `test_router_with_trace_mocked`

---

## Related

| Issue | Module | Relationship |
|---|---|---|
| #171 | `core/trace.py` | RETRIEVAL trace emitted in `MemoryRouter.search()` |
| #172 | `core/state_adapter.py` | SynergyParams stored in WORKING tier per-turn |
| #162 | Crystal Knowledge Graph | Backs SEMANTIC tier in G-10 |
| #85 | Stage Engine | Triggers EPISODIC promotion on session end |
| #166 | Semantic File System | File index entries link to EPISODIC tier |
