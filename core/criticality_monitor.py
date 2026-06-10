"""
Criticality Monitor — watches GAIA-OS for self-organised criticality signals.

Provides:
  - CriticalDynamicsMonitor  : main class
  - CriticalityLevel         : enum
  - CriticalitySnapshot      : dataclass
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

log = logging.getLogger(__name__)


class CriticalityLevel(str, Enum):
    SUBCRITICAL = "subcritical"
    NEAR_CRITICAL = "near_critical"
    CRITICAL = "critical"
    SUPERCRITICAL = "supercritical"


@dataclass
class CriticalitySnapshot:
    """A point-in-time criticality measurement."""

    level: CriticalityLevel = CriticalityLevel.SUBCRITICAL
    branching_ratio: float = 0.0  # <1 sub, ==1 critical, >1 super
    avalanche_size: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "level": self.level.value,
            "branching_ratio": self.branching_ratio,
            "avalanche_size": self.avalanche_size,
            "metadata": self.metadata,
        }


class CriticalDynamicsMonitor:
    """Monitors GAIA for signs of self-organised criticality."""

    CRITICAL_THRESHOLD = 0.95
    SUPER_THRESHOLD = 1.05

    def __init__(self) -> None:
        self._snapshots: List[CriticalitySnapshot] = []
        self._current_level = CriticalityLevel.SUBCRITICAL
        log.info("CriticalDynamicsMonitor initialised")

    def record(self, branching_ratio: float, avalanche_size: float = 0.0) -> CriticalitySnapshot:
        level = self._classify(branching_ratio)
        snap = CriticalitySnapshot(
            level=level,
            branching_ratio=branching_ratio,
            avalanche_size=avalanche_size,
        )
        self._snapshots.append(snap)
        self._current_level = level
        return snap

    def _classify(self, ratio: float) -> CriticalityLevel:
        if ratio < self.CRITICAL_THRESHOLD - 0.1:
            return CriticalityLevel.SUBCRITICAL
        if ratio < self.CRITICAL_THRESHOLD:
            return CriticalityLevel.NEAR_CRITICAL
        if ratio <= self.SUPER_THRESHOLD:
            return CriticalityLevel.CRITICAL
        return CriticalityLevel.SUPERCRITICAL

    def get_current_level(self) -> CriticalityLevel:
        return self._current_level

    def get_snapshots(self) -> List[CriticalitySnapshot]:
        return list(self._snapshots)

    def is_critical(self) -> bool:
        return self._current_level in (
            CriticalityLevel.CRITICAL,
            CriticalityLevel.SUPERCRITICAL,
        )

    def reset(self) -> None:
        self._snapshots.clear()
        self._current_level = CriticalityLevel.SUBCRITICAL

    def to_dict(self) -> dict:
        return {
            "current_level": self._current_level.value,
            "snapshot_count": len(self._snapshots),
        }


_monitor: Optional[CriticalDynamicsMonitor] = None


def get_criticality_monitor() -> CriticalDynamicsMonitor:
    global _monitor
    if _monitor is None:
        _monitor = CriticalDynamicsMonitor()
    return _monitor
