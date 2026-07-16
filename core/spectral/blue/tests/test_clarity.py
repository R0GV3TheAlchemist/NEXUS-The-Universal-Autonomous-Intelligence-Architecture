import pytest
from core.spectral.blue.clarity import (
    distinguish_truth_deception, detect_silence_pattern,
    classify_blue_fire, assess_perception_health, map_throat_archetype
)


def test_distinguish_self_deception():
    s = {"truth_index": 0.4, "distortion_index": 0.3, "self_deception": 0.85}
    assert distinguish_truth_deception(s) == "self_deception"


def test_distinguish_clear_truth():
    s = {"truth_index": 0.9, "distortion_index": 0.05, "self_deception": 0.0}
    assert distinguish_truth_deception(s) == "clear_truth"


def test_classify_blue_fire_fermentation():
    s = {"fermentation_flag": True}
    assert classify_blue_fire(s) == "fermentation"


def test_detect_silence_pattern():
    s = {"silence_markers": ["voice_suppression", "expression_shame"], "silence_depth": 0.8}
    result = detect_silence_pattern(s)
    assert result["silence_present"] is True
    assert result["intervention_suggested"] is True


def test_map_throat_archetype_truth_speaker():
    s = {"truth_index": 0.9, "expression_rate": 0.85, "silence_score": 0.0}
    assert map_throat_archetype(s) == "truth_speaker"
