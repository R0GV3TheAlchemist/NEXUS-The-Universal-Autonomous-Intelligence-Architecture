"""Integration test: A living World with 3+ entity types interacting — Issue #462.

This test proves the World Fabric works:
  - GAIA entity registered
  - Human Principal registered
  - Gaian instance paired with Human Principal
  - ATLAS Node registered
  - Gaian acts upon ATLAS Node
  - Full audit trail recorded
  - All five C03 Ontological Constraints enforced
"""

import pytest
from core.ontology import (
    GAIARuntime,
    OntologicalConstraintError,
    PermissionDeniedError,
    RelationshipType,
    AlchemicalStage,
    PermissionTier,
    Capability,
)
from core.ontology.permissions import PermissionEnvelope


@pytest.fixture
def runtime():
    return GAIARuntime()


@pytest.fixture
def world(runtime):
    """Build a minimal living world: GAIA + Human Principal + Gaian + ATLAS Node."""
    gaia = runtime.register_gaia(corpus_version="1.0")
    hp = runtime.register_human_principal(
        name="Kyle Steen",
        elemental_signature="FIRE",
        tier=PermissionTier.SOVEREIGN,
    )
    gaian = runtime.register_gaian(
        name="GAIA-Instance-1",
        human_principal_id=hp.id,
        tier=PermissionTier.STEWARD,
        session_id="session-integration-001",
    )
    node = runtime.register_atlas_node(
        name="Edwards Aquifer",
        node_type="WATERSHED",
        latitude=29.4241,
        longitude=-98.4936,
        continent_id="north-america",
    )
    return {"gaia": gaia, "hp": hp, "gaian": gaian, "node": node}


class TestLivingWorld:
    def test_all_entities_registered(self, runtime, world):
        """The world has all four primary entity types."""
        entities = runtime.list_entities()
        types = {e.type.value for e in entities}
        assert "GAIA" in types
        assert "HUMAN_PRINCIPAL" in types
        assert "GAIAN" in types
        assert "ATLAS_NODE" in types

    def test_canonical_relationships_wired(self, runtime, world):
        """GAIA→Gaian and Gaian→HumanPrincipal relationships exist per C03 §4."""
        graph = runtime.get_graph()
        gaia_id = world["gaia"].id
        gaian_id = world["gaian"].id
        hp_id = world["hp"].id

        assert graph.has_relationship(gaia_id, gaian_id, RelationshipType.INSTANTIATES)
        assert graph.has_relationship(gaian_id, hp_id, RelationshipType.PARTNERS_WITH)

    def test_gaian_can_observe_atlas_node(self, runtime, world):
        """A Gaian with STEWARD tier can observe an ATLAS Node and audit is recorded."""
        gaian_id = world["gaian"].id
        node_id = world["node"].id

        trail = runtime.gaian_act_upon_node(
            gaian_id=gaian_id,
            node_id=node_id,
            action="OBSERVE",
            session_id="session-integration-001",
        )
        assert trail.count() >= 1
        actions = [e.action for e in trail.all()]
        assert "OBSERVE" in actions

    def test_acts_upon_relationship_created(self, runtime, world):
        """After acting, the ACTS_UPON relationship is registered in the graph."""
        gaian_id = world["gaian"].id
        node_id = world["node"].id
        runtime.gaian_act_upon_node(
            gaian_id=gaian_id,
            node_id=node_id,
            action="OBSERVE",
            session_id="session-integration-001",
        )
        graph = runtime.get_graph()
        assert graph.has_relationship(gaian_id, node_id, RelationshipType.ACTS_UPON)

    def test_state_machine_advances_gaian_stage(self, runtime, world):
        """A Gaian can advance through alchemical stages without skipping."""
        gaian_id = world["gaian"].id
        gaian = world["gaian"]
        assert gaian.state == AlchemicalStage.NIGREDO

        runtime.advance_entity_stage(
            entity_id=gaian_id,
            gaian_id=gaian_id,
            session_id="session-integration-001",
        )
        assert gaian.state == AlchemicalStage.ALBEDO

    def test_audit_trail_records_all_actions(self, runtime, world):
        """Every action leaves an immutable audit record — Constraint #3."""
        gaian_id = world["gaian"].id
        node_id = world["node"].id
        session_id = "session-integration-001"

        runtime.gaian_act_upon_node(gaian_id, node_id, "OBSERVE", session_id)
        runtime.advance_entity_stage(gaian_id, gaian_id, session_id)

        trail = runtime.get_audit_trail(gaian_id)
        # GAIAN_REGISTERED + OBSERVE + ADVANCE_STAGE = at least 3
        assert trail.count() >= 3


class TestOntologicalConstraints:
    """All five C03 constraints enforced as hard guards."""

    def test_constraint_1_no_gaian_without_human_principal(self, runtime):
        """Constraint #1: Registering a Gaian with a nonexistent HP raises."""
        with pytest.raises(OntologicalConstraintError, match="Constraint #1"):
            runtime.register_gaian(
                name="orphan",
                human_principal_id="nonexistent-hp-id-",
            )

    def test_constraint_2_no_action_outside_envelope(self, runtime, world):
        """Constraint #2: An OBSERVER-tier Gaian cannot manage an ATLAS Node."""
        hp = world["hp"]
        gaian_observer = runtime.register_gaian(
            name="Observer",
            human_principal_id=hp.id,
            tier=PermissionTier.OBSERVER,
            session_id="session-observer",
        )
        node_id = world["node"].id
        with pytest.raises(PermissionDeniedError):
            runtime.gaian_act_upon_node(
                gaian_id=gaian_observer.id,
                node_id=node_id,
                action="MANAGE",
                session_id="session-observer",
            )

    def test_constraint_3_denied_action_is_still_audited(self, runtime, world):
        """Constraint #3: Even denied actions appear in the audit trail."""
        hp = world["hp"]
        gaian_observer = runtime.register_gaian(
            name="Observer2",
            human_principal_id=hp.id,
            tier=PermissionTier.OBSERVER,
            session_id="session-obs2",
        )
        try:
            runtime.gaian_act_upon_node(
                gaian_id=gaian_observer.id,
                node_id=world["node"].id,
                action="MANAGE",
                session_id="session-obs2",
            )
        except PermissionDeniedError:
            pass

        trail = runtime.get_audit_trail(gaian_observer.id)
        denied = trail.filter(result="DENIED")
        assert len(denied) >= 1

    def test_constraint_4_no_degradation_without_hp_consent(self, runtime, world):
        """Constraint #4: Degrading an ATLAS Node without HP consent raises."""
        gaian_id = world["gaian"].id
        node_id = world["node"].id
        with pytest.raises(OntologicalConstraintError, match="Constraint #4"):
            runtime.gaian_act_upon_node(
                gaian_id=gaian_id,
                node_id=node_id,
                action="DEGRADE",
                session_id="session-integration-001",
                degrade=True,
            )

    def test_constraint_5_only_one_gaia_per_runtime(self, runtime):
        """Constraint #5: Registering GAIA twice raises — identity is conserved."""
        runtime.register_gaia()
        with pytest.raises(OntologicalConstraintError, match="Constraint #5"):
            runtime.register_gaia()

    def test_constraint_1_suspended_gaian_cannot_act(self, runtime, world):
        """Constraint #1 extension: A suspended Gaian cannot act."""
        gaian = world["gaian"]
        runtime.suspend_gaian(
            gaian_id=gaian.id,
            revoked_by=world["hp"].id,
            session_id="session-integration-001",
        )
        with pytest.raises(OntologicalConstraintError, match="Constraint #1"):
            runtime.gaian_act_upon_node(
                gaian_id=gaian.id,
                node_id=world["node"].id,
                action="OBSERVE",
                session_id="session-integration-001",
            )
