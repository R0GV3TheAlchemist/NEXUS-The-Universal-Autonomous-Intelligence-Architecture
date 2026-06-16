"""Unit tests: Alchemical state machine — C03 §3, C33."""

import pytest
from core.ontology.entities import AlchemicalStage, GaianEntity
from core.ontology.state_machine import AlchemicalStateMachine, StateTransitionError


@pytest.fixture
def sm():
    return AlchemicalStateMachine()


@pytest.fixture
def entity():
    return GaianEntity(name="test-entity", human_principal_id="hp-001")


class TestAlchemicalStateMachine:
    def test_advance_nigredo_to_albedo(self, sm, entity):
        assert entity.state == AlchemicalStage.NIGREDO
        new_stage = sm.advance(entity)
        assert new_stage == AlchemicalStage.ALBEDO
        assert entity.state == AlchemicalStage.ALBEDO

    def test_advance_full_sequence(self, sm, entity):
        sm.advance(entity)  # NIGREDO → ALBEDO
        sm.advance(entity)  # ALBEDO → CITRINITAS
        sm.advance(entity)  # CITRINITAS → RUBEDO
        assert entity.state == AlchemicalStage.RUBEDO

    def test_advance_beyond_rubedo_raises(self, sm, entity):
        for _ in range(3):
            sm.advance(entity)
        with pytest.raises(StateTransitionError, match="RUBEDO"):
            sm.advance(entity)

    def test_transition_to_skipping_stages_raises(self, sm, entity):
        with pytest.raises(StateTransitionError, match="skip"):
            sm.transition_to(entity, AlchemicalStage.CITRINITAS)

    def test_regress_is_allowed(self, sm, entity):
        sm.advance(entity)  # → ALBEDO
        prev = sm.regress(entity)  # → NIGREDO
        assert prev == AlchemicalStage.NIGREDO

    def test_regress_from_nigredo_raises(self, sm, entity):
        with pytest.raises(StateTransitionError, match="prima materia"):
            sm.regress(entity)

    def test_regression_is_logged(self, sm, entity):
        sm.advance(entity)  # → ALBEDO
        sm.regress(entity)  # ← NIGREDO
        assert sm.regression_count(entity.id) == 1

    def test_transition_history_is_recorded(self, sm, entity):
        sm.advance(entity)
        sm.advance(entity)
        history = sm.get_history(entity.id)
        assert len(history) == 2
        assert history[0][0] == AlchemicalStage.NIGREDO
        assert history[0][1] == AlchemicalStage.ALBEDO

    def test_next_stage(self, sm):
        assert sm.next_stage(AlchemicalStage.NIGREDO) == AlchemicalStage.ALBEDO
        assert sm.next_stage(AlchemicalStage.RUBEDO) is None

    def test_stage_index(self, sm):
        assert sm.stage_index(AlchemicalStage.NIGREDO) == 0
        assert sm.stage_index(AlchemicalStage.RUBEDO) == 3
