"""tests/test_twins.py

Test scaffold for src-python/twins

Covers: TwinSpec, TwinState, SyncPlan, TwinConsent, TwinOrchestrator
"""
import pytest

from twins import TwinSpec, TwinState, SyncPlan, TwinConsent, TwinOrchestrator


class TestTwinSpec:

    def test_twin_spec_constructs(self):
        spec = TwinSpec(name="GAIA-Alpha", model_id="dtdl:gaian:node", owner="nexus-kernel")
        assert spec.name == "GAIA-Alpha"
        assert spec.twin_id  # UUID auto-assigned


class TestTwinOrchestrator:

    def test_register_twin(self):
        orch = TwinOrchestrator()
        spec = TwinSpec(name="Node-1", model_id="m1", owner="root")
        twin_id = orch.register(spec)
        assert twin_id == spec.twin_id
        assert twin_id in orch._twins

    def test_sync_raises_not_implemented(self):
        orch = TwinOrchestrator()
        spec = TwinSpec(name="Node-1", model_id="m1", owner="root")
        orch.register(spec)
        plan = SyncPlan(twin_id=spec.twin_id)
        with pytest.raises(NotImplementedError):
            orch.sync(spec.twin_id, plan)

    def test_grant_and_revoke_consent(self):
        orch = TwinOrchestrator()
        spec = TwinSpec(name="Node-1", model_id="m1", owner="root")
        orch.register(spec)
        consent = TwinConsent(
            twin_id=spec.twin_id,
            granted_to="agent-x",
            permissions=["read", "sync"],
        )
        orch.grant_consent(consent)
        revoked = orch.revoke_consent(spec.twin_id, "agent-x")
        assert revoked is True

    def test_revoke_nonexistent_consent_returns_false(self):
        orch = TwinOrchestrator()
        result = orch.revoke_consent("no-twin", "no-agent")
        assert result is False
