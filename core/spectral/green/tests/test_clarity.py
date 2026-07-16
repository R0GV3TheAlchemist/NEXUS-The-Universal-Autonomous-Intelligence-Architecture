import pytest
from core.spectral.green.clarity import (
    distinguish_compassion_codependency, detect_grief_pattern,
    classify_green_fire, assess_bridge_health, map_heart_archetype
)


def test_distinguish_codependency():
    s = {"compassion_index": 0.6, "boundary_score": 0.2, "self_sacrifice": 0.85}
    assert distinguish_compassion_codependency(s) == "codependency"


def test_distinguish_healthy_compassion():
    s = {"compassion_index": 0.85, "boundary_score": 0.75, "self_sacrifice": 0.2}
    assert distinguish_compassion_codependency(s) == "healthy_compassion"


def test_classify_green_fire_conjunction():
    s = {"conjunction_flag": True}
    assert classify_green_fire(s) == "conjunction"


def test_detect_grief_pattern_present():
    s = {"grief_markers": ["grief_freeze", "compassion_fatigue"], "grief_depth": 0.75}
    result = detect_grief_pattern(s)
    assert result["grief_present"] is True
    assert result["intervention_suggested"] is True


def test_map_heart_archetype_beloved():
    s = {"coherence": 0.9, "compassion_index": 0.88, "grief_load": 0.05, "self_sacrifice": 0.1}
    assert map_heart_archetype(s) == "beloved"
