"""CircuitBreaker — CLOSED / OPEN / HALF_OPEN state machine — GAIA-OS Issue #187.

Each GAIA engine/skill gets its own CircuitBreaker instance managed by
SelfHealingEngine.  When a skill's failure rate exceeds the threshold the
circuit opens and subsequent calls fail-fast, protecting the rest of the
orchestration pipeline from cascading failures.

Canon refs:
  C30 — No silent failures: circuit state is surfaced in Agent Telemetry Hub.
  C01 — Sovereignty: user can inspect circuit health in the Glass Room.
  C34 — Presence: GAIA remains functional (degraded mode) even when a circuit is open.

State machine:
  CLOSED   — normal operation; failures tracked in rolling window.
  OPEN     — fail-fast; no downstream calls made; recovery probe scheduled.
  HALF_OPEN — single probe attempt; success → CLOSED, failure → OPEN.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State enum
# ---------------------------------------------------------------------------

class CircuitState(Enum):
    CLOSED = "closed"        # Normal — requests pass through.
    OPEN = "open"            # Failing — requests fail-fast.
    HALF_OPEN = "half_open"  # Probing — one request allowed through.


class CircuitOpenError(Exception):
    """Raised when a call is attempted against an OPEN circuit."""

    def __init__(self, skill_id: str, opens_at: float, open_duration_s: float):
        self.skill_id = skill_id
        self.opens_at = opens_at
        self.open_duration_s = open_duration_s
        remaining = max(0.0, open_duration_s - (time.monotonic() - opens_at))
        super().__init__(
            f"Circuit OPEN for '{skill_id}'. "
            f"Recovery probe in ~{remaining:.1f}s."
        )


# ---------------------------------------------------------------------------
# CircuitBreaker
# ---------------------------------------------------------------------------

@dataclass
class CircuitBreaker:
    """Per-skill circuit breaker.

    Attributes:
        skill_id:               Human-readable engine/skill identifier.
        failure_rate_threshold: Fraction of failures in *window_s* that trips the circuit.
        open_duration_s:        Seconds the circuit stays OPEN before a HALF_OPEN probe.
        window_s:               Rolling window width (seconds) for failure-rate calculation.
        min_calls:              Minimum calls in the window before the rate is evaluated.
    """

    skill_id: str
    failure_rate_threshold: float = 0.50   # 50 % failures → OPEN
    open_duration_s: float = 30.0
    window_s: float = 60.0
    min_calls: int = 3

    # Internal state — not part of public API.
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False, repr=False)
    _call_times: list[float] = field(default_factory=list, init=False, repr=False)
    _failure_times: list[float] = field(default_factory=list, init=False, repr=False)
    _opened_at: Optional[float] = field(default=None, init=False, repr=False)
    _half_open_probe_in_flight: bool = field(default=False, init=False, repr=False)

    # -----------------------------------------------------------------------
    # Public interface
    # -----------------------------------------------------------------------

    @property
    def state(self) -> CircuitState:
        self._maybe_transition_to_half_open()
        return self._state

    def record_success(self) -> None:
        """Record a successful call.  Closes the circuit if in HALF_OPEN."""
        now = time.monotonic()
        self._call_times.append(now)
        self._prune_window(now)
        self._half_open_probe_in_flight = False

        if self._state in (CircuitState.OPEN, CircuitState.HALF_OPEN):
            logger.info("[CircuitBreaker] '%s' recovered → CLOSED.", self.skill_id)
            self._state = CircuitState.CLOSED
            self._opened_at = None

    def record_failure(self, exc: Exception) -> None:
        """Record a failed call and potentially open the circuit."""
        now = time.monotonic()
        self._call_times.append(now)
        self._failure_times.append(now)
        self._prune_window(now)
        self._half_open_probe_in_flight = False

        if self._state == CircuitState.HALF_OPEN:
            # Probe failed — re-open.
            logger.warning(
                "[CircuitBreaker] '%s' probe failed (%s) → re-OPEN.",
                self.skill_id, type(exc).__name__,
            )
            self._trip()
            return

        if self._state == CircuitState.CLOSED and self._should_trip():
            logger.warning(
                "[CircuitBreaker] '%s' failure rate %.0f%% exceeded threshold → OPEN.",
                self.skill_id, self._failure_rate() * 100,
            )
            self._trip()

    def allow_request(self) -> bool:
        """Return True if a request should be allowed through.

        Raises:
            CircuitOpenError: if the circuit is OPEN and not yet ready to probe.
        """
        self._maybe_transition_to_half_open()

        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.HALF_OPEN:
            if self._half_open_probe_in_flight:
                raise CircuitOpenError(self.skill_id, self._opened_at or 0, self.open_duration_s)
            self._half_open_probe_in_flight = True
            return True

        # OPEN
        raise CircuitOpenError(self.skill_id, self._opened_at or 0, self.open_duration_s)

    def health_summary(self) -> dict[str, Any]:
        """Return a snapshot suitable for the Agent Telemetry Hub (Issue #188)."""
        now = time.monotonic()
        self._prune_window(now)
        return {
            "skill_id": self.skill_id,
            "state": self.state.value,
            "failure_rate": round(self._failure_rate(), 3),
            "total_calls_in_window": len(self._call_times),
            "failures_in_window": len(self._failure_times),
            "open_duration_s": self.open_duration_s,
            "opened_at": self._opened_at,
        }

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _trip(self) -> None:
        self._state = CircuitState.OPEN
        self._opened_at = time.monotonic()

    def _maybe_transition_to_half_open(self) -> None:
        if (
            self._state == CircuitState.OPEN
            and self._opened_at is not None
            and (time.monotonic() - self._opened_at) >= self.open_duration_s
        ):
            logger.info("[CircuitBreaker] '%s' probing recovery → HALF_OPEN.", self.skill_id)
            self._state = CircuitState.HALF_OPEN

    def _should_trip(self) -> bool:
        if len(self._call_times) < self.min_calls:
            return False
        return self._failure_rate() >= self.failure_rate_threshold

    def _failure_rate(self) -> float:
        if not self._call_times:
            return 0.0
        return len(self._failure_times) / len(self._call_times)

    def _prune_window(self, now: float) -> None:
        cutoff = now - self.window_s
        self._call_times = [t for t in self._call_times if t > cutoff]
        self._failure_times = [t for t in self._failure_times if t > cutoff]
