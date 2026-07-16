import pytest
from core.spectral.violet.clarity import (
    distinguish_unity_bypassing, detect_fragmentation_pattern,
    classify_violet_fire, assess_spectral_integration, map_crown_archetype
)


def test_distinguish_spiritual_bypassing():
    s = {"unity_index": 0.85, "embodiment_score": 0.15, "bypass_flag": True}
    assert distinguish_unity_bypassing(s) == "spiritual_bypassing"


def test_distinguish_embodied_unity():
    s = {"unity_index": 0.9, "embodiment_score": 0.85, "bypass_flag": False}
    assert distinguish_unity_bypassing(s) == "embodied_unity"


def test_classify_violet_fire_coagulation():
    s = {"coagulation_flag": True, "bypass_flag": False}
    assert classify_violet_fire(s) == "coagulation"


def test_assess_spectral_integration_full():
    stage_scores = {"red": 0.9, "orange": 0.8, "yellow": 0.75,
                    "green": 0.85, "blue": 0.9, "indigo": 0.8, "violet": 0.95}
    result = assess_spectral_integration({"stage_scores": stage_scores})
    assert result["great_work_ready"] is True
    assert result["integration_ratio"] == 1.0


def test_assess_spectral_integration_partial():
    stage_scores = {"red": 0.9, "orange": 0.3, "yellow": 0.75}
    result = assess_spectral_integration({"stage_scores": stage_scores})
    assert result["great_work_ready"] is False


def test_map_crown_archetype_the_whole():
    s = {"unity_index": 0.95, "embodiment_score": 0.9, "bypass_flag": False}
    assert map_crown_archetype(s) == "the_whole"
