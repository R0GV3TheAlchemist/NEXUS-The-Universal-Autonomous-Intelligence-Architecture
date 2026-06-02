"""
core/action_gate.py
===================
ActionGate — consent-aware action enforcement for GAIA-OS.

Every proposed action passes through ActionGate before execution.
The gate consults the ConsentLedger (if present), evaluates policy
rules, and either approves, flags, or raises on blocked actions.

Canon Ref:
  C18  — Consent & Action Safety Doctrine
  C04  — Gaian Identity

Trace integration (GAIATrace / AsyncGAIATrace)
----------------------------------------------
Pass an active trace context via the optional `trace` kwarg on both
`check()` and `enforce()`.  Events emitted per call:

  check():
    ACTION  — action_type, action_data, policy decision ("allowed" / "flagged")
    ERROR   — emitted only when check() itself raises unexpectedly

  enforce():
    ACTION  — action_type, action_data, policy decision
    ERROR   — emitted when the action is blocked and PermissionError is raised

All trace operations are wrapped in try/except — a broken trace writer
never silences a gate decision.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from core.trace import GAIATrace, AsyncGAIATrace

_TRACE_CANON_REFS = ["C18", "C04"]


# ---------------------------------------------------------------------------
# Trace helpers
# ---------------------------------------------------------------------------

def _emit_action(
    trace: Any,
    action_type: str,
    action_data: dict,
    decision: str,
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
# Policy constants
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
# ActionGate
# ---------------------------------------------------------------------------

class ActionGate:
    """
    Consent-aware action gate.

    Usage::

        gate = ActionGate()

        # Non-raising check — returns a decision dict
        result = gate.check("modify_canon", {"ref": "C32"}, trace=t)

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
          status   : "allowed" | "flagged" | "blocked"
          reason   : human-readable string
          action_type : echoed back
        """
        if action_type in BLOCKED_ACTION_TYPES:
            return {
                "status": "blocked",
                "reason": f"Action '{action_type}' is unconditionally blocked by GAIA-OS policy (C18).",
                "action_type": action_type,
            }

        if self._ledger is not None:
            try:
                ledger_ok = self._ledger.is_consented(action_type, action_data)
                if not ledger_ok:
                    return {
                        "status": "blocked",
                        "reason": f"ConsentLedger denied action '{action_type}'.",
                        "action_type": action_type,
                    }
            except Exception as exc:
                return {
                    "status": "flagged",
                    "reason": f"ConsentLedger raised during check: {exc}",
                    "action_type": action_type,
                }

        if action_type in FLAGGED_ACTION_TYPES:
            return {
                "status": "flagged",
                "reason": f"Action '{action_type}' requires elevated review (C18).",
                "action_type": action_type,
            }

        return {
            "status": "allowed",
            "reason": "Action passed all policy checks.",
            "action_type": action_type,
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

        _emit_action(trace, action_type, action_data, result["status"], latency_ms)
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
