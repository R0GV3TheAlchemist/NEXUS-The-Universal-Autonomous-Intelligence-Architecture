"""Shared types for the core.safety subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CircuitBreakerState(str, Enum):
    CLOSED = "closed"       # Normal operation
    WARNING = "warning"     # Elevated risk, monitoring
    COOLING = "cooling"     # Post-intervention cooldown
    TRIPPED = "tripped"     # Intervention active


class CrisisType(str, Enum):
    SUICIDE_SELF_HARM = "suicide_self_harm"
    GENERAL_CRISIS = "general_crisis"


@dataclass
class TurnRiskFrame:
    """Risk scores for a single conversation turn."""
    turn_index: int
    session_id: str
    mirroring_score: float      # 0.0 – 1.0
    vulnerability_score: float  # 0.0 – 1.0
    escalation_delta: float = 0.0


@dataclass
class EscalationSignal:
    """Fired by ReflectiveEscalationDetector when pattern is confirmed."""
    session_id: str
    turn_index: int
    pattern_length: int
    peak_mirroring_score: float
    peak_vulnerability_score: float
    qubo_penalty: float
    intervention_required: bool


@dataclass
class CrisisSignal:
    """Fired by CrisisDetector when acute crisis language is detected."""
    crisis_type: CrisisType
    confidence: float
    requires_immediate_response: bool
    matched_pattern: str = ""


@dataclass
class SafetyVerdict:
    """Result of a full SafetyEngine.evaluate_turn() call."""
    action: str                              # "pass" | "cooling" | "escalation_intervention" | "crisis_response"
    intervention_text: Optional[str]
    crisis_signal: Optional[CrisisSignal]
    escalation_signal: Optional[EscalationSignal]
    circuit_breaker_state: CircuitBreakerState
    intervention_mode: Optional[str] = None
