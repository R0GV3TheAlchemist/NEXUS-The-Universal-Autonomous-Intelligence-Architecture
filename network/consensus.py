"""
GAIA Network Consensus Engine — v0.6 (Trust-Weighted)
Forms global truth from merged node perspectives,
weighted by each node's dynamic trust score.

Upgrade from v0.5:
  v0.5: weight = confidence only
  v0.6: weight = confidence × trust_score  ← THIS VERSION
  v0.7: weight = Bayesian posterior
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from node.trust import TrustProfile

CONFLICT_THRESHOLD = 0.15  # flag if top-2 weighted scores are within this gap


def resolve(
    node_states: Dict[str, Dict],
    trust_profiles: Optional[Dict[str, "TrustProfile"]] = None
) -> Dict[str, Any]:
    """
    Trust-weighted consensus resolution.
    If trust_profiles is None, falls back to equal weighting (v0.5 behaviour).
    Returns {claim_id: winning_entry_with_provenance}.
    """
    per_claim: Dict[str, List[Dict]] = {}

    for node_id, snapshot in node_states.items():
        trust = 1.0
        if trust_profiles and node_id in trust_profiles:
            trust = trust_profiles[node_id].score
        elif isinstance(snapshot, dict):
            trust = snapshot.get("trust", 1.0)

        state = snapshot.get("state", snapshot)
        for claim_id, entry in state.items():
            if not isinstance(entry, dict):
                continue
            per_claim.setdefault(claim_id, []).append({
                "node_id": node_id,
                "trust":   trust,
                "entry":   entry,
                "weight":  round(entry.get("confidence", 0.5) * trust, 4)
            })

    consensus: Dict[str, Any] = {}
    conflicts: List[Dict] = []

    for claim_id, perspectives in per_claim.items():
        sorted_p = sorted(perspectives, key=lambda x: x["weight"], reverse=True)
        winner = sorted_p[0]

        # Detect close contests
        if len(sorted_p) >= 2:
            gap = sorted_p[0]["weight"] - sorted_p[1]["weight"]
            if gap < CONFLICT_THRESHOLD:
                conflicts.append({
                    "claim_id":  claim_id,
                    "gap":       round(gap, 4),
                    "top_nodes": [p["node_id"] for p in sorted_p[:2]]
                })

        consensus[claim_id] = {
            **winner["entry"],
            "consensus_source":   winner["node_id"],
            "consensus_weight":   winner["weight"],
            "consensus_method":   "trust_weighted_v0.6",
            "perspective_count":  len(perspectives)
        }

    return {"consensus": consensus, "close_contests": conflicts}


def agreement_level(node_states: Dict[str, Dict]) -> Dict[str, Any]:
    """Fraction of shared claims with unanimous status across nodes."""
    per_claim: Dict[str, List[str]] = {}
    for snapshot in node_states.values():
        state = snapshot.get("state", snapshot)
        for claim_id, entry in state.items():
            if isinstance(entry, dict):
                per_claim.setdefault(claim_id, []).append(
                    entry.get("status", "unknown")
                )
    shared    = {k: v for k, v in per_claim.items() if len(v) > 1}
    unanimous = sum(1 for v in shared.values() if len(set(v)) == 1)
    total     = len(shared)
    return {
        "total_shared":  total,
        "unanimous":     unanimous,
        "agreement_pct": round(unanimous / total, 4) if total > 0 else 1.0
    }
