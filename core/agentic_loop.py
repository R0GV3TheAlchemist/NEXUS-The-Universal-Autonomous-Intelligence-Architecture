"""
agentic_loop.py
~~~~~~~~~~~~~~~
GAIA's core Perceive → Reason → Act → Observe (PRAO) loop.

Revision notes
--------------
obs-wiring      : TraceContext spans, StructuredLogger records, Telemetry
                  counters, AuditLog events — all using real API signatures.
canon-rag       : _reason() calls RAGPipeline.retrieve() before the planner.
persisted-index : _maybe_ingest_canon() passes store_path to ingest_canon()
                  so Canon is only embedded once; subsequent cold starts
                  reuse the persisted SQLite index if the fingerprint matches.
fix-ci          : HaltCondition, AgenticLoopResult, create_loop(),
                  async run(), cancel() satisfy test_agentic_loop_obs.py.
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

_DEFAULT_CANON_STORE = Path.home() / ".gaia" / "data"
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & result types
# ---------------------------------------------------------------------------

class HaltCondition(Enum):
    """Reason the agentic loop terminated."""
    GOAL_ACHIEVED   = "goal_achieved"
    MAX_ITERATIONS  = "max_iterations"
    GAIAN_CANCELLED = "cancelled"
    ERROR           = "error"


@dataclass
class AgenticLoopResult:
    """Return value from AgenticLoop.run()."""
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


# ---------------------------------------------------------------------------
# Supporting data structures
# ---------------------------------------------------------------------------

@dataclass
class AgentState:
    """Mutable snapshot passed through each PRAO phase."""
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


# ---------------------------------------------------------------------------
# Action gate
# ---------------------------------------------------------------------------

class ActionGate:
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


def _default_stub_planner(
    state: AgentState,
    *,
    canon_context: str = "",
    _counter: list = [0],  # noqa: B006
) -> dict:
    """Minimal planner for tests: returns complete=True after 3 calls."""
    _counter[0] += 1
    if _counter[0] >= _STUB_COMPLETE_AFTER:
        _counter[0] = 0
        return {"complete": True}
    return {"tool": "noop", "args": {}}


# ---------------------------------------------------------------------------
# Helpers — thin wrappers so every call goes through the patchable singletons
# ---------------------------------------------------------------------------

def _sl_info(msg: str, meta: Optional[dict] = None) -> None:
    """Emit an INFO record to the module-level structured logger."""
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


def _audit_record(
    event_type: str,
    actor:      str = "gaia",
    action:     str = "",
    outcome:    str = "ok",
    meta:       Optional[dict] = None,
) -> None:
    """Record an audit event via the module-level AuditLog singleton."""
    if _OBS_AVAILABLE and _audit:
        _audit.record(
            event_type=event_type,
            actor=actor,
            action=action or event_type,
            outcome=outcome,
            meta=meta or {},
        )


def _tel_record(key: str, latency_s: float, error: bool = False) -> None:
    """Record a latency sample (converted to ms) via module-level Telemetry."""
    if _OBS_AVAILABLE and _telemetry:
        _telemetry.record(key, latency_ms=latency_s * 1000, error=error)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

class AgenticLoop:
    """
    Orchestrates the PRAO cycle for a single GAIA session.

    Parameters
    ----------
    planner          : callable(state, *, canon_context='') → action dict
    tools            : mapping of tool name → callable
    perceiver        : callable(state) → updated state (optional)
    observer         : callable(state, result) → updated state (optional)
    rag              : RAGPipeline instance (optional)
    human_callback   : callable(action) → bool for human-approval gate
    action_gate      : ActionGate-compatible object (optional)
    max_iterations   : safety ceiling (default 50)
    canon_store_path : Path to persist Canon SQLite index
    """

    def __init__(
        self,
        planner:          Optional[Callable] = None,
        tools:            Optional[Dict[str, Callable]] = None,
        perceiver:        Optional[Callable] = None,
        observer:         Optional[Callable] = None,
        rag:              Optional[Any] = None,
        human_callback:   Optional[Callable] = None,
        action_gate:      Optional[Any] = None,
        max_iterations:   int = 50,
        audit:            Optional[Any] = None,
        telemetry:        Optional[Any] = None,
        canon_store_path: Optional[Path] = _DEFAULT_CANON_STORE,
    ) -> None:
        self._planner          = planner or _default_stub_planner
        self._tools            = tools or {}
        self._perceiver        = perceiver
        self._observer         = observer
        self._human_callback   = human_callback
        self._max_iterations   = max_iterations
        self._gate             = action_gate or ActionGate()
        self._canon_store_path = canon_store_path
        self._cancelled        = False

        # Allow per-instance overrides (used by tests via create_loop)
        self._audit     = audit
        self._telemetry = telemetry

        self._rag: Optional[Any] = rag
        if self._rag is None and _RAG_AVAILABLE:
            self._rag = RAGPipeline()

    # ------------------------------------------------------------------
    # Cancel
    # ------------------------------------------------------------------

    def cancel(self) -> None:
        """Signal the loop to halt at the start of the next cycle."""
        self._cancelled = True

    # ------------------------------------------------------------------
    # Obs helpers (use instance override if set, else module singletons)
    # ------------------------------------------------------------------

    def _get_audit(self):
        return self._audit if self._audit is not None else _audit

    def _get_telemetry(self):
        return self._telemetry if self._telemetry is not None else _telemetry

    def _log_info(self, msg: str, meta: Optional[dict] = None) -> None:
        _sl_info(msg, meta)
        al = self._get_audit()
        if al:
            al.record(event_type=AuditEventType.AGENT_ACTION if _OBS_AVAILABLE else "agent.action",
                      actor="gaia", action=msg, outcome="ok", meta=meta or {})

    def _log_warning(self, msg: str, meta: Optional[dict] = None) -> None:
        _sl_warning(msg, meta)

    def _log_error(self, msg: str, meta: Optional[dict] = None) -> None:
        _sl_error(msg, meta)

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
        tool_name = action.get("tool", "")
        tool_fn   = self._tools.get(tool_name)
        if tool_fn is None:
            return ActionResult(tool=tool_name, output=None, success=False,
                                error=f"Unknown tool: {tool_name}")
        t0 = time.monotonic()
        try:
            output = tool_fn(**action.get("args", {}))
            if asyncio.iscoroutine(output):
                output = asyncio.get_event_loop().run_until_complete(output)
            elapsed = time.monotonic() - t0
            self._tel_record(f"tool.{tool_name}", elapsed)
            self._audit_event(
                AuditEventType.AGENT_ACTION if _OBS_AVAILABLE else "agent.action",
                action=tool_name, outcome="ok",
                meta={"tool": tool_name, "success": True, "duration_s": round(elapsed, 4)},
            )
            return ActionResult(tool=tool_name, output=output, success=True)
        except Exception as exc:  # noqa: BLE001
            elapsed = time.monotonic() - t0
            self._tel_record(f"tool.{tool_name}", elapsed, error=True)
            self._audit_event(
                AuditEventType.AGENT_ACTION if _OBS_AVAILABLE else "agent.action",
                action=tool_name, outcome="error",
                meta={"tool": tool_name, "success": False, "error": str(exc)},
            )
            return ActionResult(tool=tool_name, output=None, success=False, error=str(exc))

    def _observe(self, state: AgentState, result: ActionResult) -> AgentState:
        if self._observer:
            return self._observer(state, result)
        obs = f"{result.tool}: {'ok' if result.success else result.error}"
        state.observations.append(obs)
        state.history.append(result.__dict__)
        return state

    # ------------------------------------------------------------------
    # Canon startup
    # ------------------------------------------------------------------

    def _maybe_ingest_canon(self, session_id: str) -> None:
        if self._rag is None:
            return
        if getattr(self._rag, "canon_loaded", False):
            return
        _sl_info("canon.ingest.start",
            meta={"session_id": session_id,
                  "store_path": str(self._canon_store_path) if self._canon_store_path else "memory"})
        try:
            report = self._rag.ingest_canon(store_path=self._canon_store_path)
            warm = report.get("warm_start", False)
            _sl_info(
                f"canon.ingest.{'warm' if warm else 'cold'}_start_complete",
                meta={"session_id": session_id, **report},
            )
        except Exception as exc:  # noqa: BLE001
            _sl_error(f"canon.ingest.failed — {exc}",
                meta={"session_id": session_id, "error": str(exc)})

    # ------------------------------------------------------------------
    # Main entry point (async)
    # ------------------------------------------------------------------

    async def run(
        self,
        goal:          str,
        gaian_id:      str = "gaia",
        initial_state: Optional[AgentState] = None,
    ) -> AgenticLoopResult:
        session_id = str(uuid.uuid4())
        state      = initial_state or AgentState(goal=goal)
        t_session  = time.monotonic()
        iterations = 0
        halt       = HaltCondition.MAX_ITERATIONS

        self._audit_event(
            AuditEventType.SESSION_START if _OBS_AVAILABLE else "session.start",
            gaian_id=gaian_id,
            action="session_start",
            meta={"session_id": session_id, "goal": goal, "gaian_id": gaian_id},
        )

        try:
            self._maybe_ingest_canon(session_id)

            if self._cancelled:
                _sl_info("CANCELLED before loop start", meta={"session_id": session_id})
                halt = HaltCondition.GAIAN_CANCELLED
            else:
                for iteration in range(1, self._max_iterations + 1):
                    iterations = iteration

                    if self._cancelled:
                        _sl_info("CANCELLED",
                            meta={"session_id": session_id, "iteration": iteration})
                        halt = HaltCondition.GAIAN_CANCELLED
                        break

                    state  = self._run_phase("perceive", self._perceive, state)
                    action = self._run_phase("reason",   self._reason,   state)

                    if action.get("complete"):
                        state.complete = True
                        halt = HaltCondition.GOAL_ACHIEVED
                        break

                    # Gate — supports sync ActionGate and async evaluate() objects
                    raw_gate = self._gate
                    if hasattr(raw_gate, "evaluate") and asyncio.iscoroutinefunction(raw_gate.evaluate):
                        gate_obj    = await raw_gate.evaluate(action, gaian_id)
                        approved    = getattr(gate_obj, "approved", False)
                        needs_human = getattr(gate_obj, "requires_human_approval", False)
                        reason      = getattr(gate_obj, "reason", None)
                    else:
                        gate_result = self._gate.approve(action, self._human_callback)
                        if asyncio.iscoroutine(gate_result):
                            gate_result = await gate_result
                        approved    = bool(gate_result)
                        needs_human = False
                        reason      = None

                    if not approved:
                        policy  = "blocked"
                        outcome = "blocked"
                        self._audit_event(
                            AuditEventType.POLICY_DECISION if _OBS_AVAILABLE else "policy.decision",
                            gaian_id=gaian_id,
                            action="policy_check",
                            outcome=outcome,
                            meta={"session_id": session_id, "iteration": iteration,
                                  "action": action, "approved": False,
                                  "outcome": outcome, "reason": reason or policy},
                        )
                        if needs_human:
                            self._audit_event(
                                AuditEventType.PERMISSION_DENY if _OBS_AVAILABLE else "permission.deny",
                                gaian_id=gaian_id,
                                action="permission_check",
                                outcome="denied",
                                meta={"session_id": session_id, "action": action},
                            )
                        break

                    self._audit_event(
                        AuditEventType.POLICY_DECISION if _OBS_AVAILABLE else "policy.decision",
                        gaian_id=gaian_id,
                        action="policy_check",
                        outcome="approved",
                        meta={"session_id": session_id, "iteration": iteration,
                              "action": action, "approved": True},
                    )

                    result = self._run_phase("act",     self._act,     state, action)
                    state  = self._run_phase("observe",  self._observe, state, result)

                    _sl_info("agentic_loop.cycle",
                        meta={"session_id": session_id, "iteration": iteration,
                              "action": action.get("tool"), "success": result.success,
                              "progress": action.get("progress")})
                    self._tel_record("agentic_loop.cycle", time.monotonic() - t_session)

                else:
                    state.error = f"max_iterations ({self._max_iterations}) reached"
                    halt = HaltCondition.MAX_ITERATIONS

        except Exception as exc:  # noqa: BLE001
            state.error = str(exc)
            halt = HaltCondition.ERROR
            _sl_error(f"agentic_loop.session.error — {exc}",
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
    max_iterations:    int = 50,
    tool_registry:     Optional[Dict[str, Callable]] = None,
    action_gate:       Optional[Any] = None,
    approval_callback: Optional[Callable] = None,
    planner:           Optional[Callable] = None,
    audit:             Optional[Any] = None,
    telemetry:         Optional[Any] = None,
) -> AgenticLoop:
    """
    Factory to create a pre-configured AgenticLoop.
    canon_store_path is always None so tests have no filesystem side-effects.
    """
    return AgenticLoop(
        planner=planner,
        tools=tool_registry or {},
        action_gate=action_gate,
        human_callback=approval_callback,
        max_iterations=max_iterations,
        audit=audit,
        telemetry=telemetry,
        canon_store_path=None,
    )
