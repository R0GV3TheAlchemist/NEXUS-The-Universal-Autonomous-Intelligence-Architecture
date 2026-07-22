"""timeservice.engine

NEXUS Time Synchronisation Service

Maintains a monotonic, NTP/PTP-synchronised clock for the NEXUS
distributed system. Emits TimeSyncEvent objects consumed by other
modules (Schumann, StageEngine, SovereignMemory).

Phase C: stub only.
Phase D: wire to ntplib / PTP daemon.

Research reference:
    NTP RFC 5905       - Network Time Protocol v4
    IEEE 1588 PTP      - sub-microsecond distributed time sync
    ntplib (PyPI)      - Python NTP reference implementation
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Optional

logger = logging.getLogger("timeservice.engine")


class SyncProtocol(Enum):
    """Time synchronisation protocol."""
    NTP = auto()    # Network Time Protocol (RFC 5905)
    PTP = auto()    # Precision Time Protocol (IEEE 1588)
    LOCAL = auto()  # System clock (fallback, not distributed-safe)


@dataclass
class TimeSyncConfig:
    """Configuration for the time synchronisation service.

    Fields:
        protocol:       Preferred sync protocol.
        ntp_servers:    List of NTP server hostnames/IPs.
        sync_interval:  How often to re-sync in seconds.
        max_drift_ms:   Maximum acceptable clock drift in milliseconds.
    """
    protocol: SyncProtocol = SyncProtocol.NTP
    ntp_servers: list[str] = field(default_factory=lambda: [
        "pool.ntp.org", "time.cloudflare.com", "time.google.com"
    ])
    sync_interval: float = 60.0
    max_drift_ms: float = 50.0


@dataclass
class TimeSyncEvent:
    """Time synchronisation event.

    Emitted after each successful sync cycle.

    Fields:
        synced_at:      UTC time of sync.
        offset_ms:      Measured clock offset in milliseconds.
        protocol:       Protocol used for this sync.
        authoritative:  True if synced to an external authority (NTP/PTP).
    """
    synced_at: datetime
    offset_ms: float
    protocol: SyncProtocol
    authoritative: bool = True


class TimeProvider:
    """Provides the current NEXUS system time.

    Phase C: returns UTC system time directly.
    Phase D: return NTP/PTP-corrected time offset.
    """

    def now(self) -> datetime:
        """Return the current UTC datetime."""
        return datetime.now(timezone.utc)


class TimeService:
    """NEXUS distributed time synchronisation service.

    Maintains a consistent clock reference across GAIAN nodes.
    Emits TimeSyncEvent on each sync cycle.

    Phase C: stubs only.
    Phase D: wire to ntplib for NTP sync; IEEE 1588 PTP daemon for sub-ms precision.
    """

    def __init__(self, config: TimeSyncConfig | None = None) -> None:
        self.config = config or TimeSyncConfig()
        self._provider = TimeProvider()
        self._last_sync: Optional[TimeSyncEvent] = None
        logger.info("TimeService initialised (protocol=%s).", self.config.protocol)

    @property
    def last_sync(self) -> Optional[TimeSyncEvent]:
        """Return the most recent TimeSyncEvent, or None if never synced."""
        return self._last_sync

    def now(self) -> datetime:
        """Return the current synchronised UTC time."""
        return self._provider.now()

    def sync(self) -> TimeSyncEvent:
        """Perform a time sync cycle against configured NTP servers.

        Returns:
            TimeSyncEvent describing the sync result.

        Raises:
            NotImplementedError: Always in Phase C.
                Expected: use ntplib to query NTP servers, compute offset,
                update internal clock correction, emit TimeSyncEvent.
        """
        raise NotImplementedError(
            "TimeService.sync() not implemented. "
            "Expected: ntplib.NTPClient().request(server) per server, "
            "compute mean offset, store as TimeSyncEvent."
        )
