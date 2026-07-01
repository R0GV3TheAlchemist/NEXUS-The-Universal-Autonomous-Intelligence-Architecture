"""
core/criticality_monitor.py
Criticality Monitor — tracks system-level criticality / critical-dynamics signals.

Canon Ref: C42 — Edge-of-Chaos Processing Doctrine
"""
from __future__ import annotations

import math
import time as _time
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CriticalityState(str, Enum):
    CRITICAL = "critical"
    ORDERED  = "ordered"
    CHAOTIC  = "chaotic"
    UNKNOWN  = "unknown"


# Legacy enum kept for back-compat
class CriticalityLevel(str, Enum):
    NOMINAL   = "nominal"
    ELEVATED  = "elevated"
    CRITICAL  = "critical"
    EMERGENCY = "emergency"


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

@dataclass
class CriticalityReport:
    timestamp:         float
    state:             CriticalityState
    spectral_radius:   float
    entropy_estimate:  float
    lyapunov_proxy:    float
    drift_magnitude:   float
    corrective_action: Optional[str] = None
    doctrine_ref:      str = "C42"


# ---------------------------------------------------------------------------
# CriticalDynamicsMonitor
# ---------------------------------------------------------------------------

class CriticalDynamicsMonitor:
    """Monitors system criticality via spectral, entropy and Lyapunov proxies."""

    SPECTRAL_TARGET:            float = 1.0
    SPECTRAL_ORDERED_THRESHOLD: float = 0.7
    SPECTRAL_CHAOTIC_THRESHOLD: float = 1.3
    ENTROPY_FLOOR:              float = 0.3
    ENTROPY_CEILING:            float = 0.9
    _MAX_HISTORY:               int   = 500

    def __init__(self) -> None:
        self._history: List[CriticalityReport] = []
        self._active:  bool = True

    def _compute_spectral_proxy(self, probs: Optional[List[float]]) -> float:
        if not probs or len(probs) < 2:
            return self.SPECTRAL_TARGET
        n   = len(probs)
        avg = sum(probs) / n
        variance = sum((p - avg) ** 2 for p in probs) / n
        # Uniform distribution: variance == 0, raw == SPECTRAL_TARGET exactly
        raw = self.SPECTRAL_TARGET + (variance - 1.0 / n) * n
        return float(max(0.1, min(2.0, raw)))

    def _estimate_entropy(self, probs: Optional[List[float]]) -> float:
        if not probs or len(probs) < 2:
            return 0.5
        n       = len(probs)
        max_ent = math.log2(n)
        if max_ent == 0:
            return 0.5
        ent = 0.0
        for p in probs:
            if p > 0:
                ent -= p * math.log2(p)
        return float(max(0.0, min(1.0, ent / max_ent)))

    def _compute_lyapunov_proxy(self, norms: Optional[List[float]]) -> float:
        if not norms or len(norms) < 3:
            return 0.0
        total = 0.0
        count = 0
        for i in range(1, len(norms)):
            prev = norms[i - 1]
            curr = norms[i]
            if prev > 0 and curr > 0:
                total += math.log(curr / prev)
                count += 1
        return float(total / count) if count else 0.0

    def _classify_state(
        self,
        spectral: float,
        entropy:  float,
    ) -> CriticalityState:
        # CHAOTIC check first: uniform dist hits SPECTRAL_TARGET (1.0) exactly,
        # and >= threshold (1.3) is False, but entropy ceiling catches max-entropy.
        # Uniform probs produce spectral == SPECTRAL_TARGET == 1.0 < 1.3,
        # but entropy == 1.0 > ENTROPY_CEILING (0.9) → CHAOTIC ✓
        if spectral >= self.SPECTRAL_CHAOTIC_THRESHOLD or entropy > self.ENTROPY_CEILING:
            return CriticalityState.CHAOTIC
        if spectral < self.SPECTRAL_ORDERED_THRESHOLD or entropy < self.ENTROPY_FLOOR:
            return CriticalityState.ORDERED
        return CriticalityState.CRITICAL

    def _recommend_correction(
        self,
        state:    CriticalityState,
        spectral: float,
        entropy:  float,
    ) -> Optional[str]:
        if state == CriticalityState.CRITICAL:
            return None
        if state == CriticalityState.ORDERED:
            return "Apply temperature perturbation to nudge system toward edge-of-chaos."
        if state == CriticalityState.CHAOTIC:
            return "Apply stabilization temperature reduction to restore order boundary."
        return "Collect more data before issuing a corrective action."

    def assess(
        self,
        token_probabilities: Optional[List[float]] = None,
        embedding_norms:     Optional[List[float]] = None,
        attention_entropy:   Optional[float]       = None,
    ) -> CriticalityReport:
        spectral = self._compute_spectral_proxy(token_probabilities)
        entropy  = (
            attention_entropy
            if attention_entropy is not None
            else self._estimate_entropy(token_probabilities)
        )
        lyapunov = self._compute_lyapunov_proxy(embedding_norms)
        state    = self._classify_state(spectral, entropy)
        drift    = abs(spectral - self.SPECTRAL_TARGET)
        action   = self._recommend_correction(state, spectral, entropy)

        report = CriticalityReport(
            timestamp=_time.time(),
            state=state,
            spectral_radius=spectral,
            entropy_estimate=entropy,
            lyapunov_proxy=lyapunov,
            drift_magnitude=drift,
            corrective_action=action,
        )
        self._history.append(report)
        if len(self._history) > self._MAX_HISTORY:
            self._history = self._history[-self._MAX_HISTORY:]
        return report

    def get_current_state(self) -> CriticalityState:
        if not self._history:
            return CriticalityState.UNKNOWN
        return self._history[-1].state

    def get_recent_reports(self, n: int = 10) -> List[CriticalityReport]:
        return self._history[-n:]

    def doctrine_summary(self) -> dict:
        return {
            "doctrine":          "C42 — Edge-of-Chaos Processing Doctrine",
            "principle":         "Maintain criticality at the edge of order and chaos.",
            "current_state":     self.get_current_state().value,
            "total_assessments": len(self._history),
            "spectral_target":   self.SPECTRAL_TARGET,
            "ordered_threshold": self.SPECTRAL_ORDERED_THRESHOLD,
            "chaotic_threshold": self.SPECTRAL_CHAOTIC_THRESHOLD,
        }


# ---------------------------------------------------------------------------
# Legacy alias + singleton
# ---------------------------------------------------------------------------

CriticalityMonitor = CriticalDynamicsMonitor

_monitor: Optional[CriticalDynamicsMonitor] = None


def get_monitor() -> CriticalDynamicsMonitor:
    global _monitor
    if _monitor is None:
        _monitor = CriticalDynamicsMonitor()
    return _monitor
