"""
shadow_engine/types.py
Core types and constants for the shadow engine.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

# Canonical activation threshold (Canon §Shadow-3.1)
ACTIVATION_THRESHOLD: float = 0.35

# Delta within which two archetypes are considered co-active
CO_ACTIVE_DELTA: float = 0.05


class ShadowArchetype(str, Enum):
    SABOTEUR     = "saboteur"
    VICTIM       = "victim"
    CONTROLLER   = "controller"
    AVOIDANT     = "avoidant"
    INNER_CRITIC = "inner_critic"
    PROTECTOR    = "protector"
    EXILE        = "exile"


@dataclass
class ShadowRecord:
    """A single shadow activation snapshot."""

    # --- identity ---
    principal_id: str = ""
    archetype: Optional[ShadowArchetype] = None

    # --- engine outputs ---
    archetype_scores: Dict[str, float] = field(default_factory=dict)
    active_archetype: Optional[str] = None
    shadow_intensity: float = 0.0
    integration_progress: float = 0.0
    days_active: int = 0

    # --- legacy scalar fields ---
    intensity: float = 0.0
    trigger_text: str = ""
    integrated: bool = False
    recorded_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    exchange_index: int = 0

    @property
    def is_activated(self) -> bool:
        return self.shadow_intensity >= ACTIVATION_THRESHOLD

    def to_dict(self) -> dict:
        return {
            "principal_id":        self.principal_id,
            "archetype":          self.archetype.value if self.archetype else None,
            "archetype_scores":   self.archetype_scores,
            "active_archetype":   self.active_archetype,
            "shadow_intensity":   round(self.shadow_intensity, 4),
            "integration_progress": round(self.integration_progress, 4),
            "days_active":        self.days_active,
            "intensity":          round(self.intensity, 4),
            "trigger_text":       self.trigger_text,
            "integrated":         self.integrated,
            "recorded_at":        self.recorded_at,
            "exchange_index":     self.exchange_index,
            "is_activated":       self.is_activated,
        }
