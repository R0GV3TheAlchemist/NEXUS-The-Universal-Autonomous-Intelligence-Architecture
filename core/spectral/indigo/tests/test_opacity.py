import pytest
from core.spectral.indigo.opacity import (
    block_alert, psychic_overload_detection,
    vision_fog_marker, saturn_jupiter_routing, apply_shadow_channel
)


def test_block_alert_never_interrupts():
    s = {"block_markers": ["intuition_suppression"]}
    result = block_alert(s)
    assert result["interrupt_flag"] is False


def test_psychic_overload_detected():
    s = {"load_history": [0.8, 0.9, 0.75]}
    result = psychic_overload_detection(s)
    assert result["overload_detected"] is True
    assert result["interrupt_flag"] is False


def test_vision_fog_marker():
    s = {"field_clarity": 0.1}
    result = vision_fog_marker(s)
    assert result["fogged"] is True
    assert result["interrupt_flag"] is False


def test_saturn_jupiter_routing():
    assert saturn_jupiter_routing({"structure_need": 0.9, "expansion_index": 0.2}) == "saturn"
    assert saturn_jupiter_routing({"structure_need": 0.2, "expansion_index": 0.8}) == "jupiter"


def test_apply_shadow_channel_no_mutation():
    primary = {"intuition_index": 0.7}
    shadow = [{"type": "vision_fog", "interrupt_flag": False}]
    enriched = apply_shadow_channel(primary, shadow)
    assert "_indigo_shadow" in enriched
    assert "_indigo_shadow" not in primary
