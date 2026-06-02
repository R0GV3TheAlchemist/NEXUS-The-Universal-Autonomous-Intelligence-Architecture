"""
core/action_gate.py
===================
ActionGate — consent-aware, risk-tiered action enforcement for GAIA-OS.

Every proposed action passes through ActionGate before execution.
The gate consults the ConsentLedger (if present), evaluates policy
rules, and either approves, flags, or raises on blocked actions.

Canon Refs:
  C18  — Consent & Action Safety Doctrine
  C04  — Gaian Identity

Trace integration (GAIATrace / AsyncGAIATrace)
----------------------------------------------
Pass an active trace context via the optional ``trace`` kwarg on both
``check()`` and ``enforce()``.  Events emitted per call:

  check():
    ACTION  — action_type, action_data, policy decision, risk_tier
    ERROR   — emitted only when check() itself raises unexpectedly

  enforce():
    ACTION  — action_type, action_data, policy decision, risk_tier
    ERROR   — emitted when the action is blocked and PermissionError is raised

All trace operations are wrapped in try/except — a broken trace writer
never silences a gate decision.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from core.trace import GAIATrace, AsyncGAIATrace

_TRACE_CANON_REFS = ["C18", "C04"]


# ---------------------------------------------------------------------------
# RiskTier
# ---------------------------------------------------------------------------

class RiskTier(str, Enum):
    """
    Canonical risk classification for GAIA-OS actions (C18).

    Tiers are ordered LOW < MEDIUM < HIGH < CRITICAL.  Every action
    processed by ActionGate is assigned a tier; the tier is included in
    check()/enforce() result dicts and in trace ACTION events.

    Tier semantics
    --------------
    LOW
        Read-only or informational actions.  No consent check needed.
        Examples: ``read_memory``, ``query_canon``, ``get_status``

    MEDIUM
        Stateful writes that are reversible.  Ledger consent recommended.
        Examples: ``write_memory``, ``update_preference``, ``schedule_task``

    HIGH
        Sensitive or privacy-adjacent operations.  Ledger consent required;
        flagged for elevated review.
        Examples: ``export_pii``, ``modify_canon``, ``escalate_privilege``

    CRITICAL
        Unconditionally blocked.  No consent pathway can approve these.
        Examples: ``delete_gaian``, ``override_consent``,
                  ``bypass_ethics_layer``, ``hard_reset_memory``
    """
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"

    def __lt__(self, other: "RiskTier") -> bool:
        _order = ["low", "medium", "high", "critical"]
        return _order.index(self.value) < _order.index(other.value)

    def __le__(self, other: "RiskTier") -> bool:
        return self == other or self < other


# ---------------------------------------------------------------------------
# Risk tier map  (action_type -> RiskTier)
# Unknown action types default to MEDIUM.
# ---------------------------------------------------------------------------

RISK_TIER_MAP: Dict[str, RiskTier] = {
    # LOW — read-only / informational
    "read_memory":         RiskTier.LOW,
    "query_canon":         RiskTier.LOW,
    "get_status":          RiskTier.LOW,
    "list_gaians":         RiskTier.LOW,
    "ping":                RiskTier.LOW,
    # MEDIUM — reversible writes
    "write_memory":        RiskTier.MEDIUM,
    "update_preference":   RiskTier.MEDIUM,
    "schedule_task":       RiskTier.MEDIUM,
    "send_message":        RiskTier.MEDIUM,
    "create_session":      RiskTier.MEDIUM,
    # HIGH — sensitive / privacy-adjacent (flagged)
    "modify_canon":        RiskTier.HIGH,
    "escalate_privilege":  RiskTier.HIGH,
    "export_pii":          RiskTier.HIGH,
    # CRITICAL — unconditionally blocked
    "delete_gaian":        RiskTier.CRITICAL,
    "override_consent":    RiskTier.CRITICAL,
    "bypass_ethics_layer": RiskTier.CRITICAL,
    "hard_reset_memory":   RiskTier.CRITICAL,
}

_DEFAULT_TIER = RiskTier.MEDIUM


def get_risk_tier(action_type: str) -> RiskTier:
    """Return the canonical RiskTier for *action_type*, defaulting to MEDIUM."""
    return RISK_TIER_MAP.get(action_type, _DEFAULT_TIER)


# ---------------------------------------------------------------------------
# Policy constants  (kept as frozensets for O(1) lookup)
# ---------------------------------------------------------------------------

BLOCKED_ACTION_TYPES: frozenset = frozenset({
    "delete_gaian",
    "override_consent",
    "bypass_ethics_layer",
    "hard_reset_memory",
})

FLAGGED_ACTION_TYPES: frozenset = frozenset({
    "modify_canon",
    "escalate_privilege",
    "export_pii",
})


# ---------------------------------------------------------------------------
# Trace helpers
# ---------------------------------------------------------------------------

def _emit_action(
    trace: Any,
    action_type: str,
    action_data: dict,
    decision: str,
    risk_tier: RiskTier,
    latency_ms: float,
) -> None:
    if trace is None:
        return
    try:
        from core.trace import TraceEventType
        trace.record_output(
            output={
                "action_type": action_type,
                "action_data": action_data,
                "decision":    decision,
                "risk_tier":   risk_tier.value,
            },
            event_type=TraceEventType.ACTION,
            canon_refs=_TRACE_CANON_REFS,
        )
        trace.record_meta("latency_ms", round(latency_ms, 3))
    except Exception:
        pass


def _emit_gate_error(
    trace: Any,
    action_type: str,
    reason: str,
) -> None:
    if trace is None:
        return
    try:
        from core.trace import TraceEventType
        trace.record_output(
            output={"action_type": action_type, "blocked_reason": reason},
            event_type=TraceEventType.ERROR,
            canon_refs=_TRACE_CANON_REFS,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# ActionGate
# ---------------------------------------------------------------------------

class ActionGate:
    """
    Consent-aware, risk-tiered action gate (C18).

    Usage::

        gate = ActionGate()

        # Non-raising check — returns a decision dict including 'risk_tier'
        result = gate.check("modify_canon", {"ref": "C32"}, trace=t)
        # result["risk_tier"] == "high"

        # Raising enforce — raises PermissionError on blocked actions
        gate.enforce("export_pii", {"fields": ["email"]}, trace=t)
    """

    def __init__(self, consent_ledger: Any = None) -> None:
        """
        Parameters
        ----------
        consent_ledger:
            Optional ConsentLedger instance.  When provided, gate
            delegates consent checks to it before applying policy rules.
        """
        self._ledger = consent_ledger

    # ------------------------------------------------------------------
    # Internal policy check
    # ------------------------------------------------------------------

    def _policy_check(
        self,
        action_type: str,
        action_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Apply built-in policy rules.  Returns a result dict with keys:
          status    : "allowed" | "flagged" | "blocked"
          reason    : human-readable string
          action_type : echoed back
          risk_tier : RiskTier value string
        """
        tier = get_risk_tier(action_type)

        if action_type in BLOCKED_ACTION_TYPES:
            return {
                "status":      "blocked",
                "reason":      f"Action '{action_type}' is unconditionally blocked by GAIA-OS policy (C18).",
                "action_type": action_type,
                "risk_tier":   tier.value,
            }

        if self._ledger is not None:
            try:
                ledger_ok = self._ledger.is_consented(action_type, action_data)
                if not ledger_ok:
                    return {
                        "status":      "blocked",
                        "reason":      f"ConsentLedger denied action '{action_type}'.",
                        "action_type": action_type,
                        "risk_tier":   tier.value,
                    }
            except Exception as exc:
                return {
                    "status":      "flagged",
                    "reason":      f"ConsentLedger raised during check: {exc}",
                    "action_type": action_type,
                    "risk_tier":   tier.value,
                }

        if action_type in FLAGGED_ACTION_TYPES:
            return {
                "status":      "flagged",
                "reason":      f"Action '{action_type}' requires elevated review (C18).",
                "action_type": action_type,
                "risk_tier":   tier.value,
            }

        return {
            "status":      "allowed",
            "reason":      "Action passed all policy checks.",
            "action_type": action_type,
            "risk_tier":   tier.value,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(
        self,
        action_type: str,
        action_data: Optional[Dict[str, Any]] = None,
        *,
        trace: Any = None,
        gaian_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Non-raising gate check.  Returns the policy result dict.

        Result dict keys
        ----------------
        status      : ``"allowed"`` | ``"flagged"`` | ``"blocked"``
        reason      : human-readable policy explanation
        action_type : echoed from input
        risk_tier   : ``RiskTier`` value string (``"low"`` … ``"critical"``)

        Parameters
        ----------
        action_type:
            Short identifier for the action (e.g. ``"export_pii"``)
        action_data:
            Arbitrary payload describing the action.  Forwarded to the
            ConsentLedger and included in the trace event.
        trace:
            Optional GAIATrace / AsyncGAIATrace context for event emission.
        gaian_id:
            Forwarded into trace events for per-Gaian attribution.
        """
        action_data = action_data or {}
        if gaian_id is not None:
            action_data = {"gaian_id": gaian_id, **action_data}

        t0 = time.perf_counter()
        try:
            result = self._policy_check(action_type, action_data)
        except Exception as exc:
            _emit_gate_error(trace, action_type, str(exc))
            raise
        latency_ms = (time.perf_counter() - t0) * 1000.0

        _emit_action(
            trace, action_type, action_data,
            result["status"],
            get_risk_tier(action_type),
            latency_ms,
        )
        return result

    def enforce(
        self,
        action_type: str,
        action_data: Optional[Dict[str, Any]] = None,
        *,
        trace: Any = None,
        gaian_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Raising gate check.  Identical to :meth:`check` but raises
        ``PermissionError`` when the policy result is ``"blocked"``.

        Parameters
        ----------
        action_type, action_data, trace, gaian_id:
            Same as :meth:`check`.

        Raises
        ------
        PermissionError
            When the action is blocked by policy or ConsentLedger.
        """
        result = self.check(
            action_type,
            action_data,
            trace=trace,
            gaian_id=gaian_id,
        )
        if result["status"] == "blocked":
            _emit_gate_error(trace, action_type, result["reason"])
            raise PermissionError(result["reason"])
        return result
