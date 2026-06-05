"""
core/memory

The Memory runtime package.
Canonical foundation: C01 (Gaian Sovereignty) + C-SENTINEL Article 4 (Memory Sovereignty)
Issue: #213
"""

from core.memory.memory_store import (
    MemoryStore,
    MemoryEntry,
    MemoryProvenance,
    MemoryTier,
    MemoryCategory,
    ProvenanceSource,
    SessionState,
    get_memory_store,
    _default_store_path,
)


class FallbackEmbedder:
    """
    Simple fallback embedder for memory entries.
    Returns a zero-vector when no real embedding model is available.
    Replace embed() with a real model call when the embedding layer is ready.
    """

    DIMENSIONS = 384

    def embed(self, text: str) -> list[float]:
        """Generate a placeholder embedding for text."""
        _ = text  # consumed when real model is plugged in
        return [0.0] * self.DIMENSIONS


__all__ = [
    "MemoryStore",
    "MemoryEntry",
    "MemoryProvenance",
    "MemoryTier",
    "MemoryCategory",
    "ProvenanceSource",
    "SessionState",
    "get_memory_store",
    "_default_store_path",
    "FallbackEmbedder",
]
