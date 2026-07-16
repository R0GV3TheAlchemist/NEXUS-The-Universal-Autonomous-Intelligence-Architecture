import pytest
from core.spectral.orange.opacity import (
    calcination_alert, martyrdom_loop_detection,
    sacral_depletion_marker, venus_aphrodite_routing, apply_shadow_channel
)


def test_calcination_alert_never_interrupts():
    s = {"calcination_markers": ["purification_by_fire", "desire_transmutation"]}
    result = calcination_alert(s)
    assert result["interrupt_flag"] is False


def test_martyrdom_loop_detection_detected():
    s = {"guilt_history": [0.7, 0.8, 0.9, 0.65]}
    result = martyrdom_loop_detection(s)
    assert result["loop_detected"] is True


def test_martyrdom_loop_not_detected():
    s = {"guilt_history": [0.3, 0.2, 0.7]}
    result = martyrdom_loop_detection(s)
    assert result["loop_detected"] is False


def test_sacral_depletion_flagged():
    s = {"vitality": 0.1}
    result = sacral_depletion_marker(s)
    assert result["depletion_flag"] is True
    assert result["interrupt_flag"] is False


def test_venus_aphrodite_routing():
    assert venus_aphrodite_routing({"desire_index": 0.8, "receptivity": 0.3}) == "aphrodite"
    assert venus_aphrodite_routing({"desire_index": 0.2, "receptivity": 0.9}) == "venus"


def test_apply_shadow_channel_does_not_mutate():
    primary = {"intensity": 0.7, "color": "ORANGE"}
    shadow = [{"type": "sacral_depletion", "interrupt_flag": False}]
    enriched = apply_shadow_channel(primary, shadow)
    assert "_orange_shadow" in enriched
    assert "_orange_shadow" not in primary
