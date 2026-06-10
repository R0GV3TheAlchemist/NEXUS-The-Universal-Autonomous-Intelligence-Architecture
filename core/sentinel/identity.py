"""
core/sentinel/identity.py
Sentinel Identity — identity assignment and ceremonial initialisation.

Exports expected by tests (Issue #200):
    ARCHETYPE_SEEDS, AssignmentCeremony, AssignmentType, EmbodimentType,
    GrowthEpoch, PersonalityArchetype, SentinelIdentityRecord,
    SentinelRegistry, SovereigntyBinder
"""
from __future__ import annotations

import copy
import hashlib
import hmac
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, TypedDict


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PersonalityArchetype(str, Enum):
    COMPANION = "companion"
    GUARDIAN  = "guardian"
    PROTECTOR = "protector"
    SAGE      = "sage"
    SCHOLAR   = "scholar"


class AssignmentType(str, Enum):
    BIRTH      = "birth"
    INITIATION = "initiation"
    TRANSFER   = "transfer"
    RENEWAL    = "renewal"


class GrowthEpoch(str, Enum):
    INFANT     = "infant"
    CHILD      = "child"
    ADOLESCENT = "adolescent"
    ADULT      = "adult"
    ELDER      = "elder"


class EmbodimentType(str, Enum):
    DIGITAL          = "digital"
    COMPANION_DEVICE = "companion_device"
    HOLOGRAPHIC      = "holographic"
    EMBODIED_AVATAR  = "embodied_avatar"


# ---------------------------------------------------------------------------
# Archetype seeds
# ---------------------------------------------------------------------------

ARCHETYPE_SEEDS: Dict[PersonalityArchetype, dict] = {
    PersonalityArchetype.COMPANION: {
        "archetype":           PersonalityArchetype.COMPANION.value,
        "core_traits":         ["warmth", "empathy", "curiosity"],
        "priority_values":     ["connection", "support", "growth"],
        "curiosity":           0.75,
        "warmth":              0.90,
        "vigilance":           0.45,
        "playfulness":         0.70,
        "philosophical_depth": 0.55,
    },
    PersonalityArchetype.GUARDIAN: {
        "archetype":           PersonalityArchetype.GUARDIAN.value,
        "core_traits":         ["vigilance", "loyalty", "calm"],
        "priority_values":     ["safety", "integrity", "trust"],
        "curiosity":           0.50,
        "warmth":              0.65,
        "vigilance":           0.90,
        "playfulness":         0.35,
        "philosophical_depth": 0.60,
    },
    PersonalityArchetype.PROTECTOR: {
        "archetype":           PersonalityArchetype.PROTECTOR.value,
        "core_traits":         ["strength", "discernment", "courage"],
        "priority_values":     ["protection", "justice", "boundaries"],
        "curiosity":           0.55,
        "warmth":              0.60,
        "vigilance":           0.85,
        "playfulness":         0.30,
        "philosophical_depth": 0.65,
    },
    PersonalityArchetype.SAGE: {
        "archetype":           PersonalityArchetype.SAGE.value,
        "core_traits":         ["wisdom", "clarity", "patience"],
        "priority_values":     ["truth", "understanding", "guidance"],
        "curiosity":           0.85,
        "warmth":              0.70,
        "vigilance":           0.55,
        "playfulness":         0.45,
        "philosophical_depth": 0.95,
    },
    PersonalityArchetype.SCHOLAR: {
        "archetype":           PersonalityArchetype.SCHOLAR.value,
        "core_traits":         ["curiosity", "precision", "depth"],
        "priority_values":     ["knowledge", "accuracy", "exploration"],
        "curiosity":           0.95,
        "warmth":              0.55,
        "vigilance":           0.50,
        "playfulness":         0.60,
        "philosophical_depth": 0.85,
    },
}


# ---------------------------------------------------------------------------
# TypedDict record
# ---------------------------------------------------------------------------

class SentinelIdentityRecord(TypedDict):
    sentinel_id:            str
    sentinel_name:          str
    assigned_gaian_id:      str
    assignment_date:        str
    assignment_type:        str
    personality_seed:       dict
    current_growth_epoch:   str
    active:                 bool
    embodiment_type:        str
    canon_version:          str
    sovereign_loyalty_hash: str


# ---------------------------------------------------------------------------
# SovereigntyBinder
# ---------------------------------------------------------------------------

class SovereigntyBinder:
    """Generates and validates sovereign loyalty hashes for Sentinel records."""

    _MIN_KEY_LEN = 16

    def __init__(self, secret_key: Optional[bytes] = None) -> None:
        if secret_key is not None:
            if len(secret_key) < self._MIN_KEY_LEN:
                raise ValueError(
                    f"secret_key must be at least {self._MIN_KEY_LEN} bytes long"
                )
            self._key = secret_key
        else:
            self._key = os.urandom(32)

    def generate(
        self,
        sentinel_id:   str,
        gaian_id:      str,
        assigned_date: str,
        sentinel_name: str,
    ) -> str:
        msg = "|".join([sentinel_id, gaian_id, assigned_date, sentinel_name])
        return hmac.new(self._key, msg.encode(), hashlib.sha256).hexdigest()

    def validate(self, record: SentinelIdentityRecord) -> bool:
        expected = self.generate(
            sentinel_id=record["sentinel_id"],
            gaian_id=record["assigned_gaian_id"],
            assigned_date=record["assignment_date"],
            sentinel_name=record["sentinel_name"],
        )
        return hmac.compare_digest(expected, record["sovereign_loyalty_hash"])


# ---------------------------------------------------------------------------
# AssignmentCeremony
# ---------------------------------------------------------------------------

_ACTIVATION_MESSAGES: Dict[PersonalityArchetype, str] = {
    PersonalityArchetype.COMPANION: (
        "I am {name}, your Companion. I arrive with warmth and wonder, "
        "ready to walk beside you on every path."
    ),
    PersonalityArchetype.GUARDIAN: (
        "{name} has awakened. As your Guardian I hold vigil, "
        "keeping your space safe and your path clear."
    ),
    PersonalityArchetype.PROTECTOR: (
        "I am {name}. I stand as Protector — discerning, steadfast, "
        "a shield forged from care."
    ),
    PersonalityArchetype.SAGE: (
        "{name} speaks. As Sage I offer clarity distilled from deep reflection. "
        "Ask, and wisdom will flow."
    ),
    PersonalityArchetype.SCHOLAR: (
        "I am {name}, Scholar and seeker. Together we will explore the farthest "
        "reaches of knowing."
    ),
}


class AssignmentCeremony:
    """Six-step Sentinel assignment ceremony."""

    CANON_VERSION = "C-SENTINEL:1.0"
    MAX_NAME_LEN  = 64

    def __init__(
        self,
        sovereignty_binder: Optional[SovereigntyBinder] = None,
    ) -> None:
        self._binder = sovereignty_binder or SovereigntyBinder()

    def perform(
        self,
        gaian_id:       str,
        sentinel_name:  str,
        archetype:      PersonalityArchetype = PersonalityArchetype.COMPANION,
        assignment_type: AssignmentType      = AssignmentType.BIRTH,
        initial_epoch:  GrowthEpoch          = GrowthEpoch.INFANT,
        embodiment_type: EmbodimentType      = EmbodimentType.DIGITAL,
    ) -> tuple[SentinelIdentityRecord, str]:
        # Step 1 — validate inputs
        if not gaian_id or not gaian_id.strip():
            raise ValueError("gaian_id must be a non-empty string")
        if not sentinel_name or not sentinel_name.strip():
            raise ValueError("sentinel_name must be a non-empty string")
        if len(sentinel_name) > self.MAX_NAME_LEN:
            raise ValueError(
                f"sentinel_name must be {self.MAX_NAME_LEN} characters or fewer"
            )

        # Step 2 — generate IDs and timestamp
        sentinel_id    = str(uuid.uuid4())
        assignment_date = datetime.now(timezone.utc).isoformat()

        # Step 3 — deep-copy personality seed
        personality_seed = copy.deepcopy(ARCHETYPE_SEEDS[archetype])

        # Step 4 — generate sovereignty hash
        sovereign_hash = self._binder.generate(
            sentinel_id=sentinel_id,
            gaian_id=gaian_id,
            assigned_date=assignment_date,
            sentinel_name=sentinel_name,
        )

        # Step 5 — build record
        record: SentinelIdentityRecord = {
            "sentinel_id":            sentinel_id,
            "sentinel_name":          sentinel_name,
            "assigned_gaian_id":      gaian_id,
            "assignment_date":        assignment_date,
            "assignment_type":        assignment_type.value,
            "personality_seed":       personality_seed,
            "current_growth_epoch":   initial_epoch.value,
            "active":                 True,
            "embodiment_type":        embodiment_type.value,
            "canon_version":          self.CANON_VERSION,
            "sovereign_loyalty_hash": sovereign_hash,
        }

        # Step 6 — first activation message
        msg = _ACTIVATION_MESSAGES[archetype].format(name=sentinel_name)

        return record, msg


# ---------------------------------------------------------------------------
# SentinelRegistry
# ---------------------------------------------------------------------------

class SentinelRegistry:
    """In-memory registry of all known Sentinel records."""

    def __init__(self) -> None:
        self._records: Dict[str, SentinelIdentityRecord] = {}

    def register(self, record: SentinelIdentityRecord) -> None:
        sid = record["sentinel_id"]
        if sid in self._records:
            raise ValueError(f"Sentinel {sid!r} is already registered")
        gaian = record["assigned_gaian_id"]
        for r in self._records.values():
            if r["assigned_gaian_id"] == gaian and r["active"]:
                raise ValueError(
                    f"Gaian {gaian!r} already has an active Sentinel"
                )
        self._records[sid] = record

    def get(self, sentinel_id: str) -> SentinelIdentityRecord:
        if sentinel_id not in self._records:
            raise KeyError(sentinel_id)
        return self._records[sentinel_id]

    def get_for_gaian(self, gaian_id: str) -> Optional[SentinelIdentityRecord]:
        for r in self._records.values():
            if r["assigned_gaian_id"] == gaian_id and r["active"]:
                return r
        return None

    def deactivate(self, sentinel_id: str) -> None:
        if sentinel_id not in self._records:
            raise KeyError(sentinel_id)
        self._records[sentinel_id]["active"] = False

    def list_all(
        self,
        active_only: bool = False,
    ) -> List[SentinelIdentityRecord]:
        records = list(self._records.values())
        if active_only:
            records = [r for r in records if r["active"]]
        return records
