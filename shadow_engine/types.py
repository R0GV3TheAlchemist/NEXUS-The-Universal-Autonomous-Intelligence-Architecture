"""
shadow_engine/types.py
Core types and constants for the shadow engine.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

# Canonical activation threshold (Canon §Shadow-3.1)
ACTIVATION_THRESHOLD: float = 0.35


class ShadowArchetype(str, Enum):
    SABOTEUR   = "saboteur"
    VICTIM     = "victim"
    CONTROLLER = "controller"
    AVOIDANT   = "avoidant"
    INNER_CRITIC = "inner_critic"
    PROTECTOR  = "protector"
    EXILE      = "exile"


@dataclass
class ShadowRecord:
    """A single shadow activation event."""
    archetype:       ShadowArchetype
    intensity:       float
    trigger_text:    str = ""
    integrated:      bool = False
    recorded_at:     str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    exchange_index:  int = 0

    @property
    def is_activated(self) -> bool:
        return self.intensity >= ACTIVATION_THRESHOLD

    def to_dict(self) -> dict:
        return {
            "archetype":      self.archetype.value,
            "intensity":      round(self.intensity, 4),
            "trigger_text":   self.trigger_text,
            "integrated":     self.integrated,
            "recorded_at":    self.recorded_at,
            "exchange_index": self.exchange_index,
            "is_activated":   self.is_activated,
        }
