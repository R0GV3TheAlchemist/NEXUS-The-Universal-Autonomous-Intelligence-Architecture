"""GAIA Alchemical State Machine — Canon C03 §3, C33.

Every entity moves through the four alchemical stages:
  NIGREDO → ALBEDO → CITRINITAS → RUBEDO

Forward skipping is a constitutional violation.
Regression (reverse transition) is allowed but must be explicitly invoked.
The state machine is the guardian of alchemical integrity across all entities.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .entities import AlchemicalStage, Entity


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class StateTransitionError(Exception):
    """Raised when an illegal alchemical state transition is attempted."""
    pass


# ---------------------------------------------------------------------------
# State Machine
# ---------------------------------------------------------------------------

# Canonical forward order — C33: the Magnum Opus stages in sequence
_STAGE_ORDER: list[AlchemicalStage] = [
    AlchemicalStage.NIGREDO,
    AlchemicalStage.CITRINITAS,
    AlchemicalStage.ALBEDO,
    AlchemicalStage.RUBEDO,
]

# Correct forward-only order per C33
_FORWARD_ORDER: list[AlchemicalStage] = [
    AlchemicalStage.NIGREDO,
    AlchemicalStage.ALBEDO,
    AlchemicalStage.CITRINITAS,
    AlchemicalStage.RUBEDO,
]

# Valid forward transitions (no skipping)
_VALID_FORWARD: dict[AlchemicalStage, AlchemicalStage] = {
    AlchemicalStage.NIGREDO: AlchemicalStage.ALBEDO,
    AlchemicalStage.ALBEDO: AlchemicalStage.CITRINITAS,
    AlchemicalStage.CITRINITAS: AlchemicalStage.RUBEDO,
}

# Valid reverse transitions (regression — allowed but logged)
_VALID_REVERSE: dict[AlchemicalStage, AlchemicalStage] = {
    AlchemicalStage.ALBEDO: AlchemicalStage.NIGREDO,
    AlchemicalStage.CITRINITAS: AlchemicalStage.ALBEDO,
    AlchemicalStage.RUBEDO: AlchemicalStage.CITRINITAS,
}


class AlchemicalStateMachine:
    """Guards and executes alchemical stage transitions for any Entity.

    This is the single source of truth for what stage transitions are
    permitted. Enforces: no stage-skipping forward, logs all regressions,
    and raises StateTransitionError on illegal attempts.
    """

    def __init__(self) -> None:
        # transition_log: entity_id → list of (from, to, timestamp, is_regression)
        self._transition_log: dict[
            str, list[tuple[AlchemicalStage, AlchemicalStage, datetime, bool]]
        ] = {}

    # ------------------------------------------------------------------
    # Core Transition
    # ------------------------------------------------------------------

    def advance(self, entity: Entity) -> AlchemicalStage:
        """Advance entity one stage forward. Raises StateTransitionError if at RUBEDO."""
        current = entity.state
        next_stage = _VALID_FORWARD.get(current)
        if next_stage is None:
            raise StateTransitionError(
                f"Entity {entity.id[:8]} is already at RUBEDO — "
                f"the Magnum Opus is complete. No further advancement."
            )
        return self._apply_transition(entity, next_stage, is_regression=False)

    def regress(self, entity: Entity) -> AlchemicalStage:
        """Regress entity one stage backward. Allowed but logged as regression."""
        current = entity.state
        prev_stage = _VALID_REVERSE.get(current)
        if prev_stage is None:
            raise StateTransitionError(
                f"Entity {entity.id[:8]} is at NIGREDO — "
                f"cannot regress further. This is the prima materia."
            )
        return self._apply_transition(entity, prev_stage, is_regression=True)

    def transition_to(
        self, entity: Entity, target: AlchemicalStage, force: bool = False
    ) -> AlchemicalStage:
        """Transition entity to a specific stage.

        Args:
            entity: The entity to transition.
            target: The target AlchemicalStage.
            force: If True, allows regression without the explicit regress() call.
                   Still logs regression. Does NOT allow stage-skipping forward.

        Raises:
            StateTransitionError: If the transition skips stages forward.
        """
        current = entity.state
        if current == target:
            return current

        current_idx = _FORWARD_ORDER.index(current)
        target_idx = _FORWARD_ORDER.index(target)

        if target_idx > current_idx + 1:
            skipped = _FORWARD_ORDER[current_idx + 1 : target_idx]
            raise StateTransitionError(
                f"Illegal stage skip for entity {entity.id[:8]}: "
                f"{current.value} → {target.value} skips {[s.value for s in skipped]}. "
                f"The Magnum Opus cannot be rushed."
            )

        is_regression = target_idx < current_idx
        return self._apply_transition(entity, target, is_regression=is_regression)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _apply_transition(
        self, entity: Entity, target: AlchemicalStage, is_regression: bool
    ) -> AlchemicalStage:
        from_stage = entity.state
        entity.state = target
        entity.touch()
        self._transition_log.setdefault(entity.id, []).append(
            (from_stage, target, datetime.now(timezone.utc), is_regression)
        )
        return target

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_history(
        self, entity_id: str
    ) -> list[tuple[AlchemicalStage, AlchemicalStage, datetime, bool]]:
        """Return full transition history for an entity. [(from, to, at, is_regression)]"""
        return list(self._transition_log.get(entity_id, []))

    def regression_count(self, entity_id: str) -> int:
        """Number of regression events for an entity."""
        return sum(1 for _, _, _, is_reg in self.get_history(entity_id) if is_reg)

    def stage_index(self, stage: AlchemicalStage) -> int:
        """Numeric position of a stage in the forward order (0=NIGREDO, 3=RUBEDO)."""
        return _FORWARD_ORDER.index(stage)

    def next_stage(self, current: AlchemicalStage) -> Optional[AlchemicalStage]:
        """Return the next stage or None if already at RUBEDO."""
        return _VALID_FORWARD.get(current)

    def previous_stage(self, current: AlchemicalStage) -> Optional[AlchemicalStage]:
        """Return the previous stage or None if already at NIGREDO."""
        return _VALID_REVERSE.get(current)
