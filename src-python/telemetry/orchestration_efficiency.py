"""Issue #188 + #190 — Orchestration Efficiency (OE) metric.

OE = (successful_tasks × avg_dq_score) / (avg_total_latency_s × avg_engine_count)

Higher OE = high quality delivered fast with fewer engines (minimal waste).
Low OE = slow engines, too many engines invoked, low DQ, or many fallbacks.

Canon C05: OE trends are transparently surfaced in the Glass Room dashboard.
Canon C01: OERouter suggestions require user approval before routing changes.
"""
from __future__ import annotations

import statistics
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class OEWindowDuration(str, Enum):
    HOUR_1 = "1h"
    HOUR_24 = "24h"
    DAY_7 = "7d"
    DAY_30 = "30d"


# Number of seconds in each window
_WINDOW_SECONDS: dict[OEWindowDuration, int] = {
    OEWindowDuration.HOUR_1: 3_600,
    OEWindowDuration.HOUR_24: 86_400,
    OEWindowDuration.DAY_7: 604_800,
    OEWindowDuration.DAY_30: 2_592_000,
}


@dataclass
class OrchestrationEfficiencyRecord:
    """A single orchestration run's contribution to OE."""
    session_id: str
    intent_class: str
    engines_invoked: list[str]
    total_latency_s: float
    dq_score: float
    degraded: bool
    timestamp: float = field(default_factory=time.time)
    conflict_detected: bool = False

    @property
    def engine_count(self) -> int:
        return len(self.engines_invoked)


@dataclass
class OrchestrationEfficiencyWindow:
    """Aggregated OE metrics over a rolling time window."""
    window: OEWindowDuration
    computed_at: float = field(default_factory=time.time)

    successful_tasks: int = 0
    failed_tasks: int = 0
    total_tasks: int = 0

    avg_total_latency_s: float = 0.0
    avg_engine_count: float = 0.0
    avg_dq_score: float = 0.0
    degraded_fraction: float = 0.0
    conflict_fraction: float = 0.0

    oe_score: float = 0.0               # Composite OE metric
    bottleneck_hint: str | None = None  # Intent class with highest avg latency

    def to_dict(self) -> dict[str, Any]:
        return {
            "window": self.window.value,
            "computed_at": self.computed_at,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "total_tasks": self.total_tasks,
            "avg_total_latency_s": round(self.avg_total_latency_s, 3),
            "avg_engine_count": round(self.avg_engine_count, 2),
            "avg_dq_score": round(self.avg_dq_score, 3),
            "degraded_fraction": round(self.degraded_fraction, 3),
            "conflict_fraction": round(self.conflict_fraction, 3),
            "oe_score": round(self.oe_score, 4),
            "bottleneck_hint": self.bottleneck_hint,
        }


class OrchestrationEfficiencyService:
    """Computes and stores OE records; produces rolling-window aggregates."""

    def __init__(self) -> None:
        self._records: list[OrchestrationEfficiencyRecord] = []

    def record(self, rec: OrchestrationEfficiencyRecord) -> None:
        """Append a new OE record."""
        self._records.append(rec)
        # Prune records older than 30 days to keep memory bounded
        cutoff = time.time() - _WINDOW_SECONDS[OEWindowDuration.DAY_30]
        self._records = [r for r in self._records if r.timestamp >= cutoff]

    def compute_window(
        self, duration: OEWindowDuration = OEWindowDuration.HOUR_24
    ) -> OrchestrationEfficiencyWindow:
        """Compute an OE aggregate for the given time window."""
        cutoff = time.time() - _WINDOW_SECONDS[duration]
        window_records = [r for r in self._records if r.timestamp >= cutoff]

        if not window_records:
            return OrchestrationEfficiencyWindow(window=duration)

        total = len(window_records)
        # A task is "successful" if it completed (dq_score > 0)
        successful = [r for r in window_records if r.dq_score > 0]
        failed = total - len(successful)

        latencies = [r.total_latency_s for r in window_records]
        engine_counts = [r.engine_count for r in window_records]
        dq_scores = [r.dq_score for r in successful] if successful else [0.0]
        degraded_count = sum(1 for r in window_records if r.degraded)
        conflict_count = sum(1 for r in window_records if r.conflict_detected)

        avg_latency = statistics.mean(latencies)
        avg_engines = statistics.mean(engine_counts)
        avg_dq = statistics.mean(dq_scores)

        # OE = (successful_tasks × avg_dq) / (avg_latency × avg_engine_count)
        # Guard against division-by-zero
        if avg_latency > 0 and avg_engines > 0:
            oe = (len(successful) * avg_dq) / (avg_latency * avg_engines)
        else:
            oe = 0.0

        # Identify bottleneck intent class (highest avg latency)
        intent_latencies: dict[str, list[float]] = {}
        for r in window_records:
            intent_latencies.setdefault(r.intent_class, []).append(r.total_latency_s)
        bottleneck = max(
            intent_latencies,
            key=lambda k: statistics.mean(intent_latencies[k]),
            default=None,
        )

        return OrchestrationEfficiencyWindow(
            window=duration,
            successful_tasks=len(successful),
            failed_tasks=failed,
            total_tasks=total,
            avg_total_latency_s=avg_latency,
            avg_engine_count=avg_engines,
            avg_dq_score=avg_dq,
            degraded_fraction=degraded_count / total,
            conflict_fraction=conflict_count / total,
            oe_score=oe,
            bottleneck_hint=bottleneck,
        )

    def compute_all_windows(self) -> dict[str, dict[str, Any]]:
        """Compute OE for all four standard windows. Used by Glass Room dashboard."""
        return {
            d.value: self.compute_window(d).to_dict()
            for d in OEWindowDuration
        }
