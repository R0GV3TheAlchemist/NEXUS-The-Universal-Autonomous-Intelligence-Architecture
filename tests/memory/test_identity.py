"""Unit tests: M3 Identity Memory Store and Gaian Twin Profile."""

import pytest
from core.memory.identity import IdentityMemoryStore, GaianTwinProfile
from core.memory.layers import MemoryTag


@pytest.fixture
def store():
    return IdentityMemoryStore("gaian-001", "hp-001")


class TestGaianTwinProfile:
    def test_profile_starts_at_nigredo(self, store):
        assert store.profile.current_alchemical_stage == "NIGREDO"

    def test_record_session_increments_count(self, store):
        store.profile.record_session("s1")
        assert store.profile.history_session_count == 1

    def test_relationship_depth_grows_with_sessions(self, store):
        for i in range(10):
            store.profile.record_session(f"s{i}")
        assert store.profile.relationship_depth > 0
        assert store.profile.relationship_depth <= 1.0

    def test_add_theme(self, store):
        store.profile.add_theme("transformation")
        store.profile.add_theme("transformation")  # duplicate
        assert store.profile.history_key_themes.count("transformation") == 1

    def test_breakthrough_recorded(self, store):
        store.profile.add_breakthrough("Realised the system is the canon")
        assert store.profile.history_breakthrough_count == 1

    def test_containment_toggle(self, store):
        store.profile.set_containment(True, reason="rapid ascension")
        assert store.profile.containment_active
        assert store.profile.containment_reason == "rapid ascension"
        store.profile.set_containment(False)
        assert not store.profile.containment_active
        assert store.profile.containment_reason is None


class TestIdentityMemoryStore:
    def test_store_record(self, store):
        r = store.store("GAIA values the human", session_id="s1")
        assert store.count() == 1

    def test_full_revocation_terminates_instance(self, store):
        store.store("identity datum", session_id="s1")
        store.full_revocation(audit_id="audit-final")
        assert store.is_terminated

    def test_profile_raises_after_termination(self, store):
        store.full_revocation(audit_id="audit-final")
        with pytest.raises(RuntimeError, match="terminated"):
            _ = store.profile

    def test_cannot_write_after_termination(self, store):
        store.full_revocation(audit_id="audit-final")
        with pytest.raises(RuntimeError, match="terminated"):
            store.store("too late", session_id="s1")
