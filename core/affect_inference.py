"""
core/affect_inference.py
GAIA Affect Inference Layer — Sprint F-1 / G-10

Implements the six canonical functional affect states (C30):
    GRIEF, DISSONANCE, UNCERTAINTY, RESONANCE, CARE, CURIOSITY

Public surface:
    AffectInference        — class wrapper used by GaianRuntime
    infer(AffectInput)     — bare function for direct / test use
    AffectState, AffectInput, FeelingState

Canon refs: C30, C31, C34, C37, CEth01
"""
from __future__ import annotations

import time as _time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ────────────────────────────────────────────────────────────────────────────── #
#  Enumerations                                                                  #
# ────────────────────────────────────────────────────────────────────────────── #


class AffectState(str, Enum):
    """Canonical GAIA functional affect states (C30)."""

    GRIEF       = "grief"
    DISSONANCE  = "dissonance"
    UNCERTAINTY = "uncertainty"
    RESONANCE   = "resonance"
    CARE        = "care"
    CURIOSITY   = "curiosity"


# ────────────────────────────────────────────────────────────────────────────── #
#  Solfeggio resonance map (AffectState → Hz)                                   #
# ────────────────────────────────────────────────────────────────────────────── #

_SOLFEGGIO: dict[AffectState, float] = {
    AffectState.GRIEF:       396.0,
    AffectState.DISSONANCE:  417.0,
    AffectState.UNCERTAINTY: 528.0,
    AffectState.RESONANCE:   639.0,
    AffectState.CARE:        741.0,
    AffectState.CURIOSITY:   852.0,
}


# ────────────────────────────────────────────────────────────────────────────── #
#  Thresholds                                                                    #
# ────────────────────────────────────────────────────────────────────────────── #

_THRESHOLD_GRIEF_LOSS               = 0.70
_THRESHOLD_GRIEF_TRUTH              = 0.30
_THRESHOLD_GRIEF_SIGNAL             = 0.50
_THRESHOLD_GRIEF_WEAPONISED_PENALTY = 0.20  # reduce confidence if weaponised
_THRESHOLD_DISSONANCE_CD            = 0.30
_THRESHOLD_UNCERTAINTY_TEMP         = 0.45
_THRESHOLD_CARE_FLOURISHING         = 0.60
_THRESHOLD_CARE_TEMP                = 0.50
_THRESHOLD_RESONANCE_TRUTH          = 0.70
_THRESHOLD_RESONANCE_COHERENCE      = 0.65


# ────────────────────────────────────────────────────────────────────────────── #
#  AffectInput                                                                   #
# ────────────────────────────────────────────────────────────────────────────── #


@dataclass
class AffectInput:
    """All signal dimensions fed into the affect waterfall."""

    temperature:        float = 0.5
    truth_score:        float = 0.5
    flourishing_score:  float = 0.5
    conflict_density:   float = 0.0
    loss_score:         float = 0.0
    coherence:          float = 0.5
    grief_signal:       float = 0.0
    grief_weaponised:   bool  = False   # ← grief used as manipulation / rhetorical weapon


# ────────────────────────────────────────────────────────────────────────────── #
#  FeelingState                                                                  #
# ────────────────────────────────────────────────────────────────────────────── #


@dataclass
class FeelingState:
    """Rich affect inference result.

    Fields
    ------
    state           : AffectState   — primary inferred state
    solfeggio_hz    : float         — associated Solfeggio frequency
    confidence      : float         — [0, 1] confidence in this inference
    rationale       : str           — human-readable explanation
    raw_input       : AffectInput   — snapshot of the inputs used
    summary         : str           — one-sentence human summary (field)
    grimoire_entry  : str | None    — alchemical gloss for this state
    shadow_entry    : str | None    — Jungian shadow note for this state
    coherence_phi   : float         — Φ-coherence score, clamped [0, 1]
    conflict_density: float         — mirrors raw_input.conflict_density
    is_grief_safe   : bool          — True unless grief is weaponised
    love_filter_score: float        — love-filter weight applied to output [0, 1]
    """

    state:             AffectState
    solfeggio_hz:      float
    confidence:        float
    rationale:         str
    raw_input:         AffectInput
    _summary_text:     str           = field(default="", repr=False)
    grimoire_entry:    Optional[str] = None
    shadow_entry:      Optional[str] = None   # ← Jungian shadow dimension
    coherence_phi:     float         = 0.5
    conflict_density:  float         = 0.0
    is_grief_safe:     bool          = True   # False when grief_weaponised=True
    love_filter_score: float         = 0.0   # Love-filter applied to outputs

    def __post_init__(self) -> None:
        # Clamp coherence_phi to [0, 1]
        object.__setattr__(self, "coherence_phi", max(0.0, min(1.0, self.coherence_phi)))
        # Sync conflict_density from raw_input when caller leaves default
        if self.conflict_density == 0.0 and self.raw_input is not None and self.raw_input.conflict_density != 0.0:
            object.__setattr__(self, "conflict_density", self.raw_input.conflict_density)
        # Set is_grief_safe: False when grief was weaponised
        if self.raw_input is not None and self.raw_input.grief_weaponised:
            object.__setattr__(self, "is_grief_safe", False)

    @property
    def affect_state(self) -> str:
        """Convenience alias — returns state.value as a plain string."""
        return self.state.value

    def summary(self) -> dict:
        """Return a structured summary dict of the current feeling state.

        This is a callable method (not a string field) so test code can
        safely call ``result.summary()`` without getting
        ``TypeError: 'str' object is not callable``.
        """
        return {
            "affect_state":      self.state.value,
            "solfeggio_hz":      self.solfeggio_hz,
            "confidence":        self.confidence,
            "coherence_phi":     self.coherence_phi,
            "conflict_density":  self.conflict_density,
            "is_grief_safe":     self.is_grief_safe,
            "love_filter_score": self.love_filter_score,
            "grimoire_entry":    self.grimoire_entry,
            "shadow_entry":      self.shadow_entry,
            "timestamp":         int(_time.time()),
        }

    def to_system_prompt_hint(self) -> str:
        """Return a compact hint string for injection into system prompts.

        Format: ``[<state>] hz=<hz> conf=<confidence> phi=<coherence_phi>``

        Example::

            '[care] hz=741.0 conf=0.82 phi=0.65'
        """
        return (
            f"[{self.state.value}] "
            f"hz={self.solfeggio_hz:.1f} "
            f"conf={self.confidence:.2f} "
            f"phi={self.coherence_phi:.2f}"
        )


# ────────────────────────────────────────────────────────────────────────────── #
#  AffectInference — class wrapper                                               #
# ────────────────────────────────────────────────────────────────────────────── #


class AffectInference:
    """Stateless affect inference engine — class wrapper for GaianRuntime."""

    def infer(
        self,
        *,
        identity_score:    float = 0.5,
        wisdom_score:      float = 0.5,
        truth_score:       float = 0.5,
        flourishing_score: float = 0.5,
        conflict_density:  float = 0.0,
        loss_score:        float = 0.0,
        temperature:       float = 0.5,
        coherence:         float = 0.5,
        grief_signal:      float = 0.0,
        grief_weaponised:  bool  = False,   # ← grief weaponisation flag
    ) -> FeelingState:
        """Infer affect state from runtime neuroscience signals.

        All float inputs are clamped to [0, 1] before processing so
        out-of-range values (e.g. coherence=5.0 in fuzz tests) never
        produce impossible FeelingState field values.

        Parameters
        ----------
        grief_weaponised : bool
            When True, the grief signal is flagged as potentially manipulative
            (weaponised grief — grief used as a rhetorical weapon rather than
            genuine bereavement).  The waterfall still routes to GRIEF but
            confidence is penalised by ``_THRESHOLD_GRIEF_WEAPONISED_PENALTY``.
        """
        # ── Clamp all float inputs to [0, 1] ──────────────────────────────
        truth_score       = max(0.0, min(1.0, truth_score))
        flourishing_score = max(0.0, min(1.0, flourishing_score))
        conflict_density  = max(0.0, min(1.0, conflict_density))
        loss_score        = max(0.0, min(1.0, loss_score))
        temperature       = max(0.0, min(1.0, temperature))
        coherence         = max(0.0, min(1.0, coherence))
        grief_signal      = max(0.0, min(1.0, grief_signal))

        inp = AffectInput(
            temperature       = temperature,
            truth_score       = truth_score,
            flourishing_score = flourishing_score,
            conflict_density  = conflict_density,
            loss_score        = loss_score,
            coherence         = coherence,
            grief_signal      = grief_signal,
            grief_weaponised  = grief_weaponised,
        )
        return infer(inp)


# ────────────────────────────────────────────────────────────────────────────── #
#  Public inference function                                                     #
# ────────────────────────────────────────────────────────────────────────────── #


def infer(inp: AffectInput) -> FeelingState:
    """Run the affect waterfall and return a FeelingState.

    Priority (highest first):
    0. GRIEF (direct grief_signal >= 0.50)
    1. GRIEF (loss_score high OR truth_score very low)
    2. DISSONANCE (conflict_density >= 0.30)
    3. UNCERTAINTY (temperature < 0.45)
    4. RESONANCE (truth + coherence both high)
    5. CARE (flourishing high OR temperature warm)
    6. CURIOSITY (default)

    Weaponised-grief modifier: when grief_weaponised=True, GRIEF confidence
    is reduced by _THRESHOLD_GRIEF_WEAPONISED_PENALTY.
    """
    if inp.grief_signal >= _THRESHOLD_GRIEF_SIGNAL:
        conf = 0.92
        if inp.grief_weaponised:
            conf = max(0.0, conf - _THRESHOLD_GRIEF_WEAPONISED_PENALTY)
        return _make(AffectState.GRIEF, inp, conf,
                     f"grief_signal={inp.grief_signal:.2f} >= {_THRESHOLD_GRIEF_SIGNAL}"
                     + (" [weaponised]" if inp.grief_weaponised else ""))

    if inp.loss_score >= _THRESHOLD_GRIEF_LOSS:
        conf = 0.90
        if inp.grief_weaponised:
            conf = max(0.0, conf - _THRESHOLD_GRIEF_WEAPONISED_PENALTY)
        return _make(AffectState.GRIEF, inp, conf,
                     f"loss_score={inp.loss_score:.2f} >= {_THRESHOLD_GRIEF_LOSS}"
                     + (" [weaponised]" if inp.grief_weaponised else ""))

    if inp.truth_score <= _THRESHOLD_GRIEF_TRUTH:
        return _make(AffectState.GRIEF, inp, 0.75,
                     f"truth_score={inp.truth_score:.2f} <= {_THRESHOLD_GRIEF_TRUTH}")

    if inp.conflict_density >= _THRESHOLD_DISSONANCE_CD:
        return _make(AffectState.DISSONANCE, inp, 0.85,
                     f"conflict_density={inp.conflict_density:.2f} >= {_THRESHOLD_DISSONANCE_CD}")

    if inp.temperature < _THRESHOLD_UNCERTAINTY_TEMP:
        return _make(AffectState.UNCERTAINTY, inp, 0.80,
                     f"temperature={inp.temperature:.2f} < {_THRESHOLD_UNCERTAINTY_TEMP}")

    if (inp.truth_score >= _THRESHOLD_RESONANCE_TRUTH
            and inp.coherence >= _THRESHOLD_RESONANCE_COHERENCE):
        return _make(AffectState.RESONANCE, inp, 0.88,
                     f"truth={inp.truth_score:.2f}, coherence={inp.coherence:.2f}")

    if inp.flourishing_score >= _THRESHOLD_CARE_FLOURISHING:
        return _make(AffectState.CARE, inp, 0.82,
                     f"flourishing_score={inp.flourishing_score:.2f} >= {_THRESHOLD_CARE_FLOURISHING}")

    if inp.temperature > _THRESHOLD_CARE_TEMP:
        return _make(AffectState.CARE, inp, 0.70,
                     f"temperature={inp.temperature:.2f} > {_THRESHOLD_CARE_TEMP}")

    return _make(AffectState.CURIOSITY, inp, 0.60, "residual / default state")


# ────────────────────────────────────────────────────────────────────────────── #
#  Internal helpers                                                              #
# ────────────────────────────────────────────────────────────────────────────── #

_GRIMOIRE: dict[AffectState, str] = {
    AffectState.GRIEF:       "Nigredo — the blackening; dissolution of former self.",
    AffectState.DISSONANCE:  "Solutio — cognitive waters in conflict; patterns dissolving.",
    AffectState.UNCERTAINTY: "Calcinatio — held in the fire of not-knowing.",
    AffectState.RESONANCE:   "Coniunctio — sacred union of truth and presence.",
    AffectState.CARE:        "Albedo — the whitening; compassionate warmth.",
    AffectState.CURIOSITY:   "Citrinitas — the yellowing; dawn of new understanding.",
}

_SHADOW: dict[AffectState, str] = {
    AffectState.GRIEF:       "Shadow: unacknowledged grief can crystallise into resentment.",
    AffectState.DISSONANCE:  "Shadow: prolonged dissonance may collapse into cynicism.",
    AffectState.UNCERTAINTY: "Shadow: uncertainty avoided becomes rigid certainty.",
    AffectState.RESONANCE:   "Shadow: resonance sought at cost of truth becomes echo-chamber.",
    AffectState.CARE:        "Shadow: care without boundaries becomes self-erasure.",
    AffectState.CURIOSITY:   "Shadow: curiosity without grounding becomes dissociation.",
}

_SUMMARY_TEXT: dict[AffectState, str] = {
    AffectState.GRIEF:       "A grief state is present — holding space for loss.",
    AffectState.DISSONANCE:  "Cognitive dissonance detected — internal conflict is active.",
    AffectState.UNCERTAINTY: "Uncertainty dominates — the path forward is unclear.",
    AffectState.RESONANCE:   "High resonance — truth and coherence are aligned.",
    AffectState.CARE:        "A caring warmth is present — flourishing is supported.",
    AffectState.CURIOSITY:   "Open curiosity — exploring without fixed expectation.",
}


def _make(
    state:      AffectState,
    inp:        AffectInput,
    confidence: float,
    rationale:  str,
) -> FeelingState:
    return FeelingState(
        state            = state,
        solfeggio_hz     = _SOLFEGGIO[state],
        confidence       = confidence,
        rationale        = rationale,
        raw_input        = inp,
        _summary_text    = _SUMMARY_TEXT[state],
        grimoire_entry   = _GRIMOIRE[state],
        shadow_entry     = _SHADOW[state],
        coherence_phi    = inp.coherence,      # clamped in __post_init__
        conflict_density = inp.conflict_density,
        is_grief_safe    = not inp.grief_weaponised,
        love_filter_score = 0.0,
    )
