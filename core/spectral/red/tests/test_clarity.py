"""
Tests for core/spectral/red/clarity.py

Covers:
  - distinguish_anger_passion
  - detect_sacred_wound
  - classify_red_fire (all 3 branches)
  - assess_integration_level
  - map_warrior_archetype
"""

import pytest
from core.spectral.red.clarity import (
    distinguish_anger_passion,
    detect_sacred_wound,
    classify_red_fire,
    assess_integration_level,
    map_warrior_archetype,
)


# ---------------------------------------------------------------------------
# distinguish_anger_passion
# ---------------------------------------------------------------------------

class TestDistinguishAngerPassion:
    def test_passion_features_return_passion(self):
        signal = {"features": ["life_force", "creative_drive", "vitality"]}
        assert distinguish_anger_passion(signal) == "passion"

    def test_anger_features_return_anger(self):
        signal = {"features": ["reactivity", "blame_projection", "defensiveness"]}
        assert distinguish_anger_passion(signal) == "anger"

    def test_tie_defaults_to_anger(self):
        signal = {"features": ["life_force", "reactivity"]}
        assert distinguish_anger_passion(signal) == "anger"

    def test_empty_features_returns_anger(self):
        assert distinguish_anger_passion({"features": []}) == "anger"

    def test_none_signal_returns_anger(self):
        assert distinguish_anger_passion(None) == "anger"

    def test_empty_signal_returns_anger(self):
        assert distinguish_anger_passion({}) == "anger"

    def test_does_not_default_to_single_output_on_mixed(self):
        """Must discriminate — single passion feature beats zero anger features."""
        signal = {"features": ["purposeful"]}
        assert distinguish_anger_passion(signal) == "passion"


# ---------------------------------------------------------------------------
# detect_sacred_wound
# ---------------------------------------------------------------------------

class TestDetectSacredWound:
    def test_wound_resonance_triggers_wound_present(self):
        result = detect_sacred_wound({"wound_resonance": True})
        assert result["wound_present"] is True

    def test_historical_trigger_triggers_wound_present(self):
        result = detect_sacred_wound({"historical_trigger": True})
        assert result["wound_present"] is True

    def test_no_wound_markers_returns_not_present(self):
        result = detect_sacred_wound({"completion": True})
        assert result["wound_present"] is False

    def test_returns_wound_present_key(self):
        result = detect_sacred_wound({"wound_resonance": True})
        assert "wound_present" in result

    def test_returns_stage_key(self):
        result = detect_sacred_wound({"wound_resonance": True})
        assert "stage" in result

    def test_returns_estimated_origin_key(self):
        result = detect_sacred_wound({"wound_resonance": True})
        assert "estimated_origin" in result

    def test_explicit_stage_respected(self):
        result = detect_sacred_wound({"wound_resonance": True, "wound_stage": "integrating"})
        assert result["stage"] == "integrating"

    def test_invalid_stage_falls_back(self):
        result = detect_sacred_wound({"wound_resonance": True, "wound_stage": "nonsense"})
        assert result["stage"] in ("metabolizing", "unacknowledged", "contact", "integrating", "integrated", "complete", "pre-contact")

    def test_none_signal_returns_not_present(self):
        result = detect_sacred_wound(None)
        assert result["wound_present"] is False

    def test_estimated_origin_passed_through(self):
        result = detect_sacred_wound({"wound_resonance": True, "estimated_origin": "early_loss"})
        assert result["estimated_origin"] == "early_loss"


# ---------------------------------------------------------------------------
# classify_red_fire
# ---------------------------------------------------------------------------

class TestClassifyRedFire:
    def test_reactive_override_returns_reactive(self):
        assert classify_red_fire({"reactive": True}) == "reactive"

    def test_completion_override_returns_generative(self):
        assert classify_red_fire({"completion": True}) == "generative"

    def test_living_flame_returns_generative(self):
        assert classify_red_fire({"living_flame": True}) == "generative"

    def test_passion_features_return_generative(self):
        signal = {"features": ["life_force", "creative_drive", "vitality"]}
        assert classify_red_fire(signal) == "generative"

    def test_protective_features_return_protective(self):
        signal = {"features": ["life_force", "boundary", "protective"]}
        assert classify_red_fire(signal) == "protective"

    def test_anger_with_boundary_returns_protective(self):
        signal = {"features": ["reactivity", "boundary"]}
        assert classify_red_fire(signal) == "protective"

    def test_anger_only_returns_reactive(self):
        signal = {"features": ["reactivity", "blame_projection"]}
        assert classify_red_fire(signal) == "reactive"

    def test_empty_signal_returns_reactive(self):
        assert classify_red_fire({}) == "reactive"

    def test_none_returns_reactive(self):
        assert classify_red_fire(None) == "reactive"

    def test_all_three_branches_reachable(self):
        generative = classify_red_fire({"completion": True})
        protective = classify_red_fire({"features": ["boundary", "protective", "life_force"]})
        reactive   = classify_red_fire({"reactive": True})
        assert {generative, protective, reactive} == {"generative", "protective", "reactive"}


# ---------------------------------------------------------------------------
# assess_integration_level
# ---------------------------------------------------------------------------

class TestAssessIntegrationLevel:
    def test_empty_history_returns_0_5(self):
        assert assess_integration_level("entity_1", []) == 0.5

    def test_generative_history_raises_score(self):
        history = [{"classification": "generative"} for _ in range(5)]
        score = assess_integration_level("entity_1", history)
        assert score > 0.5

    def test_reactive_history_lowers_score(self):
        history = [{"classification": "reactive"} for _ in range(5)]
        score = assess_integration_level("entity_1", history)
        assert score < 0.5

    def test_integrated_wound_stage_bonus(self):
        history = [{"classification": "generative", "wound_stage": "integrated"}]
        score = assess_integration_level("entity_1", history)
        assert score > 0.5 + 0.05

    def test_score_bounded_to_1(self):
        history = [{"classification": "generative", "wound_stage": "integrated"} for _ in range(100)]
        assert assess_integration_level("x", history) <= 1.0

    def test_score_bounded_to_0(self):
        history = [{"classification": "reactive"} for _ in range(100)]
        assert assess_integration_level("x", history) >= 0.0

    def test_returns_float(self):
        assert isinstance(assess_integration_level("x", []), float)


# ---------------------------------------------------------------------------
# map_warrior_archetype
# ---------------------------------------------------------------------------

class TestMapWarriorArchetype:
    def test_athena_override_returns_athena(self):
        assert map_warrior_archetype({"archetype": "athena"}) == "athena"

    def test_ares_override_returns_ares(self):
        assert map_warrior_archetype({"archetype": "ares"}) == "ares"

    def test_generative_fire_maps_to_athena(self):
        signal = {"completion": True}
        assert map_warrior_archetype(signal) == "athena"

    def test_reactive_fire_maps_to_ares(self):
        signal = {"reactive": True}
        assert map_warrior_archetype(signal) == "ares"

    def test_none_returns_ares(self):
        assert map_warrior_archetype(None) == "ares"

    def test_empty_returns_ares(self):
        assert map_warrior_archetype({}) == "ares"

    def test_return_values_match_opacity_ares_athena_vocabulary(self):
        """Vocabulary must be coordinated with opacity.ares_athena_routing."""
        results = {
            map_warrior_archetype({"completion": True}),
            map_warrior_archetype({"reactive": True}),
        }
        assert results <= {"ares", "athena"}
