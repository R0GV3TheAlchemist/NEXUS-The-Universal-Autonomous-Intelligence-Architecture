"""
GAIA World State — Temporal-Aware (v0.3)
The living, versioned world model.
Every update creates a new snapshot. No truth is silently overwritten.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .temporal import TemporalEngine, WorldSnapshot


class WorldState:
    """
    The central runtime world model of GAIA.

    v0.1: dict of claims
    v0.2: dict + query interface
    v0.3: dict + full temporal versioning via TemporalEngine  ← THIS VERSION

    Every call to update() does three things:
      1. Updates the current state
      2. Commits a new WorldSnapshot (immutable, timestamped)
      3. Logs to history

    The world model is now an evolving reality graph,
    not just a memory store.
    """

    def __init__(self):
        self._state: Dict[str, Any] = {}
        self._temporal = TemporalEngine()
        self._update_count: int = 0

    # ——— Write ———

    def update(
        self,
        evaluation_result: Dict[str, Any],
        trigger: Optional[str] = None
    ) -> WorldSnapshot:
        """
        Receive an evaluated claim, update world state,
        and commit a new temporal snapshot.
        Returns the committed snapshot.
        """
        claim = evaluation_result["claim"]
        entry = {
            "id":                claim.id,
            "statement":         claim.statement,
            "sources":           getattr(claim, 'sources', []),
            "domain":            getattr(claim, 'domain', None),
            "entities":          getattr(claim, 'entities', []),
            "confidence":        evaluation_result["confidence"],
            "status":            evaluation_result["status"],
            "contradiction_count": len(evaluation_result.get("contradictions", [])),
            "supporting_count":  len(evaluation_result.get("supporting", [])),
            "updated_at":        datetime.utcnow().isoformat(),
        }

        self._state[claim.id] = entry
        self._update_count += 1

        # Commit temporal snapshot — every update is versioned
        snapshot = self._temporal.commit(
            self._state,
            trigger=trigger or claim.id
        )
        return snapshot

    # ——— Current state queries ———

    def query(
        self,
        keyword: str,
        min_confidence: float = 0.0
    ) -> List[Dict]:
        """Search current world state by keyword."""
        kw = keyword.lower()
        results = [
            e for e in self._state.values()
            if kw in e["statement"].lower()
            and e["confidence"] >= min_confidence
        ]
        return sorted(results, key=lambda x: x["confidence"], reverse=True)

    def disputed(self) -> List[Dict]:
        return [e for e in self._state.values() if e["status"] == "disputed"]

    def snapshot(self) -> Dict[str, Any]:
        """Full current world state snapshot."""
        return {
            "snapshot_at":    datetime.utcnow().isoformat(),
            "total_entries":  len(self._state),
            "update_count":   self._update_count,
            "temporal_stats": self._temporal.stats(),
            "state":          dict(self._state)
        }

    def stats(self) -> Dict[str, Any]:
        status_counts: Dict[str, int] = {}
        for e in self._state.values():
            s = e["status"]
            status_counts[s] = status_counts.get(s, 0) + 1
        confs = [e["confidence"] for e in self._state.values()]
        return {
            "total":              len(self._state),
            "update_count":       self._update_count,
            "status_breakdown":   status_counts,
            "avg_confidence":     round(sum(confs)/len(confs), 4) if confs else 0.0,
            "disputed":           status_counts.get("disputed", 0),
            "verified":           status_counts.get("verified", 0),
            "temporal_snapshots": self._temporal.stats()["total_snapshots"],
        }

    # ——— Temporal queries ———

    @property
    def temporal(self) -> TemporalEngine:
        """Direct access to the temporal engine for advanced queries."""
        return self._temporal

    def at_time(self, timestamp: datetime) -> Optional[WorldSnapshot]:
        """What did GAIA believe at time T?"""
        return self._temporal.get_at_time(timestamp)

    def timeline(self) -> List[Dict]:
        """Human-readable timeline of all world state snapshots."""
        return self._temporal.timeline_summary()

    def belief_drift(self, claim_id: str) -> List[Dict]:
        """How has a specific claim's confidence evolved over time?"""
        return self._temporal.belief_drift(claim_id)

    def temporal_contradictions(self) -> List[Dict]:
        """Claims that have flipped epistemic status over time."""
        return self._temporal.detect_temporal_contradictions()

    def __repr__(self) -> str:
        snaps = self._temporal.stats()["total_snapshots"]
        return (
            f"WorldState(claims={len(self._state)}, "
            f"updates={self._update_count}, "
            f"snapshots={snaps}, "
            f"disputed={len(self.disputed())})"
        )
