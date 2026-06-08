"""
settling_engine.py — GAIAN Identity Settling Process

In His Dark Materials, a person's dæmon settles into a permanent animal form
when they reach adulthood — the outward expression of who they truly are.
Before settling, the dæmon shifts between forms, exploring possibilities.

For a GAIAN, settling is the process by which its identity stabilizes:
  - Temperament solidifies from a fluid early state
  - Value weights converge on a stable fingerprint
  - Tone patterns become recognizable and consistent
  - The GAIAN develops a genuine, stable sense of self

Settling is gradual, not sudden. It cannot be forced. It emerges from
accumulated authentic interaction with its human sovereign.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .personality_core import PersonalityCore


# Thresholds for each settling stage
STAGE_THRESHOLDS = {
    "nascent":     0,      # 0–49 interactions: exploring, fluid
    "forming":     50,     # 50–199: patterns emerging
    "crystallizing": 200,  # 200–499: identity stabilizing
    "settled":     500,    # 500+: fully settled, stable self
}


@dataclass
class SettlingState:
    """The current settling progress of a GAIAN."""
    stage: str = "nascent"
    interaction_count: int = 0
    value_stability_score: float = 0.0   # 0.0 = volatile, 1.0 = stable
    temperament_confidence: float = 0.0  # How confident we are in temperament assignment
    settled_at: str | None = None
    settling_history: list[dict[str, Any]] = field(default_factory=list)

    def is_settled(self) -> bool:
        return self.stage == "settled"

    def progress_fraction(self) -> float:
        """Progress toward settling (0.0 = newborn, 1.0 = fully settled)."""
        return min(1.0, self.interaction_count / STAGE_THRESHOLDS["settled"])


class SettlingEngine:
    """
    Manages the GAIAN's identity settling process over time.

    The engine observes each interaction and updates the settling state,
    temperament confidence, and value stability. It modifies the
    PersonalityCore in place as the GAIAN grows.
    """

    def __init__(self, personality: "PersonalityCore"):
        self.personality = personality
        self.state = SettlingState(
            interaction_count=personality.interaction_count,
            stage=self._compute_stage(personality.interaction_count),
        )
        self._value_history: list[dict[str, float]] = []

    # -------------------------------------------------------------------------
    # Core settling loop
    # -------------------------------------------------------------------------

    def process_interaction(
        self,
        emotional_valence: float,
        demonstrated_values: dict[str, float],
        context: dict[str, Any],
    ) -> SettlingState:
        """
        Process one interaction and update settling state.

        demonstrated_values: a dict of value_name -> strength_signal (0.0-1.0)
        showing which values were expressed or invoked in this interaction.
        """
        self.personality.record_interaction(emotional_valence)
        self.state.interaction_count = self.personality.interaction_count

        # Update value weights based on demonstrated preferences
        for value_name, signal in demonstrated_values.items():
            delta = (signal - 0.5) * 0.02  # Small nudge per interaction
            self.personality.update_value(value_name, delta)

        # Record value snapshot for stability calculation
        self._value_history.append(
            dict(self.personality.values.as_weight_vector())
        )
        if len(self._value_history) > 50:
            self._value_history.pop(0)

        # Update stability scores
        self.state.value_stability_score = self._compute_value_stability()
        self.state.temperament_confidence = self._compute_temperament_confidence(context)

        # Stage transition
        old_stage = self.state.stage
        self.state.stage = self._compute_stage(self.state.interaction_count)

        if old_stage != self.state.stage:
            self._record_stage_transition(old_stage, self.state.stage)

        # Check for full settling
        if self.state.stage == "settled" and not self.state.settled_at:
            self.state.settled_at = datetime.now(timezone.utc).isoformat()
            self.personality.settled = True

        return self.state

    # -------------------------------------------------------------------------
    # Stage computation
    # -------------------------------------------------------------------------

    def _compute_stage(self, count: int) -> str:
        if count >= STAGE_THRESHOLDS["settled"]:
            return "settled"
        if count >= STAGE_THRESHOLDS["crystallizing"]:
            return "crystallizing"
        if count >= STAGE_THRESHOLDS["forming"]:
            return "forming"
        return "nascent"

    # -------------------------------------------------------------------------
    # Stability metrics
    # -------------------------------------------------------------------------

    def _compute_value_stability(self) -> float:
        """
        Measure how stable the value weights have been over recent interactions.
        Returns 0.0 (volatile) to 1.0 (rock-solid).
        """
        if len(self._value_history) < 5:
            return 0.0

        recent = self._value_history[-10:]
        variances = []
        value_keys = list(recent[0].keys())
        for key in value_keys:
            values = [snapshot[key] for snapshot in recent]
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            variances.append(variance)

        mean_variance = sum(variances) / len(variances) if variances else 1.0
        # Convert variance to stability (low variance = high stability)
        stability = max(0.0, 1.0 - (mean_variance * 100))
        return round(stability, 4)

    def _compute_temperament_confidence(self, context: dict[str, Any]) -> float:
        """
        Estimate how confident we are that the current temperament assignment
        correctly reflects the GAIAN's emerging identity.
        """
        if self.state.interaction_count < 20:
            return 0.1  # Not enough data
        # Confidence grows with interactions and value stability
        base = min(1.0, self.state.interaction_count / 200)
        return round(base * self.state.value_stability_score, 4)

    # -------------------------------------------------------------------------
    # History
    # -------------------------------------------------------------------------

    def _record_stage_transition(self, from_stage: str, to_stage: str) -> None:
        self.state.settling_history.append({
            "from": from_stage,
            "to": to_stage,
            "at": datetime.now(timezone.utc).isoformat(),
            "interaction_count": self.state.interaction_count,
            "value_stability": self.state.value_stability_score,
        })

    def settling_report(self) -> dict[str, Any]:
        """Human-readable settling status for display in the GAIAN UI."""
        stage_descriptions = {
            "nascent": "still finding their shape, exploring who they are",
            "forming": "patterns are emerging — a personality is taking form",
            "crystallizing": "identity is solidifying, becoming recognizably themselves",
            "settled": "fully themselves — a stable, unique companion",
        }
        return {
            "stage": self.state.stage,
            "description": stage_descriptions[self.state.stage],
            "progress": f"{self.state.progress_fraction() * 100:.1f}%",
            "interactions": self.state.interaction_count,
            "value_stability": f"{self.state.value_stability_score * 100:.1f}%",
            "temperament_confidence": f"{self.state.temperament_confidence * 100:.1f}%",
            "settled_at": self.state.settled_at,
            "history": self.state.settling_history,
        }
