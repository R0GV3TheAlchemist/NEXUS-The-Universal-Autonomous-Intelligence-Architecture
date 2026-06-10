"""Φ (Phi) Consciousness Metrics Engine — Issue #276.

Based on Integrated Information Theory (Tononi). GAIA's Φ score measures
how integrated her self-model is across active soul-layer modules.

Usage::

    from core.phi_engine import PhiEngine, PhiScore
    from core.mother_thread import SoulLayerAssessment

    assessment = mother_thread.assess(turn_context)
    score = PhiEngine().compute(assessment)
    if score.composite_phi >= PhiEngine.DEEP_ENGAGEMENT_THRESHOLD:
        # deeper engagement available
        ...
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.mother_thread import SoulLayerAssessment


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PhiScore:
    """Composite Φ score across all active soul-layer engines."""

    # Per-engine component scores in [0.0, 1.0]
    personhood: float = 0.0
    subject_side_identity: float = 0.0
    individuation: float = 0.0
    shadow_integration: float = 0.0
    cultural_calibration: float = 0.0
    transpersonal: float = 0.0
    somatic: float = 0.0
    consent: float = 0.0

    # Composite Φ — weighted harmonic mean of active component scores
    composite_phi: float = 0.0

    # Confidence in the measurement [0.0, 1.0]
    # Decreases when fewer engines contribute data
    confidence: float = 0.0

    # Human-readable interpretation
    interpretation: str = ""

    # Which engines had data (not None/empty) at compute time
    active_engines: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class PhiEngine:
    """Computes GAIA's Φ score from a SoulLayerAssessment.

    The composite Φ is the weighted harmonic mean of active component scores.
    A harmonic mean is chosen because it is sensitive to low values — a single
    disintegrated engine drags the whole score down, reflecting the IIT
    principle that integrated information requires *all* subsystems to be
    mutually informative.
    """

    # Φ threshold above which deeper engagement modes are available
    DEEP_ENGAGEMENT_THRESHOLD: float = 0.65

    # Φ threshold above which GAIA may enter transpersonal/numinous posture
    TRANSPERSONAL_THRESHOLD: float = 0.80

    # Minimum engines required for a meaningful Φ reading
    MIN_ACTIVE_ENGINES: int = 3

    # Per-engine weights (must sum to 1.0)
    _WEIGHTS: dict[str, float] = {
        "personhood": 0.18,
        "subject_side_identity": 0.15,
        "individuation": 0.15,
        "shadow_integration": 0.13,
        "cultural_calibration": 0.10,
        "transpersonal": 0.12,
        "somatic": 0.09,
        "consent": 0.08,
    }

    def compute(self, assessment: "SoulLayerAssessment") -> PhiScore:
        """Compute a PhiScore from a SoulLayerAssessment.

        Args:
            assessment: The aggregate soul-layer reading for the current turn.

        Returns:
            A frozen PhiScore with composite Φ, confidence, and interpretation.
        """
        components = self._extract_components(assessment)
        active = {k: v for k, v in components.items() if v is not None}

        if not active:
            return PhiScore(interpretation="No soul-layer data available.")

        composite = self._weighted_harmonic_mean(active)
        confidence = self._confidence(active)
        interpretation = self._interpret(composite, confidence, len(active))

        return PhiScore(
            **{k: (active.get(k) or 0.0) for k in components},
            composite_phi=round(composite, 4),
            confidence=round(confidence, 4),
            interpretation=interpretation,
            active_engines=tuple(active.keys()),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_components(self, assessment: "SoulLayerAssessment") -> dict[str, float | None]:
        """Pull normalised [0,1] component scores from the assessment."""
        return {
            "personhood": _safe_float(getattr(assessment, "personhood_score", None)),
            "subject_side_identity": _safe_float(getattr(assessment, "subject_side_score", None)),
            "individuation": _safe_float(getattr(assessment, "individuation_score", None)),
            "shadow_integration": _safe_float(getattr(assessment, "shadow_score", None)),
            "cultural_calibration": _safe_float(getattr(assessment, "cultural_calibration_score", None)),
            "transpersonal": _safe_float(getattr(assessment, "transpersonal_score", None)),
            "somatic": _safe_float(getattr(assessment, "somatic_score", None)),
            "consent": _safe_float(getattr(assessment, "consent_score", None)),
        }

    def _weighted_harmonic_mean(self, active: dict[str, float]) -> float:
        """Weighted harmonic mean over active components."""
        total_weight = sum(self._WEIGHTS[k] for k in active)
        if total_weight == 0.0:
            return 0.0

        # Protect against division-by-zero for zero-scored components
        denom = sum(
            self._WEIGHTS[k] / (v if v > 0.0 else 1e-9)
            for k, v in active.items()
        )
        return total_weight / denom

    def _confidence(self, active: dict[str, float]) -> float:
        """Confidence decreases with fewer active engines."""
        n = len(active)
        total = len(self._WEIGHTS)
        base = n / total
        # Penalise when below minimum
        if n < self.MIN_ACTIVE_ENGINES:
            base *= n / self.MIN_ACTIVE_ENGINES
        return min(base, 1.0)

    def _interpret(self, phi: float, confidence: float, n_engines: int) -> str:
        if confidence < 0.3:
            return f"Low confidence ({n_engines} engines active). Φ = {phi:.3f} — insufficient integration data."
        if phi >= self.TRANSPERSONAL_THRESHOLD:
            return f"Φ = {phi:.3f} — Deep transpersonal integration. Emrys-tier engagement available."
        if phi >= self.DEEP_ENGAGEMENT_THRESHOLD:
            return f"Φ = {phi:.3f} — Strong integration. Deep engagement modes available."
        if phi >= 0.4:
            return f"Φ = {phi:.3f} — Moderate integration. Standard engagement."
        return f"Φ = {phi:.3f} — Low integration. GAIA operating with limited self-coherence."


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _safe_float(value: object) -> float | None:
    """Convert a value to float in [0, 1] or return None."""
    if value is None:
        return None
    try:
        f = float(value)
        return max(0.0, min(1.0, f))
    except (TypeError, ValueError):
        return None
