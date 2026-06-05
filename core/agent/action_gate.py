"""
core/agent/action_gate.py
~~~~~~~~~~~~~~~~~~~~~~~~~
Consent and human oversight enforcement layer for GAIA-OS.

Implements issue #248:
- Tiered action risk levels
- Gate requirements per risk level
- Multi-party approval for irreversible actions
- Cryptographically signed consent receipts
- Time-bounded approvals that expire
- Approval delegation with scope limits
- Emergency halt propagation across sessions

Design notes
------------
This is intentionally lightweight and dependency-free for v1.
Receipts are HMAC-SHA256 signed over canonical JSON using a per-gate key.
The gate integrates with AuditLog so every policy decision is durable and
inspectable.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import threading
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from core.obs import AuditEventType, get_audit


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ActionRiskLevel(Enum):
    LOW          = "low"
    MEDIUM       = "medium"
    HIGH         = "high"
    IRREVERSIBLE = "irreversible"


class GateRequirement(Enum):
    AUTO_APPROVE   = "auto_approve"
    LOG_ONLY       = "log_only"
    HUMAN_REQUIRED = "human_required"
    MULTI_PARTY    = "multi_party"


DEFAULT_GATE_POLICY: Dict[ActionRiskLevel, GateRequirement] = {
    ActionRiskLevel.LOW:          GateRequirement.LOG_ONLY,
    ActionRiskLevel.MEDIUM:       GateRequirement.HUMAN_REQUIRED,
    ActionRiskLevel.HIGH:         GateRequirement.HUMAN_REQUIRED,
    ActionRiskLevel.IRREVERSIBLE: GateRequirement.MULTI_PARTY,
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ConsentReceipt:
    receipt_id:      str
    session_id:      str
    tool_name:       str
    actor:           str
    risk_level:      str
    requirement:     str
    args:            Dict[str, Any]
    requested_at:    str
    approved_by:     List[str]                  = field(default_factory=list)
    approved_at:     Optional[str]              = None
    expires_at:      Optional[str]              = None
    status:          str                        = "pending"   # pending / approved / denied / expired
    signature:       Optional[str]              = None

    def canonical_body(self) -> bytes:
        body = asdict(self).copy()
        body.pop("signature", None)
        return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode()


@dataclass
class DelegationScope:
    delegated_to:    str
    granted_by:      str
    risk_levels:     List[str]
    created_at:      str
    expires_at:      str
    signature:       Optional[str] = None

    def canonical_body(self) -> bytes:
        body = asdict(self).copy()
        body.pop("signature", None)
        return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode()


# ---------------------------------------------------------------------------
# ActionGate
# ---------------------------------------------------------------------------

class ActionGate:
    """
    Mandatory consent gate before any consequential action executes.

    Core behavior:
    - LOW          -> log only
    - MEDIUM/HIGH  -> single human approval required
    - IRREVERSIBLE -> multi-party approval required (default 2 approvers)

    Approvals can be delegated for bounded risk scopes and bounded time.
    Emergency halt propagates to all registered sessions.
    """

    def __init__(self, multi_party_threshold: int = 2) -> None:
        self._policy: Dict[str, ActionRiskLevel] = {}
        self._receipts: Dict[str, ConsentReceipt] = {}
        self._delegations: Dict[str, DelegationScope] = {}
        self._halted_sessions: Set[str] = set()
        self._registered_sessions: Set[str] = set()
        self._multi_party_threshold = max(2, multi_party_threshold)
        self._lock = threading.Lock()
        self._key = secrets.token_bytes(32)
        self._audit = get_audit()

    # ------------------------------------------------------------------
    # Signing helpers
    # ------------------------------------------------------------------

    def _sign(self, payload: bytes) -> str:
        return hmac.new(self._key, payload, hashlib.sha256).hexdigest()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _is_expired(self, iso_ts: Optional[str]) -> bool:
        if not iso_ts:
            return False
        return datetime.fromisoformat(iso_ts) < datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Session registration / emergency halt
    # ------------------------------------------------------------------

    def register_session(self, session_id: str) -> None:
        with self._lock:
            self._registered_sessions.add(session_id)

    def emergency_halt(self, session_id: Optional[str] = None, actor: str = "gaian") -> None:
        """
        Halt one session or all known sessions.
        This is the local precursor to distributed halt propagation.
        """
        with self._lock:
            if session_id is None:
                self._halted_sessions.update(self._registered_sessions)
                target = "all_sessions"
            else:
                self._halted_sessions.add(session_id)
                target = session_id
        self._audit.record(
            event_type=AuditEventType.POLICY_DECISION,
            actor=actor,
            action="emergency_halt",
            outcome="ok",
            resource=target,
            meta={"scope": "global" if session_id is None else "session"},
        )

    def is_halted(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._halted_sessions

    # ------------------------------------------------------------------
    # Tool risk registration
    # ------------------------------------------------------------------

    def register_tool(self, name: str, risk_level: ActionRiskLevel) -> None:
        with self._lock:
            self._policy[name] = risk_level

    def get_risk_level(self, name: str, default: ActionRiskLevel = ActionRiskLevel.MEDIUM) -> ActionRiskLevel:
        with self._lock:
            return self._policy.get(name, default)

    # ------------------------------------------------------------------
    # Delegation
    # ------------------------------------------------------------------

    def delegate(
        self,
        delegated_to: str,
        granted_by: str,
        risk_levels: List[ActionRiskLevel],
        expires_in_seconds: int = 3600,
    ) -> DelegationScope:
        scope = DelegationScope(
            delegated_to=delegated_to,
            granted_by=granted_by,
            risk_levels=[r.value for r in risk_levels],
            created_at=self._now(),
            expires_at=(datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)).isoformat(),
        )
        scope.signature = self._sign(scope.canonical_body())
        with self._lock:
            self._delegations[delegated_to] = scope
        self._audit.record(
            event_type=AuditEventType.PERMISSION_GRANT,
            actor=granted_by,
            action="delegate_approval",
            outcome="ok",
            resource=delegated_to,
            meta={"risk_levels": scope.risk_levels, "expires_at": scope.expires_at},
        )
        return scope

    def revoke_delegation(self, delegated_to: str, actor: str = "gaian") -> bool:
        with self._lock:
            existed = delegated_to in self._delegations
            self._delegations.pop(delegated_to, None)
        self._audit.record(
            event_type=AuditEventType.PERMISSION_DENY,
            actor=actor,
            action="revoke_delegation",
            outcome="ok" if existed else "noop",
            resource=delegated_to,
        )
        return existed

    def _delegation_allows(self, approver: str, risk_level: ActionRiskLevel) -> bool:
        with self._lock:
            scope = self._delegations.get(approver)
        if not scope:
            return False
        if self._is_expired(scope.expires_at):
            return False
        return risk_level.value in scope.risk_levels

    # ------------------------------------------------------------------
    # Approval flow
    # ------------------------------------------------------------------

    def request_approval(
        self,
        tool_name: str,
        actor: str,
        args: Dict[str, Any],
        session_id: str,
        risk_level: Optional[ActionRiskLevel] = None,
        expires_in_seconds: int = 900,
    ) -> ConsentReceipt:
        """
        Create a consent receipt and auto-approve it when policy allows.
        Every decision is audited.
        """
        self.register_session(session_id)

        if self.is_halted(session_id):
            receipt = ConsentReceipt(
                receipt_id=str(uuid.uuid4()),
                session_id=session_id,
                tool_name=tool_name,
                actor=actor,
                risk_level=(risk_level or self.get_risk_level(tool_name)).value,
                requirement=GateRequirement.HUMAN_REQUIRED.value,
                args=args,
                requested_at=self._now(),
                expires_at=(datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)).isoformat(),
                status="denied",
            )
            receipt.signature = self._sign(receipt.canonical_body())
            self._audit.record(
                event_type=AuditEventType.PERMISSION_DENY,
                actor=actor,
                action=f"gate:{tool_name}",
                outcome="halted",
                resource=session_id,
                meta={"reason": "emergency_halt"},
            )
            with self._lock:
                self._receipts[receipt.receipt_id] = receipt
            return receipt

        rl = risk_level or self.get_risk_level(tool_name)
        requirement = DEFAULT_GATE_POLICY[rl]
        receipt = ConsentReceipt(
            receipt_id=str(uuid.uuid4()),
            session_id=session_id,
            tool_name=tool_name,
            actor=actor,
            risk_level=rl.value,
            requirement=requirement.value,
            args=args,
            requested_at=self._now(),
            expires_at=(datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)).isoformat(),
        )

        if requirement in (GateRequirement.AUTO_APPROVE, GateRequirement.LOG_ONLY):
            receipt.status = "approved"
            receipt.approved_at = self._now()
            receipt.approved_by = ["system"]
            self._audit.record(
                event_type=AuditEventType.PERMISSION_GRANT,
                actor=actor,
                action=f"gate:{tool_name}",
                outcome="auto_approved",
                meta={"risk_level": rl.value, "requirement": requirement.value},
            )
        else:
            self._audit.record(
                event_type=AuditEventType.POLICY_DECISION,
                actor=actor,
                action=f"gate:{tool_name}",
                outcome="pending_approval",
                meta={"risk_level": rl.value, "requirement": requirement.value},
            )

        receipt.signature = self._sign(receipt.canonical_body())
        with self._lock:
            self._receipts[receipt.receipt_id] = receipt
        return receipt

    def approve(self, receipt_id: str, approver: str) -> bool:
        with self._lock:
            receipt = self._receipts.get(receipt_id)
            if not receipt:
                return False
            if receipt.status in ("denied", "expired"):
                return False
            if self._is_expired(receipt.expires_at):
                receipt.status = "expired"
                return False

            rl = ActionRiskLevel(receipt.risk_level)
            requirement = GateRequirement(receipt.requirement)

            # Authorization check: gaian always allowed; delegate may be allowed
            if approver != "gaian" and not self._delegation_allows(approver, rl):
                self._audit.record(
                    event_type=AuditEventType.PERMISSION_DENY,
                    actor=approver,
                    action="approve_receipt",
                    outcome="scope_denied",
                    resource=receipt_id,
                    meta={"risk_level": rl.value},
                )
                return False

            if approver not in receipt.approved_by:
                receipt.approved_by.append(approver)

            threshold = 1 if requirement == GateRequirement.HUMAN_REQUIRED else self._multi_party_threshold
            if len(receipt.approved_by) >= threshold:
                receipt.status = "approved"
                receipt.approved_at = self._now()

            receipt.signature = self._sign(receipt.canonical_body())

        self._audit.record(
            event_type=AuditEventType.PERMISSION_GRANT,
            actor=approver,
            action="approve_receipt",
            outcome=receipt.status,
            resource=receipt_id,
            meta={"approved_by": list(receipt.approved_by)},
        )
        return receipt.status == "approved"

    def deny(self, receipt_id: str, approver: str = "gaian") -> bool:
        with self._lock:
            receipt = self._receipts.get(receipt_id)
            if not receipt:
                return False
            receipt.status = "denied"
            receipt.signature = self._sign(receipt.canonical_body())
        self._audit.record(
            event_type=AuditEventType.PERMISSION_DENY,
            actor=approver,
            action="deny_receipt",
            outcome="denied",
            resource=receipt_id,
        )
        return True

    def is_approved(self, receipt_id: str) -> bool:
        with self._lock:
            receipt = self._receipts.get(receipt_id)
            if not receipt:
                return False
            if self._is_expired(receipt.expires_at):
                receipt.status = "expired"
                receipt.signature = self._sign(receipt.canonical_body())
                return False
            return receipt.status == "approved"

    def get_receipt(self, receipt_id: str) -> Optional[ConsentReceipt]:
        with self._lock:
            return self._receipts.get(receipt_id)

    def verify_receipt(self, receipt_id: str) -> bool:
        receipt = self.get_receipt(receipt_id)
        if not receipt:
            return False
        expected = self._sign(receipt.canonical_body())
        return hmac.compare_digest(expected, receipt.signature or "")
