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
    """Tiers in GAIA's sovereign memory hierarchy.

    Used by the memory router to decide which store to consult
    and in which order, and by tests to assert tier registration.
    """
    WORKING   = "working"    # Short-lived, in-process scratchpad
    SEMANTIC  = "semantic"   # Distilled patterns via sentence-transformers
    LONG_TERM = "long_term"  # Persistent episodic + semantic SQLite store
    BIOMETRIC = "biometric"  # Physiological signals (HRV, GSR, …)
    ARCHIVAL  = "archival"   # Cold compressed store for older episodes


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
    created_at   : int           # Unix ms
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
    NOT include principal_id in the column list (timestamp, signal_type,
    value, source only).
    """
    timestamp    : int           # Unix ms
    signal_type  : str
    value        : float
    source       : str
    principal_id : str = ""     # Empty when reconstructed from partial row


@dataclass
class SearchResult:
    episode_id   : str
    principal_id : str
    content      : str
    score        : float
    tier         : MemoryTier = MemoryTier.SEMANTIC
    tags         : List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Memory record  (returned by _row_to_memory_record and search_memory)
# ---------------------------------------------------------------------------

@dataclass
class MemoryRecord:
    """Decrypted, caller-facing view of an episodic or semantic memory row.

    Constructed by SovereignMemory._row_to_memory_record() and
    _semantic_row_to_record() — field names must match exactly.
    """
    id           : str
    principal_id : str
    type         : str
    created_at   : int           # Unix ms
    tags         : List[str]
    preview      : str           # First 280 chars of decrypted content


# ---------------------------------------------------------------------------
# Affect snapshot  (used by store_affect_snapshot)
# ---------------------------------------------------------------------------

@dataclass
class AffectSnapshot:
    """Snapshot of biometric affect data at a point in time.

    Holds one or more BiometricSample readings captured together and
    exposes to_biometric_rows() for batch INSERT into biometric_history.

    Used by SovereignMemory.store_affect_snapshot() (sovereign_memory/__init__.py)
    to persist all samples in a single atomic transaction.
    """
    principal_id      : str
    timestamp         : int                              # Unix ms — snapshot time
    biometric_samples : List[BiometricSample] = field(default_factory=list)

    def to_biometric_rows(self) -> List[Dict[str, Any]]:
        """Convert samples to rows suitable for biometric_history INSERT.

        Each dict maps to the five columns: principal_id, timestamp,
        signal_type, value, source  — matching the executemany() call in
        SovereignMemory.store_affect_snapshot().
        """
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


# ---------------------------------------------------------------------------
# Stage types  (used by get_stage_history)
# ---------------------------------------------------------------------------

@dataclass
class StageRecord:
    """Current Alchemical Stage state for a principal."""
    principal_id : str
    stage        : int           # 0–8 (Nigredo → Rubedo)
    entered_at   : int           # Unix ms
    notes        : str = ""


@dataclass
class StageTransitionRecord:
    """One row from the stage_transitions table.

    Field names match the column names used in get_stage_history().
    """
    id              : str
    principal_id    : str
    from_stage      : int
    to_stage        : int
    transitioned_at : int        # Unix ms
    is_regression   : bool
    markers_met     : Dict[str, Any]
    ceremony_shown  : bool


# ---------------------------------------------------------------------------
# Marker scores  (used by MarkerScores import in __init__.py)
# ---------------------------------------------------------------------------

@dataclass
class MarkerScores:
    """Named marker weights for stage-transition eligibility.

    `markers` is a free-form dict so that callers can pass arbitrary
    signal names without requiring a schema change.
    """
    markers : Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Legacy artifact  (used by tag_as_legacy / export_legacy)
# ---------------------------------------------------------------------------

@dataclass
class LegacyArtifact:
    """A decrypted legacy artifact record.

    Returned after decryption — the DB stores cipher fields; this type
    holds the plaintext view used in export and display.
    """
    id                : str
    principal_id      : str
    created_at        : int           # Unix ms
    stage_at_creation : int
    title             : str
    content           : str
    tags              : List[str] = field(default_factory=list)
    source_episode_id : Optional[str] = None
    export_formats    : List[str] = field(default_factory=lambda: ["markdown", "json"])
