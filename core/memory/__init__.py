"""
core/memory/__init__.py
GAIA Memory Package — Sprint G-8

Clean public surface. Two MemoryTier definitions exist in this package:
  - taxonomy.MemoryTier  : old string enum (short_term, long_term ...)
                           used internally by store.py / SQLite layer
  - hierarchy.MemoryTier : canonical auto() enum used by MemoryRouter / tiers

We expose ONLY hierarchy.MemoryTier as `MemoryTier`.
MemoryItem and MemoryKind are pulled directly from taxonomy to avoid
store.py re-exporting them via a shadowed MemoryTier that clashes.

Public imports::

    from core.memory import MemoryTier, MemoryQuery, MemoryRouter
    from core.memory import build_default_router
    from core.memory import MemoryItem, MemoryKind, RetrievedMemory
    from core.memory import FallbackEmbedder, MemoryPruner
    from core.memory import WorkingMemoryStore, ShortTermMemoryStore
    from core.memory import EpisodicMemoryStore, SemanticMemoryStore
    from core.memory import LongTermMemoryStore
"""

# ---------------------------------------------------------------------------
# 1. Hierarchy abstractions  (MemoryTier is the canonical one going forward)
# ---------------------------------------------------------------------------
from core.memory.hierarchy import (
    MemoryQuery,
    MemoryRouter,
    MemoryStore as AbstractMemoryStore,
    MemoryTier,
)

# ---------------------------------------------------------------------------
# 2. Domain types from taxonomy — MemoryKind + MemoryItem ONLY.
#    Do NOT import taxonomy.MemoryTier here; it clashes with hierarchy.MemoryTier.
# ---------------------------------------------------------------------------
from core.memory.taxonomy import MemoryKind, MemoryItem

# ---------------------------------------------------------------------------
# 3. Concrete SQLite store + RetrievedMemory
# ---------------------------------------------------------------------------
from core.memory.store import MemoryStore, RetrievedMemory

# ---------------------------------------------------------------------------
# 4. Embedder
# ---------------------------------------------------------------------------
from core.memory.embedder import FallbackEmbedder

# ---------------------------------------------------------------------------
# 5. Pruner
# ---------------------------------------------------------------------------
from core.memory.pruner import MemoryPruner

# ---------------------------------------------------------------------------
# 6. Tier stores
# ---------------------------------------------------------------------------
from core.memory.tiers.working    import WorkingMemoryStore
from core.memory.tiers.short_term import ShortTermMemoryStore
from core.memory.tiers.episodic   import EpisodicMemoryStore
from core.memory.tiers.semantic   import SemanticMemoryStore
from core.memory.tiers.long_term  import LongTermMemoryStore


# ---------------------------------------------------------------------------
# 7. Factory
# ---------------------------------------------------------------------------

def build_default_router(
    *,
    semantic_store: AbstractMemoryStore | None = None,
    long_term_store: AbstractMemoryStore | None = None,
) -> MemoryRouter:
    """Return a MemoryRouter wired with all five canonical tier stores."""
    stores = {
        MemoryTier.WORKING:    WorkingMemoryStore(),
        MemoryTier.SHORT_TERM: ShortTermMemoryStore(),
        MemoryTier.EPISODIC:   EpisodicMemoryStore(),
        MemoryTier.SEMANTIC:   semantic_store  or SemanticMemoryStore(),
        MemoryTier.LONG_TERM:  long_term_store or LongTermMemoryStore(),
    }
    return MemoryRouter(stores)


__all__ = [
    # Hierarchy
    "MemoryTier",
    "MemoryQuery",
    "MemoryRouter",
    "AbstractMemoryStore",
    # Domain types
    "MemoryItem",
    "MemoryKind",
    # Concrete store
    "MemoryStore",
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
