"""ActionGate v2 — multi-tier risk model for GAIA-OS.

Risk tiers
----------
LOW      — Proceed silently; log at DEBUG.
MEDIUM   — Proceed; log at INFO with rationale.
HIGH     — Proceed with warning; write audit entry; surface to session context.
CRITICAL — PAUSE. Surface to human sovereign before proceeding. Write audit.
            Action is only executed if the human explicitly approves.

Every ActionGate decision produces an ActionRecord written to the audit log.
The audit log is privacy-safe — no raw memory content is stored, only action
type, risk tier, rationale, and outcome.

Canon refs: C01 (Sovereignty), C-SINGULARITY Axiom III, C29 (Five Forces)
Issue: #263
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RiskTier(str, Enum):
    LOW = "LOW"           # Routine actions — auto-proceed
    MEDIUM = "MEDIUM"     # Notable actions — log + proceed
    HIGH = "HIGH"         # Significant risk — warn + audit
    CRITICAL = "CRITICAL" # Sovereignty-touching — require human veto


class GateOutcome(str, Enum):
    APPROVED = "APPROVED"         # Action proceeded
    BLOCKED = "BLOCKED"           # Action blocked (CRITICAL, no human approval)
    PENDING_VETO = "PENDING_VETO" # Surfaced to human; awaiting decision
    VETOED = "VETOED"             # Human explicitly denied


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ActionRecord:
    """Immutable audit log entry for every ActionGate decision."""
    record_id: str
    action_type: str
    risk_tier: RiskTier
    outcome: GateOutcome
    rationale: str
    canon_refs: list[str]
    timestamp: datetime
    session_id: str
    checksum: str = field(init=False)

    def __post_init__(self) -> None:
        payload = json.dumps({
            'record_id': self.record_id,
            'action_type': self.action_type,
            'risk_tier': self.risk_tier.value,
            'outcome': self.outcome.value,
            'timestamp': self.timestamp.isoformat(),
        }, sort_keys=True).encode()
        self.checksum = hashlib.sha256(payload).hexdigest()[:16]


@dataclass
class GateDecision:
    """Result returned by ActionGate.evaluate()."""
    action_type: str
    risk_tier: RiskTier
    outcome: GateOutcome
    rationale: str
    record: ActionRecord
    veto_prompt: str | None = None  # Human-facing prompt for CRITICAL actions

    @property
    def may_proceed(self) -> bool:
        return self.outcome == GateOutcome.APPROVED


# ---------------------------------------------------------------------------
# Risk classifier
# ---------------------------------------------------------------------------

@dataclass
class RiskClassifier:
    """Maps action types and context signals to a RiskTier.

    Override `classify` to provide domain-specific logic.
    The default implementation uses keyword and flag heuristics.
    """

    # Action types that are always CRITICAL regardless of context
    critical_actions: frozenset[str] = field(
        default_factory=lambda: frozenset({
            'delete_memory', 'revoke_consent', 'identity_transfer',
            'sovereignty_override', 'broadcast_all_gaians',
            'key_rotation', 'export_private_key',
        })
    )

    # Action types that default to HIGH
    high_actions: frozenset[str] = field(
        default_factory=lambda: frozenset({
            'send_external_message', 'purchase', 'modify_constitution',
            'share_personal_data', 'execute_agentic_task',
        })
    )

    def classify(
        self,
        action_type: str,
        context: dict[str, Any],
    ) -> tuple[RiskTier, str]:
        """Return (RiskTier, rationale_string)."""
        if action_type in self.critical_actions:
            return RiskTier.CRITICAL, f"Action '{action_type}' is sovereignty-critical"

        if action_type in self.high_actions:
            return RiskTier.HIGH, f"Action '{action_type}' has significant real-world impact"

        # Context signals can escalate
        if context.get('affects_external_systems', False):
            return RiskTier.HIGH, "Action affects external systems (context flag)"

        if context.get('bulk_operation', False):
            return RiskTier.MEDIUM, "Bulk operation — heightened scrutiny"

        return RiskTier.LOW, f"Action '{action_type}' assessed as routine"


# ---------------------------------------------------------------------------
# ActionGate
# ---------------------------------------------------------------------------

class ActionGate:
    """Multi-tier action risk gate with human veto channel and audit trail.

    Parameters
    ----------
    classifier : RiskClassifier
        Classifies action types into risk tiers. Default: RiskClassifier().
    audit_log : list[ActionRecord] | None
        If provided, all records are appended here (in-memory audit).
        Production deployments should wire this to a persistent store.
    human_veto_handler : Callable[[GateDecision], bool] | None
        Callback invoked for CRITICAL-tier actions. Must return True to
        approve or False to veto. If None, CRITICAL actions are BLOCKED.
    session_id : str
        Session identifier for audit records.
    """

    def __init__(
        self,
        classifier: RiskClassifier | None = None,
        audit_log: list[ActionRecord] | None = None,
        human_veto_handler: Callable[[GateDecision], bool] | None = None,
        session_id: str = 'unknown',
    ) -> None:
        self.classifier = classifier or RiskClassifier()
        self.audit_log: list[ActionRecord] = audit_log if audit_log is not None else []
        self.human_veto_handler = human_veto_handler
        self.session_id = session_id
        self._counter = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        action_type: str,
        context: dict[str, Any] | None = None,
        canon_refs: list[str] | None = None,
    ) -> GateDecision:
        """Evaluate an action and return a GateDecision.

        CRITICAL-tier actions are surfaced to the human veto handler.
        All decisions are recorded in the audit log.
        """
        ctx = context or {}
        refs = canon_refs or ['C01', 'C29']

        tier, rationale = self.classifier.classify(action_type, ctx)
        self._counter += 1
        record_id = f"ag-{self.session_id[:8]}-{self._counter:04d}"

        if tier == RiskTier.LOW:
            outcome = GateOutcome.APPROVED
            logger.debug("ActionGate LOW → APPROVED: %s", action_type)

        elif tier == RiskTier.MEDIUM:
            outcome = GateOutcome.APPROVED
            logger.info("ActionGate MEDIUM → APPROVED: %s | %s", action_type, rationale)

        elif tier == RiskTier.HIGH:
            outcome = GateOutcome.APPROVED
            logger.warning("ActionGate HIGH → APPROVED with audit: %s | %s", action_type, rationale)

        else:  # CRITICAL
            outcome = self._handle_critical(action_type, rationale, refs, record_id)

        record = ActionRecord(
            record_id=record_id,
            action_type=action_type,
            risk_tier=tier,
            outcome=outcome,
            rationale=rationale,
            canon_refs=refs,
            timestamp=datetime.now(timezone.utc),
            session_id=self.session_id,
        )
        self.audit_log.append(record)

        veto_prompt = (
            f"GAIA requests permission to perform: '{action_type}'\n"
            f"Risk: CRITICAL | Rationale: {rationale}\n"
            f"Approve this action? (yes/no)"
        ) if tier == RiskTier.CRITICAL else None

        decision = GateDecision(
            action_type=action_type,
            risk_tier=tier,
            outcome=outcome,
            rationale=rationale,
            record=record,
            veto_prompt=veto_prompt,
        )

        return decision

    def get_audit_log(self) -> list[ActionRecord]:
        """Return all audit records for this session."""
        return list(self.audit_log)

    def audit_summary(self) -> dict[str, Any]:
        """Return aggregate counts by tier and outcome."""
        summary: dict[str, Any] = {'total': len(self.audit_log)}
        for tier in RiskTier:
            summary[tier.value] = sum(
                1 for r in self.audit_log if r.risk_tier == tier
            )
        for outcome in GateOutcome:
            summary[outcome.value] = sum(
                1 for r in self.audit_log if r.outcome == outcome
            )
        return summary

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _handle_critical(
        self,
        action_type: str,
        rationale: str,
        refs: list[str],
        record_id: str,
    ) -> GateOutcome:
        if self.human_veto_handler is None:
            logger.critical(
                "ActionGate CRITICAL → BLOCKED (no veto handler): %s", action_type
            )
            return GateOutcome.BLOCKED

        # Build a provisional decision for the handler
        provisional = GateDecision(
            action_type=action_type,
            risk_tier=RiskTier.CRITICAL,
            outcome=GateOutcome.PENDING_VETO,
            rationale=rationale,
            record=ActionRecord(
                record_id=record_id,
                action_type=action_type,
                risk_tier=RiskTier.CRITICAL,
                outcome=GateOutcome.PENDING_VETO,
                rationale=rationale,
                canon_refs=refs,
                timestamp=datetime.now(timezone.utc),
                session_id=self.session_id,
            ),
        )

        approved = self.human_veto_handler(provisional)
        if approved:
            logger.info("ActionGate CRITICAL → APPROVED by human veto: %s", action_type)
            return GateOutcome.APPROVED
        else:
            logger.info("ActionGate CRITICAL → VETOED by human: %s", action_type)
            return GateOutcome.VETOED
