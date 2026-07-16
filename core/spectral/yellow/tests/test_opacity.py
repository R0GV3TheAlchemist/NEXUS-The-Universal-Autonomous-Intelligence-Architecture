import pytest
from core.spectral.yellow.opacity import (
    inflation_alert, shame_spiral_detection,
    will_suppression_marker, sol_luna_routing, apply_shadow_channel
)


def test_inflation_alert_never_interrupts():
    s = {"inflation_markers": ["grandiosity"]}
    result = inflation_alert(s)
    assert result["interrupt_flag"] is False


def test_shame_spiral_detected():
    s = {"shame_history": [0.7, 0.8, 0.9, 0.7]}
    result = shame_spiral_detection(s)
    assert result["spiral_detected"] is True
    assert result["interrupt_flag"] is False


def test_will_suppression_flagged():
    s = {"will_strength": 0.1}
    result = will_suppression_marker(s)
    assert result["suppressed"] is True
    assert result["interrupt_flag"] is False


def test_sol_luna_routing():
    assert sol_luna_routing({"will_strength": 0.9, "receptivity": 0.2}) == "sol"
    assert sol_luna_routing({"will_strength": 0.2, "receptivity": 0.8}) == "luna"


def test_apply_shadow_channel_no_mutation():
    primary = {"will_strength": 0.6}
    shadow = [{"type": "shame_spiral", "interrupt_flag": False}]
    enriched = apply_shadow_channel(primary, shadow)
    assert "_yellow_shadow" in enriched
    assert "_yellow_shadow" not in primary
