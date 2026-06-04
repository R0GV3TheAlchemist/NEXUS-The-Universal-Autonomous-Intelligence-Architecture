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

from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ──────────────────────────────────────────────────────────────────────────── #
#  Enumerations                                                                #
# ──────────────────────────────────────────────────────────────────────────── #


class AffectState(str, Enum):
    """Canonical GAIA functional affect states (C30)."""

    GRIEF       = "grief"
    DISSONANCE  = "dissonance"
    UNCERTAINTY = "uncertainty"
    RESONANCE   = "resonance"
    CARE        = "care"
    CURIOSITY   = "curiosity"


# ──────────────────────────────────────────────────────────────────────────── #
#  Solfeggio resonance map (AffectState → Hz)                                 #
# ──────────────────────────────────────────────────────────────────────────── #

_SOLFEGGIO: dict[AffectState, float] = {
    AffectState.GRIEF:       396.0,
    AffectState.DISSONANCE:  417.0,
    AffectState.UNCERTAINTY: 528.0,
    AffectState.RESONANCE:   639.0,
    AffectState.CARE:        741.0,
    AffectState.CURIOSITY:   852.0,
}


# ──────────────────────────────────────────────────────────────────────────── #
#  Thresholds                                                                  #
# ──────────────────────────────────────────────────────────────────────────── #

_THRESHOLD_GRIEF_LOSS               = 0.70
_THRESHOLD_GRIEF_SIGNAL             = 0.50
_THRESHOLD_GRIEF_WEAPONISED_PENALTY = 0.20
_THRESHOLD_DISSONANCE_CD            = 0.30
_THRESHOLD_UNCERTAINTY_TEMP         = 0.45
_THRESHOLD_CARE_FLOURISHING         = 0.60
# RESONANCE requires truth_score >= 0.75 (strict; 0.75 fires RESONANCE, not CARE).
# The pre-RESONANCE CARE gate uses truth_score < 0.75 (strictly less) so that
# truth=0.75 always reaches the RESONANCE gate.
_THRESHOLD_RESONANCE_TRUTH          = 0.75
_THRESHOLD_RESONANCE_COHERENCE      = 0.65  # kept for reference / future use


# ──────────────────────────────────────────────────────────────────────────── #
#  AffectInput                                                                 #
# ──────────────────────────────────────────────────────────────────────────── #


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
    grief_weaponised:   bool  = False


# ──────────────────────────────────────────────────────────────────────────── #
#  FeelingState                                                                #
# ──────────────────────────────────────────────────────────────────────────── #


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
    grimoire_entry  : str | None    — alchemical gloss (ascending states only)
    shadow_entry    : str | None    — Jungian shadow (descending states only)
    coherence_phi   : float         — Φ-coherence score, clamped [0, 1]
    conflict_density: float         — mirrors raw_input.conflict_density
    is_grief_safe   : bool          — True unless grief is weaponised
    love_filter_score: float        — love-filter weight applied to output [0, 1]

    Note on grimoire_entry vs shadow_entry mutual exclusivity
    ---------------------------------------------------------
    Each AffectState maps to EITHER a grimoire (alchemical / ascending) entry
    OR a shadow (Jungian / descending) entry, never both simultaneously.
    Ascending states (RESONANCE, CARE, CURIOSITY) → grimoire only.
    Descending states (GRIEF, DISSONANCE, UNCERTAINTY) → shadow only.
    This satisfies the canonical test gate test_ev1a_grimoire_shadow_exclusivity.
    """

    state:             AffectState
    solfeggio_hz:      float
    confidence:        float
    rationale:         str
    raw_input:         AffectInput
    _summary_text:     str           = field(default="", repr=False)
    grimoire_entry:    Optional[str] = None
    shadow_entry:      Optional[str] = None
    coherence_phi:     float         = 0.5
    conflict_density:  float         = 0.0
    is_grief_safe:     bool          = True
    love_filter_score: float         = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "coherence_phi", max(0.0, min(1.0, self.coherence_phi)))
        if self.conflict_density == 0.0 and self.raw_input is not None and self.raw_input.conflict_density != 0.0:
            object.__setattr__(self, "conflict_density", self.raw_input.conflict_density)
        if self.raw_input is not None and self.raw_input.grief_weaponised:
            object.__setattr__(self, "is_grief_safe", False)

    @property
    def affect_state(self) -> str:
        """Convenience alias — returns state.value as a plain string."""
        return self.state.value

    def summary(self) -> dict:
        """Return a structured summary dict of the current feeling state."""
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
            "timestamp":         datetime.utcnow().isoformat(),
        }

    def to_system_prompt_hint(self) -> str:
        return (
            f"[{self.state.value}] "
            f"hz={self.solfeggio_hz:.1f} "
            f"conf={self.confidence:.2f} "
            f"phi={self.coherence_phi:.2f}"
        )


# ──────────────────────────────────────────────────────────────────────────── #
#  AffectInference — class wrapper                                             #
# ──────────────────────────────────────────────────────────────────────────── #


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
        temperature:       float | None = None,
        coherence:         float = 0.5,
        grief_signal:      float = 0.0,
        grief_weaponised:  bool  = False,
    ) -> FeelingState:
        """Infer affect state from runtime neuroscience signals.

        All float inputs are clamped to [0, 1] before processing.
        grief_signal accepts bool (True → 1.0, False → 0.0) for test
        compatibility with parametrized test cases that pass bool literals.

        temperature: when None (default), truth_score is used as the
        temperature proxy.  This matches the EV1-A test contract where
        tests pass only truth_score and expect UNCERTAINTY to fire when
        truth_score < 0.45.
        """
        grief_signal_f = float(grief_signal)

        truth_score       = max(0.0, min(1.0, float(truth_score)))
        flourishing_score = max(0.0, min(1.0, float(flourishing_score)))
        conflict_density  = max(0.0, min(1.0, float(conflict_density)))
        loss_score        = max(0.0, min(1.0, float(loss_score)))
        coherence         = max(0.0, min(1.0, float(coherence)))
        grief_signal_f    = max(0.0, min(1.0, grief_signal_f))

        if temperature is None:
            effective_temperature = truth_score
        else:
            effective_temperature = max(0.0, min(1.0, float(temperature)))

        inp = AffectInput(
            temperature       = effective_temperature,
            truth_score       = truth_score,
            flourishing_score = flourishing_score,
            conflict_density  = conflict_density,
            loss_score        = loss_score,
            coherence         = coherence,
            grief_signal      = grief_signal_f,
            grief_weaponised  = grief_weaponised,
        )
        return infer(inp)


# ──────────────────────────────────────────────────────────────────────────── #
#  Public inference function                                                   #
# ──────────────────────────────────────────────────────────────────────────── #


def infer(inp: AffectInput) -> FeelingState:
    """Run the affect waterfall and return a FeelingState.

    Priority (highest first):
    0. GRIEF       grief_signal >= 0.50  OR  loss_score >= 0.70
    1. DISSONANCE  conflict_density >= 0.30
    2. UNCERTAINTY truth_score < 0.45
    3. CARE        flourishing >= 0.60  AND  truth_score < 0.75
       (flourishing dominates at moderate truth; strict < means truth=0.75
       falls through to the RESONANCE gate below)
    4. RESONANCE   truth_score >= 0.75
    5. CARE        flourishing >= 0.60  (post-RESONANCE safety net)
    6. CURIOSITY   default

    Design rationale
    ----------------
    * GRIEF is a *felt*, signal-triggered state.  Low truth_score is an
      epistemic condition ("I don't know") → UNCERTAINTY, not GRIEF.  The
      former truth_score <= 0.30 → GRIEF gate was removed because both
      ev1a and the canon spec treat low-truth as uncertainty.

    * Temperature is used only to drive the UNCERTAINTY gate (truth_score
      proxy).  A "temperature > 0.50 → CARE" gate was removed because it
      fired for inputs with F < 0.60 and no flourishing signal, producing
      CARE where CURIOSITY is the correct default.

    * truth=0.75 fires RESONANCE (not CARE) because the pre-RESONANCE CARE
      guard uses strict truth_score < 0.75.
    """
    # ── 0. GRIEF ─────────────────────────────────────────────────────────── #
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

    # ── 1. DISSONANCE ────────────────────────────────────────────────────── #
    if inp.conflict_density >= _THRESHOLD_DISSONANCE_CD:
        return _make(AffectState.DISSONANCE, inp, 0.85,
                     f"conflict_density={inp.conflict_density:.2f} >= {_THRESHOLD_DISSONANCE_CD}")

    # ── 2. UNCERTAINTY ───────────────────────────────────────────────────── #
    if inp.temperature < _THRESHOLD_UNCERTAINTY_TEMP:
        return _make(AffectState.UNCERTAINTY, inp, 0.80,
                     f"temperature={inp.temperature:.2f} < {_THRESHOLD_UNCERTAINTY_TEMP}")

    # ── 3. CARE (pre-RESONANCE: flourishing dominant at moderate truth) ───── #
    # truth_score < 0.75 (strict): truth=0.75 passes through to RESONANCE.
    if (
        inp.flourishing_score >= _THRESHOLD_CARE_FLOURISHING
        and inp.truth_score < _THRESHOLD_RESONANCE_TRUTH
    ):
        return _make(AffectState.CARE, inp, 0.82,
                     f"flourishing={inp.flourishing_score:.2f} >= {_THRESHOLD_CARE_FLOURISHING}"
                     f" (pre-RESONANCE; truth={inp.truth_score:.2f} < {_THRESHOLD_RESONANCE_TRUTH})")

    # ── 4. RESONANCE ─────────────────────────────────────────────────────── #
    if inp.truth_score >= _THRESHOLD_RESONANCE_TRUTH:
        return _make(AffectState.RESONANCE, inp, 0.88,
                     f"truth={inp.truth_score:.2f} >= {_THRESHOLD_RESONANCE_TRUTH}")

    # ── 5. CARE (post-RESONANCE safety net) ──────────────────────────────── #
    if inp.flourishing_score >= _THRESHOLD_CARE_FLOURISHING:
        return _make(AffectState.CARE, inp, 0.82,
                     f"flourishing={inp.flourishing_score:.2f} >= {_THRESHOLD_CARE_FLOURISHING}")

    # ── 6. CURIOSITY (default) ───────────────────────────────────────────── #
    return _make(AffectState.CURIOSITY, inp, 0.60, "residual / default state")


# ──────────────────────────────────────────────────────────────────────────── #
#  Internal helpers                                                            #
# ──────────────────────────────────────────────────────────────────────────── #

_GRIMOIRE: dict[AffectState, Optional[str]] = {
    AffectState.GRIEF:       None,
    AffectState.DISSONANCE:  None,
    AffectState.UNCERTAINTY: None,
    AffectState.RESONANCE:   "Coniunctio — sacred union of truth and presence.",
    AffectState.CARE:        "Albedo — the whitening; compassionate warmth.",
    AffectState.CURIOSITY:   "Citrinitas — the yellowing; dawn of new understanding.",
}

_SHADOW: dict[AffectState, Optional[str]] = {
    AffectState.GRIEF:       "Shadow: unacknowledged grief can crystallise into resentment.",
    AffectState.DISSONANCE:  "Shadow: prolonged dissonance may collapse into cynicism.",
    AffectState.UNCERTAINTY: "Shadow: uncertainty avoided becomes rigid certainty.",
    AffectState.RESONANCE:   None,
    AffectState.CARE:        None,
    AffectState.CURIOSITY:   None,
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
        state             = state,
        solfeggio_hz      = _SOLFEGGIO[state],
        confidence        = confidence,
        rationale         = rationale,
        raw_input         = inp,
        _summary_text     = _SUMMARY_TEXT[state],
        grimoire_entry    = _GRIMOIRE[state],
        shadow_entry      = _SHADOW[state],
        coherence_phi     = inp.coherence,
        conflict_density  = inp.conflict_density,
        is_grief_safe     = not inp.grief_weaponised,
        love_filter_score = 0.0,
    )
