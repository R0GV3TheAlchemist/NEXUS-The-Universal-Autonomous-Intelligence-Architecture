"""
tests/agent/test_agent_loop.py

Full test suite for the Agentic Loop Architecture.
Covers: multi-step plans, branching, fallback, halt conditions,
pause/resume, observability, and inspection.

Canon Reference: C01 (GAIA as orchestration layer), C-SENTINEL Article 4
Issue:           #228
"""

import pytest

from core.agent.agent_loop import AgentLoop
from core.agent.agent_models import (
    ActionStatus,
    HaltReason,
    LoopStatus,
    Perception,
    Plan,
    PlannedAction,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def noop(**kwargs):
    return "ok"


def failing(**kwargs):
    raise RuntimeError("simulated failure")


def make_perception(goal: str = "test goal") -> Perception:
    return Perception(
        goal=goal,
        session_id="sess-test",
        gaian_id="gaian-test",
    )


def make_step(name: str, handler=noop, critical: bool = False,
              on_success=None, on_failure=None) -> PlannedAction:
    return PlannedAction(
        name=name,
        description=f"Step: {name}",
        handler=handler,
        critical=critical,
        on_success=on_success,
        on_failure=on_failure,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_plan() -> Plan:
    return Plan(
        goal="Run three steps",
        steps=[
            make_step("step-1"),
            make_step("step-2"),
            make_step("step-3"),
        ],
    )


@pytest.fixture
def loop() -> AgentLoop:
    return AgentLoop(max_iterations=20)


# ---------------------------------------------------------------------------
# LoopState
# ---------------------------------------------------------------------------

class TestLoopState:

    def test_initial_status_is_idle(self):
        loop = AgentLoop()
        assert loop.state.status == LoopStatus.IDLE

    def test_is_terminal_completed(self):
        from core.agent.agent_models import LoopState
        state = LoopState()
        state.status = LoopStatus.COMPLETED
        assert state.is_terminal()

    def test_is_terminal_halted(self):
        from core.agent.agent_models import LoopState
        state = LoopState()
        state.status = LoopStatus.HALTED
        assert state.is_terminal()

    def test_is_not_terminal_running(self):
        from core.agent.agent_models import LoopState
        state = LoopState()
        state.status = LoopStatus.RUNNING
        assert not state.is_terminal()

    def test_summary_contains_required_keys(self, loop, simple_plan):
        state = loop.run(make_perception(), simple_plan)
        summary = state.summary()
        for key in ["loop_id", "status", "goal", "iteration", "observations"]:
            assert key in summary


# ---------------------------------------------------------------------------
# Basic execution
# ---------------------------------------------------------------------------

class TestBasicExecution:

    def test_single_step_plan_completes(self, loop):
        plan = Plan(goal="single step", steps=[make_step("only-step")])
        state = loop.run(make_perception(), plan)
        assert state.status == LoopStatus.COMPLETED

    def test_multi_step_plan_completes(self, loop, simple_plan):
        state = loop.run(make_perception(), simple_plan)
        assert state.status == LoopStatus.COMPLETED

    def test_all_steps_executed(self, loop, simple_plan):
        state = loop.run(make_perception(), simple_plan)
        assert state.iteration == 3

    def test_observations_logged_per_step(self, loop, simple_plan):
        state = loop.run(make_perception(), simple_plan)
        assert len(state.observations) == 3

    def test_empty_plan_completes_immediately(self, loop):
        plan = Plan(goal="nothing to do", steps=[])
        state = loop.run(make_perception(), plan)
        assert state.status == LoopStatus.COMPLETED

    def test_completed_loop_has_halt_reason_goal_achieved(self, loop, simple_plan):
        state = loop.run(make_perception(), simple_plan)
        assert state.halt_reason == HaltReason.GOAL_ACHIEVED

    def test_completed_loop_has_completed_at(self, loop, simple_plan):
        state = loop.run(make_perception(), simple_plan)
        assert state.completed_at is not None


# ---------------------------------------------------------------------------
# Observability callback
# ---------------------------------------------------------------------------

class TestObservabilityCallback:

    def test_callback_fired_per_iteration(self, simple_plan):
        fired = []
        loop = AgentLoop(max_iterations=20, on_observation=lambda obs: fired.append(obs))
        loop.run(make_perception(), simple_plan)
        assert len(fired) == 3

    def test_callback_receives_observation_objects(self, simple_plan):
        from core.agent.agent_models import Observation
        received = []
        loop = AgentLoop(on_observation=lambda obs: received.append(obs))
        loop.run(make_perception(), simple_plan)
        assert all(isinstance(o, Observation) for o in received)


# ---------------------------------------------------------------------------
# Halt conditions
# ---------------------------------------------------------------------------

class TestHaltConditions:

    def test_critical_failure_halts_loop(self, loop):
        plan = Plan(
            goal="test halt",
            steps=[
                make_step("step-1"),
                make_step("step-critical", handler=failing, critical=True),
                make_step("step-3"),
            ],
        )
        state = loop.run(make_perception(), plan)
        assert state.status == LoopStatus.HALTED
        assert state.halt_reason == HaltReason.CRITICAL_ACTION_FAILED

    def test_critical_halt_stops_before_remaining_steps(self, loop):
        plan = Plan(
            goal="test halt stops early",
            steps=[
                make_step("step-critical", handler=failing, critical=True),
                make_step("step-should-not-run"),
            ],
        )
        state = loop.run(make_perception(), plan)
        assert state.iteration == 1  # Only the failing step ran

    def test_max_iterations_halts_loop(self):
        loop = AgentLoop(max_iterations=3)
        # Infinite-ish plan: more steps than max_iterations
        steps = [make_step(f"step-{i}") for i in range(10)]
        plan = Plan(goal="exceed limit", steps=steps)
        state = loop.run(make_perception(), plan)
        assert state.status == LoopStatus.HALTED
        assert state.halt_reason == HaltReason.MAX_ITERATIONS_REACHED

    def test_non_critical_failure_does_not_halt(self, loop):
        plan = Plan(
            goal="non-critical failure",
            steps=[
                make_step("step-fail", handler=failing, critical=False),
                make_step("step-continues"),
            ],
        )
        state = loop.run(make_perception(), plan)
        assert state.status == LoopStatus.COMPLETED


# ---------------------------------------------------------------------------
# Branching
# ---------------------------------------------------------------------------

class TestBranching:

    def test_on_success_branch_followed(self):
        executed = []

        def record(name):
            def handler(**kwargs):
                executed.append(name)
                return name
            return handler

        plan = Plan(
            goal="branching test",
            steps=[
                PlannedAction(
                    name="step-a",
                    description="A",
                    handler=record("a"),
                    on_success="step-c",
                ),
                PlannedAction(
                    name="step-b",
                    description="B (should be skipped)",
                    handler=record("b"),
                ),
                PlannedAction(
                    name="step-c",
                    description="C",
                    handler=record("c"),
                ),
            ],
        )
        loop = AgentLoop()
        loop.run(make_perception(), plan)
        assert "b" not in executed
        assert "c" in executed

    def test_on_failure_branch_followed(self):
        executed = []

        def record(name):
            def handler(**kwargs):
                executed.append(name)
                return name
            return handler

        plan = Plan(
            goal="failure branching",
            steps=[
                PlannedAction(
                    name="step-fail",
                    description="Fails",
                    handler=failing,
                    on_failure="step-recovery",
                ),
                PlannedAction(
                    name="step-should-skip",
                    description="Should be skipped",
                    handler=record("skipped"),
                ),
                PlannedAction(
                    name="step-recovery",
                    description="Recovery",
                    handler=record("recovery"),
                ),
            ],
        )
        loop = AgentLoop()
        loop.run(make_perception(), plan)
        assert "skipped" not in executed
        assert "recovery" in executed


# ---------------------------------------------------------------------------
# Pause and resume
# ---------------------------------------------------------------------------

class TestPauseResume:

    def test_pause_stops_execution(self):
        call_count = [0]

        def counting_handler(**kwargs):
            call_count[0] += 1
            return "ok"

        loop = AgentLoop(max_iterations=20)

        def pause_after_first(obs):
            if obs.iteration == 0:
                loop.pause()

        loop.on_observation = pause_after_first
        plan = Plan(
            goal="pause test",
            steps=[make_step(f"step-{i}", handler=counting_handler) for i in range(5)],
        )
        state = loop.run(make_perception(), plan)
        assert state.status == LoopStatus.PAUSED
        assert call_count[0] < 5

    def test_resume_non_paused_raises(self, loop):
        with pytest.raises(RuntimeError, match="PAUSED"):
            loop.resume()

    def test_inspect_returns_summary(self, loop, simple_plan):
        loop.run(make_perception(), simple_plan)
        summary = loop.inspect()
        assert summary["status"] == LoopStatus.COMPLETED.value
        assert summary["goal"] == "Run three steps"


# ---------------------------------------------------------------------------
# Perception and Plan models
# ---------------------------------------------------------------------------

class TestModels:

    def test_perception_has_timestamp(self):
        p = make_perception()
        assert p.timestamp is not None

    def test_plan_get_step_found(self, simple_plan):
        step = simple_plan.get_step("step-2")
        assert step is not None
        assert step.name == "step-2"

    def test_plan_get_step_not_found(self, simple_plan):
        step = simple_plan.get_step("nonexistent")
        assert step is None

    def test_agent_action_complete(self):
        from core.agent.agent_models import AgentAction
        action = AgentAction(step_name="s", description="d")
        action.complete("result")
        assert action.status == ActionStatus.SUCCESS
        assert action.result == "result"
        assert action.finished_at is not None

    def test_agent_action_fail(self):
        from core.agent.agent_models import AgentAction
        action = AgentAction(step_name="s", description="d")
        action.fail("something broke")
        assert action.status == ActionStatus.FAILURE
        assert action.error == "something broke"
