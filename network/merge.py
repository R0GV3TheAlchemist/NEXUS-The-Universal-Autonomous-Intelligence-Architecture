"""
GAIA Network Merge
Combines all node state snapshots into a unified multi-perspective view.
"""

from typing import Dict, List


def merge_states(node_states: Dict[str, Dict]) -> Dict[str, List[Dict]]:
    """
    Merge all node perspectives into: {claim_id: [perspective, ...]}
    Does NOT resolve conflicts — that's consensus.py's job.
    """
    merged: Dict[str, List[Dict]] = {}
    for node_id, snapshot in node_states.items():
        trust = snapshot.get("trust", 1.0)
        for claim_id, entry in snapshot.get("state", {}).items():
            merged.setdefault(claim_id, []).append({
                "node_id": node_id,
                "trust":   trust,
                "entry":   entry
            })
    return merged
