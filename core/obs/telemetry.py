"""
core/obs/telemetry.py

Per-tool latency and error rate telemetry for GAIA-OS.
Tracks: call count, total latency, error count, p50/p95/p99 latency.
Thread-safe. No external dependencies.

Usage:
    from core.obs import get_telemetry
    tel = get_telemetry()
    tel.record("rag.query", latency_ms=42.3, error=False)
    print(tel.summary())
"""
import json
import threading
from collections import defaultdict
from typing import Any, Dict, List, Optional


class ToolMetrics:
    def __init__(self):
        self.call_count: int = 0
        self.error_count: int = 0
        self.total_latency_ms: float = 0.0
        self._latencies: List[float] = []
        self._lock = threading.Lock()

    def record(self, latency_ms: float, error: bool = False) -> None:
        with self._lock:
            self.call_count += 1
            self.total_latency_ms += latency_ms
            self._latencies.append(latency_ms)
            if error:
                self.error_count += 1

    def _percentile(self, p: float) -> Optional[float]:
        with self._lock:
            if not self._latencies:
                return None
            sorted_l = sorted(self._latencies)
            idx = max(0, int(len(sorted_l) * p / 100) - 1)
            return round(sorted_l[idx], 3)

    @property
    def avg_latency_ms(self) -> Optional[float]:
        with self._lock:
            if self.call_count == 0:
                return None
            return round(self.total_latency_ms / self.call_count, 3)

    @property
    def error_rate(self) -> float:
        with self._lock:
            if self.call_count == 0:
                return 0.0
            return round(self.error_count / self.call_count, 4)

    @property
    def p50(self) -> Optional[float]:
        return self._percentile(50)

    @property
    def p95(self) -> Optional[float]:
        return self._percentile(95)

    @property
    def p99(self) -> Optional[float]:
        return self._percentile(99)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_count": self.call_count,
            "error_count": self.error_count,
            "error_rate": self.error_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "p50_ms": self.p50,
            "p95_ms": self.p95,
            "p99_ms": self.p99,
        }


class Telemetry:
    """
    Global telemetry registry.
    One ToolMetrics instance per tool name.
    """

    def __init__(self):
        self._tools: Dict[str, ToolMetrics] = defaultdict(ToolMetrics)
        self._lock = threading.Lock()

    def record(self, tool: str, latency_ms: float, error: bool = False) -> None:
        with self._lock:
            metrics = self._tools[tool]
        metrics.record(latency_ms, error)

    def get(self, tool: str) -> Optional[ToolMetrics]:
        with self._lock:
            return self._tools.get(tool)

    def summary(self) -> Dict[str, Any]:
        with self._lock:
            return {name: m.to_dict() for name, m in self._tools.items()}

    def export_json(self) -> str:
        return json.dumps(self.summary(), indent=2)

    def reset(self, tool: Optional[str] = None) -> None:
        with self._lock:
            if tool:
                if tool in self._tools:
                    del self._tools[tool]
            else:
                self._tools.clear()
