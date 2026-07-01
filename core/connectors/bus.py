"""
core.connectors.bus
===================
ConnectorBus — an in-process, async-capable publish/subscribe message bus
that routes ConnectorEvents from connector instances to any number of
registered handler coroutines.

Architecture
------------
The bus is the nervous system of the connector layer.  Connectors emit events
via ``bus.publish()``.  Any GAIA subsystem (workflows, agents, the future
os_interface layer) subscribes via ``bus.subscribe()`` using topic patterns.

Topic patterns follow a dot-separated hierarchy::

    calendar.event.created
    iot.sensor.temperature.reading
    os.filesystem.file.modified
    os.display.resolution.changed

Subscriptions match by exact string OR by prefix wildcard (``"iot.*"``,
``"os.*"``).
"""

from __future__ import annotations

import asyncio
import fnmatch
import logging
from collections import defaultdict
from typing import Awaitable, Callable, Dict, List

from .model import ConnectorEvent

HandlerFn = Callable[[ConnectorEvent], Awaitable[None]]

logger = logging.getLogger(__name__)


class ConnectorBus:
    """Async publish/subscribe event bus for connector events.

    Usage
    -----
    >>> bus = ConnectorBus()
    >>>
    >>> async def on_calendar_event(event: ConnectorEvent) -> None:
    ...     print(event.event_type, event.payload)
    >>>
    >>> bus.subscribe("calendar.*", on_calendar_event)
    >>> await bus.publish(some_connector_event)
    """

    def __init__(self) -> None:
        # pattern → list of handler coroutines
        self._subscriptions: Dict[str, List[HandlerFn]] = defaultdict(list)
        self._published_count: int = 0
        self._error_count: int = 0

    # ------------------------------------------------------------------
    # Subscription management
    # ------------------------------------------------------------------

    def subscribe(
        self,
        pattern: str,
        handler: HandlerFn,
    ) -> None:
        """Register ``handler`` to receive events matching ``pattern``.

        Parameters
        ----------
        pattern : str
            Exact event_type string OR a glob pattern (e.g. ``"iot.*"``,
            ``"os.filesystem.*"``, ``"*"``).
        handler : async callable
            Coroutine function ``(ConnectorEvent) -> None``.
        """
        self._subscriptions[pattern].append(handler)

    def unsubscribe(
        self,
        pattern: str,
        handler: HandlerFn,
    ) -> None:
        """Remove a previously registered handler."""
        handlers = self._subscriptions.get(pattern, [])
        try:
            handlers.remove(handler)
        except ValueError:
            pass
        if not handlers:
            self._subscriptions.pop(pattern, None)

    def subscription_count(self) -> int:
        """Return total number of handler registrations across all patterns."""
        return sum(len(v) for v in self._subscriptions.values())

    # ------------------------------------------------------------------
    # Publishing
    # ------------------------------------------------------------------

    async def publish(self, event: ConnectorEvent) -> int:
        """Deliver an event to all matching subscribers.

        Matches the event's ``event_type`` against all registered patterns
        using glob matching.  Handlers are called concurrently via
        ``asyncio.gather``.

        Returns
        -------
        int
            Number of handlers the event was delivered to.
        """
        matched_handlers: List[HandlerFn] = []

        for pattern, handlers in self._subscriptions.items():
            if fnmatch.fnmatch(event.event_type, pattern):
                matched_handlers.extend(handlers)

        if not matched_handlers:
            self._published_count += 1
            return 0

        results = await asyncio.gather(
            *[handler(event) for handler in matched_handlers],
            return_exceptions=True,
        )

        error_count = sum(1 for r in results if isinstance(r, Exception))
        if error_count:
            self._error_count += error_count
            for i, r in enumerate(results):
                if isinstance(r, Exception):
                    logger.error(
                        "ConnectorBus handler error for event '%s': %s",
                        event.event_type,
                        r,
                    )

        self._published_count += 1
        return len(matched_handlers) - error_count

    def publish_sync(self, event: ConnectorEvent) -> None:
        """Fire-and-forget synchronous wrapper around publish().

        Creates a task in the running event loop if one exists, otherwise
        runs the coroutine in a new loop.  Intended for use from synchronous
        code that cannot await.
        """
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.publish(event))
        except RuntimeError:
            asyncio.run(self.publish(event))

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        """Return bus throughput statistics."""
        return {
            "total_published": self._published_count,
            "total_handler_errors": self._error_count,
            "active_patterns": sorted(self._subscriptions.keys()),
            "total_handlers": self.subscription_count(),
        }
