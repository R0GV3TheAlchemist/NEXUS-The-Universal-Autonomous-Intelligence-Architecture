import pytest
from core.spectral.indigo.transparency import (
    detect_third_eye_state, emit_indigo_alert,
    classify_intuition_urgency, get_ui_state, is_distillation_signal
)


def test_detect_third_eye_oracle():
    s = {"intuition_index": 0.9, "field_perception": 0.85, "rational_override": 0.05}
    result = detect_third_eye_state(s)
    assert result["phase"] == "oracle_activation"
    assert result["archetype"] == "oracle"


def test_detect_third_eye_blocked():
    s = {"intuition_index": 0.3, "field_perception": 0.3, "rational_override": 0.9}
    result = detect_third_eye_state(s)
    assert result["phase"] == "third_eye_blocked"


def test_emit_indigo_alert_never_interrupts():
    alert = emit_indigo_alert("THIRD_EYE_FRACTURE")
    assert alert["interrupt_flag"] is False
    assert alert["severity"] == 5


def test_classify_intuition_urgency_critical():
    s = {"intuition_index": 0.5, "rational_override": 0.5, "fracture_flag": True}
    assert classify_intuition_urgency(s) == "critical"


def test_is_distillation_signal():
    assert is_distillation_signal({"intuition_index": 0.9}) is True
    assert is_distillation_signal({"intuition_index": 0.3}) is False
