"""tests/test_telemetry.py

Test scaffold for src-python/telemetry

Covers: TelemetryCollector, TelemetryEvent
"""
import pytest

from telemetry import TelemetryCollector
from telemetry.collector import TelemetryEvent


class TestTelemetryCollector:

    def test_initialises(self):
        collector = TelemetryCollector(service_name="nexus-test")
        assert collector.service_name == "nexus-test"
        assert collector.count() == 0

    def test_emit_stores_event(self):
        collector = TelemetryCollector()
        event = TelemetryEvent(source="schumann", event_type="metric", payload={"hz": 7.83})
        collector.emit(event)
        assert collector.count() == 1

    def test_record_metric_convenience(self):
        collector = TelemetryCollector()
        collector.record_metric(source="affectengine", name="arousal", value=0.72)
        assert collector.count() == 1

    def test_flush_clears_buffer(self):
        collector = TelemetryCollector()
        collector.record_metric("mesh", "latency_ms", 12.4)
        collector.record_metric("crystal", "resonance_hz", 7.83)
        events = collector.flush()
        assert len(events) == 2
        assert collector.count() == 0

    def test_flush_returns_events_in_order(self):
        collector = TelemetryCollector()
        collector.record_metric("a", "x", 1.0)
        collector.record_metric("b", "y", 2.0)
        events = collector.flush()
        assert events[0].source == "a"
        assert events[1].source == "b"
