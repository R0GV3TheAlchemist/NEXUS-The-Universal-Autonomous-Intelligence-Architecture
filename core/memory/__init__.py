"""GAIA Persistent Memory & Gaian Twin State Store.

Canon References: C17 (Persistent Memory and Identity Architecture),
                  C04 (Human/Gaian Twin Architecture),
                  C23 (Shadow Registry and Failure Mode Catalogue)

This package is GAIA's memory layer — the mechanism by which every
Human Principal's Gaian Twin accumulates wisdom, emotional context,
history, and identity across sessions and lifetimes.

Without this, every GAIA session is orphaned from all prior context.
With this, every session is the Stone operating from its complete
temporal position.
"""

from .layers import MemoryLayer, MemoryRecord, MemoryScope, MemoryTag
from .session_buffer import SessionBuffer
from .episodic import EpisodicMemoryStore
from .semantic import SemanticMemoryStore
from .identity import IdentityMemoryStore, GaianTwinProfile
from .shared import SharedMemoryStore
from .shadow_registry import ShadowRegistry, ShadowEntry, ShadowPattern
from .retrieval import MemoryRetrievalEngine, RetrievalQuery, RankedMemory
from .manager import MemoryManager

# ---------------------------------------------------------------------------
# FallbackEmbedder — re-exported from embedder.py
# Tests and consumers import: from core.memory import FallbackEmbedder
# ---------------------------------------------------------------------------
from .embedder import FallbackEmbedder


# ---------------------------------------------------------------------------
# build_default_router — convenience factory
# Returns a MemoryManager configured with all default layers.
# Tests import: from core.memory import build_default_router
# ---------------------------------------------------------------------------

def build_default_router(
    gaian_id: str = "default",
    session_id: str = "default",
) -> MemoryManager:
    """
    Build and return a MemoryManager with all default memory layers.

    This is the primary entry point for application code that needs a
    fully configured memory system without manual wiring.

    Args:
        gaian_id:   The Gaian Twin identifier for this memory context.
        session_id: The current session identifier.

    Returns:
        A configured MemoryManager instance.
    """
    return MemoryManager(gaian_id=gaian_id, session_id=session_id)


__all__ = [
    "MemoryLayer",
    "MemoryRecord",
    "MemoryScope",
    "MemoryTag",
    "SessionBuffer",
    "EpisodicMemoryStore",
    "SemanticMemoryStore",
    "IdentityMemoryStore",
    "GaianTwinProfile",
    "SharedMemoryStore",
    "ShadowRegistry",
    "ShadowEntry",
    "ShadowPattern",
    "MemoryRetrievalEngine",
    "RetrievalQuery",
    "RankedMemory",
    "MemoryManager",
    # New in this fix
    "FallbackEmbedder",
    "build_default_router",
]


# ---------------------------------------------------------------------------
# Memory store / item exports — required by tests/test_memory_store.py
# ---------------------------------------------------------------------------
from .memory_store import MemoryStore          # noqa: F401
from .items import MemoryItem, MemoryKind, RetrievedMemory          # noqa: F401
from .memory_store import MemoryTier                                  # noqa: F401
from .pruner import MemoryPruner                                      # noqa: F401
