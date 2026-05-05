"""
SchumannEngine — the core processing loop for Issue #64.

Responsibilities
----------------
1. Collect PlanetarySignalSample from one or more source adapters.
2. Maintain rolling 24-hour baselines per channel.
3. Classify disturbance level from deviation in σ units.
4. Compute alignment_score with fixed, documented weights.
5. Emit SchumannState on each tick — the only output consumed by
   Stage Engine (#63).

Alignment score formula (bounded to [0, 1])
------------------------------------------
    alignment = 0.45 × stability
              + 0.30 × harmonic_coherence
              + 0.25 × signal_quality

where:
  stability          = 1 - min(abs(deviation_sigma) / 4, 1)
  harmonic_coherence = mean of normalised harmonic powers (f1..f5)
  signal_quality     = mean of per-sample quality flags in the window

All experimental outputs are gated behind `SCHUMANN_EXPERIMENTAL=1`
and placed in SchumannState.experimental_flags only.
"""

from __future__ import annotations

import asyncio
import collections
import logging
import os
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Deque, Dict, List, Optional

from .models import DisturbanceLevel, PlanetarySignalSample, SchumannState
from .sources import BaseSource, build_source

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class EngineConfig:
    """
    Runtime configuration for SchumannEngine.

    Parameters
    ----------
    source              : Source adapter key ("dev" | "noaa_ftp" | "local_sensor").
    source_kwargs       : Extra kwargs forwarded to the source constructor.
    window_size         : Number of most-recent samples kept per channel
                          for baseline and deviation calculations.
    staleness_threshold : Seconds before a channel is considered stale.
    min_quality         : Samples below this quality are discarded.
    experimental        : Enable experimental outputs (feature flag).
    on_state_change     : Optional callback(old: SchumannState, new: SchumannState).
                          Called every time disturbance_level changes.
    """
    source              : str                           = "dev"
    source_kwargs       : dict                          = field(default_factory=dict)
    window_size         : int                           = 2880   # 4h @ 5s ticks
    staleness_threshold : float                         = 30.0   # seconds
    min_quality         : float                         = 0.3
    experimental        : bool                          = False
    on_state_change     : Optional[Callable]            = None

    def __post_init__(self) -> None:
        if self.experimental:
            return
        # Respect environment variable override
        if os.getenv("SCHUMANN_EXPERIMENTAL", "0") == "1":
            self.experimental = True


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class SchumannEngine:
    """
    Main Schumann Alignment Layer service.

    Usage::

        config = EngineConfig(source="dev", source_kwargs={"inject_storm": True})
        engine = SchumannEngine(config)
        await engine.start()

        state = await engine.tick()
        print(state.alignment_score)

        await engine.stop()
    """

    HARMONIC_CHANNELS = ["sr_f1", "sr_f2", "sr_f3", "sr_f4", "sr_f5"]
    FREQ_CHANNEL      = "sr_f1_freq"
    KP_CHANNEL        = "geomag_kp"

    def __init__(self, config: EngineConfig) -> None:
        self.config  = config
        self._source : BaseSource = build_source(
            config.source, **config.source_kwargs
        )
        # Rolling windows: channel -> deque of (timestamp, value, quality)
        self._windows: Dict[str, Deque] = collections.defaultdict(
            lambda: collections.deque(maxlen=config.window_size)
        )
        self._last_state: Optional[SchumannState] = None
        self._running    = False
        self._bg_task: Optional[asyncio.Task] = None

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    async def start(self) -> None:
        """Start background ingestion loop."""
        await self._source.warmup()
        self._running  = True
        self._bg_task  = asyncio.create_task(self._ingest_loop())
        logger.info("SchumannEngine started (source=%s)", self.config.source)

    async def stop(self) -> None:
        """Stop background ingestion loop."""
        self._running = False
        if self._bg_task:
            self._bg_task.cancel()
            try:
                await self._bg_task
            except asyncio.CancelledError:
                pass
        await self._source.teardown()
        logger.info("SchumannEngine stopped.")

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    async def tick(self) -> SchumannState:
        """
        Compute and return the current SchumannState.

        This is the ONLY method Stage Engine (#63) should call.
        It is safe to call every second — computation is O(window_size).
        """
        state = self._compute_state()
        if (
            self._last_state is not None
            and self._last_state.disturbance_level != state.disturbance_level
            and self.config.on_state_change is not None
        ):
            try:
                self.config.on_state_change(self._last_state, state)
            except Exception:
                logger.exception("on_state_change callback raised")
        self._last_state = state
        return state

    @property
    def last_state(self) -> Optional[SchumannState]:
        return self._last_state

    # ------------------------------------------------------------------ #
    # Internal: ingestion loop
    # ------------------------------------------------------------------ #

    async def _ingest_loop(self) -> None:
        """Continuously pull samples from source into rolling windows."""
        try:
            async for sample in self._source.stream():
                if not self._running:
                    break
                if sample.quality < self.config.min_quality:
                    logger.debug(
                        "Discarding low-quality sample: ch=%s q=%.2f",
                        sample.channel, sample.quality,
                    )
                    continue
                self._windows[sample.channel].append(
                    (sample.timestamp, sample.value, sample.quality)
                )
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("SchumannEngine ingest loop crashed")

    # ------------------------------------------------------------------ #
    # Internal: state computation
    # ------------------------------------------------------------------ #

    def _compute_state(self) -> SchumannState:
        now = datetime.now(timezone.utc)
        staleness_cutoff = now - timedelta(seconds=self.config.staleness_threshold)

        # --- Fundamental frequency ---
        freq_vals  = self._fresh_values(self.FREQ_CHANNEL, staleness_cutoff)
        fundamental_hz = statistics.mean(freq_vals) if freq_vals else 7.83
        baseline_hz    = self._baseline(self.FREQ_CHANNEL)
        deviation      = self._deviation_sigma(self.FREQ_CHANNEL, freq_vals)

        # --- Harmonic powers ---
        harmonic_power: Dict[str, float] = {}
        for ch in self.HARMONIC_CHANNELS:
            label  = ch.split("_")[1]  # sr_f1 -> f1
            vals   = self._fresh_values(ch, staleness_cutoff)
            harmonic_power[label] = statistics.mean(vals) if vals else 0.0

        # --- Geomagnetic activity ---
        kp_vals = self._fresh_values(self.KP_CHANNEL, staleness_cutoff)
        geo_activity = statistics.mean(kp_vals) if kp_vals else 0.0
        geo_activity = max(0.0, min(1.0, geo_activity))

        # --- Signal quality ---
        all_qualities: List[float] = []
        for ch_deque in self._windows.values():
            for ts, val, q in ch_deque:
                if ts >= staleness_cutoff:
                    all_qualities.append(q)
        signal_quality = statistics.mean(all_qualities) if all_qualities else 0.0

        # --- Disturbance level ---
        disturbance = self._classify_disturbance(
            deviation=deviation,
            signal_quality=signal_quality,
            has_data=bool(freq_vals),
        )

        # --- Alignment score ---
        stability          = max(0.0, 1.0 - min(abs(deviation) / 4.0, 1.0))
        harmonic_coherence = (
            statistics.mean(harmonic_power.values())
            if harmonic_power else 0.0
        )
        harmonic_coherence = max(0.0, min(1.0, harmonic_coherence))
        alignment_score    = (
            0.45 * stability
            + 0.30 * harmonic_coherence
            + 0.25 * signal_quality
        )
        alignment_score = max(0.0, min(1.0, alignment_score))

        # --- Confidence ---
        confidence = self._compute_confidence(
            signal_quality=signal_quality,
            disturbance=disturbance,
            n_fresh_freq=len(freq_vals),
        )

        # --- Experimental flags (feature-gated) ---
        experimental: Dict[str, float] = {}
        if self.config.experimental:
            experimental["quantum_bio_coupling"]    = 0.0  # Not yet computed
            experimental["seismic_precursor_score"] = 0.0  # CNN-BiGRU stub
            experimental["laic_channel_state"]      = 0.0  # LAIC stub

        source_ids = list({
            row[0].strftime("%Y") for row in
            list(self._windows.get(self.FREQ_CHANNEL, []))
        })
        # Simple: just report the source adapter ID
        source_ids = [self._source.source_id]

        state = SchumannState(
            timestamp            = now,
            fundamental_hz       = fundamental_hz,
            harmonic_power       = harmonic_power,
            geomagnetic_activity = geo_activity,
            signal_quality       = signal_quality,
            disturbance_level    = disturbance,
            alignment_score      = alignment_score,
            confidence           = confidence,
            source_ids           = source_ids,
            baseline_hz          = baseline_hz,
            deviation_sigma      = deviation,
            experimental_flags   = experimental,
        )
        logger.debug(
            "SchumannState: f=%.3fHz dist=%s align=%.3f conf=%.3f",
            state.fundamental_hz,
            state.disturbance_level.value,
            state.alignment_score,
            state.confidence,
        )
        return state

    # ------------------------------------------------------------------ #
    # Internal: helpers
    # ------------------------------------------------------------------ #

    def _fresh_values(
        self, channel: str, cutoff: datetime
    ) -> List[float]:
        return [
            val for ts, val, q in self._windows.get(channel, [])
            if ts >= cutoff
        ]

    def _baseline(self, channel: str) -> float:
        vals = [v for _, v, _ in self._windows.get(channel, [])]
        return statistics.mean(vals) if vals else 7.83

    def _deviation_sigma(self, channel: str, fresh: List[float]) -> float:
        """Deviation of current fresh values from historical mean, in σ."""
        all_vals = [v for _, v, _ in self._windows.get(channel, [])]
        if len(all_vals) < 5 or not fresh:
            return 0.0
        try:
            mu    = statistics.mean(all_vals)
            sigma = statistics.stdev(all_vals)
            if sigma < 1e-9:
                return 0.0
            return (statistics.mean(fresh) - mu) / sigma
        except statistics.StatisticsError:
            return 0.0

    @staticmethod
    def _classify_disturbance(
        deviation: float,
        signal_quality: float,
        has_data: bool,
    ) -> DisturbanceLevel:
        if not has_data or signal_quality < 0.2:
            return DisturbanceLevel.UNAVAILABLE
        abs_dev = abs(deviation)
        if abs_dev > 2.0 or signal_quality < 0.5:
            return DisturbanceLevel.DISTURBED
        if abs_dev > 1.0:
            return DisturbanceLevel.ELEVATED
        return DisturbanceLevel.STABLE

    @staticmethod
    def _compute_confidence(
        signal_quality: float,
        disturbance: DisturbanceLevel,
        n_fresh_freq: int,
    ) -> float:
        base = signal_quality
        if disturbance == DisturbanceLevel.UNAVAILABLE:
            base *= 0.1
        elif disturbance == DisturbanceLevel.DISTURBED:
            base *= 0.6
        if n_fresh_freq < 3:
            base *= 0.5
        return max(0.0, min(1.0, base))
