import pytest
from core.spectral.indigo.clarity import (
    distinguish_intuition_delusion, detect_block_pattern,
    classify_indigo_fire, assess_field_perception_health, map_intuition_archetype
)


def test_distinguish_active_delusion():
    s = {"intuition_index": 0.6, "reality_anchor": 0.3, "delusion_index": 0.85}
    assert distinguish_intuition_delusion(s) == "active_delusion"


def test_distinguish_grounded_intuition():
    s = {"intuition_index": 0.85, "reality_anchor": 0.75, "delusion_index": 0.05}
    assert distinguish_intuition_delusion(s) == "grounded_intuition"


def test_classify_indigo_fire_distillation():
    s = {"distillation_flag": True}
    assert classify_indigo_fire(s) == "distillation"


def test_detect_block_pattern():
    s = {"block_markers": ["intuition_suppression", "rational_override"], "block_depth": 0.75}
    result = detect_block_pattern(s)
    assert result["block_present"] is True
    assert result["intervention_suggested"] is True


def test_map_intuition_archetype_oracle():
    s = {"intuition_index": 0.9, "field_perception": 0.85, "rational_override": 0.05, "reality_anchor": 0.7}
    assert map_intuition_archetype(s) == "oracle"
