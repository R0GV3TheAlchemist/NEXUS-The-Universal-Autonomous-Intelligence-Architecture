"""
core/simulation — GAIA Simulation Framework

Provides a full harness for running, observing, and validating
GAIA agent scenarios in controlled simulation environments.

Modules:
    runner          — SimulationRunner: lifecycle orchestration
    scenario        — ScenarioEngine: scenario loading and execution
    agent_harness   — AgentHarness: isolated agent spin-up/teardown
    state_snapshot  — StateSnapshot: deterministic state capture
    metrics         — MetricsCollector: runtime telemetry
    events          — SimulationEventBus: pub/sub simulation events
    seed            — SeedController: deterministic RNG seeding
"""

from .runner import SimulationRunner
from .scenario import ScenarioEngine, Scenario, ScenarioResult
from .agent_harness import AgentHarness
from .state_snapshot import StateSnapshot, SnapshotDiff
from .metrics import MetricsCollector, MetricRecord
from .events import SimulationEventBus, SimulationEvent
from .seed import SeedController

__all__ = [
    "SimulationRunner",
    "ScenarioEngine",
    "Scenario",
    "ScenarioResult",
    "AgentHarness",
    "StateSnapshot",
    "SnapshotDiff",
    "MetricsCollector",
    "MetricRecord",
    "SimulationEventBus",
    "SimulationEvent",
    "SeedController",
]
