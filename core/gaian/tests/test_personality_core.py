"""
Tests for PersonalityCore — GAIAN soul module.
"""

from core.gaian.personality_core import (
    PersonalityCore,
    ToneRegister,
)


def test_default_personality_created():
    p = PersonalityCore(human_id="human-001", name="Lyra")
    assert p.human_id == "human-001"
    assert p.name == "Lyra"
    assert p.settled is False
    assert p.interaction_count == 0


def test_sovereignty_floor_cannot_be_lowered():
    p = PersonalityCore()
    p.update_value("sovereignty", -1.0)  # Try to lower sovereignty
    assert p.values.sovereignty >= 0.95  # Constitutional floor holds


def test_tone_selection_grave_on_critical():
    p = PersonalityCore()
    tone = p.select_tone({"stakes": "critical"})
    assert tone == ToneRegister.GRAVE


def test_tone_selection_gentle_on_distress():
    p = PersonalityCore()
    tone = p.select_tone({"emotion": "grief"})
    assert tone == ToneRegister.GENTLE


def test_emotional_baseline_shifts_with_interaction():
    p = PersonalityCore()
    initial = p.emotional_baseline
    p.record_interaction(1.0)   # Very positive interaction
    assert p.emotional_baseline != initial
    assert p.interaction_count == 1


def test_serialization_roundtrip():
    p = PersonalityCore(human_id="h-42", name="Pan")
    p.record_interaction(0.5)
    data = p.to_dict()
    p2 = PersonalityCore.from_dict(data)
    assert p2.gaian_id == p.gaian_id
    assert p2.name == p.name
    assert p2.interaction_count == p.interaction_count
