"""
Data contracts for the Schumann Alignment Layer.

Design rules
------------
* Raw measurements stay in PlanetarySignalSample.  Interpretation lives
  in SchumannState.  The two must never be mixed.
* SchumannState is the ONLY type that Stage Engine (#63) consumes.
* All float fields use IEEE-754 double.  NaN is NEVER written into a
  SchumannState field — use confidence=0.0 + disturbance=UNAVAILABLE
  instead.
* alignment_score is always in [0.0, 1.0].  Callers MUST NOT treat
  it as a direct proxy for mood or consciousness state — it is a signal
  quality+stability index only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class DisturbanceLevel(str, Enum):
    """Qualitative planetary electromagnetic state.

    Ordered from quietest to most disturbed.
    UNAVAILABLE means we have no usable signal at all.
    """
    STABLE      = "stable"       # deviation < 1σ from rolling baseline
    ELEVATED    = "elevated"     # deviation 1–2σ
    DISTURBED   = "disturbed"    # deviation > 2σ  (storm, flare, etc.)
    UNAVAILABLE = "unavailable"  # source offline / stale / quality < threshold

    def __lt__(self, other: DisturbanceLevel) -> bool:
        _order = ["stable", "elevated", "disturbed", "unavailable"]
        return _order.index(self.value) < _order.index(other.value)


@dataclass
class PlanetarySignalSample:
    """One raw measurement from any planetary EM data source.

    Parameters
    ----------
    timestamp  : UTC moment the sample was acquired by the source.
    channel    : Logical channel name.  Canonical names:
                   sr_f1          — Schumann fundamental amplitude (pT)
                   sr_f2          — 2nd harmonic amplitude (pT)
                   sr_f3          — 3rd harmonic amplitude (pT)
                   sr_f1_freq     — instantaneous fundamental frequency (Hz)
                   geomag_kp      — planetary K-index proxy (0–9)
                   geomag_dst     — storm-time Dst index (nT)
    value      : Measured value in the declared unit.
    unit       : SI unit string (pT, Hz, nT, index).
    source     : Source adapter ID (e.g. "dev", "noaa_ftp", "local_sensor").
    quality    : Source-reported quality in [0.0, 1.0].  Use 1.0 when the
                 source does not publish quality flags.
    """
    timestamp : datetime
    channel   : str
    value     : float
    unit      : str
    source    : str
    quality   : float = 1.0

    def __post_init__(self) -> None:
        if not (0.0 <= self.quality <= 1.0):
            raise ValueError(f"quality must be in [0,1], got {self.quality}")
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware (UTC)")


@dataclass
class SchumannState:
    """Processed planetary EM state snapshot — the Stage Engine contract.

    All fields are guaranteed non-NaN.  Callers should check `confidence`
    before acting on any other field.  When confidence < 0.4, treat the
    state as advisory only.

    Parameters
    ----------
    timestamp          : UTC time this state was computed.
    fundamental_hz     : Best estimate of the SR fundamental frequency (Hz).
                         Nominal value 7.83 Hz.  Range: ~7.0–8.5 Hz.
    harmonic_power     : Dict mapping harmonic label to normalised power.
                         Keys: f1, f2, f3, f4, f5.  Values: 0.0–1.0.
    geomagnetic_activity : Normalised geomagnetic activity index.
                         Derived from Kp or Dst.  Range: 0.0 (quiet) to
                         1.0 (severe storm).
    signal_quality     : Overall data-quality score: 0.0 (unusable) to
                         1.0 (excellent).  Drops when samples are stale,
                         sparse, clipped, or inconsistent.
    disturbance_level  : Qualitative EM state (see DisturbanceLevel).
    alignment_score    : Composite score in [0.0, 1.0].
                         0.45 × stability + 0.30 × harmonic_coherence
                         + 0.25 × signal_quality.
                         NOT a mood or consciousness score.
    confidence         : How much to trust this snapshot.  Below 0.4 the
                         Stage Engine should use it as advisory input only.
    source_ids         : List of source adapter IDs that contributed.
    baseline_hz        : Rolling 24-hour mean fundamental frequency.
    deviation_sigma    : Current deviation from baseline in σ units.
    experimental_flags : Feature-flagged outputs.  Keys defined in
                         EXPERIMENTAL_KEYS.  Always present but may be
                         empty.  Callers MUST NOT depend on these for
                         core logic.
    """
    EXPERIMENTAL_KEYS = frozenset([
        "quantum_bio_coupling",   # Fröhlich condensation proxy
        "seismic_precursor_score",# CNN-BiGRU output — NOT operational
        "laic_channel_state",     # Lithosphere-Atmosphere-Ionosphere
    ])

    timestamp             : datetime
    fundamental_hz        : float
    harmonic_power        : dict[str, float]
    geomagnetic_activity  : float
    signal_quality        : float
    disturbance_level     : DisturbanceLevel
    alignment_score       : float
    confidence            : float
    source_ids            : list[str]
    baseline_hz           : float                   = 7.83
    deviation_sigma       : float                   = 0.0
    experimental_flags    : dict[str, float]        = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    @property
    def is_trusted(self) -> bool:
        """True when confidence is high enough for Stage Engine to use."""
        return self.confidence >= 0.4

    @property
    def is_disturbed(self) -> bool:
        return self.disturbance_level in (
            DisturbanceLevel.DISTURBED, DisturbanceLevel.UNAVAILABLE
        )

    def to_stage_dict(self) -> dict:
        """Minimal dict for Stage Engine consumption."""
        return {
            "timestamp"            : self.timestamp.isoformat(),
            "fundamental_hz"       : self.fundamental_hz,
            "geomagnetic_activity" : self.geomagnetic_activity,
            "disturbance_level"    : self.disturbance_level.value,
            "alignment_score"      : self.alignment_score,
            "confidence"           : self.confidence,
            "is_trusted"           : self.is_trusted,
        }
