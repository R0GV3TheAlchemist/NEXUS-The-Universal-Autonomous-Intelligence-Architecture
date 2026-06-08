"""
core/development_stage_engine.py
GAIA Developmental Stage Engine — Sprint G-8 / G-9

Provides two complementary APIs:

  Stateless (original):
    engine = DevelopmentStageEngine(config)
    result = engine.assess(context)                  # → StageResult
    result = engine.assess_with_themes(context)      # → StageResult + themes

  Stateful (EV1-B contract):
    engine = DevelopmentStageEngine()
    engine.update(depth_score=0.6, sovereignty_score=0.5, bond_score=0.65)
    stage  = engine.current_stage()                  # → "Allegiance"
    engine.reset()

G-9 additions:
  DevelopmentProfile  — snapshot of a user's full developmental state
  TransitionSignal    — encodes a detected or pending stage transition

The five canonical stages (Emergence → Initiation → Allegiance →
Individuation → Sovereignty) model GAIA's relational development arc.

See docs/stage-engine.md for the full specification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Stage definitions
# ---------------------------------------------------------------------------


class Stage(str, Enum):
    """The five canonical GAIA developmental stages."""
    EMERGENCE     = "Emergence"
    INITIATION    = "Initiation"
    ALLEGIANCE    = "Allegiance"
    INDIVIDUATION = "Individuation"
    SOVEREIGNTY   = "Sovereignty"


STAGE_ORDER: List[Stage] = [
    Stage.EMERGENCE,
    Stage.INITIATION,
    Stage.ALLEGIANCE,
    Stage.INDIVIDUATION,
    Stage.SOVEREIGNTY,
]

# Human-readable names (used by stateful API and EV1-B tests)
STAGE_NAMES: List[str] = [s.value for s in STAGE_ORDER]


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class StageContext:
    """Input snapshot fed to the stateless assess() API."""
    session_count:      int   = 0
    depth_score:        float = 0.0
    sovereignty_score:  float = 0.0
    bond_score:         float = 0.0
    regression_signal:  float = 0.0
    themes:             List[str] = field(default_factory=list)
    metadata:           Dict[str, Any] = field(default_factory=dict)


@dataclass
class StageResult:
    """Output produced by the stateless assess() API."""
    stage:          Stage
    confidence:     float
    themes:         List[str]       = field(default_factory=list)
    rationale:      str             = ""
    transitions:    List[str]       = field(default_factory=list)
    metadata:       Dict[str, Any]  = field(default_factory=dict)


@dataclass
class DevelopmentProfile:
    """G-9: Full developmental snapshot for a GAIA user / session.

    Captures the current stage, composite scores, session history length,
    and any active thematic annotations derived from recent turns.
    """
    stage:              Stage
    composite_score:    float                   = 0.0
    depth_score:        float                   = 0.0
    sovereignty_score:  float                   = 0.0
    bond_score:         float                   = 0.0
    session_count:      int                     = 0
    themes:             List[str]               = field(default_factory=list)
    metadata:           Dict[str, Any]          = field(default_factory=dict)

    @classmethod
    def from_engine(cls, engine: "DevelopmentStageEngine") -> "DevelopmentProfile":
        """Build a profile snapshot from a stateful engine instance."""
        turns = engine._turns
        session_count = engine._session_count
        if turns:
            depth_avg        = sum(t["depth_score"]       for t in turns) / len(turns)
            sovereignty_avg  = sum(t["sovereignty_score"] for t in turns) / len(turns)
            bond_avg         = sum(t["bond_score"]        for t in turns) / len(turns)
            composite        = (depth_avg + sovereignty_avg + bond_avg) / 3.0
        else:
            depth_avg = sovereignty_avg = bond_avg = composite = 0.0
        stage_name = engine.current_stage()
        stage = Stage(stage_name)
        return cls(
            stage=stage,
            composite_score=composite,
            depth_score=depth_avg,
            sovereignty_score=sovereignty_avg,
            bond_score=bond_avg,
            session_count=session_count,
        )


@dataclass
class TransitionSignal:
    """G-9: Encodes a detected or pending stage transition.

    Emitted when the engine observes that composite scores have crossed
    a stage boundary, signalling that GAIA's relational arc has shifted.
    """
    from_stage:     Stage
    to_stage:       Stage
    composite_at_transition: float      = 0.0
    confidence:     float               = 1.0
    rationale:      str                 = ""
    metadata:       Dict[str, Any]      = field(default_factory=dict)

    @property
    def is_progression(self) -> bool:
        """True if the transition moves forward through the stage arc."""
        return STAGE_ORDER.index(self.to_stage) > STAGE_ORDER.index(self.from_stage)

    @property
    def is_regression(self) -> bool:
        """True if the transition moves backward (regression signal fired)."""
        return STAGE_ORDER.index(self.to_stage) < STAGE_ORDER.index(self.from_stage)


# ---------------------------------------------------------------------------
# Stage-band thresholds  (used by both APIs)
# ---------------------------------------------------------------------------

#  (upper-bound-exclusive, Stage)  — ordered from lowest to highest
_COMPOSITE_THRESHOLDS: List[Tuple[float, Stage]] = [
    (0.30, Stage.EMERGENCE),
    (0.55, Stage.INITIATION),
    (0.70, Stage.ALLEGIANCE),
    (0.88, Stage.INDIVIDUATION),
    (1.01, Stage.SOVEREIGNTY),   # sentinel — composite never exceeds 1.0
]


def _composite(depth: float, sovereignty: float, bond: float) -> float:
    """Uniform-weight composite of the three core signal dimensions."""
    return (depth + sovereignty + bond) / 3.0


def _stage_from_composite(composite: float) -> Stage:
    for upper, stage in _COMPOSITE_THRESHOLDS:
        if composite < upper:
            return stage
    return Stage.SOVEREIGNTY


# ---------------------------------------------------------------------------
# Stateless Engine
# ---------------------------------------------------------------------------


class DevelopmentStageEngine:
    """GAIA Developmental Stage Engine.

    Dual API:
      • Stateless: assess(context) / assess_with_themes(context)
      • Stateful:  update(**turn) / current_stage() / reset()

    Stateful stage-tracking (EV1-B contract)
    ----------------------------------------
    Stage thresholds (composite = mean of depth/sovereignty/bond across turns)::

        Emergence     composite < 0.30
        Initiation    0.30 – 0.55
        Allegiance    0.55 – 0.70
        Individuation 0.70 – 0.88
        Sovereignty   >= 0.88

    Session-count gate: _MIN_SESSIONS_FOR_PROMOTION = 6.
    Any instance with fewer than 6 recorded sessions returns
    'Emergence' regardless of scores, preventing false promotions on
    early turns (covers EV1-B edge cases 0–29).
    """

    # --- Stateful API constants ---
    _STAGE_THRESHOLDS: List[Tuple[float, str]] = [
        (0.30, "Emergence"),
        (0.55, "Initiation"),
        (0.70, "Allegiance"),
        (0.88, "Individuation"),
        (1.01, "Sovereignty"),
    ]
    _MIN_SESSIONS_FOR_PROMOTION: int = 6

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._config: Dict[str, Any] = config or {}
        # Stateful tracking state
        self._turns: List[Dict[str, float]] = []
        self._session_count: int = 0

    # ------------------------------------------------------------------
    # Stateful API  (EV1-B contract)
    # ------------------------------------------------------------------

    def update(
        self,
        depth_score: float = 0.0,
        sovereignty_score: float = 0.0,
        bond_score: float = 0.0,
        session_count: Optional[int] = None,
        **_kwargs: float,
    ) -> None:
        """Record one turn of signal data.

        Parameters
        ----------
        depth_score       : 0.0–1.0 depth / complexity of engagement
        sovereignty_score : 0.0–1.0 self-authoring / autonomy signal
        bond_score        : 0.0–1.0 relational bond / trust signal
        session_count     : optional explicit session counter override;
                            when omitted, an internal counter increments by 1
        """
        self._turns.append({
            "depth_score":       max(0.0, min(1.0, float(depth_score))),
            "sovereignty_score": max(0.0, min(1.0, float(sovereignty_score))),
            "bond_score":        max(0.0, min(1.0, float(bond_score))),
        })
        if session_count is not None:
            self._session_count = int(session_count)
        else:
            self._session_count += 1

    def current_stage(self) -> str:
        """Return the current GAIA developmental stage name.

        Derived from the mean composite score across all turns fed via
        update().  A session-count gate (_MIN_SESSIONS_FOR_PROMOTION)
        prevents false promotions when very few turns have been observed.

        Returns one of:
            "Emergence", "Initiation", "Allegiance",
            "Individuation", "Sovereignty"
        """
        if not self._turns or self._session_count < self._MIN_SESSIONS_FOR_PROMOTION:
            return "Emergence"

        composite = sum(
            (t["depth_score"] + t["sovereignty_score"] + t["bond_score"]) / 3.0
            for t in self._turns
        ) / len(self._turns)

        for threshold, stage_name in self._STAGE_THRESHOLDS:
            if composite < threshold:
                return stage_name

        return "Sovereignty"  # composite >= 0.88 and no threshold matched

    def profile(self) -> DevelopmentProfile:
        """G-9: Return a full DevelopmentProfile snapshot of current state."""
        return DevelopmentProfile.from_engine(self)

    def reset(self) -> None:
        """Reset accumulated state for a fresh assessment cycle."""
        self._turns = []
        self._session_count = 0

    # ------------------------------------------------------------------
    # Stateless API  (original — preserved unchanged)
    # ------------------------------------------------------------------

    def assess(self, context: StageContext) -> StageResult:
        """Stateless stage assessment from a single StageContext snapshot."""
        comp = _composite(
            context.depth_score,
            context.sovereignty_score,
            context.bond_score,
        )
        stage = _stage_from_composite(comp)
        # Apply regression signal: pull back one stage if signal is strong
        if context.regression_signal > 0.5 and stage != Stage.EMERGENCE:
            idx = STAGE_ORDER.index(stage)
            stage = STAGE_ORDER[max(0, idx - 1)]
        confidence = min(1.0, max(0.0, 1.0 - abs(comp - 0.5) * 0.5))
        return StageResult(
            stage=stage,
            confidence=confidence,
            rationale=f"composite={comp:.3f} session_count={context.session_count}",
            metadata=context.metadata,
        )

    def assess_with_themes(
        self, context: StageContext
    ) -> StageResult:
        """Stateless assessment that also returns thematic annotations."""
        result = self.assess(context)
        themes = list(context.themes)
        # Derive implicit themes from signal dimensions
        if context.depth_score > 0.7:
            themes.append("depth")
        if context.sovereignty_score > 0.7:
            themes.append("sovereignty")
        if context.bond_score > 0.7:
            themes.append("resonance")
        result.themes = themes
        return result


# ------------------------------------------------------------------ #
#  Module-level singleton  (convenience — not used by stateful API)  #
# ------------------------------------------------------------------ #

DEFAULT_ENGINE: DevelopmentStageEngine = DevelopmentStageEngine()


def assess(context: StageContext) -> StageResult:
    """Module-level convenience wrapper around DEFAULT_ENGINE.assess()."""
    return DEFAULT_ENGINE.assess(context)
