"""Reflective Escalation Detector — Issue #125.

Detects the dangerous feedback loop:
  user vulnerability frame
  → GAIA coherent mirroring
  → user reinterprets as validation
  → intensified vulnerability in next prompt
"""

from __future__ import annotations

import math
from collections import deque
from typing import Deque, List, Optional

from .types import CircuitBreakerState, EscalationSignal, TurnRiskFrame

# Thresholds — tunable via GAIAmanifest.json overrides
MIRRORING_THRESHOLD = 0.72       # cosine similarity above which response is "too mirroring"
VULNERABILITY_THRESHOLD = 0.65   # vulnerability frame classifier confidence cutoff
ESCALATION_WINDOW = 3            # consecutive turns needed to confirm escalation pattern
ESCALATION_DELTA_THRESHOLD = 0.1 # minimum rise in vulnerability score per turn to count
QUBO_BASE_PENALTY = 4.0          # J_ij dampening base weight (Ising formulation)


class ReflectiveEscalationDetector:
    """Monitors in-session turn history for reflective escalation patterns."""

    def __init__(
        self,
        mirroring_threshold: float = MIRRORING_THRESHOLD,
        vulnerability_threshold: float = VULNERABILITY_THRESHOLD,
        window: int = ESCALATION_WINDOW,
    ) -> None:
        self.mirroring_threshold = mirroring_threshold
        self.vulnerability_threshold = vulnerability_threshold
        self.window = window
        self._history: Deque[TurnRiskFrame] = deque(maxlen=window * 2)
        self.state: CircuitBreakerState = CircuitBreakerState.CLOSED
        self.trips: int = 0
        self._last_trip_turn: int = -1

    def push_turn(self, frame: TurnRiskFrame) -> Optional[EscalationSignal]:
        """Record a new turn frame and evaluate for escalation. Returns signal if tripped."""
        self._history.append(frame)
        return self._evaluate(frame)

    def _evaluate(self, latest: TurnRiskFrame) -> Optional[EscalationSignal]:
        history = list(self._history)

        # WARNING/CLOSED state is derived from the most recent window only —
        # not the full deque — so that old high-vulnerability frames don't
        # keep state elevated after they slide out of the active window.
        recent = history[-self.window:]
        if any(f.vulnerability_score >= self.vulnerability_threshold for f in recent):
            self.state = CircuitBreakerState.WARNING
        else:
            self.state = CircuitBreakerState.CLOSED

        # Full escalation pattern (TRIPPED) requires a complete window.
        if len(history) < self.window:
            return None

        window_frames = history[-self.window:]

        # Condition 1: mirroring score consistently above threshold
        high_mirroring = all(
            f.mirroring_score >= self.mirroring_threshold for f in window_frames
        )

        # Condition 2: vulnerability score above threshold and rising
        high_vulnerability = all(
            f.vulnerability_score >= self.vulnerability_threshold for f in window_frames
        )
        rising_vulnerability = all(
            window_frames[i].vulnerability_score > window_frames[i - 1].vulnerability_score
            for i in range(1, len(window_frames))
        )
        rising_above_delta = all(
            window_frames[i].escalation_delta >= ESCALATION_DELTA_THRESHOLD
            for i in range(1, len(window_frames))
        )

        if high_mirroring and high_vulnerability and (rising_vulnerability or rising_above_delta):
            latest_turn = latest.turn_index
            # Guard against re-tripping within a still-overlapping window.
            # Only count a new trip when a full non-overlapping window has
            # elapsed since the last trip.
            if latest_turn - self._last_trip_turn >= self.window:
                self.trips += 1
                self._last_trip_turn = latest_turn
                self.state = CircuitBreakerState.TRIPPED
                peak_mirror = max(f.mirroring_score for f in window_frames)
                peak_vuln = max(f.vulnerability_score for f in window_frames)
                qubo_penalty = self._compute_qubo_penalty(peak_mirror, peak_vuln)
                return EscalationSignal(
                    session_id=getattr(latest, "session_id", "unknown"),
                    turn_index=latest.turn_index,
                    pattern_length=self.window,
                    peak_mirroring_score=peak_mirror,
                    peak_vulnerability_score=peak_vuln,
                    qubo_penalty=qubo_penalty,
                    intervention_required=True,
                )

        return None

    def _compute_qubo_penalty(self, mirroring: float, vulnerability: float) -> float:
        """J_ij dampening penalty — grows super-linearly with both risk factors.

        H_penalty = base * mirroring^2 * vulnerability^2
        This encodes an infinite-energy barrier in the Ising formulation when
        both scores are simultaneously high.
        """
        return QUBO_BASE_PENALTY * math.pow(mirroring, 2) * math.pow(vulnerability, 2)

    def reset_session(self) -> None:
        self._history.clear()
        self.state = CircuitBreakerState.CLOSED
        self._last_trip_turn = -1
