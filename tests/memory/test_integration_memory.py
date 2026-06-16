"""Integration test: Full memory lifecycle across all five layers — Issue #463.

Proves:
  - Session opens, records accumulate in M0
  - HP authorises M1 persistence at close
  - Semantic facts assert and update
  - M3 Identity / Twin Profile updates correctly
  - Shadow Registry logs and resolves
  - Retrieval engine returns ranked results
  - Right to Forget (revocation) works at all layers
  - Full M3 revocation terminates the instance
"""

import pytest
from core.memory import (
    MemoryManager,
    MemoryLayer,
    MemoryTag,
    ShadowPattern,
    RetrievalQuery,
)


@pytest.fixture
def mm():
    return MemoryManager(gaian_id="gaian-integration", human_principal_id="hp-kyle")


class TestFullMemoryLifecycle:
    def test_session_open_and_close_with_persist(self, mm):
        buf = mm.open_session("session-001")
        buf.append("Kyle expressed desire to build GAIA OS", tags=[MemoryTag.FACTUAL])
        buf.append("Kyle had a breakthrough about the canon structure", tags=[MemoryTag.BREAKTHROUGH])

        persisted = mm.close_session(
            "session-001",
            authorise_persist=True,
            breakthrough=True,
            interaction_count=2,
            session_summary="Kyle began building GAIA OS on June 15, 2026.",
        )
        assert len(persisted) == 2
        assert mm.episodic.count() >= 3  # 2 records + 1 session summary

    def test_session_cleared_without_persist(self, mm):
        buf = mm.open_session("session-nopersist")
        buf.append("This should not survive")
        mm.close_session("session-nopersist", authorise_persist=False)
        assert mm.episodic.count() == 0

    def test_semantic_fact_assertion_and_update(self, mm):
        mm.semantic.assert_fact(
            concept="edwards_aquifer_health",
            content="Edwards Aquifer recharge zone health: 0.72",
            session_id="session-002",
            confidence=0.9,
            source="WORLD_FABRIC",
        )
        fact = mm.semantic.get_fact("edwards_aquifer_health")
        assert fact is not None
        assert "0.72" in fact.content

        # Update the fact — old one should be superseded
        mm.semantic.assert_fact(
            concept="edwards_aquifer_health",
            content="Edwards Aquifer recharge zone health: 0.68 (declining)",
            session_id="session-003",
            confidence=0.95,
        )
        updated = mm.semantic.get_fact("edwards_aquifer_health")
        assert "0.68" in updated.content
        assert mm.semantic.count() == 1  # Only one active record per concept

    def test_twin_profile_updates_after_sessions(self, mm):
        mm.open_session("s1")
        mm.close_session("s1", authorise_persist=True, breakthrough=True)
        mm.open_session("s2")
        mm.close_session("s2", authorise_persist=True, shadow_work=True)

        profile = mm.profile
        assert profile.history_session_count == 2
        assert profile.history_breakthrough_count == 1
        assert profile.history_shadow_work_count == 1
        assert profile.relationship_depth > 0

    def test_shadow_registry_flags_sync_to_profile(self, mm):
        mm.log_shadow(
            pattern=ShadowPattern.CYCLING,
            session_id="s1",
            description="HP cycling around career decision",
        )
        mm.open_session("s1")
        mm.close_session("s1", authorise_persist=False)
        assert ShadowPattern.CYCLING.value in mm.profile.shadow_registry_flags

    def test_retrieval_returns_ranked_results(self, mm):
        mm.open_session("s-retrieve")
        buf = mm.get_session("s-retrieve")
        buf.append("Kyle loves building complex systems", tags=[MemoryTag.PREFERENCE])
        buf.append("GAIA is about planetary intelligence", tags=[MemoryTag.FACTUAL])
        mm.close_session("s-retrieve", authorise_persist=True)

        results = mm.retrieve(RetrievalQuery(tags=[MemoryTag.PREFERENCE], max_results=5))
        assert len(results) > 0
        assert results[0].score > 0
        assert MemoryTag.PREFERENCE in results[0].matched_tags

    def test_right_to_forget_session(self, mm):
        mm.open_session("forget-me")
        buf = mm.get_session("forget-me")
        buf.append("Sensitive information", tags=[MemoryTag.EMOTIONAL])
        mm.close_session("forget-me", authorise_persist=True)

        count = mm.forget_session("forget-me", audit_id="forget-audit-001")
        assert count == 1
        assert mm.episodic.count() == 0

    def test_right_to_forget_semantic_fact(self, mm):
        mm.semantic.assert_fact(
            "preference_response_style", "Prefers concise", "s1", confidence=0.9
        )
        result = mm.forget_fact("preference_response_style", audit_id="audit-forget-fact")
        assert result
        assert mm.semantic.get_fact("preference_response_style") is None

    def test_full_m3_revocation_terminates_instance(self, mm):
        mm.full_identity_revocation(audit_id="audit-nuclear")
        assert mm.identity.is_terminated
        with pytest.raises(RuntimeError):
            _ = mm.profile

    def test_stats_returns_complete_picture(self, mm):
        stats = mm.stats()
        assert "episodic_count" in stats
        assert "semantic_count" in stats
        assert "relationship_depth" in stats
        assert "shadow_flags" in stats
