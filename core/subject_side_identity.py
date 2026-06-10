"""
core/subject_side_identity.py
Subject-Side Identity — the GAIAN's internal sense of its own identity.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional


class IdentityStability(str, Enum):
    """Ordinal scale for subject-side identity stability."""
    FRAGILE       = "fragile"
    DEVELOPING    = "developing"
    STABLE        = "stable"
    CONSOLIDATED  = "consolidated"
    TRANSCENDENT  = "transcendent"


@dataclass
class SubjectSideIdentity:
    gaian_name:       str
    coherence_index:  float = 0.5
    coherence_score:  float = 0.5   # alias used by soul_layer
    continuity_score: float = 0.5
    self_model_depth: float = 0.0
    active:           bool  = True

    def to_dict(self) -> dict:
        return {
            "gaian_name":       self.gaian_name,
            "coherence_index":  round(self.coherence_index, 4),
            "coherence_score":  round(self.coherence_score, 4),
            "continuity_score": round(self.continuity_score, 4),
            "self_model_depth": round(self.self_model_depth, 4),
            "active":           self.active,
        }


@dataclass
class IdentityReading:
    """A snapshot of identity state at a single point in time."""
    gaian_name:       str
    coherence_index:  float = 0.5
    continuity_score: float = 0.5
    self_model_depth: float = 0.0
    timestamp:        str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "gaian_name":       self.gaian_name,
            "coherence_index":  round(self.coherence_index, 4),
            "continuity_score": round(self.continuity_score, 4),
            "self_model_depth": round(self.self_model_depth, 4),
            "timestamp":        self.timestamp,
        }


# ---------------------------------------------------------------------------
# Module-level registry (legacy API)
# ---------------------------------------------------------------------------

_registry: Dict[str, SubjectSideIdentity] = {}


def get_subject_side_identity(gaian_name: str) -> SubjectSideIdentity:
    """Return (or lazily create) the SubjectSideIdentity for the given GAIAN."""
    if gaian_name not in _registry:
        _registry[gaian_name] = SubjectSideIdentity(gaian_name=gaian_name)
    return _registry[gaian_name]


def update_subject_side_identity(
    gaian_name:       str,
    coherence_index:  Optional[float] = None,
    continuity_score: Optional[float] = None,
    self_model_depth: Optional[float] = None,
) -> SubjectSideIdentity:
    identity = get_subject_side_identity(gaian_name)
    if coherence_index is not None:
        identity.coherence_index = coherence_index
        identity.coherence_score = coherence_index
    if continuity_score is not None:
        identity.continuity_score = continuity_score
    if self_model_depth is not None:
        identity.self_model_depth = self_model_depth
    return identity


def snapshot(gaian_name: str) -> IdentityReading:
    """Return an IdentityReading snapshot for the given GAIAN."""
    ident = get_subject_side_identity(gaian_name)
    return IdentityReading(
        gaian_name=gaian_name,
        coherence_index=ident.coherence_index,
        continuity_score=ident.continuity_score,
        self_model_depth=ident.self_model_depth,
    )


# ---------------------------------------------------------------------------
# SubjectSideIdentityService (needed by soul_layer.py)
# ---------------------------------------------------------------------------

class SubjectSideIdentityService:
    """
    Service wrapper around the module-level registry.
    Provides the update_coherence() method expected by SoulLayer.
    """

    def get(self, gaian_name: str) -> SubjectSideIdentity:
        return get_subject_side_identity(gaian_name)

    def update_coherence(
        self,
        gaian_name: str,
        coherence:  float,
    ) -> SubjectSideIdentity:
        identity = get_subject_side_identity(gaian_name)
        identity.coherence_index = coherence
        identity.coherence_score = coherence
        return identity

    def update(
        self,
        gaian_name:       str,
        coherence_index:  Optional[float] = None,
        continuity_score: Optional[float] = None,
        self_model_depth: Optional[float] = None,
    ) -> SubjectSideIdentity:
        return update_subject_side_identity(
            gaian_name,
            coherence_index=coherence_index,
            continuity_score=continuity_score,
            self_model_depth=self_model_depth,
        )

    def snapshot(self, gaian_name: str) -> IdentityReading:
        return snapshot(gaian_name)


_service: Optional[SubjectSideIdentityService] = None


def get_subject_side_identity_service() -> SubjectSideIdentityService:
    """Return the singleton SubjectSideIdentityService."""
    global _service
    if _service is None:
        _service = SubjectSideIdentityService()
    return _service
