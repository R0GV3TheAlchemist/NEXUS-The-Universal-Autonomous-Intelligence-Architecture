"""
core/mesh/crdt_state.py
=======================
CRDT Shared State engine for MotherThread P2P coordination.

Implements two foundational CRDT primitives:

  LWWRegister  — Last-Write-Wins Register (per-key scalar / dict values).
                 Conflict resolution: highest (node_id, timestamp) wins.

  ORSet        — Observed-Remove Set.
                 Add wins over concurrent remove.  Each element is tagged
                 with a unique dot (node_id, counter) so concurrent adds
                 of the same value by different nodes are preserved.

CRDTStateEngine wraps both and exposes a clean merge / gossip API so the
MotherThread can replicate state across P2P mesh peers without a central
coordinator.

Canon Ref:
  C04  — privacy-first: no Gaian slugs or names stored in shared CRDT state
  C43  — epistemic integrity: state is observable, not interpretive
  C47  — sovereign nodes; no single point of authority
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LWW Register
# ---------------------------------------------------------------------------

@dataclass
class LWWEntry:
    value: Any
    timestamp: float
    node_id: str

    def dominates(self, other: "LWWEntry") -> bool:
        """True if this entry should win over other."""
        if self.timestamp != other.timestamp:
            return self.timestamp > other.timestamp
        # Tie-break by node_id lexicographic order (deterministic)
        return self.node_id > other.node_id


class LWWRegister:
    """
    Last-Write-Wins Register.

    Each key maps to the LWWEntry with the highest (timestamp, node_id).
    Merge is commutative, associative, and idempotent — the three CRDT
    lattice laws.
    """

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        self._store: Dict[str, LWWEntry] = {}

    def set(self, key: str, value: Any, timestamp: Optional[float] = None) -> None:
        """Write a value for key. Uses current time if timestamp not given."""
        ts = timestamp if timestamp is not None else time.time()
        entry = LWWEntry(value=value, timestamp=ts, node_id=self.node_id)
        existing = self._store.get(key)
        if existing is None or entry.dominates(existing):
            self._store[key] = entry

    def get(self, key: str, default: Any = None) -> Any:
        entry = self._store.get(key)
        return entry.value if entry is not None else default

    def merge(self, remote: "LWWRegister") -> None:
        """Merge remote register into self. Idempotent."""
        for key, remote_entry in remote._store.items():
            local_entry = self._store.get(key)
            if local_entry is None or remote_entry.dominates(local_entry):
                self._store[key] = remote_entry

    def merge_dict(self, state_dict: dict) -> None:
        """
        Merge a serialised register payload (from gossip).
        state_dict format: {key: {"value": ..., "timestamp": ..., "node_id": ...}}
        """
        for key, entry_dict in state_dict.items():
            try:
                remote_entry = LWWEntry(
                    value=entry_dict["value"],
                    timestamp=float(entry_dict["timestamp"]),
                    node_id=str(entry_dict["node_id"]),
                )
                local_entry = self._store.get(key)
                if local_entry is None or remote_entry.dominates(local_entry):
                    self._store[key] = remote_entry
            except (KeyError, TypeError, ValueError) as exc:
                logger.warning("[LWWRegister] Skipping malformed entry for key %s: %s", key, exc)

    def to_dict(self) -> dict:
        return {
            key: {
                "value": e.value,
                "timestamp": e.timestamp,
                "node_id": e.node_id,
            }
            for key, e in self._store.items()
        }

    def keys(self):
        return self._store.keys()

    def __len__(self) -> int:
        return len(self._store)


# ---------------------------------------------------------------------------
# OR-Set
# ---------------------------------------------------------------------------

# A dot uniquely identifies one add-operation: (node_id, logical_counter)
Dot = Tuple[str, int]


class ORSet:
    """
    Observed-Remove Set (OR-Set).

    Each element is stored with the set of unique "dots" that added it.
    Remove only removes the dots the removing node has observed — so a
    concurrent add on another node will survive the remove.

    Merge is commutative, associative, and idempotent.
    """

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        self._counter: int = 0
        # element → set of dots that added it
        self._entries: Dict[Any, Set[Dot]] = {}
        # tombstoned dots (removed)
        self._tombstones: Set[Dot] = set()

    def _next_dot(self) -> Dot:
        self._counter += 1
        return (self.node_id, self._counter)

    def add(self, element: Any) -> None:
        """Add an element."""
        dot = self._next_dot()
        if element not in self._entries:
            self._entries[element] = set()
        self._entries[element].add(dot)

    def remove(self, element: Any) -> None:
        """
        Remove all currently observed dots for element.
        Concurrent adds on other nodes (with new dots) will survive.
        """
        dots = self._entries.pop(element, set())
        self._tombstones.update(dots)

    def contains(self, element: Any) -> bool:
        dots = self._entries.get(element, set())
        return bool(dots - self._tombstones)

    def value(self) -> set:
        """Return the current set of live elements."""
        return {
            elem for elem, dots in self._entries.items()
            if dots - self._tombstones
        }

    def merge(self, remote: "ORSet") -> None:
        """Merge a remote ORSet into self. Idempotent."""
        # Merge entries
        all_elements = set(self._entries.keys()) | set(remote._entries.keys())
        for elem in all_elements:
            local_dots = self._entries.get(elem, set())
            remote_dots = remote._entries.get(elem, set())
            merged_dots = local_dots | remote_dots
            if merged_dots:
                self._entries[elem] = merged_dots
        # Merge tombstones
        self._tombstones.update(remote._tombstones)
        # Update counter to avoid future dot collisions
        if remote._counter > self._counter:
            self._counter = remote._counter

    def merge_dict(self, state_dict: dict) -> None:
        """
        Merge a serialised ORSet payload (from gossip).
        state_dict format:
          {
            "entries": {"elem_key": [[node_id, counter], ...]},
            "tombstones": [[node_id, counter], ...],
            "max_counter": int,
          }
        """
        try:
            for elem_key, raw_dots in state_dict.get("entries", {}).items():
                dots: Set[Dot] = {(d[0], int(d[1])) for d in raw_dots}
                if elem_key not in self._entries:
                    self._entries[elem_key] = set()
                self._entries[elem_key].update(dots)
            for raw_dot in state_dict.get("tombstones", []):
                self._tombstones.add((raw_dot[0], int(raw_dot[1])))
            remote_counter = int(state_dict.get("max_counter", 0))
            if remote_counter > self._counter:
                self._counter = remote_counter
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            logger.warning("[ORSet] Merge failed: %s", exc)

    def to_dict(self) -> dict:
        return {
            "entries": {
                elem: list(dots)
                for elem, dots in self._entries.items()
            },
            "tombstones": list(self._tombstones),
            "max_counter": self._counter,
        }

    def __len__(self) -> int:
        return len(self.value())


# ---------------------------------------------------------------------------
# CRDTStateEngine
# ---------------------------------------------------------------------------

class CRDTStateEngine:
    """
    Composite CRDT state engine for MotherThread shared state.

    Exposes:
      • An LWWRegister for collective field scalars
        (phi, noosphere_stage, element distribution …)
      • An ORSet for the live Gaian node registry
        (node_ids only — no slugs, no names)

    Designed to receive gossip payloads from P2PMesh and merge them
    without coordination or leader election.

    Canon: C04 (privacy), C43 (epistemic), C47 (sovereign)
    """

    GOSSIP_TOPIC = "crdt_state_sync"

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        self.register = LWWRegister(node_id)
        self.node_set = ORSet(node_id)

    # ------------------------------------------------------------------
    # LWW Register helpers
    # ------------------------------------------------------------------

    def set_field(self, key: str, value: Any, timestamp: Optional[float] = None) -> None:
        """Write a collective field value."""
        self.register.set(key, value, timestamp=timestamp)

    def get_field(self, key: str, default: Any = None) -> Any:
        return self.register.get(key, default=default)

    # ------------------------------------------------------------------
    # OR-Set helpers (node registry)
    # ------------------------------------------------------------------

    def join_node(self, node_id: str) -> None:
        """Register a node_id as live in the shared set."""
        self.node_set.add(node_id)

    def leave_node(self, node_id: str) -> None:
        """Remove a node_id from the shared set."""
        self.node_set.remove(node_id)

    def live_nodes(self) -> set:
        return self.node_set.value()

    # ------------------------------------------------------------------
    # Merge (from gossip)
    # ------------------------------------------------------------------

    def merge_gossip(self, payload: dict) -> None:
        """
        Merge a gossip payload received from a remote peer.
        Payload format:
          {
            "register": { <LWWRegister.to_dict()> },
            "node_set": { <ORSet.to_dict()> },
          }
        """
        if "register" in payload:
            self.register.merge_dict(payload["register"])
        if "node_set" in payload:
            self.node_set.merge_dict(payload["node_set"])

    def to_gossip_payload(self) -> dict:
        """Serialise full state for gossip broadcast."""
        return {
            "register": self.register.to_dict(),
            "node_set": self.node_set.to_dict(),
        }

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_status(self) -> dict:
        return {
            "node_id": self.node_id,
            "register_keys": list(self.register.keys()),
            "register_size": len(self.register),
            "live_node_count": len(self.node_set),
            "live_nodes": list(self.live_nodes()),
            "privacy_note": (
                "Register keys are collective field metrics only. "
                "No Gaian slugs or names stored. Canon C04."
            ),
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_crdt_instance: Optional[CRDTStateEngine] = None


def get_crdt_engine(node_id: Optional[str] = None) -> CRDTStateEngine:
    """Return the module-level CRDTStateEngine singleton."""
    global _crdt_instance
    if _crdt_instance is None:
        import uuid as _uuid
        _crdt_instance = CRDTStateEngine(node_id=node_id or str(_uuid.uuid4()))
    return _crdt_instance
