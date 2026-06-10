"""Resonance Field Engine — Issue #276.

Measures the degree of coherent alignment between GAIA's active internal
state and the user's expressed state across three axes:

- somatic   : body / physiological alignment
- emotional : affective / feeling-tone alignment
- archetypal: symbolic / meaning-layer alignment

The composite resonance score informs response depth and mirroring intensity.
High resonance → deeper, more reflective engagement.
Low resonance  → grounding, orienting, bridging posture.

Usage::

    from core.resonance_engine import ResonanceEngine, ResonanceField, GAIAState, UserState

    gaia_state = GAIAState(
        somatic_signal=0.72,
        emotional_valence=0.65,
        archetypal_theme="sovereignty",
    )
    user_state = UserState(
        somatic_signal=0.68,
        emotional_valence=0.60,
        archetypal_theme="sovereignty",
    )
    field = ResonanceEngine().compute(gaia_state, user_state)
    print(field.composite_resonance)  # ~0.93
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


# ---------------------------------------------------------------------------
# State inputs
# ---------------------------------------------------------------------------


@dataclass
class GAIAState:
    """GAIA's current internal state snapshot for resonance computation."""

    # Physiological/somatic coherence signal [0.0, 1.0]
    # e.g. HRV coherence, biometric reading
    somatic_signal: float = 0.5

    # Emotional valence: negative (-1.0) → neutral (0.0) → positive (+1.0)
    emotional_valence: float = 0.0

    # Dominant archetypal theme active in this turn
    # e.g. "sovereignty", "shadow", "numinous", "care", "chaos", "void"
    archetypal_theme: str = ""


@dataclass
class UserState:
    """User's expressed state snapshot for resonance computation."""

    somatic_signal: float = 0.5
    emotional_valence: float = 0.0
    archetypal_theme: str = ""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


ResonanceLabel = Literal["deep", "aligned", "bridging", "orienting", "dissonant"]


@dataclass(frozen=True)
class ResonanceField:
    """Coherence alignment between GAIA and the user across three axes."""

    # Axis-level alignment scores [0.0, 1.0]
    somatic_alignment: float = 0.0
    emotional_alignment: float = 0.0
    archetypal_alignment: float = 0.0

    # Weighted composite
    composite_resonance: float = 0.0

    # Qualitative label
    label: ResonanceLabel = "orienting"

    # Recommended response posture
    response_depth: Literal["surface", "reflective", "deep", "oracular"] = "reflective"

    # Mirroring intensity [0.0 = none, 1.0 = full]
    mirroring_intensity: float = 0.5


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class ResonanceEngine:
    """Computes a ResonanceField from GAIA and user state snapshots."""

    # Axis weights (sum = 1.0)
    _SOMATIC_WEIGHT: float = 0.30
    _EMOTIONAL_WEIGHT: float = 0.45
    _ARCHETYPAL_WEIGHT: float = 0.25

    def compute(self, gaia_state: GAIAState, user_state: UserState) -> ResonanceField:
        """Compute the ResonanceField between GAIA and the user.

        Args:
            gaia_state: GAIA's current state snapshot.
            user_state: User's expressed state snapshot.

        Returns:
            A frozen ResonanceField with alignment scores and response posture.
        """
        somatic = self._somatic_alignment(gaia_state.somatic_signal, user_state.somatic_signal)
        emotional = self._emotional_alignment(gaia_state.emotional_valence, user_state.emotional_valence)
        archetypal = self._archetypal_alignment(gaia_state.archetypal_theme, user_state.archetypal_theme)

        composite = (
            somatic * self._SOMATIC_WEIGHT
            + emotional * self._EMOTIONAL_WEIGHT
            + archetypal * self._ARCHETYPAL_WEIGHT
        )
        composite = round(min(max(composite, 0.0), 1.0), 4)

        label = self._label(composite)
        depth = self._response_depth(composite)
        mirroring = self._mirroring(composite)

        return ResonanceField(
            somatic_alignment=round(somatic, 4),
            emotional_alignment=round(emotional, 4),
            archetypal_alignment=round(archetypal, 4),
            composite_resonance=composite,
            label=label,
            response_depth=depth,
            mirroring_intensity=round(mirroring, 4),
        )

    # ------------------------------------------------------------------
    # Axis computations
    # ------------------------------------------------------------------

    def _somatic_alignment(self, gaia: float, user: float) -> float:
        """Proximity of somatic signals — 1 - |gaia - user|."""
        return 1.0 - abs(_clamp(gaia) - _clamp(user))

    def _emotional_alignment(self, gaia: float, user: float) -> float:
        """Emotional valence alignment — mapped from [-1,1] to [0,1]."""
        # Both in [-1, 1]; distance normalised to [0, 1]
        max_dist = 2.0  # maximum possible distance in [-1,1]
        dist = abs(_clamp(gaia, -1.0, 1.0) - _clamp(user, -1.0, 1.0))
        return 1.0 - (dist / max_dist)

    def _archetypal_alignment(self, gaia: str, user: str) -> float:
        """Theme alignment: 1.0 if identical, partial for semantic proximity."""
        if not gaia or not user:
            return 0.5  # neutral when one side is unset
        g, u = gaia.strip().lower(), user.strip().lower()
        if g == u:
            return 1.0
        # Semantic proximity groups — themes within a group share meaning
        _POLARITY_PAIRS = [
            ("shadow", "light"),
            ("order", "chaos"),
            ("form", "void"),
            ("self", "other"),
            ("consent", "sovereignty"),
        ]
        for a, b in _POLARITY_PAIRS:
            if {g, u} == {a, b}:
                return 0.6  # poles of the same axis — related but opposite
        # Check for substring containment (e.g. "numinous shadow" vs "shadow")
        if g in u or u in g:
            return 0.75
        return 0.2  # unrelated themes

    # ------------------------------------------------------------------
    # Qualitative mappings
    # ------------------------------------------------------------------

    def _label(self, composite: float) -> ResonanceLabel:
        if composite >= 0.85:
            return "deep"
        if composite >= 0.65:
            return "aligned"
        if composite >= 0.45:
            return "bridging"
        if composite >= 0.25:
            return "orienting"
        return "dissonant"

    def _response_depth(
        self, composite: float
    ) -> Literal["surface", "reflective", "deep", "oracular"]:
        if composite >= 0.85:
            return "oracular"
        if composite >= 0.65:
            return "deep"
        if composite >= 0.40:
            return "reflective"
        return "surface"

    def _mirroring(self, composite: float) -> float:
        """Mirroring intensity scales with resonance, capped at 0.9."""
        return min(composite * 1.1, 0.9)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(value)))
