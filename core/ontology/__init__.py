"""GAIA Ontology Runtime — the World Fabric.

Canon References: C03 (Ontology and Runtime Model), C14 (OS and World Fabric Spec)

This package is the semantic foundation of GAIA-OS.
Every module that creates, relates, or transitions entities must import from here.
Where any other module conflicts with C03 definitions, C03 governs.
"""
from .entities import (
    EntityType,
    AlchemicalStage,
    PermissionTier,
    Entity,
    GAIAEntity,
    GaianEntity,
    HumanPrincipalEntity,
    ATLASNodeEntity,
)
from .relationships import RelationshipType, Relationship, RelationshipGraph
from .state_machine import AlchemicalStateMachine, StateTransitionError
from .permissions import PermissionEnvelope, AuditTrail, AuditEntry, PermissionDeniedError, Capability
from .runtime import GAIARuntime, OntologicalConstraintError
from .gaia_mode import GAIAMode          # Fix 3 — D6 engine
from .registry import GAIANRegistry      # Fix 4 — boot phase tests

__all__ = [
    "EntityType",
    "AlchemicalStage",
    "PermissionTier",
    "Entity",
    "GAIAEntity",
    "GaianEntity",
    "HumanPrincipalEntity",
    "ATLASNodeEntity",
    "RelationshipType",
    "Relationship",
    "RelationshipGraph",
    "AlchemicalStateMachine",
    "StateTransitionError",
    "PermissionEnvelope",
    "AuditTrail",
    "AuditEntry",
    "PermissionDeniedError",
    "Capability",
    "GAIARuntime",
    "OntologicalConstraintError",
    "GAIAMode",        # Fix 3
    "GAIANRegistry",   # Fix 4
]
