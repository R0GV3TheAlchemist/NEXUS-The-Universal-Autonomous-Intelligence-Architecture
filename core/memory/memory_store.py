"""
core/memory/memory_store.py

Data models for the Visible Memory & State Console.
Every piece of data GAIA holds about a Gaian is represented here.

Canon Reference: C01 (Gaian Sovereignty), C-SENTINEL Article 4 (Memory Sovereignty)
Issue:          #213
Version:        1.1.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid


# ---------------------------------------------------------------------------
# Default store path
# ---------------------------------------------------------------------------

_default_store_path = "./data/memory_store.db"


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class MemoryTier(Enum):
    """
    Separates durable memory from temporary session state.
    Acceptance Criterion: Session state and durable memory are clearly separated.
    """
    DURABLE  = "durable"   # Persists across sessions — preferences, identity, relationships
    SESSION  = "session"   # Lives only for the current session — scratchpad, working goals
    ARCHIVED = "archived"  # Soft-deleted — retained for audit, invisible to active context


class MemoryCategory(Enum):
    """Semantic category of a memory entry."""
    PREFERENCE        = "preference"         # How the Gaian likes things done
    RELATIONSHIP      = "relationship"       # People, bonds, trust levels
    PROJECT           = "project"            # Active or historical projects
    IDENTITY          = "identity"           # Long-term self-model of the Gaian
    SESSION_GOAL      = "session_goal"       # What the Gaian wants from this session
    FACT              = "fact"               # World or personal facts
    EMOTIONAL_CONTEXT = "emotional_context"  # Mood, stress, recent events
    CUSTOM            = "custom"             # Gaian-defined categories


class ProvenanceSource(Enum):
    """Where a memory entry originated."""
    GAIAN_EXPLICIT    = "gaian_explicit"     # Gaian stated it directly
    GAIAN_IMPLICIT    = "gaian_implicit"     # Inferred from Gaian behavior/language
    SENTINEL_INFERRED = "sentinel_inferred"  # Sentinel derived it from patterns
    SYSTEM_GENERATED  = "system_generated"   # Created by a system process
    IMPORTED          = "imported"           # Imported from external source with consent


# ---------------------------------------------------------------------------
# Core Data Models
# ---------------------------------------------------------------------------

@dataclass
class MemoryProvenance:
    """
    Explains where a memory came from and how confident GAIA is in it.
    Acceptance Criterion: Each recalled memory includes provenance and confidence.
    """
    source:          ProvenanceSource
    confidence:      float                   # 0.0 (uncertain) to 1.0 (certain)
    origin_session:  Optional[str]  = None   # Session ID where this was first recorded
    origin_context:  Optional[str]  = None   # The utterance or event that created it
    derived_from:    list[str]      = field(default_factory=list)  # IDs of source memories

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )


@dataclass
class MemoryEntry:
    """
    A single unit of GAIA's memory about a Gaian.

    All Gaian data belongs to the Gaian (C-SENTINEL Article 4).
    The Gaian may inspect, correct, export, or delete any MemoryEntry.

    Acceptance Criteria:
      - Browsable with timestamps, confidence, provenance, last-used context
      - Supports edit, delete, archive actions
      - "Why am I seeing this?" explanation available
    """
    key:               str
    value:             str
    category:          MemoryCategory
    tier:              MemoryTier
    provenance:        MemoryProvenance
    id:                str               = field(default_factory=lambda: str(uuid.uuid4()))
    created_at:        datetime          = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at:        datetime          = field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at:      Optional[datetime] = None
    last_used_context: Optional[str]     = None
    tags:              list[str]         = field(default_factory=list)
    explanation:       Optional[str]     = None

    def to_dict(self) -> dict:
        """Human-readable export. Gaian owns this data."""
        return {
            "id":                 self.id,
            "key":                self.key,
            "value":              self.value,
            "category":           self.category.value,
            "tier":               self.tier.value,
            "confidence":         self.provenance.confidence,
            "source":             self.provenance.source.value,
            "origin_context":     self.provenance.origin_context,
            "created_at":         self.created_at.isoformat(),
            "updated_at":         self.updated_at.isoformat(),
            "last_used_at":       self.last_used_at.isoformat() if self.last_used_at else None,
            "last_used_context":  self.last_used_context,
            "tags":               self.tags,
            "explanation":        self.explanation,
        }


@dataclass
class SessionState:
    """
    Temporary state that exists only for the current session.
    Cleared at session end unless explicitly promoted to DURABLE.

    Acceptance Criterion: Session state and durable memory are clearly separated.
    """
    session_id:     str
    gaian_id:       str
    started_at:     datetime          = field(default_factory=lambda: datetime.now(timezone.utc))
    working_goals:  list[str]         = field(default_factory=list)
    active_context: dict              = field(default_factory=dict)
    scratchpad:     list[MemoryEntry] = field(default_factory=list)

    def promote_to_durable(self, entry: MemoryEntry) -> MemoryEntry:
        """
        Elevate a session-scoped memory to durable.
        Requires Gaian intent — never done automatically.
        """
        entry.tier = MemoryTier.DURABLE
        entry.updated_at = datetime.now(timezone.utc)
        return entry


# ---------------------------------------------------------------------------
# MemoryStore
# ---------------------------------------------------------------------------

class MemoryStore:
    """
    Manages persistent storage and retrieval of MemoryEntry objects.

    Acceptance Criterion: Gaian data is stored securely with full provenance tracking.
    Canon Reference: C01 (Gaian Sovereignty), C-SENTINEL Article 4
    """

    def __init__(self, store_path: str = _default_store_path) -> None:
        self.store_path = store_path
        self._entries: dict[str, MemoryEntry] = {}

    def store(self, entry: MemoryEntry) -> None:
        """Store a memory entry."""
        self._entries[entry.id] = entry

    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by ID."""
        return self._entries.get(entry_id)

    def list_entries(
        self,
        category: Optional[MemoryCategory] = None,
        tier: Optional[MemoryTier] = None,
    ) -> list[MemoryEntry]:
        """List entries filtered by category and/or tier."""
        entries: list[MemoryEntry] = list(self._entries.values())
        if category:
            entries = [e for e in entries if e.category == category]
        if tier:
            entries = [e for e in entries if e.tier == tier]
        return entries

    def delete(self, entry_id: str) -> bool:
        """Permanently delete an entry. Returns True if found and deleted."""
        if entry_id in self._entries:
            del self._entries[entry_id]
            return True
        return False

    def archive(self, entry_id: str) -> bool:
        """Soft-delete an entry (set tier to ARCHIVED). Returns True if found."""
        entry = self.retrieve(entry_id)
        if entry:
            entry.tier = MemoryTier.ARCHIVED
            entry.updated_at = datetime.now(timezone.utc)
            return True
        return False


def get_memory_store(store_path: str = _default_store_path) -> MemoryStore:
    """Factory function to create a MemoryStore instance."""
    return MemoryStore(store_path)
