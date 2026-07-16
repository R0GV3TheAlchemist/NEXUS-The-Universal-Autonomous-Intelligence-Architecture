import pytest
from core.spectral.blue.transparency import (
    detect_throat_state, emit_throat_alert,
    classify_expression_urgency, get_ui_state, is_fermentation_signal
)


def test_detect_throat_state_sovereign_voice():
    s = {"truth_index": 0.9, "expression_rate": 0.85, "silence_score": 0.05}
    result = detect_throat_state(s)
    assert result["phase"] == "sovereign_voice"
    assert result["archetype"] == "truth_speaker"


def test_detect_throat_state_suppressed():
    s = {"truth_index": 0.4, "expression_rate": 0.3, "silence_score": 0.8}
    result = detect_throat_state(s)
    assert result["phase"] == "voice_suppressed"


def test_emit_throat_alert_never_interrupts():
    alert = emit_throat_alert("VOICE_FRACTURE")
    assert alert["interrupt_flag"] is False
    assert alert["severity"] == 5


def test_classify_expression_urgency_critical():
    s = {"expression_rate": 0.5, "silence_score": 0.5, "fracture_flag": True}
    assert classify_expression_urgency(s) == "critical"


def test_is_fermentation_signal():
    assert is_fermentation_signal({"truth_index": 0.85}) is True
    assert is_fermentation_signal({"truth_index": 0.5}) is False
