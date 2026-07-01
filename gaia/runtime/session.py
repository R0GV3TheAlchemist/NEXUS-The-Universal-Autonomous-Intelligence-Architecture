"""
gaia.runtime.session
~~~~~~~~~~~~~~~~~~~~
PrimordialSession — the lifecycle event bus at the heart of GAIA.

Responsibilities:
  - Assign a unique session UUID at birth.
  - Maintain a typed hook registry: event_name → list[callable].
  - Fire lifecycle events in order, catching and logging handler errors
    so one bad hook never silences the rest.
  - Expose session.end() which fires 'session_ended' exactly once,
    then marks the session closed so duplicate calls are no-ops.

Lifecycle events (in order):
    gaian_born        fired immediately on __init__
    gaian_named       fired when set_name() is called
    fragment_written  fired when write_fragment() is called
    epoch_closed      fired when close_epoch() is called
    session_ended     fired when end() is called

All handlers receive a single dict payload. The payload schema for
each event is documented on the fire_* methods below.
"""

import uuid
import logging
import threading
from datetime import datetime, timezone
from typing import Callable

logger = logging.getLogger("gaia.runtime.session")

# Canonical event names — import these instead of spelling strings.
EVT_GAIAN_BORN        = "gaian_born"
EVT_GAIAN_NAMED       = "gaian_named"
EVT_FRAGMENT_WRITTEN  = "fragment_written"
EVT_EPOCH_CLOSED      = "epoch_closed"
EVT_SESSION_ENDED     = "session_ended"

ALL_EVENTS = (
    EVT_GAIAN_BORN,
    EVT_GAIAN_NAMED,
    EVT_FRAGMENT_WRITTEN,
    EVT_EPOCH_CLOSED,
    EVT_SESSION_ENDED,
)


class PrimordialSession:
    """
    The primordial session — GAIA's runtime identity and event spine.

    Usage::

        session = PrimordialSession()
        session.register("gaian_named", my_handler)
        session.set_name("GAIA-Prime")
        # ... work happens ...
        session.end()
    """

    def __init__(self) -> None:
        self._session_id: str = str(uuid.uuid4())
        self._name: str | None = None
        self._born_at: datetime = datetime.now(timezone.utc)
        self._ended: bool = False
        self._lock = threading.Lock()

        # Registry: event_name → ordered list of callables
        self._hooks: dict[str, list[Callable]] = {evt: [] for evt in ALL_EVENTS}

        logger.info("[PrimordialSession] born  session_id=%s", self._session_id)
        self._fire(EVT_GAIAN_BORN, {
            "session_id": self._session_id,
            "born_at": self._born_at.isoformat(),
        })

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def name(self) -> str | None:
        return self._name

    @property
    def born_at(self) -> datetime:
        return self._born_at

    @property
    def is_ended(self) -> bool:
        return self._ended

    # ------------------------------------------------------------------
    # Hook registration
    # ------------------------------------------------------------------

    def register(self, event: str, handler: Callable, *, reason: str = "") -> None:
        """
        Register *handler* to be called when *event* fires.

        Args:
            event:   One of the EVT_* constants (e.g. 'gaian_named').
            handler: Any callable that accepts a single dict payload.
            reason:  Human-readable string logged at registration time
                     so startup logs are self-documenting.

        Raises:
            ValueError: If *event* is not a recognised lifecycle event.
        """
        if event not in self._hooks:
            raise ValueError(
                f"Unknown event '{event}'. Valid events: {ALL_EVENTS}"
            )
        with self._lock:
            self._hooks[event].append(handler)
        logger.debug(
            "[PrimordialSession] registered  event=%s  handler=%s  reason=%s",
            event, handler.__qualname__, reason or "(none)",
        )

    # ------------------------------------------------------------------
    # Lifecycle actions
    # ------------------------------------------------------------------

    def set_name(self, name: str) -> None:
        """
        Assign GAIA's display name and fire 'gaian_named'.

        Payload: {session_id, name, named_at}
        """
        self._name = name
        logger.info("[PrimordialSession] named  name=%s", name)
        self._fire(EVT_GAIAN_NAMED, {
            "session_id": self._session_id,
            "name": name,
            "named_at": datetime.now(timezone.utc).isoformat(),
        })

    def write_fragment(self, content: str, *, metadata: dict | None = None) -> str:
        """
        Record a memory fragment and fire 'fragment_written'.

        Returns the fragment_id so callers can reference it.

        Payload: {session_id, fragment_id, content, metadata, written_at}
        """
        fragment_id = str(uuid.uuid4())
        payload = {
            "session_id":  self._session_id,
            "fragment_id": fragment_id,
            "content":     content,
            "metadata":    metadata or {},
            "written_at":  datetime.now(timezone.utc).isoformat(),
        }
        logger.debug("[PrimordialSession] fragment_written  fragment_id=%s", fragment_id)
        self._fire(EVT_FRAGMENT_WRITTEN, payload)
        return fragment_id

    def close_epoch(self, summary: str, *, fragment_count: int = 0,
                    metadata: dict | None = None) -> str:
        """
        Close the current epoch and fire 'epoch_closed'.

        Returns the epoch_id.

        Payload: {session_id, epoch_id, summary, fragment_count, metadata, closed_at}
        """
        epoch_id = str(uuid.uuid4())
        payload = {
            "session_id":     self._session_id,
            "epoch_id":       epoch_id,
            "summary":        summary,
            "fragment_count": fragment_count,
            "metadata":       metadata or {},
            "closed_at":      datetime.now(timezone.utc).isoformat(),
        }
        logger.info("[PrimordialSession] epoch_closed  epoch_id=%s", epoch_id)
        self._fire(EVT_EPOCH_CLOSED, payload)
        return epoch_id

    def end(self) -> None:
        """
        End the session — fires 'session_ended' exactly once.

        Subsequent calls are silent no-ops so it's safe to call from
        both normal exit and exception handlers.

        Payload: {session_id, name, born_at, ended_at, duration_seconds}
        """
        with self._lock:
            if self._ended:
                return
            self._ended = True

        ended_at = datetime.now(timezone.utc)
        duration = (ended_at - self._born_at).total_seconds()
        logger.info(
            "[PrimordialSession] ended  session_id=%s  duration=%.1fs",
            self._session_id, duration,
        )
        self._fire(EVT_SESSION_ENDED, {
            "session_id":       self._session_id,
            "name":             self._name,
            "born_at":          self._born_at.isoformat(),
            "ended_at":         ended_at.isoformat(),
            "duration_seconds": duration,
        })

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _fire(self, event: str, payload: dict) -> None:
        """Invoke all registered handlers for *event* with *payload*."""
        with self._lock:
            handlers = list(self._hooks.get(event, []))
        for handler in handlers:
            try:
                handler(payload)
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "[PrimordialSession] handler error  event=%s  "
                    "handler=%s  error=%s",
                    event, handler.__qualname__, exc,
                )

    def __repr__(self) -> str:
        status = "ended" if self._ended else "active"
        return (
            f"<PrimordialSession id={self._session_id[:8]}... "
            f"name={self._name!r} status={status}>"
        )
