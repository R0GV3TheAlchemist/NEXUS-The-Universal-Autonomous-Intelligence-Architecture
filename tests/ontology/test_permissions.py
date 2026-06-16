"""Unit tests: Permission Envelope and Audit Trail — C03 §3.3–3.5."""

import pytest
from core.ontology.entities import PermissionTier
from core.ontology.permissions import (
    AuditTrail,
    Capability,
    PermissionDeniedError,
    PermissionEnvelope,
)


@pytest.fixture
def envelope():
    return PermissionEnvelope(
        gaian_id="gaian-001",
        human_principal_id="hp-001",
        session_id="session-001",
        tier=PermissionTier.COLLABORATOR,
    )


@pytest.fixture
def trail():
    return AuditTrail(gaian_id="gaian-001")


class TestPermissionEnvelope:
    def test_collaborator_has_write_entity(self, envelope):
        assert envelope.has(Capability.WRITE_ENTITY)

    def test_collaborator_lacks_manage_atlas_node(self, envelope):
        assert not envelope.has(Capability.MANAGE_ATLAS_NODE)

    def test_require_raises_on_missing_capability(self, envelope):
        with pytest.raises(PermissionDeniedError):
            envelope.require(Capability.REVOKE_GAIAN)

    def test_grant_adds_extra_capability(self, envelope):
        envelope.grant(Capability.MANAGE_ATLAS_NODE)
        assert envelope.has(Capability.MANAGE_ATLAS_NODE)

    def test_revoke_removes_tier_capability(self, envelope):
        envelope.revoke(Capability.WRITE_ENTITY)
        assert not envelope.has(Capability.WRITE_ENTITY)

    def test_sovereign_tier_has_all_capabilities(self):
        env = PermissionEnvelope(
            gaian_id="g", human_principal_id="hp", session_id="s",
            tier=PermissionTier.SOVEREIGN,
        )
        for cap in Capability:
            assert env.has(cap), f"SOVEREIGN should have {cap.value}"

    def test_observer_has_only_read_capabilities(self):
        env = PermissionEnvelope(
            gaian_id="g", human_principal_id="hp", session_id="s",
            tier=PermissionTier.OBSERVER,
        )
        assert env.has(Capability.READ_ENTITY)
        assert not env.has(Capability.WRITE_ENTITY)
        assert not env.has(Capability.MANAGE_ATLAS_NODE)


class TestAuditTrail:
    def test_record_appends_entry(self, trail):
        trail.record(action="TEST", human_principal_id="hp", session_id="s")
        assert trail.count() == 1

    def test_all_returns_copy(self, trail):
        trail.record(action="A", human_principal_id="hp", session_id="s")
        entries = trail.all()
        entries.clear()  # modifying the copy should not affect the trail
        assert trail.count() == 1

    def test_filter_by_result(self, trail):
        trail.record(action="OK", human_principal_id="hp", session_id="s", result="SUCCESS")
        trail.record(action="FAIL", human_principal_id="hp", session_id="s", result="DENIED")
        denied = trail.filter(result="DENIED")
        assert len(denied) == 1
        assert denied[0].action == "FAIL"

    def test_filter_by_target(self, trail):
        trail.record(action="A", human_principal_id="hp", session_id="s", target_entity_id="node-1")
        trail.record(action="B", human_principal_id="hp", session_id="s", target_entity_id="node-2")
        filtered = trail.filter(target_entity_id="node-1")
        assert len(filtered) == 1
