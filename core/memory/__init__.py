"""
core/memory/__init__.py
GAIA Memory Package — Sprint G-8

Public surface:
  build_default_router()  — factory that wires all five tier stores into
                            a ready-to-use MemoryRouter.

Canon refs: C34 (Presence), C01 (Sovereignty)
"""
from __future__ import annotations

from .hierarchy import MemoryQuery, MemoryRouter, MemoryStore, MemoryTier
from .tiers import (
    WorkingMemoryStore,
    ShortTermMemoryStore,
    EpisodicMemoryStore,
    SemanticMemoryStore,
    LongTermMemoryStore,
)


def build_default_router(
    *,
    db_path: str = ":memory:",
    semantic_store: SemanticMemoryStore | None = None,
    long_term_store: LongTermMemoryStore | None = None,
) -> MemoryRouter:
    """Return a MemoryRouter wired with all five tier stores.

    Parameters
    ----------
    db_path:
        SQLite database path for ShortTermMemoryStore.
        Defaults to ':memory:' (in-process, no persistence).
    semantic_store:
        Optional pre-built SemanticMemoryStore to inject
        (e.g. one pre-loaded with canon facts).
    long_term_store:
        Optional pre-built LongTermMemoryStore to inject.

    Canon refs: C34, C01
    """
    return MemoryRouter({
        MemoryTier.WORKING:    WorkingMemoryStore(),
        MemoryTier.SHORT_TERM: ShortTermMemoryStore(db_path=db_path),
        MemoryTier.EPISODIC:   EpisodicMemoryStore(),
        MemoryTier.SEMANTIC:   semantic_store  if semantic_store  is not None else SemanticMemoryStore(),
        MemoryTier.LONG_TERM:  long_term_store if long_term_store is not None else LongTermMemoryStore(),
    })


__all__ = [
    # Hierarchy types
    "MemoryQuery",
    "MemoryRouter",
    "MemoryStore",
    "MemoryTier",
    # Tier stores
    "WorkingMemoryStore",
    "ShortTermMemoryStore",
    "EpisodicMemoryStore",
    "SemanticMemoryStore",
    "LongTermMemoryStore",
    # Factory
    "build_default_router",
]
