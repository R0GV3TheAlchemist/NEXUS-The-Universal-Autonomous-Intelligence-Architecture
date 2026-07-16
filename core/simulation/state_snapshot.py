"""
core/simulation/state_snapshot.py

StateSnapshot — deterministic capture and comparison of simulation state.

Supports:
  - Capturing a full deep-copy snapshot at any step
  - Computing a canonical SHA-256 hash of the state
  - Diffing two snapshots to surface changes
  - Serialisation to/from JSON
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class StateSnapshot:
    """
    An immutable record of all agent states at a given simulation step.

    Attributes:
        step:       Simulation step index when the snapshot was taken
        state:      Deep-copy of the full state dict {agent_id: state_dict}
        hash:       SHA-256 fingerprint of the canonical JSON representation
        timestamp:  UTC ISO-8601 string of when the snapshot was created
    """

    step: int
    state: Dict[str, Any]
    hash: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def capture(cls, step: int, state: Dict[str, Any]) -> "StateSnapshot":
        """Create a snapshot from a live state dict."""
        frozen = copy.deepcopy(state)
        canonical = json.dumps(frozen, sort_keys=True, default=str)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return cls(step=step, state=frozen, hash=digest)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "hash": self.hash,
            "timestamp": self.timestamp,
            "state": self.state,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateSnapshot":
        return cls(
            step=data["step"],
            state=data["state"],
            hash=data["hash"],
            timestamp=data.get("timestamp", ""),
        )

    @classmethod
    def from_json(cls, raw: str) -> "StateSnapshot":
        return cls.from_dict(json.loads(raw))


@dataclass
class SnapshotDiff:
    """
    The delta between two StateSnapshots.

    Attributes:
        step_a, step_b: The step indices of the compared snapshots
        added:    Keys present in b but not in a
        removed:  Keys present in a but not in b
        changed:  Keys whose values differ between a and b
        identical: True if both snapshots have the same hash
    """

    step_a: int
    step_b: int
    added: List[str]
    removed: List[str]
    changed: List[Tuple[str, Any, Any]]  # (key, value_a, value_b)
    identical: bool

    @classmethod
    def compute(cls, snap_a: StateSnapshot, snap_b: StateSnapshot) -> "SnapshotDiff":
        """Compute the diff between two snapshots."""
        if snap_a.hash == snap_b.hash:
            return cls(
                step_a=snap_a.step,
                step_b=snap_b.step,
                added=[],
                removed=[],
                changed=[],
                identical=True,
            )

        keys_a = set(snap_a.state.keys())
        keys_b = set(snap_b.state.keys())

        added = sorted(keys_b - keys_a)
        removed = sorted(keys_a - keys_b)
        changed = []

        for key in keys_a & keys_b:
            if snap_a.state[key] != snap_b.state[key]:
                changed.append((key, snap_a.state[key], snap_b.state[key]))

        return cls(
            step_a=snap_a.step,
            step_b=snap_b.step,
            added=added,
            removed=removed,
            changed=sorted(changed, key=lambda x: x[0]),
            identical=False,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_a": self.step_a,
            "step_b": self.step_b,
            "identical": self.identical,
            "added": self.added,
            "removed": self.removed,
            "changed": [{"key": k, "before": a, "after": b} for k, a, b in self.changed],
        }
