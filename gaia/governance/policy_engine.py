"""
GAIA Policy Engine
The COEXISTENCE_LAWS and GAIAN_LAWS encoded as executable constraints.
Governance is not above the system. Governance IS the system.
"""

from typing import Dict, Any
from ..epistemics.claim import Claim


# COEXISTENCE_LAWS as executable policy
# Source: COEXISTENCE_LAWS.md
COEXISTENCE_LAWS = {
    "CL1": "Substrate neutrality — GAIA does not privilege any substrate, model, or modality",
    "CL2": "Anti-domination — No agent may dominate the world model or override consent",
    "CL3": "Transparency — All reasoning must be traceable",
    "CL4": "Informed consent — Sovereign entities control their own data and participation",
    "CL5": "Do no harm — No action that degrades coherence or harms living systems",
}

# GAIAN_LAWS as executable policy
# Source: GAIAN_LAWS.md
GAIAN_LAWS = {
    "L1": "Coherence primacy — The world model must maintain internal coherence",
    "L2": "Evidence primacy — No claim enters the world model without evidence",
    "L3": "Temporal integrity — Truth states are versioned, never silently overwritten",
    "L4": "Contradiction transparency — Disputes are explicit, never hidden",
    "L5": "Biophotonic priority — Living system coherence takes precedence",
}


class PolicyEngine:
    """
    Evaluates proposed actions and claims against COEXISTENCE_LAWS
    and GAIAN_LAWS before they are executed or ingested.

    This is governance BELOW the model — not a post-hoc filter
    but a pre-execution constraint layer.
    """

    def check_claim(
        self,
        claim: Claim
    ) -> Dict[str, Any]:
        """
        Check whether a claim can be ingested under GAIAN_LAWS.
        Returns: {"permitted": bool, "violations": list, "notes": str}
        """
        violations = []

        # L2: Evidence primacy — every claim must have a source
        if not claim.source or claim.source.strip() == "":
            violations.append(("L2", "Claim has no source — evidence primacy violated"))

        # L2: Source confidence must be non-zero
        if claim.source_confidence <= 0.0:
            violations.append(("L2", "Source confidence is zero — claim is unsourced"))

        # CL4: Consent — claims about persons must carry consent flag (v0.2+)
        # Placeholder for future consent architecture

        permitted = len(violations) == 0
        return {
            "permitted": permitted,
            "violations": violations,
            "notes": "Policy check passed" if permitted else f"{len(violations)} violation(s) found"
        }

    def check_action(
        self,
        action: Dict[str, Any],
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Check whether a proposed agent action is permitted.
        CL2: No agent may dominate the world model.
        """
        violations = []

        # CL2: Agents cannot directly mutate world state — must go through ingest cycle
        if action.get("type") == "direct_world_model_write":
            violations.append(
                ("CL2", f"Agent {agent_id} attempted direct world model write — not permitted")
            )

        permitted = len(violations) == 0
        return {
            "permitted": permitted,
            "agent_id": agent_id,
            "violations": violations,
            "notes": "Action permitted" if permitted else f"Action blocked: {violations[0][1]}"
        }
