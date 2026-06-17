"""
gaia/core/talisman.py

Talisman Object v1 — coherence anchors for GAIA-OS.

Canon anchors:
  - Issue #580 (Talisman Object)
  - Issue #576 (GAIAState)
  - Issue #568 (D6 Meta-Coherence Engine)

Design rules:
  - v1 is DIGITAL ONLY and PERSONAL ONLY.
  - A Talisman modifies GAIAState through bounded deltas.
  - Talismans never bypass D6; they only nudge probes and let D6 decide.

For the Good and the Greater Good.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


class TalismanStatus(str, Enum):
    DORMANT = "dormant"
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass
class TalismanEffect:
    coherence_delta: float = 0.0
    energy_delta: float = 0.0
    stress_delta: float = 0.0
    entropy_delta: float = 0.0

    def to_json(self) -> dict:
        return {
            "coherence_delta": self.coherence_delta,
            "energy_delta": self.energy_delta,
            "stress_delta": self.stress_delta,
            "entropy_delta": self.entropy_delta,
        }


@dataclass
class Talisman:
    name: str
    purpose: str
    created_by: str = "Kyle Steen"
    id: str = field(default_factory=lambda: str(uuid4()))
    status: TalismanStatus = TalismanStatus.DORMANT
    effect: TalismanEffect = field(default_factory=TalismanEffect)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activated_at: datetime | None = None
    notes: str = ""

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "purpose": self.purpose,
            "created_by": self.created_by,
            "status": self.status.value,
            "effect": self.effect.to_json(),
            "created_at": self.created_at.isoformat(),
            "last_activated_at": self.last_activated_at.isoformat() if self.last_activated_at else None,
            "notes": self.notes,
        }
