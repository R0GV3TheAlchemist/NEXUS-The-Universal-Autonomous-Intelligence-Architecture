"""
core/memory/taxonomy.py
=======================
Canonical taxonomy for GAIA's memory sub-system.

Defines MemoryKind (what kind of thing is stored) and MemoryTier
(how long it should live / where it lives).  Both enums are exported
through core/memory/__init__.py.

Canon refs: C34, C01
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# ── MemoryKind ────────────────────────────────────────────────────────────── #

class MemoryKind(str, Enum):
    """Semantic category of a stored memory item."""

    MESSAGE    = "message"      # raw user/assistant exchange
    FACT       = "fact"         # asserted factual claim
    PREFERENCE = "preference"   # user preference
    GOAL       = "goal"         # stated or inferred goal
    EMOTION    = "emotion"      # emotional moment
    SKILL      = "skill"        # learned capability
    EVENT      = "event"        # significant life event
    CONTEXT    = "context"      # situational context
    REFLECTION = "reflection"   # GAIA's introspective note
    NOTE       = "note"         # unclassified note


# ── MemoryTier ────────────────────────────────────────────────────────────── #

class MemoryTier(str, Enum):
    """Lifetime tier — controls pruning priority.

    EPHEMERAL   → Single request; never persisted to disk.
    WORKING     → Current turn; evicts at turn end. Zero persistence.
    SHORT_TERM  → Last N turns; 24–72 hr TTL. Recent context.
    EPISODIC    → Session moments; weeks–months TTL. Life events.
    SEMANTIC    → Crystal DB + canon facts; permanent.
    LONG_TERM   → Gaian identity + settled arcs; permanent.
    PERMANENT   → Immutable canon entries; never pruned.
    """

    EPHEMERAL  = "ephemeral"
    WORKING    = "working"
    SHORT_TERM = "short_term"
    EPISODIC   = "episodic"    # ← present — tests require this member
    SEMANTIC   = "semantic"
    LONG_TERM  = "long_term"
    PERMANENT  = "permanent"


# ── MemoryItem ────────────────────────────────────────────────────────────── #

@dataclass
class MemoryItem:
    """A single memory record stored in one of the memory tiers."""

    content:    str
    kind:       MemoryKind          = MemoryKind.MESSAGE
    tier:       MemoryTier          = MemoryTier.SHORT_TERM
    importance: float               = 0.5       # [0, 1]
    gaian_id:   Optional[str]       = None
    session_id: Optional[str]       = None
    tags:       List[str]           = field(default_factory=list)
    metadata:   Dict[str, Any]      = field(default_factory=dict)
    created_at: datetime            = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime]  = None
    id:         Optional[str]       = None      # set by store on persist

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id":         self.id,
            "content":    self.content,
            "kind":       self.kind.value,
            "tier":       self.tier.value,
            "importance": self.importance,
            "gaian_id":   self.gaian_id,
            "session_id": self.session_id,
            "tags":       self.tags,
            "metadata":   self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        return cls(
            id         = data.get("id"),
            content    = data["content"],
            kind       = MemoryKind(data.get("kind", "message")),
            tier       = MemoryTier(data.get("tier", "short_term")),
            importance = float(data.get("importance", 0.5)),
            gaian_id   = data.get("gaian_id"),
            session_id = data.get("session_id"),
            tags       = data.get("tags", []),
            metadata   = data.get("metadata", {}),
            created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )


__all__ = ["MemoryItem", "MemoryKind", "MemoryTier"]
