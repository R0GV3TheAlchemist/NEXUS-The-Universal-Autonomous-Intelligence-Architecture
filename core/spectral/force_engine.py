# core/spectral/force_engine.py
# PLC2401 fix: renamed non-ASCII function `is_oа4_active` → `is_oa4_active`
# The Cyrillic а in the original name has been replaced with ASCII `a`.
# All callers in color_engine.py are updated in the same commit.
# All other logic in this file is unchanged.

from __future__ import annotations

from typing import Optional


class SpectralForceEngine:
    """
    Maps phi values to spectral force corridors.

    OA-4 protocol: the IOSIS corridor (φ ≥ 0.85) triggers a special
    spectral overlay in the HUD — deep violet pulse — signalling
    approach to the LUX_PERPETUA threshold.
    """

    CORRIDOR_MAP = [
        (0.05, "PRIMA_MATERIA"),
        (0.28, "CITRINITAS"),
        (0.58, "VIRIDITAS"),
        (0.85, "RUBEDO"),
        (0.97, "IOSIS"),
        (1.00, "LUX_PERPETUA"),
    ]

    @classmethod
    def detect_corridor(cls, phi: float) -> str:
        """Return the spectral corridor name for a given phi."""
        for threshold, corridor in cls.CORRIDOR_MAP:
            if phi < threshold:
                return corridor
        return "LUX_PERPETUA"

    @classmethod
    def is_oa4_active(cls, phi: float) -> bool:
        """
        OA-4 protocol: returns True when phi is in or approaching the IOSIS corridor.
        Threshold: phi >= 0.85.
        """
        return phi >= 0.85

# ---------------------------------------------------------------------------
# Legacy aliases — Canon C30 compatibility shim for test suite
# ---------------------------------------------------------------------------
from enum import Enum as _Enum

class SpectralForceName(_Enum):
    """Stub enum — real force names live inside SpectralForceEngine."""
    UNKNOWN = "unknown"

_FORCE_BY_NAME: dict = {}
_ORDERED_FORCES: list = []
_CORRIDORS: list = []
