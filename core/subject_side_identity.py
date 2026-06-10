"""
core/subject_side_identity.py
Subject-Side Identity — the GAIAN's internal sense of its own identity.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SubjectSideIdentity:
    gaian_name:          str
    coherence_index:     float = 0.5
    continuity_score:    float = 0.5
    self_model_depth:    float = 0.0
    active:              bool  = True

    def to_dict(self) -> dict:
        return {
            "gaian_name":       self.gaian_name,
            "coherence_index":  round(self.coherence_index, 4),
            "continuity_score": round(self.continuity_score, 4),
            "self_model_depth": round(self.self_model_depth, 4),
            "active":           self.active,
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
    if coherence_index  is not None: identity.coherence_index  = coherence_index
    if continuity_score is not None: identity.continuity_score = continuity_score
    if self_model_depth is not None: identity.self_model_depth = self_model_depth
    return identity
