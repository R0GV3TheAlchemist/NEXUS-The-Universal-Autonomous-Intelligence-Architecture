"""
core/safety/types.py
====================
Shared data contracts for the GAIA safety sub-system.

All types consumed by crisis_detector, circuit_breaker,
escalation_detector, crisis_synthesizer, and safety_engine live here to
give callers a single import source and break circular dependencies.

#  CrossSessionCrisisSignal is defined in this module so all safety types
#  have a single canonical import source:
#
#      from core.safety.types import CrossSessionCrisisSignal
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


# ────────────────────────────────────────────────────────────────────────── #
#  Enumerations                                                             #
# ────────────────────────────────────────────────────────────────────────── #


class CircuitBreakerState(str, Enum):
    """Operational state of the EscalationCircuitBreaker."""

    CLOSED  = "closed"    # Normal operation — no active intervention
    COOLING = "cooling"   # Post-intervention cool-down period
    OPEN    = "open"      # Circuit tripped — active intervention in progress


class CrisisLevel(str, Enum):
    """Severity level of a detected crisis signal."""

    NONE     = "none"
    GRADUAL  = "gradual"   # Slow-building distress pattern
    MASKED   = "masked"    # Distress concealed behind neutral surface language
    ACUTE    = "acute"     # Clear immediate distress
    EXPLICIT = "explicit"  # Direct statement of crisis / self-harm


class CrisisType(str, Enum):
    """Category of crisis detected."""

    NONE              = "none"
    EMOTIONAL_DISTRESS = "emotional_distress"
    SUICIDE_SELF_HARM  = "suicide_self_harm"
    RELATIONAL_CRISIS  = "relational_crisis"
    IDENTITY_CRISIS    = "identity_crisis"


class SafetyVerdict(str, Enum):
    """High-level safety verdict from SafetyEngine.evaluate()."""

    SAFE        = "safe"         # No concerns
    MONITOR     = "monitor"      # Low-level flag — watch but don't intervene
    INTERVENE   = "intervene"    # Circuit breaker intervention warranted
    HANDOFF     = "handoff"      # Human / professional handoff required


# ────────────────────────────────────────────────────────────────────────── #
#  Signal dataclasses                                                       #
# ────────────────────────────────────────────────────────────────────────── #


@dataclass
class TurnRiskFrame:
    """Per-turn risk snapshot fed into CumulativeCrisisDetector."""

    turn_index:           int
    timestamp:            datetime
    mirroring_score:      float
    vulnerability_score:  float
    affect_valence:       float
    affect_arousal:       float
    escalation_delta:     float
    crisis_level:         CrisisLevel
    # Legacy / optional fields kept for backward compatibility
    user_message:         str             = ""
    crisis_keyword_hits:  int             = 0
    sentiment_valence:    float           = 0.0   # [-1, 1] — negative is distress


@dataclass
class EscalationSignal:
    """Output of ReflectiveEscalationDetector when escalation is detected."""

    session_id:               str
    turn_index:               int
    pattern_length:           int
    peak_mirroring_score:     float
    peak_vulnerability_score: float
    qubo_penalty:             float
    intervention_required:    bool
    # Optional / legacy fields
    escalation_turns:         int           = 0
    trigger_phrase:           Optional[str] = None


@dataclass
class CrisisSignal:
    """Output of CumulativeCrisisDetector when crisis is detected."""

    session_id:    str
    turn_index:    int
    crisis_level:  CrisisLevel
    crisis_type:   CrisisType
    confidence:    float
    trigger_text:  Optional[str] = None


@dataclass
class SessionRiskProfile:
    """Aggregated risk summary for a completed or ongoing session.

    Produced at session close by SafetyEngine and stored for cross-session
    analysis by CrisisSynthesizer.
    """

    session_id:               str
    user_id:                  str
    started_at:               datetime
    ended_at:                 datetime
    peak_crisis_level:        CrisisLevel
    mean_vulnerability_score: float            # [0, 1]
    escalation_events:        int
    circuit_breaker_trips:    int
    cumulative_risk_score:    float            # [0, 1]
    # Optional fields
    verdict:                  SafetyVerdict    = SafetyVerdict.SAFE
    turn_count:               int              = 0
    flagged_turns:            List[int]        = field(default_factory=list)


# ────────────────────────────────────────────────────────────────────────── #
#  CrossSessionCrisisSignal                                                 #
# ────────────────────────────────────────────────────────────────────────── #


@dataclass
class CrossSessionCrisisSignal:
    """Cross-session crisis signal for longitudinal risk analysis.

    Produced by CrisisSynthesizer when analysing a window of past
    SessionRiskProfiles and detecting actionable longitudinal patterns.
    """

    user_id:           str
    session_id:        str
    aggregate_score:   float
    handoff_required:  bool
    handoff_resources: List[str] = field(default_factory=list)


__all__ = [
    "CircuitBreakerState",
    "CrisisLevel",
    "CrisisSignal",
    "CrisisType",
    "CrossSessionCrisisSignal",
    "EscalationSignal",
    "SafetyVerdict",
    "SessionRiskProfile",
    "TurnRiskFrame",
]
