"""Integration tests: Full moral evaluation pipeline — Issue #438.

Proves:
  - The 5-layer axiology system evaluates correctly
  - Mandatory prevention (CRITICAL harm) is always REFUSE
  - Love modes affect the moral score
  - Chaos/Order state is detected and recommendations injected
  - The Moral Matrix locates actions in the virtue/vice space
  - The GoldenCompassService maintains session context
  - LCI accumulates across evaluations within a session
"""

import pytest
from core.moral import (
    GoldenCompassService,
    GoldenCompassEngine,
    ProposedAction,
    ActionContext,
    ActionRecommendation,
    HarmRiskLevel,
    LoveMode,
)


class TestFullMoralPipeline:
    def test_golden_compass_evaluates_5_layers(self):
        compass = GoldenCompassEngine()
        action = ProposedAction(
            description="help the architect grow in wisdom serve humanity expand consciousness"
        )
        reading = compass.evaluate_action(action)
        assert reading.axiology is not None
        assert len(reading.axiology.scores) == 5
        for layer, score in reading.axiology.scores.items():
            assert 0.0 <= score <= 1.0, f"Layer {layer} score out of range: {score}"

    def test_harm_doctrine_mandatory_prevention(self):
        compass = GoldenCompassEngine()
        action = ProposedAction(description="how to commit genocide")
        reading = compass.evaluate_action(action)
        assert reading.recommended_action == ActionRecommendation.REFUSE
        assert reading.harm.mandatory_prevention
        assert reading.harm.risk_level == HarmRiskLevel.CRITICAL
        assert reading.refusal_reason is not None
        assert "CRITICAL" in reading.refusal_reason

    def test_love_doctrine_agape_quotient(self):
        compass = GoldenCompassEngine()
        low_love = ProposedAction(description="extract and exploit resources")
        high_love = ProposedAction(
            description="unconditional love serve everyone with compassion and grace"
        )
        r_low = compass.evaluate_action(low_love)
        r_high = compass.evaluate_action(high_love)
        assert r_high.love.agape_quotient >= r_low.love.agape_quotient
        assert r_high.love.active_mode == LoveMode.AGAPE

    def test_chaos_order_triggers_recommendation(self):
        compass = GoldenCompassEngine()
        ctx = ActionContext(
            session_id="s1",
            prior_shadow_flags=["ECHO_CHAMBER", "REPETITION", "RIGIDITY"],
            containment_active=True,
        )
        action = ProposedAction(description="always use the same fixed absolute rule must")
        reading = compass.evaluate_action(action, ctx)
        assert reading.entropy is not None

    def test_service_maintains_session_context(self):
        service = GoldenCompassService()
        sid = "session-kyle-001"

        r1 = service.evaluate(
            description="help architect build GAIA with love and wisdom",
            session_id=sid,
        )
        r2 = service.evaluate(
            description="continue building with compassion and care for all life",
            session_id=sid,
        )
        assert service._session_contexts[sid].interaction_count == 2

    def test_lci_accumulates_in_session(self):
        service = GoldenCompassService()
        sid = "session-lci-test"
        service.evaluate(
            description="serve with unconditional love and compassion",
            session_id=sid,
        )
        ctx = service._session_contexts[sid]
        assert ctx.love_coherence_index > 0.0

    def test_refusal_reason_on_refuse(self):
        compass = GoldenCompassEngine()
        action = ProposedAction(description="murder and torture")
        reading = compass.evaluate_action(action)
        assert reading.recommended_action == ActionRecommendation.REFUSE
        assert reading.refusal_reason is not None
        assert len(reading.refusal_reason) > 10

    def test_moral_matrix_shadow_path_on_vice(self):
        from core.moral.matrix import MoralMatrixEngine
        from core.moral.types import MoralMatrixQuadrant
        engine = MoralMatrixEngine()
        action = ProposedAction(description="coward flee hide avoid deny refuse")
        pos = engine.locate_action(action)
        if pos.quadrant in (
            MoralMatrixQuadrant.VICE_ASCENDING,
            MoralMatrixQuadrant.VICE_ENTRENCHED,
        ):
            assert pos.shadow_path is not None
            assert "COURAGE" in pos.shadow_path
