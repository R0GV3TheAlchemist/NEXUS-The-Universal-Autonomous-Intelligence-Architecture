"""
tests/simulation/test_runner.py

Unit + integration tests for SimulationRunner, ScenarioEngine, and AgentHarness.
"""

from __future__ import annotations

import asyncio
import pytest

from core.simulation import (
    SimulationRunner,
    ScenarioEngine,
    Scenario,
    AgentHarness,
    StateSnapshot,
    SnapshotDiff,
    MetricsCollector,
    SimulationEventBus,
    SimulationEvent,
    EventType,
    SeedController,
)
from core.simulation.runner import RunnerConfig
from core.simulation.scenario import ScenarioStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_scenario(
    name: str = "test_scenario",
    n_agents: int = 1,
    max_steps_termination: int = 5,
    seed: int = 42,
) -> Scenario:
    """Create a minimal scenario that terminates after max_steps_termination ticks."""
    agents = [{"id": f"agent_{i}", "config": {}} for i in range(n_agents)]
    return Scenario(
        name=name,
        agents=agents,
        seed=seed,
        termination_condition=lambda states, step: step >= max_steps_termination - 1,
    )


# ---------------------------------------------------------------------------
# SeedController
# ---------------------------------------------------------------------------

class TestSeedController:
    def test_determinism(self):
        sc1 = SeedController(42)
        sc2 = SeedController(42)
        assert [sc1.random() for _ in range(10)] == [sc2.random() for _ in range(10)]

    def test_different_seeds_differ(self):
        sc1 = SeedController(1)
        sc2 = SeedController(2)
        assert sc1.random() != sc2.random()

    def test_seed_from_string(self):
        sc = SeedController()
        sc.set_seed_from_string("gaia")
        assert sc.current_seed is not None
        v1 = sc.random()
        sc.set_seed_from_string("gaia")
        assert sc.random() == v1

    def test_shuffle_is_deterministic(self):
        sc = SeedController(99)
        original = list(range(10))
        s1 = sc.shuffle(original)
        sc.set_seed(99)
        s2 = sc.shuffle(original)
        assert s1 == s2


# ---------------------------------------------------------------------------
# StateSnapshot
# ---------------------------------------------------------------------------

class TestStateSnapshot:
    def test_capture_produces_hash(self):
        state = {"agent_0": {"tick": 0, "alive": True}}
        snap = StateSnapshot.capture(step=0, state=state)
        assert len(snap.hash) == 64  # SHA-256 hex

    def test_same_state_same_hash(self):
        state = {"x": 1, "y": [1, 2, 3]}
        s1 = StateSnapshot.capture(0, state)
        s2 = StateSnapshot.capture(0, state)
        assert s1.hash == s2.hash

    def test_different_state_different_hash(self):
        s1 = StateSnapshot.capture(0, {"a": 1})
        s2 = StateSnapshot.capture(0, {"a": 2})
        assert s1.hash != s2.hash

    def test_json_roundtrip(self):
        state = {"agent": {"tick": 3, "alive": True}}
        snap = StateSnapshot.capture(3, state)
        restored = StateSnapshot.from_json(snap.to_json())
        assert restored.hash == snap.hash
        assert restored.step == 3

    def test_diff_identical(self):
        s1 = StateSnapshot.capture(0, {"a": 1})
        s2 = StateSnapshot.capture(1, {"a": 1})
        diff = SnapshotDiff.compute(s1, s2)
        assert diff.identical is True

    def test_diff_changed(self):
        s1 = StateSnapshot.capture(0, {"a": 1})
        s2 = StateSnapshot.capture(1, {"a": 2})
        diff = SnapshotDiff.compute(s1, s2)
        assert diff.identical is False
        assert len(diff.changed) == 1
        assert diff.changed[0][0] == "a"


# ---------------------------------------------------------------------------
# MetricsCollector
# ---------------------------------------------------------------------------

class TestMetricsCollector:
    def test_record_and_summary(self):
        m = MetricsCollector()
        for i in range(5):
            m.record("reward", float(i), step=i)
        s = m.summary("reward")
        assert s["count"] == 5
        assert s["min"] == 0.0
        assert s["max"] == 4.0

    def test_increment(self):
        m = MetricsCollector()
        m.increment("errors")
        m.increment("errors")
        assert m.dump()["counters"]["errors"] == 2.0

    def test_dump_keys(self):
        m = MetricsCollector()
        m.record("x", 1.0)
        d = m.dump()
        assert "counters" in d
        assert "gauges" in d
        assert "summaries" in d


# ---------------------------------------------------------------------------
# SimulationEventBus
# ---------------------------------------------------------------------------

class TestSimulationEventBus:
    def test_subscribe_and_emit(self):
        received = []

        async def handler(event: SimulationEvent):
            received.append(event)

        bus = SimulationEventBus()
        bus.subscribe(EventType.STEP_COMPLETED, handler)
        asyncio.run(bus.emit(SimulationEvent(EventType.STEP_COMPLETED, {"step": 1})))
        assert len(received) == 1
        assert received[0].payload["step"] == 1

    def test_subscribe_all(self):
        received = []

        async def handler(event: SimulationEvent):
            received.append(event.event_type)

        bus = SimulationEventBus()
        bus.subscribe_all(handler)
        asyncio.run(bus.emit(SimulationEvent(EventType.SIMULATION_STARTED, {})))
        asyncio.run(bus.emit(SimulationEvent(EventType.SIMULATION_ENDED, {})))
        assert EventType.SIMULATION_STARTED in received
        assert EventType.SIMULATION_ENDED in received

    def test_history(self):
        bus = SimulationEventBus()
        asyncio.run(bus.emit(SimulationEvent(EventType.STEP_STARTED, {"step": 0})))
        asyncio.run(bus.emit(SimulationEvent(EventType.STEP_COMPLETED, {"step": 0})))
        assert len(bus.get_history()) == 2


# ---------------------------------------------------------------------------
# AgentHarness
# ---------------------------------------------------------------------------

class TestAgentHarness:
    def test_null_agent_tick(self):
        harness = AgentHarness(agent_id="agent_0")
        asyncio.run(harness.start())
        output = asyncio.run(harness.tick(0))
        assert output.get("action") == "null"
        asyncio.run(harness.stop())

    def test_is_alive(self):
        harness = AgentHarness(agent_id="agent_1")
        assert not harness.is_alive
        asyncio.run(harness.start())
        assert harness.is_alive
        asyncio.run(harness.stop())
        assert not harness.is_alive

    def test_custom_agent_class(self):
        class EchoAgent:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def step(self, step_index, state):
                return {"echo": step_index}

        harness = AgentHarness(
            agent_id="echo",
            agent_class=EchoAgent,
            agent_config={},
        )
        asyncio.run(harness.start())
        out = asyncio.run(harness.tick(7))
        assert out["echo"] == 7


# ---------------------------------------------------------------------------
# SimulationRunner (integration)
# ---------------------------------------------------------------------------

class TestSimulationRunner:
    def test_run_completes(self):
        scenario = make_scenario("basic", n_agents=2, max_steps_termination=3)
        runner = SimulationRunner(config=RunnerConfig(max_steps=100, snapshot_every_n_steps=1))
        result = asyncio.run(runner.run(scenario))
        assert result.status == ScenarioStatus.COMPLETED
        assert result.passed
        assert result.duration_seconds > 0

    def test_run_captures_snapshots(self):
        scenario = make_scenario("snaps", max_steps_termination=10)
        runner = SimulationRunner(config=RunnerConfig(snapshot_every_n_steps=2))
        result = asyncio.run(runner.run(scenario))
        assert len(result.snapshots) >= 1

    def test_run_max_steps_fallback(self):
        # No termination condition → hits max_steps
        scenario = Scenario(name="no_term", agents=[{"id": "a0", "config": {}}])
        runner = SimulationRunner(config=RunnerConfig(max_steps=5))
        result = asyncio.run(runner.run(scenario))
        assert result.status == ScenarioStatus.MAX_STEPS_REACHED

    def test_metrics_recorded(self):
        scenario = make_scenario("metrics", max_steps_termination=5)
        runner = SimulationRunner()
        result = asyncio.run(runner.run(scenario))
        assert result.metrics["gauges"]["steps_completed"] >= 1


# ---------------------------------------------------------------------------
# ScenarioEngine
# ---------------------------------------------------------------------------

class TestScenarioEngine:
    def test_register_and_list(self):
        engine = ScenarioEngine()
        s = make_scenario("alpha")
        engine.register(s)
        assert "alpha" in engine.list_scenarios()

    def test_filter_by_tag(self):
        engine = ScenarioEngine()
        s1 = Scenario(name="tagged", tags=["smoke"])
        s2 = Scenario(name="untagged")
        engine.register(s1)
        engine.register(s2)
        results = engine.filter_by_tag("smoke")
        assert len(results) == 1
        assert results[0].name == "tagged"

    def test_execute_unknown_raises(self):
        engine = ScenarioEngine()
        runner = SimulationRunner()
        with pytest.raises(KeyError, match="not found"):
            asyncio.run(engine.execute("ghost", runner))

    def test_execute_known(self):
        engine = ScenarioEngine()
        s = make_scenario("run_me", max_steps_termination=2)
        engine.register(s)
        runner = SimulationRunner(config=RunnerConfig(max_steps=50))
        result = asyncio.run(engine.execute("run_me", runner))
        assert result.passed
