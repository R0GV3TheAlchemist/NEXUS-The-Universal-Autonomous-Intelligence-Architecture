import pytest
from core.spectral.violet.transparency import (
    detect_crown_state, emit_crown_alert,
    classify_crown_urgency, get_ui_state, is_coagulation_signal
)


def test_detect_crown_state_great_work():
    s = {"unity_index": 0.95, "embodiment_score": 0.9, "bypass_flag": False}
    result = detect_crown_state(s)
    assert result["phase"] == "great_work_completion"
    assert result["archetype"] == "the_whole"


def test_detect_crown_state_bypassing():
    s = {"unity_index": 0.9, "embodiment_score": 0.8, "bypass_flag": True}
    result = detect_crown_state(s)
    assert result["phase"] == "spiritual_bypassing"
    assert result["archetype"] == "false_ascendant"


def test_emit_crown_alert_never_interrupts():
    alert = emit_crown_alert("GREAT_WORK_COLLAPSE")
    assert alert["interrupt_flag"] is False
    assert alert["severity"] == 5


def test_classify_crown_urgency_critical_on_bypass():
    s = {"unity_index": 0.8, "bypass_flag": True, "collapse_flag": False}
    assert classify_crown_urgency(s) == "critical"


def test_is_coagulation_signal():
    assert is_coagulation_signal({"unity_index": 0.9}) is True
    assert is_coagulation_signal({"unity_index": 0.4}) is False
