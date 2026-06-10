"""
core/agent/agent_loop.py

The Agentic Loop — GAIA's autonomous execution runtime.

Implements the perceive → reason → act → observe → repeat/complete cycle
described in issue #228.

Design principles:
  - The Gaian is always in control: pause, inspect, resume at any point.
  - Hard halt conditions prevent runaway execution.
  - Every action and observation is logged for full observability.
  - The loop integrates with the Policy Engine before executing any action.
  - Canon ref: C01 (GAIA as orchestration layer), C-SENTINEL Article 4.

Canon Reference: C01, C-SENTINEL Article 4
Issue:          #228
Version:        1.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable, Optional

from core.agent.agent_models import (
    ActionStatus,
    AgentAction,
    HaltReason,
    LoopState,
    LoopStatus,
    Observation,
    Perception,
    Plan,
    PlannedAction,
)

try:
    from core.agent.action_gate import ActionGate, ActionRiskLevel
except Exception:
    ActionGate = None           # type: ignore[assignment,misc]
    ActionRiskLevel = None      # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


class AgentLoop:
    """
    The Agentic Loop — GAIA's core autonomous execution runtime.

    Usage:
        loop = AgentLoop(max_iterations=20)
        state = loop.run(perception=perception, plan=plan)

    The loop can be paused by calling loop.pause() from any thread or callback.
    It can be resumed by calling loop.resume().
    The full state is always accessible via loop.state.

    Acceptance Criteria:
      - Agentic loop is a first-class runtime component.
      - Supports multi-step plans with branching and fallback.
      - Each loop iteration is logged for observability.
      - Loop can be paused, inspected, and resumed by Gaian.
      - Hard halt conditions prevent runaway loops.
    """

    def __init__(
        self,
        max_iterations: int = 50,
        on_observation: Optional[Callable[[Observation], None]] = None,
        action_gate: Optional["ActionGate"] = None,
    ) -> None:
        """
        Args:
            max_iterations:  Hard limit on loop iterations. Prevents runaway execution.
            on_observation:  Optional callback fired after every observation. Use for
                             real-time UI updates or external logging.
            action_gate:     Optional ActionGate. If provided, every action must pass
                             consent / oversight enforcement before execution.
        """
        self.max_iterations   = max_iterations
        self.on_observation   = on_observation
        self.action_gate      = action_gate
        self.state            = LoopState(max_iterations=max_iterations)
        self._pause_requested = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, perception: Perception, plan: Plan) -> LoopState:
        """
        Execute the full agentic loop for the given perception and plan.
        Returns the final LoopState when the loop terminates.
        """
        self._initialise(perception, plan)

        step_index = 0

        while not self.state.is_terminal():
            # --- Pause check ---
            if self._pause_requested:
                self.state.status = LoopStatus.PAUSED
                logger.info("[AgentLoop] loop_id=%s PAUSED at step=%s iteration=%d",
                            self.state.loop_id, self.state.current_step, self.state.iteration)
                break

            # --- Hard halt: max iterations ---
            if self.state.iteration >= self.max_iterations:
                self._halt(HaltReason.MAX_ITERATIONS_REACHED)
                break

            # --- External / policy halt ---
            if self.action_gate and self.action_gate.is_halted(perception.session_id):
                self._halt(HaltReason.GAIAN_REQUESTED)
                break

            # --- Determine current step ---
            if step_index >= len(plan.steps):
                self._complete()
                break

            planned = plan.steps[step_index]
            self.state.current_step = planned.name

            # --- Act ---
            action = self._act(planned, perception)

            # --- Observe ---
            observation = self._observe(action, planned)
            self.state.log_observation(observation)

            if self.on_observation:
                try:
                    self.on_observation(observation)
                except Exception as cb_err:
                    logger.warning("[AgentLoop] on_observation callback error: %s", cb_err)

            # --- Halt? ---
            if observation.should_halt:
                self._halt(observation.halt_reason or HaltReason.CRITICAL_ACTION_FAILED)
                break

            # --- Branch or advance ---
            if observation.next_step:
                # Branching: jump to named step
                target = plan.get_step(observation.next_step)
                if target:
                    step_index = plan.steps.index(target)
                else:
                    logger.warning(
                        "[AgentLoop] branch target '%s' not found — advancing normally",
                        observation.next_step,
                    )
                    step_index += 1
            elif action.status == ActionStatus.SUCCESS and planned.on_success:
                # Normal advance — on_success branch
                target = plan.get_step(planned.on_success)
                step_index = plan.steps.index(target) if target else step_index + 1
            elif action.status in (ActionStatus.FAILURE, ActionStatus.SKIPPED) and planned.on_failure:
                target = plan.get_step(planned.on_failure)
                step_index = plan.steps.index(target) if target else step_index + 1
            else:
                step_index += 1

        if not self.state.is_terminal() and self.state.status != LoopStatus.PAUSED:
            self._complete()

        return self.state

    def pause(self) -> None:
        """
        Request a graceful pause at the end of the current iteration.
        Acceptance Criterion: Loop can be paused by Gaian at any time.
        """
        self._pause_requested = True
        logger.info("[AgentLoop] pause requested loop_id=%s", self.state.loop_id)

    def resume(self, plan: Optional[Plan] = None) -> LoopState:
        """
        Resume a paused loop, optionally with a revised plan.
        Acceptance Criterion: Loop can be resumed by Gaian at any time.
        """
        if self.state.status != LoopStatus.PAUSED:
            raise RuntimeError(
                f"Cannot resume loop in status '{self.state.status.value}'. "
                "Only PAUSED loops can be resumed."
            )
        self._pause_requested = False
        self.state.status = LoopStatus.RUNNING
        if plan:
            self.state.plan = plan
        logger.info("[AgentLoop] resumed loop_id=%s", self.state.loop_id)
        return self.run(self.state.perception, plan or self.state.plan)

    def inspect(self) -> dict:
        """
        Return a human-readable summary of the current loop state.
        Acceptance Criterion: Loop can be inspected by Gaian at any time.
        """
        return self.state.summary()

    # ------------------------------------------------------------------
    # Internal lifecycle
    # ------------------------------------------------------------------

    def _initialise(self, perception: Perception, plan: Plan) -> None:
        self.state.perception   = perception
        self.state.plan         = plan
        self.state.status       = LoopStatus.RUNNING
        self.state.started_at   = datetime.now(timezone.utc)
        self.state.iteration    = 0
        self._pause_requested   = False
        logger.info(
            "[AgentLoop] START loop_id=%s goal='%s' steps=%d max_iter=%d",
            self.state.loop_id, perception.goal, len(plan.steps), self.max_iterations,
        )
        if self.action_gate:
            self.action_gate.register_session(perception.session_id)

    def _act(self, planned: PlannedAction, perception: Perception) -> AgentAction:
        """Execute a single planned action and return the execution record."""
        action = AgentAction(
            step_name=planned.name,
            description=planned.description,
        )
        logger.info(
            "[AgentLoop] ACT loop_id=%s step='%s' iter=%d",
            self.state.loop_id, planned.name, self.state.iteration,
        )

        # --------------------------------------------------------------
        # Consent gate check before execution
        # --------------------------------------------------------------
        if self.action_gate:
            risk_level = None
            if planned.risk_level and ActionRiskLevel is not None:
                try:
                    risk_level = ActionRiskLevel(planned.risk_level)
                except Exception:
                    risk_level = None
            receipt = self.action_gate.request_approval(
                tool_name=planned.name,
                actor=perception.gaian_id,
                args=planned.args,
                session_id=perception.session_id,
                risk_level=risk_level,
            )
            if not self.action_gate.is_approved(receipt.receipt_id):
                action.skip(f"Approval not granted for '{planned.name}' ({receipt.requirement})")
                logger.warning(
                    "[AgentLoop] step '%s' SKIPPED — approval not granted receipt=%s",
                    planned.name, receipt.receipt_id,
                )
                return action

        try:
            result = planned.handler(**planned.args)
            action.complete(result)
        except Exception as exc:
            action.fail(str(exc))
            logger.error(
                "[AgentLoop] step '%s' FAILED: %s", planned.name, exc
            )
        return action

    def _observe(self, action: AgentAction, planned: PlannedAction) -> Observation:
        """Evaluate an action's outcome and decide what happens next."""
        should_halt  = False
        halt_reason  = None
        next_step    = None
        notes        = ""

        if action.status == ActionStatus.SKIPPED:
            if planned.critical:
                should_halt = True
                halt_reason = HaltReason.POLICY_DENIED
                notes = f"Critical step '{planned.name}' was skipped by ActionGate: {action.error}"
            else:
                notes = f"Step '{planned.name}' skipped by ActionGate: {action.error}"
                if planned.on_failure:
                    next_step = planned.on_failure
        elif action.status == ActionStatus.FAILURE:
            if planned.critical:
                should_halt = True
                halt_reason = HaltReason.CRITICAL_ACTION_FAILED
                notes = f"Critical step '{planned.name}' failed: {action.error}"
            else:
                notes = f"Step '{planned.name}' failed (non-critical): {action.error}"
                if planned.on_failure:
                    next_step = planned.on_failure
        else:
            notes = f"Step '{planned.name}' succeeded."
            if planned.on_success:
                next_step = planned.on_success

        obs = Observation(
            action=action,
            iteration=self.state.iteration,
            notes=notes,
            should_halt=should_halt,
            halt_reason=halt_reason,
            next_step=next_step,
        )
        logger.info(
            "[AgentLoop] OBSERVE loop_id=%s step='%s' status=%s halt=%s",
            self.state.loop_id, planned.name, action.status.value, should_halt,
        )
        return obs

    def _complete(self) -> None:
        self.state.status       = LoopStatus.COMPLETED
        self.state.halt_reason  = HaltReason.GOAL_ACHIEVED
        self.state.completed_at = datetime.now(timezone.utc)
        logger.info(
            "[AgentLoop] COMPLETE loop_id=%s iterations=%d",
            self.state.loop_id, self.state.iteration,
        )

    def _halt(self, reason: HaltReason) -> None:
        self.state.status       = LoopStatus.HALTED
        self.state.halt_reason  = reason
        self.state.completed_at = datetime.now(timezone.utc)
        logger.warning(
            "[AgentLoop] HALTED loop_id=%s reason=%s iterations=%d",
            self.state.loop_id, reason.value, self.state.iteration,
        )
