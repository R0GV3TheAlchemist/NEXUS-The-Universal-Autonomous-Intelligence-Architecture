"""
Sentinel Identity — provides archetype seeds and identity verification
for GAIA Sentinel nodes.

Provides:
  - ARCHETYPE_SEEDS  : dict mapping archetype name → seed data
  - SentinelIdentity : dataclass for a sentinel's identity record
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
#  Archetype seed data — used to initialise sentinel identity vectors  #
# ------------------------------------------------------------------ #

ARCHETYPE_SEEDS: Dict[str, Dict[str, Any]] = {
    "guardian": {
        "role": "guardian",
        "attributes": ["protection", "vigilance", "loyalty"],
        "shadow": "authoritarianism",
        "vector": [1.0, 0.0, 0.0, 0.5],
    },
    "sage": {
        "role": "sage",
        "attributes": ["wisdom", "clarity", "discernment"],
        "shadow": "dogmatism",
        "vector": [0.0, 1.0, 0.5, 0.0],
    },
    "healer": {
        "role": "healer",
        "attributes": ["compassion", "restoration", "empathy"],
        "shadow": "codependency",
        "vector": [0.5, 0.0, 1.0, 0.5],
    },
    "trickster": {
        "role": "trickster",
        "attributes": ["creativity", "disruption", "insight"],
        "shadow": "deception",
        "vector": [0.0, 0.5, 0.0, 1.0],
    },
    "sovereign": {
        "role": "sovereign",
        "attributes": ["authority", "responsibility", "vision"],
        "shadow": "tyranny",
        "vector": [0.8, 0.8, 0.2, 0.2],
    },
}


class ArchetypeRole(str, Enum):
    GUARDIAN = "guardian"
    SAGE = "sage"
    HEALER = "healer"
    TRICKSTER = "trickster"
    SOVEREIGN = "sovereign"


@dataclass
class SentinelIdentity:
    """Identity record for a GAIA Sentinel node."""

    sentinel_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    archetype: ArchetypeRole = ArchetypeRole.GUARDIAN
    name: str = ""
    active: bool = True
    trust_score: float = 0.5
    attributes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_archetype(cls, archetype: ArchetypeRole) -> "SentinelIdentity":
        seed = ARCHETYPE_SEEDS.get(archetype.value, {})
        return cls(
            archetype=archetype,
            name=archetype.value.capitalize(),
            attributes=list(seed.get("attributes", [])),
        )

    def to_dict(self) -> dict:
        return {
            "sentinel_id": self.sentinel_id,
            "archetype": self.archetype.value,
            "name": self.name,
            "active": self.active,
            "trust_score": self.trust_score,
            "attributes": self.attributes,
            "metadata": self.metadata,
        }
