"""
core/subject_side_identity.py
Subject-Side Identity — the GAIAN's internal sense of its own identity.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class SubjectSideIdentity:
    gaian_name:       str
    coherence_index:  float = 0.5
    continuity_score: float = 0.5
    self_model_depth: float = 0.0
    active:           bool  = True

    def to_dict(self) -> dict:
        return {
            "gaian_name":       self.gaian_name,
            "coherence_index":  round(self.coherence_index, 4),
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


_registry: dict[str, SubjectSideIdentity] = {}


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
