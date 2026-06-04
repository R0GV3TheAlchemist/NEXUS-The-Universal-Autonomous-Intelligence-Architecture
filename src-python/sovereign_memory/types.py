"""Shared types for Sovereign Memory (Issue #66).

All public types that cross module boundaries live here to avoid
circular imports between __init__.py, vec_search.py, crypto.py, etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Memory tier enumeration
# ---------------------------------------------------------------------------

class MemoryTier(str, Enum):
    """Tiers in GAIA's sovereign memory hierarchy."""
    WORKING   = "working"
    SEMANTIC  = "semantic"
    LONG_TERM = "long_term"
    BIOMETRIC = "biometric"
    ARCHIVAL  = "archival"


# ---------------------------------------------------------------------------
# Core record types
# ---------------------------------------------------------------------------

@dataclass
class EpisodeRecord:
    episode_id   : str
    principal_id : str
    content      : str
    type         : str
    tags         : List[str]
    created_at   : int
    deleted      : bool = False


@dataclass
class SemanticPattern:
    pattern_id   : str
    principal_id : str
    pattern      : str
    episode_ids  : List[str]
    confidence   : float
    tags         : List[str]
    created_at   : int


@dataclass
class BiometricSample:
    """A single biometric reading.

    Note: principal_id is optional here because get_biometric_history()
    reconstructs BiometricSample via **dict(row) from a SELECT that does
    NOT include principal_id in the column list.
    """
    timestamp    : int
    signal_type  : str
    value        : float
    source       : str
    principal_id : str = ""


@dataclass
class SearchResult:
    episode_id   : str
    principal_id : str
    content      : str
    score        : float
    tier         : MemoryTier = MemoryTier.SEMANTIC
    tags         : List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Memory record
# ---------------------------------------------------------------------------

@dataclass
class MemoryRecord:
    id           : str
    principal_id : str
    type         : str
    created_at   : int
    tags         : List[str]
    preview      : str


# ---------------------------------------------------------------------------
# Affect snapshot
# ---------------------------------------------------------------------------

# Names of scalar affect fields and the signal_type string they map to in
# biometric_history. Order is stable so to_biometric_rows() is predictable.
_AFFECT_SIGNAL_FIELDS: List[tuple[str, str]] = [
    ("valence",      "affect_valence"),
    ("arousal",      "affect_arousal"),
    ("dominance",    "affect_dominance"),
    ("entropy",      "affect_entropy"),
    ("arc_stability","affect_arc_stability"),
    ("confidence",   "affect_confidence"),
]


@dataclass
class AffectSnapshot:
    """Snapshot of biometric affect data at a point in time.

    Two usage modes:

    1. **Scalar-field mode** (used by tests and the affect inference pipeline):
       Populate the scalar affect fields (valence, arousal, …) and leave
       ``biometric_samples`` empty.  ``to_biometric_rows()`` synthesises one
       ``BiometricSample`` per non-None scalar field automatically.

    2. **Sample-list mode** (used by biometric sensors / HRV pipeline):
       Populate ``biometric_samples`` directly.  ``to_biometric_rows()``
       passes them through as-is, ignoring scalar affect fields.

    Fields
    ------
    principal_id      : GAIA principal this snapshot belongs to.
    timestamp         : Unix millisecond epoch of the snapshot.
    biometric_samples : Explicit list of BiometricSample readings.
    id                : Optional stable snapshot identifier.
    source            : Provenance label (e.g. "journal", "sensor", "manual").

    Affect-signal scalar fields
    ---------------------------
    emotion, confidence, valence, arousal, dominance,
    entropy, arc_stability, is_neutral_primary
    """
    principal_id      : str
    timestamp         : int
    biometric_samples : List[BiometricSample] = field(default_factory=list)
    id                : str = ""
    source            : str = ""

    # Scalar affect fields — used by to_biometric_rows() when biometric_samples is empty
    emotion           : Optional[str]   = None
    confidence        : float           = 0.0
    valence           : float           = 0.0
    arousal           : float           = 0.0
    dominance         : float           = 0.0
    entropy           : float           = 0.0
    arc_stability     : float           = 1.0
    is_neutral_primary: bool            = False

    def to_biometric_rows(self) -> List[Dict[str, Any]]:
        """Convert this snapshot to a list of biometric_history row dicts.

        **Sample-list mode**: if ``biometric_samples`` is non-empty, convert
        each sample directly (existing behaviour — no change for callers that
        populate the list explicitly).

        **Scalar-field mode**: if ``biometric_samples`` is empty, synthesise
        one row per scalar affect field that has a non-None value.  This
        covers the test pattern::

            snap = AffectSnapshot(
                principal_id=PID,
                timestamp=int(time.time() * 1000),
                source="journal",
                valence=0.7,
                arousal=0.6,
                ...
            )
            mem.store_affect_snapshot(snap)
            rows = mem.get_biometric_history(PID, "affect_valence", days=1)
            assert len(rows) == 1          # ✔ now passes
        """
        if self.biometric_samples:
            # Sample-list mode — pass through as before
            return [
                {
                    "principal_id": self.principal_id,
                    "timestamp"   : sample.timestamp,
                    "signal_type" : sample.signal_type,
                    "value"       : sample.value,
                    "source"      : sample.source,
                }
                for sample in self.biometric_samples
            ]

        # Scalar-field mode — synthesise one row per non-None affect field
        rows: List[Dict[str, Any]] = []
        for attr_name, signal_type in _AFFECT_SIGNAL_FIELDS:
            value = getattr(self, attr_name, None)
            if value is not None:
                rows.append({
                    "principal_id": self.principal_id,
                    "timestamp"   : self.timestamp,
                    "signal_type" : signal_type,
                    "value"       : float(value),
                    "source"      : self.source,
                })
        return rows


# ---------------------------------------------------------------------------
# Stage types
# ---------------------------------------------------------------------------

@dataclass
class StageRecord:
    principal_id : str
    stage        : int
    entered_at   : int
    notes        : str = ""


@dataclass
class StageTransitionRecord:
    id              : str
    principal_id    : str
    from_stage      : int
    to_stage        : int
    transitioned_at : int
    is_regression   : bool
    markers_met     : Dict[str, Any]
    ceremony_shown  : bool


# ---------------------------------------------------------------------------
# Marker scores
# ---------------------------------------------------------------------------

@dataclass
class MarkerScores:
    markers : Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Legacy artifact
# ---------------------------------------------------------------------------

@dataclass
class LegacyArtifact:
    id                : str
    principal_id      : str
    created_at        : int
    stage_at_creation : int
    title             : str
    content           : str
    tags              : List[str] = field(default_factory=list)
    source_episode_id : Optional[str] = None
    export_formats    : List[str] = field(default_factory=lambda: ["markdown", "json"])
