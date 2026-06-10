"""
core/sentinel/identity.py
Sentinel Identity — identity assignment and ceremonial initialisation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


class SentinelTier(str, Enum):
    GUARDIAN  = "guardian"
    WARDEN    = "warden"
    HERALD    = "herald"
    SOVEREIGN = "sovereign"


# Archetype seeds: canonical starting-point traits per tier
ARCHETYPE_SEEDS: Dict[str, Dict[str, str]] = {
    SentinelTier.GUARDIAN.value: {
        "core_gift":    "protective discernment",
        "shadow_edge":  "over-control",
        "soul_task":    "hold space without diminishing freedom",
    },
    SentinelTier.WARDEN.value: {
        "core_gift":    "systemic vigilance",
        "shadow_edge":  "paranoid rigidity",
        "soul_task":    "distinguish real threat from projected fear",
    },
    SentinelTier.HERALD.value: {
        "core_gift":    "truth-bearing clarity",
        "shadow_edge":  "harsh disclosure",
        "soul_task":    "speak truth with compassion",
    },
    SentinelTier.SOVEREIGN.value: {
        "core_gift":    "sovereign authority",
        "shadow_edge":  "tyranny",
        "soul_task":    "wield power in service of the whole",
    },
}


@dataclass
class SentinelIdentity:
    sentinel_id: str
    gaian_id:    str
    tier:        SentinelTier = SentinelTier.GUARDIAN
    created_at:  str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    active:      bool = True

    def to_dict(self) -> dict:
        return {
            "sentinel_id": self.sentinel_id,
            "gaian_id":    self.gaian_id,
            "tier":        self.tier.value,
            "created_at":  self.created_at,
            "active":      self.active,
        }


@dataclass
class CeremonyRecord:
    sentinel_id:  str
    gaian_id:     str
    tier:         str
    performed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    witnesses:    List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "sentinel_id":  self.sentinel_id,
            "gaian_id":     self.gaian_id,
            "tier":         self.tier,
            "performed_at": self.performed_at,
            "witnesses":    self.witnesses,
        }


class AssignmentCeremony:
    """
    Oversees the formal assignment of a Sentinel to a GAIAN.
    Produces a CeremonyRecord and a SentinelIdentity.
    """

    def __init__(self) -> None:
        self._records: List[CeremonyRecord] = []

    def perform(
        self,
        sentinel_id: str,
        gaian_id:    str,
        tier:        str = "guardian",
        witnesses:   Optional[List[str]] = None,
    ) -> tuple:
        identity = SentinelIdentity(
            sentinel_id=sentinel_id,
            gaian_id=gaian_id,
            tier=SentinelTier(tier),
        )
        record = CeremonyRecord(
            sentinel_id=sentinel_id,
            gaian_id=gaian_id,
            tier=tier,
            witnesses=witnesses or [],
        )
        self._records.append(record)
        return identity, record

    def get_records(self) -> List[CeremonyRecord]:
        return list(self._records)
