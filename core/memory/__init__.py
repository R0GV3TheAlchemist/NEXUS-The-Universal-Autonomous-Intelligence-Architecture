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
]
