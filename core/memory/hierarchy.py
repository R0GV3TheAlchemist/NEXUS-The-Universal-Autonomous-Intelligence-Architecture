"""
core/memory/hierarchy.py
GAIA Memory Hierarchy — Sprint G-8

Formalizes five cognitive memory tiers and a routing layer that directs
retrieval queries to the correct tier(s) rather than searching everything.
This makes memory retrieval cost-predictable and retrieval logic testable.

Canon Ref: C34 (Presence — GAIA knows what tier of memory a moment belongs to)
           C01 (Sovereignty — memory routing is explicit, not opaque)
"""
from __future__ import annotations

from enum import Enum, auto
from typing import Any, Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# Memory tiers
# ---------------------------------------------------------------------------

class MemoryTier(Enum):
    """The five cognitive memory tiers in GAIA-OS.

    Each tier has a different storage backend, TTL, and retrieval cost:

    WORKING    — Current turn context; evicts at turn end (in-memory dict).
    SHORT_TERM — Last N turns; 24-72 hr TTL (SQLite/Redis).
    EPISODIC   — Session moments; weeks-months TTL (ArcadeDB / graph DB).
    SEMANTIC   — Crystal Knowledge Graph facts; permanent.
    LONG_TERM  — Gaian identity and settled personality arcs; permanent.
    """
    WORKING    = auto()
    SHORT_TERM = auto()
    EPISODIC   = auto()
    SEMANTIC   = auto()
    LONG_TERM  = auto()


# ---------------------------------------------------------------------------
# MemoryQuery — describes what is being sought
# ---------------------------------------------------------------------------

class MemoryQuery:
    """Describes what kind of memory is being sought.

    Parameters
    ----------
    query_text:
        The natural-language or embedding query string.
    intent:
        Routing hint — one of ``"context"``, ``"recall"``, ``"fact"``,
        ``"identity"``, or ``"full"``.  Controls which tiers are searched
        when ``tiers`` is ``None``.
    gaian_id:
        Optional scoping to a specific Gaian persona.
    tiers:
        Explicit tier list; overrides intent-based routing when provided.
    max_results:
        Maximum number of results to return across all searched tiers.
    recency_weight:
        Float in [0.0, 1.0].  Higher values rank recent memories first;
        lower values rank by relevance.
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
    ) -> None:
        if intent not in self.VALID_INTENTS:
            raise ValueError(f"intent must be one of {self.VALID_INTENTS!r}, got {intent!r}")
        self.query_text    = query_text
        self.intent        = intent
        self.gaian_id      = gaian_id
        self.tiers         = tiers
        self.max_results   = max_results
        self.recency_weight = recency_weight


# ---------------------------------------------------------------------------
# MemoryStore — protocol for tier-specific backends
# ---------------------------------------------------------------------------

@runtime_checkable
class MemoryStore(Protocol):
    """Protocol every tier-specific memory store must satisfy.

    Implementations are injected into ``MemoryRouter`` at construction time.
    """

    async def write(
        self,
        key: str,
        value: Any,
        gaian_id: str | None = None,
    ) -> None: ...

    async def read(
        self,
        key: str,
        gaian_id: str | None = None,
    ) -> Any | None: ...

    async def search(self, query: MemoryQuery) -> list[dict]: ...

    async def evict_expired(self) -> int:
        """Evict expired entries; return the number evicted."""
        ...


# ---------------------------------------------------------------------------
# MemoryRouter
# ---------------------------------------------------------------------------

class MemoryRouter:
    """
    Routes ``MemoryQuery`` objects to the appropriate tier(s).
    Merges and ranks results when multiple tiers are searched.

    Intent-to-tier routing rules
    ----------------------------
    ``"context"``  → WORKING + SHORT_TERM
    ``"recall"``   → SHORT_TERM + EPISODIC
    ``"fact"``     → SEMANTIC
    ``"identity"`` → LONG_TERM
    ``"full"``     → all tiers (expensive; only for explicit full-context requests)
    """

    _INTENT_MAP: dict[str, list[MemoryTier]] = {
        "context":  [MemoryTier.WORKING,    MemoryTier.SHORT_TERM],
        "recall":   [MemoryTier.SHORT_TERM, MemoryTier.EPISODIC],
        "fact":     [MemoryTier.SEMANTIC],
        "identity": [MemoryTier.LONG_TERM],
        "full":     list(MemoryTier),
    }

    def __init__(self, stores: dict[MemoryTier, MemoryStore]) -> None:
        self._stores = stores

    async def search(self, query: MemoryQuery) -> list[dict]:
        """Search the appropriate tier(s) and return ranked results."""
        tiers = query.tiers or self._INTENT_MAP.get(query.intent, list(MemoryTier))
        results: list[dict] = []
        for tier in tiers:
            store = self._stores.get(tier)
            if store:
                tier_results = await store.search(query)
                for r in tier_results:
                    r["_tier"] = tier.name
                results.extend(tier_results)
        return self._rank(results, query)

    def _rank(self, results: list[dict], query: MemoryQuery) -> list[dict]:
        """Combine recency and relevance scores, weighted by ``query.recency_weight``."""
        for r