"""
core/memory

The Memory runtime package.
Canonical foundation: C01 (Gaian Sovereignty) + C-SENTINEL Article 4 (Memory Sovereignty)
Issue: #213
"""

from core.memory.memory_store import (
    MemoryEntry,
    MemoryProvenance,
    MemoryTier as MemoryTierLegacy,
    MemoryCategory,
    ProvenanceSource,
    SessionState,
    get_memory_store,
    _default_store_path,
)

# Hierarchy tier system (superset, used by test_memory_hierarchy)
from core.memory.hierarchy import (
    MemoryTier,
    MemoryQuery,
    MemoryStore as HierarchyMemoryStore,
    MemoryRouter,
    build_default_router,
)

# Flat SQLite-backed MemoryStore (used by test_memory_store)
from core.memory.store_sqlite import MemoryStore

# Core item models
from core.memory.items import MemoryItem, MemoryKind, RetrievedMemory

# Pruner
from core.memory.pruner import MemoryPruner


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
            # Normalise to -1..1
            floats.append(max(-1.0, min(1.0, val / 1e38)))
        # Pad if needed
        while len(floats) < self.DIMENSIONS:
            floats.append(0.0)
        return floats[:self.DIMENSIONS]

    def embed_sync(self, text: str) -> list[float]:
        import asyncio
        return asyncio.run(self.embed(text))


__all__ = [
    # Legacy flat-store models
    "MemoryEntry",
    "MemoryProvenance",
    "MemoryTierLegacy",
    "MemoryCategory",
    "ProvenanceSource",
    "SessionState",
    "get_memory_store",
    "_default_store_path",
    # Hierarchy
    "MemoryTier",
    "MemoryQuery",
    "HierarchyMemoryStore",
    "MemoryRouter",
    "build_default_router",
    # SQLite store
    "MemoryStore",
    # Item models
    "MemoryItem",
    "MemoryKind",
    "RetrievedMemory",
    # Pruner
    "MemoryPruner",
    # Embedder
    "FallbackEmbedder",
]
