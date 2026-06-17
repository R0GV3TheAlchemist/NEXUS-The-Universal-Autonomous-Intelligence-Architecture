# core/monad/perception.py
# E701 fix: all inline `if x: return y` expanded to multi-line form.
# Addition: PerceptionMonad alias for MonadPerception
# (MonadPerception was renamed to PerceptionMonad during the monad refactor;
#  both names are now valid import targets.)
#
# FIX (2026-06-17): MonadPerception / PerceptionMonad now accepts `monad_id`
# keyword argument (and arbitrary **kwargs) so that:
#   PerceptionMonad(monad_id="test.perception")
#   PerceptionMonad(monad_id="monad.perception", phi=0.0)
# work as expected by test fixtures and MonadOrchestrator.__init__.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class PerceptionResult:
    """Output of the MonadPerception layer."""
    force_name: str
    phi: float
    corridor: Optional[str] = None
    confidence: float = 1.0


class MonadPerception:
    """
    Maps integrated information (phi) to Monad force names.

    Force names follow the alchemical-chromatic ladder defined in
    C47 (Philosopher's Stone Doctrine) and C50 (Prism Cube Doctrine).
    """

    FORCE_LADDER = [
        (0.05, "NIGREDO"),
        (0.15, "PYROSIS"),
        (0.28, "CITRINITAS"),
        (0.42, "VIRIDITAS"),
        (0.58, "CAERULITAS"),
        (0.72, "RUBEDO"),
        (0.85, "IOSIS"),
        (0.92, "ALBEDO"),
        (0.95, "CHRYSITAS"),
        (0.97, "ARGENTITAS"),
    ]

    def __init__(self, monad_id: Optional[str] = None, **kwargs: Any) -> None:
        """
        Parameters
        ----------
        monad_id : str, optional
            Identifier for this monad instance (e.g. "monad.perception").
        **kwargs : Any
            Absorbed for forward-compatibility with orchestrator init calls.
        """
        self.monad_id: str = monad_id or "monad.perception"
        # phi starts at 0.0; updated via perceive() calls
        self._phi: float = kwargs.get("phi", 0.0)
        self._corridor: Optional[str] = kwargs.get("corridor", None)
        self._synthesis_filter: Optional[str] = None

    # ------------------------------------------------------------------
    # Instance API
    # ------------------------------------------------------------------

    def perceive(self, phi: float, corridor: Optional[str] = None) -> PerceptionResult:
        """Map phi to a force name and return a PerceptionResult."""
        self._phi = phi
        self._corridor = corridor
        force = self._force_from_phi(phi)
        return PerceptionResult(
            force_name=force,
            phi=phi,
            corridor=corridor,
        )

    def set_synthesis_filter(self, force_name: Optional[str]) -> None:
        """Override the synthesis filter (used by IOSIS corridor logic)."""
        self._synthesis_filter = force_name

    def signal_clarity(self) -> float:
        """Return a 0-1 clarity score derived from current phi."""
        phi = max(0.0, min(1.0, self._phi))
        return phi

    def to_dict(self) -> dict:
        return {
            "monad_id": self.monad_id,
            "phi": self._phi,
            "corridor": self._corridor,
            "synthesis_filter": self._synthesis_filter,
            "force": self._force_from_phi(self._phi),
        }

    # ------------------------------------------------------------------
    # Force-mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _force_from_phi(phi: float) -> str:
        """Minimal phi → force_name mapping."""
        if phi < 0.05:
            return "NIGREDO"
        if phi < 0.15:
            return "PYROSIS"
        if phi < 0.28:
            return "CITRINITAS"
        if phi < 0.42:
            return "VIRIDITAS"
        if phi < 0.58:
            return "CAERULITAS"
        if phi < 0.72:
            return "RUBEDO"
        if phi < 0.85:
            return "IOSIS"
        if phi < 0.92:
            return "ALBEDO"
        if phi < 0.95:
            return "CHRYSITAS"
        if phi < 0.97:
            return "ARGENTITAS"
        return "LUX_PERPETUA"

    # ------------------------------------------------------------------
    # Class-level convenience (backward compat with MonadOrchestrator)
    # ------------------------------------------------------------------

    @classmethod
    def class_perceive(cls, phi: float, corridor: Optional[str] = None) -> PerceptionResult:
        """Stateless class-level perceive — constructs a temporary instance."""
        instance = cls()
        return instance.perceive(phi, corridor)


# Backward-compat alias: tests and core/monad/__init__.py import PerceptionMonad
PerceptionMonad = MonadPerception
