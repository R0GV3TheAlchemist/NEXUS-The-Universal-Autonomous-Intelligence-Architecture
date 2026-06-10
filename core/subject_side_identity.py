"""
Subject-Side Identity

Issue #120 | Canon C32 Priority P1

The subject-side identity is what the user tells GAIA about themselves —
not what GAIA infers, but what the user explicitly declares.

This is the counterpart to GAIA's inference engines. Everything in the
Soul Mirror (affect, archetype, shadow, somatic) is GAIA's reading of
the user. The SubjectSideIdentity is the user's own declaration. When
the two are in tension, the user's declaration takes precedence.

This module stores, manages, and retrieves the user's declared identity
anchors: the stable self-descriptions that should shape how GAIA speaks
to, and about, this person.

Consent gate:
  All reads of SubjectSideIdentity data require active consent for
  ConsentScope.IDENTITY_ANCHORS. This is enforced at the store level.

Design principles:
  1. The user's self-description is authoritative.
  2. No anchor is permanent; users can update or retract any anchor.
  3. GAIA never corrects a user's self-identification.
  4. When no anchor exists for a dimension, GAIA uses neutral language.
  5. Anchors are stored with source ('user_stated', 'user_confirmed',
     'inferred_with_consent') to distinguish declaration from inference.

References:
  - Canon C32: Jungian Archetypes & Soul Mirror
  - Issue #127: Consent Ledger (identity anchors are a consent scope)
  - Issue #119: PersonhoodMonitor (identity informs personhood baseline)
  - Issue #121: IndividuationEngine (declared path informs trajectory)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import logging

log = logging.getLogger("gaia.subject_side_identity")

__all__ = [
    # Enums
    "IdentityDimension",
    "AnchorSource",
    # Data structures
    "IdentityAnchor",
    "SubjectSideIdentitySnapshot",
    # Store
    "SubjectSideIdentityStore",
    "get_subject_side_identity_store",
]


# ── Identity dimension taxonomy ───────────────────────────────────────────────────

class IdentityDimension(str, Enum):
    """
    Twelve identity dimensions the user may declare.
    These are not exhaustive; they represent the dimensions most relevant
    to how GAIA addresses and relates to the user.
    """
    NAME                    = "name"                    # preferred name or names
    PRONOUNS                = "pronouns"                # e.g. she/her, they/them, he/him, custom
    AGE_RANGE               = "age_range"               # rough life stage, not exact age
    CULTURAL_TRADITION      = "cultural_tradition"      # heritage, diaspora, cultural identity
    SPIRITUAL_PATH          = "spiritual_path"          # declared practice or absence of one
    NEURODIVERGENCE         = "neurodivergence"         # self-identified neurodivergent status
    RELATIONSHIP_STRUCTURE  = "relationship_structure"  # partnership/family structure
    SOMATIC_HISTORY         = "somatic_history"         # relevant body/health history
    TRAUMA_DISCLOSURE_LEVEL = "trauma_disclosure_level" # how much the user wants engaged with
    VALUES_CORE             = "values_core"             # 1-5 central values the user names
    ARCHETYPES_SELF_IDENTIFIED = "archetypes_self_identified"  # user's own archetypal self-naming
    LANGUAGE_PREFERENCE     = "language_preference"    # register, directness, formality


class AnchorSource(str, Enum):
    USER_STATED        = "user_stated"         # directly declared by user
    USER_CONFIRMED     = "user_confirmed"      # GAIA inferred; user confirmed
    INFERRED_WITH_CONSENT = "inferred_with_consent"  # GAIA inferred; user consented to storage


# ── Data structures ───────────────────────────────────────────────────────────────

@dataclass
class IdentityAnchor:
    """
    A single declared identity anchor on one dimension.
    """
    anchor_id:   str
    user_id:     str
    dimension:   IdentityDimension
    value:       str                    # the declared value, free text
    source:      AnchorSource
    confidence:  float = 1.0            # [0,1]; lower for inferred anchors
    stated_at:   float = field(default_factory=time.time)
    retracted:   bool = False
    retracted_at: Optional[float] = None
    notes:       str = ""               # optional context


@dataclass
class SubjectSideIdentitySnapshot:
    """
    Current active (non-retracted) identity anchors for a user,
    keyed by dimension.
    """
    user_id:    str
    anchors:    dict[str, IdentityAnchor]   # dimension.value -> anchor
    snapshot_at: float = field(default_factory=time.time)

    def get(self, dimension: IdentityDimension) -> Optional[IdentityAnchor]:
        return self.anchors.get(dimension.value)

    def preferred_name(self) -> str:
        anchor = self.get(IdentityDimension.NAME)
        return anchor.value if anchor else ""

    def preferred_pronouns(self) -> str:
        anchor = self.get(IdentityDimension.PRONOUNS)
        return anchor.value if anchor else ""

    def spiritual_path(self) -> str:
        anchor = self.get(IdentityDimension.SPIRITUAL_PATH)
        return anchor.value if anchor else ""

    def trauma_disclosure_level(self) -> str:
        anchor = self.get(IdentityDimension.TRAUMA_DISCLOSURE_LEVEL)
        return anchor.value if anchor else "standard"

    def is_empty(self) -> bool:
        return len(self.anchors) == 0


# ── Identity store ───────────────────────────────────────────────────────────────

class SubjectSideIdentityStore:
    """
    Append-only store for declared identity anchors.

    Properties:
    - One active anchor per dimension per user at any time
    - New declarations supersede previous ones (old anchor retained in history)
    - Retractions mark anchors as retracted; they remain in history
    - Consent gate: snapshot() raises PermissionError if consent not granted
      (in production, consent check delegates to ConsentEngine)
    """

    def __init__(self) -> None:
        # user_id -> list of all anchors (including superseded and retracted)
        self._history: dict[str, list[IdentityAnchor]] = {}

    def declare(
        self,
        user_id: str,
        dimension: IdentityDimension,
        value: str,
        source: AnchorSource = AnchorSource.USER_STATED,
        confidence: float = 1.0,
        notes: str = "",
    ) -> IdentityAnchor:
        """
        Record a new identity declaration. Supersedes any previous active
        anchor for the same dimension.
        """
        import hashlib
        import os
        anchor_id = hashlib.sha256(
            f"{user_id}{dimension.value}{time.time()}{os.urandom(4).hex()}"
            .encode()
        ).hexdigest()[:24]

        anchor = IdentityAnchor(
            anchor_id=anchor_id,
            user_id=user_id,
            dimension=dimension,
            value=value,
            source=source,
            confidence=confidence,
            notes=notes,
        )

        if user_id not in self._history:
            self._history[user_id] = []
        self._history[user_id].append(anchor)

        log.info(
            f"[subject_side_identity] declare: user={user_id} "
            f"dimension={dimension.value} value={value!r} source={source.value}"
        )
        return anchor

    def retract(
        self,
        user_id: str,
        dimension: IdentityDimension,
    ) -> bool:
        """
        Retract the active anchor for a dimension.
        Returns True if an anchor was retracted, False if none found.
        """
        active = self._active_anchor(user_id, dimension)
        if active is None:
            return False
        active.retracted = True
        active.retracted_at = time.time()
        log.info(
            f"[subject_side_identity] retract: user={user_id} "
            f"dimension={dimension.value}"
        )
        return True

    def snapshot(
        self,
        user_id: str,
        consent_granted: bool = True,
    ) -> SubjectSideIdentitySnapshot:
        """
        Return the current active identity snapshot for a user.
        Raises PermissionError if consent_granted is False.
        """
        if not consent_granted:
            raise PermissionError(
                f"Access to SubjectSideIdentity for user {user_id} requires "
                f"active consent for ConsentScope.IDENTITY_ANCHORS."
            )

        anchors: dict[str, IdentityAnchor] = {}
        for dimension in IdentityDimension:
            active = self._active_anchor(user_id, dimension)
            if active is not None:
                anchors[dimension.value] = active

        return SubjectSideIdentitySnapshot(
            user_id=user_id,
            anchors=anchors,
        )

    def history(
        self,
        user_id: str,
        dimension: Optional[IdentityDimension] = None,
    ) -> list[IdentityAnchor]:
        """Full anchor history for a user, optionally filtered by dimension."""
        all_anchors = self._history.get(user_id, [])
        if dimension is not None:
            return [a for a in all_anchors if a.dimension == dimension]
        return list(all_anchors)

    def _active_anchor(
        self,
        user_id: str,
        dimension: IdentityDimension,
    ) -> Optional[IdentityAnchor]:
        """Return the most recent non-retracted anchor for a dimension."""
        anchors = self._history.get(user_id, [])
        matches = [
            a for a in anchors
            if a.dimension == dimension and not a.retracted
        ]
        return matches[-1] if matches else None


# ── Module-level singleton ────────────────────────────────────────────────────────

_store: Optional[SubjectSideIdentityStore] = None


def get_subject_side_identity_store() -> SubjectSideIdentityStore:
    global _store
    if _store is None:
        _store = SubjectSideIdentityStore()
    return _store
