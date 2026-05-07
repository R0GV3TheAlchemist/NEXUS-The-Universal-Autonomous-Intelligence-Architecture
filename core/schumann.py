"""
GAIA-OS Schumann Biometric Alignment Layer — Python Sidecar
Pillar: Viriditas (Pillar II)
Spec: docs/knowledge/SCHUMANN_BIOMETRIC_ALIGNMENT_SPEC.md  (Issue #64)

This module implements the Python-side alignment pipeline:

    [Wearable HRV] ─► HRVNormalizer ─► hrv_score (0-100)
                                              │
    [Schumann Feed] ─► SchumannParser ──────┘
                                              │
                              [compute_alignment(hrv, schumann, kp)]
                                              │
                                     [AlignmentState]
                                              │
                              ┌───────────────────┘
                              │                  │
                     [UI Tier Engine]   [AffectStageAdapter]
                                         (hrv_rmssd_ms passthrough)

The Rust Tauri backend handles feed polling (GCI, NOAA, OpenWeatherMap).
This module consumes the parsed values and produces AlignmentState.

Privacy guarantee: zero biometric data leaves the device.
All normalization uses local 30-day rolling history stored in memory.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Deque, Literal, Optional


# ---------------------------------------------------------------------------
# UI Tier
# ---------------------------------------------------------------------------

UiTier = Literal["vibrant", "full", "standard", "core", "minimal"]

# Alignment score → UI tier mapping (per spec Issue #68)
_UI_TIER_THRESHOLDS: list[tuple[int, UiTier]] = [
    (80, "vibrant"),   # 80-100
    (60, "full"),      # 60-79
    (40, "standard"),  # 40-59
    (20, "core"),      # 20-39
    (0,  "minimal"),   # 0-19
]


def _score_to_ui_tier(score: float) -> UiTier:
    """Map an alignment score (0-100) to a UI tier."""
    for threshold, tier in _UI_TIER_THRESHOLDS:
        if score >= threshold:
            return tier
    return "minimal"


# ---------------------------------------------------------------------------
# AlignmentState
# ---------------------------------------------------------------------------

@dataclass
class AlignmentState:
    """
    Output of the Schumann alignment pipeline.

    Fields:
        score         — composite alignment 0-100
        hrv_score     — normalized HRV score 0-100
        schumann_score— normalized Schumann amplitude score 0-100
        ui_tier       — one of: vibrant / full / standard / core / minimal
        kp_index      — solar wind Kp index used in this computation
        hrv_rmssd_ms  — raw RMSSD in ms (passthrough for AffectStageAdapter)
        last_updated  — UTC ISO timestamp
    """
    score:          float
    hrv_score:      float
    schumann_score: float
    ui_tier:        UiTier
    kp_index:       float
    hrv_rmssd_ms:   float
    last_updated:   str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def is_storm_alert(self) -> bool:
        """True when Kp >= 8 — triggers auto-switch to restorative mode."""
        return self.kp_index >= 8.0


# ---------------------------------------------------------------------------
# compute_alignment  (exact spec formula)
# ---------------------------------------------------------------------------

def compute_alignment(
    hrv_score: float,
    schumann_score: float,
    solar_kp: float,
) -> float:
    """
    Compute the composite alignment score.

    Spec formula (SCHUMANN_BIOMETRIC_ALIGNMENT_SPEC.md):
        base       = 100 - abs(hrv_score - schumann_score)
        kp_penalty = min(solar_kp * 3, 30)
        score      = max(0, base - kp_penalty)

    Args:
        hrv_score:      normalized HRV score 0-100
        schumann_score: normalized Schumann amplitude score 0-100
        solar_kp:       NOAA Kp index (0-9)

    Returns:
        Alignment score 0-100 (float, never negative)
    """
    base = 100.0 - abs(hrv_score - schumann_score)
    kp_penalty = min(solar_kp * 3.0, 30.0)
    return max(0.0, base - kp_penalty)


# ---------------------------------------------------------------------------
# HRVNormalizer
# ---------------------------------------------------------------------------

class HRVNormalizer:
    """
    Normalizes raw HRV RMSSD readings (ms) to a 0-100 score using a
    30-day rolling baseline.

    Normalization formula:
        score = clamp((rmssd - baseline_min) / baseline_range * 100, 0, 100)

    Where baseline_min and baseline_range are derived from the rolling
    history (min and peak-to-peak range over the window).

    When fewer than 2 history points exist, falls back to the static
    physiological range: 20ms (baseline) → 100ms (excellent).
    """

    _STATIC_MIN = 20.0
    _STATIC_RANGE = 80.0   # 100 - 20
    _MAX_HISTORY = 30

    def __init__(self) -> None:
        self._history: Deque[float] = deque(maxlen=self._MAX_HISTORY)

    def add_reading(self, rmssd_ms: float) -> None:
        """Append a new raw RMSSD reading to the rolling history."""
        self._history.append(rmssd_ms)

    def normalize(self, rmssd_ms: float) -> float:
        """
        Normalize a raw RMSSD value to 0-100.
        Automatically adds the reading to rolling history.
        """
        self.add_reading(rmssd_ms)

        if len(self._history) >= 2:
            baseline_min = min(self._history)
            baseline_max = max(self._history)
            baseline_range = baseline_max - baseline_min
            if baseline_range < 1.0:  # degenerate window — all readings identical
                return 50.0
            raw = (rmssd_ms - baseline_min) / baseline_range * 100.0
        else:
            raw = (rmssd_ms - self._STATIC_MIN) / self._STATIC_RANGE * 100.0

        return max(0.0, min(100.0, raw))

    @property
    def history(self) -> list[float]:
        return list(self._history)


# ---------------------------------------------------------------------------
# SchumannParser
# ---------------------------------------------------------------------------

class SchumannParser:
    """
    Normalizes raw Schumann resonance amplitude readings (µT or arbitrary
    power units from the GCI feed) to a 0-100 score using a 30-day
    rolling baseline.

    Same normalization approach as HRVNormalizer: rolling min/range.
    Falls back to static range (0.1 – 2.0 µT typical) when history
    is insufficient.
    """

    _STATIC_MIN = 0.1
    _STATIC_RANGE = 1.9   # 2.0 - 0.1
    _MAX_HISTORY = 30

    def __init__(self) -> None:
        self._history: Deque[float] = deque(maxlen=self._MAX_HISTORY)

    def add_reading(self, amplitude: float) -> None:
        self._history.append(amplitude)

    def normalize(self, amplitude: float) -> float:
        """
        Normalize a raw Schumann amplitude to 0-100.
        Automatically adds the reading to rolling history.
        """
        self.add_reading(amplitude)

        if len(self._history) >= 2:
            baseline_min = min(self._history)
            baseline_max = max(self._history)
            baseline_range = baseline_max - baseline_min
            if baseline_range < 0.001:
                return 50.0
            raw = (amplitude - baseline_min) / baseline_range * 100.0
        else:
            raw = (amplitude - self._STATIC_MIN) / self._STATIC_RANGE * 100.0

        return max(0.0, min(100.0, raw))

    @property
    def history(self) -> list[float]:
        return list(self._history)


# ---------------------------------------------------------------------------
# AlignmentScorer
# ---------------------------------------------------------------------------

class AlignmentScorer:
    """
    Orchestrates the full alignment pipeline.

    Usage:
        scorer = AlignmentScorer()

        # Call once per polling cycle (every 10 min in production)
        state = scorer.score(
            hrv_rmssd_ms=55.0,
            schumann_amplitude=0.85,
            solar_kp=2.0,
        )

        # Pass to AffectStageAdapter:
        record = adapter.update(
            user_id="user_gaia",
            feeling=feeling,
            ...,
            hrv_rmssd_ms_override=state.hrv_rmssd_ms,
        )
    """

    def __init__(self) -> None:
        self._hrv = HRVNormalizer()
        self._schumann = SchumannParser()

    def score(
        self,
        hrv_rmssd_ms: float,
        schumann_amplitude: float,
        solar_kp: float = 0.0,
    ) -> AlignmentState:
        """
        Run one alignment cycle.

        Args:
            hrv_rmssd_ms:       raw RMSSD from wearable (ms)
            schumann_amplitude: raw amplitude from GCI / NOAA feed
            solar_kp:           current Kp index from NOAA Space Weather API

        Returns:
            AlignmentState with all derived fields populated
        """
        hrv_score = self._hrv.normalize(hrv_rmssd_ms)
        schumann_score = self._schumann.normalize(schumann_amplitude)
        alignment = compute_alignment(hrv_score, schumann_score, solar_kp)
        tier = _score_to_ui_tier(alignment)

        return AlignmentState(
            score=round(alignment, 2),
            hrv_score=round(hrv_score, 2),
            schumann_score=round(schumann_score, 2),
            ui_tier=tier,
            kp_index=solar_kp,
            hrv_rmssd_ms=hrv_rmssd_ms,
        )

    @property
    def hrv_normalizer(self) -> HRVNormalizer:
        return self._hrv

    @property
    def schumann_parser(self) -> SchumannParser:
        return self._schumann
