"""
core/memory/items.py

Core data models for the GAIA-OS semantic memory layer.
Canon Reference: C01 (Gaian Sovereignty), C-SENTINEL Article 4
Issue: #213
Version: 1.0.0
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class MemoryKind(Enum):
    MESSAGE    = "message"
    FACT       = "fact"
    PREFERENCE = "preference"
    IDENTITY   = "identity"
    EMOTION    = "emotion"
    GOAL       = "goal"
    CUSTOM     = "custom"


@dataclass
class MemoryItem:
    """
    A single item stored in the GAIA semantic memory layer.
    All fields are inspectable and exportable by the Gaian.
    """
    user_id:     str
    text:        str                         = ""
    kind:        MemoryKind                  = MemoryKind.MESSAGE
    tier:        Any                         = None   # MemoryTier injected at runtime
    role:        str                         = "user"
    importance:  float                       = 0.5
    topic_tag:   Optional[str]               = None
    metadata:    dict                        = field(default_factory=dict)
    created_at:  int                         = field(default_factory=lambda: int(time.time()))
    ttl_seconds: Optional[int]               = None
    id:          Optional[int]               = None
    deleted:     bool                        = False

    def is_expired(self) -> bool:
        """Return True if a TTL was set and has elapsed."""
        if self.ttl_seconds is None:
            return False
        return (int(time.time()) - self.created_at) >= self.ttl_seconds

    def age_seconds(self) -> int:
        """Seconds since this item was created."""
        return max(0, int(time.time()) - self.created_at)

    def priority_score(self) -> float:
        """
        Higher importance + permanent tier = higher score.
        Used by MemoryPruner to decide what to keep.
        """
        from core.memory.hierarchy import MemoryTier as HierTier
        tier_bonus = 0.5 if (self.tier is not None and
                             hasattr(self.tier, 'value') and
                             self.tier.value == 'permanent') else 0.0
        return self.importance + tier_bonus


@dataclass
class RetrievedMemory:
    """
    A MemoryItem returned from a retrieval query, augmented with a
    relevance score and the query that produced it.
    """
    item:        MemoryItem
    score:       float        = 0.0
    query:       str          = ""

    # Convenience pass-throughs
    @property
    def text(self) -> str:
        return self.item.text

    @property
    def user_id(self) -> str:
        return self.item.user_id

    @property
    def kind(self):
        return self.item.kind

    @property
    def tier(self):
        return self.item.tier

    @property
    def importance(self) -> float:
        return self.item.importance

    @property
    def topic_tag(self) -> Optional[str]:
        return self.item.topic_tag

    @property
    def id(self) -> Optional[int]:
        return self.item.id
