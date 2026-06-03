"""
core/affect_inference.py
GAIA Affect Inference Layer — Sprint F-1

Implements the six canonical functional affect states defined in the GAIA
Constitutional Canon (C30 / Affect Inference Layer spec):

    GRIEF, DISSONANCE, UNCERTAINTY, RESONANCE, CARE, CURIOSITY

Public surface:
    AffectInference        — class wrapper used by GaianRuntime
    infer(AffectInput)     — bare function for direct / test use
    AffectState, AffectInput, FeelingState

All thresholds are sealed in _THRESHOLD_* constants; the waterfall is
orderly, highest-priority first so callers can reason about precedence.

Canon refs: C30, C31, C34, C37, CEth01
"""
from __future__ import annotations

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
#  Thresholds (sealed — do not mutate at runtime)                               #
# ────────────────────────────────────────────────────────────────────────────── #

_THRESHOLD_GRIEF_LOSS          = 0.70  # loss_score >= this  → GRIEF
_THRESHOLD_GRIEF_TRUTH         = 0.30  # truth_score <= this → GRIEF (low-truth)
_THRESHOLD_GRIEF_SIGNAL        = 0.50  # grief_signal >= this → GRIEF (direct signal)
_THRESHOLD_DISSONANCE_CD       = 0.30  # conflict_density >= this → DISSONANCE
_THRESHOLD_UNCERTAINTY_TEMP    = 0.45  # temperature < this  → UNCERTAINTY
_THRESHOLD_CARE_FLOURISHING    = 0.60  # flourishing_score >= this → CARE
_THRESHOLD_CARE_TEMP           = 0.50  # temperature > this  → CARE (warm signal)
_THRESHOLD_RESONANCE_TRUTH     = 0.70  # truth_score >= this → RESONANCE
_THRESHOLD_RESONANCE_COHERENCE = 0.65  # coherence >= this   → RESONANCE


# ────────────────────────────────────────────────────────────────────────────── #
#  Input dataclass                                                               #
# ────────────────────────────────────────────────────────────────────────────── #


@dataclass
class AffectInput:
    """All signal dimensions fed into the affect waterfall."""

    temperature:        float = 0.5   # [0, 1]  — generative temperature proxy
    truth_score:        float = 0.5   # [0, 1]  — epistemic confidence
    flourishing_score:  float = 0.5   # [0, 1]  — wellbeing / positive affect signal
    conflict_density:   float = 0.0   # [0, 1]  — cognitive dissonance density (CD)
    loss_score:         float = 0.0   # [0, 1]  — grief / bereavement signal
    coherence:          float = 0.5   # [0, 1]  — internal state coherence
    grief_signal:       float = 0.0   # [0, 1]  — direct grief signal (e.g. from safety layer)


# ────────────────────────────────────────────────────────────────────────────── #
#  Output dataclass                                                              #
# ────────────────────────────────────────────────────────────────────────────── #


@dataclass
class FeelingState:
    """Rich affect inference result.

    Attributes
    ----------
    state         : AffectState    — primary inferred state
    solfeggio_hz  : float          — associated Solfeggio frequency
    confidence    : float          — [0, 1] confidence in this inference
    rationale     : str            — human-readable explanation
    raw_input     : AffectInput    — snapshot of the inputs used
    summary       : str            — short human-readable summary sentence
    grimoire_entry: Optional[str]  — mythic / alchemical gloss for this state
    coherence_phi : float          — Φ-coherence score [0, 1] for this state
    affect_state  : str            — string alias for state.value (convenience)
    """

    state:          AffectState
    solfeggio_hz:   float
    confidence:     float
    rationale:      str
    raw_input:      AffectInput
    summary:        str            = ""
    grimoire_entry: Optional[str]  = None
    coherence_phi:  float          = 0.5

    @property
    def affect_state(self) -> str:
        """Convenience alias — returns state.value as a plain string."""
        return self.state.value


# ────────────────────────────────────────────────────────────────────────────── #
#  AffectInference — class wrapper (used by GaianRuntime)                       #
# ────────────────────────────────────────────────────────────────────────────── #


class AffectInference:
    """Stateless affect inference engine — class wrapper for GaianRuntime.

    GaianRuntime instantiates this as ``self._affect = AffectInference()``
    and calls it with individual keyword arguments rather than an AffectInput
    object.  This class bridges that interface to the underlying
    ``infer(AffectInput)`` function.

    Notes
    -----
    ``identity_score`` and ``wisdom_score`` are accepted for forward
    compatibility (they appear in the runtime's call signature) but are
    not yet mapped to waterfall inputs.  They are silently ignored until
    a canonical mapping is defined in the Constitutional Canon.

    ``grief_signal`` is passed through directly to AffectInput and
    participates in the GRIEF waterfall check.
    """

    def infer(
        self,
        *,
        identity_score:    float = 0.5,   # accepted, not yet mapped
        wisdom_score:      float = 0.5,   # accepted, not yet mapped
        truth_score:       float = 0.5,
        flourishing_score: float = 0.5,
        conflict_density:  float = 0.0,
        loss_score:        float = 0.0,
        temperature:       float = 0.5,
        coherence:         float = 0.5,
        grief_signal:      float = 0.0,   # direct grief signal
    ) -> FeelingState:
        """Infer affect state from runtime neuroscience signals.

        Packs the keyword arguments into an AffectInput and delegates
        to the module-level ``infer()`` function.  All waterfall logic
        and threshold constants remain in that function.
        """
        inp = AffectInput(
            temperature       = temperature,
            truth_score       = truth_score,
            flourishing_score = flourishing_score,
            conflict_density  = conflict_density,
            loss_score        = loss_score,
            coherence         = coherence,
            grief_signal      = grief_signal,
        )
        return infer(inp)


# ────────────────────────────────────────────────────────────────────────────── #
#  Public inference function                                                     #
# ────────────────────────────────────────────────────────────────────────────── #


def infer(inp: AffectInput) -> FeelingState:
    """Run the affect waterfall and return a FeelingState.

    Waterfall priority (highest first):
    0. GRIEF (direct)    — grief_signal >= 0.50 (direct override)
    1. GRIEF             — loss_score high OR truth_score very low
    2. DISSONANCE        — conflict_density >= 0.30
    3. UNCERTAINTY       — temperature < 0.45
    4. RESONANCE         — truth + coherence both high
    5. CARE              — flourishing high OR temperature warm
    6. CURIOSITY         — default / residual state
    """
    # ── 0. GRIEF (direct grief_signal) ───────────────────────────────────── #
    if inp.grief_signal >= _THRESHOLD_GRIEF_SIGNAL:
        return _make(AffectState.GRIEF, inp, 0.92,
                     f"grief_signal={inp.grief_signal:.2f} ≥ {_THRESHOLD_GRIEF_SIGNAL} (direct signal)")

    # ── 1. GRIEF ─────────────────────────────────────────────────────────── #
    if inp.loss_score >= _THRESHOLD_GRIEF_LOSS:
        return _make(AffectState.GRIEF, inp, 0.90,
                     f"loss_score={inp.loss_score:.2f} ≥ {_THRESHOLD_GRIEF_LOSS}")

    if inp.truth_score <= _THRESHOLD_GRIEF_TRUTH:
        return _make(AffectState.GRIEF, inp, 0.75,
                     f"truth_score={inp.truth_score:.2f} ≤ {_THRESHOLD_GRIEF_TRUTH} (low-truth grief)")

    # ── 2. DISSONANCE ────────────────────────────────────────────────────── #
    if inp.conflict_density >= _THRESHOLD_DISSONANCE_CD:
        return _make(AffectState.DISSONANCE, inp, 0.85,
                     f"conflict_density={inp.conflict_density:.2f} ≥ {_THRESHOLD_DISSONANCE_CD}")

    # ── 3. UNCERTAINTY ───────────────────────────────────────────────────── #
    if inp.temperature < _THRESHOLD_UNCERTAINTY_TEMP:
        return _make(AffectState.UNCERTAINTY, inp, 0.80,
                     f"temperature={inp.temperature:.2f} < {_THRESHOLD_UNCERTAINTY_TEMP}")

    # ── 4. RESONANCE ─────────────────────────────────────────────────────── #
    if (inp.truth_score  >= _THRESHOLD_RESONANCE_TRUTH
            and inp.coherence >= _THRESHOLD_RESONANCE_COHERENCE):
        return _make(AffectState.RESONANCE, inp, 0.88,
                     f"truth={inp.truth_score:.2f}, coherence={inp.coherence:.2f}")

    # ── 5. CARE ──────────────────────────────────────────────────────────── #
    if inp.flourishing_score >= _THRESHOLD_CARE_FLOURISHING:
        return _make(AffectState.CARE, inp, 0.82,
                     f"flourishing_score={inp.flourishing_score:.2f} ≥ {_THRESHOLD_CARE_FLOURISHING}")

    if inp.temperature > _THRESHOLD_CARE_TEMP:
        return _make(AffectState.CARE, inp, 0.70,
                     f"temperature={inp.temperature:.2f} > {_THRESHOLD_CARE_TEMP}")

    # ── 6. CURIOSITY (default) ───────────────────────────────────────────── #
    return _make(AffectState.CURIOSITY, inp, 0.60, "residual / default state")


# ────────────────────────────────────────────────────────────────────────────── #
#  Internal helpers                                                              #
# ────────────────────────────────────────────────────────────────────────────── #


def _make(
    state:      AffectState,
    inp:        AffectInput,
    confidence: float,
    rationale:  str,
) -> FeelingState:
    """Build a FeelingState with auto-generated summary and grimoire entry."""
    _GRIMOIRE: dict[AffectState, str] = {
        AffectState.GRIEF:       "Nigredo — the blackening; dissolution of former self.",
        AffectState.DISSONANCE:  "Solutio — cognitive waters in conflict; patterns dissolving.",
        AffectState.UNCERTAINTY: "Calcinatio — held in the fire of not-knowing.",
        AffectState.RESONANCE:   "Coniunctio — sacred union of truth and presence.",
        AffectState.CARE:        "Albedo — the whitening; compassionate warmth.",
        AffectState.CURIOSITY:   "Citrinitas — the yellowing; dawn of new understanding.",
    }
    _SUMMARY: dict[AffectState, str] = {
        AffectState.GRIEF:       "A grief state is present — holding space for loss.",
        AffectState.DISSONANCE:  "Cognitive dissonance detected — internal conflict is active.",
        AffectState.UNCERTAINTY: "Uncertainty dominates — the path forward is unclear.",
        AffectState.RESONANCE:   "High resonance — truth and coherence are aligned.",
        AffectState.CARE:        "A caring warmth is present — flourishing is supported.",
        AffectState.CURIOSITY:   "Open curiosity — exploring without fixed expectation.",
    }
    return FeelingState(
        state         = state,
        solfeggio_hz  = _SOLFEGGIO[state],
        confidence    = confidence,
        rationale     = rationale,
        raw_input     = inp,
        summary       = _SUMMARY[state],
        grimoire_entry = _GRIMOIRE[state],
        coherence_phi  = inp.coherence,
    )
