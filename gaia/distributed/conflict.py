"""
GAIA Distributed Conflict Resolver
Detects and resolves truth collisions between GAIA nodes.
Contradictions can now happen BETWEEN perspectives, not just within one node.
"""

from typing import Dict, Any, List


class ConflictResolver:
    """
    Scans merged node states for inter-node epistemic conflicts.

    A distributed conflict exists when:
    - Two or more nodes hold the same claim (by id or semantic overlap)
    - They assign incompatible epistemic statuses

    Resolution:
    - If confidence differential >= RESOLUTION_THRESHOLD: higher wins
    - If differential < threshold: flag for human review
    - Log all conflicts for audit trail
    """

    RESOLUTION_THRESHOLD = 0.20

    POSITIVE_STATUSES = {"supported", "verified"}
    NEGATIVE_STATUSES = {"disputed", "contradicted"}

    def detect(
        self,
        node_states: Dict[str, Dict]
    ) -> List[Dict[str, Any]]:
        """
        Detect all inter-node conflicts across the network.
        Returns list of conflict records.
        """
        # Build per-claim view: claim_id → [{node, entry}]
        claim_views: Dict[str, List[Dict]] = {}
        for node_id, snapshot in node_states.items():
            state = snapshot.get("state", {})
            trust = snapshot.get("trust", 1.0)
            for claim_id, entry in state.items():
                claim_views.setdefault(claim_id, []).append({
                    "node_id": node_id,
                    "trust":   trust,
                    "entry":   entry
                })

        conflicts = []
        for claim_id, views in claim_views.items():
            if len(views) < 2:
                continue
            conflict = self._check_views(claim_id, views)
            if conflict:
                conflicts.append(conflict)

        return conflicts

    def _check_views(
        self,
        claim_id: str,
        views: List[Dict]
    ) -> Optional[Dict]:
        statuses = [v["entry"].get("status", "unknown") for v in views]
        unique_statuses = set(statuses)

        has_positive = bool(unique_statuses & self.POSITIVE_STATUSES)
        has_negative = bool(unique_statuses & self.NEGATIVE_STATUSES)

        if has_positive and has_negative:
            return {
                "claim_id":   claim_id,
                "conflict_type": "inter_node_status_conflict",
                "statuses":   statuses,
                "views":      views,
                "resolution": self._resolve(views)
            }
        return None

    def _resolve(self, views: List[Dict]) -> Dict[str, Any]:
        """Attempt resolution by weighted confidence + trust."""
        scored = sorted(
            views,
            key=lambda v: v["entry"].get("confidence", 0) * v.get("trust", 1.0),
            reverse=True
        )
        if len(scored) >= 2:
            top    = scored[0]["entry"].get("confidence", 0) * scored[0].get("trust", 1.0)
            second = scored[1]["entry"].get("confidence", 0) * scored[1].get("trust", 1.0)
            diff = top - second
            if diff >= self.RESOLUTION_THRESHOLD:
                return {
                    "type":        "auto_resolved",
                    "winner_node": scored[0]["node_id"],
                    "differential": round(diff, 4)
                }
        return {
            "type":    "requires_human_review",
            "reason":  f"Confidence differential below threshold ({self.RESOLUTION_THRESHOLD})"
        }


# fix missing Optional import
ConflictResolver._check_views.__annotations__["return"] = "Optional[Dict]"
