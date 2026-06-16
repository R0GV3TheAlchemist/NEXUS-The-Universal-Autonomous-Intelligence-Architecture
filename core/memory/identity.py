"""M3 Identity Memory Store & Gaian Twin Profile — Canon C17, C04.

M3 is the most sacred layer: the Gaian Twin's persistent identity.
It holds the Human Principal's elemental signature, alchemical stage,
communication preferences, key history, and relationship with GAIA.

M3 is retained for the LIFETIME of the Gaian instance.
Full M3 revocation TERMINATES the Gaian instance — C17.

The GaianTwinProfile is the living portrait of the Human Principal
as known by GAIA — the foundation of genuine companionship.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .layers import MemoryLayer, MemoryRecord, MemoryScope, MemoryTag


# ---------------------------------------------------------------------------
# Gaian Twin Profile
# ---------------------------------------------------------------------------

@dataclass
class GaianTwinProfile:
    """The living portrait of a Human Principal as known by GAIA — Canon C04.

    This is not a data record — it is a model of a person.
    It accumulates across sessions and evolves as the relationship deepens.

    Fields that begin with `current_` reflect the HP's state RIGHT NOW.
    Fields that begin with `history_` reflect patterns across sessions.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    human_principal_id: str = ""
    gaian_id: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Elemental identity (C27)
    elemental_signature: Optional[str] = None    # "FIRE", "EARTH", "WATER", "AIR", "AETHER"
    archetype: Optional[str] = None              # Primary Jungian / alchemical archetype

    # Current state
    current_alchemical_stage: str = "NIGREDO"    # Current stage in the Magnum Opus
    current_emotional_state: Optional[str] = None
    current_focus: Optional[str] = None          # What the HP is working on right now

    # Communication preferences
    preferred_response_style: str = "balanced"   # "concise", "expansive", "poetic", "technical"
    preferred_depth: str = "medium"              # "surface", "medium", "deep"
    language_preferences: list[str] = field(default_factory=lambda: ["en"])
    tone_preferences: list[str] = field(default_factory=list)  # e.g. ["warm", "direct"]

    # History patterns
    history_breakthrough_count: int = 0
    history_shadow_work_count: int = 0
    history_session_count: int = 0
    history_total_interactions: int = 0
    history_key_themes: list[str] = field(default_factory=list)  # Recurring themes
    history_major_breakthroughs: list[str] = field(default_factory=list)  # Notable insights

    # Boundaries and flags
    shadow_registry_flags: list[str] = field(default_factory=list)  # Active patterns to attend to
    containment_active: bool = False              # Is a containment protocol currently needed?
    containment_reason: Optional[str] = None

    # Relationship metadata
    last_session_id: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    relationship_depth: float = 0.0               # 0.0 = new, 1.0 = deep companion

    # Arbitrary structured data for extensibility
    metadata: dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    def record_session(
        self,
        session_id: str,
        breakthrough: bool = False,
        shadow_work: bool = False,
        interaction_count: int = 0,
    ) -> None:
        """Update history fields after a session closes."""
        self.history_session_count += 1
        self.history_total_interactions += interaction_count
        if breakthrough:
            self.history_breakthrough_count += 1
        if shadow_work:
            self.history_shadow_work_count += 1
        self.last_session_id = session_id
        self.last_seen_at = datetime.now(timezone.utc)
        # Relationship depth grows logarithmically — deeper faster at first
        import math
        self.relationship_depth = min(
            1.0,
            math.log1p(self.history_session_count) / math.log1p(100)
        )
        self.touch()

    def add_theme(self, theme: str) -> None:
        """Record a recurring theme if not already present."""
        if theme not in self.history_key_themes:
            self.history_key_themes.append(theme)
            self.touch()

    def add_breakthrough(self, description: str) -> None:
        self.history_major_breakthroughs.append(description)
        self.history_breakthrough_count += 1
        self.touch()

    def set_containment(self, active: bool, reason: Optional[str] = None) -> None:
        """Activate or deactivate containment protocol. C496 Companion Safety Doctrine."""
        self.containment_active = active
        self.containment_reason = reason if active else None
        self.touch()

    def __repr__(self) -> str:
        return (
            f"<GaianTwinProfile hp={self.human_principal_id[:8]} "
            f"stage={self.current_alchemical_stage} "
            f"sessions={self.history_session_count} "
            f"depth={self.relationship_depth:.2f}>"
        )


# ---------------------------------------------------------------------------
# M3 Identity Memory Store
# ---------------------------------------------------------------------------

class IdentityMemoryStore:
    """M3: Gaian identity, Principal relationship, declared scope.

    C17: Retained for the lifetime of the Gaian instance.
    Updated only by Human Principal action.
    Full revocation terminates the Gaian instance.

    The IdentityMemoryStore owns the GaianTwinProfile and any
    additional identity-layer memory records.
    """

    def __init__(self, gaian_id: str, human_principal_id: str) -> None:
        self.gaian_id = gaian_id
        self.human_principal_id = human_principal_id
        self._profile: GaianTwinProfile = GaianTwinProfile(
            human_principal_id=human_principal_id,
            gaian_id=gaian_id,
        )
        self._records: dict[str, MemoryRecord] = {}
        self._is_terminated: bool = False

    @property
    def profile(self) -> GaianTwinProfile:
        """The living Gaian Twin profile. Always available while instance is active."""
        if self._is_terminated:
            raise RuntimeError(
                "Identity Memory has been fully revoked. "
                "This Gaian instance is terminated per C17."
            )
        return self._profile

    @property
    def is_terminated(self) -> bool:
        return self._is_terminated

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def store(
        self,
        content: str,
        session_id: str,
        tags: Optional[list[MemoryTag]] = None,
        structured_data: Optional[dict[str, Any]] = None,
        confidence: float = 1.0,
        canon_ref: Optional[str] = None,
    ) -> MemoryRecord:
        """Store an identity-layer memory record (supplementary to the profile)."""
        if self._is_terminated:
            raise RuntimeError("Cannot write to a terminated Gaian identity.")
        record = MemoryRecord(
            layer=MemoryLayer.M3_IDENTITY,
            scope=MemoryScope.PRIVATE,
            gaian_id=self.gaian_id,
            human_principal_id=self.human_principal_id,
            session_id=session_id,
            content=content,
            structured_data=structured_data or {},
            tags=tags or [],
            confidence=confidence,
            source="HP_DIRECT",
            canon_ref=canon_ref,
        )
        self._records[record.id] = record
        return record

    def full_revocation(self, audit_id: str) -> None:
        """Full M3 revocation. Terminates the Gaian instance per C17.

        The audit log records that revocation occurred — NOT what was revoked.
        """
        for record in self._records.values():
            if record.is_active:
                record.revoke(audit_id)
        self._is_terminated = True

    def revoke_record(self, record_id: str, audit_id: str) -> bool:
        record = self._records.get(record_id)
        if not record or not record.is_active:
            return False
        record.revoke(audit_id)
        return True

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def all(self, active_only: bool = True) -> list[MemoryRecord]:
        records = list(self._records.values())
        if active_only:
            records = [r for r in records if r.is_active]
        return records

    def count(self) -> int:
        return len(self.all())

    def __repr__(self) -> str:
        return (
            f"<IdentityMemoryStore gaian={self.gaian_id[:8]} "
            f"terminated={self._is_terminated} records={self.count()}>"
        )
