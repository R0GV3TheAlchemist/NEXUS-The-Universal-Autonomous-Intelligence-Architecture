"""
core/simulation/agent_harness.py

AgentHarness — isolated wrapper that manages a single simulated GAIA agent.

Responsibilities:
  - Instantiate and configure a GAIA agent in isolation
  - Expose a tick(step) interface called once per simulation step
  - Maintain agent state between ticks
  - Forward events to the shared SimulationEventBus
  - Clean up on stop()
"""

from __future__ import annotations

import asyncio
import copy
import logging
from typing import Any, Dict, Optional

from .events import SimulationEventBus, SimulationEvent, EventType

logger = logging.getLogger(__name__)


class AgentHarness:
    """
    Wraps a single GAIA agent for use within a simulation.

    If no real agent class is provided the harness operates in
    stub mode — useful for integration-testing the simulation
    infrastructure itself.

    Args:
        agent_id:     Unique string identifier for this agent
        agent_config: Dict passed verbatim to the underlying agent
        event_bus:    Shared SimulationEventBus
        agent_class:  Optional class to instantiate as the agent.
                      If None, a NullAgent stub is used.
    """

    def __init__(
        self,
        agent_id: str,
        agent_config: Optional[Dict[str, Any]] = None,
        event_bus: Optional[SimulationEventBus] = None,
        agent_class: Optional[Any] = None,
    ) -> None:
        self.agent_id = agent_id
        self.agent_config = agent_config or {}
        self.event_bus = event_bus or SimulationEventBus()
        self._agent_class = agent_class
        self._agent: Any = None
        self.state: Dict[str, Any] = {
            "agent_id": agent_id,
            "tick": 0,
            "alive": False,
            "outputs": [],
        }
        self._started = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Initialise the agent. Called once before the first tick."""
        if self._agent_class is not None:
            try:
                self._agent = self._agent_class(**self.agent_config)
                if hasattr(self._agent, "initialize"):
                    result = self._agent.initialize()
                    if asyncio.iscoroutine(result):
                        await result
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "[AgentHarness:%s] Failed to initialise agent class", self.agent_id
                )
                raise RuntimeError(
                    f"AgentHarness '{self.agent_id}' could not start: {exc}"
                ) from exc
        else:
            self._agent = _NullAgent(self.agent_id)

        self.state["alive"] = True
        self._started = True
        await self.event_bus.emit(
            SimulationEvent(
                EventType.AGENT_STARTED,
                {"agent_id": self.agent_id, "config": self.agent_config},
            )
        )
        logger.debug("[AgentHarness:%s] started", self.agent_id)

    async def stop(self) -> None:
        """Gracefully shut down the agent."""
        if self._agent is not None and hasattr(self._agent, "shutdown"):
            result = self._agent.shutdown()
            if asyncio.iscoroutine(result):
                await result
        self.state["alive"] = False
        await self.event_bus.emit(
            SimulationEvent(EventType.AGENT_STOPPED, {"agent_id": self.agent_id})
        )
        logger.debug("[AgentHarness:%s] stopped", self.agent_id)

    # ------------------------------------------------------------------
    # Tick
    # ------------------------------------------------------------------

    async def tick(self, step_index: int) -> Dict[str, Any]:
        """
        Advance the agent by one simulation step.

        Returns a dict describing the agent's output for this tick.
        """
        if not self._started:
            raise RuntimeError(
                f"AgentHarness '{self.agent_id}' was not started before tick."
            )

        self.state["tick"] = step_index

        try:
            if hasattr(self._agent, "step"):
                output = self._agent.step(step_index, copy.deepcopy(self.state))
                if asyncio.iscoroutine(output):
                    output = await output
            else:
                output = {"noop": True}
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[AgentHarness:%s] Exception during tick %d: %s",
                self.agent_id, step_index, exc
            )
            output = {"error": str(exc)}

        if isinstance(output, dict):
            self.state["outputs"].append(output)

        await self.event_bus.emit(
            SimulationEvent(
                EventType.AGENT_TICK,
                {"agent_id": self.agent_id, "step": step_index, "output": output},
            )
        )

        return output or {}

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def is_alive(self) -> bool:
        return self.state.get("alive", False)

    def get_output_history(self) -> list:
        return list(self.state.get("outputs", []))


# ---------------------------------------------------------------------------
# Null Agent — stub for harness-only tests
# ---------------------------------------------------------------------------

class _NullAgent:
    """A do-nothing agent used when no real agent class is wired in."""

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id

    def step(self, step_index: int, state: Dict[str, Any]) -> Dict[str, Any]:
        return {"agent_id": self.agent_id, "step": step_index, "action": "null"}
