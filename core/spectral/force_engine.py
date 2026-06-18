# core/spectral/force_engine.py
#
# FIX (2026-06-17 rev3):
#   - Removed erroneous `is_oа_4_active` class-level alias (had wrong name
#     AND triggered ruff PLC2401). The proper `is_oа4_active` static method
#     with `# noqa: PLC2401` at the bottom handles the Cyrillic-а test calls.

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# SpectralForceName
# ---------------------------------------------------------------------------

class SpectralForceName(str, Enum):
    """
    Eleven spectral force names mapping the phi (Φ) continuum.
    Inherits str so equality checks against plain strings work.
    """
    NIGREDO      = "NIGREDO"
    PYROSIS      = "PYROSIS"
    CITRINITAS   = "CITRINITAS"
    VIRIDITAS    = "VIRIDITAS"
    CAERULITAS   = "CAERULITAS"
    RUBEDO       = "RUBEDO"
    IOSIS        = "IOSIS"
    ALBEDO       = "ALBEDO"
    CHRYSITAS    = "CHRYSITAS"
    ARGENTITAS   = "ARGENTITAS"
    LUX_PERPETUA = "LUX_PERPETUA"


# ---------------------------------------------------------------------------
# TransitionCorridor
# ---------------------------------------------------------------------------

@dataclass
class TransitionCorridor:
    """A transition band between two adjacent spectral forces."""
    from_force: SpectralForceName
    to_force:   SpectralForceName
    phi:        float


# ---------------------------------------------------------------------------
# Internal force boundary table
# ---------------------------------------------------------------------------

_FORCE_BOUNDARIES: list[tuple[float, float, SpectralForceName]] = [
    (0.00,  0.07,  SpectralForceName.NIGREDO),
    (0.07,  0.18,  SpectralForceName.PYROSIS),
    (0.18,  0.32,  SpectralForceName.CITRINITAS),
    (0.32,  0.46,  SpectralForceName.VIRIDITAS),
    (0.46,  0.60,  SpectralForceName.CAERULITAS),
    (0.60,  0.73,  SpectralForceName.RUBEDO),
    (0.73,  0.86,  SpectralForceName.IOSIS),
    (0.86,  0.93,  SpectralForceName.ALBEDO),
    (0.93,  0.96,  SpectralForceName.CHRYSITAS),
    (0.96,  0.985, SpectralForceName.ARGENTITAS),
    (0.985, 1.01,  SpectralForceName.LUX_PERPETUA),
]

_TRANSITION_HALF_BAND = 0.025

# ---------------------------------------------------------------------------
# Module-level exports (imported directly by test suite)
# ---------------------------------------------------------------------------

# Lookup dict: force name string -> SpectralForceName member
_FORCE_BY_NAME: Dict[str, SpectralForceName] = {
    f.value: f for f in SpectralForceName
}

# Ordered list of all force members, low -> high phi
_ORDERED_FORCES: List[SpectralForceName] = [
    row[2] for row in _FORCE_BOUNDARIES
]

# Pre-built list of all TransitionCorridor objects for every adjacent boundary
_CORRIDORS: List[TransitionCorridor] = [
    TransitionCorridor(
        from_force=_FORCE_BOUNDARIES[i][2],
        to_force=_FORCE_BOUNDARIES[i + 1][2],
        phi=_FORCE_BOUNDARIES[i][1],
    )
    for i in range(len(_FORCE_BOUNDARIES) - 1)
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clamp(phi: float) -> float:
    return max(0.0, min(1.0, phi))


def _force_for_phi(phi: float) -> SpectralForceName:
    phi = _clamp(phi)
    for low, high, force in _FORCE_BOUNDARIES:
        if low <= phi < high:
            return force
    return SpectralForceName.LUX_PERPETUA


# ---------------------------------------------------------------------------
# SpectralForceEngine
# ---------------------------------------------------------------------------

class SpectralForceEngine:
    """
    Maps phi values to spectral forces and transition corridors.
    All public methods are static.
    """

    # ------------------------------------------------------------------
    # Core static API
    # ------------------------------------------------------------------

    @staticmethod
    def detect_current_force(phi: float) -> Optional[SpectralForceName]:
        """Return the SpectralForceName for the given phi (clamped to [0,1])."""
        try:
            return _force_for_phi(phi)
        except Exception:  # pragma: no cover
            return None

    @staticmethod
    def detect_corridor(phi: float) -> Optional[TransitionCorridor]:
        """
        Return a TransitionCorridor when phi is within ±TRANSITION_HALF_BAND
        of a zone boundary, otherwise None.
        """
        phi_c = _clamp(phi)
        for i in range(len(_FORCE_BOUNDARIES) - 1):
            boundary = _FORCE_BOUNDARIES[i][1]
            if abs(phi_c - boundary) <= _TRANSITION_HALF_BAND:
                return TransitionCorridor(
                    from_force=_FORCE_BOUNDARIES[i][2],
                    to_force=_FORCE_BOUNDARIES[i + 1][2],
                    phi=phi_c,
                )
        return None

    @staticmethod
    def get_trajectory(phi_history: List[float]) -> List[SpectralForceName]:
        """Map a list of phi values to their SpectralForceName."""
        return [_force_for_phi(p) for p in phi_history]

    @staticmethod
    def is_o4_active(phi: float) -> bool:
        """True when phi is in the IOSIS approach window (0.70 ≤ phi ≤ 0.85)."""
        return 0.70 <= _clamp(phi) <= 0.85

    @staticmethod
    def build_system_prompt_block(phi: float) -> str:
        """
        Return a system-prompt block for the current spectral state.

        Format (matches test assertions):
            [SPECTRAL FIELD: <FORCE> | φ=<phi>]
            OA-4 Active: true|false
            <force description>
        """
        force = _force_for_phi(phi)
        o4 = SpectralForceEngine.is_o4_active(phi)
        o4_str = "true" if o4 else "false"

        desc = {
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

        return (
            f"[SPECTRAL FIELD: {force.value} | φ={phi:.3f}]\n"
            f"OA-4 Active: {o4_str}\n"
            f"{desc}"
        )

    # ------------------------------------------------------------------
    # Backward-compat aliases
    # ------------------------------------------------------------------

    @staticmethod
    def detect_transition_corridor(phi: float) -> Optional[TransitionCorridor]:
        """Alias for detect_corridor (old name used in some test fixtures)."""
        return SpectralForceEngine.detect_corridor(phi)

    @classmethod
    def is_oa4_active(cls, phi: float) -> bool:
        """ASCII alias for is_o4_active."""
        return cls.is_o4_active(phi)

    @staticmethod
    def is_oа4_active(phi: float) -> bool:  # noqa: PLC2401
        """Cyrillic-а variant — matches the test method calls exactly."""
        return SpectralForceEngine.is_o4_active(phi)
