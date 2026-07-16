import pytest
from core.spectral.green.transparency import (
    detect_heart_state, emit_heart_alert,
    classify_heart_urgency, get_ui_state, is_conjunction_signal
)


def test_detect_heart_state_full_coherence():
    s = {"coherence": 0.9, "compassion_index": 0.85, "grief_load": 0.05}
    result = detect_heart_state(s)
    assert result["phase"] == "full_heart_coherence"
    assert result["archetype"] == "beloved"


def test_detect_heart_state_grief():
    s = {"coherence": 0.4, "compassion_index": 0.4, "grief_load": 0.8}
    result = detect_heart_state(s)
    assert result["phase"] == "grief_processing"


def test_emit_heart_alert_never_interrupts():
    alert = emit_heart_alert("HEART_FRACTURE")
    assert alert["interrupt_flag"] is False
    assert alert["severity"] == 5


def test_classify_heart_urgency_critical():
    s = {"coherence": 0.5, "grief_load": 0.5, "fracture_flag": True}
    assert classify_heart_urgency(s) == "critical"


def test_is_conjunction_signal_true():
    s = {"coherence": 0.85}
    assert is_conjunction_signal(s) is True
