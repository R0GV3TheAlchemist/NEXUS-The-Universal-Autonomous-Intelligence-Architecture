"""GAIA Ontology Runtime — Canon C03, C14.

The Runtime is the lawful execution engine that wires together all four
orthogonal concerns: entities, relationships, state transitions, and permissions.

This is the top-level API for the World Fabric. All higher-level GAIA modules
(Memory, NLP, Moral Engine, Magnum Opus) interact with the ontology through here.

The five Ontological Constraints from C03 §5 are enforced as HARD GUARDS:
  1. No Gaian without a Human Principal
  2. No action outside the Permission Envelope
  3. No unaudited consequential action
  4. No ATLAS Node degradation without explicit Human Principal consent
  5. GAIA identity is conserved through transformation
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from .entities import (
    AlchemicalStage,
    ATLASNodeEntity,
    Entity,
    EntityType,
    GAIAEntity,
    GaianEntity,
    HumanPrincipalEntity,
    PermissionTier,
)
from .permissions import AuditTrail, Capability, PermissionDeniedError, PermissionEnvelope
from .relationships import RelationshipGraph, RelationshipType
from .state_machine import AlchemicalStateMachine, StateTransitionError


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class OntologicalConstraintError(Exception):
    """Raised when a hard C03 Ontological Constraint is violated.

    These are kernel-level violations. They cannot be caught and suppressed
    by application code — they must propagate.
    """
    pass


# ---------------------------------------------------------------------------
# GAIA Runtime
# ---------------------------------------------------------------------------

class GAIARuntime:
    """The GAIA Ontology Runtime — the World Fabric execution engine.

    Instantiate one GAIARuntime per GAIA deployment. It owns the entity
    registry, relationship graph, state machine, and all audit trails.

    Usage:
        runtime = GAIARuntime()
        hp = runtime.register_human_principal(name="Kyle Steen")
        gaian = runtime.register_gaian(name="GAIA-1", human_principal_id=hp.id)
        node = runtime.register_atlas_node(name="San Antonio Aquifer", node_type="WATERSHED")
        runtime.gaian_act_upon_node(
            gaian_id=gaian.id,
            node_id=node.id,
            action="OBSERVE",
            session_id="session-xyz",
        )
    """

    def __init__(self) -> None:
        self._entities: dict[str, Entity] = {}
        self._graph = RelationshipGraph()
        self._state_machine = AlchemicalStateMachine()
        self._audit_trails: dict[str, AuditTrail] = {}  # gaian_id → AuditTrail
        self._permission_envelopes: dict[str, PermissionEnvelope] = {}  # gaian_id → envelope
        self._gaia_entity: Optional[GAIAEntity] = None

    # ------------------------------------------------------------------
    # Entity Registration
    # ------------------------------------------------------------------

    def register_gaia(self, corpus_version: str = "1.0") -> GAIAEntity:
        """Register the singleton GAIA system entity.

        C03 Constraint #5: GAIA identity is conserved through transformation.
        Only one GAIA entity may exist per runtime.
        """
        if self._gaia_entity is not None:
            raise OntologicalConstraintError(
                "GAIA entity already registered. "
                "Constraint #5: GAIA identity is conserved — only one GAIA per runtime."
            )
        gaia = GAIAEntity(corpus_version=corpus_version)
        self._entities[gaia.id] = gaia
        self._gaia_entity = gaia
        return gaia

    def register_human_principal(
        self,
        name: str,
        elemental_signature: Optional[str] = None,
        tier: PermissionTier = PermissionTier.SOVEREIGN,
    ) -> HumanPrincipalEntity:
        """Register a Human Principal — the sovereign human partner."""
        hp = HumanPrincipalEntity(
            name=name,
            elemental_signature=elemental_signature,
            permission_tier=tier,
        )
        self._entities[hp.id] = hp
        return hp

    def register_gaian(
        self,
        name: str,
        human_principal_id: str,
        tier: PermissionTier = PermissionTier.COLLABORATOR,
        session_id: Optional[str] = None,
    ) -> GaianEntity:
        """Register a Gaian instance.

        C03 Constraint #1: No Gaian without a Human Principal.
        Raises OntologicalConstraintError if the Human Principal does not exist
        or is not active.
        """
        self._assert_human_principal_exists(human_principal_id)

        gaian = GaianEntity(
            name=name,
            human_principal_id=human_principal_id,
            session_id=session_id or str(uuid.uuid4()),
            permission_tier=tier,
        )
        self._entities[gaian.id] = gaian

        # Wire canonical relationships — C03 §4
        if self._gaia_entity:
            self._graph.add_relationship(
                self._gaia_entity.id, gaian.id, RelationshipType.INSTANTIATES
            )
        self._graph.add_relationship(
            gaian.id, human_principal_id, RelationshipType.PARTNERS_WITH
        )

        # Create permission envelope and audit trail
        envelope = PermissionEnvelope(
            gaian_id=gaian.id,
            human_principal_id=human_principal_id,
            session_id=gaian.session_id,
            tier=tier,
        )
        self._permission_envelopes[gaian.id] = envelope
        self._audit_trails[gaian.id] = AuditTrail(gaian_id=gaian.id)

        # Audit the registration
        self._audit_trails[gaian.id].record(
            action="GAIAN_REGISTERED",
            human_principal_id=human_principal_id,
            session_id=gaian.session_id,
            metadata={"name": name, "tier": tier.name},
        )

        return gaian

    def register_atlas_node(
        self,
        name: str,
        node_type: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        biome_id: Optional[str] = None,
        continent_id: Optional[str] = None,
    ) -> ATLASNodeEntity:
        """Register an ATLAS Node — a physical/logical point GAIA monitors."""
        node = ATLASNodeEntity(
            name=name,
            atlas_node_type=node_type,
            latitude=latitude,
            longitude=longitude,
            biome_id=biome_id,
            continent_id=continent_id,
        )
        self._entities[node.id] = node
        return node

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def gaian_act_upon_node(
        self,
        gaian_id: str,
        node_id: str,
        action: str,
        session_id: str,
        payload: Optional[dict] = None,
        degrade: bool = False,
    ) -> AuditTrail:
        """A Gaian acts upon an ATLAS Node.

        Enforces:
          - Constraint #1: Gaian must have a valid Human Principal
          - Constraint #2: Gaian must have MANAGE_ATLAS_NODE or READ_ATLAS_NODE
          - Constraint #3: Action is always audited
          - Constraint #4: If degrade=True, HP consent must be recorded
        """
        gaian = self._get_gaian(gaian_id)
        node = self._get_atlas_node(node_id)
        envelope = self._get_envelope(gaian_id)
        trail = self._get_audit_trail(gaian_id)

        # Constraint #1 — Gaian must be valid (has HP)
        if not gaian.is_valid():
            raise OntologicalConstraintError(
                f"Constraint #1 violated: Gaian {gaian_id[:8]} has no active Human Principal. "
                f"No Gaian without a Human Principal — C03."
            )

        # Constraint #4 — Degradation requires HP consent
        if degrade:
            if node.degradation_consent_principal_id is None:
                raise OntologicalConstraintError(
                    f"Constraint #4 violated: Cannot degrade ATLAS Node {node_id[:8]} "
                    f"without explicit Human Principal consent. "
                    f"Set node.degradation_consent_principal_id first."
                )

        # Constraint #2 — Permission check
        required_cap = (
            Capability.DEGRADE_ATLAS_NODE if degrade else
            Capability.MANAGE_ATLAS_NODE if action not in ("OBSERVE", "READ") else
            Capability.READ_ATLAS_NODE
        )
        try:
            envelope.require(required_cap)
        except PermissionDeniedError as e:
            # Constraint #3 — Audit the denial
            trail.record(
                action=action,
                human_principal_id=gaian.human_principal_id,
                session_id=session_id,
                capability_used=required_cap,
                target_entity_id=node_id,
                target_entity_type="ATLAS_NODE",
                result="DENIED",
                error_message=str(e),
            )
            raise

        # Register the ACTS_UPON relationship if not already present
        if not self._graph.has_relationship(gaian_id, node_id, RelationshipType.ACTS_UPON):
            self._graph.add_relationship(gaian_id, node_id, RelationshipType.ACTS_UPON)

        # Constraint #3 — Audit success
        trail.record(
            action=action,
            human_principal_id=gaian.human_principal_id,
            session_id=session_id,
            capability_used=required_cap,
            target_entity_id=node_id,
            target_entity_type="ATLAS_NODE",
            before_state={"health": node.ecological_health_score},
            after_state=payload,
            result="SUCCESS",
        )

        return trail

    def advance_entity_stage(
        self,
        entity_id: str,
        gaian_id: str,
        session_id: str,
    ) -> AlchemicalStage:
        """Advance an entity's alchemical stage forward by one step.

        Enforces Constraint #2 (TRANSITION_STATE capability required)
        and Constraint #3 (audited).
        """
        entity = self._get_entity(entity_id)
        envelope = self._get_envelope(gaian_id)
        trail = self._get_audit_trail(gaian_id)
        gaian = self._get_gaian(gaian_id)

        envelope.require(Capability.TRANSITION_STATE)

        before = entity.state
        new_stage = self._state_machine.advance(entity)

        trail.record(
            action="ADVANCE_STAGE",
            human_principal_id=gaian.human_principal_id,
            session_id=session_id,
            capability_used=Capability.TRANSITION_STATE,
            target_entity_id=entity_id,
            target_entity_type=entity.type.value,
            before_state=before.value,
            after_state=new_stage.value,
            result="SUCCESS",
        )
        return new_stage

    def suspend_gaian(
        self,
        gaian_id: str,
        revoked_by: str,
        session_id: str,
    ) -> None:
        """Suspend a Gaian instance. Only a Human Principal (SOVEREIGN) can do this."""
        hp = self._get_entity(revoked_by)
        if not isinstance(hp, HumanPrincipalEntity):
            raise OntologicalConstraintError(
                f"Only a Human Principal can suspend a Gaian. "
                f"Entity {revoked_by[:8]} is not a Human Principal."
            )
        gaian = self._get_gaian(gaian_id)
        gaian.is_suspended = True
        gaian.touch()

        trail = self._get_audit_trail(gaian_id)
        trail.record(
            action="GAIAN_SUSPENDED",
            human_principal_id=revoked_by,
            session_id=session_id,
            target_entity_id=gaian_id,
            target_entity_type="GAIAN",
            result="SUCCESS",
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        return self._entities.get(entity_id)

    def get_audit_trail(self, gaian_id: str) -> Optional[AuditTrail]:
        return self._audit_trails.get(gaian_id)

    def get_permission_envelope(self, gaian_id: str) -> Optional[PermissionEnvelope]:
        return self._permission_envelopes.get(gaian_id)

    def get_graph(self) -> RelationshipGraph:
        return self._graph

    def get_state_machine(self) -> AlchemicalStateMachine:
        return self._state_machine

    def list_entities(
        self, entity_type: Optional[EntityType] = None
    ) -> list[Entity]:
        entities = list(self._entities.values())
        if entity_type:
            entities = [e for e in entities if e.type == entity_type]
        return entities

    # ------------------------------------------------------------------
    # Private guards
    # ------------------------------------------------------------------

    def _assert_human_principal_exists(self, hp_id: str) -> None:
        hp = self._entities.get(hp_id)
        if hp is None or not isinstance(hp, HumanPrincipalEntity) or not hp.is_active:
            raise OntologicalConstraintError(
                f"Constraint #1: Human Principal {hp_id[:8] if hp_id else 'NONE'} "
                f"does not exist or is inactive. "
                f"No Gaian without a Human Principal — C03."
            )

    def _get_entity(self, entity_id: str) -> Entity:
        entity = self._entities.get(entity_id)
        if entity is None:
            raise KeyError(f"Entity {entity_id[:8]} not found in runtime.")
        return entity

    def _get_gaian(self, gaian_id: str) -> GaianEntity:
        entity = self._get_entity(gaian_id)
        if not isinstance(entity, GaianEntity):
            raise TypeError(f"Entity {gaian_id[:8]} is not a GaianEntity.")
        return entity

    def _get_atlas_node(self, node_id: str) -> ATLASNodeEntity:
        entity = self._get_entity(node_id)
        if not isinstance(entity, ATLASNodeEntity):
            raise TypeError(f"Entity {node_id[:8]} is not an ATLASNodeEntity.")
        return entity

    def _get_envelope(self, gaian_id: str) -> PermissionEnvelope:
        envelope = self._permission_envelopes.get(gaian_id)
        if envelope is None:
            raise OntologicalConstraintError(
                f"No Permission Envelope found for Gaian {gaian_id[:8]}. "
                f"Constraint #2: No action outside the Permission Envelope."
            )
        return envelope

    def _get_audit_trail(self, gaian_id: str) -> AuditTrail:
        trail = self._audit_trails.get(gaian_id)
        if trail is None:
            raise OntologicalConstraintError(
                f"No Audit Trail found for Gaian {gaian_id[:8]}. "
                f"Constraint #3: No unaudited consequential action."
            )
        return trail
