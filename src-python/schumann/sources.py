"""
Source adapters — convert external data into PlanetarySignalSample streams.

Each adapter implements the async generator protocol:

    async def stream(self) -> AsyncIterator[PlanetarySignalSample]: ...

Adapter registry
----------------
dev           — Deterministic synthetic dataset for local development/CI.
                Produces clean Schumann-like signal with configurable
                disturbance injection.  Zero network required.
noaa_ftp      — (stub) Future: pulls real-time Kp/Dst from NOAA FTP.
local_sensor  — (stub) Future: reads local magnetometer via serial/USB.

Adding a new adapter
--------------------
1. Subclass BaseSource.
2. Implement `async def stream()`.
3. Register in SOURCE_REGISTRY at the bottom of this file.
"""

from __future__ import annotations

import asyncio
import math
import random
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import AsyncIterator, Optional

from .models import PlanetarySignalSample


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class BaseSource(ABC):
    """Abstract base for all planetary signal sources."""

    source_id: str = "base"

    @abstractmethod
    async def stream(self) -> AsyncIterator[PlanetarySignalSample]:
        ...

    async def warmup(self) -> None:
        """Optional: run once before stream() is called."""

    async def teardown(self) -> None:
        """Optional: run once when engine shuts down."""


# ---------------------------------------------------------------------------
# Dev source  (deterministic, no network)
# ---------------------------------------------------------------------------

class DevSource(BaseSource):
    """
    Synthetic deterministic Schumann signal generator.

    Produces a signal centred on 7.83 Hz with realistic diurnal variation
    (±0.2 Hz over a simulated 24-hour cycle) and Gaussian noise.

    Parameters
    ----------
    tick_interval_s  : Seconds between emitted samples (default 5 s).
    inject_storm     : If True, inject a geomagnetic storm event after
                       60 ticks.  Useful for testing disturbance logic.
    seed             : RNG seed for reproducibility (default 42).
    """

    source_id = "dev"

    # SR harmonic frequencies (Hz)
    HARMONICS = {
        "f1": 7.83,
        "f2": 14.30,
        "f3": 20.80,
        "f4": 27.30,
        "f5": 33.80,
    }
    # Baseline harmonic amplitudes (normalised, f1 = 1.0)
    HARMONIC_BASELINES = {
        "f1": 1.00,
        "f2": 0.55,
        "f3": 0.30,
        "f4": 0.18,
        "f5": 0.10,
    }

    def __init__(
        self,
        tick_interval_s: float = 5.0,
        inject_storm: bool = False,
        seed: int = 42,
    ) -> None:
        self.tick_interval_s = tick_interval_s
        self.inject_storm    = inject_storm
        self._rng            = random.Random(seed)
        self._tick           = 0

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _diurnal_offset(self) -> float:
        """±0.2 Hz sinusoidal offset over a 24h simulated cycle."""
        phase = 2 * math.pi * (self._tick % 1440) / 1440
        return 0.2 * math.sin(phase)

    def _storm_kp(self) -> float:
        """Returns elevated Kp during injected storm window."""
        if self.inject_storm and 60 <= self._tick <= 80:
            return 0.7 + self._rng.gauss(0, 0.05)
        return 0.1 + self._rng.gauss(0, 0.02)

    async def stream(self) -> AsyncIterator[PlanetarySignalSample]:  # type: ignore[override]
        while True:
            self._tick += 1
            ts   = self._now()
            f1   = 7.83 + self._diurnal_offset() + self._rng.gauss(0, 0.05)
            kp   = max(0.0, min(1.0, self._storm_kp()))

            # Fundamental frequency channel
            yield PlanetarySignalSample(
                timestamp=ts, channel="sr_f1_freq",
                value=f1, unit="Hz", source=self.source_id,
            )

            # Amplitude channels for all harmonics
            for label, base_amp in self.HARMONIC_BASELINES.items():
                noise = self._rng.gauss(0, 0.03)
                amp   = max(0.0, base_amp + noise)
                yield PlanetarySignalSample(
                    timestamp=ts, channel=f"sr_{label}",
                    value=amp, unit="pT_norm", source=self.source_id,
                )

            # Geomagnetic activity
            yield PlanetarySignalSample(
                timestamp=ts, channel="geomag_kp",
                value=kp, unit="index", source=self.source_id,
            )

            await asyncio.sleep(self.tick_interval_s)


# ---------------------------------------------------------------------------
# NOAA FTP stub (future)
# ---------------------------------------------------------------------------

class NOAAFTPSource(BaseSource):
    """
    Stub: pull real-time Kp / Dst index from NOAA FTP.

    Implementation note: NOAA publishes 1-minute Kp estimates at:
        ftp://ftp.swpc.noaa.gov/pub/lists/geomag/
    This adapter is a stub.  Implement parse_kp_file() and
    integrate with asyncio / aiofiles when activating.
    """

    source_id = "noaa_ftp"

    async def stream(self) -> AsyncIterator[PlanetarySignalSample]:  # type: ignore[override]
        raise NotImplementedError(
            "NOAAFTPSource is a stub.  Activate with SCHUMANN_SOURCE=noaa_ftp "
            "only after implementing the FTP polling loop."
        )
        yield  # Make Python recognise this as an async generator


# ---------------------------------------------------------------------------
# Local sensor stub (future)
# ---------------------------------------------------------------------------

class LocalSensorSource(BaseSource):
    """
    Stub: read a locally-attached magnetometer (MMS-1 class or similar)
    via serial/USB.  Target noise floor: 0.4 pT/√Hz @ 128 Hz sample rate.
    """

    source_id = "local_sensor"

    async def stream(self) -> AsyncIterator[PlanetarySignalSample]:  # type: ignore[override]
        raise NotImplementedError(
            "LocalSensorSource is a stub.  Requires hardware + driver layer."
        )
        yield


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

SOURCE_REGISTRY: dict[str, type[BaseSource]] = {
    DevSource.source_id          : DevSource,
    NOAAFTPSource.source_id      : NOAAFTPSource,
    LocalSensorSource.source_id  : LocalSensorSource,
}


def build_source(source_id: str, **kwargs) -> BaseSource:
    """Factory: build a source adapter by its registry key."""
    if source_id not in SOURCE_REGISTRY:
        raise ValueError(
            f"Unknown source '{source_id}'. "
            f"Available: {list(SOURCE_REGISTRY)}"
        )
    return SOURCE_REGISTRY[source_id](**kwargs)
