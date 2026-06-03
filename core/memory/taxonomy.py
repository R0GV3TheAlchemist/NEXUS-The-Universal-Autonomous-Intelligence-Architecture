"""
core.memory.taxonomy
====================
Data types that describe what kind of thing GAIA remembers.

MemoryKind
----------
A fine-grained label on every memory item so the retriever can filter
by type (e.g. only pull back USER_PREFERENCE items when building a
personalisation block).

MemoryTier
----------
Lifetime / volatility tier.  The pruner uses this to decide eviction
priority — WORKING/EPHEMERAL items are the first to go.

MemoryItem
----------
The canonical in-process representation of one memory row.  The store
serialises to / deserialises from SQLite using this dataclass.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MemoryKind(str, Enum):
    """What *kind* of information this memory encodes."""

    # Conversational
    MESSAGE       = "message"        # raw user/assistant turn
    SUMMARY       = "summary"        # compressed summary of older turns

    # User profile
    PREFERENCE    = "preference"     # explicit or inferred preference
    FACT          = "fact"           # biographical / factual assertion
    GOAL          = "goal"           # short- or long-term goal
    BELIEF        = "belief"         # world-view, value, opinion

    # Operational
    TASK          = "task"           # action item / TODO
    PLAN          = "plan"           # multi-step plan or strategy
    ARTIFACT      = "artifact"       # reference to a file/doc/code snippet

    # Metacognitive
    REFLECTION    = "reflection"     # GAIA's self-observation
    FEEDBACK      = "feedback"       # explicit user feedback on GAIA

    # Catch-all
    NOTE          = "note"           # unclassified note


class MemoryTier(str, Enum):
    """Lifetime tier — controls pruning priority."""

    WORKING     = "working"      # Current turn; evicts at turn end. Zero persistence.
    EPHEMERAL   = "ephemeral"    # single session; pruned first (legacy alias for WORKING)
    SHORT_TERM  = "short_term"   # days; pruned second
    LONG_TERM   = "long_term"    # weeks–months; pruned only under pressure
    PERMANENT   = "permanent"    # never auto-pruned (user-pinned facts etc.)


@dataclass
class MemoryItem:
    """
    One unit of memory.  Mirrors a row in the ``memory_items`` SQLite table.

    Attributes
    ----------
    id          : int       Row id (assigned by the store on insert).
    user_id     : str       Which user this memory belongs to.
    kind        : MemoryKind
    tier        : MemoryTier
    role        : str       'user' | 'gaia' | 'system'
    text        : str       The canonical text chunk (200–500 tokens).
    importance  : float     0.0–1.0; higher = more important to keep.
    created_at  : int       Unix timestamp (seconds).
    session_id  : str | None  Optional session grouping.
    topic_tag   : str | None  Coarse topic label for filtered retrieval.
    ttl_seconds : int | None  Optional time-to-live hint for ephemeral items.
    deleted     : bool      Soft-delete flag.
    """

    user_id:     str
    text:        str
    role:        str                   = "user"
    kind:        MemoryKind            = MemoryKind.MESSAGE
    tier:        MemoryTier            = MemoryTier.SHORT_TERM
    importance:  float                 = 0.5
    created_at:  int                   = field(default_factory=lambda: int(time.time()))
    id:          Optional[int]         = None
    session_id:  Optional[str]         = None
    topic_tag:   Optional[str]         = None
    ttl_seconds: Optional[int]         = None
    deleted:     bool                  = False

    # --- helpers -----------------------------------------------------------

    def is_expired(self) -> bool:
        """Return True if a TTL was set and has elapsed."""
        if self.ttl_seconds is None:
            return False
        return int(time.time()) > self.created_at + self.ttl_seconds

    def age_seconds(self) -> int:
        """Seconds since this memory was created."""
        return int(time.time()) - self.created_at

    def priority_score(self, recency_weight: float = 0.3) -> float:
        """
        Combined keep-priority score (higher = more worth keeping).
        Used by the pruner when selecting eviction candidates.
        """
        recency = 1.0 / (1.0 + self.age_seconds() / 86_400)  # decays over days
        tier_boost = {
            MemoryTier.PERMANENT:  1.0,
            MemoryTier.LONG_TERM:  0.7,
            MemoryTier.SHORT_TERM: 0.4,
            MemoryTier.EPHEMERAL:  0.1,
            MemoryTier.WORKING:    0.0,
        }.get(self.tier, 0.1)
        return (
            self.importance * (1.0 - recency_weight)
            + recency * recency_weight
            + tier_boost * 0.2
        )
