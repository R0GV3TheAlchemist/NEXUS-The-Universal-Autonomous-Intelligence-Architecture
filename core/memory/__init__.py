"""
core/memory/__init__.py
GAIA Memory Package — Sprint G-8

Public surface. MemoryTier is exported from taxonomy (EPHEMERAL / SHORT_TERM /
LONG_TERM / PERMANENT) — the string enum used by store.py, MemoryItem, and all
tests. The hierarchy tier stores (WorkingMemoryStore etc.) use their own
internal tier mapping and are unaffected.

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
# 1. Hierarchy abstractions — MemoryQuery and MemoryRouter only.
#    MemoryTier is NOT imported from hierarchy; taxonomy is the canonical enum.
# ---------------------------------------------------------------------------
from core.memory.hierarchy import (
    MemoryQuery,
    MemoryRouter,
    MemoryStore as AbstractMemoryStore,
)

# ---------------------------------------------------------------------------
# 2. Canonical MemoryTier + domain types from taxonomy.
#    taxonomy.MemoryTier: EPHEMERAL, SHORT_TERM, LONG_TERM, PERMANENT
#    These are the values used by store.py, MemoryItem, and the test suite.
# ---------------------------------------------------------------------------
from core.memory.taxonomy import MemoryKind, MemoryItem, MemoryTier

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
    _working   = WorkingMemoryStore()
    _short     = ShortTermMemoryStore()
    _episodic  = EpisodicMemoryStore()
    _semantic  = semantic_store  or SemanticMemoryStore()
    _long_term = long_term_store or LongTermMemoryStore()
    stores = {
        getattr(_working,   "TIER", None) or "working":    _working,
        getattr(_short,     "TIER", None) or "short_term": _short,
        getattr(_episodic,  "TIER", None) or "episodic":   _episodic,
        getattr(_semantic,  "TIER", None) or "semantic":   _semantic,
        getattr(_long_term, "TIER", None) or "long_term":  _long_term,
    }
    return MemoryRouter(stores)


__all__ = [
    # Taxonomy (canonical)
    "MemoryTier",
    "MemoryItem",
    "MemoryKind",
    # Hierarchy abstractions
    "MemoryQuery",
    "MemoryRouter",
    "AbstractMemoryStore",
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
