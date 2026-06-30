"""
GAIA Temporal Engine — v0.3
The layer that makes GAIA an evolving reality model, not just a memory system.

Before: GAIA = static world state
After:  GAIA = versioned history of reality snapshots

Every world update creates a new snapshot.
Every snapshot is a frozen, queryable version of reality at a moment in time.
This enables:
  - Time-based contradiction resolution (true at T1, false at T2 = no conflict)
  - State replay (what did GAIA believe at time X?)
  - Belief drift detection (how has confidence changed over time?)
  - Causality grounded in time (event ordering)
"""

import copy
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorldSnapshot(BaseModel):
    """
    A frozen, immutable version of the GAIA world state at a moment in time.
    The atomic unit of temporal versioning.

    In the 'Git for reality' metaphor:
      snapshot = commit
      snapshot.state = the full repo state at that commit
      snapshot.timestamp = commit timestamp
      snapshot.trigger = commit message
    """
    id: str = Field(default_factory=lambda: f"snap_{str(uuid.uuid4())[:8]}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    state: Dict[str, Any] = {}        # frozen world state at this moment
    trigger: Optional[str] = None     # what caused this snapshot (claim id, event, etc.)
    claim_count: int = 0
    verified_count: int = 0
    disputed_count: int = 0
    avg_confidence: float = 0.0

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def diff_summary(self, previous: "WorldSnapshot") -> Dict[str, Any]:
        """
        Compute what changed between this snapshot and a previous one.
        Returns new entries, removed entries, and confidence shifts.
        """
        prev_ids = set(previous.state.keys())
        curr_ids = set(self.state.keys())

        new_entries = curr_ids - prev_ids
        removed_entries = prev_ids - curr_ids

        confidence_shifts = []
        for cid in curr_ids & prev_ids:
            prev_conf = previous.state[cid].get("confidence", 0)
            curr_conf = self.state[cid].get("confidence", 0)
            delta = round(curr_conf - prev_conf, 4)
            if abs(delta) > 0.01:
                confidence_shifts.append({
                    "claim_id": cid,
                    "statement": self.state[cid].get("statement", "")[:60],
                    "prev_confidence": prev_conf,
                    "curr_confidence": curr_conf,
                    "delta": delta
                })

        return {
            "new_entries":       list(new_entries),
            "removed_entries":   list(removed_entries),
            "confidence_shifts": confidence_shifts,
            "claim_delta":       len(curr_ids) - len(prev_ids)
        }

    def __repr__(self) -> str:
        return (
            f"WorldSnapshot(id={self.id}, "
            f"t={self.timestamp.strftime('%H:%M:%S')}, "
            f"claims={self.claim_count}, "
            f"avg_conf={self.avg_confidence:.3f})"
        )


class TemporalEngine:
    """
    The Temporal Engine maintains the full history of GAIA's world states.

    Every call to commit() creates a new immutable WorldSnapshot.
    The history is append-only — truth states are never silently overwritten.
    (GAIAN_LAW L3: Temporal integrity)

    Query interface:
      - get_at_time(t)     → closest snapshot before time t
      - diff(snap_a, snap_b) → what changed between two moments
      - belief_drift(claim_id) → how a claim's confidence evolved
      - detect_temporal_contradictions() → claims that flipped status over time
    """

    def __init__(self):
        self._snapshots: List[WorldSnapshot] = []
        self._snapshot_index: Dict[str, WorldSnapshot] = {}  # id → snapshot

    # ——— Write ———

    def commit(
        self,
        world_state: Dict[str, Any],
        trigger: Optional[str] = None
    ) -> WorldSnapshot:
        """
        Create a new versioned snapshot of the current world state.
        This is a 'git commit' for reality.
        """
        frozen = copy.deepcopy(world_state)

        # Compute snapshot stats
        confidences = [v.get("confidence", 0) for v in frozen.values()]
        statuses = [v.get("status", "unknown") for v in frozen.values()]

        snapshot = WorldSnapshot(
            state=frozen,
            trigger=trigger,
            claim_count=len(frozen),
            verified_count=statuses.count("verified"),
            disputed_count=statuses.count("disputed"),
            avg_confidence=round(sum(confidences)/len(confidences), 4)
                           if confidences else 0.0
        )

        self._snapshots.append(snapshot)
        self._snapshot_index[snapshot.id] = snapshot
        return snapshot

    # ——— Query ———

    def get_at_time(self, timestamp: datetime) -> Optional[WorldSnapshot]:
        """
        Retrieve the closest world state snapshot at or before `timestamp`.
        'What did GAIA believe at time T?'
        """
        valid = [
            s for s in self._snapshots
            if s.timestamp <= timestamp
        ]
        return valid[-1] if valid else None

    def get_latest(self) -> Optional[WorldSnapshot]:
        """Return the most recent snapshot."""
        return self._snapshots[-1] if self._snapshots else None

    def get_by_id(self, snapshot_id: str) -> Optional[WorldSnapshot]:
        return self._snapshot_index.get(snapshot_id)

    def history(self) -> List[WorldSnapshot]:
        """Full ordered snapshot history."""
        return list(self._snapshots)

    # ——— Analysis ———

    def diff(
        self,
        snap_a: WorldSnapshot,
        snap_b: WorldSnapshot
    ) -> Dict[str, Any]:
        """What changed between two snapshots?"""
        return snap_b.diff_summary(snap_a)

    def belief_drift(
        self,
        claim_id: str
    ) -> List[Dict[str, Any]]:
        """
        How has a specific claim's confidence evolved over all snapshots?
        Returns ordered list of {snapshot_id, timestamp, confidence, status}.
        """
        drift = []
        for snap in self._snapshots:
            if claim_id in snap.state:
                entry = snap.state[claim_id]
                drift.append({
                    "snapshot_id": snap.id,
                    "timestamp":   snap.timestamp.isoformat(),
                    "confidence":  entry.get("confidence", 0),
                    "status":      entry.get("status", "unknown")
                })
        return drift

    def detect_temporal_contradictions(self) -> List[Dict[str, Any]]:
        """
        Detect claims that flipped between positive and negative status over time.
        'Was true at T1, false at T2' = temporal state change, NOT a contradiction.
        'Was supported at T1, contradicted at T1' = true contradiction.

        Returns list of claims that have undergone status transitions.
        """
        positive = {"supported", "verified"}
        negative = {"disputed", "contradicted"}

        # Track each claim's status history
        claim_status_history: Dict[str, List[str]] = {}
        for snap in self._snapshots:
            for cid, entry in snap.state.items():
                claim_status_history.setdefault(cid, []).append(
                    entry.get("status", "unknown")
                )

        transitions = []
        for cid, statuses in claim_status_history.items():
            # Find status flips
            flips = []
            for i in range(1, len(statuses)):
                prev, curr = statuses[i-1], statuses[i]
                if (
                    (prev in positive and curr in negative) or
                    (prev in negative and curr in positive)
                ):
                    flips.append({"from": prev, "to": curr, "at_index": i})

            if flips:
                # Get statement from latest snapshot containing this claim
                statement = ""
                for snap in reversed(self._snapshots):
                    if cid in snap.state:
                        statement = snap.state[cid].get("statement", "")[:80]
                        break

                transitions.append({
                    "claim_id":   cid,
                    "statement":  statement,
                    "flips":      flips,
                    "total_snapshots_present": len(statuses)
                })

        return transitions

    def timeline_summary(self) -> List[Dict[str, Any]]:
        """Human-readable summary of the full snapshot timeline."""
        return [
            {
                "index":          i,
                "snapshot_id":    s.id,
                "timestamp":      s.timestamp.isoformat(),
                "claims":         s.claim_count,
                "avg_confidence": s.avg_confidence,
                "disputed":       s.disputed_count,
                "trigger":        s.trigger or "manual"
            }
            for i, s in enumerate(self._snapshots)
        ]

    def stats(self) -> Dict[str, Any]:
        return {
            "total_snapshots":   len(self._snapshots),
            "latest_snapshot":   self._snapshots[-1].id if self._snapshots else None,
            "latest_timestamp":  self._snapshots[-1].timestamp.isoformat()
                                 if self._snapshots else None,
            "latest_claim_count": self._snapshots[-1].claim_count
                                  if self._snapshots else 0,
        }

    def __repr__(self) -> str:
        return f"TemporalEngine(snapshots={len(self._snapshots)})"
