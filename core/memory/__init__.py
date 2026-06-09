"""
core/memory

The Memory runtime package.
Canonical foundation: C01 (Gaian Sovereignty) + C-SENTINEL Article 4 (Memory Sovereignty)
Issue: #213

== Tier enum design ==

Two separate MemoryTier-like enums exist for two separate contracts:

  core.memory.hierarchy.MemoryTier  -- exactly 5 members (hierarchy architecture tests).
                                       Imported directly by test_memory_hierarchy.py.

  core.memory.store_tier.StoreTier  -- 7 members (flat SQLite store needs PERMANENT + EPHEMERAL).
                                       Used internally by MemoryStore and MemoryPruner.

This __init__.py re-exports StoreTier as `MemoryTier` so that test_memory_store.py,
which does `from core.memory import MemoryTier`, receives the 7-member version with
.PERMANENT and .EPHEMERAL attributes.

test_memory_hierarchy.py imports directly from core.memory.hierarchy and therefore
always gets the strict 5-member version -- the two never conflict.
"""

from core.memory.hierarchy import (
    MemoryQuery,
    MemoryRouter,
    MemoryStore as HierarchyMemoryStore,
    MemoryTier as _HierarchyMemoryTier,
    build_default_router,
)
from core.memory.items import MemoryItem, MemoryKind, RetrievedMemory
from core.memory.memory_store import (
    MemoryCategory,
    MemoryEntry,
    MemoryProvenance,
    MemoryTier as MemoryTierLegacy,
    ProvenanceSource,
    SessionState,
    _default_store_path,
    get_memory_store,
)
from core.memory.pruner import MemoryPruner
from core.memory.store_sqlite import MemoryStore

# StoreTier re-exported as MemoryTier for test_memory_store.py
# (needs PERMANENT + EPHEMERAL members)
from core.memory.store_tier import StoreTier as MemoryTier


class FallbackEmbedder:
    """
    Fallback embedder for memory entries.
    Returns a deterministic hash-based vector so different texts give different vectors.
    Replace embed() with a real model when the embedding layer is ready.
    Supports both sync and async usage.
    """

    def __init__(self, dim: int = 384) -> None:
        self.DIMENSIONS = dim

    async def embed(self, text: str) -> list[float]:
        """Generate a deterministic pseudo-embedding for text."""
        import hashlib
        import struct
        seed = hashlib.sha256(text.encode()).digest()
        floats = []
        for i in range(0, min(len(seed), self.DIMENSIONS * 4), 4):
            chunk = seed[i:i+4].ljust(4, b'\x00')
            val = struct.unpack('f', chunk)[0]
            floats.append(max(-1.0, min(1.0, val / 1e38)))
        while len(floats) < self.DIMENSIONS:
            floats.append(0.0)
        return floats[:self.DIMENSIONS]

    def embed_sync(self, text: str) -> list[float]:
        import asyncio
        return asyncio.run(self.embed(text))


__all__ = [
    "FallbackEmbedder",
    "HierarchyMemoryStore",
    "MemoryCategory",
    "MemoryEntry",
    "MemoryItem",
    "MemoryKind",
    "MemoryPruner",
    "MemoryProvenance",
    "MemoryQuery",
    "MemoryRouter",
    "MemoryStore",
    "MemoryTier",
    "MemoryTierLegacy",
    "ProvenanceSource",
    "RetrievedMemory",
    "SessionState",
    "_HierarchyMemoryTier",
    "_default_store_path",
    "build_default_router",
    "get_memory_store",
]
