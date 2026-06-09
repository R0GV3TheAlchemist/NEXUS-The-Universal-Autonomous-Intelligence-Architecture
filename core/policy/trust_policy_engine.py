"""
core/policy/trust_policy_engine.py

Trust & Permission Policy Engine — Issue #229
Governs every autonomous action GAIA takes.
Runs BEFORE every agent action, not after.

Canon ref: C01 (Gaian sovereignty), SOVEREIGNTY.md
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger("gaia.policy.trust")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PermissionScope(str, Enum):
    """Declared permission scopes for all GAIA tools and capabilities."""
    # Read-only operations
    READ_MEMORY = "read:memory"
    READ_CANON = "read:canon"
    READ_SESSION = "read:session"
    READ_SYSTEM = "read:system"

    # Write / mutating operations
    WRITE_MEMORY = "write:memory"
    WRITE_CANON = "write:canon"
    WRITE_FILE = "write:file"
    DELETE_FILE = "delete:file"

    # External service calls
    CALL_EXTERNAL_API = "call:external_api"
    CALL_GITHUB = "call:github"
    CALL_WEB_SEARCH = "call:web_search"
    CALL_LLM = "call:llm"

    # Sensitive / high-risk
    ACCESS_BIOMETRICS = "access:biometrics"
    ACCESS_LOCATION = "access:location"
    EXECUTE_CODE = "execute:code"
    MODIFY_POLICY = "modify:policy"
    HALT_SYSTEM = "halt:system"


class PolicyDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class PolicyRecord:
    """Immutable audit record for every policy decision."""
    record_id: str
    timestamp: str
    agent_id: str
    session_id: str
    tool_name: str
    scope: str
    decision: PolicyDecision
    reason: str
    context: dict[str, Any] = field(default_factory=dict)
    approved_by: str | None = None

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "tool_name": self.tool_name,
            "scope": self.scope,
            "decision": self.decision.value,
            "reason": self.reason,
            "context": self.context,
            "approved_by": self.approved_by,
        }


@dataclass
class ToolPolicy:
    """Policy definition for a single tool or capability."""
    tool_name: str
    required_scope: PermissionScope
    risk_level: RiskLevel
    requires_explicit_approval: bool = False
    pre_approved: bool = False
    description: str = ""


@dataclass
class PolicyEvaluationResult:
    decision: PolicyDecision
    scope: PermissionScope
    risk_level: RiskLevel
    reason: str
    record_id: str
    requires_approval: bool = False
    approval_prompt: str | None = None


# ---------------------------------------------------------------------------
# Trust & Permission Policy Engine
# ---------------------------------------------------------------------------

class TrustPolicyEngine:
    """
    Mandatory gate before every GAIA agent action.

    Usage:
        engine = TrustPolicyEngine(session_id="abc", agent_id="planner")
        result = engine.evaluate(tool_name="write_file", context={"path": "/etc/passwd"})
        if result.decision == PolicyDecision.ALLOW:
            proceed()
        elif result.decision == PolicyDecision.REQUIRE_APPROVAL:
            approved = await ask_gaian(result.approval_prompt)
            engine.record_approval(result.record_id, approved_by="gaian")
    """

    def __init__(
        self,
        session_id: str,
        agent_id: str,
        audit_log_path: Path | None = None,
        approval_callback: Callable[[str], bool] | None = None,
    ):
        self.session_id = session_id
        self.agent_id = agent_id
        self.audit_log_path = audit_log_path or Path("logs/policy_audit.jsonl")
        self.approval_callback = approval_callback
        self._policies: dict[str, ToolPolicy] = {}
        self._pre_approved_scopes: set[PermissionScope] = set()
        self._audit_records: list[PolicyRecord] = []
        self._load_default_policies()

    # ------------------------------------------------------------------
    # Policy registration
    # ------------------------------------------------------------------

    def register_policy(self, policy: ToolPolicy) -> None:
        """Register a tool policy. Overwrites existing entry."""
        self._policies[policy.tool_name] = policy
        logger.debug(f"Registered policy for tool: {policy.tool_name}")

    def pre_approve_scope(self, scope: PermissionScope) -> None:
        """Gaian pre-approves a scope for this session. Editable at any time."""
        self._pre_approved_scopes.add(scope)
        logger.info(f"Scope pre-approved for session {self.session_id}: {scope.value}")

    def revoke_scope(self, scope: PermissionScope) -> None:
        """Gaian revokes a previously pre-approved scope."""
        self._pre_approved_scopes.discard(scope)
        logger.info(f"Scope revoked for session {self.session_id}: {scope.value}")

    # ------------------------------------------------------------------
    # Core evaluation — runs BEFORE every agent action
    # ------------------------------------------------------------------

    def evaluate(self, tool_name: str, context: dict[str, Any] | None = None) -> PolicyEvaluationResult:
        """
        Evaluate whether a tool call is permitted.
        This MUST be called before every agent action.
        """
        context = context or {}
        policy = self._policies.get(tool_name)

        if policy is None:
            # Unknown tool — deny by default
            result = self._deny(
                tool_name=tool_name,
                scope=PermissionScope.CALL_EXTERNAL_API,
                risk_level=RiskLevel.HIGH,
                reason=f"No policy registered for tool '{tool_name}'. Denied by default.",
                context=context,
            )
            return result

        scope = policy.required_scope
        risk = policy.risk_level

        # CRITICAL risk — always requires explicit approval
        if risk == RiskLevel.CRITICAL:
            return self._require_approval(
                tool_name=tool_name,
                scope=scope,
                risk_level=risk,
                reason=f"Critical-risk action '{tool_name}' always requires Gaian approval.",
                context=context,
                approval_prompt=(
                    f"⚠️ GAIA is requesting a CRITICAL action: **{tool_name}**\n"
                    f"Scope: {scope.value}\n"
                    f"Context: {json.dumps(context, default=str)}\n"
                    f"Do you approve? (yes/no)"
                ),
            )

        # Pre-approved scope — allow without prompt
        if scope in self._pre_approved_scopes:
            return self._allow(
                tool_name=tool_name,
                scope=scope,
                risk_level=risk,
                reason=f"Scope '{scope.value}' is pre-approved for this session.",
                context=context,
            )

        # Explicit approval required by policy
        if policy.requires_explicit_approval:
            return self._require_approval(
                tool_name=tool_name,
                scope=scope,
                risk_level=risk,
                reason=f"Policy for '{tool_name}' requires explicit Gaian approval.",
                context=context,
                approval_prompt=(
                    f"GAIA wants to run: **{tool_name}**\n"
                    f"Risk: {risk.value} | Scope: {scope.value}\n"
                    f"Context: {json.dumps(context, default=str)}\n"
                    f"Approve? (yes/no)"
                ),
            )

        # High-risk without pre-approval — require approval
        if risk == RiskLevel.HIGH:
            return self._require_approval(
                tool_name=tool_name,
                scope=scope,
                risk_level=risk,
                reason=f"High-risk tool '{tool_name}' requires approval unless pre-approved.",
                context=context,
                approval_prompt=(
                    f"GAIA wants to run a high-risk action: **{tool_name}**\n"
                    f"Scope: {scope.value}\n"
                    f"Approve? (yes/no)"
                ),
            )

        # LOW / MEDIUM risk, no special flags — allow
        return self._allow(
            tool_name=tool_name,
            scope=scope,
            risk_level=risk,
            reason=f"Tool '{tool_name}' permitted under scope '{scope.value}'.",
            context=context,
        )

    # ------------------------------------------------------------------
    # Approval recording
    # ------------------------------------------------------------------

    def record_approval(self, record_id: str, approved_by: str) -> None:
        """Record that a Gaian approved a pending action."""
        for record in self._audit_records:
            if record.record_id == record_id:
                record.approved_by = approved_by
                self._write_audit_record(record)
                logger.info(f"Action approved: {record_id} by {approved_by}")
                return
        logger.warning(f"record_approval: no record found for id {record_id}")

    # ------------------------------------------------------------------
    # Audit log
    # ------------------------------------------------------------------

    def get_audit_log(self) -> list[dict]:
        """Return all policy decisions for this session."""
        return [r.to_dict() for r in self._audit_records]

    def _write_audit_record(self, record: PolicyRecord) -> None:
        try:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.audit_log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record.to_dict()) + "\n")
        except Exception as exc:
            logger.error(f"Failed to write audit record: {exc}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_record(
        self,
        tool_name: str,
        scope: PermissionScope,
        decision: PolicyDecision,
        reason: str,
        context: dict,
    ) -> PolicyRecord:
        record = PolicyRecord(
            record_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id=self.agent_id,
            session_id=self.session_id,
            tool_name=tool_name,
            scope=scope.value,
            decision=decision,
            reason=reason,
            context=context,
        )
        self._audit_records.append(record)
        self._write_audit_record(record)
        return record

    def _allow(
        self,
        tool_name: str,
        scope: PermissionScope,
        risk_level: RiskLevel,
        reason: str,
        context: dict,
    ) -> PolicyEvaluationResult:
        record = self._make_record(tool_name, scope, PolicyDecision.ALLOW, reason, context)
        logger.debug(f"ALLOW [{tool_name}]: {reason}")
        return PolicyEvaluationResult(
            decision=PolicyDecision.ALLOW,
            scope=scope,
            risk_level=risk_level,
            reason=reason,
            record_id=record.record_id,
        )

    def _deny(
        self,
        tool_name: str,
        scope: PermissionScope,
        risk_level: RiskLevel,
        reason: str,
        context: dict,
    ) -> PolicyEvaluationResult:
        record = self._make_record(tool_name, scope, PolicyDecision.DENY, reason, context)
        logger.warning(f"DENY [{tool_name}]: {reason}")
        return PolicyEvaluationResult(
            decision=PolicyDecision.DENY,
            scope=scope,
            risk_level=risk_level,
            reason=reason,
            record_id=record.record_id,
        )

    def _require_approval(
        self,
        tool_name: str,
        scope: PermissionScope,
        risk_level: RiskLevel,
        reason: str,
        context: dict,
        approval_prompt: str,
    ) -> PolicyEvaluationResult:
        record = self._make_record(
            tool_name, scope, PolicyDecision.REQUIRE_APPROVAL, reason, context
        )
        logger.info(f"REQUIRE_APPROVAL [{tool_name}]: {reason}")
        return PolicyEvaluationResult(
            decision=PolicyDecision.REQUIRE_APPROVAL,
            scope=scope,
            risk_level=risk_level,
            reason=reason,
            record_id=record.record_id,
            requires_approval=True,
            approval_prompt=approval_prompt,
        )

    # ------------------------------------------------------------------
    # Default policy loader
    # ------------------------------------------------------------------

    def _load_default_policies(self) -> None:
        from core.policy.default_policies import DEFAULT_TOOL_POLICIES
        for policy in DEFAULT_TOOL_POLICIES:
            self.register_policy(policy)
        logger.info(f"Loaded {len(DEFAULT_TOOL_POLICIES)} default tool policies.")
