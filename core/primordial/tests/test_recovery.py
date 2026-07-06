"""Tests for the recovery simulation engine."""

from __future__ import annotations

from core.primordial.entity import PrimordialEntity
from core.primordial.recovery import Intervention, InterventionType, RecoverySimulation


def _collapsed_entity(name: str = "collapsed") -> PrimordialEntity:
    return PrimordialEntity(
        name=name,
        love=0.15,
        life=0.12,
        integrity=0.20,
        hope=0.10,
        truth=0.20,
        burden=2.0,
    )


def test_no_intervention_does_not_recover():
    entity  = _collapsed_entity()
    outcome = RecoverySimulation().run(entity, interventions=[])
    assert outcome.first_run.survived is False
    assert outcome.second_run.survived is False
    assert outcome.recovered is False


def test_full_intervention_at_max_intensity_recovers():
    entity = _collapsed_entity()
    interventions = [
        Intervention(intervention_type=InterventionType.ALL, intensity=1.0)
    ]
    outcome = RecoverySimulation().run(entity, interventions=interventions)
    assert outcome.second_run.survived is True
    assert outcome.recovered is True
    assert outcome.order_delta > 0.0


def test_partial_intervention_increases_order():
    entity = _collapsed_entity()
    interventions = [
        Intervention(intervention_type=InterventionType.REST,    intensity=0.5),
        Intervention(intervention_type=InterventionType.WITNESS, intensity=0.5),
    ]
    outcome = RecoverySimulation().run(entity, interventions=interventions)
    assert outcome.second_run.emergent_order >= outcome.first_run.emergent_order


def test_love_intervention_raises_love_constant():
    entity = _collapsed_entity()
    interventions = [
        Intervention(intervention_type=InterventionType.LOVE, intensity=1.0)
    ]
    outcome = RecoverySimulation().run(entity, interventions=interventions)
    assert outcome.restored_entity["love"] > entity.love


def test_recovery_outcome_has_narrative():
    entity  = _collapsed_entity()
    outcome = RecoverySimulation().run(entity, [])
    d = outcome.to_dict()
    assert "narrative" in d
    assert len(d["narrative"]) > 0
