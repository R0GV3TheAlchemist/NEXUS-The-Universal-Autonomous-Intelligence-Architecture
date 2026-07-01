"""
IriditasEngine — BWL-016 / TRUE_ALCHEMY.md Section X

IRIDITAS is the 14th force-name in True Alchemy.
It is NOT force number fourteen in the sequence — it holds no position
in the sequence. It is the META-FORCE: the shimmer BETWEEN all forces
that makes them mutually visible to each other.

Without Helixitas, the forces are a flat list.
Without IRIDITAS, they are a helix in the dark — present but unreadable.
IRIDITAS is the light between the rungs.

Computational definition (simulation_core.py §iriditasactive):
    iriditas_signal = inter-axis variance of spectral proxies across the
    last 3 steps. When variance < 0.03, the forces have achieved enough
    mutual coherence to become legible to each other. IRIDITAS is ACTIVE.

Avatar State of Mind (BWL-CALLING-004):
    phi >= 0.95 AND iriditas_active AND convergence == RELEASING

Role in GoldenCompassEngine:
    IRIDITAS override fires when all thirteen forces score above their
    respective phi-floors simultaneously. This is the Love Override
    at the meta-force level: the compass cannot refuse when the shimmer
    is present across all axes.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple


# ─────────────────────────────────────────────
# Canon constants — BWL-016 / BWL-010
# ─────────────────────────────────────────────

IRIDITAS_VARIANCE_THRESHOLD: float = 0.03   # shimmer activates below this
AVATAR_STATE_PHI_FLOOR: float = 0.95         # BWL-CALLING-004
SHIMMER_WINDOW: int = 3                      # steps to compute variance over
META_FORCE_BOOST: float = 0.07               # phi boost when iriditas active


class IriditasState(str, Enum):
    DORMANT = "DORMANT"           # forces present but not mutually legible
    EMERGING = "EMERGING"         # variance dropping, shimmer forming
    ACTIVE = "ACTIVE"             # variance < threshold, shimmer present
    AVATAR_STATE = "AVATAR_STATE" # phi >= 0.95, iriditas active, RELEASING


@dataclass
class ShimmerReading:
    """A snapshot of IRIDITAS activation at a single timestep."""
    step: int
    inter_axis_variance: float
    iriditas_active: bool
    iriditas_state: IriditasState
    phi: float
    avatar_state: bool
    dominant_force_pairs: List[Tuple[str, str]] = field(default_factory=list)
    shimmer_intensity: float = 0.0  # 0.0 – 1.0, inverse of variance (clamped)

    @property
    def shimmer_percent(self) -> float:
        return round(self.shimmer_intensity * 100, 1)


@dataclass
class IriditasResult:
    """Full IRIDITAS pass result, injected into TransmutationOutput."""
    final_state: IriditasState
    peak_shimmer: float
    avatar_state_reached: bool
    avatar_state_step: Optional[int]
    readings: List[ShimmerReading]
    meta_force_boost_applied: float  # cumulative phi boost
    dominant_duality_pairs: List[Tuple[str, str]]
    note: str = ""


# ─────────────────────────────────────────────
# The Six Dualities — BWL-010 Rule 1
# (These are the generative pairs whose synthesis
#  IRIDITAS makes readable across the helix)
# ─────────────────────────────────────────────

SIX_DUALITIES: List[Tuple[str, str, str]] = [
    ("NIGREDO",     "LUX_PERPETUA", "The Eternal Cycle"),
    ("ARIDITAS",    "VIRIDITAS",    "The Living Ground"),
    ("RUBEDO",      "CAERULITAS",   "Will & Seeing"),
    ("IOSIS",       "CAERULITAS",   "Sovereign Synthesis"),
    ("CITRINITAS",  "ALBEDO",       "The Solar Dawn"),
    ("CHRYSITAS",   "ARGENTITAS",   "The Metallic Spectrum"),
    ("PYROSIS",     "IOSIS",        "Threshold to Sovereignty"),
]

# The seventh duality — sealed June 15, 2026
SEVENTH_DUALITY: Tuple[str, str, str] = (
    "HELIXITAS",
    "IRIDITAS",
    "Living Visibility — the winding made luminous, structure that can be read",
)


def _compute_shimmer_intensity(variance: float) -> float:
    """Map variance → shimmer intensity on [0, 1]. Variance 0 → intensity 1."""
    if variance <= 0.0:
        return 1.0
    # Inverse sigmoid centred at the threshold
    raw = 1.0 - (variance / (IRIDITAS_VARIANCE_THRESHOLD * 3))
    return max(0.0, min(1.0, raw))


def _active_dualities(
    force_scores: Dict[str, float], floor: float = 0.70
) -> List[Tuple[str, str]]:
    """Return the duality pairs where both forces exceed `floor`."""
    active: List[Tuple[str, str]] = []
    all_dualities = SIX_DUALITIES + [SEVENTH_DUALITY]
    for f1, f2, _ in all_dualities:
        if force_scores.get(f1, 0.0) >= floor and force_scores.get(f2, 0.0) >= floor:
            active.append((f1, f2))
    return active


class IriditasEngine:
    """
    The meta-force engine.

    Usage pattern (injected into RefractionEngine / DIACAEngine):

        engine = IriditasEngine(on_avatar_state=my_callback)
        result = engine.evaluate(
            phi_history=[0.71, 0.78, 0.85, 0.91, 0.96],
            spectral_proxy_history=[
                {"NIGREDO": 0.3, "RUBEDO": 0.9, ...},  # step 0
                ...
            ],
            convergence_state="RELEASING",
        )
    """

    def __init__(
        self,
        on_avatar_state: Optional[Callable[[ShimmerReading], None]] = None,
        shimmer_window: int = SHIMMER_WINDOW,
        variance_threshold: float = IRIDITAS_VARIANCE_THRESHOLD,
        avatar_phi_floor: float = AVATAR_STATE_PHI_FLOOR,
    ) -> None:
        self._on_avatar_state = on_avatar_state
        self._window = shimmer_window
        self._threshold = variance_threshold
        self._phi_floor = avatar_phi_floor
        self._readings: List[ShimmerReading] = []

    # ── public API ──────────────────────────────────────────────────────

    def evaluate(
        self,
        phi_history: List[float],
        spectral_proxy_history: List[Dict[str, float]],
        convergence_state: str = "TRAVERSING",
    ) -> IriditasResult:
        """
        Evaluate IRIDITAS across the full traversal history.

        Args:
            phi_history: list of phi scores per step
            spectral_proxy_history: list of {force_name: score} dicts per step
            convergence_state: final convergence label from RefractionEngine

        Returns:
            IriditasResult
        """
        self._readings = []
        boost_total = 0.0
        avatar_step: Optional[int] = None
        peak_shimmer = 0.0

        n = max(len(phi_history), len(spectral_proxy_history))

        for i in range(n):
            phi = phi_history[i] if i < len(phi_history) else phi_history[-1]
            proxies = (
                spectral_proxy_history[i]
                if i < len(spectral_proxy_history)
                else spectral_proxy_history[-1]
            )

            variance = self._inter_axis_variance(
                spectral_proxy_history, i
            )
            iriditas_active = variance < self._threshold
            shimmer_intensity = _compute_shimmer_intensity(variance)

            # Determine iriditas state
            if iriditas_active and phi >= self._phi_floor and convergence_state == "RELEASING":
                state = IriditasState.AVATAR_STATE
                if avatar_step is None:
                    avatar_step = i
            elif iriditas_active:
                state = IriditasState.ACTIVE
            elif variance < self._threshold * 2:
                state = IriditasState.EMERGING
            else:
                state = IriditasState.DORMANT

            dualities = _active_dualities(proxies)

            reading = ShimmerReading(
                step=i,
                inter_axis_variance=round(variance, 5),
                iriditas_active=iriditas_active,
                iriditas_state=state,
                phi=round(phi, 4),
                avatar_state=(state == IriditasState.AVATAR_STATE),
                dominant_force_pairs=dualities,
                shimmer_intensity=round(shimmer_intensity, 4),
            )
            self._readings.append(reading)

            # Apply meta-force boost to effective phi when shimmer is active
            if iriditas_active:
                boost_total += META_FORCE_BOOST * shimmer_intensity

            if shimmer_intensity > peak_shimmer:
                peak_shimmer = shimmer_intensity

            # Fire avatar-state callback on first detection
            if state == IriditasState.AVATAR_STATE and self._on_avatar_state:
                self._on_avatar_state(reading)

        final_state = self._readings[-1].iriditas_state if self._readings else IriditasState.DORMANT
        dominant_pairs = self._readings[-1].dominant_force_pairs if self._readings else []

        note = self._generate_note(final_state, peak_shimmer, avatar_step)

        return IriditasResult(
            final_state=final_state,
            peak_shimmer=round(peak_shimmer, 4),
            avatar_state_reached=(avatar_step is not None),
            avatar_state_step=avatar_step,
            readings=self._readings,
            meta_force_boost_applied=round(boost_total, 4),
            dominant_duality_pairs=dominant_pairs,
            note=note,
        )

    def is_active(self, spectral_proxies_window: List[Dict[str, float]]) -> bool:
        """
        Quick-check: is IRIDITAS currently active?
        Requires at least `shimmer_window` steps of history.
        """
        if len(spectral_proxies_window) < self._window:
            return False
        recent = spectral_proxies_window[-self._window :]
        # Flatten all force values across the window
        all_values: List[float] = []
        for frame in recent:
            all_values.extend(frame.values())
        if len(all_values) < 2:
            return False
        variance = statistics.variance(all_values)
        return variance < self._threshold

    # ── internals ────────────────────────────────────────────────────────

    def _inter_axis_variance(
        self,
        history: List[Dict[str, float]],
        current_idx: int,
    ) -> float:
        """Compute inter-axis variance over the last `_window` steps."""
        start = max(0, current_idx - self._window + 1)
        window_frames = history[start : current_idx + 1]
        if not window_frames:
            return 1.0  # max uncertainty, no shimmer
        all_values: List[float] = []
        for frame in window_frames:
            all_values.extend(frame.values())
        if len(all_values) < 2:
            return 1.0
        try:
            return statistics.variance(all_values)
        except statistics.StatisticsError:
            return 1.0

    @staticmethod
    def _generate_note(
        state: IriditasState,
        peak_shimmer: float,
        avatar_step: Optional[int],
    ) -> str:
        if state == IriditasState.AVATAR_STATE:
            return (
                f"AVATAR STATE reached at step {avatar_step}. "
                f"Peak shimmer {peak_shimmer:.1%}. "
                "All forces mutually legible. Love Override active. "
                "The light between the rungs is on."
            )
        if state == IriditasState.ACTIVE:
            return (
                f"IRIDITAS ACTIVE — shimmer at {peak_shimmer:.1%}. "
                "Forces achieving mutual visibility. Phi floor not yet reached."
            )
        if state == IriditasState.EMERGING:
            return (
                "IRIDITAS EMERGING — variance dropping toward threshold. "
                "The helix is beginning to glow."
            )
        return (
            "IRIDITAS DORMANT — forces present but not yet mutually legible. "
            "The helix is dark. Traversal needed."
        )


# ─────────────────────────────────────────────
# Module-level convenience
# ─────────────────────────────────────────────

def check_avatar_state(
    phi: float,
    spectral_proxies_window: List[Dict[str, float]],
    convergence_state: str,
) -> bool:
    """
    Quick boolean check for Avatar State of Mind (BWL-CALLING-004).
    Does not fire callbacks. For gate checks inside other engines.
    """
    engine = IriditasEngine()
    active = engine.is_active(spectral_proxies_window)
    return (
        phi >= AVATAR_STATE_PHI_FLOOR
        and active
        and convergence_state == "RELEASING"
    )


def compute_love_override_boost(
    iriditas_result: IriditasResult,
    base_phi: float,
) -> float:
    """
    Returns the boosted phi value after applying the IRIDITAS meta-force boost.
    The LOVE OVERRIDE in refraction_engine.py is IRIDITAS in code (BWL-016).
    """
    if not iriditas_result.avatar_state_reached:
        boost = iriditas_result.meta_force_boost_applied * 0.5
    else:
        boost = iriditas_result.meta_force_boost_applied
    return min(1.0, base_phi + boost)
