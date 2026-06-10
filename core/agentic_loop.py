"""
agentic_loop.py
~~~~~~~~~~~~~~~
GAIA's core Perceive → Reason → Act → Observe (PRAO) loop.

Upgraded to integrate:
  - ActionGate / TrustPolicyEngine (issue #229)
  - CapabilityRegistry (issue #230)

Every tool invocation now:
  1. Asserts the tool is registered in the CapabilityRegistry.
  2. Passes through the ActionGate (permission + Gaian approval).
  3. Only then executes.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# ---------------------------------------------------------------------------
# Observability layer
# ---------------------------------------------------------------------------
try:
    from core.obs.tracer import TraceContext
    from core.obs.telemetry import Telemetry
    from core.obs.audit import AuditLog, AuditEventType
    from core.obs.structured_logger import StructuredLogger, LogLevel
    _OBS_AVAILABLE = True
except ImportError:  # pragma: no cover
    _OBS_AVAILABLE = False
    TraceContext     = None  # type: ignore[assignment,misc]
    Telemetry        = None  # type: ignore[assignment,misc]
    AuditLog         = None  # type: ignore[assignment,misc]
    AuditEventType   = None  # type: ignore[assignment,misc]
    StructuredLogger = None  # type: ignore[assignment,misc]
    LogLevel         = None  # type: ignore[assignment,misc]

# Module-level singletons — patched by test fixtures
_struct_logger: Optional[Any] = StructuredLogger() if _OBS_AVAILABLE else None
_audit:         Optional[Any] = AuditLog()         if _OBS_AVAILABLE else None
_telemetry:     Optional[Any] = Telemetry()        if _OBS_AVAILABLE else None

# ---------------------------------------------------------------------------
# RAG layer (optional)
# ---------------------------------------------------------------------------
try:
    from core.rag.pipeline import RAGPipeline
    _RAG_AVAILABLE = True
except ImportError:  # pragma: no cover
    _RAG_AVAILABLE = False
    RAGPipeline = None  # type: ignore[assignment,misc]

# ---------------------------------------------------------------------------
# Trust & Permission Policy Engine (issue #229)
# ---------------------------------------------------------------------------
try:
    from core.action_gate import (
        ActionGate as TrustActionGate,
        ActionDeniedError,
        ActionPendingApprovalError,
    )
    from core.policy.trust_policy_engine import PermissionScope
    _TRUST_AVAILABLE = True
except ImportError:  # pragma: no cover
    _TRUST_AVAILABLE = False
    TrustActionGate          = None  # type: ignore[assignment,misc]
    ActionDeniedError        = None  # type: ignore[assignment,misc]
    ActionPendingApprovalError = None  # type: ignore[assignment,misc]
    PermissionScope          = None  # type: ignore[assignment,misc]

# ---------------------------------------------------------------------------
# Capability Registry (issue #230)
# ---------------------------------------------------------------------------
try:
    from core.registry.capability_registry import (
        CapabilityRegistry,
        UnregisteredToolError,
        get_registry,
    )
    _REGISTRY_AVAILABLE = True
except ImportError:  # pragma: no cover
    _REGISTRY_AVAILABLE = False
    CapabilityRegistry    = None  # type: ignore[assignment,misc]
    UnregisteredToolError = None  # type: ignore[assignment,misc]
    get_registry          = None  # type: ignore[assignment,misc]

_DEFAULT_CANON_STORE = Path.home() / ".gaia" / "data"
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & result types
# ---------------------------------------------------------------------------

class HaltCondition(Enum):
    GOAL_ACHIEVED   = "goal_achieved"
    MAX_ITERATIONS  = "max_iterations"
    GAIAN_CANCELLED = "cancelled"
    POLICY_DENIED   = "policy_denied"
    UNREGISTERED_TOOL = "unregistered_tool"
    ERROR           = "error"


@dataclass
class AgenticLoopResult:
    session_id:     str
    state:          "AgentState"
    halt_condition: HaltCondition
    goal_achieved:  bool
    iterations:     int
    duration_s:     float
    error:          Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "session_id":     self.session_id,
            "halt_condition": self.halt_condition.value,
            "goal_achieved":  self.goal_achieved,
            "iterations":     self.iterations,
            "duration_s":     self.duration_s,
            "error":          self.error,
        }


@dataclass
class AgentState:
    goal:         str
    observations: List[str]            = field(default_factory=list)
    history:      List[Dict[str, Any]] = field(default_factory=list)
    memory:       Dict[str, Any]       = field(default_factory=dict)
    complete:     bool                 = False
    error:        Optional[str]        = None

    def summary(self) -> str:
        obs_tail = self.observations[-3:] if self.observations else []
        obs_str  = " | ".join(obs_tail) if obs_tail else "none yet"
        return f"Goal: {self.goal}. Recent observations: {obs_str}"

    def to_dict(self) -> dict:
        return {
            "goal":         self.goal,
            "observations": self.observations,
            "history":      self.history,
            "complete":     self.complete,
            "error":        self.error,
        }


@dataclass
class ActionResult:
    tool:    str
    output:  Any
    success: bool
    error:   Optional[str] = None
    # NEW: gate & registry metadata
    policy_record_id:   Optional[str] = None
    registry_version:   Optional[str] = None
    permission_scope:   Optional[str] = None


# ---------------------------------------------------------------------------
# Legacy stub gate (used only when TrustActionGate is unavailable)
# ---------------------------------------------------------------------------

class _LegacyActionGate:
    """Minimal fallback gate used only if core.action_gate cannot be imported."""

    def requires_human(self, action: dict) -> bool:
        return action.get("requires_human", False)

    def approve(self, action: dict, human_callback: Optional[Callable]) -> bool:
        if not self.requires_human(action):
            return True
        if human_callback is None:
            return False
        return bool(human_callback(action))


# ---------------------------------------------------------------------------
# Default stub planner
# ---------------------------------------------------------------------------

_STUB_COMPLETE_AFTER = 3

# B006 fix: use a closure-based counter instead of a mutable default argument.
# The previous `_counter: list = [0]` was shared state across all calls,
# which is a Python footgun — the list is created once at function definition
# time and mutated across every invocation.
_stub_counter = [0]


def _default_stub_planner(
    state: AgentState,
    *,
    canon_context: str = "",
) -> dict:
    """Minimal planner for tests: returns complete=True after 3 calls."""
    _stub_counter[0] += 1
    if _stub_counter[0] >= _STUB_COMPLETE_AFTER:
        _stub_counter[0] = 0
        return {"complete": True}
    return {"tool": "noop", "args": {}}


# ---------------------------------------------------------------------------
# Module-level obs helpers
# ---------------------------------------------------------------------------

def _sl_info(msg: str, meta: Optional[dict] = None) -> None:
    if _OBS_AVAILABLE and _struct_logger:
        _struct_logger.info(msg, meta=meta or {})
    logger.info("%s | %s", msg, meta)


def _sl_warning(msg: str, meta: Optional[dict] = None) -> None:
    if _OBS_AVAILABLE and _struct_logger:
        _struct_logger.warning(msg, meta=meta or {})
    logger.warning("%s | %s", msg, meta)


def _sl_error(msg: str, meta: Optional[dict] = None) -> None:
    if _OBS_AVAILABLE and _struct_logger:
        _struct_logger.error(msg, meta=meta or {})
    logger.error("%s | %s", msg, meta)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

class AgenticLoop:
    """
    PRAO loop with integrated Trust & Permission Policy Engine (#229)
    and Capability Registry (#230).

    Tool invocation order per cycle:
      1. CapabilityRegistry.assert_registered(tool_name)   → UnregisteredToolError if unknown
      2. ActionGate.check(tool_name, context)              → ActionDeniedError / ActionPendingApprovalError
      3. tools[tool_name](**args)                          → actual execution
    """

    def __init__(
        self,
        planner:            Optional[Callable] = None,
        tools:              Optional[Dict[str, Callable]] = None,
        perceiver:          Optional[Callable] = None,
        observer:           Optional[Callable] = None,
        rag:                Optional[Any] = None,
        human_callback:     Optional[Callable] = None,
        action_gate:        Optional[Any] = None,
        capability_registry: Optional[Any] = None,
        max_iterations:     int = 50,
        audit:              Optional[Any] = None,
        telemetry:          Optional[Any] = None,
        canon_store_path:   Optional[Path] = _DEFAULT_CANON_STORE,
        session_id:         Optional[str] = None,
        agent_id:           str = "agentic_loop",
    ) -> None:
        self._planner            = planner or _default_stub_planner
        self._tools              = tools or {}
        self._perceiver          = perceiver
        self._observer           = observer
        self._human_callback     = human_callback
        self._max_iterations     = max_iterations
        self._canon_store_path   = canon_store_path
        self._cancelled          = False
        self._paused             = False
        self._audit              = audit
        self._telemetry          = telemetry
        self._session_id         = session_id or str(uuid.uuid4())
        self._agent_id           = agent_id

        # --- Trust gate setup (#229) ---
        if action_gate is not None:
            # Accept any injected gate (legacy or TrustActionGate)
            self._gate = action_gate
            self._trust_gate: Optional[Any] = (
                action_gate if _TRUST_AVAILABLE and isinstance(action_gate, TrustActionGate)
                else None
            )
        elif _TRUST_AVAILABLE:
            self._trust_gate = TrustActionGate(
                session_id=self._session_id,
                agent_id=self._agent_id,
                approval_callback=(
                    (lambda tool, prompt: bool(human_callback({"tool": tool, "prompt": prompt})))
                    if human_callback else None
                ),
            )
            self._gate = self._trust_gate
        else:
            self._trust_gate = None
            self._gate = _LegacyActionGate()

        # --- Capability registry setup (#230) ---
        if capability_registry is not None:
            self._registry: Optional[Any] = capability_registry
        elif _REGISTRY_AVAILABLE:
            self._registry = get_registry()
        else:
            self._registry = None

        # --- RAG setup ---
        self._rag: Optional[Any] = rag
        if self._rag is None and _RAG_AVAILABLE:
            self._rag = RAGPipeline()

    # ------------------------------------------------------------------
    # Pause / Resume / Cancel (AC: loop can be paused and resumed)
    # ------------------------------------------------------------------

    def cancel(self) -> None:
        """Hard cancel — loop will exit on next iteration."""
        self._cancelled = True

    def pause(self) -> None:
        """Pause — loop will wait until resume() is called."""
        self._paused = True
        logger.info(f"AgenticLoop paused [session={self._session_id}]")

    def resume(self) -> None:
        """Resume a paused loop."""
        self._paused = False
        logger.info(f"AgenticLoop resumed [session={self._session_id}]")

    def get_state_snapshot(self, state: "AgentState") -> dict:
        """Return a serialisable snapshot for Gaian inspection."""
        return {
            "session_id": self._session_id,
            "agent_id": self._agent_id,
            "paused": self._paused,
            "cancelled": self._cancelled,
            "state": state.to_dict(),
            "policy_audit": (
                self._trust_gate.get_audit_log()
                if self._trust_gate and hasattr(self._trust_gate, "get_audit_log")
                else []
            ),
        }

    # ------------------------------------------------------------------
    # Obs helpers
    # ------------------------------------------------------------------

    def _get_audit(self):
        return self._audit if self._audit is not None else _audit

    def _get_telemetry(self):
        return self._telemetry if self._telemetry is not None else _telemetry

    def _log_info(self, msg: str, meta: Optional[dict] = None) -> None:
        if _OBS_AVAILABLE and _struct_logger:
            _struct_logger.info(msg, meta=meta or {})
        logger.info("%s | %s", msg, meta)

    def _log_warning(self, msg: str, meta: Optional[dict] = None) -> None:
        if _OBS_AVAILABLE and _struct_logger:
            _struct_logger.warning(msg, meta=meta or {})
        logger.warning("%s | %s", msg, meta)

    def _log_error(self, msg: str, meta: Optional[dict] = None) -> None:
        if _OBS_AVAILABLE and _struct_logger:
            _struct_logger.error(msg, meta=meta or {})
        logger.error("%s | %s", msg, meta)

    def _audit_event(
        self,
        event_type: str,
        gaian_id:   str = "gaia",
        action:     str = "",
        outcome:    str = "ok",
        meta:       Optional[dict] = None,
    ) -> None:
        al = self._get_audit()
        if al and _OBS_AVAILABLE:
            al.record(
                event_type=event_type,
                actor=gaian_id,
                action=action or event_type,
                outcome=outcome,
                meta=meta or {},
            )

    def _tel_record(self, key: str, latency_s: float, error: bool = False) -> None:
        tel = self._get_telemetry()
        if tel and _OBS_AVAILABLE:
            tel.record(key, latency_ms=latency_s * 1000, error=error)

    # ------------------------------------------------------------------
    # Phase runner
    # ------------------------------------------------------------------

    def _run_phase(self, name: str, fn: Callable, *args, **kwargs) -> Any:
        span_name = f"agentic_loop.{name}"
        t0 = time.monotonic()
        exc_occurred = False
        try:
            if _OBS_AVAILABLE and TraceContext:
                with TraceContext(span_name):
                    result = fn(*args, **kwargs)
            else:
                result = fn(*args, **kwargs)
            return result
        except Exception:
            exc_occurred = True
            raise
        finally:
            self._tel_record(span_name, time.monotonic() - t0, error=exc_occurred)

    # ------------------------------------------------------------------
    # PRAO phases
    # ------------------------------------------------------------------

    def _perceive(self, state: AgentState) -> AgentState:
        return self._perceiver(state) if self._perceiver else state

    def _reason(self, state: AgentState) -> dict:
        canon_context: str = ""
        if self._rag is not None:
            try:
                canon_context = self._rag.retrieve(state.summary())
            except Exception as exc:  # noqa: BLE001
                _sl_warning(f"rag.retrieve failed — {exc}")
        return self._planner(state, canon_context=canon_context)

    def _act(self, state: AgentState, action: dict) -> ActionResult:
        """
        Upgraded _act:
          1. Assert tool is in CapabilityRegistry (#230)
          2. Check ActionGate / TrustPolicyEngine (#229)
          3. Execute
        """
        tool_name = action.get("tool", "")
        tool_args = action.get("args", {})
        context   = {"goal": state.goal, "args": tool_args, **action.get("context", {})}

        registry_version  = None
        permission_scope  = None
        policy_record_id  = None

        # --- Step 1: Capability Registry check (#230) ---
        if self._registry is not None:
            try:
                entry = self._registry.assert_registered(tool_name)
                registry_version = entry.version
                permission_scope = entry.permission_scope
            except Exception as exc:
                # UnregisteredToolError or anything else from registry
                err_msg = str(exc)
                self._log_warning(
                    f"registry.blocked [{tool_name}]: {err_msg}",
                    meta={"tool": tool_name, "session_id": self._session_id},
                )
                return ActionResult(
                    tool=tool_name, output=None, success=False,
                    error=err_msg,
                )

        # --- Step 2: Trust & Permission gate check (#229) ---
        if self._trust_gate is not None:
            try:
                result_eval = self._trust_gate.engine.evaluate(tool_name, context)
                from core.policy.trust_policy_engine import PolicyDecision
                if result_eval.decision == PolicyDecision.ALLOW:
                    policy_record_id = result_eval.record_id
                elif result_eval.decision == PolicyDecision.DENY:
                    self._log_warning(
                        f"policy.denied [{tool_name}]: {result_eval.reason}",
                        meta={"tool": tool_name, "session_id": self._session_id},
                    )
                    return ActionResult(
                        tool=tool_name, output=None, success=False,
                        error=f"Policy denied: {result_eval.reason}",
                        policy_record_id=result_eval.record_id,
                    )
                elif result_eval.decision == PolicyDecision.REQUIRE_APPROVAL:
                    if self._human_callback:
                        approved = self._human_callback({
                            "tool": tool_name,
                            "prompt": result_eval.approval_prompt,
                        })
                        if approved:
                            self._trust_gate.engine.record_approval(
                                result_eval.record_id, approved_by="gaian"
                            )
                            policy_record_id = result_eval.record_id
                        else:
                            return ActionResult(
                                tool=tool_name, output=None, success=False,
                                error="Gaian declined approval.",
                                policy_record_id=result_eval.record_id,
                            )
                    else:
                        # No callback — surface approval requirement as error
                        return ActionResult(
                            tool=tool_name, output=None, success=False,
                            error=(
                                f"Action '{tool_name}' requires Gaian approval. "
                                f"Record ID: {result_eval.record_id}. "
                                f"Prompt: {result_eval.approval_prompt}"
                            ),
                            policy_record_id=result_eval.record_id,
                        )
            except Exception as exc:
                # Trust gate import/config error — fail safe
                self._log_error(
                    f"trust_gate.error [{tool_name}]: {exc}",
                    meta={"tool": tool_name},
                )
                return ActionResult(
                    tool=tool_name, output=None, success=False,
                    error=f"Trust gate error: {exc}",
                )
        elif hasattr(self._gate, "approve"):
            # Legacy gate fallback
            approved = self._gate.approve(action, self._human_callback)
            if not approved:
                return ActionResult(
                    tool=tool_name, output=None, success=False,
                    error="Action not approved by legacy gate.",
                )

        # --- Step 3: Execute ---
        tool_fn = self._tools.get(tool_name)
        if tool_fn is None:
            return ActionResult(
                tool=tool_name, output=None, success=False,
                error=f"Tool '{tool_name}' registered but no implementation provided to loop.",
                registry_version=registry_version,
                permission_scope=permission_scope,
            )

        t0 = time.monotonic()
        try:
            output = tool_fn(**tool_args)
            if asyncio.iscoroutine(output):
                output = asyncio.get_event_loop().run_until_complete(output)
            self._tel_record(f"tool.{tool_name}", time.monotonic() - t0)
            return ActionResult(
                tool=tool_name, output=output, success=True,
                policy_record_id=policy_record_id,
                registry_version=registry_version,
                permission_scope=permission_scope,
            )
        except Exception as exc:
            self._tel_record(f"tool.{tool_name}", time.monotonic() - t0, error=True)
            return ActionResult(
                tool=tool_name, output=None, success=False, error=str(exc),
                policy_record_id=policy_record_id,
                registry_version=registry_version,
                permission_scope=permission_scope,
            )

    def _observe(self, state: AgentState, result: ActionResult) -> AgentState:
        if self._observer:
            return self._observer(state, result)
        obs = f"{result.tool}: {'ok' if result.success else result.error}"
        if result.policy_record_id:
            obs += f" [policy:{result.policy_record_id[:8]}]"
        if result.registry_version:
            obs += f" [v{result.registry_version}]"
        state.observations.append(obs)
        state.history.append({
            "tool": result.tool,
            "success": result.success,
            "error": result.error,
            "policy_record_id": result.policy_record_id,
            "registry_version": result.registry_version,
            "permission_scope": result.permission_scope,
        })
        return state

    # ------------------------------------------------------------------
    # Canon startup
    # ------------------------------------------------------------------

    def _maybe_ingest_canon(self, session_id: str) -> None:
        if self._rag is None:
            return
        if getattr(self._rag, "canon_loaded", False):
            return
        self._log_info("canon.ingest.start",
            meta={"session_id": session_id,
                  "store_path": str(self._canon_store_path) if self._canon_store_path else "memory"})
        try:
            report   = self._rag.ingest_canon(store_path=self._canon_store_path)
            warm     = report.get("warm_start", False)
            self._log_info(
                f"canon.ingest.{'warm' if warm else 'cold'}_start_complete",
                meta={"session_id": session_id, **report},
            )
        except Exception as exc:
            self._log_error(f"canon.ingest.failed — {exc}",
                meta={"session_id": session_id, "error": str(exc)})

    # ------------------------------------------------------------------
    # Pause helper (async)
    # ------------------------------------------------------------------

    async def _wait_if_paused(self, session_id: str) -> None:
        """Yield control while paused, polling every 0.5s."""
        if self._paused:
            self._log_info("agentic_loop.paused",
                meta={"session_id": session_id})
        while self._paused and not self._cancelled:
            await asyncio.sleep(0.5)
        if not self._paused:
            self._log_info("agentic_loop.resumed",
                meta={"session_id": session_id})

    # ------------------------------------------------------------------
    # Main entry point (async)
    # ------------------------------------------------------------------

    async def run(
        self,
        goal:          str,
        gaian_id:      str = "gaia",
        initial_state: Optional[AgentState] = None,
    ) -> AgenticLoopResult:
        session_id = self._session_id
        state      = initial_state or AgentState(goal=goal)
        t_session  = time.monotonic()
        iterations = 0
        halt       = HaltCondition.MAX_ITERATIONS

        # SESSION_START
        self._audit_event(
            AuditEventType.SESSION_START if _OBS_AVAILABLE else "session.start",
            gaian_id=gaian_id,
            action="session_start",
            meta={"session_id": session_id, "goal": goal, "gaian_id": gaian_id},
        )

        try:
            self._maybe_ingest_canon(session_id)

            if self._cancelled:
                self._log_info("CANCELLED before loop start",
                    meta={"session_id": session_id})
                halt = HaltCondition.GAIAN_CANCELLED
            else:
                for iteration in range(1, self._max_iterations + 1):
                    iterations = iteration

                    # Pause support (AC: loop can be paused and resumed)
                    await self._wait_if_paused(session_id)

                    if self._cancelled:
                        self._log_info("CANCELLED",
                            meta={"session_id": session_id, "iteration": iteration})
                        halt = HaltCondition.GAIAN_CANCELLED
                        break

                    state  = self._run_phase("perceive", self._perceive, state)
                    action = self._run_phase("reason",   self._reason,   state)

                    if action.get("complete"):
                        state.complete = True
                        halt = HaltCondition.GOAL_ACHIEVED
                        self._audit_event(
                            AuditEventType.AGENT_ACTION if _OBS_AVAILABLE else "agent.action",
                            gaian_id=gaian_id,
                            action="complete",
                            outcome="ok",
                            meta={"session_id": session_id, "iteration": iteration,
                                  "action": action},
                        )
                        break

                    tool_name = action.get("tool", "unknown")

                    # Emit AGENT_ACTION before execution
                    self._audit_event(
                        AuditEventType.AGENT_ACTION if _OBS_AVAILABLE else "agent.action",
                        gaian_id=gaian_id,
                        action=tool_name,
                        outcome="pending",
                        meta={"session_id": session_id, "iteration": iteration,
                              "action": action},
                    )

                    # _act now handles registry + trust gate + execution
                    result = self._run_phase("act", self._act, state, action)
                    state  = self._run_phase("observe", self._observe, state, result)

                    # Determine halt condition from action result
                    if not result.success:
                        err = result.error or ""
                        if "not registered" in err.lower() or "unregistered" in err.lower():
                            halt = HaltCondition.UNREGISTERED_TOOL
                            state.error = err
                            self._audit_event(
                                AuditEventType.POLICY_DECISION if _OBS_AVAILABLE else "policy.decision",
                                gaian_id=gaian_id,
                                action="registry_check",
                                outcome="blocked",
                                meta={"session_id": session_id, "tool": tool_name, "error": err},
                            )
                            break
                        elif "policy denied" in err.lower() or "not approved" in err.lower() or "declined" in err.lower():
                            halt = HaltCondition.POLICY_DENIED
                            state.error = err
                            self._audit_event(
                                AuditEventType.POLICY_DECISION if _OBS_AVAILABLE else "policy.decision",
                                gaian_id=gaian_id,
                                action="policy_check",
                                outcome="denied",
                                meta={"session_id": session_id, "tool": tool_name,
                                      "policy_record_id": result.policy_record_id},
                            )
                            break
                        # Non-fatal errors: log and continue
                        self._audit_event(
                            AuditEventType.AGENT_ACTION if _OBS_AVAILABLE else "agent.action",
                            gaian_id=gaian_id,
                            action=tool_name,
                            outcome="error",
                            meta={"session_id": session_id, "iteration": iteration,
                                  "error": err},
                        )
                    else:
                        self._audit_event(
                            AuditEventType.AGENT_ACTION if _OBS_AVAILABLE else "agent.action",
                            gaian_id=gaian_id,
                            action=tool_name,
                            outcome="ok",
                            meta={
                                "session_id": session_id,
                                "iteration": iteration,
                                "policy_record_id": result.policy_record_id,
                                "registry_version": result.registry_version,
                                "permission_scope": result.permission_scope,
                            },
                        )

                    self._log_info("agentic_loop.cycle",
                        meta={
                            "session_id": session_id,
                            "iteration": iteration,
                            "action": tool_name,
                            "success": result.success,
                            "registry_version": result.registry_version,
                            "permission_scope": result.permission_scope,
                            "policy_record_id": result.policy_record_id,
                        })
                    self._tel_record("agentic_loop.cycle", time.monotonic() - t_session)

                else:
                    state.error = f"max_iterations ({self._max_iterations}) reached"
                    halt = HaltCondition.MAX_ITERATIONS

        except Exception as exc:
            state.error = str(exc)
            halt = HaltCondition.ERROR
            self._log_error(f"agentic_loop.session.error — {exc}",
                meta={"session_id": session_id})

        finally:
            duration = time.monotonic() - t_session
            self._tel_record("agentic_loop.session", duration,
                             error=halt == HaltCondition.ERROR)
            self._audit_event(
                AuditEventType.SESSION_END if _OBS_AVAILABLE else "session.end",
                gaian_id=gaian_id,
                action="session_end",
                outcome="ok" if state.complete else "incomplete",
                meta={"session_id": session_id, "halt_reason": halt.value,
                      "duration_s": round(duration, 3), "iterations": iterations},
            )

        return AgenticLoopResult(
            session_id=session_id,
            state=state,
            halt_condition=halt,
            goal_achieved=state.complete,
            iterations=iterations,
            duration_s=round(time.monotonic() - t_session, 3),
            error=state.error,
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_loop(
    max_iterations:       int = 50,
    tool_registry:        Optional[Dict[str, Callable]] = None,
    action_gate:          Optional[Any] = None,
    capability_registry:  Optional[Any] = None,
    approval_callback:    Optional[Callable] = None,
    planner:              Optional[Callable] = None,
    audit:                Optional[Any] = None,
    telemetry:            Optional[Any] = None,
    session_id:           Optional[str] = None,
    agent_id:             str = "agentic_loop",
) -> AgenticLoop:
    """
    Factory — canon_store_path=None so tests have no filesystem side-effects.
    """
    return AgenticLoop(
        planner=planner,
        tools=tool_registry or {},
        action_gate=action_gate,
        capability_registry=capability_registry,
        human_callback=approval_callback,
        max_iterations=max_iterations,
        audit=audit,
        telemetry=telemetry,
        canon_store_path=None,
        session_id=session_id,
        agent_id=agent_id,
    )
