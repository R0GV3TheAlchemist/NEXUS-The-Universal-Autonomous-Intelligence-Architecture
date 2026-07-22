"""telemetry

NEXUS Telemetry Collector

Provides the TelemetryCollector class used by src-python/main.py
via the sidecar telemetry integration. This module acts as the
local telemetry wrapper for NEXUS, forwarding structured events
to the configured backend (Prometheus, OpenTelemetry, or logging).

Architecture reference:
    NEXUS_UNIVERSAL_OS.md  Domain 1.7 - Telemetry
Integration:
    main.py imports: from sidecar.telemetry import TelemetryCollector
    This module provides the local stub until sidecar is wired.
"""
from __future__ import annotations

from telemetry.collector import TelemetryCollector

__all__ = ["TelemetryCollector"]
