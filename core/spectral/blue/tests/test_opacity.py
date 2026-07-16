import pytest
from core.spectral.blue.opacity import (
    silence_alert, distortion_loop_detection,
    perception_fog_marker, jupiter_mercury_routing, apply_shadow_channel
)


def test_silence_alert_never_interrupts():
    s = {"silence_markers": ["voice_suppression"]}
    result = silence_alert(s)
    assert result["interrupt_flag"] is False


def test_distortion_loop_detected():
    s = {"distortion_history": [0.7, 0.8, 0.65]}
    result = distortion_loop_detection(s)
    assert result["loop_detected"] is True
    assert result["interrupt_flag"] is False


def test_perception_fog_marker():
    s = {"perception_fog": 0.8}
    result = perception_fog_marker(s)
    assert result["fogged"] is True
    assert result["interrupt_flag"] is False


def test_jupiter_mercury_routing():
    assert jupiter_mercury_routing({"vision_index": 0.9, "precision_index": 0.3}) == "jupiter"
    assert jupiter_mercury_routing({"vision_index": 0.2, "precision_index": 0.8}) == "mercury"


def test_apply_shadow_channel_no_mutation():
    primary = {"truth_index": 0.7}
    shadow = [{"type": "perception_fog", "interrupt_flag": False}]
    enriched = apply_shadow_channel(primary, shadow)
    assert "_blue_shadow" in enriched
    assert "_blue_shadow" not in primary
