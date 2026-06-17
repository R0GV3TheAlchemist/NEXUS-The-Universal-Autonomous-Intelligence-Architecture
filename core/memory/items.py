"""
core/memory/items.py

Core data models for the GAIA-OS semantic memory layer.
Canon Reference: C01 (Gaian Sovereignty), C-SENTINEL Article 4
Issue: #213
Version: 1.1.0
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


# Tier priority weights for priority_score().
# Strings used here because PERMANENT/EPHEMERAL are not hierarchy enum members.
_TIER_PRIORITY: dict[str, float] = {
    "permanent":  0.5,
    "long_term":  0.4,
    "semantic":   0.4,
    "episodic":   0.2,
    "short_term": 0.1,
    "working":    0.05,
    "ephemeral":  0.0,
}


@dataclass
class MemoryItem:
    """
    A single item stored in the GAIA semantic memory layer.
    All fields are inspectable and exportable by the Gaian.
    """
    user_id:     str
    text:        str               = ""
    kind:        MemoryKind        = MemoryKind.MESSAGE
    tier:        Any               = None
    role:        str               = "user"
    importance:  float             = 0.5
    topic_tag:   Optional[str]     = None
    metadata:    dict              = field(default_factory=dict)
    created_at:  int               = field(default_factory=lambda: int(time.time()))
    ttl_seconds: Optional[int]     = None
    id:          Optional[int]     = None
    deleted:     bool              = False

    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        return (int(time.time()) - self.created_at) >= self.ttl_seconds

    def age_seconds(self) -> int:
        return max(0, int(time.time()) - self.created_at)

    def priority_score(self) -> float:
        """
        Higher importance + higher-priority tier = higher score.
        Used by MemoryPruner to decide what to keep.
        """
        tier_val = self.tier.value if hasattr(self.tier, 'value') else str(self.tier or "ephemeral")
        tier_bonus = _TIER_PRIORITY.get(tier_val, 0.0)
        return self.importance + tier_bonus


@dataclass
class RetrievedMemory:
    """
    A MemoryItem returned from a retrieval query, augmented with a
    relevance score and the query that produced it.
    """
    item:  MemoryItem
    score: float      = 0.0
    query: str        = ""

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


from core.memory.pruner import MemoryPruner  # noqa: F401 re-export


from core.memory.memory_store import MemoryStore  # noqa: F401 re-export


from core.memory.memory_store import MemoryTier  # noqa: F401 re-export
