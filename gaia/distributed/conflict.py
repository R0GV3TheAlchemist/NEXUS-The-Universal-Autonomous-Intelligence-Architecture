"""
Conflict resolution for distributed GAIA nodes.
"""
from __future__ import annotations

from typing import Dict, List, Optional


class ConflictResolver:
    """Resolves conflicting knowledge claims across federated nodes."""

    def resolve(
        self,
        claim_id: str,
        views: List[Dict]
    ) -> Optional[Dict]:
        statuses = [v["entry"].get("status", "unknown") for v in views]
        unique_statuses = set(statuses)

        if len(unique_statuses) == 1:
            # All nodes agree
            return views[0]["entry"]

        # Majority vote
        status_counts: Dict[str, int] = {}
        for s in statuses:
            status_counts[s] = status_counts.get(s, 0) + 1

        majority_status = max(status_counts, key=status_counts.get)  # type: ignore[arg-type]
        majority_count = status_counts[majority_status]

        if majority_count > len(views) / 2:
            for v in views:
                if v["entry"].get("status") == majority_status:
                    return v["entry"]

        # No majority — return None to signal unresolved conflict
        return None
