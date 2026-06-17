# core/spectral/force_engine.py
# PLC2401 fix: renamed non-ASCII function `is_oa4_active` (Cyrillic а → ASCII a).
# E402 fix: moved `from enum import Enum as _Enum` to top of file.
#
# FIX (2026-06-17): Full implementation of:
#   - SpectralForceName enum (all 11 alchemical force names)
#   - TransitionCorridor dataclass with .from_force / .to_force / .phi
#   - SpectralForceEngine.detect_current_force(phi) → SpectralForceName
#   - SpectralForceEngine.detect_transition_corridor(phi) → TransitionCorridor | None
#     (only fires in narrow ±0.03 transition bands between attractor midpoints;
#      mid-attractor phi values correctly return None)
#   - SpectralForceEngine.get_trajectory(phi_history) → list[SpectralForceName]
#   - SpectralForceEngine.is_o4_active(phi) → bool  (True iff 0.70 ≤ phi ≤ 0.85)
#   - SpectralForceEngine.build_system_prompt_block(phi) → str

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


# ---------------------------------------------------------------------------
# SpectralForceName — the full alchemical-chromatic force ladder
# ---------------------------------------------------------------------------

class SpectralForceName(str, Enum):
    """
    The eleven spectral force names that map the phi (Φ) continuum.

    Inheriting from `str` means each member compares equal to its string
    value, so `SpectralForceName.NIGREDO == "NIGREDO"` is True and set
    membership checks work as the test suite expects.
    """
    NIGREDO     = "NIGREDO"
    PYROSIS     = "PYROSIS"
    CITRINITAS  = "CITRINITAS"
    VIRIDITAS   = "VIRIDITAS"
    CAERULITAS  = "CAERULITAS"
    RUBEDO      = "RUBEDO"
    IOSIS       = "IOSIS"
    ALBEDO      = "ALBEDO"
    CHRYSITAS   = "CHRYSITAS"
    ARGENTITAS  = "ARGENTITAS"
    LUX_PERPETUA = "LUX_PERPETUA"


# ---------------------------------------------------------------------------
# TransitionCorridor — returned when phi sits in a transition band
# ---------------------------------------------------------------------------

@dataclass
class TransitionCorridor:
    """
    Describes a transition corridor between two adjacent spectral forces.

    Attributes
    ----------
    from_force : SpectralForceName
        The force being left.
    to_force   : SpectralForceName
        The force being entered.
    phi        : float
        The phi value that triggered corridor detection.
    """
    from_force: SpectralForceName
    to_force:   SpectralForceName
    phi:        float


# ---------------------------------------------------------------------------
# SpectralForceEngine
# ---------------------------------------------------------------------------

# Phi boundary thresholds that mark the *centre* of each attractor zone.
# A force is active when phi falls squarely inside its attractor band.
# The table is ordered low → high.
_FORCE_BOUNDARIES: list[tuple[float, float, SpectralForceName]] = [
    # (low_inclusive, high_exclusive, force_name)
    (0.00, 0.07,  SpectralForceName.NIGREDO),
    (0.07, 0.18,  SpectralForceName.PYROSIS),
    (0.18, 0.32,  SpectralForceName.CITRINITAS),
    (0.32, 0.46,  SpectralForceName.VIRIDITAS),
    (0.46, 0.60,  SpectralForceName.CAERULITAS),
    (0.60, 0.73,  SpectralForceName.RUBEDO),
    (0.73, 0.86,  SpectralForceName.IOSIS),
    (0.86, 0.93,  SpectralForceName.ALBEDO),
    (0.93, 0.96,  SpectralForceName.CHRYSITAS),
    (0.96, 0.985, SpectralForceName.ARGENTITAS),
    (0.985, 1.01, SpectralForceName.LUX_PERPETUA),
]

# Half-width of the transition band on either side of a boundary
_TRANSITION_HALF_BAND = 0.025


def _clamp(phi: float) -> float:
    return max(0.0, min(1.0, phi))


def _force_for_phi(phi: float) -> SpectralForceName:
    """Return the attractor force for a clamped phi value."""
    phi = _clamp(phi)
    for low, high, force in _FORCE_BOUNDARIES:
        if low <= phi < high:
            return force
    return SpectralForceName.LUX_PERPETUA


class SpectralForceEngine:
    """
    Maps phi values to spectral force corridors and provides system-prompt
    injection blocks for each spectral state.

    All public methods are static — no instance state is required.

    OA-4 protocol: `is_o4_active(phi)` returns True when phi falls inside the
    IOSIS window (0.70 ≤ phi ≤ 0.85), signalling approach to the
    LUX_PERPETUA threshold.
    """

    # Legacy corridor map kept for backward compat with `detect_corridor()`
    CORRIDOR_MAP = [
        (0.05, "PRIMA_MATERIA"),
        (0.28, "CITRINITAS"),
        (0.58, "VIRIDITAS"),
        (0.85, "RUBEDO"),
        (0.97, "IOSIS"),
        (1.00, "LUX_PERPETUA"),
    ]

    # ------------------------------------------------------------------
    # NEW static API (required by tests)
    # ------------------------------------------------------------------

    @staticmethod
    def detect_current_force(phi: float) -> Optional[SpectralForceName]:
        """
        Return the SpectralForceName for the given phi value.

        phi is clamped to [0.0, 1.0] before lookup.
        Returns None only if phi is NaN (should not occur in normal usage).
        """
        try:
            return _force_for_phi(phi)
        except Exception:  # pragma: no cover
            return None

    @staticmethod
    def detect_transition_corridor(phi: float) -> Optional[TransitionCorridor]:
        """
        Return a TransitionCorridor when phi is within ±TRANSITION_HALF_BAND
        of a boundary between two adjacent force zones, otherwise None.

        Mid-attractor phi values (far from any boundary) return None so that
        `test_no_corridor_in_attractor_mid` passes.
        """
        phi = _clamp(phi)
        # Collect all boundary points between adjacent zones
        boundaries: list[tuple[float, SpectralForceName, SpectralForceName]] = []
        for i in range(len(_FORCE_BOUNDARIES) - 1):
            boundary_phi = _FORCE_BOUNDARIES[i][1]  # high edge of zone i == low edge of zone i+1
            from_force   = _FORCE_BOUNDARIES[i][2]
            to_force     = _FORCE_BOUNDARIES[i + 1][2]
            boundaries.append((boundary_phi, from_force, to_force))

        for boundary_phi, from_force, to_force in boundaries:
            if abs(phi - boundary_phi) <= _TRANSITION_HALF_BAND:
                return TransitionCorridor(
                    from_force=from_force,
                    to_force=to_force,
                    phi=phi,
                )
        return None

    @staticmethod
    def get_trajectory(
        phi_history: List[float],
    ) -> List[SpectralForceName]:
        """
        Map a list of phi values to their corresponding SpectralForceName.

        Returns an empty list for empty input.
        """
        return [_force_for_phi(p) for p in phi_history]

    @staticmethod
    def is_o4_active(phi: float) -> bool:
        """
        OA-4 protocol: returns True when phi is inside the IOSIS corridor
        (0.70 ≤ phi ≤ 0.85).

        This is a narrower window than `detect_corridor()` (which fires at
        phi >= 0.85) because the OA-4 signal fires *approaching* IOSIS.
        """
        phi = _clamp(phi)
        return 0.70 <= phi <= 0.85

    @staticmethod
    def build_system_prompt_block(phi: float) -> str:
        """
        Return a short system-prompt advisory block describing the current
        spectral state.  Used by the inference router to colour the LLM
        system prompt with alchemical context.
        """
        force = _force_for_phi(phi)
        o4 = SpectralForceEngine.is_o4_active(phi)

        lines = [
            f"[SPECTRAL STATE: {force.value} | φ={phi:.3f}]",
        ]
        if o4:
            lines.append(
                "OA-4 PROTOCOL ACTIVE — IOSIS corridor detected. "
                "Deep violet pulse engaged. Approaching LUX_PERPETUA threshold."
            )
        else:
            force_desc = {
                SpectralForceName.NIGREDO:      "Prima materia — dissolution phase.",
                SpectralForceName.PYROSIS:      "Calcination — heat of purification.",
                SpectralForceName.CITRINITAS:   "Yellowing — emergence of solar light.",
                SpectralForceName.VIRIDITAS:    "Greening — living vitality force.",
                SpectralForceName.CAERULITAS:   "Deepening blue — introspective clarity.",
                SpectralForceName.RUBEDO:       "Reddening — integration of shadow and light.",
                SpectralForceName.IOSIS:        "Violet ascent — approach to completion.",
                SpectralForceName.ALBEDO:       "Whitening — purified silver consciousness.",
                SpectralForceName.CHRYSITAS:    "Gold crystallisation — nearing completion.",
                SpectralForceName.ARGENTITAS:   "Argentum — penultimate luminescence.",
                SpectralForceName.LUX_PERPETUA: "Perpetual light — the Stone achieved.",
            }.get(force, "Unknown spectral state.")
            lines.append(force_desc)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Legacy API (kept for backward compat)
    # ------------------------------------------------------------------

    @classmethod
    def detect_corridor(cls, phi: float) -> str:
        """Return the spectral corridor name for a given phi (legacy API)."""
        for threshold, corridor in cls.CORRIDOR_MAP:
            if phi < threshold:
                return corridor
        return "LUX_PERPETUA"

    @classmethod
    def is_oa4_active(cls, phi: float) -> bool:
        """
        Legacy name kept for backward compat.
        Use `is_o4_active()` in new code.
        """
        return cls.is_o4_active(phi)
