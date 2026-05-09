"""
core/schumann_alignment.py

GAIA-OS Schumann Biometric Alignment — Python Sidecar
Pillar II: Viriditas
Issue: #64 (Phase 2)
Version: v1.0.0

Pipeline:
  [Wearable cache] ──► HRVNormalizer ──► coherence score
  [Schumann feed]  ──► SchumannParser ──► schumann score
                                          │
                              compute_alignment() → 0–100
                                          │
                              AlignmentStateEmitter → IPC JSON

All biometric data stays on-device.  Schumann feed is fetched
anonymously.  No user identity leaves the process boundary.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
import math
import statistics
from collections import deque
from datetime import datetime, timezone
from typing import Deque, List, Literal, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

UiTier = Literal["minimal", "core", "standard", "full", "vibrant"]


@dataclasses.dataclass(frozen=True)
class AlignmentState:
    """Canonical output struct emitted to Tauri IPC."""

    score: float          # 0–100
    hrv_score: float      # normalised HRV (0–100, 50 = personal baseline)
    schumann_score: float # normalised Schumann amplitude (0–100)
    solar_kp: float       # raw Kp index at time of computation
    ui_tier: UiTier
    last_updated: str     # ISO-8601 UTC
    fallback_mode: str    # empty string when all feeds healthy

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self))


# ---------------------------------------------------------------------------
# Tier mapping
# ---------------------------------------------------------------------------

def score_to_ui_tier(score: float) -> UiTier:
    """
    Map alignment score 0–100 → UI tier.

    80–100  vibrant
    60–79   full
    40–59   standard
    20–39   core
     0–19   minimal
    """
    if score >= 80:
        return "vibrant"
    if score >= 60:
        return "full"
    if score >= 40:
        return "standard"
    if score >= 20:
        return "core"
    return "minimal"


# ---------------------------------------------------------------------------
# Core formula  (spec: SCHUMANN_BIOMETRIC_ALIGNMENT_SPEC.md §Step 3)
# ---------------------------------------------------------------------------

def compute_alignment(
    hrv_score: float,
    schumann_score: float,
    solar_kp: float,
) -> float:
    """
    Compute the Schumann–HRV alignment score (0–100).

    Args:
        hrv_score:       Normalised HRV score, 0–100.
                         50 represents the user's 30-day personal baseline.
        schumann_score:  Normalised Schumann amplitude, 0–100.
                         Derived from 7.83 Hz band power vs 30-day mean.
        solar_kp:        Raw NOAA Kp index (0–9 scale).
                         High geomagnetic activity penalises alignment.

    Returns:
        Alignment score clamped to [0, 100].

    Formula (per spec):
        base      = 100 - |hrv_score - schumann_score|
        kp_penalty = min(solar_kp * 3, 30)
        score     = max(0, base - kp_penalty)
    """
    if not (0.0 <= hrv_score <= 100.0):
        raise ValueError(f"hrv_score must be 0–100, got {hrv_score}")
    if not (0.0 <= schumann_score <= 100.0):
        raise ValueError(f"schumann_score must be 0–100, got {schumann_score}")
    if solar_kp < 0:
        raise ValueError(f"solar_kp must be ≥ 0, got {solar_kp}")

    base: float = 100.0 - abs(hrv_score - schumann_score)
    kp_penalty: float = min(solar_kp * 3.0, 30.0)
    return max(0.0, base - kp_penalty)


# ---------------------------------------------------------------------------
# HRV Normaliser
# ---------------------------------------------------------------------------

class HRVNormalizer:
    """
    Converts raw RMSSD (ms) to a 0–100 score anchored to the
    user's rolling 30-day personal baseline.

    Score 50 always = personal baseline mean.
    Score 100 = baseline + 2σ (or above).
    Score 0   = baseline − 2σ (or below).

    Args:
        window_days: Rolling baseline window in days (default 30).
                     Each "sample" is treated as one measurement.
        max_samples: Hard cap on deque length to bound memory.
    """

    def __init__(
        self,
        window_days: int = 30,
        max_samples: int = 1440,  # 1 sample/min × 24h × 60 min worst case
    ) -> None:
        self._window_days = window_days
        self._history: Deque[float] = deque(maxlen=max_samples)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest(self, rmssd_ms: float) -> None:
        """Feed a new raw RMSSD reading into the rolling window."""
        if rmssd_ms < 0:
            raise ValueError(f"RMSSD must be ≥ 0 ms, got {rmssd_ms}")
        self._history.append(rmssd_ms)

    def normalize(self, rmssd_ms: float) -> float:
        """
        Normalise a raw RMSSD reading to 0–100 using the stored
        rolling baseline.  Returns 50.0 when history is too short
        to compute a meaningful baseline (<2 samples).
        """
        if rmssd_ms < 0:
            raise ValueError(f"RMSSD must be ≥ 0 ms, got {rmssd_ms}")

        if len(self._history) < 2:
            logger.debug("HRVNormalizer: insufficient history, returning baseline 50.0")
            return 50.0

        mean = statistics.mean(self._history)
        stdev = statistics.stdev(self._history)

        if stdev == 0.0:
            return 50.0

        z = (rmssd_ms - mean) / stdev          # z-score relative to baseline
        score = 50.0 + (z / 2.0) * 50.0       # map ±2σ → 0–100
        return max(0.0, min(100.0, score))

    @property
    def baseline_mean(self) -> Optional[float]:
        """Current rolling baseline mean (ms), or None if insufficient data."""
        return statistics.mean(self._history) if len(self._history) >= 2 else None

    @property
    def sample_count(self) -> int:
        return len(self._history)


# ---------------------------------------------------------------------------
# Schumann Parser
# ---------------------------------------------------------------------------

class SchumannParser:
    """
    Normalises raw Schumann 7.83 Hz band-power readings from the
    HeartMath GCI feed (or NOAA GOES fallback) to a 0–100 score
    anchored to a 30-day rolling mean.

    Semantics mirror HRVNormalizer: score 50 = historical mean,
    score 100 = mean + 2σ, score 0 = mean − 2σ.
    """

    def __init__(self, max_samples: int = 4320) -> None:  # ~30 days at 10-min intervals
        self._history: Deque[float] = deque(maxlen=max_samples)

    def ingest(self, amplitude: float) -> None:
        """Feed a raw 7.83 Hz band-power amplitude reading."""
        if amplitude < 0:
            raise ValueError(f"Schumann amplitude must be ≥ 0, got {amplitude}")
        self._history.append(amplitude)

    def normalize(self, amplitude: float) -> float:
        """
        Normalise a raw Schumann amplitude to 0–100 against the
        rolling 30-day baseline.  Returns 50.0 when history is
        too short (<2 samples).
        """
        if amplitude < 0:
            raise ValueError(f"Schumann amplitude must be ≥ 0, got {amplitude}")

        if len(self._history) < 2:
            logger.debug("SchumannParser: insufficient history, returning baseline 50.0")
            return 50.0

        mean = statistics.mean(self._history)
        stdev = statistics.stdev(self._history)

        if stdev == 0.0:
            return 50.0

        z = (amplitude - mean) / stdev
        score = 50.0 + (z / 2.0) * 50.0
        return max(0.0, min(100.0, score))

    @property
    def sample_count(self) -> int:
        return len(self._history)


# ---------------------------------------------------------------------------
# Alignment State Emitter
# ---------------------------------------------------------------------------

class AlignmentStateEmitter:
    """
    Orchestrates the full pipeline and emits AlignmentState structs
    ready for Tauri IPC consumption.

    Usage (within Tauri Python sidecar main loop):

        emitter = AlignmentStateEmitter(hrv_normalizer, schumann_parser)
        state = await emitter.compute(
            raw_rmssd=55.0,
            raw_schumann_amplitude=12.3,
            solar_kp=2.1,
        )
        ipc_send(state.to_json())

    Failure / fallback modes (per spec §Failure Modes):
        - No wearable data  → hrv_score fixed at 50 (neutral baseline)
        - No Schumann feed  → schumann_score fixed at 50
        - Both unavailable  → score forced to "standard" tier (50)
        - Kp > 8 storm      → score floor set to 0 (caller switches to restorative)
    """

    # Kp threshold that triggers automatic restorative mode
    KP_STORM_THRESHOLD: float = 8.0

    def __init__(
        self,
        hrv_normalizer: HRVNormalizer,
        schumann_parser: SchumannParser,
    ) -> None:
        self._hrv = hrv_normalizer
        self._schumann = schumann_parser
        self._last_state: Optional[AlignmentState] = None

    # ------------------------------------------------------------------
    # Primary compute path
    # ------------------------------------------------------------------

    async def compute(
        self,
        raw_rmssd: Optional[float] = None,
        raw_schumann_amplitude: Optional[float] = None,
        solar_kp: float = 0.0,
    ) -> AlignmentState:
        """
        Compute and return the current AlignmentState.

        Args:
            raw_rmssd:               Latest RMSSD reading in ms.
                                     Pass None if wearable unavailable.
            raw_schumann_amplitude:  Latest 7.83 Hz band-power reading.
                                     Pass None if feed unavailable.
            solar_kp:                Current NOAA Kp index (0–9).

        Returns:
            AlignmentState with all fields populated.
        """
        fallback_notes: list[str] = []

        # --- HRV score ---------------------------------------------------
        if raw_rmssd is not None:
            self._hrv.ingest(raw_rmssd)
            hrv_score = self._hrv.normalize(raw_rmssd)
        else:
            hrv_score = 50.0  # neutral baseline fallback
            fallback_notes.append("hrv_unavailable")
            logger.warning("AlignmentStateEmitter: no wearable data — using HRV baseline 50")

        # --- Schumann score ----------------------------------------------
        if raw_schumann_amplitude is not None:
            self._schumann.ingest(raw_schumann_amplitude)
            schumann_score = self._schumann.normalize(raw_schumann_amplitude)
        else:
            schumann_score = 50.0  # neutral baseline fallback
            fallback_notes.append("schumann_unavailable")
            logger.warning("AlignmentStateEmitter: Schumann feed unavailable — using baseline 50")

        # --- Both unavailable --------------------------------------------
        if "hrv_unavailable" in fallback_notes and "schumann_unavailable" in fallback_notes:
            score = 50.0  # force standard tier
            fallback_notes.append("both_unavailable_standard_forced")
            logger.warning("AlignmentStateEmitter: all feeds down — forcing standard tier (50)")
        else:
            score = compute_alignment(hrv_score, schumann_score, solar_kp)

        # --- Kp storm override -------------------------------------------
        if solar_kp > self.KP_STORM_THRESHOLD:
            score = 0.0
            fallback_notes.append(f"kp_storm_{solar_kp:.1f}")
            logger.warning(
                "AlignmentStateEmitter: Kp=%.1f > %.1f — forcing restorative mode (score=0)",
                solar_kp,
                self.KP_STORM_THRESHOLD,
            )

        state = AlignmentState(
            score=round(score, 2),
            hrv_score=round(hrv_score, 2),
            schumann_score=round(schumann_score, 2),
            solar_kp=round(solar_kp, 2),
            ui_tier=score_to_ui_tier(score),
            last_updated=datetime.now(timezone.utc).isoformat(),
            fallback_mode=",".join(fallback_notes),
        )

        self._last_state = state
        return state

    @property
    def last_state(self) -> Optional[AlignmentState]:
        """The most recently emitted AlignmentState, or None."""
        return self._last_state
