"""
GAIA World Model State Manager
The runtime world model — receives evaluated claims and maintains
the current best-supported state of everything GAIA tracks.
"""

from typing import Dict, Any, List
from datetime import datetime
from ..epistemics.claim import Claim


class WorldModelState:
    """
    The WorldModelState is GAIA's living representation of reality.

    It holds the current best-supported state of every entity and claim
    that has been evaluated by the EpistemicEvaluator.

    Key properties:
    - Every entry is evidence-weighted (no raw belief)
    - Every entry is timestamped (temporal versioning)
    - Every entry carries its epistemic status
    - Snapshots can be taken at any point in time
    """

    def __init__(self):
        self._state: Dict[str, Dict[str, Any]] = {}  # claim_id → state entry
        self._history: List[Dict] = []               # ordered list of all updates
        self._created_at = datetime.utcnow()
        self._update_count = 0

    def update(self, evaluation_result: Dict[str, Any]) -> None:
        """
        Receive an evaluated claim and update the world model state.
        Every update is logged to history for full auditability.
        """
        claim: Claim = evaluation_result["claim"]
        entry = {
            "claim_id": claim.id,
            "statement": claim.statement,
            "entity_refs": claim.entity_refs,
            "source": claim.source,
            "confidence": evaluation_result["confidence"],
            "status": evaluation_result["status"],
            "contradiction_count": len(evaluation_result.get("contradictions", [])),
            "supporting_count": len(evaluation_result.get("supporting_claims", [])),
            "domain": claim.domain,
            "timestamp": datetime.utcnow().isoformat(),
            "evaluation_notes": evaluation_result.get("evaluation_notes", "")
        }
        self._state[claim.id] = entry
        self._history.append({"update_index": self._update_count, **entry})
        self._update_count += 1

    def query_best_supported(
        self,
        entity_id: str,
        min_confidence: float = 0.0
    ) -> List[Dict]:
        """
        The primary agent query interface.
        Returns best-supported current state of all claims about an entity,
        sorted by confidence descending.
        """
        results = [
            entry for entry in self._state.values()
            if entity_id in entry.get("entity_refs", [])
            and entry["confidence"] >= min_confidence
        ]
        return sorted(results, key=lambda x: x["confidence"], reverse=True)

    def query_by_status(
        self,
        status: str
    ) -> List[Dict]:
        """Return all claims currently holding a given epistemic status."""
        return [e for e in self._state.values() if e["status"] == status]

    def query_disputed(self) -> List[Dict]:
        """Return all currently disputed claims — the active contradiction register."""
        return self.query_by_status("disputed")

    def snapshot(self) -> Dict[str, Any]:
        """Return a point-in-time snapshot of the full world model state."""
        return {
            "snapshot_timestamp": datetime.utcnow().isoformat(),
            "total_claims": len(self._state),
            "update_count": self._update_count,
            "state": dict(self._state)
        }

    def stats(self) -> Dict[str, Any]:
        """Return summary statistics for the current world model state."""
        status_counts: Dict[str, int] = {}
        for entry in self._state.values():
            s = entry["status"]
            status_counts[s] = status_counts.get(s, 0) + 1

        confidences = [e["confidence"] for e in self._state.values()]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            "total_claims": len(self._state),
            "update_count": self._update_count,
            "status_distribution": status_counts,
            "avg_confidence": round(avg_confidence, 4),
            "disputed_count": status_counts.get("disputed", 0),
            "verified_count": status_counts.get("verified", 0),
        }

    def __repr__(self) -> str:
        return (
            f"WorldModelState(claims={len(self._state)}, "
            f"updates={self._update_count}, "
            f"disputed={len(self.query_disputed())})"
        )
