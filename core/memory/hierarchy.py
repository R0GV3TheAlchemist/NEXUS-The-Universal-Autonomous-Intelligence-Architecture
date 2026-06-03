"""
core/memory/hierarchy.py
GAIA Memory Hierarchy — Sprint G-8

Formalizes five cognitive memory tiers and a MemoryRouter that directs
retrieval queries to the correct tier(s) rather than searching everything.
This makes memory retrieval cost-predictable and retrieval logic testable.

Canon Refs:
  C34  Presence — GAIA knows what tier of memory a moment belongs to.
  C01  Sovereignty — memory routing is explicit and auditable.

Design principles:
  1. NO call site outside this package may choose tiers ad-hoc.
     All routing goes through MemoryRouter.search() or MemoryRouter.write().
  2. MemoryStore implementations are injected (never instantiated here).
     This keeps the routing layer pure and independently testable.
  3. Ranking is deterministic given fixed recency_weight.
     The scoring formula is specified in _rank() and in the spec.
"""
from __future__ import annotations

import asyncio
import logging
from enum import Enum, auto
from typing import Any, Protocol, runtime_checkable

log = logging.getLogger(__name__)

# ── Optional GAIATrace integration ─────────────────────────────────────── #
try:
    from core.trace import AsyncGAIATrace, TraceEventType
    _TRACE_AVAILABLE = True
except ImportError:
    _TRACE_AVAILABLE = False


# ── MemoryTier ────────────────────────────────────────────────────────────── #

class MemoryTier(Enum):
    """The five cognitive memory tiers, ordered from most-volatile to least.

    WORKING    → Current turn; evicts at turn end. Zero persistence.
    SHORT_TERM → Last N turns; 24–72 hr TTL. Recent context.
    EPISODIC   → Session moments; weeks–months TTL. Life events.
    SEMANTIC   → Crystal DB + canon facts; permanent.
    LONG_TERM  → Gaian identity + settled arcs; permanent.
    """
    WORKING    = auto()
    SHORT_TERM = auto()
    EPISODIC   = auto()
    SEMANTIC   = auto()
    LONG_TERM  = auto()

    @property
    def is_permanent(self) -> bool:
        """True for tiers that never auto-expire."""
        return self in (MemoryTier.SEMANTIC, MemoryTier.LONG_TERM)

    @property
    def default_ttl_hours(self) -> float | None:
        """Canonical TTL for this tier, in hours. None = no expiry."""
        return {
            MemoryTier.WORKING:    0.0,
            MemoryTier.SHORT_TERM: 48.0,
            MemoryTier.EPISODIC:   720.0,
            MemoryTier.SEMANTIC:   None,
            MemoryTier.LONG_TERM:  None,
        }[self]


# ── MemoryQuery ───────────────────────────────────────────────────────────── #

class MemoryQuery:
    """Describes what kind of memory is being sought.

    Attributes:
        query_text:     Natural language query string.
        intent:         Routing hint. One of:
                        'context'  → WORKING + SHORT_TERM
                        'recall'   → SHORT_TERM + EPISODIC
                        'fact'     → SEMANTIC
                        'identity' → LONG_TERM
                        'full'     → all tiers (expensive)
        gaian_id:       Scopes results to a specific Gaian.
        tiers:          Explicit tier override; overrides intent routing.
        max_results:    Maximum results returned after merge + rank.
        recency_weight: [0, 1] weight toward recency vs. relevance in ranking.
        canon_refs:     Canon entries this query was issued under.
    """

    VALID_INTENTS = frozenset({"context", "recall", "fact", "identity", "full"})

    def __init__(
        self,
        query_text: str,
        intent: str,
        gaian_id: str | None = None,
        tiers: list[MemoryTier] | None = None,
        max_results: int = 10,
        recency_weight: float = 0.5,
        canon_refs: list[str] | None = None,
    ) -> None:
        if intent not in self.VALID_INTENTS:
            raise ValueError(
                f"Invalid intent {intent!r}. Must be one of {sorted(self.VALID_INTENTS)}."
            )
        if not 0.0 <= recency_weight <= 1.0:
            raise ValueError(f"recency_weight must be in [0, 1], got {recency_weight}.")
        self.query_text    = query_text
        self.intent        = intent
        self.gaian_id      = gaian_id
        self.tiers         = tiers
        self.max_results   = max(1, max_results)
        self.recency_weight = recency_weight
        self.canon_refs    = canon_refs or ["C34", "C01"]

    def __repr__(self) -> str:
        return (
            f"MemoryQuery(intent={self.intent!r}, "
            f"gaian_id={self.gaian_id!r}, "
            f"text={self.query_text[:40]!r})"
        )


# ── MemoryStore Protocol ───────────────────────────────────────────────────── #

@runtime_checkable
class MemoryStore(Protocol):
    """Protocol contract for all tier-specific memory store implementations."""

    async def write(
        self,
        key: str,
        value: Any,
        gaian_id: str | None = None,
        ttl_hours: float | None = None,
    ) -> None: ...

    async def read(
        self,
        key: str,
        gaian_id: str | None = None,
    ) -> Any | None: ...

    async def search(
        self,
        query: MemoryQuery,
    ) -> list[dict]: ...

    async def evict_expired(self) -> int: ...


# ── MemoryRouter ─────────────────────────────────────────────────────────────── #

class MemoryRouter:
    """Routes MemoryQuery objects to the correct tier(s)."""

    CANON_REFS = ["C34", "C01"]

    _INTENT_MAP: dict[str, list[MemoryTier]] = {
        "context":  [MemoryTier.WORKING,    MemoryTier.SHORT_TERM],
        "recall":   [MemoryTier.SHORT_TERM, MemoryTier.EPISODIC],
        "fact":     [MemoryTier.SEMANTIC],
        "identity": [MemoryTier.LONG_TERM],
        "full":     list(MemoryTier),
    }

    def __init__(self, stores: dict[MemoryTier, MemoryStore]) -> None:
        missing = [t for t in MemoryTier if t not in stores]
        if missing:
            log.warning("MemoryRouter: missing stores for tiers: %s", [t.name for t in missing])
        self._stores = stores

    async def search(self, query: MemoryQuery) -> list[dict]:
        tiers = query.tiers or self._INTENT_MAP.get(query.intent, list(MemoryTier))
        if _TRACE_AVAILABLE:
            async with AsyncGAIATrace(
                event=TraceEventType.MEMORY_RECALL,
                gaian_id=query.gaian_id,
                canon_refs=query.canon_refs,
                inputs={"intent": query.intent, "tiers": [t.name for t in tiers],
                        "query_text": query.query_text[:80]},
            ) as trace:
                results = await self._fan_out(tiers, query)
                ranked  = self._rank(results, query)
                trace.record_output({"result_count": len(ranked)})
                return ranked
        else:
            results = await self._fan_out(tiers, query)
            return self._rank(results, query)

    async def _fan_out(self, tiers: list[MemoryTier], query: MemoryQuery) -> list[dict]:
        tasks, tier_labels = [], []
        for tier in tiers:
            store = self._stores.get(tier)
            if store:
                tasks.append(store.search(query))
                tier_labels.append(tier)
        if not tasks:
            return []
        gathered = await asyncio.gather(*tasks, return_exceptions=True)
        results: list[dict] = []
        for tier, outcome in zip(tier_labels, gathered):
            if isinstance(outcome, Exception):
                log.warning("MemoryRouter: tier %s raised %r", tier.name, outcome)
                continue
            for r in outcome:
                r["_tier"] = tier.name
            results.extend(outcome)
        return results

    def _rank(self, results: list[dict], query: MemoryQuery) -> list[dict]:
        w = query.recency_weight
        for r in results:
            rel = float(r.get("_relevance", 0.5))
            rec = float(r.get("_recency",   0.5))
            r["_score"] = w * rec + (1.0 - w) * rel
        return sorted(results, key=lambda x: x["_score"], reverse=True)[: query.max_results]

    async def write(
        self,
        tier: MemoryTier,
        key: str,
        value: Any,
        gaian_id: str | None = None,
        ttl_hours: float | None = None,
    ) -> None:
        store = self._stores.get(tier)
        if store is None:
            log.warning("MemoryRouter.write: no store registered for tier %s", tier.name)
            return
        await store.write(key, value, gaian_id, ttl_hours)

    async def promote(
        self,
        key: str,
        from_tier: MemoryTier,
        to_tier: MemoryTier,
        gaian_id: str | None = None,
    ) -> bool:
        src = self._stores.get(from_tier)
        dst = self._stores.get(to_tier)
        if not src or not dst:
            log.warning("MemoryRouter.promote: missing store(s) for %s → %s", from_tier.name, to_tier.name)
            return False
        value = await src.read(key, gaian_id)
        if value is None:
            return False
        await dst.write(key, value, gaian_id)
        return True

    async def evict_all_expired(self) -> dict[str, int]:
        results: dict[str, int] = {}
        for tier, store in self._stores.items():
            try:
                count = await store.evict_expired()
                results[tier.name] = count
            except Exception as exc:  # noqa: BLE001
                log.warning("MemoryRouter.evict: tier %s raised %r", tier.name, exc)
                results[tier.name] = -1
        return results

    def registered_tiers(self) -> list[MemoryTier]:
        return list(self._stores.keys())
