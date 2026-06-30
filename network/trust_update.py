"""
GAIA Trust Update Engine — v0.6
Applies adversarial validation results to node trust profiles.

This is the feedback loop that makes GAIA self-correcting:
  - Network validates a claim
  - Result is applied to the submitting node's trust score
  - Over time: reliable nodes gain influence, unreliable nodes lose it
  - Consensus becomes credibility-weighted, not democratically averaged

Update rules (v0.6 heuristic):
  network_supported  → submitting node: +accept
  network_rejected   → submitting node: +reject
  network_contested  → submitting node: +dispute (all participants)

v0.7 upgrade: replace with Bayesian posterior update
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from node.trust import TrustProfile
    from network.adversary import ValidationResult


def update_from_validation(
    submitting_node_id: str,
    validation_result: "ValidationResult",
    trust_profiles: Dict[str, "TrustProfile"]
) -> Dict[str, Any]:
    """
    Apply a ValidationResult to the submitting node's trust profile.
    Returns a summary of the trust update applied.
    """
    profile = trust_profiles.get(submitting_node_id)
    if not profile:
        return {"error": f"No trust profile for node {submitting_node_id}"}

    verdict = validation_result.verdict
    claim_id = validation_result.claim_id
    prev_score = profile.score

    if verdict == "network_supported":
        new_score = profile.update_on_accept(claim_id)
        action = "accepted"
    elif verdict == "network_rejected":
        new_score = profile.update_on_reject(claim_id)
        action = "rejected"
    else:  # network_contested or no_data
        new_score = profile.update_on_dispute(claim_id)
        action = "disputed"

    return {
        "node_id":    submitting_node_id,
        "claim_id":   claim_id,
        "verdict":    verdict,
        "action":     action,
        "prev_score": prev_score,
        "new_score":  new_score,
        "delta":      round(new_score - prev_score, 4),
        "new_tier":   profile.tier()
    }


def batch_update(
    validation_results: List["ValidationResult"],
    trust_profiles: Dict[str, "TrustProfile"],
    node_state_snapshots: Optional[Dict[str, Dict]] = None
) -> List[Dict[str, Any]]:
    """
    Apply a batch of validation results.
    Uses node_opinions within each ValidationResult to identify
    which node submitted each claim (if available).
    Returns list of trust update summaries.
    """
    updates = []
    for result in validation_results:
        # Identify submitting node from opinions
        # In v0.6: apply to all nodes that had strong opinions
        for opinion_entry in result.node_opinions:
            node_id = opinion_entry.get("node_id")
            opinion = opinion_entry.get("opinion")
            profile = trust_profiles.get(node_id)
            if not profile:
                continue

            prev = profile.score
            if opinion == "support" and result.verdict == "network_supported":
                new = profile.update_on_accept(result.claim_id)
                action = "accepted"
            elif opinion == "reject" and result.verdict == "network_rejected":
                new = profile.update_on_accept(result.claim_id)  # correct prediction
                action = "correct_rejection"
            elif result.verdict == "network_contested":
                new = profile.update_on_dispute(result.claim_id)
                action = "disputed"
            else:
                continue

            updates.append({
                "node_id":  node_id,
                "claim_id": result.claim_id,
                "opinion":  opinion,
                "verdict":  result.verdict,
                "action":   action,
                "delta":    round(new - prev, 4),
                "new_score": new,
                "new_tier": profile.tier()
            })
    return updates


def trust_leaderboard(
    trust_profiles: Dict[str, "TrustProfile"]
) -> List[Dict[str, Any]]:
    """
    Ranked list of all nodes by trust score.
    Useful for monitoring network health.
    """
    return sorted(
        [p.summary() for p in trust_profiles.values()],
        key=lambda x: x["score"],
        reverse=True
    )
