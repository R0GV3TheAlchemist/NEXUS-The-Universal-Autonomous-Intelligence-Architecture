"""timeservice

NEXUS Time Synchronisation Service

Provides accurate, consistent time across distributed GAIAN nodes
using NTP/PTP synchronisation. Emits TimeSync events consumed by
the Schumann engine, StageEngine, and SovereignMemory.

Architecture reference:
    NEXUS_UNIVERSAL_OS.md  Domain 1.6 - Time Service
Research reference:
    NTP RFC 5905       - Network Time Protocol v4
    PTP IEEE 1588      - Precision Time Protocol
    ntplib (PyPI)      - Python NTP client
"""
from __future__ import annotations

from timeservice.engine import TimeService, TimeSyncConfig, TimeSyncEvent, TimeProvider

__all__ = ["TimeService", "TimeSyncConfig", "TimeSyncEvent", "TimeProvider"]
