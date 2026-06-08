"""
core/planner/step_dispatcher.py

Action handler registry and step dispatcher for the GAIA task scheduler.

Responsibilities:
  - Define the _HANDLERS registry: action key → async coroutine factory
  - dispatch_step(goal, step, rt) — resolve + execute one GoalStep,
    call step.mark_done() / step.mark_failed(), goal.auto_advance()
  - submit_pending_steps(rt, user_id) — find the next PENDING step for
    every active goal belonging to user_id and submit it to rt._scheduler

Handler contract:
  Each handler is an async callable(goal, step, rt) -> Any.
  It MUST raise on failure so the scheduler retry / failure path fires.
  It MUST NOT call step.mark_done() itself — dispatch_step does that.

Adding a new action handler:
  1. Write  async def _handle_<name>(goal, step, rt): ...
  2. Register it: _HANDLERS["<action_key>"] = _handle_<name>

Canon: Doc 21 (Sovereignty), Doc 35 (Security)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable

from core.planner.goal import Goal, GoalStep
from core.planner.scheduler import Task

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Action handler type
# ---------------------------------------------------------------------------

HandlerFn = Callable[[Goal, GoalStep, Any], Awaitable[Any]]


# ---------------------------------------------------------------------------
# Built-in handlers
# ---------------------------------------------------------------------------

async def _handle_noop(goal: Goal, step: GoalStep, rt: Any) -> str:
    """Default no-op handler — marks the step done immediately."""
    log.debug("[StepDispatcher] noop step '%s' (goal=%s)", step.description, goal.id[:8])
    return "noop"


async def _handle_remember(goal: Goal, step: GoalStep, rt: Any) -> str:
    """Store a memory item from step.params into the runtime MemoryStore."""
    text       = step.params.get("text", step.description)
    kind       = step.params.get("kind", "note")
    importance = float(step.params.get("importance", 0.7))
    user_id    = goal.user_id

    await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: rt._memory_store.remember_sync(
            user_id=user_id,
            text=text,
            kind=kind,
            role="system",
            importance=importance,
            metadata={"goal_id": goal.id, "step_index": step.index},
        ),
    )
    log.info("[StepDispatcher] remembered step '%s' for goal=%s", step.description, goal.id[:8])
    return f"remembered: {text[:80]}"


async def _handle_recall(goal: Goal, step: GoalStep, rt: Any) -> list:
    """Recall memories matching step.params['query'] and store result in step.result."""
    query  = step.params.get("query", step.description)
    top_k  = int(step.params.get("top_k", 5))
    user_id = goal.user_id

    items = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: rt._memory_store.retrieve_sync(
            query=query, user_id=user_id, top_k=top_k
        ),
    )
    log.info("[StepDispatcher] recalled %d items for goal=%s", len(items), goal.id[:8])
    return [getattr(i, "text", str(i)) for i in items]


async def _handle_log(goal: Goal, step: GoalStep, rt: Any) -> str:
    """Emit a structured log entry — useful for audit trails inside goal chains."""
    message = step.params.get("message", step.description)
    level   = step.params.get("level", "info").lower()
    getattr(log, level, log.info)("[GoalLog] goal=%s step=%d: %s", goal.id[:8], step.index, message)
    return message


# ---------------------------------------------------------------------------
# Handler registry
# ---------------------------------------------------------------------------

_HANDLERS: dict[str, HandlerFn] = {
    "noop":    _handle_noop,
    "remember": _handle_remember,
    "recall":  _handle_recall,
    "log":     _handle_log,
}


def register_handler(action_key: str, fn: HandlerFn) -> None:
    """Register a custom handler at runtime (e.g. from a plugin)."""
    _HANDLERS[action_key] = fn
    log.debug("[StepDispatcher] registered handler for action_key='%s'", action_key)


# ---------------------------------------------------------------------------
# Core dispatch
# ---------------------------------------------------------------------------

async def dispatch_step(goal: Goal, step: GoalStep, rt: Any) -> Any:
    """
    Execute one GoalStep against the registered handler.

    On success: calls step.mark_done(result) and goal.auto_advance().
    On failure: calls step.mark_failed(error) and goal.auto_advance().
    Always re-raises so the TaskScheduler retry / on_failure path fires.
    """
    handler = _HANDLERS.get(step.action, _handle_noop)
    step.mark_started()
    try:
        result = await handler(goal, step, rt)
        step.mark_done(result)
        goal.auto_advance()
        log.info(
            "[StepDispatcher] step %d/%d DONE goal=%s action=%s",
            step.index, len(goal.steps) - 1, goal.id[:8], step.action,
        )
        return result
    except Exception as exc:
        step.mark_failed(str(exc))
        goal.auto_advance()
        log.warning(
            "[StepDispatcher] step %d FAILED goal=%s: %s",
            step.index, goal.id[:8], exc,
        )
        raise


# ---------------------------------------------------------------------------
# Queue submission helper
# ---------------------------------------------------------------------------

def submit_pending_steps(rt: Any, user_id: str) -> int:
    """
    Find the next PENDING step for every active goal belonging to user_id
    and submit a Task to rt._scheduler.

    Deduplication: skips goals that already have a scheduler task queued
    (checked via scheduler.pending_for_goal).

    Returns the number of tasks submitted.
    """
    submitted = 0
    active_goals = rt._goal_registry.active(user_id=user_id)

    for goal in active_goals:
        # Skip if this goal already has work queued
        if rt._scheduler.pending_for_goal(goal.id):
            continue

        step = goal.next_step()
        if step is None:
            continue

        # Snapshot references for the closure
        _goal = goal
        _step = step
        _rt   = rt

        async def _coroutine(_g=_goal, _s=_step, _r=_rt):
            return await dispatch_step(_g, _s, _r)

        task = Task(
            name=f"goal:{_goal.id[:8]}:step:{_step.index}:{_step.action}",
            coroutine=_coroutine,
            priority=_goal.priority.value,
            goal_id=_goal.id,
            step_index=_step.index,
            action_key=_step.action if _step.action != "noop" else None,
            context={"user_id": user_id, "goal_title": _goal.title},
            max_retries=1,
            backoff_sec=2.0,
        )
        rt._scheduler.submit(task)
        submitted += 1
        log.debug(
            "[StepDispatcher] submitted task for goal=%s step=%d action=%s",
            _goal.id[:8], _step.index, _step.action,
        )

    return submitted
