"""
core/memory/__init__.py
GAIA Memory Hierarchy Package — Sprint G-8

Public surface area for all memory operations.
All callers should import from here, not from sub-modules.

Usage::

    from core.memory import MemoryTier, MemoryQuery, MemoryRouter
    from core.memory import build_default_router
"""
from core.memory.hierarchy import (
    MemoryQuery,
    MemoryRouter,
    MemoryStore,
    MemoryTier,
)
from core.memory.tiers.working import WorkingMemoryStore
from core.memory.tiers.short_term import ShortTermMemoryStore
from core.memory.tiers.episodic import EpisodicMemoryStore
from core.memory.tiers.semantic import SemanticMemoryStore
from core.memory.tiers.long_term import LongTermMemoryStore


def build_default_router(
    *,
    semantic_store: MemoryStore | None = None,
    long_term_store: MemoryStore | None = None,
) -> MemoryRouter:
    """Construct a MemoryRouter wired with the five canonical tier stores.

    Args:
        semantic_store:  Optional custom SemanticMemoryStore (e.g., Crystal DB).
                         If None, falls back to the default in-process stub.
        long_term_store: Optional custom LongTermMemoryStore (e.g., Tauri Store).
                         If None, falls back to the default in-process stub.

    Returns:
        A fully configured MemoryRouter ready for production use.
    """
    stores: dict[MemoryTier, MemoryStore] = {
        MemoryTier.WORKING:    WorkingMemoryStore(),
        MemoryTier.SHORT_TERM: ShortTermMemoryStore(),
        MemoryTier.EPISODIC:   EpisodicMemoryStore(),
        MemoryTier.SEMANTIC:   semantic_store  or SemanticMemoryStore(),
        MemoryTier.LONG_TERM:  long_term_store or LongTermMemoryStore(),
    }
    return MemoryRouter(stores)


__all__ = [
    "MemoryTier",
    "MemoryQuery",
    "MemoryStore",
    "MemoryRouter",
    "WorkingMemoryStore",
    "ShortTermMemoryStore",
    "EpisodicMemoryStore",
    "SemanticMemoryStore",
    "LongTermMemoryStore",
    "build_default_router",
]
