"""Data models for the GAIA Agent Telemetry Hub."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Core telemetry event — one row in the append-only SQLite log
# ---------------------------------------------------------------------------

@dataclass
class TelemetryEvent:
    """Immutable record of a single GAIA engine action.

    Privacy contract:
    - input_summary / output_summary hold non-sensitive labels only.
    - Raw user content, file contents, and conversation text are NEVER stored here.
    - Biometric and emotional values are stored as labels (e.g. "high"), never raw numbers.
    """

    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: str = ""

    # Source
    source: str = ""  # "synergy_orchestrator" | "sandbox" | "skill" | "healing" | "biometric" | "planetary" | "action_gate"
    event_type: str = ""  # "job_started" | "job_completed" | "job_failed" | "fallback_used" | "circuit_broken" | "action_gate_triggered" | "skill_invoked" | "context_change"

    # Skill / engine metadata
    skill_id: Optional[str] = None
    trust_tier: Optional[str] = None      # From Skill Trust (#150)
    intent_class: Optional[str] = None    # From Synergy Orchestrator intent
    risk_tier: Optional[str] = None       # From Action Gate: "GREEN" | "YELLOW" | "RED"

    # Payload summaries (non-sensitive only)
    input_summary: str = ""
    output_summary: str = ""

    # Performance
    duration_ms: int = 0

    # Quality
    dq_score: Optional[float] = None
    degraded: bool = False
    fallback_mode: Optional[str] = None

    # Context labels at event time
    biometric_context: Optional[str] = None   # "high" | "building" | "stressed" | "depleted"
    planetary_context: Optional[str] = None   # "quiet" | "elevated" | "storm" | "kp_storm"

    # Canon governance
    canon_refs: list[str] = field(default_factory=list)

    # Free tags
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "source": self.source,
            "event_type": self.event_type,
            "skill_id": self.skill_id,
            "trust_tier": self.trust_tier,
            "intent_class": self.intent_class,
            "risk_tier": self.risk_tier,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "duration_ms": self.duration_ms,
            "dq_score": self.dq_score,
            "degraded": self.degraded,
            "fallback_mode": self.fallback_mode,
            "biometric_context": self.biometric_context,
            "planetary_context": self.planetary_context,
            "canon_refs": ",".join(self.canon_refs),
            "tags": ",".join(self.tags),
        }


# ---------------------------------------------------------------------------
# Skill health report — circuit breaker state + error stats per skill
# ---------------------------------------------------------------------------

@dataclass
class SkillHealthReport:
    skill_id: str
    circuit_state: str = "CLOSED"        # "CLOSED" | "OPEN" | "HALF_OPEN"
    total_events: int = 0
    error_count: int = 0
    fallback_count: int = 0
    avg_duration_ms: float = 0.0
    error_rate: float = 0.0              # 0.0 – 1.0
    last_failure_at: Optional[datetime] = None
    window_minutes: int = 60

    @property
    def healthy(self) -> bool:
        return self.circuit_state == "CLOSED" and self.error_rate < 0.5


# ---------------------------------------------------------------------------
# Orchestration Efficiency (OE) — rolling window metric
# ---------------------------------------------------------------------------

@dataclass
class OrchestrationEfficiency:
    """OE = successful_tasks * avg_dq_score / (avg_total_latency_s * avg_engine_count)

    Higher OE means high quality delivered fast with fewer engines (minimal waste).
    """
    window: str = "24h"                 # "1h" | "24h" | "7d" | "30d"
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    avg_total_latency_s: float = 0.0
    avg_engine_count: float = 0.0
    avg_dq_score: float = 0.0
    degraded_fraction: float = 0.0
    oe_score: float = 0.0
    bottleneck_skill: Optional[str] = None

    def compute_oe(self) -> float:
        """Compute composite OE score. Returns 0.0 if inputs are degenerate."""
        if self.avg_total_latency_s <= 0 or self.avg_engine_count <= 0:
            return 0.0
        raw = (self.successful_tasks * self.avg_dq_score) / (
            self.avg_total_latency_s * self.avg_engine_count
        )
        self.oe_score = round(raw, 4)
        return self.oe_score


# ---------------------------------------------------------------------------
# Decision Quality record — stored alongside each orchestration run
# ---------------------------------------------------------------------------

@dataclass
class DecisionQualityRecord:
    session_id: str
    intent_class: str
    dq_score: float
    engines_invoked: list[str] = field(default_factory=list)
    degraded: bool = False
    degradation_reason: Optional[str] = None
    conflict_detected: bool = False
    conflict_type: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
