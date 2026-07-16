import pytest
from core.spectral.yellow.transparency import (
    detect_solar_state, emit_solar_alert,
    classify_will_urgency, get_ui_state, is_separation_signal
)


def test_detect_solar_state_sovereign():
    s = {"will_strength": 0.9, "ego_clarity": 0.85, "shame_index": 0.05}
    result = detect_solar_state(s)
    assert result["phase"] == "sovereign_activation"
    assert result["archetype"] == "sovereign"


def test_detect_solar_state_shame_collapse():
    s = {"will_strength": 0.3, "ego_clarity": 0.4, "shame_index": 0.8}
    result = detect_solar_state(s)
    assert result["phase"] == "shame_collapse"


def test_emit_solar_alert_never_interrupts():
    alert = emit_solar_alert("WILL_COLLAPSE")
    assert alert["interrupt_flag"] is False
    assert alert["severity"] == 2


def test_classify_will_urgency_critical():
    s = {"will_strength": 0.5, "shame_index": 0.5, "collapse_flag": True}
    assert classify_will_urgency(s) == "critical"


def test_is_separation_signal_true():
    s = {"ego_clarity": 0.9}
    assert is_separation_signal(s) is True
