"""
Tests for core/spectral/red/transparency.py

Covers:
  - detect_rubedo_state
  - emit_sentinel_alert
  - classify_urgency
  - get_ui_state
  - is_completion_signal
"""

import pytest
from core.spectral.red.transparency import (
    detect_rubedo_state,
    emit_sentinel_alert,
    classify_urgency,
    get_ui_state,
    is_completion_signal,
)


# ---------------------------------------------------------------------------
# detect_rubedo_state
# ---------------------------------------------------------------------------

class TestDetectRubedoState:
    def test_all_thresholds_met_returns_true(self):
        metrics = {"coherence": 0.90, "integration": 0.85, "actualization": 0.80}
        assert detect_rubedo_state(metrics) is True

    def test_borderline_exact_thresholds_returns_true(self):
        metrics = {"coherence": 0.85, "integration": 0.80, "actualization": 0.75}
        assert detect_rubedo_state(metrics) is True

    def test_low_coherence_returns_false(self):
        metrics = {"coherence": 0.70, "integration": 0.85, "actualization": 0.80}
        assert detect_rubedo_state(metrics) is False

    def test_low_integration_returns_false(self):
        metrics = {"coherence": 0.90, "integration": 0.79, "actualization": 0.80}
        assert detect_rubedo_state(metrics) is False

    def test_low_actualization_returns_false(self):
        metrics = {"coherence": 0.90, "integration": 0.85, "actualization": 0.74}
        assert detect_rubedo_state(metrics) is False

    def test_empty_dict_returns_false(self):
        assert detect_rubedo_state({}) is False

    def test_none_returns_false(self):
        assert detect_rubedo_state(None) is False

    def test_missing_keys_treated_as_zero(self):
        assert detect_rubedo_state({"coherence": 0.90}) is False


# ---------------------------------------------------------------------------
# emit_sentinel_alert
# ---------------------------------------------------------------------------

class TestEmitSentinelAlert:
    def test_level_1_returns_correct_structure(self):
        result = emit_sentinel_alert(1, "test threat")
        assert result["level"] == 1
        assert result["label"] == "ALERT"
        assert result["hex"] == "#DC2626"
        assert result["context"] == "test threat"
        assert result["layer"] == "transparency"
        assert result["tablet"] == "Ruby Tablet"

    def test_level_2_maps_to_danger(self):
        result = emit_sentinel_alert(2, "serious threat")
        assert result["label"] == "DANGER"

    def test_level_3_maps_to_scarlet(self):
        result = emit_sentinel_alert(3, "critical")
        assert result["label"] == "SCARLET"

    def test_level_below_1_clamped_to_1(self):
        result = emit_sentinel_alert(0, "test")
        assert result["level"] == 1

    def test_level_above_3_clamped_to_3(self):
        result = emit_sentinel_alert(99, "test")
        assert result["level"] == 3

    def test_none_level_defaults_to_1(self):
        result = emit_sentinel_alert(None, "test")
        assert result["level"] == 1

    def test_none_context_produces_empty_string(self):
        result = emit_sentinel_alert(1, None)
        assert result["context"] == ""


# ---------------------------------------------------------------------------
# classify_urgency
# ---------------------------------------------------------------------------

class TestClassifyUrgency:
    def test_living_flame_takes_priority(self):
        signal = {"living_flame": True, "completion": True, "error": True}
        assert classify_urgency(signal) == "living_flame"

    def test_completion_before_error(self):
        signal = {"completion": True, "error": True}
        assert classify_urgency(signal) == "completion"

    def test_error_flag(self):
        assert classify_urgency({"error": True}) == "error"

    def test_error_code_flag(self):
        assert classify_urgency({"error_code": "RED_500"}) == "error"

    def test_default_is_alert(self):
        assert classify_urgency({"some_key": "value"}) == "alert"

    def test_empty_dict_is_alert(self):
        assert classify_urgency({}) == "alert"

    def test_none_is_alert(self):
        assert classify_urgency(None) == "alert"


# ---------------------------------------------------------------------------
# get_ui_state
# ---------------------------------------------------------------------------

class TestGetUiState:
    def test_rubedo_activation(self):
        state = get_ui_state("rubedo_activation")
        assert state["hex"] == "#CC2200"
        assert state["animation"] == "pulsing"

    def test_sentinel_alert(self):
        state = get_ui_state("sentinel_alert")
        assert state["hex"] == "#DC2626"
        assert state["animation"] == "solid"

    def test_completion_signal(self):
        state = get_ui_state("completion_signal")
        assert state["hex"] == "#DC143C"
        assert state["animation"] == "static"

    def test_error_state(self):
        state = get_ui_state("error_state")
        assert state["hex"] == "#FF3333"

    def test_living_flame_mode(self):
        state = get_ui_state("living_flame_mode")
        assert state["hex"] == "#FF2400"
        assert state["animation"] == "animated"

    def test_unknown_raises_key_error(self):
        with pytest.raises(KeyError):
            get_ui_state("nonexistent_state")

    def test_returns_copy_not_reference(self):
        a = get_ui_state("rubedo_activation")
        b = get_ui_state("rubedo_activation")
        a["hex"] = "#000000"
        assert b["hex"] == "#CC2200"


# ---------------------------------------------------------------------------
# is_completion_signal
# ---------------------------------------------------------------------------

class TestIsCompletionSignal:
    def test_completion_true_returns_true(self):
        assert is_completion_signal({"completion": True}) is True

    def test_completion_with_sentinel_returns_false(self):
        assert is_completion_signal({"completion": True, "sentinel": True}) is False

    def test_completion_with_error_returns_false(self):
        assert is_completion_signal({"completion": True, "error": True}) is False

    def test_no_completion_flag_returns_false(self):
        assert is_completion_signal({"sentinel": True}) is False

    def test_empty_dict_returns_false(self):
        assert is_completion_signal({}) is False

    def test_none_returns_false(self):
        assert is_completion_signal(None) is False

    def test_rubedo_and_sentinel_are_semantically_opposite(self):
        """Both carry red — but Rubedo completion != SENTINEL danger."""
        rubedo   = {"completion": True, "sentinel": False}
        sentinel = {"completion": False, "sentinel": True}
        assert is_completion_signal(rubedo)   is True
        assert is_completion_signal(sentinel) is False
