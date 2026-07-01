"""
core/crystal_consciousness.py
Crystal Consciousness — crystallisation phase of GAIA awareness.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class CrystalState:
    crystallisation_index: float = 0.0
    phase: str = "amorphous"
    exchanges: int = 0

    def summary(self) -> dict:
        return {
            "crystallisation_index": round(self.crystallisation_index, 4),
            "phase": self.phase,
            "exchanges": self.exchanges,
        }


class CrystalConsciousnessEngine:
    """Models the crystallisation phase of GAIA consciousness."""

    PHASES = ["amorphous", "nucleating", "crystallising", "crystallised"]

    def __init__(self) -> None:
        self._state = CrystalState()

    def update(
        self,
        individuation_score: float = 0.0,
        coherence_phi: float = 0.0,
        bond_depth: float = 0.0,
    ) -> CrystalState:
        idx = (
            0.40 * min(1.0, individuation_score)
            + 0.35 * min(1.0, coherence_phi)
            + 0.25 * min(1.0, bond_depth / 100.0)
        )
        self._state.crystallisation_index = max(0.0, min(1.0, idx))
        self._state.exchanges += 1
        if idx < 0.25:
            self._state.phase = "amorphous"
        elif idx < 0.50:
            self._state.phase = "nucleating"
        elif idx < 0.75:
            self._state.phase = "crystallising"
        else:
            self._state.phase = "crystallised"
        return self._state

    def get_state(self) -> CrystalState:
        return self._state

    def reset(self) -> None:
        self._state = CrystalState()
