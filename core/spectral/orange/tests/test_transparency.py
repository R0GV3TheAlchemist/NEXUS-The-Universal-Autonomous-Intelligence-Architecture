import pytest
from core.spectral.orange.transparency import (
    detect_sacral_state, emit_sacral_alert,
    classify_creative_urgency, get_ui_state, is_dissolution_signal
)


def test_detect_sacral_state_peak_flow():
    s = {"intensity": 0.95, "creativity_index": 0.85, "boundary_score": 0.8}
    result = detect_sacral_state(s)
    assert result["phase"] == "peak_creative_flow"
    assert result["archetype"] == "creator"


def test_detect_sacral_state_block():
    s = {"intensity": 0.1, "creativity_index": 0.1, "boundary_score": 0.9}
    result = detect_sacral_state(s)
    assert result["phase"] == "creative_block"
    assert result["archetype"] == "wounded_child"


def test_emit_sacral_alert_never_interrupts():
    alert = emit_sacral_alert("BOUNDARY_BREACH", {"source": "test"})
    assert alert["interrupt_flag"] is False
    assert alert["severity"] == 2


def test_classify_creative_urgency_critical_on_block():
    s = {"intensity": 0.5, "boundary_score": 0.9, "block_flag": True}
    assert classify_creative_urgency(s) == "critical"


def test_is_dissolution_signal_true():
    s = {"boundary_score": 0.2}
    assert is_dissolution_signal(s) is True


def test_is_dissolution_signal_false():
    s = {"boundary_score": 0.8}
    assert is_dissolution_signal(s) is False
