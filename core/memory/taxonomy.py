"""
core/memory/taxonomy.py
=======================
Canonical taxonomy for GAIA's memory sub-system.

Canon refs: C34, C01
"""
from __future__ import annotations

import time as _time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MemoryKind(str, Enum):
    """Semantic category of a stored memory item."""

    MESSAGE    = "message"
    FACT       = "fact"
    PREFERENCE = "preference"
    GOAL       = "goal"
    EMOTION    = "emotion"
    SKILL      = "skill"
    EVENT      = "event"
    CONTEXT    = "context"
    REFLECTION = "reflection"
    NOTE       = "note"


class MemoryTier(str, Enum):
    """Lifetime tier — controls pruning priority.

    String values allow transparent storage in SQL / JSON without a
    separate mapping table.  Use ``.value`` to get the string for DB writes.
    """

    EPHEMERAL  = "ephemeral"
    WORKING    = "working"
    SHORT_TERM = "short_term"
    EPISODIC   = "episodic"
    SEMANTIC   = "semantic"
    LONG_TERM  = "long_term"
    PERMANENT  = "permanent"


@dataclass
class MemoryItem:
    """A single memory record stored in one of the memory tiers.

    Parameters
    ----------
    content / text :
        The memory content string.  ``text`` is an alias for ``content``
        accepted at construction time for compatibility with callers that
        use ``MemoryItem(text=...)``.  Stored internally as ``content``.
    role :
        Optional conversational role label (e.g. ``"user"``, ``"assistant"``).
        Stored as a metadata key when provided.
    topic_tag :
        Optional free-form topic label for filtered retrieval.
    ttl_seconds :
        Optional time-to-live in seconds from ``created_at``.  When set,
        ``is_expired()`` returns True once the TTL has elapsed.
    """

    content:     str
    kind:        MemoryKind          = MemoryKind.MESSAGE
    tier:        MemoryTier          = MemoryTier.SHORT_TERM
    importance:  float               = 0.5
    user_id:     Optional[str]       = None
    gaian_id:    Optional[str]       = None
    session_id:  Optional[str]       = None
    role:        Optional[str]       = None
    tags:        List[str]           = field(default_factory=list)
    metadata:    Dict[str, Any]      = field(default_factory=dict)
    created_at:  datetime            = field(default_factory=datetime.utcnow)
    updated_at:  Optional[datetime]  = None
    id:          Optional[str]       = None
    topic_tag:   Optional[str]       = None   # ← explicit field for test/store compat
    ttl_seconds: Optional[int]       = None   # ← explicit field for TTL support

    def __init__(
        self,
        content: str = "",
        *,
        text:        Optional[str]       = None,   # ← alias for content
        kind:        MemoryKind          = MemoryKind.MESSAGE,
        tier:        MemoryTier          = MemoryTier.SHORT_TERM,
        importance:  float               = 0.5,
        user_id:     Optional[str]       = None,
        gaian_id:    Optional[str]       = None,
        session_id:  Optional[str]       = None,
        role:        Optional[str]       = None,
        tags:        Optional[List[str]] = None,
        metadata:    Optional[Dict[str, Any]] = None,
        created_at:  Optional[datetime]  = None,
        updated_at:  Optional[datetime]  = None,
        id:          Optional[str]       = None,
        topic_tag:   Optional[str]       = None,
        ttl_seconds: Optional[int]       = None,
        deleted:     bool                = False,
    ) -> None:
        # Accept ``text`` as an alias for ``content``
        self.content     = text if text is not None else content
        self.kind        = kind
        self.tier        = tier
        self.importance  = importance
        self.user_id     = user_id
        self.gaian_id    = gaian_id
        self.session_id  = session_id
        self.role        = role
        self.tags        = tags if tags is not None else []
        self.metadata    = metadata if metadata is not None else {}
        self.created_at  = created_at or datetime.utcnow()
        self.updated_at  = updated_at
        self.id          = id
        self.topic_tag   = topic_tag
        self.ttl_seconds = ttl_seconds
        self.deleted     = deleted

    # ------------------------------------------------------------------
    # Aliases
    # ------------------------------------------------------------------

    @property
    def text(self) -> str:
        """Alias: return content as 'text' for callers that read item.text."""
        return self.content

    # ------------------------------------------------------------------
    # TTL helpers
    # ------------------------------------------------------------------

    def _created_epoch(self) -> int:
        """Return created_at as a UTC epoch integer."""
        if isinstance(self.created_at, datetime):
            return int(self.created_at.timestamp())
        return int(self.created_at)

    def age_seconds(self) -> int:
        """Return age of this item in whole seconds since created_at."""
        return max(0, int(_time.time()) - self._created_epoch())

    def is_expired(self) -> bool:
        """Return True if TTL has elapsed; False if no TTL is set."""
        if self.ttl_seconds is None:
            return False
        return self.age_seconds() >= self.ttl_seconds

    # ------------------------------------------------------------------
    # Priority scoring
    # ------------------------------------------------------------------

    def priority_score(self) -> float:
        """Compute a blended priority: importance x tier-weight x recency-decay.

        Higher = more important to keep / surface first.
        Decays to ~36.8 % of its initial value after 24 h.
        """
        _TIER_WEIGHTS: Dict[MemoryTier, float] = {
            MemoryTier.EPHEMERAL:  0.5,
            MemoryTier.WORKING:    1.0,
            MemoryTier.SHORT_TERM: 1.2,
            MemoryTier.EPISODIC:   1.5,
            MemoryTier.SEMANTIC:   1.8,
            MemoryTier.LONG_TERM:  2.0,
            MemoryTier.PERMANENT:  2.0,
        }
        tier_w     = _TIER_WEIGHTS.get(self.tier, 1.0)
        age_decay  = max(0.0, 1.0 - (self.age_seconds() / 86_400.0))
        return self.importance * tier_w * age_decay

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id":          self.id,
            "content":     self.content,
            "kind":        self.kind.value,
            "tier":        self.tier.value,
            "importance":  self.importance,
            "user_id":     self.user_id,
            "gaian_id":    self.gaian_id,
            "session_id":  self.session_id,
            "role":        self.role,
            "tags":        self.tags,
            "metadata":    self.metadata,
            "topic_tag":   self.topic_tag,
            "ttl_seconds": self.ttl_seconds,
            "created_at":  self.created_at.isoformat(),
            "updated_at":  self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        return cls(
            content     = data.get("content", data.get("text", "")),
            kind        = MemoryKind(data.get("kind", "message")),
            tier        = MemoryTier(data.get("tier", "short_term")),
            importance  = float(data.get("importance", 0.5)),
            user_id     = data.get("user_id"),
            gaian_id    = data.get("gaian_id"),
            session_id  = data.get("session_id"),
            role        = data.get("role"),
            tags        = data.get("tags", []),
            metadata    = data.get("metadata", {}),
            topic_tag   = data.get("topic_tag"),
            ttl_seconds = data.get("ttl_seconds"),
            created_at  = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            updated_at  = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            id          = data.get("id"),
        )


__all__ = ["MemoryItem", "MemoryKind", "MemoryTier"]
