"""
INDIGO opacity layer — shadow channel.
Domain: rational override loops, psychic numbing, vision distortion, intuition suppression.
Non-blocking. Never sets interrupt_flag = True.
"""

from .constants import BLOCK_MARKERS

_opacity_shadow = []


def block_alert(signal: dict) -> dict:
    markers = signal.get("block_markers", [])
    active = [m for m in markers if m in BLOCK_MARKERS]
    entry = {"type": "block_alert", "active_markers": active,
             "severity": min(len(active), 5), "interrupt_flag": False}
    _opacity_shadow.append(entry)
    return entry


def psychic_overload_detection(signal: dict) -> dict:
    load_history = signal.get("load_history", [])
    spike_count = sum(1 for l in load_history if l > 0.7)
    overload_detected = spike_count >= 3
    entry = {"type": "psychic_overload", "overload_detected": overload_detected,
             "spike_count": spike_count, "interrupt_flag": False}
    _opacity_shadow.append(entry)
    return entry


def vision_fog_marker(signal: dict) -> dict:
    clarity = signal.get("field_clarity", 1.0)
    fogged = clarity < 0.3
    entry = {"type": "vision_fog", "fogged": fogged,
             "clarity": clarity, "interrupt_flag": False}
    _opacity_shadow.append(entry)
    return entry


def saturn_jupiter_routing(signal: dict) -> str:
    """
    Routes to 'saturn' (structure/limitation/contraction) or 'jupiter' (expansion/vision).
    Coordinated vocabulary: jupiter aligns with BLUE opacity jupiter_mercury_routing.
    """
    structure_need = signal.get("structure_need", 0.5)
    expansion_index = signal.get("expansion_index", 0.5)
    return "saturn" if structure_need > expansion_index else "jupiter"


def apply_shadow_channel(primary_signal: dict, shadow_entries: list) -> dict:
    enriched = dict(primary_signal)
    enriched["_indigo_shadow"] = list(shadow_entries)
    return enriched
