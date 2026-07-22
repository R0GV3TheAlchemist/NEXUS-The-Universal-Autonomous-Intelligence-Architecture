"""twins

NEXUS Digital Twin Coordination Layer

Manages GAIA's digital twin descriptors, synchronisation plans,
and consent gates. Provides the foundation for the DIGITALTWINS.md
documentation and consent-provenance architecture.

Architecture reference:
    NEXUS_UNIVERSAL_OS.md  Domain 6.1 - Digital Twins
    DIGITALTWINS.md        (to be authored in Phase D)
Research reference:
    Azure Digital Twins    - twin graph and model specs
    Eclipse Ditto          - state/sync model
    W3C Web of Things      - consent and provenance framework
"""
from __future__ import annotations

from twins.engine import (
    TwinSpec,
    TwinState,
    SyncPlan,
    TwinConsent,
    TwinOrchestrator,
)

__all__ = ["TwinSpec", "TwinState", "SyncPlan", "TwinConsent", "TwinOrchestrator"]
