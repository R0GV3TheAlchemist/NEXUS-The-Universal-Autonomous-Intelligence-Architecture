# Copyright (c) 2026 Kyle Alexander Steen (R0GV3 The Alchemist). All Rights Reserved.
# NEXUS Schumann Sync Engine — SyncPulse
# Phase E: Real operating tick loop — not specced, RUNNING.
# Emits a SyncReading every tick_interval_s seconds.
# Wires into the Planetary Ledger on every sync event.

from __future__ import annotations

import logging
import math
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schumann resonance physical constants
# ---------------------------------------------------------------------------
# Fundamental mode and first five harmonics (Hz)
SCHUMANN_FUNDAMENTAL_HZ: float = 7.83
SCHUMANN_HARMONICS_HZ: tuple[float, ...] = (
    7.83,    # 1st mode
    14.3,    # 2nd mode
    20.8,    # 3rd mode
    27.3,    # 4th mode
    33.8,    # 5th mode
)
# Alignment window: reading is "in-band" if within this tolerance (Hz)
ALIGNMENT_TOLERANCE_HZ: float = 0.5
# Coherence floor (amplitude normalised 0-1 below which we flag low-coherence)
COHERENCE_FLOOR: float = 0.3


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SyncReading:
    """One tick of Schumann sensor data."""
    frequency_hz: float          # Measured / simulated primary frequency
    amplitude: float             # Normalised 0.0 – 1.0
    coherence: float             # Normalised 0.0 – 1.0
    phase_offset_rad: float      # Phase offset from reference (radians)
    timestamp: str               # ISO-8601 UTC
    source: str                  # e.g. "simulated", "sensor:station-1"
    harmonic_profile: tuple[float, ...] = field(default_factory=tuple)

    @property
    def in_band(self) -> bool:
        return abs(self.frequency_hz - SCHUMANN_FUNDAMENTAL_HZ) <= ALIGNMENT_TOLERANCE_HZ

    @property
    def high_coherence(self) -> bool:
        return self.coherence >= COHERENCE_FLOOR

    @property
    def alignment_score(self) -> float:
        """
        0.0 – 1.0.  Combines frequency proximity and coherence.
        score = coherence * (1 - |delta_f| / tolerance) clamped to [0, 1].
        """
        delta = abs(self.frequency_hz - SCHUMANN_FUNDAMENTAL_HZ)
        freq_score = max(0.0, 1.0 - delta / ALIGNMENT_TOLERANCE_HZ)
        return round(self.coherence * freq_score, 4)

    def to_dict(self) -> dict[str, Any]:
        return {
            "frequency_hz": self.frequency_hz,
            "amplitude": self.amplitude,
            "coherence": self.coherence,
            "phase_offset_rad": self.phase_offset_rad,
            "timestamp": self.timestamp,
            "source": self.source,
            "in_band": self.in_band,
            "high_coherence": self.high_coherence,
            "alignment_score": self.alignment_score,
            "harmonic_profile": list(self.harmonic_profile),
        }


@dataclass
class SyncState:
    """Accumulated engine state across ticks."""
    tick_count: int = 0
    in_band_count: int = 0
    high_coherence_count: int = 0
    last_reading: SyncReading | None = None
    running_alignment_sum: float = 0.0

    @property
    def mean_alignment_score(self) -> float:
        if self.tick_count == 0:
            return 0.0
        return round(self.running_alignment_sum / self.tick_count, 4)

    @property
    def in_band_ratio(self) -> float:
        if self.tick_count == 0:
            return 0.0
        return round(self.in_band_count / self.tick_count, 4)


# ---------------------------------------------------------------------------
# Simulated sensor (no hardware required)
# ---------------------------------------------------------------------------

class SimulatedSchumannSensor:
    """
    Physics-grounded simulation of a Schumann resonance sensor.
    Frequency drifts slowly around the fundamental using a low-frequency
    sinusoidal perturbation + small Gaussian noise — realistic for ELF
    monitoring stations.
    """

    def __init__(self, seed_offset: float = 0.0) -> None:
        self._t0 = time.monotonic()
        self._seed_offset = seed_offset

    def read(self) -> SyncReading:
        t = time.monotonic() - self._t0 + self._seed_offset
        # Slow drift: period ~120 s, amplitude ±0.4 Hz
        drift = 0.4 * math.sin(2 * math.pi * t / 120.0)
        # Micro-noise: ±0.05 Hz
        noise = 0.05 * math.sin(2 * math.pi * t * 7.3 + 1.1)
        frequency = SCHUMANN_FUNDAMENTAL_HZ + drift + noise

        # Coherence oscillates between 0.4 and 0.95
        coherence = 0.675 + 0.275 * math.sin(2 * math.pi * t / 60.0 + 0.5)
        coherence = max(0.0, min(1.0, coherence))

        # Amplitude follows coherence loosely
        amplitude = 0.5 + 0.4 * math.sin(2 * math.pi * t / 90.0)
        amplitude = max(0.0, min(1.0, amplitude))

        phase_offset = (2 * math.pi * t / 10.0) % (2 * math.pi)

        # Harmonic profile: each harmonic gets slight independent drift
        harmonic_profile = tuple(
            round(h + 0.1 * math.sin(2 * math.pi * t / (30.0 + i * 10.0)), 3)
            for i, h in enumerate(SCHUMANN_HARMONICS_HZ)
        )

        return SyncReading(
            frequency_hz=round(frequency, 4),
            amplitude=round(amplitude, 4),
            coherence=round(coherence, 4),
            phase_offset_rad=round(phase_offset, 4),
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="simulated",
            harmonic_profile=harmonic_profile,
        )


# ---------------------------------------------------------------------------
# SyncPulse engine
# ---------------------------------------------------------------------------

SyncCallback = Callable[[SyncReading, SyncState], None]


class SyncPulse:
    """
    The NEXUS Schumann Sync Engine.

    Runs a background thread that emits a SyncReading every tick_interval_s.
    Wires into the Planetary Ledger (optional) on every sync event.
    Subscribers receive (SyncReading, SyncState) on each tick.

    Usage::

        from schumann.sync_pulse import SyncPulse
        from planetary_ledger import PlanetaryLedger

        ledger = PlanetaryLedger()
        engine = SyncPulse(ledger=ledger, tick_interval_s=1.0)
        engine.subscribe(lambda r, s: print(r.alignment_score))
        engine.start()
        time.sleep(5)
        engine.stop()
    """

    def __init__(
        self,
        tick_interval_s: float = 5.0,
        sensor: SimulatedSchumannSensor | None = None,
        ledger: Any | None = None,      # PlanetaryLedger — optional
        session_id: str | None = None,
    ) -> None:
        self._tick_interval = tick_interval_s
        self._sensor = sensor or SimulatedSchumannSensor()
        self._ledger = ledger
        self._session_id = session_id
        self._state = SyncState()
        self._subscribers: list[SyncCallback] = []
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def subscribe(self, callback: SyncCallback) -> None:
        """Register a callback invoked on every tick: callback(reading, state)."""
        with self._lock:
            self._subscribers.append(callback)

    def start(self) -> None:
        """Start the sync loop in a daemon background thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="SchumannSyncPulse",
            daemon=True,
        )
        self._thread.start()
        logger.info("SyncPulse started (interval=%.1fs)", self._tick_interval)

    def stop(self, timeout: float = 10.0) -> None:
        """Signal the loop to stop and wait for the thread to exit."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
        logger.info("SyncPulse stopped after %d ticks", self._state.tick_count)

    def tick(self) -> SyncReading:
        """Fire one synchronous tick (useful for testing / manual control)."""
        reading = self._sensor.read()
        self._process(reading)
        return reading

    @property
    def state(self) -> SyncState:
        return self._state

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive() and not self._stop_event.is_set())

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                reading = self._sensor.read()
                self._process(reading)
            except Exception:
                logger.exception("SyncPulse tick error")
            self._stop_event.wait(timeout=self._tick_interval)

    def _process(self, reading: SyncReading) -> None:
        with self._lock:
            self._state.tick_count += 1
            self._state.last_reading = reading
            self._state.running_alignment_sum += reading.alignment_score
            if reading.in_band:
                self._state.in_band_count += 1
            if reading.high_coherence:
                self._state.high_coherence_count += 1

        # Write to Planetary Ledger
        if self._ledger is not None:
            try:
                from planetary_ledger import EventType
                self._ledger.append(
                    event_type=EventType.SCHUMANN_SYNC,
                    payload=reading.to_dict(),
                    tags=["schumann", "phase-e"],
                    session_id=self._session_id,
                )
            except Exception:
                logger.exception("SyncPulse ledger write failed")

        # Notify subscribers
        with self._lock:
            subs = list(self._subscribers)
        for cb in subs:
            try:
                cb(reading, self._state)
            except Exception:
                logger.exception("SyncPulse subscriber error")

        logger.debug(
            "tick=%d freq=%.4fHz score=%.4f in_band=%s",
            self._state.tick_count,
            reading.frequency_hz,
            reading.alignment_score,
            reading.in_band,
        )
