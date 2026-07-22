"""governance

NEXUS Governance Engine

Enforces AI governance policies aligned with EU AI Act, NIST AI RMF,
and IEEE Ethically Aligned Design. Evaluates GAIA actions against
declared policies and emits PolicyViolation events.

Architecture reference:
    NEXUS_UNIVERSAL_OS.md  Domain 7 - Governance
    GOVERNANCE.md          - Policy definitions
    GOVERNANCESPEC.md      - Formal governance spec
Research reference:
    EU AI Act              - risk-based AI compliance framework
    NIST AI RMF            - AI Risk Management Framework
    IEEE EAD               - Ethically Aligned Design
"""
from __future__ import annotations

from governance.engine import GovernanceEngine, GovernancePolicy, PolicyViolation, RiskLevel

__all__ = ["GovernanceEngine", "GovernancePolicy", "PolicyViolation", "RiskLevel"]
