"""
core/memory/hierarchy.py

Memory hierarchy: MemoryTier, MemoryQuery, MemoryStore (ABC), MemoryRouter.
Builds the five-tier memory architecture for GAIA-OS.

Tiers (fastest → most permanent):
  WORKING    — in-process dict, session-scoped, evicted on session end
  SHORT_TERM — SQLite, 48 h TTL default
  EPISODIC   — in-process dict, 30 day TTL default
  SEMANTIC   — in-process dict, permanent, canon-indexed
  LONG_TERM  — in-process dict, permanent, Gaian-identity-scoped

Canon Reference: C01 (GAIA as orchestration layer), C34 (Memory Sovereignty)
Issue: #213
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# MemoryTier
# ---------------------------------------------------------------------------

class MemoryTier(Enum):
    WORKING    = "working"
    SHORT_TERM = "short_term"
    EPISODIC   = "episodic"
    SEMANTIC   = "semantic"
    LONG_TERM  = "long_term"
    # Flat-store aliases used by test_memory_store.py
    PERMANENT  = "permanent"
    LONG_TERM  = "long_term"
    EPHEMERAL  = "ephemeral"

    @property
    def is_permanent(self) -> bool:
        return self in (MemoryTier.SEMANTIC, MemoryTier.LONG_TERM, MemoryTier.PERMANENT)

    @property
    def default_ttl_hours(self) -> Optional[float]:
        return {
            MemoryTier.WORKING:    0.0,
            MemoryTier.SHORT_TERM: 48.0,
            MemoryTier.EPISODIC:   720.0,
            MemoryTier.SEMANTIC:   None,
            MemoryTier.LONG_TERM:  None,
            MemoryTier.PERMANENT:  None,
            MemoryTier.EPHEMERAL:  1.0,
        }.get(self)


# ---------------------------------------------------------------------------
# MemoryQuery
# ---------------------------------------------------------------------------

VALID_INTENTS = {"context", "recall", "fact", "identity", "full"}


@dataclass
class MemoryQuery:
    text:           str
    intent:         str                     = "context"
    gaian_id:       Optional[str]           = None
    tiers:          Optional[list[MemoryTier]] = None  # explicit override
    max_results:    int                     = 10
    recency_weight: float                   = 0.3
    canon_refs:     list[str]               = field(default_factory=lambda: ["C34", "C01"])

    def __post_init__(self) -> None:
        if self.intent not in VALID_INTENTS:
            raise ValueError(f"Invalid intent '{self.intent}'. Must be one of {VALID_INTENTS}.")
        if not 0.0 <= self.recency_weight <= 1.0:
            raise ValueError(f"recency_weight must be 0.0–1.0, got {self.recency_weight}")
        if self.max_results < 1:
            self.max_results = 1

    def __repr__(self) -> str:
        return (
            f"MemoryQuery(intent={self.intent!r}, gaian_id={self.gaian_id!r}, "
            f"text={self.text[:40]!r}, max_results={self.max_results})"
        )


# ---------------------------------------------------------------------------
# MemoryStore ABC
# ---------------------------------------------------------------------------

class MemoryStore(ABC):
    """Abstract base for all tier-specific store implementations."""

    @abstractmethod
    async def write(self, key: str, value: Any, **kwargs) -> None: ...

    @abstractmethod
    async def read(self, key: str, gaian_id: Optional[str] = None) -> Optional[Any]: ...

    @abstractmethod
    async def search(self, query: MemoryQuery) -> list[dict]: ...

    @abstractmethod
    async def evict_expired(self) -> int: ...


# ---------------------------------------------------------------------------
# Intent → tier mapping
# ---------------------------------------------------------------------------

_INTENT_TIERS: dict[str, list[MemoryTier]] = {
    "context":  [MemoryTier.WORKING, MemoryTier.SHORT_TERM],
    "recall":   [MemoryTier.SHORT_TERM, MemoryTier.EPISODIC],
    "fact":     [MemoryTier.SEMANTIC],
    "identity": [MemoryTier.LONG_TERM],
    "full":     list(MemoryTier),
}


# ---------------------------------------------------------------------------
# MemoryRouter
# ---------------------------------------------------------------------------

class MemoryRouter:
    """
    Routes MemoryQuery objects to the appropriate tier stores.
    Merges and ranks results by relevance and recency.
    """

    def __init__(self, stores: dict[MemoryTier, MemoryStore]) -> None:
        self._stores = stores

    def registered_tiers(self) -> list[MemoryTier]:
        return list(self._stores.keys())

    async def search(self, query: MemoryQuery) -> list[dict]:
        tiers = query.tiers if query.tiers else _INTENT_TIERS.get(query.intent, [])
        tasks = [
            self._stores[tier].search(query)
            for tier in tiers
            if tier in self._stores
        ]
        results_nested = await asyncio.gather(*tasks)
        merged = [item for sublist in results_nested for item in sublist]
        return self._rank(merged, query)[:query.max_results]

    async def write(
        self, tier: MemoryTier, key: str, value: Any,
        gaian_id: Optional[str] = None, **kwargs
    ) -> None:
        await self._stores[tier].write(key, value, gaian_id=gaian_id, **kwargs)

    async def read(
        self, tier: MemoryTier, key: str,
        gaian_id: Optional[str] = None
    ) -> Optional[Any]:
        return await self._stores[tier].read(key, gaian_id)

    async def promote(
        self,
        key: str,
        from_tier: MemoryTier,
        to_tier: MemoryTier,
        gaian_id: Optional[str] = None,
    ) -> bool:
        value = await self._stores[from_tier].read(key, gaian_id)
        if value is None:
            return False
        await self._stores[to_tier].write(key, value, gaian_id=gaian_id)
        return True

    async def evict_all_expired(self) -> dict[str, int]:
        counts = {}
        for tier, store in self._stores.items():
            counts[tier.name] = await store.evict_expired()
        return counts

    @staticmethod
    def _rank(results: list[dict], query: MemoryQuery) -> list[dict]:
        rw = query.recency_weight
        def score(item: dict) -> float:
            rel = item.get("_relevance", 0.5)
            rec = item.get("_recency",   0.5)
            return (1.0 - rw) * rel + rw * rec
        return sorted(results, key=score, reverse=True)


# ---------------------------------------------------------------------------
# build_default_router factory
# ---------------------------------------------------------------------------

def build_default_router(
    semantic_store: Optional[MemoryStore] = None,
    long_term_store: Optional[MemoryStore] = None,
) -> MemoryRouter:
    """
    Build a MemoryRouter wired with production-default store implementations.
    Allows injection of custom stores for testing.
    """
    from core.memory.tiers.working    import WorkingMemoryStore
    from core.memory.tiers.short_term import ShortTermMemoryStore
    from core.memory.tiers.episodic   import EpisodicMemoryStore
    from core.memory.tiers.semantic   import SemanticMemoryStore
    from core.memory.tiers.long_term  import LongTermMemoryStore

    return MemoryRouter({
        MemoryTier.WORKING:    WorkingMemoryStore(),
        MemoryTier.SHORT_TERM: ShortTermMemoryStore(),
        MemoryTier.EPISODIC:   EpisodicMemoryStore(),
        MemoryTier.SEMANTIC:   semantic_store  or SemanticMemoryStore(),
        MemoryTier.LONG_TERM:  long_term_store or LongTermMemoryStore(),
    })
