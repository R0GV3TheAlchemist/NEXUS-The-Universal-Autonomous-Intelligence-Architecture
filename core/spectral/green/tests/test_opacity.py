import pytest
from core.spectral.green.opacity import (
    grief_freeze_alert, compassion_fatigue_detection,
    heart_armoring_marker, mercury_venus_routing, apply_shadow_channel
)


def test_grief_freeze_alert_never_interrupts():
    s = {"grief_markers": ["grief_freeze"]}
    result = grief_freeze_alert(s)
    assert result["interrupt_flag"] is False


def test_compassion_fatigue_detected():
    s = {"fatigue_history": [0.7, 0.8, 0.9]}
    result = compassion_fatigue_detection(s)
    assert result["fatigue_detected"] is True
    assert result["interrupt_flag"] is False


def test_heart_armoring_flagged():
    s = {"coherence": 0.1}
    result = heart_armoring_marker(s)
    assert result["armored"] is True
    assert result["interrupt_flag"] is False


def test_mercury_venus_routing():
    assert mercury_venus_routing({"bridge_stability": 0.9, "love_index": 0.3}) == "mercury"
    assert mercury_venus_routing({"bridge_stability": 0.2, "love_index": 0.8}) == "venus"


def test_apply_shadow_channel_no_mutation():
    primary = {"coherence": 0.6}
    shadow = [{"type": "heart_armoring", "interrupt_flag": False}]
    enriched = apply_shadow_channel(primary, shadow)
    assert "_green_shadow" in enriched
    assert "_green_shadow" not in primary
