"""
Tests for core/spectral/red/opacity.py

Covers:
  - nigredo_alert (invariant: interrupt_flag is ALWAYS False)
  - wound_pattern_recognition (5+ cases)
  - red_lion_detection (force_level bounded [0.0, 1.0])
  - phoenix_marker (multi-cycle history)
  - ares_athena_routing
  - apply_shadow_channel (full integration)
"""

import pytest
from core.spectral.red.opacity import (
    nigredo_alert,
    wound_pattern_recognition,
    red_lion_detection,
    phoenix_marker,
    ares_athena_routing,
    apply_shadow_channel,
)


# ---------------------------------------------------------------------------
# nigredo_alert
# ---------------------------------------------------------------------------

class TestNigredoAlert:
    def test_nigredo_flag_activates(self):
        assert nigredo_alert({"nigredo": True})["nigredo_active"] is True

    def test_dissolution_flag_activates(self):
        assert nigredo_alert({"dissolution": True})["nigredo_active"] is True

    def test_prima_materia_flag_activates(self):
        assert nigredo_alert({"prima_materia": True})["nigredo_active"] is True

    def test_no_flags_returns_false(self):
        assert nigredo_alert({"completion": True})["nigredo_active"] is False

    def test_interrupt_flag_is_always_false(self):
        """INVARIANT: Nigredo must never be interrupted."""
        assert nigredo_alert({"nigredo": True})["interrupt_flag"] is False

    def test_interrupt_flag_is_false_even_when_not_active(self):
        assert nigredo_alert({})["interrupt_flag"] is False

    def test_interrupt_flag_cannot_be_set_true_by_any_input(self):
        """Even if a caller passes interrupt_flag=True in signal, output must be False."""
        assert nigredo_alert({"interrupt_flag": True})["interrupt_flag"] is False

    def test_empty_dict_returns_false_active(self):
        result = nigredo_alert({})
        assert result["nigredo_active"] is False

    def test_none_returns_false_active(self):
        result = nigredo_alert(None)
        assert result["nigredo_active"] is False


# ---------------------------------------------------------------------------
# wound_pattern_recognition
# ---------------------------------------------------------------------------

class TestWoundPatternRecognition:
    def test_present_threat_returns_real_urgency(self):
        signal = {"features": ["present_threat", "immediate_danger"]}
        result = wound_pattern_recognition(signal, [])
        assert result["urgency_type"] == "real_urgency"

    def test_historical_trigger_alone_returns_echo_urgency(self):
        signal = {"features": ["historical_trigger", "wound_resonance"]}
        result = wound_pattern_recognition(signal, [])
        assert result["urgency_type"] == "echo_urgency"

    def test_wound_echo_true_when_echo_markers_present(self):
        signal = {"features": ["wound_resonance"]}
        result = wound_pattern_recognition(signal, [])
        assert result["wound_echo"] is True

    def test_wound_echo_false_for_present_only_signal(self):
        signal = {"features": ["present_threat", "live_emergency"]}
        result = wound_pattern_recognition(signal, [])
        assert result["wound_echo"] is False

    def test_history_amplifies_echo_score(self):
        """Repeated echo patterns in history should strengthen echo classification."""
        signal  = {"features": ["present_threat"]}  # one present marker
        history = [{"features": ["historical_trigger"]} for _ in range(5)]  # heavy history
        result  = wound_pattern_recognition(signal, history)
        # With 5 historical echoes, echo_score >> real_score
        assert result["urgency_type"] == "echo_urgency"

    def test_metabolization_stage_passed_through_if_valid(self):
        signal = {"features": ["wound_resonance"], "metabolization_stage": "integrating"}
        result = wound_pattern_recognition(signal, [])
        assert result["metabolization_stage"] == "integrating"

    def test_invalid_metabolization_stage_falls_back(self):
        signal = {"features": ["wound_resonance"], "metabolization_stage": "nonsense"}
        result = wound_pattern_recognition(signal, [])
        assert result["metabolization_stage"] in (
            "pre-contact", "contact", "metabolizing", "integrating", "complete"
        )

    def test_empty_signal_returns_echo_urgency(self):
        result = wound_pattern_recognition({}, [])
        assert result["urgency_type"] == "echo_urgency"

    def test_none_signal_returns_echo_urgency(self):
        result = wound_pattern_recognition(None, [])
        assert result["urgency_type"] == "echo_urgency"


# ---------------------------------------------------------------------------
# red_lion_detection
# ---------------------------------------------------------------------------

class TestRedLionDetection:
    def test_explicit_force_level_respected(self):
        result = red_lion_detection({"force_level": 0.8})
        assert result["force_level"] == 0.8

    def test_force_level_above_0_7_triggers_transmutation(self):
        result = red_lion_detection({"force_level": 0.75})
        assert result["transmutation_required"] is True

    def test_force_level_below_0_7_no_transmutation(self):
        result = red_lion_detection({"force_level": 0.5})
        assert result["transmutation_required"] is False

    def test_force_level_bounded_above_1(self):
        result = red_lion_detection({"force_level": 99.0})
        assert result["force_level"] <= 1.0

    def test_force_level_bounded_below_0(self):
        result = red_lion_detection({"force_level": -5.0})
        assert result["force_level"] >= 0.0

    def test_unbound_features_generate_force_level(self):
        signal = {"features": ["unbound_force", "directionless", "destructive", "escalating", "uncontrolled", "boundary_violating"]}
        result = red_lion_detection(signal)
        assert result["force_level"] == 1.0
        assert result["red_lion_active"] is True
        assert result["transmutation_required"] is True

    def test_zero_unbound_features_returns_zero_force(self):
        signal = {"features": ["life_force", "creative_drive"]}
        result = red_lion_detection(signal)
        assert result["force_level"] == 0.0
        assert result["red_lion_active"] is False

    def test_empty_signal_returns_zero(self):
        result = red_lion_detection({})
        assert result["force_level"] == 0.0

    def test_none_returns_zero(self):
        result = red_lion_detection(None)
        assert result["force_level"] == 0.0


# ---------------------------------------------------------------------------
# phoenix_marker
# ---------------------------------------------------------------------------

class TestPhoenixMarker:
    def test_no_history_returns_zero_cycles(self):
        result = phoenix_marker("e1", [])
        assert result["phoenix_complete"] is False
        assert result["cycle_count"] == 0

    def test_single_cycle_detected(self):
        history = [
            {"phase": "nigredo"},
            {"phase": "albedo"},
            {"phase": "rubedo"},
        ]
        result = phoenix_marker("e1", history)
        assert result["phoenix_complete"] is True
        assert result["cycle_count"] == 1

    def test_rubedo_without_prior_nigredo_not_counted(self):
        history = [{"phase": "rubedo"}]
        result = phoenix_marker("e1", history)
        assert result["cycle_count"] == 0

    def test_two_complete_cycles(self):
        history = [
            {"phase": "nigredo"}, {"phase": "rubedo"},
            {"phase": "nigredo"}, {"phase": "rubedo"},
        ]
        result = phoenix_marker("e1", history)
        assert result["cycle_count"] == 2

    def test_integration_gain_increases_with_cycles(self):
        one_cycle = phoenix_marker("e1", [
            {"phase": "nigredo"}, {"phase": "rubedo"},
        ])
        two_cycles = phoenix_marker("e1", [
            {"phase": "nigredo"}, {"phase": "rubedo"},
            {"phase": "nigredo"}, {"phase": "rubedo"},
        ])
        assert two_cycles["integration_gain"] > one_cycle["integration_gain"]

    def test_integration_gain_bounded_to_1(self):
        history = [{"phase": "nigredo"}, {"phase": "rubedo"}] * 100
        result = phoenix_marker("e1", history)
        assert result["integration_gain"] <= 1.0

    def test_integration_gain_is_float(self):
        history = [{"phase": "nigredo"}, {"phase": "rubedo"}]
        assert isinstance(phoenix_marker("e1", history)["integration_gain"], float)

    def test_none_history_returns_zero(self):
        result = phoenix_marker("e1", None)
        assert result["cycle_count"] == 0


# ---------------------------------------------------------------------------
# ares_athena_routing
# ---------------------------------------------------------------------------

class TestAresAthenaRouting:
    def test_shadow_override_athena(self):
        assert ares_athena_routing({"_shadow_archetype": "athena"}) == "athena"

    def test_shadow_override_ares(self):
        assert ares_athena_routing({"_shadow_archetype": "ares"}) == "ares"

    def test_generative_fire_routes_to_athena(self):
        assert ares_athena_routing({"completion": True}) == "athena"

    def test_reactive_fire_routes_to_ares(self):
        assert ares_athena_routing({"reactive": True}) == "ares"

    def test_return_values_are_only_ares_or_athena(self):
        results = {
            ares_athena_routing({"completion": True}),
            ares_athena_routing({"reactive": True}),
            ares_athena_routing({}),
        }
        assert results <= {"ares", "athena"}

    def test_none_returns_ares(self):
        assert ares_athena_routing(None) == "ares"


# ---------------------------------------------------------------------------
# apply_shadow_channel (integration)
# ---------------------------------------------------------------------------

class TestApplyShadowChannel:
    def _make_signal(self):
        return {
            "completion": True,
            "features": ["life_force", "purposeful"],
        }

    def test_returns_dict_with_opacity_shadow_key(self):
        result = apply_shadow_channel(self._make_signal())
        assert "_opacity_shadow" in result

    def test_shadow_contains_all_five_keys(self):
        shadow = apply_shadow_channel(self._make_signal())["_opacity_shadow"]
        assert set(shadow.keys()) == {"nigredo", "wound_pattern", "red_lion", "phoenix", "ares_athena"}

    def test_primary_signal_keys_not_mutated(self):
        original = self._make_signal()
        original_copy = dict(original)
        result = apply_shadow_channel(original)
        for key in original_copy:
            assert result[key] == original_copy[key]

    def test_does_not_mutate_input_signal(self):
        signal = self._make_signal()
        _ = apply_shadow_channel(signal)
        assert "_opacity_shadow" not in signal  # input must be unchanged

    def test_shadow_appended_without_modifying_primary_semantics(self):
        signal = {"some_key": "some_value"}
        result = apply_shadow_channel(signal)
        assert result["some_key"] == "some_value"

    def test_cycle_history_passed_to_phoenix(self):
        cycle_history = [{"phase": "nigredo"}, {"phase": "rubedo"}]
        result = apply_shadow_channel({}, cycle_history=cycle_history)
        assert result["_opacity_shadow"]["phoenix"]["phoenix_complete"] is True
