"""Issue #188 — TelemetryEvent: canonical schema for all GAIA agent telemetry.

Canon C05: Transparency — every agentic decision is auditable.
Canon C30: No silent failures — all degradation and conflict events are recorded.
Canon C50: Action Gate — YELLOW/RED events are flagged for review.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TelemetrySource(str, Enum):
    SYNERGY_ORCHESTRATOR = "synergy_orchestrator"
    SELF_HEALING_ENGINE = "self_healing_engine"
    SANDBOX = "sandbox"
    SKILL_TRUST = "skill_trust"
    ACTION_GATE = "action_gate"
    PLANETARY_HUB = "planetary_hub"
    BIOMETRIC_ENGINE = "biometric_engine"
    CONFLICT_RESOLVER = "conflict_resolver"   # Added by Issue #190
    INTENT_LAUNCHER = "intent_launcher"       # Added by Issue #165


class TrustTier(str, Enum):
    TRUSTED = "trusted"       # Verified GAIA skill, fully attested
    SANDBOXED = "sandboxed"   # External or unverified skill, running in sandbox
    UNTRUSTED = "untrusted"   # No trust attestation; blocked unless user overrides


class RiskTier(str, Enum):
    GREEN = "green"   # Safe, routine operation
    YELLOW = "yellow" # Notable event — logged, surfaced in Glass Room
    RED = "red"       # High-risk — auto-flagged, may require user confirmation


@dataclass
class TelemetryEvent:
    # Core identity
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    # Classification
    source: TelemetrySource = TelemetrySource.SYNERGY_ORCHESTRATOR
    event_type: str = ""
    trust_tier: TrustTier = TrustTier.TRUSTED
    risk_tier: RiskTier = RiskTier.GREEN

    # Session + skill context
    session_id: str | None = None
    skill_id: str | None = None
    intent_class: str | None = None

    # Orchestration metrics
    latency_ms: float | None = None
    engines_invoked: list[str] = field(default_factory=list)
    dq_score: float | None = None             # DecisionQuality score
    degraded: bool = False                    # Was a fallback used?
    fallback_mode: str | None = None

    # Conflict data (Issue #190)
    conflict_detected: bool = False
    conflict_type: str | None = None
    conflict_winner: str | None = None

    # Biometric + planetary context snapshots
    biometric_context: str | None = None      # e.g. "high" | "building" | "depleted"
    planetary_context: str | None = None      # e.g. "Kp=2/calm" | "Kp=7/severe"

    # Canon refs triggered
    canon_refs: list[str] = field(default_factory=list)

    # Free-form payload for source-specific data
    payload: dict[str, Any] = field(default_factory=dict)

    # Crystal indexing flag (auto-set by TelemetryCollector for YELLOW/RED)
    index_in_crystal: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "source": self.source.value,
            "event_type": self.event_type,
            "trust_tier": self.trust_tier.value,
            "risk_tier": self.risk_tier.value,
            "session_id": self.session_id,
            "skill_id": self.skill_id,
            "intent_class": self.intent_class,
            "latency_ms": self.latency_ms,
            "engines_invoked": self.engines_invoked,
            "dq_score": self.dq_score,
            "degraded": self.degraded,
            "fallback_mode": self.fallback_mode,
            "conflict_detected": self.conflict_detected,
            "conflict_type": self.conflict_type,
            "conflict_winner": self.conflict_winner,
            "biometric_context": self.biometric_context,
            "planetary_context": self.planetary_context,
            "canon_refs": self.canon_refs,
            "payload": self.payload,
            "index_in_crystal": self.index_in_crystal,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TelemetryEvent":
        e = cls()
        for k, v in d.items():
            if hasattr(e, k):
                setattr(e, k, v)
        return e
