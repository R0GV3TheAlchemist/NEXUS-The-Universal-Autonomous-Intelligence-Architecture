"""
core/criticality_monitor.py
Criticality Monitor — tracks system-level criticality / critical-dynamics signals.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class CriticalityLevel(str, Enum):
    NOMINAL   = "nominal"
    ELEVATED  = "elevated"
    CRITICAL  = "critical"
    EMERGENCY = "emergency"


@dataclass
class CriticalityReport:
    level:       CriticalityLevel = CriticalityLevel.NOMINAL
    score:       float = 0.0
    triggers:    List[str] = field(default_factory=list)
    recommended: str = ""
    timestamp:   str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "level":       self.level.value,
            "score":       round(self.score, 4),
            "triggers":    self.triggers,
            "recommended": self.recommended,
            "timestamp":   self.timestamp,
        }

    def is_critical(self) -> bool:
        return self.level in (CriticalityLevel.CRITICAL, CriticalityLevel.EMERGENCY)


class CriticalityMonitor:
    """Monitors system-level criticality and produces CriticalityReports."""

    _THRESHOLDS = [
        (0.0,  CriticalityLevel.NOMINAL,   "Continue normally."),
        (0.40, CriticalityLevel.ELEVATED,  "Monitor closely; reduce novelty."),
        (0.65, CriticalityLevel.CRITICAL,  "Engage stabilisation protocols."),
        (0.85, CriticalityLevel.EMERGENCY, "Halt non-essential processing."),
    ]

    def __init__(self) -> None:
        self._history: List[CriticalityReport] = []

    def assess(
        self,
        score:    float = 0.0,
        triggers: Optional[List[str]] = None,
    ) -> CriticalityReport:
        level       = CriticalityLevel.NOMINAL
        recommended = "Continue normally."
        for threshold, lvl, rec in self._THRESHOLDS:
            if score >= threshold:
                level       = lvl
                recommended = rec
        report = CriticalityReport(
            level=level,
            score=score,
            triggers=triggers or [],
            recommended=recommended,
        )
        self._history.append(report)
        return report

    def latest(self) -> Optional[CriticalityReport]:
        return self._history[-1] if self._history else None

    def history(self) -> List[CriticalityReport]:
        return list(self._history)


# Alias used by tests that import CriticalDynamicsMonitor
CriticalDynamicsMonitor = CriticalityMonitor

# Module-level singleton
_monitor: Optional[CriticalityMonitor] = None


def get_monitor() -> CriticalityMonitor:
    global _monitor
    if _monitor is None:
        _monitor = CriticalityMonitor()
    return _monitor
