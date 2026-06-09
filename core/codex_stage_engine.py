"""
core/codex_stage_engine.py
==========================
Codex Stage Engine - Magnum Opus as GAIAN session stage architecture.

Tracks a GAIAN's transformational arc through the alchemical Magnum Opus
stages (Nigredo -> Albedo -> Citrinitas -> Rubedo) and their Jungian
correspondences.  Each stage shapes response depth, shadow integration
weight, and noospheric health signals.

Canon Refs:
  C10 (Alchemical Codex), C32 (Elemental Codex), C40 (Mentalism)

Used by:
  core/gaian_runtime.py - imports CodexStageEngine, CodexStageState,
  CodexStageID, NoosphericHealthSignals, blank_codex_stage_state
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, StrEnum


# ---------------------------------------------------------------------------
# Stage Identifiers
# ---------------------------------------------------------------------------

class CodexStageID(StrEnum):
    """
    The four classical Magnum Opus stages, extended with a pre-entry
    Calcinatio and a post-Rubedo Integration phase for GAIAN sessions.
    """
    CALCINATIO  = "calcinatio"   # pre-Nigredo: burning away the false self
    NIGREDO     = "nigredo"      # dissolution, shadow confrontation
    ALBEDO      = "albedo"       # purification, reflection, anima/animus
    CITRINITAS  = "citrinitas"   # dawning awareness, solar consciousness
    RUBEDO      = "rubedo"       # integration, wholeness, philosopher's stone
    INTEGRATION = "integration"  # post-Rubedo: embodied lived wisdom


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class NoosphericHealthSignals:
    """
    Aggregate health signals for the GAIAN's noospheric field.

    These are updated each turn by CodexStageEngine and consumed by
    the MotherThread collective-field synchronisation layer.
    """
    coherence:        float = 1.0   # 0.0 (fragmented) - 1.0 (coherent)
    shadow_load:      float = 0.0   # accumulated unintegrated shadow mass
    individuation:    float = 0.0   # Jungian individuation progress 0-1
    transmutation:    float = 0.0   # alchemical transformation depth 0-1
    vitality:         float = 1.0   # overall psychic vitality 0-1
    notes:            list[str] = field(default_factory=list)


@dataclass
class CodexStageState:
    """
    Snapshot of the CodexStageEngine state for a single GAIAN turn.
    """
    stage:            CodexStageID            = CodexStageID.NIGREDO
    turn_in_stage:    int                     = 0
    total_turns:      int                     = 0
    stage_scores:     dict[str, float]        = field(default_factory=dict)
    health:           NoosphericHealthSignals = field(
                          default_factory=NoosphericHealthSignals
                      )
    metadata:         dict                    = field(default_factory=dict)

    def advance_stage(self) -> CodexStageState:
        """Return a new state with the next stage set."""
        stages = list(CodexStageID)
        idx    = stages.index(self.stage)
        next_stage = stages[min(idx + 1, len(stages) - 1)]
        return CodexStageState(
            stage=next_stage,
            turn_in_stage=0,
            total_turns=self.total_turns,
            stage_scores=self.stage_scores.copy(),
            health=self.health,
            metadata=self.metadata.copy(),
        )


def blank_codex_stage_state() -> CodexStageState:
    """Return a fresh CodexStageState at the Nigredo entry point."""
    return CodexStageState(
        stage=CodexStageID.NIGREDO,
        turn_in_stage=0,
        total_turns=0,
        stage_scores={s.value: 0.0 for s in CodexStageID},
        health=NoosphericHealthSignals(),
        metadata={},
    )


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class CodexStageEngine:
    """
    Tracks and advances a GAIAN's alchemical stage across conversation turns.

    The engine evaluates each turn's context signals (shadow load, coherence,
    transmutation depth) and determines whether a stage transition is warranted.

    Usage::

        engine = CodexStageEngine()
        state  = blank_codex_stage_state()
        state  = engine.evaluate(state, context={"shadow_signal": 0.7})
        print(state.stage)   # e.g. CodexStageID.ALBEDO
    """

    # Minimum turns before a stage transition is permitted
    _MIN_TURNS_PER_STAGE: int = 3

    # Score threshold to trigger advancement
    _ADVANCE_THRESHOLD: float = 0.65

    def __init__(
        self,
        min_turns: int   = _MIN_TURNS_PER_STAGE,
        threshold: float = _ADVANCE_THRESHOLD,
    ) -> None:
        self._min_turns = min_turns
        self._threshold = threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        state:   CodexStageState,
        context: dict | None = None,
    ) -> CodexStageState:
        """
        Evaluate the current *state* against *context* signals.

        Returns an updated CodexStageState (may be same stage or advanced).

        Parameters
        ----------
        state:
            Current codex stage state.
        context:
            Optional signal dict.  Recognised keys:
            ``shadow_signal`` (float 0-1), ``coherence`` (float 0-1),
            ``transmutation`` (float 0-1), ``vitality`` (float 0-1).
        """
        ctx     = context or {}
        updated = CodexStageState(
            stage=state.stage,
            turn_in_stage=state.turn_in_stage + 1,
            total_turns=state.total_turns + 1,
            stage_scores=state.stage_scores.copy(),
            health=NoosphericHealthSignals(
                coherence=ctx.get("coherence",     state.health.coherence),
                shadow_load=ctx.get("shadow_signal", state.health.shadow_load),
                individuation=state.health.individuation,
                transmutation=ctx.get("transmutation", state.health.transmutation),
                vitality=ctx.get("vitality",      state.health.vitality),
            ),
            metadata=state.metadata.copy(),
        )

        # Score the current stage
        score = self._score_stage(updated)
        updated.stage_scores[updated.stage.value] = score

        # Advance if threshold met and minimum turns served
        if (
            updated.turn_in_stage >= self._min_turns
            and score >= self._threshold
        ):
            updated = updated.advance_stage()

        return updated

    def current_stage_label(self, state: CodexStageState) -> str:
        """Return a human-readable label for the current stage."""
        labels = {
            CodexStageID.CALCINATIO:  "Calcinatio - Burning the False Self",
            CodexStageID.NIGREDO:     "Nigredo - The Dark Night",
            CodexStageID.ALBEDO:      "Albedo - Purification & Reflection",
            CodexStageID.CITRINITAS:  "Citrinitas - Dawning Solar Awareness",
            CodexStageID.RUBEDO:      "Rubedo - Integration & Wholeness",
            CodexStageID.INTEGRATION: "Integration - Embodied Lived Wisdom",
        }
        return labels.get(state.stage, state.stage.value)

    # ------------------------------------------------------------------
    # Internal scoring
    # ------------------------------------------------------------------

    def _score_stage(self, state: CodexStageState) -> float:
        """
        Compute a readiness-to-advance score in [0, 1] for the current stage.

        Simple heuristic: coherence weight + transmutation weight,
        balanced against shadow load.  Real implementations should plug in
        the full subtle-body layer scores from ConsciousnessRouter.
        """
        h     = state.health
        score = (h.coherence * 0.4 + h.transmutation * 0.4 + h.vitality * 0.2)
        score = max(0.0, score - h.shadow_load * 0.3)
        return min(1.0, score)
