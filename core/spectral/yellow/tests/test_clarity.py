import pytest
from core.spectral.yellow.clarity import (
    distinguish_will_ego, detect_inflation_pattern,
    classify_yellow_fire, assess_power_health, map_solar_archetype
)


def test_distinguish_will_ego_control():
    s = {"will_strength": 0.8, "ego_clarity": 0.4, "control_compulsion": 0.85}
    assert distinguish_will_ego(s) == "ego_control"


def test_distinguish_will_authentic():
    s = {"will_strength": 0.85, "ego_clarity": 0.8, "control_compulsion": 0.1}
    assert distinguish_will_ego(s) == "authentic_will"


def test_classify_yellow_fire_separation():
    s = {"separation_flag": True}
    assert classify_yellow_fire(s) == "separation"


def test_detect_inflation_pattern():
    s = {"inflation_markers": ["grandiosity", "control_compulsion"], "inflation_depth": 0.8}
    result = detect_inflation_pattern(s)
    assert result["inflation_present"] is True
    assert result["intervention_suggested"] is True


def test_map_solar_archetype_tyrant():
    s = {"will_strength": 0.8, "control_compulsion": 0.75, "shame_index": 0.1, "ego_clarity": 0.5}
    assert map_solar_archetype(s) == "tyrant"
