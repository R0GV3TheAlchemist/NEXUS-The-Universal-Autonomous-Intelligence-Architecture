"""GAIA Memory Layer Definitions — Canon C17 Memory Architecture Table.

Five memory layers, each with distinct persistence, scope, and access rules.
All memory records carry provenance, confidence, and revocation metadata.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class MemoryLayer(str, Enum):
    """The five C17 memory layers.

    M0 — Session Buffer: in-session working memory, never persisted automatically.
    M1 — Episodic Memory: records of specific sessions and events.
    M2 — Semantic Memory: accumulated knowledge and world model state.
    M3 — Identity Memory: Gaian identity, Principal relationship, declared scope.
    M4 — Shared Memory: explicitly authorised cross-instance shared context.
    """
    M0_SESSION = "M0_SESSION"
    M1_EPISODIC = "M1_EPISODIC"
    M2_SEMANTIC = "M2_SEMANTIC"
    M3_IDENTITY = "M3_IDENTITY"
    M4_SHARED = "M4_SHARED"


class MemoryScope(str, Enum):
    """Who owns and can access this memory record."""
    PRIVATE = "PRIVATE"       # Only the owning Gaian + Human Principal
    SHARED = "SHARED"         # Explicitly shared across authorised instances
    COLLECTIVE = "COLLECTIVE" # Noosphere layer — anonymised, pattern-level


class MemoryTag(str, Enum):
    """Semantic classification tags for memory records."""
    BREAKTHROUGH = "BREAKTHROUGH"     # A major insight or realisation
    SHADOW = "SHADOW"                 # Shadow material, failure, aversion
    PREFERENCE = "PREFERENCE"         # Stated preference or boundary
    ALCHEMICAL = "ALCHEMICAL"         # Alchemical stage event
    ECOLOGICAL = "ECOLOGICAL"         # ATLAS Node / world fabric data
    RELATIONAL = "RELATIONAL"         # Relationship between entities
    EMOTIONAL = "EMOTIONAL"           # Emotional state record
    FACTUAL = "FACTUAL"               # World knowledge, semantic fact
    CANON = "CANON"                   # Canon document reference
    SESSION_SUMMARY = "SESSION_SUMMARY"  # End-of-session distillation


@dataclass
class MemoryRecord:
    """A single memory record — the atomic unit of GAIA's memory system.

    Every record carries:
    - Full provenance (who created it, when, in what session)
    - Confidence score (0.0 = uncertain, 1.0 = verified ground truth)
    - Relevance score (set by retrieval engine at query time)
    - Revocation state (Human Principal may revoke any record)
    - Decay tracking (stale data flagged per C14 World Fabric governance)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    layer: MemoryLayer = MemoryLayer.M1_EPISODIC
    scope: MemoryScope = MemoryScope.PRIVATE
    gaian_id: str = ""
    human_principal_id: str = ""
    session_id: str = ""
    content: str = ""                        # The memory itself — natural language
    structured_data: dict[str, Any] = field(default_factory=dict)  # Optional structured payload
    tags: list[MemoryTag] = field(default_factory=list)
    confidence: float = 1.0                  # 0.0–1.0; per C14 confidence classes
    relevance: float = 0.0                   # Set by retrieval engine at query time
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None    # None = never expires
    is_revoked: bool = False
    revoked_at: Optional[datetime] = None
    revocation_audit_id: Optional[str] = None  # Audit trail entry ID for this revocation
    source: str = ""                         # e.g. "SESSION", "HP_DIRECT", "WORLD_FABRIC"
    canon_ref: Optional[str] = None          # e.g. "C03", "C17" if memory references canon

    @property
    def is_active(self) -> bool:
        """A record is active if not revoked and not expired."""
        if self.is_revoked:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True

    @property
    def age_days(self) -> float:
        """Age of this record in days."""
        delta = datetime.now(timezone.utc) - self.created_at
        return delta.total_seconds() / 86400

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    def revoke(self, audit_id: str) -> None:
        """Revoke this record. The audit log records that revocation occurred — not content."""
        self.is_revoked = True
        self.revoked_at = datetime.now(timezone.utc)
        self.revocation_audit_id = audit_id
        self.touch()

    def __repr__(self) -> str:
        return (
            f"<MemoryRecord {self.id[:8]} layer={self.layer.value} "
            f"tags={[t.value for t in self.tags]} active={self.is_active}>"
        )
