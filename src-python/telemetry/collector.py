"""telemetry.collector

NEXUS Telemetry Collector

Collects and emits structured telemetry events from all NEXUS modules.
Phase C: stub that logs events to the Python logging system.
Phase D: wire to OpenTelemetry SDK or Prometheus push gateway.

Reference:
    OpenTelemetry Python SDK - opentelemetry-api, opentelemetry-sdk
    Prometheus client       - prometheus-client
    NEXUS_UNIVERSAL_OS.md   Domain 1.7
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

logger = logging.getLogger("telemetry.collector")


@dataclass
class TelemetryEvent:
    """A structured telemetry event.

    Fields:
        source:     Module or component emitting the event.
        event_type: Event category (e.g., 'metric', 'trace', 'log').
        payload:    Structured data payload.
        timestamp:  UTC emission time.
        trace_id:   Optional distributed trace ID.
    """
    source: str
    event_type: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    trace_id: Optional[str] = None


class TelemetryCollector:
    """NEXUS telemetry event collector.

    Phase C: buffers events and logs them via Python logging.
    Phase D: forward to OpenTelemetry exporter or Prometheus.

    Reference:
        OpenTelemetry Python SDK.
        NEXUS_UNIVERSAL_OS.md Domain 1.7.
    """

    def __init__(self, service_name: str = "nexus") -> None:
        self.service_name = service_name
        self._events: list[TelemetryEvent] = []
        logger.info("TelemetryCollector initialised (service=%s).", service_name)

    def emit(self, event: TelemetryEvent) -> None:
        """Emit a telemetry event.

        Phase C: appends to internal buffer and logs.
        Phase D: forward to OpenTelemetry / Prometheus exporter.
        """
        self._events.append(event)
        logger.debug(
            "[TELEMETRY] %s | %s | %s | %s",
            event.source,
            event.event_type,
            event.timestamp.isoformat(),
            event.payload,
        )

    def record_metric(
        self,
        source: str,
        name: str,
        value: float,
        labels: Optional[Mapping[str, str]] = None,
    ) -> None:
        """Convenience method to record a numeric metric.

        Args:
            source: Module emitting the metric.
            name:   Metric name (e.g., 'affect.arousal').
            value:  Numeric value.
            labels: Optional key-value label pairs.
        """
        self.emit(TelemetryEvent(
            source=source,
            event_type="metric",
            payload={"name": name, "value": value, "labels": labels or {}},
        ))

    def flush(self) -> list[TelemetryEvent]:
        """Flush and return all buffered events.

        Phase D: this will trigger export to the configured backend.
        """
        events = list(self._events)
        self._events.clear()
        return events

    def count(self) -> int:
        """Return the number of buffered events."""
        return len(self._events)
