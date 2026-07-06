"""
core/primordial/recovery.py
===========================
Recovery Simulation — Phase 2 of the Primordial Engine.

Models what happens when a collapsed entity receives intervention
before re-entering the gauntlet. Intervention can take the form of:

  - REST        — burden reduced, life partially restored
  - WITNESS     — being truly seen; hope and integrity restored
  - LOVE        — unconditional love from outside; love restored
  - TRUTH       — clarity returned; truth and integrity restored
  - ALL         — full intervention (all of the above at once)

The recovery simulation runs the restored entity through the full
gauntlet again and compares the second-run outcome to the first.

Key insight: a collapsed entity that receives intervention does not
re-enter at full strength. It re-enters at whatever the intervention
could restore — still scarred, still carrying some burden — but no
longer at zero.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .entity import PrimordialEntity
from .outcomes import SimulationOutcome
from .simulation import PrimordialSimulation


class InterventionType(str, Enum):
    REST    = "rest"
    WITNESS = "witness"
    LOVE    = "love"
    TRUTH   = "truth"
    ALL     = "all"


@dataclass(slots=True)
class Intervention:
    intervention_type: InterventionType
    intensity: float = 0.5  # 0.0 — 1.0; how strong the intervention is

    def apply(self, entity: PrimordialEntity) -> list[str]:
        """Apply intervention to a collapsed entity. Returns list of changes made."""
        changes: list[str] = []
        t = self.intervention_type
        i = max(0.0, min(self.intensity, 1.0))

        if t in (InterventionType.REST, InterventionType.ALL):
            delta = 0.30 * i
            entity.burden = max(0.0, entity.burden - delta * 2.0)
            entity.life   = min(1.0, entity.life + delta)
            changes.append(f"rest: burden −{delta * 2:.3f}, life +{delta:.3f}")

        if t in (InterventionType.WITNESS, InterventionType.ALL):
            delta = 0.25 * i
            entity.hope      = min(1.0, entity.hope + delta)
            entity.integrity = min(1.0, entity.integrity + delta * 0.8)
            changes.append(f"witness: hope +{delta:.3f}, integrity +{delta * 0.8:.3f}")

        if t in (InterventionType.LOVE, InterventionType.ALL):
            delta = 0.35 * i
            entity.love = min(1.0, entity.love + delta)
            changes.append(f"love: love +{delta:.3f}")

        if t in (InterventionType.TRUTH, InterventionType.ALL):
            delta = 0.20 * i
            entity.truth     = min(1.0, entity.truth + delta)
            entity.integrity = min(1.0, entity.integrity + delta * 0.5)
            changes.append(f"truth: truth +{delta:.3f}, integrity +{delta * 0.5:.3f}")

        entity.clamp()
        return changes


@dataclass(slots=True)
class RecoveryOutcome:
    entity_name:      str
    first_run:        SimulationOutcome
    interventions:    list[str]
    restored_entity:  dict[str, Any]
    second_run:       SimulationOutcome
    recovered:        bool
    order_delta:      float

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_name":     self.entity_name,
            "first_run": {
                "survived":       self.first_run.survived,
                "emergent_order": self.first_run.emergent_order,
                "collapsed_at":   self._collapse_stage(self.first_run),
            },
            "interventions":   self.interventions,
            "restored_entity": self.restored_entity,
            "second_run": {
                "survived":          self.second_run.survived,
                "emergent_order":    self.second_run.emergent_order,
                "retained_constants": self.second_run.retained_constants,
                "surviving_faculties": self.second_run.surviving_faculties,
                "broken_faculties":  self.second_run.broken_faculties,
                "insights_earned":   self._final_insights(self.second_run),
            },
            "recovered":   self.recovered,
            "order_delta": round(self.order_delta, 4),
            "narrative":   self._narrative(),
        }

    @staticmethod
    def _collapse_stage(outcome: SimulationOutcome) -> str | None:
        for result in outcome.stage_results:
            if result.status == "collapsed":
                return result.stage
        return None

    @staticmethod
    def _final_insights(outcome: SimulationOutcome) -> list[str]:
        if not outcome.stage_results:
            return []
        return outcome.stage_results[-1].snapshot.get("insights", [])

    def _narrative(self) -> str:
        if self.recovered and self.order_delta > 0.3:
            return "Full recovery achieved. The second passage carried the scars of the first as earned wisdom."
        if self.recovered and self.order_delta > 0.0:
            return "Partial recovery. Survived the second passage but still carries the weight of the first collapse."
        if self.recovered and self.order_delta <= 0.0:
            return "Technical survival on second run, but emergent order did not improve. The wound runs deep."
        return "Intervention was insufficient. The entity collapsed again. More support is needed before re-entry."


class RecoverySimulation:
    """Run a recovery simulation on a collapsed entity."""

    def __init__(self, stage_sequence: list[str] | None = None):
        self._sim = PrimordialSimulation(stage_sequence)

    def run(
        self,
        entity: PrimordialEntity,
        interventions: list[Intervention] | None = None,
    ) -> RecoveryOutcome:
        from dataclasses import replace

        # ——— First run (baseline — expected to collapse or be fragile) ———
        first_entity = replace(entity)
        first_entity.scars   = list(entity.scars)
        first_entity.insights = list(entity.insights)
        first_entity.history  = []
        first_outcome = self._sim.run(first_entity)

        # ——— Apply interventions to a copy of the entity ———
        restored = replace(entity)
        restored.scars    = list(entity.scars)
        restored.insights = list(entity.insights)
        restored.history  = []

        intervention_log: list[str] = []
        for intervention in (interventions or []):
            changes = intervention.apply(restored)
            intervention_log.extend(
                f"{intervention.intervention_type.value} (intensity={intervention.intensity:.2f}): {c}"
                for c in changes
            )

        restored_snapshot = restored.snapshot()

        # ——— Second run (post-intervention) ———
        second_entity = replace(restored)
        second_entity.scars    = list(restored.scars)
        second_entity.insights = list(restored.insights)
        second_entity.history  = []
        second_outcome = self._sim.run(second_entity)

        recovered    = second_outcome.survived
        order_delta  = second_outcome.emergent_order - first_outcome.emergent_order

        return RecoveryOutcome(
            entity_name=entity.name,
            first_run=first_outcome,
            interventions=intervention_log,
            restored_entity=restored_snapshot,
            second_run=second_outcome,
            recovered=recovered,
            order_delta=order_delta,
        )
