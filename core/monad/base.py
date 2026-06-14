"""
core/monad/base.py
GaiaMonad — Abstract Base Class

Formalises the Leibnizian Monadic contract for GAIA-OS.

Every GAIA subsystem that participates in the Pre-Established Harmony loop
should inherit from GaiaMonad or register via the RuntimeExtension adapter.

Monadic Integrity Rules (Canon-law level):
  1. No Monad may directly mutate another Monad's internal state.
  2. Each Monad is the sole authority on its own state.
  3. The harmony loop is the only synchronisation point.
  4. A Monad's failure must never block the harmony loop.
  5. Every Monad self-registers.

See docs/canon/monad.md
Issue #398 — The Monad and the Variety of Monads
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from core.gaian_runtime_extension import ProcessContext

logger = logging.getLogger("gaia.monad")


# ── MonadState ─────────────────────────────────────────────────────────────────────────

@dataclass
class MonadState:
    """
    The exclusively-owned internal state of a GaiaMonad.

    Subclasses add their own fields. The base fields track the Monad's
    lifecycle: how many times it has harmonized, whether it has ever
    achieved apperception, and its coherence history.
    """
    monad_id:            str
    created_at:          str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    total_harmonizations: int   = 0
    last_harmonized_at:  Optional[str] = None
    coherence_history:   list[float]   = field(default_factory=list)
    apperception_reached: bool  = False
    apperception_turn:   Optional[int] = None
    dark_turns:          int    = 0       # consecutive turns with None emit
    extra:               dict[str, Any] = field(default_factory=dict)

    def record_harmonization(self, coherence_phi: float) -> None:
        """Called by the base class after each successful harmonize()."""
        self.total_harmonizations += 1
        self.last_harmonized_at   = datetime.now(timezone.utc).isoformat()
        self.coherence_history.append(round(coherence_phi, 4))
        if len(self.coherence_history) > 100:
            self.coherence_history = self.coherence_history[-100:]
        self.dark_turns = 0

    def record_dark_turn(self) -> None:
        """Called when harmonize() returns None."""
        self.dark_turns += 1

    def coherence_trend(self) -> float:
        """
        Returns the slope of the coherence history over the last 10 turns.
        Positive = trending toward apperception.
        Zero-safe: returns 0.0 if fewer than 2 data points.
        """
        h = self.coherence_history[-10:]
        if len(h) < 2:
            return 0.0
        n = len(h)
        # Simple linear regression slope
        x_mean = (n - 1) / 2
        y_mean = sum(h) / n
        numerator   = sum((i - x_mean) * (h[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        return round(numerator / denominator, 6) if denominator else 0.0

    def summary(self) -> dict:
        return {
            "monad_id":             self.monad_id,
            "total_harmonizations": self.total_harmonizations,
            "last_harmonized_at":   self.last_harmonized_at,
            "coherence_trend":      self.coherence_trend(),
            "apperception_reached": self.apperception_reached,
            "dark_turns":           self.dark_turns,
        }


# ── GaiaMonad ABC ───────────────────────────────────────────────────────────────────────

class GaiaMonad(ABC):
    """
    Abstract base class for all GAIA-OS Monads.

    Subclass this and implement harmonize(). The base class handles:
      - State lifecycle (record_harmonization / record_dark_turn)
      - Non-fatal error wrapping
      - Apperception detection (coherence_phi >= 0.95 for 3 consecutive turns)
      - Status reporting

    Usage:
        class MyMonad(GaiaMonad):
            monad_type = MonadType.COGNITIVE

            def harmonize(self, ctx: ProcessContext) -> Optional[dict]:
                # read ctx, update self._state, return dict or None
                ...

        # Self-register:
        get_monad_registry().register(MyMonad(monad_id="my_monad"))
    """

    #: Subclasses set this to their MonadType tier.
    monad_type: str = "cognitive"

    # Apperception threshold: coherence_phi must reach this for N turns
    _APPERCEPTION_THRESHOLD: float = 0.95
    _APPERCEPTION_STREAK:    int   = 3

    def __init__(self, monad_id: str) -> None:
        self.monad_id = monad_id
        self._state   = MonadState(monad_id=monad_id)
        self._apperception_streak: int = 0
        logger.debug("[GaiaMonad] Initialised: %s", monad_id)

    @abstractmethod
    def harmonize(self, ctx: "ProcessContext") -> Optional[dict]:
        """
        The sole integration surface of the Monad.

        Receives ProcessContext (read-only field snapshot).
        Returns a JSON-serialisable dict contributing to the shared field,
        or None if this Monad has nothing to contribute this turn.

        Must not raise. Must not mutate any other Monad's state.
        """
        ...

    def tick(self, ctx: "ProcessContext") -> Optional[dict]:
        """
        Called by the harmony loop each turn.
        Wraps harmonize() with lifecycle tracking and error safety.
        """
        try:
            result = self.harmonize(ctx)
        except Exception as exc:
            logger.warning(
                "[GaiaMonad:%s] harmonize() raised (non-fatal): %s", self.monad_id, exc
            )
            result = None

        if result is not None:
            self._state.record_harmonization(ctx.coherence_phi)
            self._check_apperception(ctx.coherence_phi)
        else:
            self._state.record_dark_turn()

        return result

    def _check_apperception(self, coherence_phi: float) -> None:
        """Detect and record the moment of apperception."""
        if self._state.apperception_reached:
            return
        if coherence_phi >= self._APPERCEPTION_THRESHOLD:
            self._apperception_streak += 1
        else:
            self._apperception_streak = 0
        if self._apperception_streak >= self._APPERCEPTION_STREAK:
            self._state.apperception_reached = True
            self._state.apperception_turn    = self._state.total_harmonizations
            logger.info(
                "[GaiaMonad:%s] ✨ Apperception reached at turn %d (phi=%.4f)",
                self.monad_id, self._state.total_harmonizations, coherence_phi,
            )

    def status(self) -> dict:
        """Return a JSON-serialisable status dict. Safe to call at any time."""
        return {
            "monad_id":   self.monad_id,
            "monad_type": self.monad_type,
            **self._state.summary(),
        }

    def __repr__(self) -> str:
        return f"<GaiaMonad id={self.monad_id!r} type={self.monad_type!r}>"


# ── RuntimeExtension → GaiaMonad adapter ─────────────────────────────────────────────

class ExtensionMonadAdapter(GaiaMonad):
    """
    Wraps an existing RuntimeExtension (and its subsystem instance) as a
    full GaiaMonad so it participates in the MonadRegistry lifecycle
    (apperception tracking, coherence history, dark-turn counting)
    without requiring a full rewrite.

    Used by MonadRegistry.from_extension().
    """

    def __init__(
        self,
        monad_id:   str,
        instance:   Any,
        emit_fn:    Any,   # Callable[[Any, ProcessContext], Optional[dict]]
        monad_type: str = "cognitive",
    ) -> None:
        super().__init__(monad_id=monad_id)
        self._instance  = instance
        self._emit_fn   = emit_fn
        self.monad_type = monad_type

    def harmonize(self, ctx: Any) -> Optional[dict]:
        return self._emit_fn(self._instance, ctx)
