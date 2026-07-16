"""
core/simulation/metrics.py

MetricsCollector — lightweight telemetry for simulation runs.

Captures:
  - Named scalar counters and gauges
  - Time-series records with step + timestamp
  - Aggregates (min, max, mean) on flush
  - Export to dict / JSON
"""

from __future__ import annotations

import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MetricRecord:
    """A single metric observation."""
    name: str
    value: float
    step: Optional[int] = None
    timestamp: float = field(default_factory=time.monotonic)
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    Collects and aggregates simulation metrics.

    Usage:
        m = MetricsCollector()
        m.record("reward", 1.0, step=5)
        m.increment("agent_errors")
        summary = m.dump()
    """

    def __init__(self) -> None:
        self._records: List[MetricRecord] = []
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record(
        self,
        name: str,
        value: float,
        step: Optional[int] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a single metric value."""
        self._records.append(
            MetricRecord(name=name, value=value, step=step, tags=tags or {})
        )
        self._gauges[name] = value

    def increment(self, name: str, amount: float = 1.0) -> None:
        """Increment a named counter."""
        self._counters[name] += amount

    def decrement(self, name: str, amount: float = 1.0) -> None:
        """Decrement a named counter."""
        self._counters[name] -= amount

    def gauge(self, name: str, value: float) -> None:
        """Set a gauge to an absolute value (no history)."""
        self._gauges[name] = value

    # ------------------------------------------------------------------
    # Aggregation / Export
    # ------------------------------------------------------------------

    def get_series(self, name: str) -> List[MetricRecord]:
        """Return all records for a given metric name."""
        return [r for r in self._records if r.name == name]

    def summary(self, name: str) -> Dict[str, Any]:
        """Return min/max/mean/count for a named metric."""
        series = [r.value for r in self.get_series(name)]
        if not series:
            return {"name": name, "count": 0}
        return {
            "name": name,
            "count": len(series),
            "min": min(series),
            "max": max(series),
            "mean": statistics.mean(series),
            "stdev": statistics.stdev(series) if len(series) > 1 else 0.0,
        }

    def dump(self) -> Dict[str, Any]:
        """Export all metrics to a serialisable dict."""
        metric_names = {r.name for r in self._records}
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "summaries": {name: self.summary(name) for name in metric_names},
            "total_records": len(self._records),
        }

    def reset(self) -> None:
        """Clear all collected data."""
        self._records.clear()
        self._counters.clear()
        self._gauges.clear()
