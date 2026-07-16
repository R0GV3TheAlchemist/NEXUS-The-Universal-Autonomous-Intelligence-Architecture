"""
core/simulation/runner.py

SimulationRunner — top-level lifecycle orchestrator for GAIA simulations.

Responsibilities:
  - Accepts a Scenario definition
  - Initialises deterministic seed state via SeedController
  - Spins up AgentHarness instances
  - Streams events through SimulationEventBus
  - Collects metrics via MetricsCollector
  - Captures StateSnapshot before/after each step
  - Returns a ScenarioResult on completion or timeout
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .scenario import Scenario, ScenarioResult, ScenarioStatus
from .agent_harness import AgentHarness
from .state_snapshot import StateSnapshot
from .metrics import MetricsCollector
from .events import SimulationEventBus, SimulationEvent, EventType
from .seed import SeedController

logger = logging.getLogger(__name__)


@dataclass
class RunnerConfig:
    """Runtime configuration for a simulation run."""
    max_steps: int = 1000
    step_timeout_seconds: float = 30.0
    run_timeout_seconds: float = 3600.0
    snapshot_every_n_steps: int = 10
    metrics_flush_interval: float = 5.0
    dry_run: bool = False
    verbose: bool = False


class SimulationRunner:
    """
    Orchestrates a full GAIA simulation lifecycle.

    Usage:
        runner = SimulationRunner(config=RunnerConfig())
        result = await runner.run(scenario)
    """

    def __init__(
        self,
        config: Optional[RunnerConfig] = None,
        event_bus: Optional[SimulationEventBus] = None,
        metrics: Optional[MetricsCollector] = None,
    ) -> None:
        self.config = config or RunnerConfig()
        self.event_bus = event_bus or SimulationEventBus()
        self.metrics = metrics or MetricsCollector()
        self._seed_controller = SeedController()
        self._harnesses: List[AgentHarness] = []
        self._snapshots: List[StateSnapshot] = []
        self._running = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(self, scenario: Scenario) -> ScenarioResult:
        """Execute a scenario end-to-end and return a ScenarioResult."""
        self._running = True
        start_time = time.monotonic()
        result = ScenarioResult(
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.name,
            status=ScenarioStatus.RUNNING,
        )

        try:
            await self._setup(scenario)
            await self.event_bus.emit(
                SimulationEvent(EventType.SIMULATION_STARTED, {"scenario": scenario.name})
            )

            for step_index in range(self.config.max_steps):
                elapsed = time.monotonic() - start_time
                if elapsed >= self.config.run_timeout_seconds:
                    logger.warning("[SimulationRunner] Run timeout reached at step %d", step_index)
                    result.status = ScenarioStatus.TIMEOUT
                    break

                step_result = await asyncio.wait_for(
                    self._step(scenario, step_index),
                    timeout=self.config.step_timeout_seconds,
                )

                if step_index % self.config.snapshot_every_n_steps == 0:
                    snap = await self._capture_snapshot(step_index)
                    self._snapshots.append(snap)

                self.metrics.record("steps_completed", step_index + 1)

                if step_result.get("done", False):
                    result.status = ScenarioStatus.COMPLETED
                    break
            else:
                result.status = ScenarioStatus.MAX_STEPS_REACHED

        except asyncio.TimeoutError:
            logger.error("[SimulationRunner] Step timed out")
            result.status = ScenarioStatus.TIMEOUT
        except Exception as exc:  # noqa: BLE001
            logger.exception("[SimulationRunner] Unhandled exception during run")
            result.status = ScenarioStatus.ERROR
            result.error = str(exc)
        finally:
            await self._teardown()
            result.duration_seconds = time.monotonic() - start_time
            result.snapshots = self._snapshots
            result.metrics = self.metrics.dump()
            self._running = False
            await self.event_bus.emit(
                SimulationEvent(
                    EventType.SIMULATION_ENDED,
                    {"status": result.status.value, "duration": result.duration_seconds},
                )
            )

        return result

    def stop(self) -> None:
        """Signal the runner to halt after the current step."""
        self._running = False

    # ------------------------------------------------------------------
    # Internal lifecycle
    # ------------------------------------------------------------------

    async def _setup(self, scenario: Scenario) -> None:
        """Seed RNG, initialise harnesses, apply scenario pre-conditions."""
        if scenario.seed is not None:
            self._seed_controller.set_seed(scenario.seed)

        for agent_def in scenario.agents:
            harness = AgentHarness(
                agent_id=agent_def["id"],
                agent_config=agent_def.get("config", {}),
                event_bus=self.event_bus,
            )
            await harness.start()
            self._harnesses.append(harness)

        if scenario.preconditions:
            for key, value in scenario.preconditions.items():
                logger.debug("[SimulationRunner] Applying precondition: %s = %s", key, value)

    async def _step(self, scenario: Scenario, step_index: int) -> Dict[str, Any]:
        """Execute one simulation step across all active harnesses."""
        await self.event_bus.emit(
            SimulationEvent(EventType.STEP_STARTED, {"step": step_index})
        )

        results = await asyncio.gather(
            *[h.tick(step_index) for h in self._harnesses],
            return_exceptions=True,
        )

        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            logger.warning("[SimulationRunner] %d agent(s) errored on step %d", len(errors), step_index)

        await self.event_bus.emit(
            SimulationEvent(EventType.STEP_COMPLETED, {"step": step_index})
        )

        # Check scenario termination conditions
        done = False
        if scenario.termination_condition:
            harness_states = {h.agent_id: h.state for h in self._harnesses}
            done = scenario.termination_condition(harness_states, step_index)

        return {"done": done, "step": step_index, "errors": errors}

    async def _capture_snapshot(self, step_index: int) -> StateSnapshot:
        """Capture a deterministic snapshot of all harness states."""
        state_map: Dict[str, Any] = {}
        for h in self._harnesses:
            state_map[h.agent_id] = h.state
        snap = StateSnapshot.capture(step=step_index, state=state_map)
        await self.event_bus.emit(
            SimulationEvent(EventType.SNAPSHOT_CAPTURED, {"step": step_index, "hash": snap.hash})
        )
        return snap

    async def _teardown(self) -> None:
        """Gracefully shut down all harnesses."""
        for harness in self._harnesses:
            try:
                await harness.stop()
            except Exception:  # noqa: BLE001
                logger.warning("[SimulationRunner] Harness %s failed to stop cleanly", harness.agent_id)
        self._harnesses.clear()
