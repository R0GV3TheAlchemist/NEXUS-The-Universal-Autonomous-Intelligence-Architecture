"""
core/simulation/events.py

SimulationEventBus — async pub/sub event system for simulation lifecycle events.

Provides:
  - EventType enum covering all simulation lifecycle moments
  - SimulationEvent dataclass
  - SimulationEventBus with subscribe/emit/replay
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    # Runner lifecycle
    SIMULATION_STARTED = "simulation.started"
    SIMULATION_ENDED = "simulation.ended"
    STEP_STARTED = "simulation.step.started"
    STEP_COMPLETED = "simulation.step.completed"
    SNAPSHOT_CAPTURED = "simulation.snapshot.captured"

    # Agent lifecycle
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"
    AGENT_TICK = "agent.tick"
    AGENT_ERROR = "agent.error"

    # Scenario
    SCENARIO_LOADED = "scenario.loaded"
    SCENARIO_TERMINATION = "scenario.termination"

    # Custom / extensible
    CUSTOM = "custom"


@dataclass
class SimulationEvent:
    """A single event emitted during a simulation run."""
    event_type: EventType
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: __import__("time").monotonic())


HandlerType = Callable[[SimulationEvent], Coroutine[Any, Any, None]]


class SimulationEventBus:
    """
    Async publish/subscribe bus for simulation events.

    Supports:
      - subscribe(event_type, async_handler)
      - subscribe_all(async_handler) — receives every event
      - emit(event) — broadcasts to all matching handlers
      - get_history() — returns list of all emitted events
      - replay(handler) — replay the full history to a new handler

    Usage:
        bus = SimulationEventBus()

        @bus.on(EventType.STEP_COMPLETED)
        async def on_step(event):
            print(event.payload)

        await bus.emit(SimulationEvent(EventType.STEP_COMPLETED, {"step": 0}))
    """

    def __init__(self) -> None:
        self._handlers: Dict[EventType, List[HandlerType]] = {}
        self._global_handlers: List[HandlerType] = []
        self._history: List[SimulationEvent] = []

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def subscribe(self, event_type: EventType, handler: HandlerType) -> None:
        """Register an async handler for a specific event type."""
        self._handlers.setdefault(event_type, []).append(handler)

    def subscribe_all(self, handler: HandlerType) -> None:
        """Register an async handler for ALL event types."""
        self._global_handlers.append(handler)

    def unsubscribe(self, event_type: EventType, handler: HandlerType) -> None:
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h is not handler
            ]

    def on(self, event_type: EventType) -> Callable[[HandlerType], HandlerType]:
        """Decorator: @bus.on(EventType.STEP_COMPLETED)"""
        def decorator(fn: HandlerType) -> HandlerType:
            self.subscribe(event_type, fn)
            return fn
        return decorator

    # ------------------------------------------------------------------
    # Emission
    # ------------------------------------------------------------------

    async def emit(self, event: SimulationEvent) -> None:
        """Broadcast an event to all registered handlers."""
        self._history.append(event)
        handlers = (
            self._handlers.get(event.event_type, [])
            + self._global_handlers
        )
        if not handlers:
            return
        results = await asyncio.gather(
            *[h(event) for h in handlers],
            return_exceptions=True,
        )
        for r in results:
            if isinstance(r, Exception):
                logger.warning("[EventBus] Handler raised: %s", r)

    # ------------------------------------------------------------------
    # History / Replay
    # ------------------------------------------------------------------

    def get_history(self, event_type: Optional[EventType] = None) -> List[SimulationEvent]:
        if event_type is None:
            return list(self._history)
        return [e for e in self._history if e.event_type == event_type]

    async def replay(self, handler: HandlerType) -> None:
        """Replay the full event history to a given handler."""
        for event in self._history:
            try:
                await handler(event)
            except Exception:  # noqa: BLE001
                logger.warning("[EventBus] Replay handler raised on event %s", event.event_type)

    def clear_history(self) -> None:
        self._history.clear()
