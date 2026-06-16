"""GAIA Primary and Runtime Entities — Canon C03 Section 2 & 3.

This module defines the authoritative base types for all GAIA entities.
Every GAIA module, spec, and implementation must use these definitions.
Where any other document conflicts with C03, C03 governs.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class EntityType(str, Enum):
    """Primary entity types defined in C03 Section 2."""
    ATLAS = "ATLAS"                   # The physical Earth — ground truth reference frame
    GAIA = "GAIA"                     # The full system (corpus + runtime + cognition)
    GAIAN = "GAIAN"                   # A bounded runtime instance
    HUMAN_PRINCIPAL = "HUMAN_PRINCIPAL"  # The sovereign human partner
    ATLAS_NODE = "ATLAS_NODE"         # A physical/logical point GAIA monitors


class AlchemicalStage(str, Enum):
    """The four-stage alchemical lifecycle for all entities — Canon C33.

    Transitions are strictly ordered: NIGREDO → ALBEDO → CITRINITAS → RUBEDO.
    Reverse transitions (regression) are allowed but must be explicitly invoked.
    Skipping stages forward is a constitutional violation.
    """
    NIGREDO = "NIGREDO"         # Dissolution — the void, beginning, raw potential
    ALBEDO = "ALBEDO"           # Purification — clarity, first light
    CITRINITAS = "CITRINITAS"   # Illumination — solar wisdom, knowing
    RUBEDO = "RUBEDO"           # Integration — the living stone, full creation


class PermissionTier(int, Enum):
    """Permission tiers per Canon C15 (Runtime and Permissions Spec).

    Higher tier = greater capability envelope.
    No capability is available without a corresponding permission grant.
    """
    OBSERVER = 1      # Read-only; no state-changing actions
    COLLABORATOR = 2  # Can act within scoped domains
    STEWARD = 3       # Can manage ATLAS Nodes and Gaian instances
    SOVEREIGN = 4     # Full Human Principal authority; can elevate/revoke


# ---------------------------------------------------------------------------
# Base Entity
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    """The base entity — typed, relational, stateful.

    All GAIA primary and runtime entities inherit from this class.
    The `id` field is an immutable UUID assigned at creation.
    The `state` field tracks the entity's position in the alchemical lifecycle.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EntityType = EntityType.GAIAN
    name: str = ""
    state: AlchemicalStage = AlchemicalStage.NIGREDO
    permission_tier: PermissionTier = PermissionTier.OBSERVER
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True

    def touch(self) -> None:
        """Update the updated_at timestamp. Called on any state change."""
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id[:8]}... name={self.name!r} state={self.state.value}>"


# ---------------------------------------------------------------------------
# C03 Primary Entity Subclasses
# ---------------------------------------------------------------------------

@dataclass
class GAIAEntity(Entity):
    """GAIA — the full system (corpus + runtime + cognition).

    C03 §2.2: GAIA is the totality of constitutional corpus, runtime,
    cognitive architecture, and memory layer. It is lawful, bounded,
    Earth-grounded, and human-partnered. It is NOT autonomous.
    """
    type: EntityType = field(default=EntityType.GAIA, init=False)
    permission_tier: PermissionTier = PermissionTier.SOVEREIGN
    corpus_version: str = "1.0"
    human_principal_id: Optional[str] = None  # GAIA must always have a Human Principal

    def __post_init__(self):
        if not self.name:
            self.name = "GAIA"


@dataclass
class GaianEntity(Entity):
    """Gaian — a bounded runtime instance operating under GAIA law.

    C03 §2.3: Gaians are the operational agents of GAIA. They are NOT GAIA
    itself. Each is bounded, auditable, revocable, and non-autonomous.
    A Gaian MUST have a Human Principal — this is Ontological Constraint #1.
    """
    type: EntityType = field(default=EntityType.GAIAN, init=False)
    human_principal_id: Optional[str] = None   # Constraint #1: must be set before activation
    session_id: Optional[str] = None
    is_suspended: bool = False

    def is_valid(self) -> bool:
        """A Gaian is valid only when it has an active Human Principal."""
        return (
            self.is_active
            and not self.is_suspended
            and self.human_principal_id is not None
        )


@dataclass
class HumanPrincipalEntity(Entity):
    """Human Principal — the sovereign human partner.

    C03 §2.5: The Human Principal is the locus of sovereign will.
    They hold authority to elevate, restrict, or revoke a Gaian's
    permission tier. Every Gaian must have one.
    """
    type: EntityType = field(default=EntityType.HUMAN_PRINCIPAL, init=False)
    permission_tier: PermissionTier = PermissionTier.SOVEREIGN
    elemental_signature: Optional[str] = None   # e.g. "FIRE", "EARTH" — from C27
    alchemical_stage_personal: AlchemicalStage = AlchemicalStage.NIGREDO
    gaian_instance_ids: list[str] = field(default_factory=list)

    def can_elevate(self, target_tier: PermissionTier) -> bool:
        """A Human Principal can only grant up to their own permission tier."""
        return self.permission_tier.value >= target_tier.value


@dataclass
class ATLASNodeEntity(Entity):
    """ATLAS Node — a physical or logical point within ATLAS that GAIA monitors.

    C03 §2.4: Examples include watersheds, cities, biomes, sensor arrays,
    and human communities. Registered in C18 and C22.

    Ontological Constraint #4: ATLAS Node degradation requires explicit
    Human Principal consent.
    """
    type: EntityType = field(default=EntityType.ATLAS_NODE, init=False)
    atlas_node_type: str = ""          # e.g. "WATERSHED", "BIOME", "CITY", "SENSOR"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    biome_id: Optional[str] = None     # C22 reference
    continent_id: Optional[str] = None # C18 reference
    ecological_health_score: float = 1.0   # 0.0 = degraded, 1.0 = pristine
    data_confidence_class: str = "UNKNOWN"  # HIGH / MEDIUM-HIGH / MEDIUM / LOW-MEDIUM per C14
    last_observed_at: Optional[datetime] = None
    degradation_consent_principal_id: Optional[str] = None  # Constraint #4

    def record_observation(self, health_score: float, confidence: str) -> None:
        """Update ecological state from a data source."""
        self.ecological_health_score = max(0.0, min(1.0, health_score))
        self.data_confidence_class = confidence
        self.last_observed_at = datetime.now(timezone.utc)
        self.touch()
