"""
core/infra/action_gate.py
(formerly core/action_gate.py — Phase C physical migration)

ActionGate — Risk-tiered action veto system.

Every action GAIA considers taking passes through this gate. Actions are
classified into three risk tiers and handled accordingly. This is a
programmatic gate, not a prompt-level suggestion — it operates at the
infrastructure level and cannot be bypassed by model output.

Risk Tiers (from GAIA Sovereignty Stack):
  GREEN  — Low risk. Proceed autonomously. Log for audit.
  YELLOW — Medium risk. Surface to user. Proceed on implicit approval.
  RED    — High risk. Hard stop. Explicit human confirmation required.

Epistemic Status: ESTABLISHED
Canon Ref: Doc 35 (Security), Doc 21 (Axiological — Sovereignty)
Trace Integration: GAIATrace(ACTION_GATE_DECISION) — Issue #171
"""

from enum import Enum
from typing import Callable, Optional
import datetime

try:
    from core.trace import GAIATrace, TraceEventType
    _TRACE_AVAILABLE = True
except ImportError:  # pragma: no cover — standalone / pre-#171 environments
    _TRACE_AVAILABLE = False


class RiskTier(Enum):
    GREEN = "green"    # Autonomous — log only
    YELLOW = "yellow"  # Surface to user — proceed on silence
    RED = "red"        # Hard stop — explicit confirmation required


class ActionGate:
    """
    Intercepts proposed actions, classifies them by risk tier,
    and enforces the appropriate confirmation protocol.

    The gate is the technical implementation of human sovereignty.
    It ensures the human sovereign retains ultimate authority over
    high-risk actions regardless of model intent or instruction.
    """

    def __init__(
        self,
        confirm_callback: Optional[Callable] = None,
        gaian_id: Optional[str] = None,
    ):
        self._confirm_callback = confirm_callback
        self._audit_log: list = []
        self._gaian_id = gaian_id

    def evaluate(self, action: dict) -> dict:
        """
        Evaluate an action against the risk tier system.

        Args:
            action: Dict with keys:
                      - 'type': str (action category)
                      - 'description': str (human-readable description)
                      - 'tier': RiskTier (declared risk level)
                      - 'payload': dict (action-specific data)

        Returns:
            Dict with keys:
              - 'approved': bool
              - 'tier': RiskTier
              - 'reason': str
        """
        tier = action.get("tier", RiskTier.YELLOW)

        if _TRACE_AVAILABLE:
            trace_ctx = GAIATrace(
                event=TraceEventType.ACTION_GATE_DECISION,
                gaian_id=self._gaian_id,
                canon_refs=["C01", "C30", "Doc35"],
                inputs={
                    "action_type": action.get("type", "unknown"),
                    "description": action.get("description", "")[:120],
                    "tier": tier.value if isinstance(tier, RiskTier) else str(tier),
                },
            )
        else:
            from contextlib import nullcontext
            trace_ctx = nullcontext()  # type: ignore[assignment]

        with trace_ctx as trace:
            result = self._evaluate_internal(action, tier)
            if _TRACE_AVAILABLE and trace is not None:
                trace.record_output({
                    "approved": result["approved"],
                    "reason": result["reason"],
                })

        return result

    def _evaluate_internal(self, action: dict, tier: RiskTier) -> dict:
        """Core tier-dispatch logic, separated so GAIATrace wraps the full call."""
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "action": action,
            "tier": tier.value,
        }

        if tier == RiskTier.GREEN:
            entry["approved"] = True
            entry["reason"] = "Auto-approved: GREEN tier"
            self._audit_log.append(entry)
            return {"approved": True, "tier": tier, "reason": entry["reason"]}

        elif tier == RiskTier.YELLOW:
            if self._confirm_callback:
                approved = self._confirm_callback(action, tier)
            else:
                approved = True
            entry["approved"] = approved
            entry["reason"] = f"YELLOW tier: {'approved' if approved else 'vetoed'} by user"
            self._audit_log.append(entry)
            return {"approved": approved, "tier": tier, "reason": entry["reason"]}

        elif tier == RiskTier.RED:
            if not self._confirm_callback:
                entry["approved"] = False
                entry["reason"] = "RED tier: no confirmation callback registered — BLOCKED"
                self._audit_log.append(entry)
                return {"approved": False, "tier": tier, "reason": entry["reason"]}
            approved = self._confirm_callback(action, tier)
            entry["approved"] = approved
            entry["reason"] = f"RED tier: explicitly {'approved' if approved else 'vetoed'} by human sovereign"
            self._audit_log.append(entry)
            return {"approved": approved, "tier": tier, "reason": entry["reason"]}

        entry["approved"] = False
        entry["reason"] = "Unknown risk tier — BLOCKED by default"
        self._audit_log.append(entry)
        return {"approved": False, "tier": tier, "reason": entry["reason"]}

    def get_audit_log(self) -> list:
        """Return the full audit log of all evaluated actions."""
        return list(self._audit_log)
