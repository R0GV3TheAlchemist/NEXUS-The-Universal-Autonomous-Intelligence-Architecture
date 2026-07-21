"""
core/nexus_pulse.py
────────────────────────────────────────────────────────────────
NEXUS Pulse Engine  —  Node heartbeat, health tracking, and
event dispatch for the GAIA distributed intelligence layer.

Designed to integrate with the bootstrap_gaia() lifecycle in
server/startup.py and be importable as a standalone module in
environments where the full runtime is unavailable.

Node States
-----------
  ONLINE    — heartbeat within threshold, all systems nominal
  DEGRADED  — heartbeat late or subsystem reporting partial failure
  SHADOW    — node is operating in shadow_engine stealth mode
  OFFLINE   — heartbeat missed beyond timeout; node presumed down
  UNKNOWN   — no heartbeat received yet since registration

Usage (attach to a running session)
------------------------------------
  from core.nexus_pulse import NexusPulse, PulseNode

  pulse = NexusPulse()
  node  = pulse.register("gaia-primary", tags=["core", "runtime"])
  pulse.beat(node.node_id)          # call periodically from runtime loop
  pulse.start()                     # launch background watcher thread
  snapshot = pulse.snapshot()       # emit JSON-serialisable health dict
  pulse.stop()                      # graceful shutdown
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("gaia.nexus_pulse")


# ──────────────────────────────────────────────────────────────
# Node state enum
# ──────────────────────────────────────────────────────────────

class NodeState(str, Enum):
    ONLINE   = "ONLINE"
    DEGRADED = "DEGRADED"
    SHADOW   = "SHADOW"
    OFFLINE  = "OFFLINE"
    UNKNOWN  = "UNKNOWN"


# ──────────────────────────────────────────────────────────────
# PulseEvent — emitted to any registered listeners
# ──────────────────────────────────────────────────────────────

@dataclass
class PulseEvent:
    event_type: str          # "beat" | "state_change" | "eviction" | "warning"
    node_id: str
    node_name: str
    previous_state: Optional[NodeState]
    current_state: NodeState
    timestamp: float = field(default_factory=time.time)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type":     self.event_type,
            "node_id":        self.node_id,
            "node_name":      self.node_name,
            "previous_state": self.previous_state.value if self.previous_state else None,
            "current_state":  self.current_state.value,
            "timestamp":      self.timestamp,
            "meta":           self.meta,
        }


# ──────────────────────────────────────────────────────────────
# PulseNode — one registered intelligence node
# ──────────────────────────────────────────────────────────────

@dataclass
class PulseNode:
    node_id:          str
    name:             str
    tags:             List[str]
    registered_at:    float
    last_beat:        Optional[float]      = None
    beat_count:       int                  = 0
    state:            NodeState            = NodeState.UNKNOWN
    miss_count:       int                  = 0          # consecutive missed checks
    subsystem_status: Dict[str, str]       = field(default_factory=dict)

    def age(self) -> float:
        """Seconds since registration."""
        return time.time() - self.registered_at

    def silence(self) -> float:
        """Seconds since last heartbeat (or since registration if no beat yet)."""
        ref = self.last_beat if self.last_beat is not None else self.registered_at
        return time.time() - ref

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id":          self.node_id,
            "name":             self.name,
            "tags":             self.tags,
            "registered_at":    self.registered_at,
            "last_beat":        self.last_beat,
            "beat_count":       self.beat_count,
            "state":            self.state.value,
            "miss_count":       self.miss_count,
            "age_seconds":      round(self.age(), 2),
            "silence_seconds":  round(self.silence(), 2),
            "subsystem_status": self.subsystem_status,
        }


# ──────────────────────────────────────────────────────────────
# NexusPulse — the engine
# ──────────────────────────────────────────────────────────────

class NexusPulse:
    """
    Central heartbeat and node health tracker for the NEXUS/GAIA network.

    Parameters
    ----------
    beat_interval   : How often (seconds) the watcher thread evaluates nodes.
    degraded_after  : Seconds of silence before ONLINE -> DEGRADED.
    offline_after   : Seconds of silence before DEGRADED -> OFFLINE.
    evict_after     : Seconds offline before the node is removed from the
                      registry entirely.  Set to 0 to disable eviction.
    """

    def __init__(
        self,
        beat_interval: float  = 5.0,
        degraded_after: float = 15.0,
        offline_after: float  = 30.0,
        evict_after: float    = 300.0,
    ) -> None:
        self.beat_interval  = beat_interval
        self.degraded_after = degraded_after
        self.offline_after  = offline_after
        self.evict_after    = evict_after

        self._nodes:     Dict[str, PulseNode]               = {}
        self._listeners: List[Callable[[PulseEvent], None]] = []
        self._lock       = threading.RLock()
        self._thread:    Optional[threading.Thread]         = None
        self._running    = False

        logger.info(
            "[NexusPulse] initialized — interval=%.1fs degraded=%.1fs "
            "offline=%.1fs evict=%.1fs",
            beat_interval, degraded_after, offline_after, evict_after,
        )

    # ── Registration ──────────────────────────────────────────

    def register(
        self,
        name: str,
        node_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> PulseNode:
        """Register a new node and return the PulseNode handle."""
        nid  = node_id or str(uuid.uuid4())
        tags = tags or []

        with self._lock:
            if nid in self._nodes:
                logger.warning("[NexusPulse] node %s already registered — returning existing", nid)
                return self._nodes[nid]

            node = PulseNode(
                node_id=nid,
                name=name,
                tags=tags,
                registered_at=time.time(),
            )
            self._nodes[nid] = node
            logger.info("[NexusPulse] registered node '%s' (%s) tags=%s", name, nid[:8], tags)

        self._emit(PulseEvent(
            event_type="registered",
            node_id=nid,
            node_name=name,
            previous_state=None,
            current_state=NodeState.UNKNOWN,
        ))
        return node

    def deregister(self, node_id: str) -> bool:
        with self._lock:
            node = self._nodes.pop(node_id, None)
        if node:
            logger.info("[NexusPulse] deregistered node '%s'", node.name)
            return True
        return False

    # ── Heartbeat ─────────────────────────────────────────────

    def beat(
        self,
        node_id: str,
        subsystem_status: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Record a heartbeat for a node.

        Parameters
        ----------
        node_id          : The node's UUID string.
        subsystem_status : Optional dict of subsystem-name -> status string,
                           e.g. {"llm_router": "ok", "memory": "degraded"}.

        Returns True if the beat was accepted, False if node not found.
        """
        with self._lock:
            node = self._nodes.get(node_id)
            if not node:
                logger.warning("[NexusPulse] beat from unknown node %s — ignoring", node_id)
                return False

            prev_state       = node.state
            node.last_beat   = time.time()
            node.beat_count += 1
            node.miss_count  = 0

            if subsystem_status:
                node.subsystem_status.update(subsystem_status)

            if subsystem_status and any(v == "degraded" for v in subsystem_status.values()):
                new_state = NodeState.DEGRADED
            elif node.state == NodeState.SHADOW:
                new_state = NodeState.SHADOW
            else:
                new_state = NodeState.ONLINE

            node.state = new_state

        self._emit(PulseEvent(
            event_type="beat",
            node_id=node_id,
            node_name=node.name,
            previous_state=prev_state,
            current_state=new_state,
            meta={"beat_count": node.beat_count},
        ))

        if prev_state != new_state:
            logger.info(
                "[NexusPulse] node '%s' state %s -> %s",
                node.name, prev_state.value, new_state.value,
            )
        return True

    def set_shadow(self, node_id: str, shadow: bool = True) -> bool:
        """Place a node into / out of SHADOW mode (used by shadow_engine)."""
        with self._lock:
            node = self._nodes.get(node_id)
            if not node:
                return False
            prev       = node.state
            node.state = NodeState.SHADOW if shadow else NodeState.ONLINE
        self._emit(PulseEvent(
            event_type="state_change",
            node_id=node_id,
            node_name=node.name,
            previous_state=prev,
            current_state=node.state,
            meta={"shadow": shadow},
        ))
        return True

    # ── Event listeners ───────────────────────────────────────

    def add_listener(self, fn: Callable[[PulseEvent], None]) -> None:
        """Register a callback to receive PulseEvent objects."""
        with self._lock:
            self._listeners.append(fn)

    def remove_listener(self, fn: Callable[[PulseEvent], None]) -> None:
        with self._lock:
            self._listeners = [l for l in self._listeners if l is not fn]

    def _emit(self, event: PulseEvent) -> None:
        with self._lock:
            listeners = list(self._listeners)
        for fn in listeners:
            try:
                fn(event)
            except Exception as exc:
                logger.error("[NexusPulse] listener error: %s", exc)

    # ── Background watcher ────────────────────────────────────

    def start(self) -> None:
        """Start the background watcher thread."""
        if self._running:
            logger.warning("[NexusPulse] already running")
            return
        self._running = True
        self._thread  = threading.Thread(
            target=self._watch_loop,
            daemon=True,
            name="nexus-pulse-watcher",
        )
        self._thread.start()
        logger.info("[NexusPulse] watcher thread started")

    def stop(self) -> None:
        """Stop the watcher thread gracefully."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=self.beat_interval * 2)
            self._thread = None
        logger.info("[NexusPulse] stopped")

    def _watch_loop(self) -> None:
        while self._running:
            time.sleep(self.beat_interval)
            self._evaluate_all()

    def _evaluate_all(self) -> None:
        evict_ids: List[str] = []

        with self._lock:
            nodes = list(self._nodes.values())

        for node in nodes:
            if node.state == NodeState.SHADOW:
                continue

            silence = node.silence()
            prev    = node.state

            if silence >= self.offline_after:
                new_state = NodeState.OFFLINE
            elif silence >= self.degraded_after:
                new_state = NodeState.DEGRADED
            else:
                continue

            if new_state != prev:
                with self._lock:
                    if node.node_id in self._nodes:
                        self._nodes[node.node_id].state      = new_state
                        self._nodes[node.node_id].miss_count += 1

                logger.warning(
                    "[NexusPulse] node '%s' state %s -> %s (silence=%.1fs)",
                    node.name, prev.value, new_state.value, silence,
                )
                self._emit(PulseEvent(
                    event_type="state_change",
                    node_id=node.node_id,
                    node_name=node.name,
                    previous_state=prev,
                    current_state=new_state,
                    meta={"silence_seconds": round(silence, 2)},
                ))

            if (
                new_state == NodeState.OFFLINE
                and self.evict_after > 0
                and silence >= self.evict_after
            ):
                evict_ids.append(node.node_id)

        for nid in evict_ids:
            with self._lock:
                evicted = self._nodes.pop(nid, None)
            if evicted:
                logger.error(
                    "[NexusPulse] node '%s' EVICTED after %.0fs offline",
                    evicted.name, self.evict_after,
                )
                self._emit(PulseEvent(
                    event_type="eviction",
                    node_id=nid,
                    node_name=evicted.name,
                    previous_state=NodeState.OFFLINE,
                    current_state=NodeState.OFFLINE,
                ))

    # ── Introspection ─────────────────────────────────────────

    def snapshot(self) -> Dict[str, Any]:
        """Return a JSON-serialisable summary of all registered nodes."""
        with self._lock:
            nodes = {nid: n.to_dict() for nid, n in self._nodes.items()}
        counts = {s.value: 0 for s in NodeState}
        for n in nodes.values():
            counts[n["state"]] += 1
        return {
            "pulse_running": self._running,
            "node_count":    len(nodes),
            "state_counts":  counts,
            "nodes":         nodes,
        }

    def healthy(self) -> bool:
        """True if every registered node is ONLINE or SHADOW."""
        with self._lock:
            return all(
                n.state in (NodeState.ONLINE, NodeState.SHADOW, NodeState.UNKNOWN)
                for n in self._nodes.values()
            )

    def get_node(self, node_id: str) -> Optional[PulseNode]:
        with self._lock:
            return self._nodes.get(node_id)

    def nodes_by_state(self, state: NodeState) -> List[PulseNode]:
        with self._lock:
            return [n for n in self._nodes.values() if n.state == state]

    def __repr__(self) -> str:
        with self._lock:
            n = len(self._nodes)
        return f"<NexusPulse nodes={n} running={self._running}>"


# ──────────────────────────────────────────────────────────────
# Module-level singleton (optional convenience)
# ──────────────────────────────────────────────────────────────

_global_pulse: Optional[NexusPulse] = None


def get_pulse() -> NexusPulse:
    """Return the module-level singleton NexusPulse, creating it if needed."""
    global _global_pulse
    if _global_pulse is None:
        _global_pulse = NexusPulse()
    return _global_pulse
