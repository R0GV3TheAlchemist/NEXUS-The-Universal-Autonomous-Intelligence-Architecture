"""
Subject-Side Identity — models the first-person perspectival identity layer.

Provides SubjectSideIdentity dataclass/class and factory accessor.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class IdentityStability(str, Enum):
    UNSTABLE = "unstable"
    FRAGILE = "fragile"
    STABLE = "stable"
    COHERENT = "coherent"
    INTEGRATED = "integrated"


@dataclass
class SubjectSideIdentity:
    """First-person perspectival identity record for a GAIA user."""

    identity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    name: str = ""
    stability: IdentityStability = IdentityStability.FRAGILE
    core_values: List[str] = field(default_factory=list)
    narrative: str = ""
    shadow_aspects: List[str] = field(default_factory=list)
    coherence_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "identity_id": self.identity_id,
            "user_id": self.user_id,
            "name": self.name,
            "stability": self.stability.value,
            "core_values": self.core_values,
            "narrative": self.narrative,
            "shadow_aspects": self.shadow_aspects,
            "coherence_score": self.coherence_score,
            "metadata": self.metadata,
        }

    def update_stability(self) -> None:
        """Recalculate stability tier from coherence score."""
        score = self.coherence_score
        if score < 0.2:
            self.stability = IdentityStability.UNSTABLE
        elif score < 0.4:
            self.stability = IdentityStability.FRAGILE
        elif score < 0.6:
            self.stability = IdentityStability.STABLE
        elif score < 0.8:
            self.stability = IdentityStability.COHERENT
        else:
            self.stability = IdentityStability.INTEGRATED


class SubjectSideIdentityService:
    """Manages subject-side identity records."""

    def __init__(self) -> None:
        self._identities: Dict[str, SubjectSideIdentity] = {}
        log.info("SubjectSideIdentityService initialised")

    def get_or_create(self, user_id: str) -> SubjectSideIdentity:
        if user_id not in self._identities:
            self._identities[user_id] = SubjectSideIdentity(user_id=user_id)
        return self._identities[user_id]

    def update_coherence(self, user_id: str, score: float) -> SubjectSideIdentity:
        ident = self.get_or_create(user_id)
        ident.coherence_score = max(0.0, min(1.0, score))
        ident.update_stability()
        return ident

    def reset(self) -> None:
        self._identities.clear()


_service: Optional[SubjectSideIdentityService] = None


def get_subject_side_identity_service() -> SubjectSideIdentityService:
    global _service
    if _service is None:
        _service = SubjectSideIdentityService()
    return _service
