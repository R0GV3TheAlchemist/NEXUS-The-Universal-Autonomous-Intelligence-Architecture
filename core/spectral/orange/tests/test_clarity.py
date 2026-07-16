import pytest
from core.spectral.orange.clarity import (
    distinguish_pleasure_compulsion, detect_sacral_wound,
    classify_orange_fire, assess_boundary_health, map_creative_archetype
)


def test_distinguish_pleasure_guilt_suppression():
    s = {"pleasure_score": 0.2, "guilt_index": 0.9, "repetition_rate": 0.3}
    assert distinguish_pleasure_compulsion(s) == "guilt_suppression"


def test_distinguish_pleasure_healthy():
    s = {"pleasure_score": 0.85, "guilt_index": 0.1, "repetition_rate": 0.2}
    assert distinguish_pleasure_compulsion(s) == "healthy_pleasure"


def test_classify_orange_fire_calcination():
    s = {"calcination_flag": True, "dissolution_flag": False, "creativity_index": 0.5}
    assert classify_orange_fire(s) == "calcination"


def test_classify_orange_fire_creative_ignition():
    s = {"calcination_flag": False, "dissolution_flag": False, "creativity_index": 0.9}
    assert classify_orange_fire(s) == "creative_ignition"


def test_detect_sacral_wound_present():
    s = {"wound_markers": ["ego_softening", "boundary_dissolution"], "wound_depth": 0.7}
    result = detect_sacral_wound(s)
    assert result["wound_present"] is True
    assert result["intervention_suggested"] is True


def test_map_creative_archetype_creator():
    s = {"intensity": 0.8, "guilt_index": 0.1, "creativity_index": 0.9}
    assert map_creative_archetype(s) == "creator"
