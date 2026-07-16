import pytest
from core.spectral.violet.opacity import (
    fragmentation_alert, bypassing_loop_detection,
    embodiment_refusal_marker, crown_saturn_routing,
    read_full_spectral_shadow, apply_shadow_channel
)


def test_fragmentation_alert_never_interrupts():
    s = {"fragmentation_markers": ["spiritual_bypassing", "embodiment_refusal"]}
    result = fragmentation_alert(s)
    assert result["interrupt_flag"] is False


def test_bypassing_loop_detected():
    s = {"bypass_history": [True, True, True, True]}
    result = bypassing_loop_detection(s)
    assert result["loop_detected"] is True
    assert result["interrupt_flag"] is False


def test_embodiment_refusal_flagged():
    s = {"embodiment_score": 0.05}
    result = embodiment_refusal_marker(s)
    assert result["refused"] is True
    assert result["interrupt_flag"] is False


def test_crown_saturn_routing():
    assert crown_saturn_routing({"unity_index": 0.9, "grounding_need": 0.2}) == "crown"
    assert crown_saturn_routing({"unity_index": 0.2, "grounding_need": 0.8}) == "saturn"


def test_read_full_spectral_shadow_interrupt_safe():
    all_shadows = {
        "red": [{"severity": 2, "interrupt_flag": False}],
        "orange": [{"severity": 1, "interrupt_flag": False}],
        "yellow": [], "green": [], "blue": [], "indigo": [], "violet": []
    }
    summary = read_full_spectral_shadow(all_shadows)
    for color, data in summary.items():
        assert data["interrupt_safe"] is True


def test_apply_shadow_channel_no_mutation():
    primary = {"unity_index": 0.8}
    shadow = [{"type": "bypassing_loop", "interrupt_flag": False}]
    enriched = apply_shadow_channel(primary, shadow)
    assert "_violet_shadow" in enriched
    assert "_violet_shadow" not in primary
