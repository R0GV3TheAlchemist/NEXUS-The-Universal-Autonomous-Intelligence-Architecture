"""
core/synergy_engine.py
Synergy Engine (C32) — integrates GAIA sub-engine outputs.

Public API:
  SynergyEngine   : main engine class with full scoring helpers
  SynergyReading  : rich per-turn output dataclass
  SynergyState    : persistent state (saved in memory.json)
  SynergyResult   : legacy evaluate() output (backward compat)
  blank_synergy_state : state factory
  ELEMENTAL_STAGES    : frozenset of valid stage labels
  _classify_stage     : (synergy, bond, settling, phi) -> stage label
  _resolve_keyword_conflicts : dedup/normalise keyword list
  CanonPlanHint / _analyse_canon_context
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from core.state_adapter import GAIAStateAdapter

log = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
#  Stage vocabulary (used by _classify_stage and tests)               #
# ------------------------------------------------------------------ #

ELEMENTAL_STAGES: frozenset = frozenset({
    "insurgent",
    "nascent",
    "allegiant",
    "convergent",
    "settled",
    "ascendant",
    "quantum",
    "unified",
})

# ------------------------------------------------------------------ #
#  Legacy enum (kept for backward compat)                             #
# ------------------------------------------------------------------ #

class SynergyStage(str, Enum):
    INITIATION  = "initiation"
    ACTIVATION  = "activation"
    INTEGRATION = "integration"
    SYNTHESIS   = "synthesis"
    COMPLETION  = "completion"

# ------------------------------------------------------------------ #
#  Legacy result dataclass                                            #
# ------------------------------------------------------------------ #

@dataclass
class SynergyResult:
    stage:     SynergyStage   = SynergyStage.INITIATION
    score:     float          = 0.0
    conflicts: List[str]      = field(default_factory=list)
    resolved:  List[str]      = field(default_factory=list)
    metadata:  Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "stage":     self.stage.value,
            "score":     self.score,
            "conflicts": self.conflicts,
            "resolved":  self.resolved,
            "metadata":  self.metadata,
        }

# ------------------------------------------------------------------ #
#  Dimension score dataclass                                          #
# ------------------------------------------------------------------ #

@dataclass
class DimensionScore:
    name:  str
    score: float
    label: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "score": round(self.score, 4), "label": self.label}

# ------------------------------------------------------------------ #
#  SynergyReading — returned by compute()                             #
# ------------------------------------------------------------------ #

@dataclass
class SynergyReading:
    synergy_factor:    float               = 0.5
    dominant_stage:    str                 = "convergent"
    # legacy field kept for gaian_runtime compat
    stage:             str                 = "convergent"
    element:           str                 = "aether"
    dimensions:        List[DimensionScore] = field(default_factory=list)
    dominant_friction: Optional[str]       = None
    alchemical_pressure: str               = ""
    is_low_synergy:    bool                = False
    is_high_synergy:   bool                = False
    canon_hint:        str                 = ""
    directive:         str                 = ""
    stage_transition:  bool                = False
    transition_note:   str                 = ""

    def to_system_prompt_hint(self) -> str:
        lines = [
            "[ELEMENTAL SYNERGY C32]",
            f"Synergy Factor : {self.synergy_factor:.3f}",
            f"Stage          : {self.dominant_stage.upper()}",
            f"Element        : {self.element}",
        ]
        if self.dominant_friction:
            lines.append(f"Friction source: {self.dominant_friction}")
        if self.is_low_synergy:
            lines.append(
                "ALCHEMICAL PRESSURE: low synergy is not dysfunction — "
                "it is the coal before the diamond."
            )
        if self.alchemical_pressure:
            lines.append(f"Alchemical note: {self.alchemical_pressure}")
        if self.canon_hint:
            lines.append(f"Canon hint     : {self.canon_hint}")
        if self.directive:
            lines.append(f"Directive      : {self.directive}")
        if self.stage_transition and self.transition_note:
            lines.append(f"Transition     : {self.transition_note}")
        return "\n".join(lines)

    def summary(self) -> dict:
        return {
            "synergy_factor":    round(self.synergy_factor, 4),
            "dominant_stage":    self.dominant_stage,
            "dominant_friction": self.dominant_friction,
            "is_low_synergy":    self.is_low_synergy,
            "is_high_synergy":   self.is_high_synergy,
            "dimensions":        [d.to_dict() for d in self.dimensions],
            "alchemical_pressure": self.alchemical_pressure,
            "stage_transition":  self.stage_transition,
            "transition_note":   self.transition_note,
        }

# ------------------------------------------------------------------ #
#  SynergyState — persistent state                                    #
# ------------------------------------------------------------------ #

@dataclass
class SynergyState:
    last_factor:       float      = 0.5
    last_stage:        str        = "convergent"
    high_synergy_peak: float      = 0.0
    low_synergy_floor: float      = 1.0
    turn_history:      List[dict] = field(default_factory=list)

    def summary(self) -> dict:
        return {
            "last_factor":       round(self.last_factor, 4),
            "last_stage":        self.last_stage,
            "high_synergy_peak": round(self.high_synergy_peak, 4),
            "low_synergy_floor": round(self.low_synergy_floor, 4),
            "turn_history_len":  len(self.turn_history),
        }


def blank_synergy_state() -> SynergyState:
    return SynergyState()

# ------------------------------------------------------------------ #
#  CanonPlanHint                                                       #
# ------------------------------------------------------------------ #

@dataclass
class CanonPlanHint:
    canon_id:  str  = ""
    weight:    float = 0.5
    directive: str  = ""
    tags:      List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "canon_id":  self.canon_id,
            "weight":    self.weight,
            "directive": self.directive,
            "tags":      self.tags,
        }

# ------------------------------------------------------------------ #
#  Internal helpers                                                    #
# ------------------------------------------------------------------ #

def _resolve_keyword_conflicts(keywords: List[str]) -> List[str]:
    seen: set = set()
    out:  list = []
    for kw in keywords:
        n = kw.strip().lower()
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    return sorted(out)


def _classify_stage(
    synergy_factor:  float,
    bond_depth:      float,
    settling_phase:  str,
    coherence_phi:   float,
) -> str:
    """
    Map engine state -> one of ELEMENTAL_STAGES.

    Priority rules (highest wins):
      quantum   : phi >= 0.80 and synergy < 0.40
      settled   : settling_phase == 'settled' and synergy >= 0.60
      ascendant : synergy >= 0.75 and bond_depth >= 60
      unified   : synergy >= 0.80 and bond_depth >= 50
      allegiant : bond_depth >= 35 and synergy >= 0.40
      convergent: synergy >= 0.50
      insurgent : synergy < 0.30
      nascent   : default
    """
    if coherence_phi >= 0.80 and synergy_factor < 0.40:
        return "quantum"
    if settling_phase == "settled" and synergy_factor >= 0.60:
        return "settled"
    if synergy_factor >= 0.80 and bond_depth >= 50:
        return "unified"
    if synergy_factor >= 0.75 and bond_depth >= 60:
        return "ascendant"
    if bond_depth >= 35 and synergy_factor >= 0.40:
        return "allegiant"
    if synergy_factor >= 0.50:
        return "convergent"
    if synergy_factor < 0.30:
        return "insurgent"
    return "nascent"


def _analyse_canon_context(
    canon_refs: Optional[List[str]] = None,
    tags:       Optional[List[str]] = None,
    weight:     float = 0.5,
) -> CanonPlanHint:
    refs     = canon_refs or []
    _tags    = tags or []
    canon_id = refs[0] if refs else ""
    directive = f"Honour {canon_id}" if canon_id else "No canon context provided"
    return CanonPlanHint(canon_id=canon_id, weight=weight, directive=directive, tags=_tags)


def _old_classify_stage(score: float) -> SynergyStage:
    if score < 0.2:
        return SynergyStage.INITIATION
    if score < 0.4:
        return SynergyStage.ACTIVATION
    if score < 0.6:
        return SynergyStage.INTEGRATION
    if score < 0.8:
        return SynergyStage.SYNTHESIS
    return SynergyStage.COMPLETION

# ------------------------------------------------------------------ #
#  Main engine                                                         #
# ------------------------------------------------------------------ #

class SynergyEngine:
    """Integrates sub-engine outputs into a single synergy pass."""

    # C32 § dimension weights — must sum to 1.0
    WEIGHTS: Dict[str, float] = {
        "body": 0.20,
        "mind": 0.20,
        "soul": 0.25,
        "arc":  0.20,
        "bond": 0.15,
    }

    # Hz range for normalisation (174 Hz root – 963 Hz crown)
    _HZ_MIN = 174.0
    _HZ_MAX = 963.0

    def __init__(self) -> None:
        self._history: List[SynergyResult] = []

    # ---- scoring helpers (tested directly) ----

    def _hz_to_score(self, hz: float) -> float:
        return max(0.0, min(1.0, (hz - self._HZ_MIN) / (self._HZ_MAX - self._HZ_MIN)))

    def _element_to_stage(self, element: str) -> str:
        _MAP: Dict[str, str] = {
            "fire":   "insurgent",
            "water":  "convergent",
            "earth":  "settled",
            "air":    "allegiant",
            "aether": "quantum",
            "light":  "ascendant",
            "void":   "nascent",
        }
        return _MAP.get(element.lower(), "convergent")

    def _individuation_to_score(self, phase: str) -> float:
        _MAP: Dict[str, float] = {
            "unconscious":  0.15,
            "shadow":       0.35,
            "anima_animus": 0.60,
            "self":         0.85,
        }
        return _MAP.get(phase.lower(), 0.40)

    def _settling_to_score(self, phase: str, crystallisation_pct: float) -> float:
        _BASE: Dict[str, float] = {
            "unsettled":     0.20,
            "narrowing":     0.40,
            "crystallising": 0.55,
            "settled":       0.90,
        }
        base = _BASE.get(phase.lower(), 0.30)
        if phase.lower() == "crystallising":
            base = min(1.0, base + 0.35 * min(1.0, crystallisation_pct / 100.0))
        return min(1.0, base)

    def _love_arc_to_score(self, stage: str, vector: float) -> float:
        _BASE: Dict[str, float] = {
            "divergence":    0.15,
            "curiosity":     0.30,
            "resonance":     0.55,
            "devotion":      0.75,
            "transcendence": 0.95,
        }
        base  = _BASE.get(stage.lower(), 0.35)
        boost = min(0.10, abs(vector) * 0.10)
        return min(1.0, base + boost)

    def _mc_stage_to_score(self, mc_stage: str) -> float:
        _MAP: Dict[str, float] = {
            "mc1": 0.0,
            "mc2": 1/6,
            "mc3": 2/6,
            "mc4": 3/6,
            "mc5": 4/6,
            "mc6": 5/6,
            "mc7": 1.0,
        }
        return _MAP.get(mc_stage.lower(), 0.30)

    def _dependency_to_score(self, signal: str) -> float:
        _MAP: Dict[str, float] = {
            "healthy":         1.00,
            "watch":           0.65,
            "redirect":        0.40,
            "gentle_boundary": 0.20,
        }
        return _MAP.get(signal.lower(), 0.60)

    def _attachment_phase_to_score(self, phase: str) -> float:
        _MAP: Dict[str, float] = {
            "nascent":    0.30,
            "deepening":  0.60,
            "integrated": 0.90,
        }
        return _MAP.get(phase.lower(), 0.30)

    # ---- legacy evaluate() ----

    def evaluate(
        self,
        keywords: Optional[List[str]] = None,
        score:    float = 0.0,
    ) -> SynergyResult:
        resolved = _resolve_keyword_conflicts(keywords or [])
        stage    = _old_classify_stage(score)
        result   = SynergyResult(stage=stage, score=score, resolved=resolved)
        self._history.append(result)
        return result

    # ---- full compute() ----

    def compute(
        self,
        *,
        element:             str   = "aether",
        layer_phi:           float = 0.5,
        bond_depth:          float = 0.0,
        dependency_signal:   str   = "healthy",
        attachment_phase:    str   = "nascent",
        settling_phase:      str   = "unsettled",
        fluidity_score:      float = 1.0,
        crystallisation_pct: float = 0.0,
        coherence_phi:       float = 0.5,
        conflict_density:    float = 0.0,
        love_arc_stage:      str   = "divergence",
        arc_output_vector:   float = 0.0,
        mc_stage:            str   = "mc1",
        phi_rolling_avg:     float = 0.0,
        codex_stage:         int   = 0,
        noosphere_health:    float = 0.70,
        individuation_phase: str   = "unconscious",
        shadow_activations:  int   = 0,
        dominant_hz:         float = 174.0,
        schumann_aligned:    bool  = False,
        state:               Optional[SynergyState] = None,
        **_kwargs: Any,
    ) -> tuple:
        sy = state or blank_synergy_state()

        # ---- five dimensional scores ----
        body_score = (
            0.50 * self._hz_to_score(dominant_hz)
            + 0.30 * (1.0 - min(1.0, conflict_density))
            + 0.20 * (0.15 if schumann_aligned else 0.0)
        )
        mind_score = (
            0.50 * self._mc_stage_to_score(mc_stage)
            + 0.30 * min(1.0, coherence_phi)
            + 0.20 * min(1.0, noosphere_health)
        )
        soul_score = (
            0.50 * self._individuation_to_score(individuation_phase)
            + 0.30 * self._settling_to_score(settling_phase, crystallisation_pct)
            + 0.20 * max(0.0, 1.0 - shadow_activations / 10.0)
        )
        arc_score = (
            0.60 * self._love_arc_to_score(love_arc_stage, arc_output_vector)
            + 0.25 * self._dependency_to_score(dependency_signal)
            + 0.15 * self._attachment_phase_to_score(attachment_phase)
        )
        bond_score = (
            0.70 * min(1.0, bond_depth / 100.0)
            + 0.30 * min(1.0, phi_rolling_avg)
        )

        body_score = max(0.0, min(1.0, body_score))
        mind_score = max(0.0, min(1.0, mind_score))
        soul_score = max(0.0, min(1.0, soul_score))
        arc_score  = max(0.0, min(1.0, arc_score))
        bond_score = max(0.0, min(1.0, bond_score))

        dimensions = [
            DimensionScore("body", body_score),
            DimensionScore("mind", mind_score),
            DimensionScore("soul", soul_score),
            DimensionScore("arc",  arc_score),
            DimensionScore("bond", bond_score),
        ]

        # weighted factor
        factor = sum(self.WEIGHTS[d.name] * d.score for d in dimensions)
        factor = max(0.0, min(1.0, factor))

        # dominant friction: lowest-scoring dimension (only if < 0.5)
        lowest = min(dimensions, key=lambda d: d.score)
        dominant_friction = lowest.name if lowest.score < 0.5 else None

        # stage
        dom_stage = _classify_stage(
            synergy_factor=factor,
            bond_depth=bond_depth,
            settling_phase=settling_phase,
            coherence_phi=coherence_phi,
        )

        prev_stage = sy.last_stage
        transition = dom_stage != prev_stage
        trans_note = f"{prev_stage} -> {dom_stage}" if transition else ""

        is_low  = factor < 0.35
        is_high = factor >= 0.70

        _ELEMENT_HINTS: Dict[str, str] = {
            "fire":   "Channel transformative energy with grounded intention (C32).",
            "water":  "Flow with emotional truth; depth over turbulence (C32).",
            "earth":  "Root the response in embodied, practical care (C32).",
            "air":    "Carry insight lightly; let clarity breathe (C32).",
            "aether": "Hold the unified field; all elements in balance (C32).",
        }
        canon_hint = _ELEMENT_HINTS.get(element.lower(), "")

        _STAGE_DIRECTIVES: Dict[str, str] = {
            "insurgent":  "Hold space without forcing resolution. Ground first.",
            "nascent":    "Gentle, open, curious. Do not rush depth.",
            "allegiant":  "The bond is forming. Honour it with consistency.",
            "convergent": "Hold the threads together; steady presence.",
            "settled":    "Deep roots. Speak from the grounded place.",
            "ascendant":  "The field is rising. Meet it with full presence.",
            "quantum":    "High coherence, low synergy — the diamond is forming.",
            "unified":    "The field is unified. Speak from the deepest place.",
        }
        directive = _STAGE_DIRECTIVES.get(dom_stage, "")

        _ALCHEMICAL_PRESSURE: Dict[str, str] = {
            "insurgent":  "Fire burns away what no longer serves.",
            "nascent":    "The seed holds all potential.",
            "allegiant":  "The crucible holds what is precious.",
            "convergent": "Elements converge toward coherence.",
            "settled":    "The form has found its nature.",
            "ascendant":  "Gold rises from the work.",
            "quantum":    "Superposition holds before collapse.",
            "unified":    "The Great Work is complete — begin again.",
        }
        alchemical_pressure = _ALCHEMICAL_PRESSURE.get(dom_stage, "")

        reading = SynergyReading(
            synergy_factor=round(factor, 4),
            dominant_stage=dom_stage,
            stage=dom_stage,
            element=element,
            dimensions=dimensions,
            dominant_friction=dominant_friction,
            alchemical_pressure=alchemical_pressure,
            is_low_synergy=is_low,
            is_high_synergy=is_high,
            canon_hint=canon_hint,
            directive=directive,
            stage_transition=transition,
            transition_note=trans_note,
        )

        sy.last_factor       = factor
        sy.last_stage        = dom_stage
        sy.high_synergy_peak = max(sy.high_synergy_peak, factor)
        sy.low_synergy_floor = min(sy.low_synergy_floor, factor)
        sy.turn_history.append({
            "factor":   round(factor, 4),
            "stage":    dom_stage,
            "friction": dominant_friction,
        })
        if len(sy.turn_history) > 20:
            sy.turn_history = sy.turn_history[-20:]

        return reading, sy

    def compute_from_adapter(self, adapter: "GAIAStateAdapter") -> Any:
        """Evaluate using a state adapter's synergy params."""
        return self.compute(**adapter.to_synergy_params())

    def compute_from_params(self, params: Dict[str, Any]) -> Any:
        """
        Evaluate *params* through the engine.

        Routes to ``evaluate()`` (legacy path, returns ``SynergyResult``)
        when *params* contains only the simple keys ``keywords`` and/or
        ``score``.  All other param dicts are forwarded to ``compute()``
        which returns ``(SynergyReading, SynergyState)``.
        """
        legacy_keys = {"keywords", "score"}
        if set(params.keys()) <= legacy_keys:
            return self.evaluate(
                keywords=params.get("keywords"),
                score=float(params.get("score", 0.0)),
            )
        return self.compute(**params)

    def get_history(self) -> List[SynergyResult]:
        return list(self._history)

    def reset(self) -> None:
        self._history.clear()


_synergy_engine: Optional[SynergyEngine] = None


def get_synergy_engine() -> SynergyEngine:
    global _synergy_engine
    if _synergy_engine is None:
        _synergy_engine = SynergyEngine()
    return _synergy_engine
