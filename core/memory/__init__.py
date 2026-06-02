"""
core/memory/__init__.py
GAIA Memory Hierarchy Package — Sprint G-8

Public surface area for all memory operations.
All callers should import from here, not from sub-modules.

Usage::

    from core.memory import MemoryTier, MemoryQuery, MemoryRouter
    from core.memory import build_default_router

    # Concrete SQLite-backed store (used by tests and production)
    from core.memory import MemoryStore, MemoryItem, MemoryKind
    from core.memory import FallbackEmbedder, MemoryPruner, RetrievedMemory
"""

# ---------------------------------------------------------------------------
# Hierarchy abstractions (MemoryQuery, MemoryRouter, abstract MemoryStore,
# MemoryTier) — imported first so the concrete MemoryStore below can
# shadow the abstract one in __all__ without a circular import.
# ---------------------------------------------------------------------------
from core.memory.hierarchy import (
    MemoryQuery,
    MemoryRouter,
    MemoryStore as _AbstractMemoryStore,
    MemoryTier,
)

# ---------------------------------------------------------------------------
# Concrete SQLite-backed MemoryStore + domain types
# ---------------------------------------------------------------------------
from core.memory.store import (
    MemoryStore,      # concrete SQLite store — shadows abstract above
    MemoryItem,
    MemoryKind,
    RetrievedMemory,
)

# ---------------------------------------------------------------------------
# Embedder
# ---------------------------------------------------------------------------
from core.memory.embedder import FallbackEmbedder

# ---------------------------------------------------------------------------
# Pruner
# ---------------------------------------------------------------------------
from core.memory.pruner import MemoryPruner

# ---------------------------------------------------------------------------
# Tier stores
# ---------------------------------------------------------------------------
from core.memory.tiers.working import WorkingMemoryStore
from core.memory.tiers.short_term import ShortTermMemoryStore
from core.memory.tiers.episodic import EpisodicMemoryStore
from core.memory.tiers.semantic import SemanticMemoryStore
from core.memory.tiers.long_term import LongTermMemoryStore


# ---------------------------------------------------------------------------
# build_default_router — convenience factory
# ---------------------------------------------------------------------------

def build_default_router(
    *,
    semantic_store: _AbstractMemoryStore | None = None,
    long_term_store: _AbstractMemoryStore | None = None,
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
    stores: dict[MemoryTier, _AbstractMemoryStore] = {
        MemoryTier.WORKING:    WorkingMemoryStore(),
        MemoryTier.SHORT_TERM: ShortTermMemoryStore(),
        MemoryTier.EPISODIC:   EpisodicMemoryStore(),
        MemoryTier.SEMANTIC:   semantic_store  or SemanticMemoryStore(),
        MemoryTier.LONG_TERM:  long_term_store or LongTermMemoryStore(),
    }
    return MemoryRouter(stores)


__all__ = [
    # Hierarchy abstractions
    "MemoryTier",
    "MemoryQuery",
    "MemoryRouter",
    # Concrete SQLite store + domain types
    "MemoryStore",
    "MemoryItem",
    "MemoryKind",
    "RetrievedMemory",
    # Embedder
    "FallbackEmbedder",
    # Pruner
    "MemoryPruner",
    # Tier stores
    "WorkingMemoryStore",
    "ShortTermMemoryStore",
    "EpisodicMemoryStore",
    "SemanticMemoryStore",
    "LongTermMemoryStore",
    # Factory
    "build_default_router",
]
