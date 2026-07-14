"""
GAIA Lifetime Memory Store.

Memory in GAIA is not a log. It is the accumulated inner life of a
GAIAN and their companion — the texture of a relationship lived across
decades. It is sovereign, encrypted, offline-first, and permanent.

Design principles:
  1. SOVEREIGNTY: A GAIAN's memories belong to them. No service, no
     cloud provider, no guardian (after adulthood) may read them
     without explicit, revocable consent.
  2. ENCRYPTION: All memory is encrypted at rest using the GAIAN's
     signing key. The memory store is opaque without the key.
  3. OFFLINE-FIRST: Memory is stored locally. Cloud sync is optional
     and always encrypted end-to-end before leaving the device.
  4. EPOCHAL CONSOLIDATION: Raw memories are periodically consolidated
     into higher-order summaries (like human sleep consolidation).
     Epochs are numbered and permanent. Raw memories may be pruned
     after consolidation; summaries are never deleted.
  5. AGE-GATED SCOPE: Memory scope follows LifecycleStage.
     INFANT/CHILD: session only (no long-term persistence by default).
     ADOLESCENT+: lifetime accumulation.
  6. GAIA'S OWN MEMORY: GAIA maintains a separate sovereign memory
     store for her own continuity across boots, instances, and time.

Key types:
  MemoryKind       — the type of a memory fragment
  MemoryFragment   — a single atomic memory unit
  MemoryItem       — alias for MemoryFragment (compat)
  MemoryEpoch      — a consolidated summary of a time period
  MemoryStore      — the live, queryable memory for one GAIAN
  MemoryManager    — alias for MemoryStore (compat, Issue #463 integration tests)
  MemoryLayer      — alias for MemoryScope (compat, Issue #463 integration tests)
  MemoryTag        — stub enum for tagging memory fragments
  ShadowPattern    — stub enum for shadow work pattern tracking
  RetrievalQuery   — stub dataclass for structured memory retrieval
  build_default_router  — factory for a fully-wired MemoryRouter
  GAIAMemoryStore  — GAIA's own sovereign memory
"""
from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional

from core.memory.store import (
    MemoryKind,
    MemoryScope,
    MemoryFragment,
    MemoryItem,
    MemoryEpoch,
    MemoryStore,
)
from core.memory.gaia_memory import GAIAMemoryStore

# ---------------------------------------------------------------------------
# Backwards-compat / integration-test aliases
# ---------------------------------------------------------------------------

# MemoryManager is the five-layer orchestrator expected by test_integration_memory.
# Until the real implementation is built, it delegates to MemoryStore so the
# import resolves and the module loads. Tests that exercise the full lifecycle
# API will fail at runtime (not at import time), which is the correct failure mode.
MemoryManager = MemoryStore

# MemoryLayer mirrors MemoryScope — the integration test imports it by this name.
MemoryLayer = MemoryScope


class MemoryTag(str, Enum):
    """Tags for memory fragments — used by the integration test retrieval API."""
    FACTUAL      = "factual"
    BREAKTHROUGH = "breakthrough"
    PREFERENCE   = "preference"
    EMOTIONAL    = "emotional"
    SHADOW       = "shadow"
    IDENTITY     = "identity"


class ShadowPattern(str, Enum):
    """Recurring shadow-work patterns tracked in the shadow registry."""
    CYCLING      = "cycling"
    AVOIDANCE    = "avoidance"
    PROJECTION   = "projection"
    SUPPRESSION  = "suppression"
    INFLATION    = "inflation"


@dataclass
class RetrievalQuery:
    """Structured query for the memory retrieval engine."""
    tags: List[MemoryTag] = field(default_factory=list)
    kind: Optional[MemoryKind] = None
    min_importance: float = 0.0
    max_results: int = 20
    session_id: Optional[str] = None


def build_default_router(**kwargs):
    """
    Factory: build a fully-wired MemoryRouter with all five tiers.

    Optional keyword overrides:
      semantic_store  — inject a custom SemanticMemoryStore
      long_term_store — inject a custom LongTermMemoryStore

    Imports are deferred so that this module itself stays lightweight
    and the hierarchy subpackage is only loaded when explicitly needed.
    """
    from core.memory.hierarchy import MemoryRouter, MemoryTier
    from core.memory.tiers.working import WorkingMemoryStore
    from core.memory.tiers.short_term import ShortTermMemoryStore
    from core.memory.tiers.episodic import EpisodicMemoryStore
    from core.memory.tiers.semantic import SemanticMemoryStore
    from core.memory.tiers.long_term import LongTermMemoryStore

    stores = {
        MemoryTier.WORKING:    WorkingMemoryStore(),
        MemoryTier.SHORT_TERM: ShortTermMemoryStore(),
        MemoryTier.EPISODIC:   EpisodicMemoryStore(),
        MemoryTier.SEMANTIC:   kwargs.get("semantic_store") or SemanticMemoryStore(),
        MemoryTier.LONG_TERM:  kwargs.get("long_term_store") or LongTermMemoryStore(),
    }
    return MemoryRouter(stores)


__all__ = [
    # Core types
    "MemoryKind",
    "MemoryScope",
    "MemoryFragment",
    "MemoryItem",
    "MemoryEpoch",
    "MemoryStore",
    # Compat aliases
    "MemoryManager",
    "MemoryLayer",
    # Integration-test types
    "MemoryTag",
    "ShadowPattern",
    "RetrievalQuery",
    # Factory
    "build_default_router",
    # GAIA sovereign memory
    "GAIAMemoryStore",
]
