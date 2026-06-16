"""Unit tests: Entity creation, types, and invariants — C03 §2."""

import pytest
from datetime import timezone

from core.ontology.entities import (
    AlchemicalStage,
    ATLASNodeEntity,
    EntityType,
    GAIAEntity,
    GaianEntity,
    HumanPrincipalEntity,
    PermissionTier,
)


class TestEntityBase:
    def test_entity_gets_uuid_on_creation(self):
        e = GaianEntity(name="test")
        assert len(e.id) == 36  # UUID format

    def test_entity_default_state_is_nigredo(self):
        e = GaianEntity(name="test")
        assert e.state == AlchemicalStage.NIGREDO

    def test_touch_updates_timestamp(self):
        e = GaianEntity(name="test")
        before = e.updated_at
        e.touch()
        assert e.updated_at >= before


class TestGAIAEntity:
    def test_type_is_gaia(self):
        g = GAIAEntity()
        assert g.type == EntityType.GAIA

    def test_default_name_is_gaia(self):
        g = GAIAEntity()
        assert g.name == "GAIA"

    def test_sovereign_permission_by_default(self):
        g = GAIAEntity()
        assert g.permission_tier == PermissionTier.SOVEREIGN


class TestGaianEntity:
    def test_type_is_gaian(self):
        g = GaianEntity(name="GAIA-1")
        assert g.type == EntityType.GAIAN

    def test_invalid_without_human_principal(self):
        g = GaianEntity(name="orphan")
        assert not g.is_valid()

    def test_valid_with_human_principal(self):
        g = GaianEntity(name="paired", human_principal_id="hp-123")
        assert g.is_valid()

    def test_suspended_gaian_is_invalid(self):
        g = GaianEntity(name="suspended", human_principal_id="hp-123")
        g.is_suspended = True
        assert not g.is_valid()


class TestHumanPrincipalEntity:
    def test_type_is_human_principal(self):
        hp = HumanPrincipalEntity(name="Kyle")
        assert hp.type == EntityType.HUMAN_PRINCIPAL

    def test_can_elevate_to_own_tier(self):
        hp = HumanPrincipalEntity(name="Kyle", permission_tier=PermissionTier.SOVEREIGN)
        assert hp.can_elevate(PermissionTier.STEWARD)
        assert hp.can_elevate(PermissionTier.SOVEREIGN)

    def test_cannot_elevate_above_own_tier(self):
        hp = HumanPrincipalEntity(name="Lesser", permission_tier=PermissionTier.COLLABORATOR)
        assert not hp.can_elevate(PermissionTier.STEWARD)


class TestATLASNodeEntity:
    def test_type_is_atlas_node(self):
        node = ATLASNodeEntity(name="Amazon Watershed", atlas_node_type="WATERSHED")
        assert node.type == EntityType.ATLAS_NODE

    def test_health_score_starts_at_1(self):
        node = ATLASNodeEntity(name="Test", atlas_node_type="BIOME")
        assert node.ecological_health_score == 1.0

    def test_record_observation_clamps_health_score(self):
        node = ATLASNodeEntity(name="Test", atlas_node_type="BIOME")
        node.record_observation(health_score=1.5, confidence="HIGH")
        assert node.ecological_health_score == 1.0
        node.record_observation(health_score=-0.5, confidence="HIGH")
        assert node.ecological_health_score == 0.0

    def test_record_observation_sets_last_observed(self):
        node = ATLASNodeEntity(name="Test", atlas_node_type="CITY")
        assert node.last_observed_at is None
        node.record_observation(0.8, "MEDIUM")
        assert node.last_observed_at is not None
